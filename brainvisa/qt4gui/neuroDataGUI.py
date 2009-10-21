# -*- coding: iso-8859-1 -*-
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
    QLineEdit.__init__( self, parent )
    if name:
      self.setObjectName( name )
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
        self.emit( SIGNAL('noDefault'), unicode(self.objectName()) )
      self.emit( SIGNAL('newValidValue'), unicode(self.objectName()), self.value )
  
  def setFocusNext( self ):
    self.checkValue()
    QApplication.postEvent( self, QKeyEvent( QEvent.KeyPress, 0x1001, 8, 0 ) )

  def checkValue( self ):
    value = self._valueFromText( unicode( self.text() ) )
    if value != self.getValue():
      self.value = value
      self.emit( SIGNAL('noDefault'), unicode(self.objectName()) )
      self.emit( SIGNAL('newValidValue'), unicode(self.objectName()), self.value )

  

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
    QComboBox.__init__( self, parent )
    DataEditor.__init__( self )
    if name:
      self.setObjectName( name )
    #self.connect( self, SIGNAL( 'returnPressed()' ), self.setFocusNext )
    #self.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, 
                                     #QSizePolicy.Minimum ) )
    self.connect( self, SIGNAL( 'activated( int )' ), self.newValue )
    self.parameter = parameter
    for n, v in self.parameter.values:
      self.addItem( n )
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
    self.setCurrentIndex( i )
  
  def newValue( self ):
    self.value = self.parameter.values[ self.currentIndex() ][ 1 ]
    self.emit( SIGNAL('noDefault'), unicode(self.objectName()) )
    self.emit( SIGNAL('newValidValue'), unicode(self.objectName()), self.value )

  def changeChoices( self ):
    oldValue = self.getValue()
    self.clear()
    for n, v in self.parameter.values:
      self.addItem( n )
    try:
      self.setValue( oldValue )
    except:
      pass


#----------------------------------------------------------------------------
class OpenChoiceEditor( QComboBox, DataEditor ):
  def __init__( self, parameter, parent, name ):
    DataEditor.__init__( self )
    QComboBox.__init__( self, parent )
    if name:
      self.setObjectName( name )
    self.setEditable(True)
    #self.connect( self, SIGNAL( 'returnPressed()' ), self.setFocusNext )
    #self.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, 
                                     #QSizePolicy.Minimum ) )
    self.parameter = parameter
    for n, v in self.parameter.values:
      self.addItem( n )
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
      self.addItem( n )
    i = self.parameter.findIndex( oldValue )
    if i >= 0:
      self.value = self.parameter.values[ i ][ 1 ]
      self.setCurrentIndex( i )

  def getFocus( self ):
    self.lineEdit().selectAll()
  
  def getValue( self ):
    return self.value

  def setValue( self, value, default=False ):
    i = self.parameter.findIndex( value )
    if i >= 0:
      self.value = self.parameter.values[ i ][ 1 ]
      self.setCurrentIndex( i )
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
      self.emit( SIGNAL('noDefault'), unicode(self.objectName()) )
      self.emit( SIGNAL('newValidValue'), unicode(self.objectName()), self.value )


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
    QLineEdit.__init__( self, parent )
    if name:
      self.setObjectName( name )
    self.setMaxLength(-1)
    self.connect( self, SIGNAL( 'returnPressed()' ), self.setFocusNext )
    self.connect( self, SIGNAL( 'lostFocus()' ), self.checkValue )
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
        self.emit( SIGNAL('noDefault'), unicode(self.objectName()) )
      self.emit( SIGNAL('newValidValue'), unicode(self.objectName()), self.value )
    
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
    QApplication.postEvent( self, QKeyEvent( QEvent.KeyPress, 0x1001, 8, 0 ) )

  def checkValue( self ):
    currentValue = self._valueFromText( str( self.text().toLatin1() ) )
    if currentValue != self.getValue() and ( self.getValue() or currentValue ):
      self.value = currentValue
      self.emit( SIGNAL('noDefault'), unicode(self.objectName()) )
      self.emit( SIGNAL('newValidValue'), unicode(self.objectName()), self.value )
        

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
    for s in string.split( str(self.text().toLatin1() ) ):
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
    for s in string.split( str(self.text().toLatin1() ) ):
      try: n = float( s )
      except:
        raise ValueError( HTMLMessage( _t_('<em>%s</em> is not a valid float') % s) )
      result.append( n )
    return result


