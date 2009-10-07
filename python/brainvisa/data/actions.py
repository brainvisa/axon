# Copyright IFR 49 (1995-2009)
#
#  This software and supporting documentation were developed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL-B license under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the 
# terms of the CeCILL-B license as circulated by CEA, CNRS
# and INRIA at the following URL "http://www.cecill.info". 
# 
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability. 
# 
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or 
# data to be ensured and,  more generally, to use and operate it in the 
# same conditions as regards security. 
# 
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.

import os, shutil, re
import  neuroProcesses
import registration
import neuroHierarchy

###################################
class FileProcess:
  """
  Represents a process to execute on a file. 
  @type file: string
  @ivar file: the file to process
  @type action: Action
  @ivar action: the action to do to process the file
  @type selected: boolean
  @ivar selected: if the process is selected, the action will be executed by process method of a DBProcessor.
  @type pattern: regexp 
  @ivar pattern: regular expression that describes the files to process in the directory self.file
  @type files: list of string
  @ivar files: if pattern is not None, files corresponding to that pattern that have been treated by doit method. useful for undoCmd.
  """
  def __init__(self, file, action, pattern=None, diskItem=None):
    self.file=file
    self.diskItem=diskItem
    self.pattern=pattern
    if pattern is not None:
      self.pattern=re.compile(pattern)
    self.action=action
    if self.action:
      self.selected=True
    else: self.selected=False
  
  def filePattern(self):
    if self.pattern is not None:
      return os.path.join(self.file, self.pattern.pattern)
    else:
      return self.file
    
  def doit(self, debug=False, context=None):
    """
    Executes the action on the file.
    """
    self.files=[]
    ret=True
    if self.pattern is not None:
      if os.path.isdir(self.file):
        content=os.listdir(self.file)
        self.action.initialize() # must get directory content before intialize because initialize may create directories that must not be taken into acount
        for f in content:
          if  self.pattern.match(f):
            #if debug:
              #print "-- ", self.action.tooltip, str(self.action), " pattern:"+self.pattern.pattern+" [ ", os.path.join(self.file, f)," ]"
            if self.action.doit(os.path.join(self.file, f), debug=debug, context=context):
              self.files.append(f)
    elif self.diskItem: # a diskitem can represent several files
      self.action.initialize()
      if isinstance(self.action, CallProcess) or isinstance(self.action, SetTransformationInfo): # a process can use directly the diskitem, no use to call it for every file
        #if debug:
          #print "-- ", self.action.tooltip, str(self.action), " [ ", self.file," ]"
        if self.action.doit(self.file, debug=debug, context=context):
          self.files.append(self.file)
      else:
        for f in self.diskItem.existingFiles():
          #if debug:
            #print "-- ", self.action.tooltip, str(self.action), " [ ", f," ]"
          if self.action.doit(f, debug=debug, context=context):
            self.files.append(f)
    else:
      self.action.initialize()
      #if debug:
        #print "-- ", self.action.tooltip, str(self.action), " [ ", self.file," ]"
      if not self.action.doit(self.file, debug=debug, context=context):
        self.file=None
  
  def undoCmd(self):
    """
    Gets the command to undo the action. 
    @rtype : string
    @return: the undo command
    """
    cmd=""
    if self.pattern is not None:
      for f in self.files:
        cmd+=self.action.undoCmd(os.path.join(self.file, f))
    elif self.diskItem:
      for f in self.files:
        cmd+=self.action.undoCmd(f)
    elif self.file is not None:
      cmd = self.action.undoCmd(self.file)
    cmd+=self.action.finalizeUndo()
    return cmd
  
  def __getattr__(self, name):
    """
    Called when trying to access to name attribute, which is not defined. 
    Used to give a value to centralRef attribute first time it is accessed.
    """
    if name == "tooltip":
      return self.action.tooltip
    else:
      raise AttributeError
  
  def __str__(self):
    return self.action.__str__()
  
###################################
# classes to represent actions to do in order to convert a database
class Action(object):
  tooltip="Action"
  icon="run.png"
  def __init__(self):
    pass
  
  def initialize(self):
    pass
  
  def doit(self, file, debug=False, context=None):
    return True
    
  def undoCmd(self, file):
    return ""
 
  def finalizeUndo(self):
    return ""
 
  def __str__(self):
    return ""
