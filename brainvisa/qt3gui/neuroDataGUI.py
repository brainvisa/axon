# -*- coding: iso-8859-1 -*-
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

from neuroData import *
#from neuroProcesses import *
#from neuroProcessesGUI import *
from backwardCompatibleQt import *
from neuroException import HTMLMessage
from brainvisa import anatomist
#----------------------------------------------------------------------------
class DataEditor:
  def __init__( self ):
    pass
  
  def checkValue( self ):
    pass

  def checkReadable( self ):
    pass

  def releaseCallbacks( self ):
    '''Unrgister all callbacks or references to self so that the editor can
    be destroyed
    '''
    pass


#----------------------------------------------------------------------------
class StringEditor( QLineEdit, DataEditor ):
  def __init__( self, parent, name ):
    DataEditor.__init__( self )
    QLineEdit.__init__( self, parent, name )
    self.setMaxLength(-1)
    self.connect( self, SIGNAL( 'returnPressed()' ), self.setFocusNext )
    self.value = None
    self.setValue( None, True )
      
  def getFocus( self ):
    self.selectAll()
  
  def getValue( self ):
    return self.value

  def _valueFromText( self, text ):
    if text:
      return text
    return None
  
  def setValue( self, value, default = False ):
    if value is None:
      self.setText( '' )
    else:
      self.setText( unicode( value ) )
    if value != self.value:
      self.value = value
      if not default:
        self.emit( PYSIGNAL('noDefault'), ( self.name(),) )
      self.emit( PYSIGNAL('newValidValue'), ( self.name(), self.value, ) )
  
  def setFocusNext( self ):
    self.checkValue()
    QApplication.postEvent( self, QKeyEvent( QEvent.KeyPress, 0x1001, 8, 0 ) )

  def checkValue( self ):
    value = self._valueFromText( unicode( self.text() ) )
    if value != self.getValue():
      self.value = value
      self.emit( PYSIGNAL('noDefault'), ( self.name(),) )
      self.emit( PYSIGNAL('newValidValue'), ( self.name(), self.value, ) )

  

#----------------------------------------------------------------------------
class PasswordEditor (StringEditor):

  def __init__( self, parent, name ):
    StringEditor.__init__( self, parent, name )
    self.setEchoMode(QLineEdit.Password)
      
      
#----------------------------------------------------------------------------
class NumberEditor( StringEditor ):
  def _valueFromText( self, value ):
    if value:
      try:
        result = int( value )
      except:
        try:
          result = long( value )
        except:
          try:
            result = float( value )
          except:
            raise ValueError(  HTMLMessage(_t_('<em>%s</em> is not a valid number') % value))
    else:
      result = None
    return result


#----------------------------------------------------------------------------
class IntegerEditor( StringEditor ):
  def _valueFromText( self, value ):
    if value:
      try:
        result = int( value )
      except:
        try:
          result = long( value )
        except:
          raise ValueError(  HTMLMessage(_t_('<em>%s</em> is not a valid integer') % value) )
    else:
      result = None
    return result


#----------------------------------------------------------------------------
class FloatEditor( StringEditor ):
  def _valueFromText( self, value ):
    if value:
      try:
        result = float( value )
      except:
        raise ValueError( HTMLMessage( _t_('<em>%s</em> is not a valid float') % value) )
    else:
      result = None
    return result


#----------------------------------------------------------------------------
class ChoiceEditor( QComboBox, DataEditor ):
  def __init__( self, parameter, parent, name ):
    QComboBox.__init__( self, 0, parent, name )
    DataEditor.__init__( self )
    #self.connect( self, SIGNAL( 'returnPressed()' ), self.setFocusNext )
    self.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, 
                                     QSizePolicy.Minimum ) )
    self.connect( self, SIGNAL( 'activated( int )' ), self.newValue )
    self.parameter = parameter
    for n, v in self.parameter.values:
      self.insertItem( n )
#dbg#    print 'ChoiceEditor values:', self.parameter.values
    self.value = self.parameter.values[ 0 ][ 1 ]
    self.parameter.warnChoices( self.changeChoices )
    #self.connect( self, SIGNAL( 'destroyed()' ), self.destroyed )

