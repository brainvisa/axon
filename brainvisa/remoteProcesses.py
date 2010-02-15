#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL license version 2 under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the 
# terms of the CeCILL license version 2 as circulated by CEA, CNRS
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
# knowledge of the CeCILL license version 2 and that you accept its terms.
from remoteToolkit import *
import neuroConfig
import pickle

#--------------------------------------------------------------------------
class ProcessInfos:
  """
  Generate and stores the needed informations to execute a BrainVISA process in console mode.
  """

  def __init__(self, process, processParams):
    """
    Retrieves and format the informations needed to run a process.
    
    @param process: Can either be a BrainVISA ExecutionNode or a the process name.
    @param processParams: Dictionnary containing the process arguments. Define only
    if the parameter 'process' refers to the process name. Leave empty otherwise.
    """
    
    self.processName = ''
    """
    The process name.
    """
    
    self.processParams = ''
    """
    The process parameters stored in a string.
    The parameters are separated by comas and preceded by the relevant keyword.
    """

    if type(process) is str:
      self.processName = process
      paramsDict = processParams
    else:
      self.processName = process.id()
      paramsDict = process.signature  
    
    for key in paramsDict.keys():
    
      if type(process) is str:
        arg = paramsDict[key]
      else:
        arg = str(eval('process.' + key))
            
      if arg == 'None':
        pass
      else:
        self.processParams = self.processParams + key + "='" + arg + "'," 
     
  def getParams(self):
    """
    @return: The process parameters.
    
    @note: Example: keyword_1='arg_1', keyword_2='arg_2', ..., keyword_n='arg_n'
    """
    
    return self.processParams.strip('\r\n')
    
  def getName(self):
    """
    @return: The process name.
    """
    
    return self.processName

#--------------------------------------------------------------------------
def getClusterInstance(context):
  """
  Gets a local or remote CentralizedClusterManager instance, depending on what is available. 
  
  @return: The CentralizedClusterManager instance and the mode the instance is using (server or not).
  
  @see: L{remoteToolkit.CentralizedClusterManager}, L{CCMServer.CCMServer}
  """ 
       
  isServer = True
    
  context.write('Connecting to Cluster Infos Server...')
      
  try:
    cluster = Pyro.core.getProxyForURI("PYRONAME://clusterManager")
    return cluster, isServer
       
  except:
    context.write('Server not responding, probing cluster from local computer...')
    cluster = CentralizedClusterManager(homedir=neuroConfig.homeBrainVISADir)
    isServer = False
    return cluster, isServer

#--------------------------------------------------------------------------
class RemoteConnectionError(Exception):
  def __init__(self, message):
    super(RemoteConnectionError, self).__init__(message)
    