#----------------------------------------------------------------------------
class ChoiceListEditor( QWidget, DataEditor ):
  class ChoiceListSelect( QWidget ): # Ex QSemiModal
    def __init__( self, clEditor, name ):
      QWidget.__init__( self, clEditor.topLevelWidget(), Qt.Dialog | Qt.Tool | Qt.WindowStaysOnTop )
      if name:
        self.setObjectName( name )
      self.setAttribute( Qt.WA_DeleteOnClose, True )
      self.setWindowModality(Qt.WindowModal)
      layout = QVBoxLayout( self )
      layout.setMargin( 10 )
      layout.setSpacing( 5 )
      self.setLayout(layout)
      
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
      self.list = QListWidget( self )
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
          self.list.addItem( nn )
      else:
        self.setValue( [ value ] )

    def add( self ):
      n = str( self.valueSelect.currentText().toLatin1() )
      v = self.valueSelect.getValue()
      self.value.append( v )
      self.list.addItem( n )

    def remove( self ):
      i = self.list.currentRow()
      if i >= 0:
        self.list.takeItem( i )
        del self.value[ i ]
    
    def _ok( self ):
      self.clEditor.setValue( self.value )
      self.close( )
      
    def _cancel( self ):
      self.close( )
  
  def __init__( self, parameter, parent, name ):
    QWidget.__init__( self, parent )
    DataEditor.__init__( self )
    if name:
      self.setObjectName( name )
    layout=QHBoxLayout(self)
    layout.setMargin(0)
    self.setLayout(layout)
    self.parameter = parameter
    self.sle = StringListEditor( self, name )
    layout.addWidget(self.sle)
    self.connect( self.sle, SIGNAL( 'newValidValue' ), self.checkValue )
    self.btn = QPushButton( '...', self )
    layout.addWidget(self.btn)
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
        self.emit( SIGNAL('noDefault'), unicode(self.objectName()) )
      self.emit( SIGNAL('newValidValue'), unicode(self.objectName()), self.value )


  def checkValue( self ):
    self.sle.checkValue()
    sleValue = self.sle.getValue()
    if sleValue is not None:
      currentValue = map( self.parameter.findValue, sleValue )
    else:
      currentValue = None
    if currentValue != self.getValue():
      self.value = currentValue
      self.emit( SIGNAL('noDefault'), unicode(self.objectName()) )
      self.emit( SIGNAL('newValidValue'), unicode(self.objectName()), self.value )

  def _selectValues( self ):
    w = self.ChoiceListSelect( self, unicode(self.objectName()) )
    try:
      w.setValue( self.getValue() )
    except:
      pass
    w.show()
    
  
 #-------------------------------------------------------------------------------