#dbg#  def __del__( self ):
#dbg#    print 'del ChoiceEditor'

  def releaseCallbacks( self ):
#dbg#    print 'ChoiceEditor.releaseCallbacks'
    if self.parameter is not None:
      self.parameter.unwarnChoices( self.changeChoices )
      #self.parameter.setChoices( ( '', None ) )
      #self.parameter = None

  def getValue( self ):
    return self.value

  def setValue( self, value, default = False ):
    i = self.parameter.findIndex( value )
    if i >= 0:
      self.value = self.parameter.values[ i ][ 1 ]
    else:
      raise Exception( HTMLMessage(_t_('<em>%s</em> is not a valid choice') % unicode(value)) )
    self.setCurrentItem( i )
  
  def newValue( self ):
    self.value = self.parameter.values[ self.currentItem() ][ 1 ]
    self.emit( PYSIGNAL('noDefault'), ( self.name(),))
    self.emit( PYSIGNAL('newValidValue'), ( self.name(), self.value, ) )

  def changeChoices( self ):
    oldValue = self.getValue()
    self.clear()
    for n, v in self.parameter.values:
      self.insertItem( n )
    try:
      self.setValue( oldValue )
    except:
      pass


#----------------------------------------------------------------------------
class OpenChoiceEditor( QComboBox, DataEditor ):
  def __init__( self, parameter, parent, name ):
    DataEditor.__init__( self )
    QComboBox.__init__( self, 1, parent, name )
    #self.connect( self, SIGNAL( 'returnPressed()' ), self.setFocusNext )
    self.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, 
                                     QSizePolicy.Minimum ) )
    self.parameter = parameter
    for n, v in self.parameter.values:
      self.insertItem( n )
    self.value = None
    self.parameter.warnChoices( self.changeChoices )
    self.connect( self, SIGNAL( 'activated( int )' ), self.valueSelected )
    self.connect( self.lineEdit(), SIGNAL( 'returnPressed()' ),
                  self.setFocusNext )

  def releaseCallbacks( self ):
    self.parameter.unwarnChoices( self.changeChoices )

  def changeChoices( self ):
    oldValue = self.getValue()
    self.clear()
    for n, v in self.parameter.values:
      self.insertItem( n )
    i = self.parameter.findIndex( oldValue )
    if i >= 0:
      self.value = self.parameter.values[ i ][ 1 ]
      self.setCurrentItem( i )

  def getFocus( self ):
    self.lineEdit().selectAll()
  
  def getValue( self ):
    return self.value

  def setValue( self, value, default=False ):
    i = self.parameter.findIndex( value )
    if i >= 0:
      self.value = self.parameter.values[ i ][ 1 ]
      self.setCurrentItem( i )
    else:
      self.value = unicode( value )
      self.setEditText( self.value )

  def setFocusNext( self ):
    self.checkValue()
    QApplication.postEvent( self, QKeyEvent( QEvent.KeyPress, 0x1001, 8, 0 ) )

  def checkValue( self ):
    value=unicode( self.currentText() )
    if value != self.getValue():
      self.value=value
      self.emit( PYSIGNAL('noDefault'), ( self.name(),) )
      self.emit( PYSIGNAL('newValidValue'), ( self.name(), self.value, ) )


  def valueSelected( self, index ):
    self.checkValue()

#----------------------------------------------------------------------------
class ListOfVectorEditor( StringEditor ):
  def __init__( self, parent, name ):
    StringEditor.__init__( self, parent, name )
    self.value = None

  def setValue( self, value, default = 0 ):
    if value is None:
      self.setText( '' )
    else:
      self.setText( string.join( map( lambda x: string.join( map( str, x ) ),
                                      value ), ';' ) )
    self.value = value

  def _valueFromText( self, text ):
    if text:
      value = []
      for line in string.split( text, ';' ):
        value.append( string.split( line ) )
      return ListOfVectorValue( value )
    return None