class RemoteProcessCall( threading.Thread ):
  """
  Starts a new BrainVISA on the specified host and then runs the wanted process on it.
  """
  
  def __init__(self, rpid, cluster, context, process, **processParams):
    """
    Initialize instance variables.
    """

    self.rpid = rpid
    """
    Remote brainvisa Process ID.
    
    @note: basically the iteration number.
    """
    
    self.host = cluster.getHost()
    """
    The host IP.
    """
    
    self.context = context
    """
    Context.
    """
       
    procInfos = ProcessInfos(process, processParams)
    
    self.ProcessName = procInfos.getName()
    """
    The process name.
    @see: L{ProcessInfos}
    """
    
    self.ProcessParameters = procInfos.getParams()
    """
    The process parameters.
    @see: L{ProcessInfos}
    """

    self.process = process

    #self.isRunning = True
    
    context.remote.updateGUI(self.host, self.rpid)
    self.exception=None
    threading.Thread.__init__(self)
    
  def run(self):
    """
    Launches the process and retrieves messages appearing on the remote context.

    The messages are written on a pipe.
    """

    host     = self.host
    if host == 'localhost':
      print 'local threaded execution for', self.ProcessName
      self.context.remote.write('%d | %s | local execution'%(self.rpid,host ) )
      try:
        self.process.run( self.context )
        return 1
      except Exception, e:
        print 'error:', e
        self.context.remote.write('%d | %s | Error'%(self.rpid,host) )
        self.exception = e
        return 0

    remoteShell = sshSession(host, UserInfos.login, UserInfos.password)
    if remoteShell is None:
      self.exception=RemoteConnectionError("SSH connection error.")
      return 0


    if neuroConfig.app.configuration.distributed_execution.remoteExecutable \
      =='':
      brainvisa_exec = sys.argv[0]
    else:
      brainvisa_exec = \
        neuroConfig.app.configuration.distributed_execution.remoteExecutable

    remoteShell.sendline(brainvisa_exec+' -b --shell --logFile ' + neuroConfig.homeBrainVISADir + '/brainvisa_%d.log'%self.rpid )
    case = remoteShell.expect(['.*prints more.', TIMEOUT], timeout=60)
    if case == 1:
      remoteShell.close()
      self.context.remote.write('%d | %s | Brainvisa failed to launch, restarting...'%(self.rpid,host) )
      time.sleep(10)
      if self.checkInterruption():
        return 0
      else:
        self.run() 
        return 0
    else:

      print "Brainvisa now is running on %s"%(host)
      try:
        #self.pid = self.__getpid(remoteShell)
        startTime = time.localtime()
        import neuroProcesses

        #print host, ": runProcess('" + self.ProcessName + "' ," + self.ProcessParameters + ")"

        from brainvisa.history import ProcessExecutionEvent
        import tempfile
        tmp = tempfile.mkstemp( '.bvproc', 'process', neuroConfig.homeBrainVISADir )
        event = ProcessExecutionEvent()
        event.setProcess( self.process._process )
        remoteShell.sendline('from neuroProcesses import *')
        remoteShell.sendline('import os')
        event.save( tmp[1] )
        os.close( tmp[0] )
        remoteShell.sendline('p = getProcessInstance( ' + repr( tmp[1] ) + ' )' )
        remoteShell.sendline('os.unlink( ' + repr( tmp[1] ) + ' )' )
        remoteShell.sendline('defaultContext().runProcess( p )')
      except Exception, e:
        print 'error:', e
        self.context.remote.write('%d | %s | %s'%(self.rpid,host,str(e)) )
        return 0

      modulo = 0

      while 1:
        case = remoteShell.expect(['.*ERROR.*','.*Error.*','.*\d{2}:\d{2}.*\(\d+.*',
                                   '.*warning:.*\r\n', '.*Exception.*\r\n','.*\r\n', TIMEOUT], timeout=10)


        # check interruption (every 10 seconds at most)
        if self.checkInterruption():
          remoteShell.close(True)
          return 0
        
        if case == 6:
          # TIMEOUT case
          # In order to give some feedback to the user (if none is given by default by the process),
          # a message with the current execution time is displayed every 5 minutes approximately.
          modulo += 1
          if modulo % 30 == 0:
            currentTime = time.localtime()
            self.context.remote.write('%d | %s | %s'%(self.rpid,host,calcTimeDiff(startTime, currentTime)) )
          continue
        
        message = remoteShell.after.strip('\r\n')
        #print host, 'message:', message
        modulo = 0
                                                                                                                                                                                                      
        if case == 0:
          print 'ERROR || %d : %s - %s'%(self.rpid,host,message)
          
          self.context.remote.write('%d | %s | Error, check console for further information'%(self.rpid,host) )
          
          remoteShell.close(True)
          self.exception = RuntimeError( _t_( 'Remote execution error: check console for further information' ) )
          return 0
          
        elif case == 1:
          print 'ERROR || %d : %s - %s'%(self.rpid,host,message)
          
          self.context.remote.write('%d | %s | Error, check console for further information'%(self.rpid,host) )
          
          remoteShell.close(True)
          self.exception = RuntimeError( _t_( 'Remote execution error: check console for further information' ) )
          return 0
          
        elif case == 2:
          regexp = re.compile('.*\d{2}:\d{2}.*\(\d+.*')
          result = regexp.findall(message)
          message = result[0]
            
          self.context.remote.write('%d | %s | %s'%(self.rpid,host,message) )
          
          remoteShell.sendline('%Exit')
          remoteShell.expect('Closing threads... Done.')
          remoteShell.sendline('exit')
          
          remoteShell.close(True)
          return 1
          
        elif case == 3:
          # ignore warnings
          pass
        elif case == 4:
          # exception
          print 'ERROR || %d : %s - %s'%(self.rpid,host,message)
          
          self.context.remote.write('%d | %s | Error, check console for further information'%(self.rpid,host) )
          remoteShell.close(True)
          self.exception = RuntimeError( _t_( 'Remote execution error: check console for further information' ) )
          return 0
          
        elif case == 5:
          #if self.__filterMessage(message) == 'Message':
          self.context.remote.write('%d | %s | %s'%(self.rpid,host,message) )
          #else:
            ## ignore other messages
            #pass
        else:
          # state theoritically impossible to reach
          print 'Something (bad) happened'
          remoteShell.close(True)
          self.exception = RuntimeError( _t_( 'Remote execution error: ' \
          'Something (bad) happened' ) )
          return 0
          
      return 0
                
  def checkInterruption(self):
    try:
      self.context.checkInterruption()
    except Exception, e:
      self.context.remote.write('%d | %s | Process interrupted'%(self.rpid,self.host) )
      self.context._setInterruptionRequest( self.context.UserInterruption() )
      self.exception = e
      return True
    else:
      return False
  
  def __filterMessage(self, msg):
    """
    Sorts messages from the remote context into different types.
    
    @param msg: Message to identify.
    @return: String defining the type of the message.
    """

    if msg.find('from neuroProcesses import *') != -1:
      return 'Init'
    elif msg.find('context = ExecutionContext()') != -1:
      return 'Init'
    elif msg.find('warning') != -1:
      return 'Warning'
    elif msg.find('Warning') != -1:
      return 'Warning'
    elif msg == '':
      return 'Null'
    else:
      regexp = re.compile('\w+=\'\w+\'')    # lines looking like: a_word='something'
      result = regexp.findall(msg)
      if result == []:
        return 'Message'
      else:
        return 'Params'
  """      
  def __getpid(self, remoteShell):
    remoteShell.sendline('import os')
    remoteShell.sendline("print 'pid', os.getpid()")
      
    remoteShell.expect(['pid.*\d+'], timeout=None)

    pid_pattern = re.compile('\d+')
    pid_str = pid_pattern.findall(remoteShell.after)

    return string.atoi(pid_str[0])
  """

