#  This software and supporting documentation are distributed by
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
from neuroData import *
from neuroDataGUI import *
from backwardCompatibleQt import *
import qwt
from brainvisa.multiplot import MultiPlot
import neuroConfig
from neuroException import HTMLMessage

def floatString( floatValue ):
  result = str( floatValue )
  if result[ -2 : ] == '.0':
    return result[ :-2 ]
  return result
  

class ParadigmEditor( QHBox, DataEditor ):
  def __init__( self, parent=None, name=None ):
    if getattr( ParadigmEditor, 'pixShow', None ) is None:
      setattr( ParadigmEditor, 'pixShow', QPixmap( \
        os.path.join( neuroConfig.iconPath, 'eye.png' ) ) )
    QHBox.__init__( self, parent, name )

    self._view = None
    
    self.label = QLabel( _t_( '%d conditions' ) % 0, self )
    self.btn = QPushButton( _t_( 'Edit' ), self )
    self.btn.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    self.connect( self.btn, SIGNAL( 'clicked()' ), self._selectValues )
    self.btnShow = QPushButton( self )
    self.btnShow.setPixmap( self.pixShow )
    self.btnShow.setSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed )
    self.connect( self.btnShow, SIGNAL( 'clicked()' ), self._showPressed )
    self.setValue( None, 1 )

  def getValue( self ):
    return self.value
  
  def setValue( self, value, default = 0 ):
    if value is None:
      conditionCount = 0
    else:
      conditionCount = len( value )
    self.label.setText( _t_( '%d conditions' ) % conditionCount )
    self.value = value
    self.emit( PYSIGNAL('newValidValue'), ( self.name(), self.value, ) )
    if not default: self.emit( PYSIGNAL('noDefault'), ( self.name(),) )

  def _selectValues( self ):
    self._paradigmDialog = ParadigmDialog( value=self.getValue(), parent = self.parent() )
    self._paradigmDialog.show()
    self.connect( self._paradigmDialog, PYSIGNAL( 'accept' ), self.setValue )

  def _showPressed( self ):
    if self._view is not None:
      self._view.hide()
      self._view.show()
      self._view.raiseW()
    else:
      self._view = MultiPlot()
      for condition, onsets in self.getValue():
        p = self._view.addPlot( condition )
        x = [0]
        y = [0]
        for time, length, amp in onsets:
          x += [ time, time+length ]
          y += [ amp, 0 ]
        self._view.setData( p, x, y )
      self._view.show()
 
      

    
