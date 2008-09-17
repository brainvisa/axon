from soma.signature.api import HasSignature
from soma.qt3gui.api import ApplicationQt3GUI
from soma.singleton import Singleton
from soma.translation import translate as _
from qt import SIGNAL
import sys, time
from threading import RLock
import neuroProcesses, neuroProcessesGUI

class ExecutionContext( object ):
  class Session( object ):
    '''
    '''
  
  
  class FileBuffer( object ):
    def __init__( self ):
      self.__lock = RLock()
      self.__buffer = []
    
    
    def write( self, text ):
      self.__lock.acquire()
      try:
        self.__buffer.append( text )
      finally:
        self.__lock.release()
      
      
    def read( self ):
      self.__lock.acquire()
      try:
        result = ''.join( self.__buffer )
        self.__buffer = []
      finally:
        self.__lock.release()
      return result
    

class ConsoleExecutionContext( Singleton, ExecutionContext ):
  class Session( ExecutionContext.Session ):
    def __init__( self ):
      self.stdout = sys.stdout
      self.stderr = sys.stderr

  def __singleton_init__( self ):
    super( Singleton, self ).__init__()

  
  def createSession( self ):
    return self.Session()


class GUIExecutionContext( ExecutionContext ):
  class Session( ExecutionContext.Session ):
    def __init__( self ):
      self.stdout = ExecutionContext.FileBuffer()
      self.stderr = ExecutionContext.FileBuffer()

  def __init__( self ):
    super( GUIExecutionContext, self ).__init__()
    self.__session = None
  
  
  def createSession( self ):
    self.__session = self.Session()
    return self.__session


class NewProcess( HasSignature ):
  def __init__( self ):
    super( NewProcess, self ).__init__()
    self.userContext = GUIExecutionContext().createSession()
  
  
  @staticmethod
  def onlineDocumentationSource():
    return None
  
  
  @staticmethod
  def onlineDocumentationHTML():
    return '<h2>This process is not documented</h2>'


  def show( self, *args, **kwargs ):
    appGUI = ApplicationQt3GUI()
    self._qtGUI = appGUI.instanceQt3GUI( self )
    self._editionWidget = self._qtGUI.editionWidget( self, live=True )
    self._editionWidget.btnRun.connect( self._editionWidget.btnRun, SIGNAL( 'clicked()' ), self.__call__ )
    self._editionWidget.show()


  def __call__( self ):
    print >> self.userContext.stdout, '<font color=blue>Process <b>%(name)s</b> started on %(time)s</font>' % \
      { 'name': self.name, 'time': time.strftime( _( '%Y/%m/%d %H:%M' ) ) }
    self.run()
    print >> self.userContext.stdout, '<font color=blue>Process <b>%(name)s</b> stopped on %(time)s</font>' % \
      { 'name': self.name, 'time': time.strftime( _( '%Y/%m/%d %H:%M' ) ) }
    self._editionWidget.tedInfo.append( self.userContext.stdout.read() )
  
  
  @classmethod
  def registerInBrainVISA( cls ):
    nameList = cls.name.split( '/' )
    if nameList and not nameList[0]:
      nameList = nameList[ 1: ]
    tree = nameList[ 0 ]
    branches = nameList[ 1:-1 ]
    leaf = nameList[ -1 ]
    
    # Find or create ProcessTree
    for processTree in neuroProcessesGUI._mainWindow.processTrees.model:
      if processTree.name == tree:
        break
    else:
      processTree = neuroProcesses.ProcessTree( name=tree, editable=False, user=False )
      neuroProcessesGUI._mainWindow.processTrees.model.append( processTree )
    # Find or create branches
    currentBranch = processTree
    for branch in branches:
      for newBranch in currentBranch:
        if newBranch.name == branch:
          break
      else:
        newBranch = processTree.Branch( name=branch, editable=False )
        currentBranch.append( newBranch )
      currentBranch = newBranch
    # Insert process
    currentBranch.append( processTree.Leaf( processId=cls, 
                                            icon='icon_process_3.png', 
                                            name=leaf,
                                            editable=False ) )
