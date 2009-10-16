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
import sys, os
from itertools import chain

from backwardCompatibleQt import QDialog, Qt, QVBoxLayout, QComboBox, SIGNAL, PYSIGNAL, SLOT, \
               QLabel, QApplication, QPixmap, QListBox, QScrollView, QGridLayout, QFrame, QWidget, QSizePolicy
from qt import QString, QStringList
from qttable import QTable

from soma.functiontools import partial
from soma.qtgui.api import createWidget, QLineEditModificationTimer
from soma.html import htmlEscape
from soma.wip.application.api import findIconFile
from soma.uuid import Uuid
from soma.undefined import Undefined
from soma.stringtools import quote_string, string_to_list, list_to_string
from neuroDiskItems import DiskItem, getFormats
from neuroProcesses import getDiskItemType, getConvertersTo

#----------------------------------------------------------------------------
class SignalNameComboBox( QComboBox ):
  def __init__( self, editable, parent, name ):
    QComboBox.__init__( self, editable, parent, name )
    self.connect( self, SIGNAL( 'activated(int)' ), self.signalName )
    self.setMaximumWidth(600)
    
  def signalName( self, index ):
    self.emit( PYSIGNAL( 'activated' ), ( str( self.name() ), index ) )


#----------------------------------------------------------------------------
def diskItemFilter( database, diskItem, required, explainRejection=False ):
  if diskItem.type is not None:
    types = database.getTypeChildren( *database.getAttributeValues( '_type', {}, required ) )
    if types and diskItem.type.name not in types:
      if explainRejection:
        return 'DiskItem type ' + repr(diskItem.type.name) + ' is not in ' + repr( tuple(types) )
      return False
  formats = database.getAttributeValues( '_format', {}, required )
  if formats and diskItem.format is not None:
    if diskItem.format.name not in formats:
      if explainRejection:
        if diskItem.format is None :
          value = None
        else :
          value = diskItem.format.name
        return 'DiskItem format ' + repr(value) + ' is not in ' + repr( tuple(formats) )
      return False
  for key in required:
    if key in ( '_type', '_format' ): continue
    values = database.getAttributeValues( key, {}, required )
    itemValue = diskItem.get( key, Undefined )
    if itemValue is Undefined:
      if explainRejection:
        return 'DiskItem do not have the required ' + repr( key ) + ' attribute'
      return False
    if (key == 'name_serie'):
      if itemValue != values:
        if explainRejection:
          return 'DiskItem attribute ' + repr(key) + ' = ' + repr( itemValue ) + ' != ' + repr( values )
        return False
    else:
      if itemValue not in values:
        if explainRejection:
            return 'DiskItem attribute ' + repr(key) + ' = ' + repr( itemValue ) + ' is not in ' + repr( tuple(values) )
        return False
  return True