class ParadigmDialog( QVBox ):
  def __init__( self, value=None, parent=None, name=None ):
    if getattr( ParadigmDialog, 'pixUp', None ) is None:
      setattr( ParadigmDialog, 'pixUp', 
        QPixmap( os.path.join( neuroConfig.iconPath, 'up.png' ) ) )
      setattr( ParadigmDialog, 'pixDown', 
        QPixmap( os.path.join( neuroConfig.iconPath, 'down.png' ) ) )
    QVBox.__init__( self, parent, name, Qt.WType_Dialog + Qt.WGroupLeader )

    self.setSpacing( 5 )
    
    self.lvConditions = QListView( self )
    self.lvConditions.setAllColumnsShowFocus( 1 )
    self.lvConditions.addColumn( _t_( 'Condition' ) )
    self.lvConditions.addColumn( _t_( 'Onsets' ) )
    self.lvConditions.setColumnWidth( 1,300)
    self.lvConditions.setSorting( -1 )
    self.lvConditions.setDefaultRenameAction( QListView.Accept )
    self.lvConditions._ignoreSelected = 0
    self.connect( self.lvConditions,
                  SIGNAL( 'selectionChanged( QListViewItem * )' ),
                  self._conditionSelected )
    self.connect( self.lvConditions,
                  SIGNAL( 'itemRenamed (QListViewItem *,int,const QString &)' ),
                  self._conditionRenamed )

    hb = QHBox( self )
    hb.setSpacing( 5 )

    self.btnAddCondition = QPushButton( _t_( 'Add' ), hb )
    self.connect( self.btnAddCondition, SIGNAL( 'clicked()' ), self._addCondition )

    self.btnRemoveCondition = QPushButton( _t_( 'Remove' ), hb )
    self.btnRemoveCondition.setEnabled( 0 )
    self.connect( self.btnRemoveCondition, SIGNAL( 'clicked()' ), self._removeCondition )

    self.btnUpCondition = QPushButton( hb )
    self.btnUpCondition.setPixmap( self.pixUp )
    self.btnUpCondition.setEnabled( 0 )
    self.connect( self.btnUpCondition, SIGNAL( 'clicked()' ), self._upCondition )

    self.btnDownCondition = QPushButton( hb )
    self.btnDownCondition.setPixmap( self.pixDown )
    self.btnDownCondition.setEnabled( 0 )
    self.connect( self.btnDownCondition, SIGNAL( 'clicked()' ), self._downCondition )

    hb = QHBox( self )
    hb.setSpacing(6)
    hb.setMargin(6)
    spacer = QSpacerItem(20,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
    hb.layout().addItem( spacer )
    btn = QPushButton( _t_( 'Ok' ), hb )
    self.connect( btn, SIGNAL( 'clicked()' ), self._ok )
    btn = QPushButton( _t_( 'Cancel' ), hb )
    self.connect( btn, SIGNAL( 'clicked()' ), SLOT( 'close()' ) )

    neuroConfig.registerObject( self )
    self.setValue( value )
    
  def setValue( self, value ):
    print '!ParadigmDialog.setValue!', value
    self.lvConditions.clear()
    if value is None: return
    for condition, onsets in value:
      onsetsText = ''
      for time, length, amp in onsets:
        onsetsText += ' ' + floatString( time )
        if length != 0.0:
          onsetsText += ':' + floatString( length )
        if amp != 1.0:
          onsetsText += ':' + floatString( amp )
      item = QListViewItem( self.lvConditions, condition, onsetsText )
      item.setRenameEnabled( 0, 1 )
      item.setRenameEnabled( 1, 1 )
      self._moveCondition( item, self.lvConditions.lastItem() )
      
  def close( self, alsoDelete ):
    neuroConfig.unregisterObject( self )
    return QHBox.close( self, alsoDelete )

  def _conditionSelected( self, item ):
    if self.lvConditions._ignoreSelected: return
    if item is None:
#      self.btnEditCondition.setEnabled( 0 )
      self.btnRemoveCondition.setEnabled( 0 )
      self.btnUpCondition.setEnabled( 0 )
      self.btnDownCondition.setEnabled( 0 )
    else:
#      self.btnEditCondition.setEnabled( 1 )
      self.btnRemoveCondition.setEnabled( 1 )
      if item.itemAbove() is not None:
        self.btnUpCondition.setEnabled( 1 )
      else:
        self.btnUpCondition.setEnabled( 0 )
      if item.itemBelow() is not None:
        self.btnDownCondition.setEnabled( 1 )
      else:
        self.btnDownCondition.setEnabled( 0 )
      self.lvConditions.setSelected( item, 1 )
      
  def _addCondition( self ):
    item = QListViewItem( self.lvConditions, _t_( 'New Condition' ) )
    item.setRenameEnabled( 0, 1 )
    item.setRenameEnabled( 1, 1 )
    qApp.processEvents()
    self._moveCondition( item, self.lvConditions.lastItem() )
    item.startRename( 0 )
   
  def _removeCondition( self ):
    item = self.lvConditions.currentItem()
    next = item.itemBelow()
    if next is None:
      next = item.itemAbove()
    self.lvConditions.takeItem( item )
    self._conditionSelected( next )

  def _upCondition( self ):
    item = self.lvConditions.currentItem()
    other = item.itemAbove().itemAbove()
    self._moveCondition( item, other )
    
  def _downCondition( self ):
    item = self.lvConditions.currentItem()
    other = item.itemBelow()
    self._moveCondition( item, other )

  def _moveCondition( self, item, other ):
    if self.lvConditions.childCount() < 2:
      return
    self.lvConditions._ignoreSelected = 1
    try:
      self.lvConditions.takeItem( item )
      items = []
      if other is None: items.append( item )
      current =  self.lvConditions.firstChild()
      while current is not None:
        items.insert( 0, current )
        if current is other:
          items.insert( 0, item )
        self.lvConditions.takeItem( current )
        current =  self.lvConditions.firstChild()
      for current in items:
        self.lvConditions.insertItem( current )
      self.lvConditions.setCurrentItem( item )
      self._conditionSelected( item )
    finally:
      self.lvConditions._ignoreSelected = 0

  def _conditionRenamed( self, item, col, text ):
    if col == 0:
      item.startRename( 1 )

  def _ok( self ):
    result = []
    conditionNames = {}
    item = self.lvConditions.firstChild()
    while item is not None:
      condition = str( item.text( 0 ).latin1() )
      if conditionNames.get( condition ) is not None:
        raise RuntimeError( _t_( 'Two conditions have the same name' ) )
      conditionNames[ condition ] = condition
      onsets = string.split( str( item.text( 1 ).latin1() ) )
      onsetsResult = []
      for onset in onsets:
        onset = string.split( onset, ':' )
        ok = 1
        if len( onset ) > 0:
          time = float( onset[ 0 ] )
          length = 0.0
          amp = 1.0
          if ( len( onset ) > 1 ):
            length = float( onset[ 1 ] )
            if ( len( onset ) > 2 ):
              amp = float( onset[ 2 ] )
              if ( len( onset ) > 3 ):
                ok = 0
        else:
          ok = 0
        if not ok:
          raise RuntimeError( HTMLMessage(_t_( 'invalid onsets for condition <em>%s</em>' ) % condition) )
        onsetsResult.append( ( time, length, amp ) )
      result.append( ( condition, onsetsResult ) )
      item = item.nextSibling()
    if not result: result = None
    self.emit( PYSIGNAL( 'accept' ), ( result, ) )
    self.close( 1 )
      
class Paradigm( Parameter ):
  def __init__( self ):
    Parameter.__init__( self )

  def findValue( self, value ):
    if value is None: return None
    #TODO: Should check value here
    return value

  def editor( self, parent, name ):
    return ParadigmEditor( parent, name )
  