#--------------------------------------------------------------------------
class RemoteContext( QObject ):
  """
  Write remote Brainvisa messages on a QListView in the graphical interface.
  """
  
  def __init__(self):
    
    QObject.__init__(self)
    self.ipList = []
    
    #self.processList = {}
    #self.ipList = {}
    
  def write(self, *messages):
    for msg in messages:
      self._write(msg)
      
  def _write(self, remoteMsg):
    """
    Parses the remote message to extract the id of the Brainvisa process and the machine it is running on.
    The message is then sent through a Qt signal to the graphical interface.
    """
              
    regexp = re.compile('[|]')
    result = regexp.split(remoteMsg)
      
    try:
      pid = result[0].strip(' ')
      ip  = result[1].strip(' ')
      regexp = re.compile('\r\n')
      msg = regexp.sub( ' ', result[2])
    except IndexError:
      pass
    else:
      regexp = re.compile('.*\d{2}:\d{2}.*\(\d+.*')
      finish_msg = regexp.findall(msg)
        
      regexp = re.compile('Error|interrupted')
      error_msg = regexp.findall(msg)
      from neuroProcessesGUI import mainThreadActions
      mainThreadActions().push( self.emit, PYSIGNAL("SIG_setProcessStatus"), (pid, ' Running...') )
      mainThreadActions().push( self.emit, PYSIGNAL("SIG_setCurrentMessage"), (pid, msg) )
      mainThreadActions().push( self.emit, PYSIGNAL("SIG_addMessage"), (pid, msg) )
        
      try:
        finish_msg = finish_msg[0]
      except IndexError:
        pass
      else:
        mainThreadActions().push( self.emit, PYSIGNAL("SIG_setProcessStatus"), (pid, ' Finished') )
        mainThreadActions().push( self.emit, PYSIGNAL("SIG_setCurrentMessage"), (pid, '') )
        
      try:
        error_msg = error_msg[0]
      except IndexError:
        pass
      else:
        mainThreadActions().push( self.emit, PYSIGNAL("SIG_setProcessStatus"), (pid, ' Error') )
  
  def updateGUI(self, ip, pid):
    """
    Updates the QListView displaying the remote Brainvisa messages.
    
    @param ip: address of the remote machine the process is working on.
    @param pid: pid of the process.
    """
    
    try:
      self.ipList.index(ip)
    except ValueError:
      self.ipList.append(ip)
      self.emit(PYSIGNAL("SIG_addIP"), (ip,) )
      
    # A little delay seems to be mandatory here, as the signals are asynchronous.
    # The addProcess function may otherwise be executed before addIP, which would crash the program.
    time.sleep(0.1)   
    self.emit(PYSIGNAL("SIG_addProcess"), (ip, pid) )
    
  def clearGUI(self):
    """
    Clears the QListView displaying the remote Brainvisa messages.
    """  
    
    self.ipList = []
    self.emit(PYSIGNAL("SIG_clear"), () )

