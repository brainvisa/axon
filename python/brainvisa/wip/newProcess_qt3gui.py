#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCIL license version 2 under
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
# knowledge of the CeCILL version 2 license and that you accept its terms.
from soma.signature.api import HasSignature
from soma.qtgui.api import QtGUI, ApplicationQtGUI, createWidget
from backwardCompatibleQt import QVBoxLayout
import os
from brainvisa.wip.newProcess import ExecutionContext


class NewProcess_Qt3GUI( QtGUI ):
  def editionWidget( self, object, parent=None, name=None, live=False ):
    self._processGUI = ApplicationQtGUI.instanceQt3GUI( object, HasSignature )
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
  
