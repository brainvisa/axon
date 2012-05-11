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
from soma.signature.api import HasSignature
from soma.qtgui.api import ApplicationQtGUI
from soma.singleton import Singleton
from soma.translation import translate as _
from brainvisa.processes.qtgui.backwardCompatibleQt import SIGNAL
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
    appGUI = ApplicationQtGUI()
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
