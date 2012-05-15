# -*- coding: utf-8 -*-

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

'''
@author: Dominique Geffroy
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

from brainvisa.processing.qtgui.backwardCompatibleQt import QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QPushButton
from soma.qtgui.api import QtGUI
from soma.signature.qt4gui.signature_qt4gui import HasSignature_Qt4GUI
from soma.translation import translate as _t_

#------------------------------------------------------------------------------
class MatlabConfiguration_Qt4GUI( QtGUI ):
  '''
  This class adds a 'guess configuration' button to default GUI.
  '''
  def __init__( self, instance ):
    QtGUI.__init__( self, instance )
    self._defaultGUI = HasSignature_Qt4GUI( instance )
  
  
  def editionWidget( self, value, parent=None, name=None, live=False ):
    widget = QWidget( parent )
    if name:
      widget.setObjectName( name )
    layout = QVBoxLayout( )
    layout.setMargin(0)
    layout.setSpacing(6)
    self._defaultWidget = self._defaultGUI.editionWidget( value, parent=widget, live=live )
    layout.addWidget( self._defaultWidget )
    widget.setLayout(layout)

    layout2 = QHBoxLayout( )
    layout2.setMargin(0)
    layout2.setSpacing(6)
    spacer = QSpacerItem( 1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum )
    layout2.addItem( spacer )
    #self.btnGuess = QPushButton(  _t_( 'guess configuration' ), widget )
    #self.btnGuess.setEnabled( False )
    #layout2.addWidget( self.btnGuess )
    spacer = QSpacerItem( 1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum )
    layout2.addItem( spacer )
    
    layout.addLayout( layout2 )
    return widget
  
  
  def closeEditionWidget( self, editionWidget ):
    #self.btnGuess.deleteLater()
    self._defaultGUI.closeEditionWidget( self._defaultWidget )
    editionWidget.close()
    editionWidget.deleteLater()
  
  
  def setObject( self, editionWidget, value ):
    self._defaultGUI.setObject( self._defaultWidget, value )


  def updateEditionWidget( self, editionWidget, value ):
    self._defaultGUI.updateEditionWidget( self._defaultWidget, value )


_valid = None
_validchecked = None

