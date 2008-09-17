from soma.signature.api import HasSignature
from soma.qt3gui.api import Qt3GUI, ApplicationQt3GUI, createWidget
from qt import QVBoxLayout
import os
from brainvisa.wip.newProcess import ExecutionContext


class NewProcess_Qt3GUI( Qt3GUI ):
  def editionWidget( self, object, parent=None, name=None, live=False ):
    self._processGUI = ApplicationQt3GUI.instanceQt3GUI( object, HasSignature )
    editionWidget = createWidget( os.path.join( os.path.dirname( __file__ ), 'newProcess.ui' ), parent=parent, name=name )
    # TODO: set layout to editionWidget.processContainerWidget
    editionWidget.processContainerWidget._layout = QVBoxLayout( editionWidget.processContainerWidget, 0, 5 )
    editionWidget.processContainerWidget._layout.setAutoAdd( True )
    self._processWidget = self._processGUI.editionWidget( object, parent=editionWidget.processContainerWidget, live=live )
    return editionWidget
  
  def closeEditionWidget( self, editionWidget ):
    self._processGUI.closeEditionWidget( self._processWidget )
    self._processWidget = None
    self._processGUI = None
  
  
  def setObject( self, editionWidget, object ):
    self._processGUI.setObject( self._processWidget, object )

  
  def updateEditionWidget( self, editionWidget, object ):
    '''
    Update C{editionWidget} to reflect the current state of C{object}.
    This method must be defined for both mutable and immutable DataType.
    '''
    self._processGUI.updateEditionWidget( self._processWidget, object )
  
