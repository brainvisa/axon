# -*- coding: utf-8 -*-
from soma.jobs.constants import *
from soma.jobs.jobClient import JobTemplate, FileTransfer, FileSending, FileRetrieving, UniversalResourcePath, FileRetrieving, Group, Workflow
import os
from neuroProcesses import ProcessExecutionNode, SerialExecutionNode, ParallelExecutionNode, WriteDiskItem, ReadDiskItem
import pickle
import neuroHierarchy

class ProcessToWorkflow( object ):
  JOB = 'j'
  PARALLEL_GROUP = 'p'
  SERIAL_GROUP = 's'
  FILE = 'f'
  
  def __init__( self, process ):
    self.process = process
    self._identifiers = {}
    # self._groups = groupId -> ( label, content )
    self._groups = { None: ( None, [] ) }
    self._inGroup = {}
    self._jobs = {}
    # self._files = fileId -> (fileName, fullPaths)
    self._files = {}
    # self._filesNames = fileName -> fileId
    self._fileNames = {}
    # self._iofiles = fileId -> (list of job for which the file is an input, list of job for which the file is an output) 
    self._iofiles = {}
  
  def _createIdentifier( self, type ):
    count = self._identifiers.get( type, 0 ) + 1
    self._identifiers[ type ] = count
    return type + str( count )
  
  
  def _processExecutionNode( self, eNode, inGroup ):
    if eNode is not None and eNode.isSelected():
      if isinstance( eNode, ProcessExecutionNode ):
        pENode = eNode._process._executionNode
        if pENode is None:
          # Create job
          jobId = self._createIdentifier( self.JOB )
          #print 'Create job:', jobId, '(', inGroup, ')', eNode._process.name
          self._jobs[ jobId ] = eNode._process
          self._groups[ inGroup ][ 1 ].append( jobId )
          self._inGroup[ jobId ] = inGroup
          return
      else:
        pENode = eNode
      if isinstance( pENode, ParallelExecutionNode ):
        process = getattr( eNode, '_process', None )
        if process is None:
          label = None
        else:
          label = process.name
        # Create parallel group
        groupId = self._createIdentifier( self.PARALLEL_GROUP )
        #print 'Create group (parallel):', groupId, '(', inGroup, ')', label
        self._groups[ groupId ] = ( label, [] )
        self._groups[ inGroup ][ 1 ].append( groupId )
        self._inGroup[ groupId ] = inGroup
        for i in eNode.children():
          self._processExecutionNode( i, groupId )
      elif isinstance( pENode, SerialExecutionNode ):
        process = getattr( eNode, '_process', None )
        if process is None:
          label = None
        else:
          label = process.name
        # Create serial group
        groupId = self._createIdentifier( self.SERIAL_GROUP )
        #print 'Create group (serial):', groupId, '(', inGroup, ')', label
        self._groups[ groupId ] = ( label, [] )
        self._groups[ inGroup ][ 1 ].append( groupId )
        self._inGroup[ groupId ] = inGroup
        for i in eNode.children():
          self._processExecutionNode( i, groupId )
      else:
        for i in eNode.children():
          self._processExecutionNode( i, inGroup )


  def doIt( self ):
    self._processExecutionNode( self.process._executionNode, None )
    #import pprint
    #pprint.pprint( self._groups )
    self._processNodes( 0, self._groups[ None ][ 1 ], None, set(), set(), False, None )
    for fid, input_output in self._iofiles.iteritems():
      input, output = input_output
      #if len( output ) > 1:
        #print '!!!', 'File "%s" is created by several processes: %s' % ( self._files[fid][0], ', '.join( self._jobs[ i ].name for i in output ) )
      #fileId = self._createIdentifier( self.FILE )
      #print "------------"
      #print repr(fid) + " " + repr(input) + " " + repr(output)
      
      if output:
        self.create_output_file( fid, self._files[fid][0], self._files[fid][1], self._files[fid][2], self._files[fid][3] )
      else:
        self.create_input_file( fid, self._files[fid][0], self._files[fid][1], self._files[fid][2], self._files[fid][3] )
      #for i in input:
        #self.create_link( fileId, i )
      #for o in output:
        #self.create_link( o, fileId )
  
  
  def _processNodes( self, depth, nodes, inGroup, begin, end, serial, previous ):
    first = None
    last = previous
    for id in nodes:
      if id[ 0 ] == self.JOB:
        process = self._jobs[ id ]
        for name, type in process.signature.iteritems():
          if isinstance( type, WriteDiskItem ):
            fileName = getattr( process, name, None )
            if fileName is not None:
              if not fileName.fullPath() in self._fileNames.keys():
                fileId = self._createIdentifier( self.FILE )
                database = fileName.get( '_database' )
                databaseUuid = None
                if database:
                  databaseUuid = neuroHierarchy.databases.database(database).uuid
                #print "file => " + repr(fileName.fullPath())
                #print "database => " + repr(database)
                #print "databaseUuid => " + repr(databaseUuid)
                self._files[fileId]=(fileName.fullPath(), fileName.fullPaths(), databaseUuid, database)
                self._fileNames[fileName.fullPath()]= fileId
              else:
                fileId = self._fileNames[fileName.fullPath()]
              self._iofiles.setdefault( fileId, ( [], [] ) )[ 1 ].append( id )
              
          elif isinstance( type, ReadDiskItem ):
            fileName = getattr( process, name, None )
            if fileName is not None:
              if fileName.fullPath() not in self._fileNames.keys():
                fileId = self._createIdentifier( self.FILE )
                database = fileName.get( '_database' )
                databaseUuid = None
                if database:
                  databaseUuid = neuroHierarchy.databases.database( database ).uuid
                self._files[fileId]=(fileName.fullPath(), fileName.fullPaths(), databaseUuid, database)
                self._fileNames[fileName.fullPath()]= fileId
              else:
                fileId = self._fileNames[fileName.fullPath()]
              self._iofiles.setdefault( fileId, ( [], [] ) )[ 0 ].append( id )
              
        self._create_job( depth, id, process, inGroup )
        if serial:
          if first is None:
            first = [ id ]
          previous = last
          last = [ id ]
        else:
          begin.add( id )
          end.add( id )
          if previous:
            for source in previous:
              if source != id:
                self.create_link(  source, id )
              
        
        
      elif id[ 0 ] == self.PARALLEL_GROUP:
        label, content = self._groups[ id ]
        self.open_group( depth, id, label, inGroup )
        b = set()
        e = set()
        self._processNodes( depth + 1, content, id, b, e, False, last )
        if serial:
          if first is None:
            first = b
          previous = None
          last = e
        else:
          begin.update( b )
          end.update( e )
        self.close_group( depth, id )
      elif id[ 0 ] == self.SERIAL_GROUP:
        label, content = self._groups[ id ]
        self.open_group( depth, id, label, inGroup )
        b = set()
        e = set()
        self._processNodes( depth + 1, content, id, b, e, True, last )
        if serial:
          if first is None:
            first = b
          previous = None
          last = e
        else:
          begin.update( b )
          end.update( e )
        self.close_group( depth, id )
        
      if serial and previous is not None:
        for source in previous:
          for destination in last:
            if source != destination:
              self.create_link( source, destination )

              
    if serial and first:
      begin.update( first )
      end.update( last )


  def _create_job( self, depth, jobId, process, inGroup ):
    command = [ 'brainvisa', '-r', process.id() ]
    for name in process.signature.keys():
      value = str( getattr( process, name ) )
      command.append( value )
    self.create_job( depth, jobId, command, inGroup, label=process.name )
 
  def process_str(self, value):
    if value and value.find(' ') != -1:
      result = "\'"+value+"\'"
    else: 
      result = value
    return result