#----------------------------------------------------------------------------
class MatrixEditor( StringEditor ):
  def __init__( self, parent, name ):
    StringEditor.__init__( self, parent, name )
    self.value = None

  def setValue( self, value, default = 0 ):
    if value is None:
      self.setText( '' )
    else:
      self.setText( string.join( map( lambda x: string.join( map( str, x ) ), 
                                      value ), ';' ) )
    self.value = value

  def _valueFromText( self, text ):
    if text:
      value = []
      if text:
        for line in string.split( text, ';' ):
          value.append( string.split( line ) )
      return MatrixValue( value )
    return None



#----------------------------------------------------------------------------
class StringListEditor( QLineEdit, DataEditor ):
  def __init__( self, parent, name ):
    DataEditor.__init__( self )
    QLineEdit.__init__( self, parent, name )
    self.setMaxLength(-1)
    self.connect( self, SIGNAL( 'returnPressed()' ), self.setFocusNext )
    self.value = None
    self.setValue( None, True )
      
  def getFocus( self ):
    self.selectAll()
  
  def getValue( self ):
    return self.value

  def _valueFromText( self, text ):
    if not text: return None
    result = []
    quote = ''
    escape = 0
    for c in text:
      if quote:
        if escape:
          current += c
          escape = 0
        else:
          if c == quote:
            result.append( current )
            quote = ''
          elif c == '\\':
            escape = 1
          else:
            current += c
      else:
        if c in ( "'", '"' ):
          quote = c
          current = ''
        elif c != ' ':
          quote = ' '
          if c == '\\': escape = 1
          else: current = c

    if quote:
      result.append( current )
    return result
    return text
  
  def setValue( self, value, default=False ):
    if value != self.value:
      self._setValue( value )
      if not default:
        self.emit( PYSIGNAL('noDefault'), ( self.name(),) )
      self.emit( PYSIGNAL('newValidValue'), ( self.name(), self.value, ) )
    
  def _setValue( self, value ):
    self.value = value
    text = ''
    if value is None:
      pass
    elif type( value ) in ( types.ListType, types.TupleType ):
      if value:
        text = self._quote( str(value[0]) )
        for v in value[ 1: ]:
          text += ' ' + self._quote( str(v) )
    elif value != '':
      text = self._quote( str(value) )
    self.setText( text )
  
  def _quote( self, text ):
    quote = ''
    result = ''
    for c in text:
      if c in ( "'", '"' ):
        if c == quote:
          result += '\\'
        elif not quote:
          if c == '"': quote = "'"
          else: quote = '"'
      elif c == '\\':
        result += '\\'
      result += c
    if not quote: quote = "'"
    return quote + result + quote
  
  def setFocusNext( self ):
    self.checkValue()
    QApplication.postEvent( self, QKeyEvent( QEvent.KeyPress, 0x1001, 8, 0 ) )

  def checkValue( self ):
    currentValue = self._valueFromText( str( self.text().latin1() ) )
    if currentValue != self.getValue() and ( self.getValue() or currentValue ):
      self.value = currentValue
      self.emit( PYSIGNAL('noDefault'), ( self.name(),) )
      self.emit( PYSIGNAL('newValidValue'), ( self.name(), self.value, ) )
        

#----------------------------------------------------------------------------

class NumberListEditor( StringListEditor ):
  def __init__( self, parent, name ):
    DataEditor.__init__( self )
    StringListEditor.__init__( self, parent, name )

  def _valueFromText( self, text ):
    if not text: return None
    result = []
    for s in string.split( text ):
      try: n = int( s )
      except:
        try: n = long( s )
        except:
          try: n = float( s )
          except:
            raise ValueError( HTMLMessage( _t_('<em>%s</em> is not a valid number') % s) )
      result.append( n )
    return result

  def _setValue( self, value ):
    self.value=value
    text = ''
    if value is None:
      pass
    elif isinstance( value, ( list, tuple ) ):
      text = string.join( map( lambda x: str(x), value ) )
    elif isinstance( value, basestring ):
      text = str(value)
    else:
      try:
        valuel = list( value ) # can convert to a list ?
        text = string.join( map( lambda x: str(x), valuel ) )
      except:
        text = str(value)
    self.setText( text )


#----------------------------------------------------------------------------
class IntegerListEditor( NumberListEditor ):
  def __init__( self, parent, name ):
    NumberListEditor.__init__( self, parent, name )

  def _valueFromText( self, text ):
    if not text: return None
    result = []
    for s in string.split( str(self.text().latin1() ) ):
      try: n = int( s )
      except:
        try: n = long( s )
        except:
          raise ValueError(  HTMLMessage(_t_('<em>%s</em> is not a valid integer') % s) )
      result.append( n )
    return result


