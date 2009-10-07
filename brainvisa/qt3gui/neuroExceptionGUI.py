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

from backwardCompatibleQt import *
from soma.qtgui.api import TextEditWithSearch

class ShowException( QDialog ):
  _theExceptionDialog = None 
  
  def __init__( self, messageHTML, detailHTML, parent = None, caption=None ):
    QDialog.__init__( self, parent, None, False, Qt.WType_Dialog + Qt.WGroupLeader + Qt.WShowModal )
#    QVBox.__init__( self, parent, None, Qt.WType_Dialog + Qt.WGroupLeader + Qt.WShowModal )
    layout = QVBoxLayout( self )
    
    layout.setMargin( 10 )
    layout.setSpacing( 5 )
    if caption is None:
      caption = _t_( 'Error' )
    self.setCaption( caption )
    self.teHTML = TextEditWithSearch( self )
    self.teHTML.setReadOnly( True )
    layout.addWidget( self.teHTML )
    self.teHTML.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding ) )
    self.messageHTML = [ messageHTML ] 
    self.detailHTML = [ detailHTML ]
    self.advancedMode = False
    self.updateText()
        
    hb = QHBoxLayout( layout )
#    layout.addLayout( hb )
    self.btnOk = QPushButton( _t_( 'Ok' ), self )
    hb.addWidget( self.btnOk )
    self.btnOk.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    self.btnOk.setDefault( True )
    self.btnOk.setAutoDefault( True )
    self.connect( self.btnOk, SIGNAL( 'clicked()' ), self, SLOT( 'close()' ) )
    
    self.btnAdvanced = QPushButton( _t_( 'more info' ), self )
    hb.addWidget( self.btnAdvanced )
    self.btnAdvanced.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    self.connect( self.btnAdvanced, SIGNAL( 'clicked()' ), self.changeAdvancedMode )
    self.updateText()
    
    self.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding ) )
    self.resize( 640, 400 )
    ShowException._theExceptionDialog = self

  
  def changeAdvancedMode( self ):
    if self.advancedMode:
      self.advancedMode = False
      self.btnAdvanced.setText( _t_( 'more info' ) )
    else:
      self.advancedMode = True
      self.btnAdvanced.setText( _t_( 'hide info' ) )
    self.updateText()
      
  def updateText( self ):
    if self.advancedMode:
      self.teHTML.setText( '<hr>\n'.join( [i + '<hr>\n' + j for i, j in zip( self.messageHTML, self.detailHTML) ] ) )
    else:
      self.teHTML.setText( '<hr>\n'.join( self.messageHTML ) )
    self.teHTML.scrollToBottom()
    
  
  def appendException( self, messageHTML, detailHTML ):
    self.messageHTML.append( messageHTML )
    self.detailHTML.append( detailHTML )
    self.updateText()
    
  def close( self, alsoDelete ):
    self.hide()
    ShowException._theExceptionDialog = None
    return 1
  