###################################
class Move(Action):
  """
  Action to move src item to dest item. items can be files or directories. 
  If intermediate directories in dest don't exist they are created. 
  Paths must be explicite, * cannot be used instead of file name.
  It is possible to rename at the same time : 
  Examples : 
  Move(destDir).doit(srcDir/item) : srcDir/item -> destDir/item (not renamed)
  Move(destDir, None, newItem).doit(srcDir/item) : srcDir/item -> destDir/newItem (renamed with fixed name)
  Move(destDir, ".*", "\0-suffix").doit(srcDir/item) : srcDir/item -> destDir/item-suffix (renamed with a name related to src name)
  """
  tooltip="Move"
  icon="move.png"
  def __init__(self, dest, patternSrc=None, patternDest=None):
    """
    @type dest: string
    @param dest: directory where to move src
    @type patternSrc: string
    @param patternSrc: regular expression that will be matched on files to move
    @type patternDest: string
    @param patternDest: regular expression to expand the match object found on file to move in order to get the new name
    """
    super(Move, self).__init__()
    self.dest=dest
    self.newDirs=[]
    self.patternSrc=patternSrc
    self.patternDest=patternDest
    if patternSrc:
      self.patternSrc=re.compile(patternSrc)

  
  def initialize(self):
    # create directories to prepare the move
    dest=os.path.normpath(self.dest)
    # store intermediate created directories to undo
    while dest and not os.path.exists(dest):
      self.newDirs.append(dest)
      dest=os.path.dirname(dest)
    it=reversed(self.newDirs)
    for d in it:
      os.mkdir(d)
    
  def doit(self, src, debug=False, context=None):
    #print str(self)
    ret=True
    if self.patternSrc:
      match=self.patternSrc.match(os.path.basename(src))
      dest=os.path.join(self.dest, match.expand(self.patternDest))
    elif self.patternDest:
      dest=os.path.join(self.dest, self.patternDest)
    else: dest=os.path.join(self.dest, os.path.basename(src))
    if debug:
      if context is None:
        context=neuroProcesses.defaultContext()
      context.write("-- ", self.tooltip,  src, " -> ", dest)
    #print "move", src, "->",  dest
    # exception for graphs : must use AimsGraphConvert to copy .data with the graph
    if src[-4:]==".arg":
      os.system("AimsGraphConvert -i '"+src+"' -o '"+dest+"'")
      os.remove(src)
    else:
      if os.path.exists(dest):
        context.write( "!Warning MOVE : destination ", dest, " already exists ; move cancelled.")
        ret=False
        #if os.path.isdir(src):
          #shutil.rmtree(src)
        #else:
          #os.remove(src)
      else:
        shutil.move(src, dest)
    return ret
    
  def undoCmd(self, src):
    if self.patternSrc:
      match=self.patternSrc.match(os.path.basename(src))
      dest=os.path.join(self.dest, match.expand(self.patternDest))
    elif self.patternDest:
      dest=os.path.join(self.dest, self.patternDest)
    else: dest=os.path.join(self.dest, os.path.basename(src))
    if dest[-4:]==".arg":
      undo="os.system(\"AimsGraphConvert -i '"+dest+"' -o '"+src+"'\")\n"+"os.remove('"+dest+"')\n"
    else:
      undo="if not os.path.exists('"+dest+"'): print '!Warning MOVE : source "+dest+" do not exist, not moved to "+src+".'\n"+\
      "else: shutil.move('"+dest+"','"+src+"')\n"
    return undo
  
  def finalizeUndo(self): 
    undo=""
    for newDir in self.newDirs:
      undo+="shutil.rmtree('"+newDir+"')\n"
    self.newDirs=[]
    return undo
  
  def __str__(self):
    if self.patternDest:
      return os.path.join(self.dest, self.patternDest)
    return self.dest
  
###################################
class Remove(Move):
  tooltip="Remove"
  icon="remove.png"
  """
  This action doesn't really remove the file, it is moved to trash directory.
  """
  def __init__(self, srcDir=""):
    """
    src: directory in trash where to put files to remove
    """
    super(Remove, self).__init__(os.path.join("trash", srcDir))
    #print "Remove ", src, " in ", self.dest
    