class GraphvizProcessToWorkflow( ProcessToWorkflow ):
  def __init__( self, process, output, clusters=True, files=True ):
    super( GraphvizProcessToWorkflow, self ).__init__( process )
    self.out = output
    self.links = set()
    self.clusters = clusters
    self.files = files
  
  
  def doIt( self ):
    print >> self.out, 'digraph "' + self.process.name + '" {'
    super( GraphvizProcessToWorkflow, self ).doIt()
    for source, destination in self.links:
      print >> self.out, '  ', source, '->', destination
    print >> self.out, '}'.edit( options )
  
    self.out.close()
  
  
  def create_job( self, depth, jobId, command, inGroup, label ):
    print 'create_job' + repr( ( depth, jobId, command, inGroup ) )
    print >> self.out, '  ' * depth, jobId, '[ shape=ellipse, label="' + label + '" ]'
  
  def open_group( self, depth, groupId, label, inGroup ):
    print 'open_group' + repr( ( depth, groupId, label, inGroup ) )
    if self.clusters:
      print >> self.out, '  ' * depth, 'subgraph cluster_' + str( groupId ), '{'
      if label:
        print >> self.out, '  ' * ( depth + 1 ), 'label = "' + label + '"'
  
  
  def close_group( self, depth, groupId ):
    print 'close_group' + repr( ( depth, groupId ) )
    if self.clusters:
      print >> self.out, '  ' * depth, '}'
  
  
  def create_input_file( self, fileId, fileName, fullPaths, databaseUuid, database_dir ):
    print 'create_input_file' + repr( ( fileId, fileName ) )
    if self.files:
      print >> self.out, '  ', fileId, '[ shape=diamond, label="' + os.path.basename( fileName ) + '" ]'


  def create_output_file( self, fileId, fileName, fullPaths, databaseUuid, database_dir ):
    print 'create_output_file' + repr( ( fileId, fileName ) )
    if self.files:
      print >> self.out, '  ', fileId, '[ shape=diamond, label="' + os.path.basename( fileName ) + '" ]'
  
  
  def create_link( self, source, destination ):
    print 'create_link' + repr( ( source, destination ) )
    if self.files or ( source[0] != self.FILE and destination[0] != self.FILE ):
      self.links.add( ( source, destination ) )


