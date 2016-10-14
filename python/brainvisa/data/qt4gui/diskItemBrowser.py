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
from __future__ import print_function
import sys, os
from itertools import chain

from brainvisa.processing.qtgui.backwardCompatibleQt import QDialog, Qt, QVBoxLayout, QComboBox, Signal, Slot, QLabel, QApplication, QPixmap, QListWidget, QWidget, QGridLayout, QFrame, QSize
from soma.qt4gui.designer import loadUi
from soma.qt_gui.qt_backend.QtGui import QAbstractItemView, QSizePolicy
from soma.qt4gui.api import SimpleTable
from soma.functiontools import partial
from soma.qtgui.api import QLineEditModificationTimer
from soma.html import htmlEscape
from soma.wip.application.api import findIconFile
from soma.uuid import Uuid
from soma.undefined import Undefined
from soma.stringtools import quote_string, unquote_string, string_to_list, list_to_string
from brainvisa.data.neuroDiskItems import DiskItem, getFormats, getDiskItemType
import brainvisa.processes
import types
import six

if sys.version_info[0] >= 3:
    xrange = range
    unicode = str
    basestring = str

#----------------------------------------------------------------------------
class SignalNameComboBox( QComboBox ):

  activatedNamed = Signal(str, int)

  def __init__( self, editable, parent, name ):
    QComboBox.__init__( self, parent )
    if name:
      self.setObjectName(name)
    self.setEditable(editable)
    self.activated[int].connect(self.signalName)
    #self.setMaximumWidth(600)

  @Slot(int)
  def signalName(self, index):
    self.activatedNamed.emit(str(self.objectName()), index)


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

  selected = Signal(DiskItem)

  _savedLayout = None
  
  def __init__( self, database, parent=None, write=False, multiple=False,
                selection={}, required={}, enableConversion=False, exactType=False ):
    """
    """
    QDialog.__init__( self, parent )
    self.setModal(True)
    layout = QVBoxLayout( )
    self.setLayout(layout)

    p = os.path.join( os.path.dirname( __file__ ), 'diskItemBrowser.ui' )
    self._ui = QWidget()
    self._ui = loadUi(p, self._ui)
    layout.addWidget(self._ui)
    
    if write:
      self._ui.labDatabaseIcon.setPixmap( QPixmap( findIconFile( 'database_write.png' ) ) )
    else: 
      self._ui.labDatabaseIcon.setPixmap( QPixmap( findIconFile( 'database_read.png' ) ) )
    
    # the area to show the attributes combos
    scrollarea=self._ui.scrollarea
    scrollarea.setFrameStyle(QFrame.NoFrame)
    self.attributesWidget=QWidget()
    gridLayout = QGridLayout()
    gridLayout.setColumnStretch( 0, 0 )
    gridLayout.setColumnStretch( 1, 1 )
    self.attributesWidget.setLayout(gridLayout)
    scrollarea.setWidget(self.attributesWidget)
    self.attributesWidget.show()
    scrollarea.setWidgetResizable(True)

    self._ui.tblItems.clicked.connect(self.itemSelected)
    self._ui.tblItems.activated.connect(self.itemSelected)
    self._ui.tblItems.entered.connect(self.itemSelected)
    self._ui.tblItems.pressed.connect(self.itemSelected)
    #print('!DiskItemBrowser!', database, selection, required)
    self._requiredAttributes = required
    self._database = database
    self._requestedTypes = database.getAttributeValues( '_type', {}, required )
    #print('!DiskItemBrowser! _requestedTypes', self._requestedTypes)
    if exactType:
      self._possibleTypes = set( self._requestedTypes )
    else:
      self._possibleTypes = set( chain( *( self._database.getTypeChildren(  t ) for t in self._requestedTypes ) ) )
    #print('!DiskItemBrowser! _possibleTypes', self._possibleTypes)
    self._possibleFormats = set( chain( *(self._database.getTypesFormats( t ) for t in self._possibleTypes) ) )
    requestedFormats = database.getAttributeValues( '_format', {}, required )
    if self._possibleFormats:
      if requestedFormats:
        self._possibleFormats = self._possibleFormats.intersection( requestedFormats )
      else:
        requestedFormats = self._possibleFormats
    else:
      self._possibleFormats = set(requestedFormats)
    self._formatsWithConverter = {}
    if enableConversion:
      any = getDiskItemType( 'Any type' )
      for type_format, converter in chain( *( six.iteritems(brainvisa.processes.getConvertersTo( ( any, f ), checkUpdate=False )) for f in getFormats( self._possibleFormats ) ) ):
          type, format = type_format
          if format.name not in self._possibleFormats:
            self._formatsWithConverter[ format.name ] = converter
    self._possibleFormats.update(six.iterkeys(self._formatsWithConverter) )
    #print('!DiskItemBrowser! _possibleFormats', self._possibleFormats)
    self._exactType=exactType
    self._write = write
    self._multiple = multiple

    if self._multiple:
      self._ui.tblItems.setSelectionMode( QAbstractItemView.ExtendedSelection )
    else:
      self._ui.tblItems.doubleClicked.connect(self.accept)

    layoutRow = 0
    e,v,d = self._database.getAttributesEdition()
    databases = v.get( '_database', () )
    if len( databases ) > 1:
      self._cmbDatabase = self._createCombo( _t_( 'Database' ), '_database', False, layoutRow )
      self._cmbDatabase.addItem( '<' + _t_( 'any' ) + '>' )
      for d in databases:
        self._cmbDatabase.addItem( d )
    else:
      self._cmbDatabase = None
    layoutRow += 1
    self._cmbType = self._createCombo( _t_( 'Data type' ), '_type', False, layoutRow )
    layoutRow += 1
    self._cmbFormat = self._createCombo( _t_( 'File format' ), '_format', False, layoutRow )
    layoutRow += 1
    self._combos = {} # Dictionary of attribute combos (attribute name -> QComboBox instance)
    self._editableAttributes, self._attributesValues, self._declaredAttributes = self._database.getAttributesEdition( *self._requestedTypes )
    self._editableAttributes = tuple( self._editableAttributes )
    self._editableAttributesValues = dict( ( (i,set()) for i in self._editableAttributes ) )
    if write:
      searchedTypes=['Any Type']
    else:
      searchedTypes=self._requestedTypes
    for t in searchedTypes:
      for values in self._database.findAttributes( self._editableAttributes, _type=t ):
        for i in xrange( len(values) ):
          if values[ i ]:
            self._editableAttributesValues[ self._editableAttributes[ i ] ].add( values[ i ] )
    #print('!DiskItemBrowser! _editableAttributes', self._editableAttributes)
    #print('!DiskItemBrowser! _editableAttributesValues', self._editableAttributesValues)
    #print('!DiskItemBrowser! _attributesValues', self._attributesValues)
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
    for a in self._declaredAttributes:
        self._combos[ a ] = self._createCombo( _t_( a ), a, True, layoutRow )
        layoutRow += 1
    self._selectedAttributes={}
    # among selection attributes keep those related to the types searched to initialize the combos
    for k, v in six.iteritems(selection):
      if k in allAttributes or k in self._declaredAttributes:
        self._selectedAttributes[ k ] = v

    self._lastSelection = None
    self.rescan()

    self._ui.btnReset.clicked[()].connect(self.resetSelectedAttributes)
    self._ui.btnOk.clicked.connect(self.accept)
    self._ui.btnCancel.clicked.connect(self.reject)
    self._ui.hsplitter.splitterMoved.connect(self.saveLayout)
    self._ui.vsplitter.splitterMoved.connect(self.saveLayout)

  def sizeHint(self):
    attributeSize=self.attributesWidget.sizeHint()
    tableSize=self._ui.grpItems.sizeHint()
    textSize=self._ui.textBrowser.sizeHint()
    return QSize((attributeSize.width()+self._ui.hsplitter.handleWidth()+tableSize.width())*1.2, (attributeSize.height()+self._ui.vsplitter.handleWidth()+textSize.height())*1.2)
  
  def saveLayout( self ):
      DiskItemBrowser._savedLayout = ( self.size(), self._ui.hsplitter.sizes(), self._ui.vsplitter.sizes() )
  
  def restoreLayout( self ):
    if DiskItemBrowser._savedLayout is not None:
      self.resize( DiskItemBrowser._savedLayout[ 0 ] )
      self._ui.hsplitter.setSizes( DiskItemBrowser._savedLayout[ 1 ] )
      self._ui.vsplitter.setSizes( DiskItemBrowser._savedLayout[ 2 ] )
      return True
    return False
  
  def resizeEvent( self, event ):
    QDialog.resizeEvent( self, event )
    if (event.spontaneous()): # take into account the event if it comes from the user and not the application
      self.saveLayout()
  
  def showEvent(self, event):
    QDialog.showEvent(self, event)
    self.restoreLayout()
  
  def _createCombo( self, caption, attributeName, editable, layoutRow ):
    gridLayout = self.attributesWidget.layout()#self._ui.attributesFrame.layout()
    label = QLabel(_t_( caption ) )
    gridLayout.addWidget( label, layoutRow, 0 )
    cmb = SignalNameComboBox( editable, None, attributeName )
    cmb._label = label
    cmb.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Fixed ) )
    if editable:
      cmb._modificationTimer = QLineEditModificationTimer( cmb.lineEdit() )
      cmb._modificationTimer.userModification.connect( partial(
        self._comboTextChanged, name=attributeName ) )
    cmb.activatedNamed.connect(self._comboSelected)
    gridLayout.addWidget( cmb, layoutRow, 1 )
    return cmb

  def itemSelectionChanged( self, dummy1, dummy2 ):
    self.itemSelected()

  def itemSelected( self, index=None ):
    if hasattr( index, 'isValid' ):
      if index.isValid():
        index = index.row()
      else:
        index = None
    if index is not None:
      index = self._tableData.sortedIndex( index )
      item = (self._items[ index ] if isinstance(self._items[ index ], DiskItem) else self._database.database(self._items[index][1]).getDiskItemFromUuid(self._items[ index ][0]))
      self._items[ index ] = item
      self._ui.textBrowser.setText( self.diskItemDisplayText( item ) )
      self.selected.emit(item)
    else:
      self.selected.emit(None)
    if self._multiple:
      self._ui.labItems.setText( _t_( '%d item(s) - %d selected' ) % ( len( self._items ), len(self._ui.tblItems.selectionModel().selectedRows(), ) ) )

  
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
        l = list( string_to_list( unicode( cmb.itemText( index ) ) ) )
        if not l:
          v = ''
        elif len( l ) == 1:
          v = l[ 0 ]
        else:
          v = l
      else:
        v=unquote_string( unicode( cmb.itemText( index ) ) )
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
    c = cmb.currentIndex()
    text = unicode( cmb.currentText() )
    if c > 0 and  text == unicode( cmb.itemText( c ) ): return
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
    def filterUniqueCols( allColsNonUnique, uniquecols, uniquecolsvals,
        attrs ):
      if not allColsNonUnique:
        if len( uniquecolsvals ) == 0:
          for att in attrs[:-1]:
            if att is None: att = ''
            uniquecolsvals.append( att )
        else:
          toremove = set()
          for i in uniquecols:
            att = attrs[i]
            if att is None: att = u''
            if i >= len( uniquecolsvals ):
              while( len( uniquecolsvals ) < i ):
                uniquecolsvals.append( u'' )
              uniquecolsvals.append( att )
              continue
            if uniquecolsvals[i] != att:
              toremove.add( i )
          uniquecols.difference_update( toremove )
          if len( uniquecols ) == 0:
            allColsNonUnique = True
      return allColsNonUnique

    QApplication.setOverrideCursor( Qt.WaitCursor )
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
        self._cmbType.addItem( any )
      if self._cmbFormat.count() and (self._write or self._lastSelection == '_format' ):
        preservedCombos.add( '_format' )
      else:
        self._cmbFormat.clear()
        self._cmbFormat.addItem( any )
      for a, cmb in six.iteritems(self._combos):
        if cmb.isEditable():
          cmb._modificationTimer.startInternalModification()
        elif cmb.count() and self._write:
          preservedCombos.add( a )
        if a not in preservedCombos:
          cmb.clear()
          cmb.addItem( any )
      
      if self._cmbDatabase is not None:
        selected = self._selectedAttributes.get( '_database' )
        for i in xrange( 1, self._cmbDatabase.count() ):
          if unicode( self._cmbDatabase.itemText( i ) ) == selected:
            self._cmbDatabase.setCurrentIndex( i )
            break
        else:
          self._cmbDatabase.setCurrentIndex( 0 )
      typesSet = set()
      formatsSet = set()
      combosSets = dict( ((i,set()) for i in self._combos ) )
      selected = self._selectedAttributes.get( '_type' )
      if selected is not None:
        selectedTypes = [ selected ]
      else:
        selectedTypes = self._requestedTypes
      required = {}
      for k, v in six.iteritems(self._requiredAttributes):
        required[ str( k ) ] = v
      for k, v in six.iteritems(self._selectedAttributes):
        if k not in self._declaredAttributes:
          required[ str( k ) ] = v
      required[ '_type' ] = selectedTypes
      required[ '_format' ] = self._possibleFormats
      # create type and format combo
      if '_type' not in preservedCombos:
        if self._write:# if the search diskitem is a writeDiskItem, it doesn't exist in the database and can have a type is not yet present in the database
          typesList=[(t,) for t in self._possibleTypes]
        else:
          typesList=self._database.findAttributes( ( '_type', ), {}, exactType=self._exactType, **required ) # types represented in the database : there is at least one diskitem of that type in the database
        for t in sorted(typesList):
          if t:
            t = t[0]
            if t not in typesSet:
              self._cmbType.addItem( t )
              typesSet.add( t )
              if selected is not None and selected == t:
                self._cmbType.setCurrentIndex( self._cmbType.count() - 1 )
      if '_format' not in preservedCombos:
        selected = self._selectedAttributes.get( '_format' )
        if self._write:
          formatsList=[(f,) for f in self._possibleFormats]
        else:
          formatsList=self._database.findAttributes( ( '_format', ), {}, exactType=self._exactType, **required  )
        for f in sorted(formatsList):
          if f:
            f = f[0]
            if f not in formatsSet and f is not None:
              self._cmbFormat.addItem( f )
              formatsSet.add( f )
              if selected is not None and selected == f:
                self._cmbFormat.setCurrentIndex( self._cmbFormat.count() - 1 )
      # set selected in required dictionary to take it into account when requesting the database
      selected=self._selectedAttributes.get( '_format' )
      if selected is not None:
        required["_format"]=[selected]
      for a, cmb in six.iteritems(self._combos):
        if a in preservedCombos: continue
        selected = self._selectedAttributes.get( a )
        s = combosSets[ a ]
        values = set( self._editableAttributesValues.get( a, () ) )
        if a in required:
          requiredValue=required.get(a)
          if isinstance( requiredValue, basestring ):
            requiredValue=[requiredValue]
          values.update( requiredValue )
        elif a in self._attributesValues and self._write:
          values.update( self._attributesValues.get(a) )
        else:
          values.update( v[0] for v in self._database.findAttributes( ( a, ), {}, exactType=self._exactType, **required ) )
        if sys.version_info[0] >= 3:
          key_func = lambda x: (type(x).__name__, x)
        else:
          key_func = None
        for v in sorted(values, key=key_func):
          if not v: v = ''
          if isinstance( v, basestring ):
            vstring = quote_string(v)
          elif type( v ) in ( types.ListType, types.TupleType ):
            vstring=list_to_string(v)
          else:
            # WARNING DEBUG
            print('unexpected database value type in DiskItem browser combo:', type(v), 'for attribute:', a)
            try:
              vstring = quote_string( str( v ) )
            except:
              vstring = None
          if vstring is not None and vstring not in s:
            cmb.addItem( vstring )
            s.add( vstring )
            if selected is not None and selected == v:
              cmb.setCurrentIndex( cmb.count() - 1 )
      self._items = []
      rawKeyAttributes = self._database.getTypesKeysAttributes( *selectedTypes )
      keyAttributes = []
      for att in ( 'subject', 'center', 'protocol', 'time_point' ):
        if att in rawKeyAttributes:
          keyAttributes.append( att )
      keyAttributes = keyAttributes + [ att for att in sorted( rawKeyAttributes ) if att not in keyAttributes ]
      keyAttributes.extend(self._declaredAttributes)
      self._tableData = SimpleTable( header=[ 'type' ] + keyAttributes + [ 'format', 'database' ] )
      # database attribute is also needed because two diskitems can have the same attributes values in two different databases
      readItems = set()
      uniquecols = set( range( len( keyAttributes ) + 3 ) )
      uniquecolsvals = []
      allColsNonUnique = False
      if sys.version_info[0] >= 3:
        key_func = lambda x: [(type(y).__name__, y) for y in x]
      else:
        key_func = None
      for attrs in sorted(self._database.findAttributes(
          ['_type'] + keyAttributes + list(self._declaredAttributes)
          + ['_format', '_database', '_uuid'], selection={},
          exactType=self._exactType, **required),
          key=key_func):
        self._tableData.addRow( attrs[:-1] )
        self._items.append( (attrs[-1], attrs[-2], ) )
        readItems.add( tuple( attrs[ :-1 ] ) )
        allColsNonUnique = filterUniqueCols( allColsNonUnique, uniquecols,
          uniquecolsvals, attrs )
      if self._write:
        for item in self._database.createDiskItems( {}, exactType=self._exactType, **required  ):
          attrs = [ item.type.name ] + [ unicode(item.getHierarchy(i)) for i in keyAttributes ] + [ item.format.name, item.getHierarchy('_database') ]
          if tuple( attrs ) not in readItems:
            self._tableData.addRow( attrs )
            self._items.append( item )
            allColsNonUnique = filterUniqueCols( allColsNonUnique, uniquecols,
              uniquecolsvals, attrs )
          for a in self._declaredAttributes:
            v = self._selectedAttributes.get(a)
            if v and not item.getHierarchy(a):
              item._globalAttributes[a] = v
      if len( self._items ) <= 1 \
          or len(uniquecols) == self._tableData.columnCount(None):
        # if only one item, show all columns even if they are (all) unique
        uniquecols = set()
      self._ui.tblItems.setModel( self._tableData )
      self._ui.tblItems.selectionModel().selectionChanged.connect(
        self.itemSelectionChanged)
      self._ui.labItems.setText( _t_( '%d item(s)' ) % ( len( self._items ), ) )
      self._ui.tblItems.horizontalHeader().setMovable( True )
      if self._items:
        self._ui.tblItems.selectRow( 0 )
        self.itemSelected( 0 )
      else:
        self.itemSelected( None )
      for a, cmb in six.iteritems(self._combos):
        if cmb.isEditable():
          selected = self._selectedAttributes.get( a )
          if selected is not None:
            if isinstance( selected, basestring ):
              cmb.setCurrentText( quote_string( selected ) )
            else:
              cmb.setCurrentText( list_to_string( selected ) )
          cmb._modificationTimer.stopInternalModification()
        else:
          if cmb.count() < 3 and cmb.currentIndex() < 1:
            cmb.hide()
            cmb._label.hide()
          else:
            cmb.show()
            cmb._label.show()

      self.attributesWidget.adjustSize()
      self._ui.tblItems.resizeColumnsToContents()
      for i in xrange( len( keyAttributes ) + 3 ):
        self._ui.tblItems.setColumnHidden( i, i in uniquecols )
    finally:
      QApplication.restoreOverrideCursor()


  def getValues( self ):
    return [
      (self._items[i] if isinstance(self._items[i], DiskItem) else self._database.database(self._items[i][1]).getDiskItemFromUuid(self._items[i][0])) \
      for i in [
        self._tableData.sortedIndex(j) for j in sorted(set([k.row() for k in self._ui.tblItems.selectedIndexes()]))
      ]
    ]

  def getAllValues( self ):
    """
    Returns all diskitems currently in the list, not only the selected ones.
    """
    return [
      (item if isinstance(item, DiskItem) else self._database.database(item[1]).getDiskItemFromUuid(item[0])) \
      for item in self._items
    ]


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
      for k in chain(diskItem._globalAttributes.keys(),
                     diskItem._minfAttributes.keys(),
                     diskItem._otherAttributes.keys()):
        if k in p:
          del p[ k ]
      o = diskItem._otherAttributes.copy()
      for k in diskItem._minfAttributes.keys():
        if k in o:
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
  
  def keyPressEvent(self, event):
    if (event.key() == Qt.Key_Return):
      event.ignore()
    else:
      QDialog.keyPressEvent(self, event)
    
  def resetSelectedAttributes(self, diskItem = None, 
                              selectedAttributes={}):
    self._selectedAttributes = {}
    self._lastSelection = None
    if diskItem is not None:
      def get(k):
          # use getHierarchy instead of get to calling aimsFileInfo when searching attributes values.
          v = diskItem.getHierarchy(k)
          if v is None:
              v = selectedAttributes.get(v)
      if diskItem.type is not None:
        self._selectedAttributes[ '_type' ] = diskItem.type.name
      if diskItem.format is not None:
        self._selectedAttributes[ '_format' ] = diskItem.format.name
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
    