#----------------------------------------------------------------------------
def calcTimeDiff( startTime, finalTime):
  """
  Returns as a string the time elapsed between two markers.
    
  @param startTime: start marker.
  @param finalTime: end marker.
  
  @note: It is basically the same function as soma.somatime.timeDifferenceToString.
  """
  
  difference = calendar.timegm( finalTime ) - calendar.timegm( startTime )  
  
  days = int( difference / 86400 )
  difference -= days * 86400
  hours = int( difference / 3600 )
  difference -= hours * 3600
  minutes = int( difference / 60 )
  seconds = int( difference - minutes * 60 )
  result = ''
  if days:
    return( _t_( '%d days %d hours %d minutes %d seconds' ) % ( days, hours, minutes, seconds ) )
  if hours:
    return( _t_( '%d hours %d minutes %d seconds' ) % ( hours, minutes, seconds ) )
  if minutes:
    return( _t_( '%d minutes %d seconds' ) % ( minutes, seconds ) )
  return( _t_( '%d seconds' ) % ( seconds, ) )
  

#--------------------------------------------------------------------------
class UserInfosBV( UserInfos ):
  """
  Stores informations about the user needed to open ssh tunnels.
  Asks for the password in a BV dialog. 
  """
  
  def __init__(self, context, signature):
    
    self.accepted = True
    self.context = context
    self.signature = signature
    UserInfos.__init__(self)  
    
  def _askPass(self): 
    """
    Asks for user password and checks its validity.
    
    @see: L{remoteToolkit.UserInfos._checkPass}
    """
    
    dlg = self.context.dialog(1,'SSH password', self.signature, ('Ok', self._accept), ('Cancel',self._cancel))
    dlg.call()
    
    if self.accepted:
      UserInfos.password = dlg.getValue('Password')
      
      if not self._checkPass(UserInfos.password):
        return self._askPass()
      return True 
       
    else:
      return False
          
  def _accept(self, userDialog):
    userDialog.close(1)
    self.accepted = True

  def _cancel(self, userDialog):
    userDialog.close(1)
    self.accepted = False  
      
  def isAccepted(self):
    return self.accepted    