#----------------------------------------------------------------------------
class FloatListEditor( NumberListEditor ):
  def __init__( self, parent, name ):
    NumberListEditor.__init__( self, parent, name )

  def _valueFromText( self, text ):
    if not text: return None
    result = []
    for s in string.split( str(self.text().latin1() ) ):
      try: n = float( s )
      except:
        raise ValueError( HTMLMessage( _t_('<em>%s</em> is not a valid float') % s) )
      result.append( n )
    return result


#----------------------------------------------------------------------------
class ChoiceListEditor( QHBox, DataEditor ):
  class ChoiceListSelect( QWidget ): # Ex QSemiModal
    def __init__( self, clEditor, name ):
      QWidget.__init__( self, clEditor.topLevelWidget(), name,
        Qt.WType_Dialog+Qt.WGroupLeader+Qt.WStyle_StaysOnTop+Qt.WShowModal )
      layout = QVBoxLayout( self )
      layout.setMargin( 10 )
      layout.setSpacing( 5 )
      
      self.clEditor = clEditor
      self.parameter = clEditor.parameter

      hb = QHBoxLayout()
      self.valueSelect = ChoiceEditor( self.parameter, self, name )
      hb.addWidget( self.valueSelect )
      btn = QPushButton( _t_('Add'), self )
      hb.addWidget( btn )
      self.connect( btn, SIGNAL( 'clicked()' ), self.add )
      btn = QPushButton( _t_('Remove'), self )
      hb.addWidget( btn )
      self.connect( btn, SIGNAL( 'clicked()' ), self.remove )
      layout.addLayout( hb )
      self.list = QListBox( self )
      layout.addWidget( self.list )
      
      hb = QHBoxLayout()
      hb.setSpacing(6)
      hb.setMargin(6)
      spacer = QSpacerItem(20,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
      hb.addItem( spacer )
      btn =QPushButton( _t_('Ok'), self )
      hb.addWidget( btn )
      self.connect( btn, SIGNAL( 'clicked()' ), self._ok )
      btn =QPushButton( _t_('Cancel'), self )
      hb.addWidget( btn )
      self.connect( btn, SIGNAL( 'clicked()' ), self._cancel )
      layout.addLayout( hb )
      self.value = []

    def setValue( self, value ):
      self.value = []
      self.list.clear()
      if value is None or value == '':
        pass
      elif type( value ) in ( types.ListType, types.TupleType ):
        for v in value:
          fv = self.parameter.findValue( v )
          nn, nv  = self.parameter.values[ 0 ]
          i = 0
          for n, vv in self.parameter.values:
            if fv == vv:
              nn = n
              nv = vv
              break
          self.value.append( nv )
          self.list.insertItem( nn )
      else:
        self.setValue( [ value ] )

    def add( self ):
      n = str( self.valueSelect.currentText().latin1() )
      v = self.valueSelect.getValue()
      self.value.append( v )
      self.list.insertItem( n )

    def remove( self ):
      i = self.list.currentItem()
      if i >= 0:
        self.list.removeItem( i )
        del self.value[ i ]
    
    def _ok( self ):
      self.clEditor.setValue( self.value )
      self.close( 1 )
      
    def _cancel( self ):
      self.close( 1 )
  
  def __init__( self, parameter, parent, name ):
    QHBox.__init__( self, parent, name )
    DataEditor.__init__( self )
    self.parameter = parameter
    self.sle = StringListEditor( self, name )
    self.connect( self.sle, PYSIGNAL( 'newValidValue' ), self.checkValue )
    self.btn = QPushButton( '...', self )
    self.connect( self.btn, SIGNAL( 'clicked()' ), self._selectValues )
    self.value=None
    self.setValue( None, 1 )
    
  def getValue( self ):
    return self.value
  
  def setValue( self, value, default = 0 ):
    self._setValue( value, default )

  def _setValue( self, value, default=0):
    if value is not None:
      value = map( self.parameter.findValue, value )
      labels = [self.parameter.values[ self.parameter.findIndex( x ) ][0] for x in value]
      self.sle.setValue( labels )
    if value != self.value:
      self.value = value
      if not default:
        self.emit( PYSIGNAL('noDefault'), ( self.name(),) )
      self.emit( PYSIGNAL('newValidValue'), ( self.name(), self.value, ) )


  def checkValue( self ):
    self.sle.checkValue()
    sleValue = self.sle.getValue()
    if sleValue is not None:
      currentValue = map( self.parameter.findValue, sleValue )
    else:
      currentValue = None
    if currentValue != self.getValue():
      self.value = currentValue
      self.emit( PYSIGNAL('noDefault'), ( self.name(),) )
      self.emit( PYSIGNAL('newValidValue'), ( self.name(), self.value, ) )

  def _selectValues( self ):
    w = self.ChoiceListSelect( self, self.name() )
    try:
      w.setValue( self.getValue() )
    except:
      pass
    w.show()
    
  
 #-------------------------------------------------------------------------------
class PointEditor( QHBox, DataEditor ):
  def __init__( self, parameter, parent, name ):
    if getattr( PointEditor, 'pixSelect', None ) is None:
      setattr( PointEditor, 'pixSelect',
               QPixmap( os.path.join( neuroConfig.iconPath, 
                                      'anaIcon_small.png' ) ) )
    DataEditor.__init__( self )
    QHBox.__init__( self, parent, name )
    self.parameter = parameter
    self.nle = NumberListEditor( self, name )
    
    self.connect( self.nle, PYSIGNAL( 'newValidValue' ), PYSIGNAL( 'newValidValue' ) )
    self.connect( self.nle, PYSIGNAL( 'noDefault' ), PYSIGNAL( 'noDefault' ) )
    
    self.btnSelect = QPushButton( self )
    self.btnSelect.setPixmap( self.pixSelect )
    self.btnSelect.setFocusPolicy( QWidget.NoFocus )
    self.connect( self.btnSelect, SIGNAL( 'clicked()' ), self.selectPressed )
    
    self.nle.setValue( None )
    
  def getValue( self ):
    return self.nle.getValue()

  def setValue( self, value, default = False ):
    # Get only the numbers for the dimension
    if value is not None:
      value = value[ 0 : self.parameter.dimension ]
    self.nle.setValue( value, default )

  def selectPressed( self ):
    a= anatomist.Anatomist()
    
    if self.parameter._Link is not None :
      linked = self.parameter._Link
      self.anatomistObject = a.loadObject( linked )
      w = self.anatomistObject.getWindows()
      if not w:
        self.anatomistView = a.viewObject( linked )
      position = a.linkCursorLastClickedPosition( self.anatomistObject.referential )
    else:
      position = a.linkCursorLastClickedPosition()
    
    if position is None:
      position=[0 for i in xrange(self.parameter.dimension)]

    self.setValue( position )
    self.checkValue() # to force link mechanism to run

  def checkValue( self ):
    self.nle.checkValue()

#-------------------------------------------------------------------------------
class PointListEditor( QHBox, DataEditor ):
  def __init__( self, parameter, parent, name ):
    if getattr( PointListEditor, 'pixSelect', None ) is None:
      setattr( PointListEditor, 'pixSelect',
               QPixmap( os.path.join( neuroConfig.iconPath, 'pencil.png' ) ) )
      setattr( PointListEditor, 'pixErase',
               QPixmap( os.path.join( neuroConfig.iconPath, 'eraser.png' ) ) )
    DataEditor.__init__( self )
    QHBox.__init__( self, parent, name )
    self.parameter = parameter
    self.led = QLineEdit( self )
    self.led.setMaxLength(-1)
    self.connect( self.led, SIGNAL( 'textChanged( const QString & )' ),
                  self.textChanged )
    self.connect( self.led, SIGNAL( 'returnPressed()' ), self.checkValue )
    self.setFocusProxy( self.led )

    self.btnSelect = QPushButton( self )
    self.btnSelect.setPixmap( self.pixSelect )
    self.btnSelect.setToggleButton( 1 )
    self.btnSelect.setFocusPolicy( QWidget.NoFocus )
    self.connect( self.btnSelect, SIGNAL( 'clicked()' ), self.selectPressed )
    
    self.btnErase = QPushButton( self )
    self.btnErase.setPixmap( self.pixErase )
    self.btnSelect.setFocusPolicy( QWidget.NoFocus )
    self.connect( self.btnErase, SIGNAL( 'clicked()' ), self.erasePressed )
    
    self.setValue( None, 1 )
     
  def getFocus( self ):
    self.led.selectAll()
  
  def getValue( self ):
    text = str( self.led.text().latin1() )
    if text:
      return map( lambda x: map( float, string.split(x) ),
                  string.split( text, ',' ) )      

  def setValue( self, value, default = 0 ):
    self._setValue( value )

  def _setValue( self, value ):
    if not value:
      self.led.setText( '' )
    else:
      self.led.setText( string.join( map( 
        lambda point: string.join( map( str, point ) ), value ), ',' ) )
  
  def setFocusNext( self ):
    QApplication.postEvent(self.led, QKeyEvent( QEvent.KeyPress, 0x1001, 8, 0 ))

  def textChanged( self ):
    try:
      v = self.getValue()
    except:
      pass
    else:
      self.emit( PYSIGNAL('noDefault'), ( self.name(),) )
      self.emit( PYSIGNAL('newValidValue'), ( self.name(), v, ) )
        

  def selectPressed( self ):
    if self.btnSelect.isOn():
      a= anatomist.Anatomist()
      a.onCursorNotifier.add(self.anatomistInputFilterEvent )
    else:
      a= anatomist.Anatomist()
      a.onCursorNotifier.remove(self.anatomistInputFilterEvent )

  def anatomistInputFilterEvent( self, event, eventParams ):
    position, window = eventParams[ 'position' ], eventParams[ 'window' ]
    v = self.getValue()
    if v is None: v = []
    v.append( map( float, position[ :self.parameter.dimension ] ) )
    self.setValue( v )

  def erasePressed( self ):
    self.setValue( None )


#----------------------------------------------------------------------------
class GenericListSelection( QWidget ):
  def __init__( self, parent, name ):
    if getattr( GenericListSelection, 'pixUp', None ) is None:
      setattr( GenericListSelection, 'pixUp', 
        QPixmap( QImage(findIconFile( 'up.png' )).smoothScale(*largeIconSize) ) )
      setattr( GenericListSelection, 'pixDown', 
        QPixmap( QImage(findIconFile( 'down.png' )).smoothScale(*largeIconSize) ) )
    
    QWidget.__init__( self, parent.topLevelWidget(), name,
      Qt.WType_Dialog + Qt.WGroupLeader + Qt.WStyle_StaysOnTop + Qt.WShowModal )
    layout = QVBoxLayout( self )
    layout.setMargin( 10 )
    layout.setSpacing( 5 )
    
    self.values = []
    
    self.lbxValues = QListBox( self )
    self.connect( self.lbxValues, SIGNAL('currentChanged( QListBoxItem * )'), self._currentChanged )
    layout.addWidget( self.lbxValues )

    hb = QHBoxLayout()
    hb.setSpacing( 6 )
    
    self.btnAdd = QPushButton( _t_( 'Add' ), self )
    self.connect( self.btnAdd, SIGNAL( 'clicked()' ), self._add )
    hb.addWidget( self.btnAdd )

    self.btnRemove = QPushButton( _t_( 'Remove' ), self )
    self.btnRemove.setEnabled( 0 )
    self.connect( self.btnRemove, SIGNAL( 'clicked()' ), self._remove )
    hb.addWidget( self.btnRemove )
    
    self.btnUp = QPushButton( self )
    self.btnUp.setPixmap( self.pixUp )
    self.btnUp.setEnabled( 0 )
    self.connect( self.btnUp, SIGNAL( 'clicked()' ), self._up )
    hb.addWidget( self.btnUp )

    self.btnDown = QPushButton( self )
    self.btnDown.setPixmap( self.pixDown )
    self.btnDown.setEnabled( 0 )
    self.connect( self.btnDown, SIGNAL( 'clicked()' ), self._down )
    hb.addWidget( self.btnDown )

    spacer = QSpacerItem( 10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum )
    hb.addItem( spacer )

    layout.addLayout( hb )
      
    hb = QHBoxLayout()
    hb.setSpacing(6)
    hb.setMargin(6)
    spacer = QSpacerItem(20,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
    hb.addItem( spacer )
    btn =QPushButton( _t_('Ok'), self )
    hb.addWidget( btn )
    self.connect( btn, SIGNAL( 'clicked()' ), self._ok )
    btn =QPushButton( _t_('Cancel'), self )
    hb.addWidget( btn )
    self.connect( btn, SIGNAL( 'clicked()' ), self._cancel )
    layout.addLayout( hb )

    neuroConfig.registerObject( self )

  def close( self, alsoDelete ):
    neuroConfig.unregisterObject( self )
    return QWidget.close( self, alsoDelete )
    
  def _currentChanged( self ):
    index = self.lbxValues.currentItem()
    if index >= 0 and index < len( self.values ):
      # TODO
      #self.sle.setValue( [ self.values[ index ].fullPath() ] )
      self.btnRemove.setEnabled( 1 )
      if index > 0:
        self.btnUp.setEnabled( 1 )
      else:
        self.btnUp.setEnabled( 0 )
      if index < ( len( self.values ) - 1 ):
        self.btnDown.setEnabled( 1 )
      else:
        self.btnDown.setEnabled( 0 )
    else:
      # TODO
      #self.sle.setValue( None )
      self.btnRemove.setEnabled( 0 )
      self.btnUp.setEnabled( 0 )
      self.btnDown.setEnabled( 0 )

  def _add( self ):
    try:
      pass
      # TODO
      #for v in map( self.parameter.findValue, self.sle.getValue() ):
        #self.values.append( v )
        #if v is None:
          #self.lbxValues.insertItem( '<' + _t_('None') + '>' )
        #else:
          #self.lbxValues.insertItem( v.fileName() )
      #self.lbxValues.setCurrentItem( len( self.values ) - 1 )   
    except:
      showException( parent=self )
  
  def _remove( self ):
    index = self.lbxValues.currentItem()
    del self.values[ index ]
    self.lbxValues.removeItem( index )
    
  def _up( self ):
    index = self.lbxValues.currentItem()
    tmp = self.values[ index ]
    self.values[ index ] = self.values[ index - 1 ]
    self.values[ index - 1 ] = tmp
    tmp = self.lbxValues.text( index )
    self.lbxValues.changeItem( self.lbxValues.text( index - 1 ), index )
    self.lbxValues.changeItem( tmp, index - 1 )
    
  def _down( self ):
    index = self.lbxValues.currentItem()
    tmp = self.values[ index ]
    self.values[ index ] = self.values[ index + 1 ]
    self.values[ index + 1 ] = tmp
    tmp = self.lbxValues.text( index )
    self.lbxValues.changeItem( self.lbxValues.text( index + 1 ), index )
    self.lbxValues.changeItem( tmp, index + 1 )
  
  def setValue( self, value ):
    if isinstance( value, ( list, tuple ) ):
      self.values = []
      self.lbxValues.clear()
      for v in value:
        self.values.append( v )
        if v is None:
          self.lbxValues.insertItem( '<' + _t_('None') + '>' )
        else:
          pass
          # TODO
          #self.lbxValues.insertItem( v.fileName() )
    
  def _ok( self ):
    # TODO
    #self.dilEditor._newValue( self.values )
    self.close( True )
    
  def _cancel( self ):
    self.close( True )



#----------------------------------------------------------------------------
class ListOfListEditor( QPushButton, DataEditor ):
  def __init__( self, parameter, parent, name, context=None ):
    QPushButton.__init__( self, parent, name )
    self.setValue( None, True )
    self.connect( self, SIGNAL( 'clicked()' ), self.startEditValues )
  
  def getValue( self ):
    return self._value
    
  def setValue( self, value, default = False ):
    self._value = value
    if value:
      self.setText( _t_( 'list of length %d' ) % ( len( value ), ) )
    else:
      self.setText( _t_( 'empty list' ) )
  
  def startEditValues( self ):
    if self.editValuesDialog is None:
      self.editValuesDialog = GenericListSelection( parent, name )
      self.connect( self.editValuesDialog, PYSIGNAL( 'accept' ), self.acceptEditedValues )
    self.editValuesDialog.show()
  
  
  def acceptEditedValues( self ):
    self.emit( PYSIGNAL( 'newValidValue' ), ( self.name(), self.acceptEditedValues.values, ) )
    self.emit( PYSIGNAL('noDefault'), ( self.name(),) )


##----------------------------------------------------------------------------
#class ObjectSelection( QComboBox ):
  #def __init__( self, objects, names = None, parent = None, name = None ):
    #QComboBox.__init__( self, 0, parent, name )
    #if names is None:
      #names = map( str, objects )
    #self.objects = objects
    #for n in names:
      #self.addItem( n )

  #def currentObject( self ):
    #i = self.currentItem()
    #if i > 0 and i < len( self.allTypes ):
      #return self.objects[ i ]
    #return None

#----------------------------------------------------------------------------
class ObjectsSelection( QListBox ):
  def __init__( self, objects, names = None, parent = None, name = None ):
    QListBox.__init__( self, parent, name )
    self.setSelectionMode( self.Extended )
    if names is None:
      names = map( str, objects )
    self.objects = objects
    for n in names:
      self.insertItem( n )

  def currentObjects( self ):
    result = []
    i = 0
    while i < self.count():
      if self.isSelected( i ):
        result.append( self.objects[ i ] )
      i += 1
    return result


#----------------------------------------------------------------------------
class NotImplementedEditor( QLabel, DataEditor ):
  def __init__( self, parent ):
    QLabel.__init__( self, '<font color=red>' + \
                     _t_( 'editor not implemented' ) + '</font>', parent )
    self._value = None
    
  def setValue( self, value, default ):
    self._value = value
    
  def getValue( self ):
    return self._value

#----------------------------------------------------------------------------
def initializeDataGUI():
  # Connect editors to Parameters. This is done here to make module neuroData
  # independant from module neuroDataGUI
  String.editor = \
    lambda self, parent, name, context: StringEditor( parent, name )
  String.listEditor = \
    lambda self, parent, name, context: StringListEditor( parent, name )
  Password.editor = \
    lambda self, parent, name, context: PasswordEditor( parent, name )
  Number.editor = \
    lambda self, parent, name, context: NumberEditor( parent, name )
  Number.listEditor = \
    lambda self, parent, name, context: NumberListEditor( parent, name )
  Integer.editor = \
    lambda self, parent, name, context: IntegerEditor( parent, name )
  Integer.listEditor = \
    lambda self, parent, name, context: IntegerListEditor( parent, name )
  Float.editor = \
    lambda self, parent, name, context: FloatEditor( parent, name )
  Float.listEditor = \
    lambda self, parent, name, context: FloatListEditor( parent, name )
  Choice.editor = \
    lambda self, parent, name, context: ChoiceEditor( self, parent, name )
  OpenChoice.editor = \
    lambda self, parent, name, context: OpenChoiceEditor( self, parent, name )
  Choice.listEditor = \
    lambda self, parent, name, context: ChoiceListEditor( self, parent, name )
  ListOf.listEditor = \
    lambda self, parent, name, context: NotImplementedEditor( parent )
  ListOf.editor = \
    lambda self, parent, name, context: self.contentType.listEditor( parent,
                                                                     name,
                                                                     context )
  Point.editor = \
    lambda self, parent, name, context: PointEditor( self, parent, name )
  Point.listEditor = \
    lambda self, parent, name, context: PointListEditor( self, parent, name )
  Point2D.editor = \
    lambda self, parent, name, context: PointEditor( self, parent, name )
  Point2D.listEditor = \
    lambda self, parent, name, context: PointListEditor( self, parent, name )
  Point3D.editor = \
    lambda self, parent, name, context: PointEditor( self, parent, name )
  Point3D.listEditor = \
    lambda self, parent, name, context: PointListEditor( self, parent, name )
  ListOfVector.editor = \
    lambda self, parent, name, context: ListOfVectorEditor( parent, name )
  Matrix.editor = \
    lambda self, parent, name, context: MatrixEditor( parent, name )