class ProcessToFastExecution( ProcessToWorkflow ):
  def __init__( self, process, output, clusters=True, files=True ):
    super( ProcessToFastExecution, self ).__init__( process )
    self.out = output
  
  
  def doIt( self ):
    super( ProcessToFastExecution, self ).doIt()
    self.out.close()

  
  def create_job( self, depth, jobId, command, inGroup, label ):
    print >> self.out, 'echo', ' '.join( repr(i) for i in command )
    print >> self.out, ' '.join( repr(i) for i in command )
  
  
  def open_group( self, depth, groupId, label, inGroup ):
    pass
  
  
  def close_group( self, depth, groupId ):
    pass
  
  
  def create_input_file( self, fileId, fileName, fullPaths, databaseUuid, database_dir ):
    pass


  def create_output_file( self, fileId, fileName, fullPaths, databaseUuid, database_dir ):
    pass
  
  
  def create_link( self, source, destination ):
    pass
  
  
  
class ProcessToSomaJobsWorkflow(ProcessToWorkflow):
  
  NO_FILE_PROCESSING = "no_file_processing"
  FILE_TRANSFER = "file_transfer"
  UNIVERSAL_RESOURCE_PATH = "universal_resource_path"
  
  def __init__( self, process, output, input_file_processing =  "no_file_processing", output_file_processing =  "no_file_processing", no_white_space = False ):
    super( ProcessToSomaJobsWorkflow, self ).__init__( process )
    self.__out = output
    
    self.__jobs = {}
    self.__file_transfers = {}
    self.__groups = {}
    self.__mainGroupId = None
    self.__dependencies =[]
    
    self.__input_file_processing = input_file_processing
    self.__output_file_processing = output_file_processing
    self.__no_white_space = no_white_space
      
    
  def doIt( self ):
    
    self.__jobs = {}
    self.__file_transfers = {}
    self.__groups = {}
    self.__mainGroupId = None
    self.__dependencies =[]
    
    #self.linkcnt = {}
    #self.linkcnt[(self.JOB, self.JOB)] = 0
    #self.linkcnt[(self.FILE, self.JOB)] = 0
    #self.linkcnt[(self.JOB, self.FILE)] = 0
    #self.linkcnt[(self.FILE, self.FILE)] = 0
    
    super( ProcessToSomaJobsWorkflow, self ).doIt()
    nodes = self.__jobs.values()
    dependencies = self.__dependencies
    mainGroup = self.__groups[self.__mainGroupId]
    groups = []
    for gid in self.__groups.keys():
      if not gid == self.__mainGroupId:
        groups.append(self.__groups[gid])
      
    workflow = Workflow(nodes, dependencies, mainGroup, groups)
    file = open(self.__out, "w")
    if file:
      pickle.dump(workflow, file)
      file.close()
      
      
    ##########################
    #print ">>> referenced input and output"
    #for n in workflow.nodes:
      #if isinstance(n, JobTemplate):
        #print "-------------"
        #print "    " + n.name
        #print "referenced inputs : " + repr(len(n.referenced_input_files)) 
        ##for r in n.referenced_input_files:
          ##print "   %30s                              %s" %(r.name,r.remote_path)
        #print "referenced outputs :" + repr(len(n.referenced_output_files)) 
        ##for r in n.referenced_output_files:
          ##print "   %30s                              %s" %(r.name,r.remote_path)
    #print "<<< referenced input and output"
    #print " "
    #print ">>> nodes"
    #for n in workflow.nodes:
      #print " " + n.name 
    #print "<<< nodes"
    #print " " 
    #print ">>> dependencies "
    #for d in workflow.dependencies:
      #print "   ( " + d[0].name + " , " + d[1].name + " ) "
    #print "<<< dependencies "
    #print " "
    #print ">>> main Group "
    #for el in workflow.mainGroup.elements:
      #print " " + el.name
    #print "<<< main Group "
    #print "  "
    #print ">>> groups "
    #for g in workflow.groups:
      #print "--------"
      #print " " + g.name
      #for el in g.elements: print "      " + el.name
    #print "<<< groups "
    ##########################
      
  def create_job( self, depth, jobId, command, inGroup, label ):
    if self.__no_white_space:
      new_command = []
      for command_el in command:
        new_command.append("\""+command_el+"\"")
      command = new_command
    #print 'create_job' + repr( ( depth, jobId, command, inGroup ) )
    self.__jobs[jobId] = JobTemplate(command=command, name_description=self.process_str(label))#jobId)#
    self.__groups[inGroup].elements.append(self.__jobs[jobId]) 
  
  def open_group( self, depth, groupId, label, inGroup ):
    #print 'open_group' + repr( ( depth, groupId, label, inGroup ) )
    self.__groups[groupId] = Group(elements = [], name = self.process_str(label))#groupId)#
    if not inGroup: 
      self.__mainGroupId = groupId
    else:
      self.__groups[inGroup].elements.append(self.__groups[groupId])
   
  def close_group( self, depth, groupId ):
    #print 'close_group' + repr( ( depth, groupId ) )
    pass
  
  
  
  def create_input_file( self, fileId, fileName, fullPaths = None, databaseUuid = None, database_dir = None ):
    
    if not self.__input_file_processing == self.NO_FILE_PROCESSING:
      #print 'create_input_file' + repr( ( fileId, os.path.basename( fileName ), fullPaths, databaseUuid, database_dir ) )
      global_out_file = None
      if self.__input_file_processing == self.FILE_TRANSFER:
        global_in_file=FileSending(remote_path = fileName, name = os.path.basename( fileName ), remote_paths = fullPaths)#fileId)# 
        self.__file_transfers[fileId]=global_in_file
      elif self.__input_file_processing == self.UNIVERSAL_RESOURCE_PATH:
        if databaseUuid and database_dir:
          global_in_file= UniversalResourcePath(relative_path = fileName[(len(database_dir)+1):], namespace = "brainvisa", uuid = databaseUuid)  
      
      if global_in_file:
        jobs_to_inspect=[]
        for job_id in self._iofiles[fileId][0]:
          if self.__input_file_processing == self.FILE_TRANSFER:
            self.__jobs[job_id].referenced_input_files.add(global_in_file)
          jobs_to_inspect.append(self.__jobs[job_id])
        for job_id in self._iofiles[fileId][1]:
          if self.__input_file_processing == self.FILE_TRANSFER:
            self.__jobs[job_id].referenced_output_files.add(global_in_file)
          jobs_to_inspect.append(self.__jobs[job_id])
        
        #print "job inspection: " + repr(len(jobs_to_inspect)) + " jobs."
        for job in jobs_to_inspect:
          #print "command : " + repr(job.command) 
          #print "file name : " + fileName
          while fileName in job.command:
            if isinstance(global_in_file, FileTransfer):
              job.command[job.command.index(fileName)] = (global_in_file, os.path.basename( fileName ).encode('utf-8'))
            else:
              job.command[job.command.index(fileName)] = global_in_file
          if job.stdin == fileName:
            job.stdin = global_in_file
          if job.stdout_file == fileName:
            job.stdout_file = global_in_file
          if job.stderr_file == fileName:
            job.stdout_file = global_in_file
    


  def create_output_file( self, fileId, fileName, fullPaths = None, databaseUuid = None, database_dir = None ):
    if not self.__output_file_processing == self.NO_FILE_PROCESSING:
      #print 'create_output_file' + repr( ( fileId, os.path.basename( fileName ), fullPaths, databaseUuid, database_dir ) )
      global_out_file = None
      if self.__output_file_processing == self.FILE_TRANSFER:
        global_out_file = FileRetrieving(remote_path = fileName,  name = os.path.basename( fileName ), remote_paths = fullPaths)#fileId)#
        self.__file_transfers[fileId]=global_out_file
      elif self.__output_file_processing == self.UNIVERSAL_RESOURCE_PATH:
        if databaseUuid and database_dir:
          global_out_file= UniversalResourcePath(relative_path = fileName[(len(database_dir)+1):], namespace = "brainvisa", uuid = databaseUuid)  
        
      if global_out_file:
        jobs_to_inspect=[]
        for job_id in self._iofiles[fileId][0]:
          if self.__output_file_processing == self.FILE_TRANSFER:
            self.__jobs[job_id].referenced_input_files.add(global_out_file)
          jobs_to_inspect.append(self.__jobs[job_id])
        for job_id in self._iofiles[fileId][1]:
          if self.__output_file_processing == self.FILE_TRANSFER:
            self.__jobs[job_id].referenced_output_files.add(global_out_file)
          jobs_to_inspect.append(self.__jobs[job_id])
          
        #print "job inspection: " + repr(len(jobs_to_inspect)) + " jobs."
        for job in jobs_to_inspect:
          #print "command : " + repr(job.command) 
          #print "file name : " + fileName
          while fileName in job.command:
            if isinstance(global_out_file, FileTransfer):
              job.command[job.command.index(fileName)] = (global_out_file, os.path.basename( fileName ).encode('utf-8'))
            else:
              job.command[job.command.index(fileName)] = global_out_file
          if job.stdin == fileName:
            job.stdin = global_out_file
          if job.stdout_file == fileName:
            job.stdout_file = global_out_file
          if job.stderr_file == fileName:
            job.stdout_file = global_out_file
    
  
  def create_link( self, source, destination ):
    #print 'create_link' + repr( ( source, destination ) )
    if source[0] == self.JOB and destination[0] == self.JOB: 
      self.__dependencies.append((self.__jobs[source], self.__jobs[destination]))
      #self.linkcnt[(self.JOB, self.JOB)] = self.linkcnt[(self.JOB, self.JOB)] +1
      #print repr(self.linkcnt[(self.JOB, self.JOB)]) +'     JOB  -> JOB  ' + repr( ( self.__jobs[source].name, self.__jobs[destination].name ) )
    elif self.__file_transfers:
      if source[0] == self.FILE and destination[0] == self.JOB:
        file = self.__file_transfers[source]
        job = self.__jobs[destination]
        job.referenced_input_files.add(file)
        #self.linkcnt[(self.FILE, self.JOB)] = self.linkcnt[(self.FILE, self.JOB)] +1
        #print repr(self.linkcnt[(self.FILE, self.JOB)]) +'     FILE -> JOB  ' + repr( (file.name, job.name ) ) + ' len(job.referenced_input_files) = ' + repr(len(job.referenced_input_files))
      elif source[0] == self.JOB and destination[0] == self.FILE: 
        job = self.__jobs[source]
        file = self.__file_transfers[destination]
        job.referenced_output_files.add(file)
        #self.linkcnt[(self.JOB, self.FILE)] = self.linkcnt[(self.JOB, self.FILE)] +1
        #print repr(self.linkcnt[(self.JOB, self.FILE)]) +'     JOB  -> FILE ' + repr( (job.name, file.name ) ) + ' len(job.referenced_output_files) = ' + repr(len(job.referenced_output_files))
      elif source[0] == self.FILE and destination[0] == self.FILE: 
        self.__dependencies.append((self.__file_transfers[source], self.__file_transfers[source]))
        #self.linkcnt[(self.FILE, self.FILE)] = self.linkcnt[(self.FILE, self.FILE)] +1
        #print repr(self.linkcnt[(self.FILE, self.FILE)]) +'     FILE -> FILE ' + repr( ( self.__file_transfers[source].name, self.__file_transfers[destination].name ) )
      

  
def process_to_workflow( process, output, input_file_processing = ProcessToSomaJobsWorkflow.NO_FILE_PROCESSING, output_file_processing = ProcessToSomaJobsWorkflow.NO_FILE_PROCESSING, no_white_space = False ):
  #ptwf = GraphvizProcessToWorkflow( process, output, clusters=clusters, files=files )
  #ptwf = ProcessToFastExecution( process, output )
  ptwf = ProcessToSomaJobsWorkflow(process, output, input_file_processing, output_file_processing, no_white_space)
  ptwf.doIt()


if __name__ == '__main__':
  import sys
  try:
    theProcess
  except NameError:
    from neuroProcesses import *
    theProcess = getProcessInstance( sys.argv[1] )
  #process_to_workflow(theProcess, open( 'test.dot', 'w' ), clusters = True, files = False)
  #process_to_workflow( theProcess, open( 'test.sh', 'w' ) )
  #process_to_workflow(theProcess, 'test.workflow')
  process_to_workflow(process = theProcess, output = sys.argv[2], input_file_processing = sys.argv[3], output_file_processing = sys.argv[4], no_white_space = sys.argv[5] == 'True')
  
  
  