#----------------------------------------------------------------------------
class DiskItemBrowser( QDialog ):
  def __init__( self, database, parent=None, write=False, multiple=False,
                selection={}, required={}, enableConversion=False ):
    """
    """
    QDialog.__init__( self, parent, None, 1, Qt.WGroupLeader )
    layout = QVBoxLayout( self )
    layout.setAutoAdd( 1 )

    p = os.path.join( os.path.dirname( __file__ ), 'diskItemBrowser.ui' )
    self._ui = createWidget( p, self )
    if write:
      self._ui.labDatabaseIcon.setPixmap( QPixmap( findIconFile( 'database_write.png' ) ) )
    
    # remove the existings ui-designer widgets
    #attributeFrameLayout = self._ui.attributesFrame.layout()
    #for x in (x for x in self._ui.attributesFrame.children() if x.isWidgetType()):
      #x.deleteLater()
    vlayout=QVBoxLayout(self._ui.attributesFrame)
    scrollview=QScrollView(self._ui.attributesFrame)
    scrollview.setResizePolicy( QScrollView.AutoOneFit )
    scrollview.setFrameStyle( QFrame.NoFrame )
    scrollview.setMargin(6)
    vlayout.addWidget(scrollview)
    self.gridwidget=QWidget(scrollview.viewport())
    vlayout=QVBoxLayout(scrollview.viewport())
    self.gridLayout=QGridLayout(self.gridwidget)
    self.gridLayout.setMargin(6)
    self.gridLayout.setSpacing(5)
    scrollview.addChild(self.gridwidget)
    #self._ui.attributesFrame.layout().addWidget(scrollview)
    vlayout.addWidget(self.gridwidget)
    
    self._items = []
    self.connect( self._ui.tblItems, SIGNAL('currentChanged( int, int )'), self.itemSelected )
      
    #print '!DiskItemBrowser!', database, selection, required
    self._requiredAttributes = required
    self._database = database
    self._requestedTypes = database.getAttributeValues( '_type', {}, required )
    #print '!DiskItemBrowser! _requestedTypes', self._requestedTypes
    self._possibleTypes = set( chain( *( self._database.getTypeChildren(  t ) for t in self._requestedTypes ) ) )
    #print '!DiskItemBrowser! _possibleTypes', self._possibleTypes
    self._possibleFormats = set( chain( *(self._database.getTypesFormats( t ) for t in self._possibleTypes) ) )
    requestedFormats = database.getAttributeValues( '_format', {}, required )
    if self._possibleFormats:
      if requestedFormats:
        self._possibleFormats = self._possibleFormats.intersection( requestedFormats )
      else:
        requestedFormats = self._possibleFormats
    else:
      self._possibleFormats = requestedFormats
    self._formatsWithConverter = {}
    if enableConversion:
      any = getDiskItemType( 'Any type' )
      for type_format, converter in chain( *( getConvertersTo( ( any, f ) ).iteritems() for f in getFormats( self._possibleFormats ) ) ):
          type, format = type_format
          if format.name not in self._possibleFormats:
            self._formatsWithConverter[ format.name ] = converter
    self._possibleFormats.update( self._formatsWithConverter.iterkeys() )
    #print '!DiskItemBrowser! _possibleFormats', self._possibleFormats
    self._write = write
    self._multiple = multiple

    if self._multiple:
      self._ui.tblItems.setSelectionMode( QTable.MultiRow )
    else:
      self.connect( self._ui.tblItems, SIGNAL( 'doubleClicked ( int, int, int, const QPoint & )' ), self, SLOT('accept()') )

    layoutRow = 0
    e,v = self._database.getAttributesEdition()
    databases = v.get( '_database', () )
    if len( databases ) > 1:
      self._cmbDatabase = self._createCombo( _t_( 'Database' ), '_database', False, layoutRow )
      self._cmbDatabase.insertItem( '<' + _t_( 'any' ) + '>' )
      for d in databases:
        self._cmbDatabase.insertItem( d )
    else:
      self._cmbDatabase = None
    layoutRow += 1
    self._cmbType = self._createCombo( _t_( 'Data type' ), '_type', False, layoutRow )
    layoutRow += 1
    self._cmbFormat = self._createCombo( _t_( 'File format' ), '_format', False, layoutRow )
    layoutRow += 1
    self._combos = {} # Dictionary of attribute combos (attribute name -> QComboBox instance)
    self._editableAttributes, self._attributesValues = self._database.getAttributesEdition( *self._requestedTypes )
    self._editableAttributes = tuple( self._editableAttributes )
    self._editableAttributesValues = dict( ( (i,set()) for i in self._editableAttributes ) )
    for values in self._database.findAttributes( self._editableAttributes, _type='Any Type' ):
      for i in xrange( len(values) ):
        if values[ i ]:
          self._editableAttributesValues[ self._editableAttributes[ i ] ].add( values[ i ] )
    #print '!DiskItemBrowser! _editableAttributes', self._editableAttributes
    #print '!DiskItemBrowser! _attributesValues', self._attributesValues
    allAttributes = list( self._database.getTypesKeysAttributes( *self._requestedTypes ) )
    for a in self._attributesValues:
      if a not in allAttributes:
        allAttributes.append( a )
    for a in allAttributes:
      if a!='name_serie':
        if a in self._editableAttributes:
          self._combos[ a ] = self._createCombo( _t_( a ), a, True, layoutRow )
          layoutRow += 1
        elif a != '_database' and a in self._attributesValues:
          self._combos[ a ] = self._createCombo( _t_( a ), a, False, layoutRow )
          layoutRow += 1
    #gridLayout = self._ui.attributesFrame.layout().children()[ 0 ]
    self.gridLayout.setColStretch( 0, 0 )
    self.gridLayout.setColStretch( 1, 1 )
    self._selectedAttributes={}
    # among selection attributes keep those related to the types searched to initialize the combos
    for k, v in selection.items():
      if k in allAttributes:
        self._selectedAttributes[k]=v
    #self._selectedAttributes = selection
    
    self._lastSelection = None
    self.rescan()
    
    
    self.connect( self._ui.btnReset, SIGNAL( 'clicked()' ), self.resetSelectedAttributes )
    #btn.setText(_t_('Ok'))
    #btn.setAutoDefault( False )
    self.connect( self._ui.btnOk, SIGNAL( 'clicked()' ), self, SLOT( 'accept()' ) )
    #btn.setText(_t_('Cancel'))
    #btn.setAutoDefault( False )
    self.connect( self._ui.btnCancel, SIGNAL( 'clicked()' ), self, SLOT( 'reject()' ) )

    self.itemSelected()
  
  def _createCombo( self, caption, attributeName, editable, layoutRow ):
    #gridLayout = self._ui.attributesFrame.layout().children()[ 0 ]
    label = QLabel(_t_( caption ), self.gridwidget )
    self.gridLayout.addWidget( label, layoutRow, 0 )
    cmb = SignalNameComboBox( editable, self.gridwidget, attributeName )
    cmb.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Fixed )
    cmb._label = label
    if editable:
      cmb._modificationTimer = QLineEditModificationTimer( cmb.lineEdit() )
      self.connect( cmb._modificationTimer, PYSIGNAL( 'userModification' ), partial( self._comboTextChanged, name=attributeName ) )
    cmb.connect( cmb, PYSIGNAL( 'activated' ), self._comboSelected )
    self.gridLayout.addWidget( cmb, layoutRow, 1 )
    return cmb
    
    
  def accept( self ):
    QDialog.accept( self )
    self.emit( PYSIGNAL( 'accept' ), () )


  def itemSelected( self, row=None, col=None ):
    index = row
    if index is not None and self._items:
      item = (self._items[ index ] if isinstance(self._items[ index ], DiskItem) else self._database.getDiskItemFromUuid(self._items[ index ]))
      self._items[ index ] = item
      self._ui.textBrowser.setText( self.diskItemDisplayText( item ) )
      self.emit( PYSIGNAL('selected'), ( item, ) )
    else:
      self.emit( PYSIGNAL('selected'), ( None, ) )

  
  def _comboSelected( self, name, index ):
    cmb = self._combos.get( name )
    if cmb is None:
      if name == '_type':
        cmb = self._cmbType
      elif name == '_format':
        cmb = self._cmbFormat
      elif name == '_database':
        cmb = self._cmbDatabase
      else:
        return
    timer = getattr( cmb, '_modificationTimer', None )
    if timer is not None:
      timer.stop()
    if index == 0:
      self._selectedAttributes.pop( name, None )
      self._lastSelection = None
    elif index > 0:
      if name=='name_serie': # only name_serie attribute must be interpreted as a list when a value of a combo box is selected. A type or format can be in several words but is not a list...
        l = list( string_to_list( unicode( cmb.text( index ) ) ) )
        if not l:
          v = ''
        elif len( l ) == 1:
          v = l[ 0 ]
        else:
          v = l
      else:
        v=unicode( cmb.text( index ) )
      self._selectedAttributes[ name ] = v
      self._lastSelection = name
    self.rescan()
      
  
  def _comboTextChanged( self, name ):
    cmb = self._combos.get( name )
    if cmb is None:
      if name == '_type':
        cmb = self._cmbType
      elif name == '_format':
        cmb = self._cmbFormat
      elif name == '_database':
        cmb = self._cmbDatabase
      else:
        return
    c = cmb.currentItem()
    text = unicode( cmb.currentText() )
    if c > 0 and  text == unicode( cmb.text( c ) ): return
    l = list( string_to_list( text ) )
    if not l:
      v = ''
    elif len( l ) == 1:
      v = l[ 0 ]
    else:
      v = l
    self._selectedAttributes[ name ] = v
      
    self._lastSelection = name
    self.rescan()
  
  
  def rescan( self ):
    QApplication.setOverrideCursor( Qt.waitCursor )
    try:
      # Fill selection combos from requests in database
      any= '<' + _t_( 'any' ) + '>'
      preservedCombos = set()
      if  self._lastSelection is not None:
        preservedCombos.add( self._lastSelection )
      if self._cmbType.count() and ( self._write or self._lastSelection == '_type' ):
        preservedCombos.add( '_type' )
      else:
        self._cmbType.clear()
        self._cmbType.insertItem( any )
      if self._cmbFormat.count() and (self._write or self._lastSelection == '_format' ):
        preservedCombos.add( '_format' )
      else:
        self._cmbFormat.clear()
        self._cmbFormat.insertItem( any )
      for a, cmb in self._combos.iteritems():
        if cmb.editable():
          cmb._modificationTimer.startInternalModification()
        elif cmb.count() and self._write:
          preservedCombos.add( a )
        if a not in preservedCombos:
          cmb.clear()
          cmb.insertItem( any )
      
      if self._cmbDatabase is not None:
        selected = self._selectedAttributes.get( '_database' )
        for i in xrange( 1, self._cmbDatabase.count() ):
          if unicode( self._cmbDatabase.text( i ) ) == selected:
            self._cmbDatabase.setCurrentItem( i )
            break
        else:
          self._cmbDatabase.setCurrentItem( 0 )
      typesSet = set()
      formatsSet = set()
      combosSets = dict( ((i,set()) for i in self._combos ) )
      selected = self._selectedAttributes.get( '_type' )
      if selected is not None:
        selectedTypes = [ selected ]
      else:
        selectedTypes = self._requestedTypes
      required = {}
      for k, v in self._requiredAttributes.iteritems():
        required[ str( k ) ] = v
      for k, v in self._selectedAttributes.iteritems():
        required[ str( k ) ] = v
      required[ '_type' ] = selectedTypes
      required[ '_format' ] = self._possibleFormats
      # create type and format combo
      if '_type' not in preservedCombos:
        if self._write:# if the search diskitem is a writeDiskItem, it doesn't exist in the database and can have a type is not yet present in the database
          typesList=[(t,) for t in self._possibleTypes]
        else:
          typesList=self._database.findAttributes( ( '_type', ), {}, **required ) # types represented in the database : there is at least one diskitem of that type in the database
        for t in sorted(typesList):
          t = t[0]
          if t not in typesSet:
            self._cmbType.insertItem( t )
            typesSet.add( t )
            if selected is not None and selected == t:
              self._cmbType.setCurrentItem( self._cmbType.count() - 1 )
      if '_format' not in preservedCombos:
        selected = self._selectedAttributes.get( '_format' )
        if self._write:
          formatsList=[(f,) for f in self._possibleFormats]
        else:
          formatsList=self._database.findAttributes( ( '_format', ), {}, **required  )
        for f in sorted(formatsList):
          f = f[0]
          if f not in formatsSet and f is not None:
            self._cmbFormat.insertItem( f )
            formatsSet.add( f )
            if selected is not None and selected == f:
              self._cmbFormat.setCurrentItem( self._cmbFormat.count() - 1 )
      # set selected in required dictionary to take it into account when requesting the database
      selected=self._selectedAttributes.get( '_format' )
      if selected is not None:
        required["_format"]=[selected]
      for a, cmb in self._combos.iteritems():
        if a in preservedCombos: continue
        selected = self._selectedAttributes.get( a )
        s = combosSets[ a ]
        values = set( self._editableAttributesValues.get( a, () ) )
        if a in required:
          values.update( [required.get(a)] )
        elif a in self._attributesValues and self._write:
          values.update( self._attributesValues.get(a) )
        else:
          values.update( [v[0] for v in self._database.findAttributes( ( a, ), {}, **required )] )
        for v in sorted(values):
          if not v: v = ''
          if isinstance( v, basestring ):
            vstring = quote_string(v)
          else:
            vstring=list_to_string(v)
          if vstring not in s:
            cmb.insertItem( vstring )
            s.add( vstring )
            if selected is not None and selected == v:
              cmb.setCurrentItem( cmb.count() - 1 )
      self._ui.tblItems.removeColumns( range(self._ui.tblItems.numCols()) )
      self._ui.tblItems.removeRows( range(self._ui.tblItems.numRows()) )
      keyAttributes = self._database.getTypesKeysAttributes( *selectedTypes )
      header = QStringList()
      self._ui.tblItems.insertColumns( 0, len( keyAttributes ) + 2 )
      for c in [ 'type' ] + keyAttributes + [ 'format' ]:
        header.append( QString( c ) )
      self._ui.tblItems.setColumnLabels( header )
      queryResult = sorted( self._database.findAttributes( [ '_type' ] + keyAttributes + [ '_format', '_uuid' ], selection={}, **required ) )
      self._ui.tblItems.insertRows( 0, len( queryResult ) )
      self._items = []
      row = 0
      for attrs in queryResult:
        for c in xrange( len( attrs ) - 1 ):
          self._ui.tblItems.setText( row, c, ( attrs[ c ] if attrs[ c ] else '' ) )
        row += 1
        self._items.append( attrs[ -1 ] )
      if self._write:
        queryResult = tuple( self._database.createDiskItems( {}, **required  ) )
        row = self._ui.tblItems.numRows()
        self._ui.tblItems.insertRows( row, len( queryResult ) )
        for item in queryResult:
          attrs = [ item.type.name ] + [ unicode(item.get(i)) for i in keyAttributes ] + [ item.format.name ]
          for c in xrange( len( attrs ) ):
            self._ui.tblItems.setText( row, c, ( attrs[ c ] if attrs[ c ] else '' ) )
          row += 1
          self._items.append( item )
      self._ui.labItems.setText( _t_( '%d item(s)' ) % ( len( self._items ), ) )
      if self._items:
        self._ui.tblItems.selectRow( 0 )
        self.itemSelected( 0 )
      else:
        self.itemSelected( None )
      for a, cmb in self._combos.iteritems():
        if cmb.editable():
          selected = self._selectedAttributes.get( a )
          if selected is not None:
            if isinstance( selected, basestring ):
              cmb.setCurrentText( quote_string( selected ) )
            else:
              cmb.setCurrentText( list_to_string( selected ) )
          cmb._modificationTimer.stopInternalModification()
        else:
          if cmb.count() < 3 and cmb.currentItem() < 1:
            cmb.hide()
            cmb._label.hide()
          else:
            cmb.show()
            cmb._label.show()
    finally:
      QApplication.restoreOverrideCursor()


  def getValues( self ):
    return [ (self._items[ i ] if isinstance(self._items[ i ], DiskItem) else self._database.getDiskItemFromUuid(self._items[ i ])) for i in xrange(self._ui.tblItems.numRows()) if self._ui.tblItems.isRowSelected( i ) ]
  
  def getAllValues( self ):
    """
    Returns all diskitems currently in the list, not only the selected ones.
    """
    return [ (item if isinstance(item, DiskItem) else self._database.getDiskItemFromUuid(item)) for item in self._items ]


  @staticmethod
  def diskItemDisplayText( diskItem ):
    text = ''
    if diskItem:
      # Name
      text += '<h2>' + htmlEscape( diskItem.fileName() ) + '</h2>'
      # Type
      text += '<b>'+ htmlEscape( _t_('Type') )+': </b>'
      if diskItem.type: text += htmlEscape( diskItem.type.name )
      else: text += _t_('None')
      text += '<br/>\n'
      # Format
      text += '<b>'+ htmlEscape( _t_('Format') ) +': </b>'
      if diskItem.format:
          text += htmlEscape( diskItem.format.name )
      else: text += _t_('None')
      text += '<br/>\n'
      # Format
      text += '<b>'+ _t_('Uuid') + ': </b>'
      if diskItem._uuid:
          text += htmlEscape( unicode( diskItem._uuid ) )
      else: text += _t_('None')
      text += '<br/>\n'
      # Directory
      if diskItem.parent:
        text += '<b>'+ htmlEscape( _t_('Directory') )+ ': </b>'+ htmlEscape( diskItem.parent.fullPath() ) + '<br/>\n'
      # Files
      text += '<b>'+ htmlEscape( _t_('Files') ) + ': </b>'
      text += '['
      fileNames = diskItem.fileNames()
      if fileNames:
        text += ' ' + htmlEscape( fileNames[0] )
        for f in fileNames[ 1: ]:
          text += ', ' + htmlEscape( f )
        text += ' '
      text += ']<br/>\n'

      # Attributes
      p = {}
      parent = diskItem.parent
      if parent is not None:
        p = parent.attributes()
      for k in diskItem._globalAttributes.keys() + \
               diskItem._minfAttributes.keys() + \
               diskItem._otherAttributes.keys():
        if p.has_key( k ):
          del p[ k ]
      o = diskItem._otherAttributes.copy()
      for k in diskItem._minfAttributes.keys():
        if o.has_key( k ):
          del o[ k ]
      attributeSets = ( 
        ( 'Hierarchy attributes', diskItem._globalAttributes ),
        #( 'Hierarchy weak attributes', diskItem._localAttributes ),
        ( 'Minf attributes', diskItem._minfAttributes ),
        ( 'Other attributes', o ),
      )
      for l, d in attributeSets:
        if not d: continue
        text += '<b>'+ htmlEscape( _t_( l ) ) +': </b><br/>\n<blockquote>'
        for ( n, v ) in d.items():
          if n == 'name_serie' or \
             n.startswith( 'pool_header.' ) or \
             n.startswith( 'RECO_' ):
            continue
          text += '<em>'+ htmlEscape( _t_( n ) ) +'</em> = ' + htmlEscape( unicode(v) ) + '<br/>\n'
        text += '</blockquote>'


      # Special Attributes
      text += '<b>'+ htmlEscape( _t_('Special attributes' ) )+': </b><br/>\n<blockquote>'
      text += '<em>'+ htmlEscape( _t_( 'Minf file name' ) ) +'</em> = <code>' + htmlEscape( os.path.basename( diskItem.minfFileName() ) ) + '</code><br/>\n'
      text += '<em>'+ htmlEscape( _t_( 'priority' ) ) +'</em> = ' + htmlEscape( unicode(diskItem.priority() ) ) + '<br/>\n'
      text += '<em>'+ htmlEscape( _t_( 'identified' ) ) +'</em> = ' + unicode( diskItem._identified ) + '<br/>\n'
      #if isinstance( diskItem, Directory ):
        #text += '<em>'+ htmlEscape( _t_( 'lastModified' ) ) +'</em> = ' + htmlEscape( time.asctime( time.localtime( diskItem.lastModified ) ) ) + '<br/>\n'
        #text += '<em>'+ htmlEscape( _t_( 'check_directory_time_only' ) ) +'</em> = ' + htmlEscape( unicode( diskItem._topParent()._check_directory_time_only ) ) + '<br/>\n'
        
      text += '</blockquote>'
      
      # Scanner
      #if neuroConfig.userLevel > 0 and getattr( diskItem, 'scanner', None ) is not None:
        #text += '<b>'+ _t_( 'Scanner' )  +': </b><br/>\n<blockquote>'

        #text += '<b>'+ _t_( 'Rules' ) +': </b><br/>\n<blockquote>'
        #for rule in diskItem.scanner.rules:
          #text += '<code>'+ htmlEscape(str(rule.pattern.pattern)) +'</code>: ' + str(rule.type) + '<br/>\n'
          
        #text += '</blockquote>'

        #text += '<b>'+ _t_( 'Possible types' ) +': </b><br/>\n<blockquote>'
        #for t in sorted( [str(i) for i in diskItem.scanner.possibleTypes.keys()] ):
          #text += '<code>' + htmlEscape( t ) + '</code><br/>\n'
        #text += '</blockquote>'

        #text += '</blockquote>'
        
    return text
  
  
  def resetSelectedAttributes( self, selectedAttributes={} ):
    self._selectedAttributes = {}
    self._lastSelection = None
    if isinstance( selectedAttributes, DiskItem ):
      # if selectedAttributes is a diskitem, use getHierarchy instead of get to calling aimsFileInfo when searching attributes values.
      get=selectedAttributes.getHierarchy
      if selectedAttributes.type is not None:
        self._selectedAttributes[ '_type' ] = selectedAttributes.type.name
      if selectedAttributes.format is not None:
        self._selectedAttributes[ '_format' ] = selectedAttributes.format.name
    else:
      get=selectedAttributes.get
    v = get( '_database' )
    if v is not None:
      self._selectedAttributes[ '_database' ] = v
    for n in self._combos:
      v = get( n )
      if v is not None:
        self._selectedAttributes[ n ] = v
    self.rescan()
    