class PointEditor( QWidget, DataEditor ):
  def __init__( self, parameter, parent, name ):
    if getattr( PointEditor, 'pixSelect', None ) is None:
      setattr( PointEditor, 'pixSelect',
               QIcon( os.path.join( neuroConfig.iconPath, 
                                      'anaIcon_small.png' ) ) )
    DataEditor.__init__( self )
    QWidget.__init__( self, parent )
    if name:
      self.setObjectName( name )
    layout=QHBoxLayout()
    layout.setMargin(0)
    layout.setSpacing(4)
    self.setLayout(layout)
    self.parameter = parameter
    self.nle = NumberListEditor( None, name )
    layout.addWidget(self.nle)
    
    self.connect( self.nle, SIGNAL( 'newValidValue' ), SIGNAL( 'newValidValue' ) )
    self.connect( self.nle, SIGNAL( 'noDefault' ), SIGNAL( 'noDefault' ) )
    
    self.btnSelect = QPushButton( )
    layout.addWidget(self.btnSelect)
    self.btnSelect.setIcon( self.pixSelect )
    self.btnSelect.setFocusPolicy( Qt.NoFocus )
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
class PointListEditor( QWidget, DataEditor ):
  def __init__( self, parameter, parent, name ):
    if getattr( PointListEditor, 'pixSelect', None ) is None:
      setattr( PointListEditor, 'pixSelect',
               QIcon( os.path.join( neuroConfig.iconPath, 'pencil.png' ) ) )
      setattr( PointListEditor, 'pixErase',
               QIcon( os.path.join( neuroConfig.iconPath, 'eraser.png' ) ) )
    DataEditor.__init__( self )
    QWidget.__init__( self, parent )
    if name:
      self.setObjectName( name )
    layout=QHBoxLayout()
    layout.setMargin(0)
    self.setLayout(layout)
    self.parameter = parameter
    self.led = QLineEdit( )
    self.led.setMaxLength(-1)
    layout.addWidget(self.led)
    self.connect( self.led, SIGNAL( 'textChanged( const QString & )' ),
                  self.textChanged )
    self.connect( self.led, SIGNAL( 'returnPressed()' ), self.setFocusNext )
    self.setFocusProxy( self.led )

    self.btnSelect = QPushButton()
    layout.addWidget(self.btnSelect)
    self.btnSelect.setIcon( self.pixSelect )
    self.btnSelect.setCheckable(True)
    self.btnSelect.setFocusPolicy( Qt.NoFocus )
    self.connect( self.btnSelect, SIGNAL( 'clicked()' ), self.selectPressed )
    
    self.btnErase = QPushButton()
    layout.addWidget(self.btnErase)
    self.btnErase.setIcon( self.pixErase )
    self.btnSelect.setFocusPolicy( Qt.NoFocus )
    self.connect( self.btnErase, SIGNAL( 'clicked()' ), self.erasePressed )
    
    self.setValue( None, 1 )
     
  def getFocus( self ):
    self.led.selectAll()
  
  def getValue( self ):
    text = str( self.led.text().toLatin1() )
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
      self.emit( SIGNAL('noDefault'), unicode(self.objectName()) )
      self.emit( SIGNAL('newValidValue'), unicode(self.objectName()), v )
        

  def selectPressed( self ):
    if self.btnSelect.isChecked():
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
        QIcon( findIconFile( 'up.png' )) )
      setattr( GenericListSelection, 'pixDown', 
        QIcon( findIconFile( 'down.png' )) )
    
    QWidget.__init__( self, parent.topLevelWidget(), Qt.Dialog | Qt.Tool | Qt.WindowStaysOnTop )
    if name:
      self.setObjectName( name )
    self.setWindowModality(Qt.WindowModal)
    layout = QVBoxLayout( )
    layout.setMargin( 10 )
    layout.setSpacing( 5 )
    self.setLayout(layout)
    
    self.values = []
    
    self.lbxValues = QListWidget( )
    self.connect( self.lbxValues, SIGNAL('currentItemChanged( QListWidgetItem *, QListWidgetItem *  )'), self._currentChanged )
    layout.addWidget( self.lbxValues )

    hb = QHBoxLayout()
    hb.setSpacing( 6 )
    
    self.btnAdd = QPushButton( _t_( 'Add' ) )
    self.connect( self.btnAdd, SIGNAL( 'clicked()' ), self._add )
    hb.addWidget( self.btnAdd )

    self.btnRemove = QPushButton( _t_( 'Remove' ) )
    self.btnRemove.setEnabled( 0 )
    self.connect( self.btnRemove, SIGNAL( 'clicked()' ), self._remove )
    hb.addWidget( self.btnRemove )
    
    self.btnUp = QPushButton( )
    self.btnUp.setIcon( self.pixUp )
    self.btnUp.setIconSize(QSize(*largeIconSize))
    self.btnUp.setEnabled( 0 )
    self.connect( self.btnUp, SIGNAL( 'clicked()' ), self._up )
    hb.addWidget( self.btnUp )

    self.btnDown = QPushButton( )
    self.btnDown.setIcon( self.pixDown )
    self.btnDown.setIconSize(QSize(*largeIconSize))
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
    btn =QPushButton( _t_('Ok') )
    hb.addWidget( btn )
    self.connect( btn, SIGNAL( 'clicked()' ), self._ok )
    btn =QPushButton( _t_('Cancel') )
    hb.addWidget( btn )
    self.connect( btn, SIGNAL( 'clicked()' ), self._cancel )
    layout.addLayout( hb )

    neuroConfig.registerObject( self )

  def closeEvent( self, event ):
    neuroConfig.unregisterObject( self )
    QWidget.closeEvent( self, event )
    
  def _currentChanged( self ):
    index = self.lbxValues.currentRow()
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
    index = self.lbxValues.currentRow()
    del self.values[ index ]
    self.lbxValues.takeItem( index )
    
  def _up( self ):
    index = self.lbxValues.currentRow()
    tmp = self.values[ index ]
    self.values[ index ] = self.values[ index - 1 ]
    self.values[ index - 1 ] = tmp
    item=self.lbxValues.takeItem( index )
    self.lbxValues.insertItem( index - 1, item )
    
  def _down( self ):
    index = self.lbxValues.currentRow()
    tmp = self.values[ index ]
    self.values[ index ] = self.values[ index + 1 ]
    self.values[ index + 1 ] = tmp
    item=self.lbxValues.takeItem( index )
    self.lbxValues.insertItem( index + 1, item )
  
  def setValue( self, value ):
    if isinstance( value, ( list, tuple ) ):
      self.values = []
      self.lbxValues.clear()
      for v in value:
        self.values.append( v )
        if v is None:
          self.lbxValues.addItem( '<' + _t_('None') + '>' )
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
    QPushButton.__init__( self, parent )
    if name:
      self.setObjectName( name )
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
      self.connect( self.editValuesDialog, SIGNAL( 'accept' ), self.acceptEditedValues )
    self.editValuesDialog.show()
  
  
  def acceptEditedValues( self ):
    self.emit( SIGNAL( 'newValidValue' ), unicode(self.objectName()), self.acceptEditedValues.values )
    self.emit( SIGNAL('noDefault'), unicode(self.objectName()) )


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
class ObjectsSelection( QListWidget ):
  def __init__( self, objects, names = None, parent = None, name = None ):
    QListBox.__init__( self, parent )
    if name:
      self.setObjectName( name )
    self.setSelectionMode( self.ExtendedSelection )
    if names is None:
      names = map( str, objects )
    self.objects = objects
    for n in names:
      self.addItem( n )

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