################################### 
## terminer de remplacer avec FileProcess pour pouvoir remplacer une action par une autre...
class Mkdir(Action):
  tooltip="Create directory"
  icon="folder_new.png"
  def __init__(self):
    super(Mkdir, self).__init__()
    
  def doit(self, newDir, debug=False, context=None):
    if debug:
      if context is None:
        context=neuroProcesses.defaultContext()
      context.write("-- ", self.tooltip, newDir)
    #print str(self)
    os.mkdir(newDir)
    return True
    
  def undoCmd(self, newDir):
    return"shutil.rmtree('"+newDir+"')"
      
###################################
class CallProcess(Action):
  tooltip="Call process"
  
  def __init__(self, processName, *args, **kwargs):
    self.processName=processName
    self.args=args
    self.kwargs=kwargs
    
  def doit(self, file, debug=False, context=None, *args, **kwargs):
    if self.args:
      args=self.args
    if self.kwargs:
      kwargs=self.kwargs
    if debug:
      if context is None:
        context=neuroProcesses.defaultContext()
      context.write("")
      context.write( "-- ", str(self), args, kwargs)
    if context is None:
      neuroProcesses.defaultContext()
    try:
      context.runProcess(self.processName, *args, **kwargs)
    except Exception, e:
      context.warning("Error while executing "+self.processName+" : "+unicode(e.message))
    return True
    
  def __str__(self):
    return self.processName
###################################
class ImportData(CallProcess):
  tooltip="Import data"
  
  def __init__(self, item, dest=None):
    """
    @type item: DiskItem
    @param item: the data to import in the database
    @type dest: WriteDiskItem
    @param dest: where the data must be copied in the database
    """
    super(ImportData, self).__init__("GeneralImport")
    self.src=item
    self.dest=dest
  
  def initialize(self):
    self.newDir=None
    if not os.path.exists("trash"):
      os.mkdir("trash")
      self.newDir="trash"
      
  def doit(self, file, debug=False, context=None):
    # creates dest files from src files, deletes src files
    self.args=(self.src.fullPath(), self.dest, )
    if debug:
      if context is None:
        context=neuroProcesses.defaultContext()
      context.write("-- ", self.tooltip, self.args)
    super(ImportData, self).doit(None, debug, context)
    for f in self.src.existingFiles():
      shutil.move(f, "trash")
    return True

  def undoCmd(self, *args):
    cmd=""
    # delete dest files
    for f in self.dest.fullPaths():
      cmd+="shutil.move('"+f+"', 'trash')\n"
    destMinf=self.dest.minfFileName()
    cmd+="if os.path.exists('"+destMinf+"'): shutil.move('"+destMinf+"', 'trash')\n"
    # restore src files
    for f in self.src.fullPaths():
      cmd+="shutil.move(os.path.join('trash', os.path.basename('"+f+"')), '"+f+"')\n"
    srcMinf=self.src.minfFileName()
    trashSrcMinf=os.path.join('trash', os.path.basename(srcMinf))
    cmd+="if os.path.exists('"+trashSrcMinf+"'): shutil.move('"+trashSrcMinf+"', '"+srcMinf+"')\n"
    return cmd

  def finalizeUndo(self):
    undo=""
    if self.newDir is not None:
      undo+="shutil.rmtree('"+self.newDir+"')\n"
    self.newDir=None
    return undo
    
  def __str__(self):
    return unicode(self.dest.relativePath())

###################################
class SetTransformationInfo(Action):
  
  def __init__(self, transformation, sourceRef, destRef):
    self.transformation=transformation
    self.sourceRef=sourceRef
    self.destRef=destRef
    
  def doit(self, file, debug=False, context=None):
    if debug:
      if context is None:
        context=neuroProcesses.defaultContext()
      context.write("")
      context.write("-- ", str(self), self.transformation, " : ")
      context.write(self.sourceRef, " -> ", self.destRef  )
    tm=registration.getTransformationManager()
    if not self.sourceRef.isReadable():
      tm.createNewReferential(self.sourceRef)
    if not self.destRef.isReadable():
      tm.createNewReferential(self.destRef)
    tm.setNewTransformationInfo( self.transformation, source_referential = self.sourceRef, destination_referential = self.destRef )
    return True
    
  def __str__(self):
    return _t_("set transformation info")

 