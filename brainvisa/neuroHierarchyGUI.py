# Copyright CEA and IFR 49 (2000-2005)
#
#  This software and supporting documentation were developed by
#      CEA/DSV/SHFJ and IFR 49
#      4 place du General Leclerc
#      91401 Orsay cedex
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

import neuroConfig
if not neuroConfig.newDatabases:
  from neuroHierarchy import *
  import neuroHierarchy
  import neuroProcesses
  from neuroProcesses import *
  from neuroProcessesGUI import *
  from neuroDataGUI import *
  from backwardCompatibleQt import *
  import backwardCompatibleQt as qt
  import neuroConfigGUI
  from neuroException import *
  from brainvisa.Static import *
  import neuroConfig
  from soma.html import htmlEscape
  from StringIO import StringIO
  import qtui
  from soma.qtgui.timered_widgets import QLineEditModificationTimer
  from brainvisa.data.actions import FileProcess, Remove, Move
  #----------------------------------------------------------------------------
  def diskItemDisplayText(diskItem):
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
                diskItem._localAttributes.keys() + \
                diskItem._minfAttributes.keys() + \
                diskItem._otherAttributes.keys():
          if p.has_key( k ):
            del p[ k ]
        o = diskItem._otherAttributes.copy()
        for k in diskItem._minfAttributes.keys():
          if o.has_key( k ):
            del o[ k ]
        attributeSets = ( 
          ( "Ancestors attributes", p ),
          ( 'Hierarchy strong attributes', diskItem._globalAttributes ),
          ( 'Hierarchy weak attributes', diskItem._localAttributes ),
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
        if isinstance( diskItem, Directory ):
          text += '<em>'+ htmlEscape( _t_( 'lastModified' ) ) +'</em> = ' + htmlEscape( time.asctime( time.localtime( diskItem.lastModified ) ) ) + '<br/>\n'
          text += '<em>'+ htmlEscape( _t_( 'check_directory_time_only' ) ) +'</em> = ' + htmlEscape( unicode( diskItem._topParent()._check_directory_time_only ) ) + '<br/>\n'
          
        text += '</blockquote>'
        
        # Scanner
        if neuroConfig.userLevel > 0 and getattr( diskItem, 'scanner', None ) is not None:
          text += '<b>'+ _t_( 'Scanner' )  +': </b><br/>\n<blockquote>'
  
          text += '<b>'+ _t_( 'Rules' ) +': </b><br/>\n<blockquote>'
          for rule in diskItem.scanner.rules:
            text += '<code>'+ htmlEscape(str(rule.pattern.pattern)) +'</code>: ' + str(rule.type) + '<br/>\n'
            
          text += '</blockquote>'
  
          text += '<b>'+ _t_( 'Possible types' ) +': </b><br/>\n<blockquote>'
          for t in sorted( [str(i) for i in diskItem.scanner.possibleTypes.keys()] ):
            text += '<code>' + htmlEscape( t ) + '</code><br/>\n'
          text += '</blockquote>'
  
          text += '</blockquote>'
          
      return text
      #self.setText( text )
  
  
  #----------------------------------------------------------------------------
  class SignalNameButton( QPushButton ):
    def __init__( self, *args, **kwargs ):
      QPushButton.__init__( self, *args ) #, **kwargs )
      self.connect( self, SIGNAL( 'clicked()' ), self.signalName )
      
    def signalName( self ):
      self.emit( PYSIGNAL( 'clicked' ), ( str(self.name()), ) )
      
  
  #----------------------------------------------------------------------------
  class SignalNameComboBox( QComboBox ):
    def __init__( self, editable, parent, name ):
      QComboBox.__init__( self, editable, parent, name )
      self.connect( self, SIGNAL( 'activated(int)' ), self.signalName )
      
    def signalName( self ):
      self.emit( PYSIGNAL( 'activated' ), ( str( self.name() ), ) )
  
    
  
  #----------------------------------------------------------------------------
  class DiskItemBrowser( QDialog ):
    def __init__( self, parameter, parent, write = 0, multiple = 0,
                  selectedType=None, selectedFormat=None, selectedAttributes={} ):
      """
      @type parameter: Parameter
      @parameter: Read or Write DiskItem describing the searched item
      @type selectedType: DiskItemType
      @param selectedType: type to use for the first search (if None the parameter type is used). Can be set if the parameter has a default value, due to linked parameters.
      @type selectedFormat: Format
      @param selectedFormat: format to use for the first search (if None the parameter formats are used). Can be set if the parameter has a default value due to linked parameters. 
      @type selectedAttributes: dict
      @param selectedAttributes: name -> value, attributes to use for the search. Comes from a default value or failed search for a default value (in this case it gives attributes values got from linked attributes even if it remains ambiguity).
      """
      QDialog.__init__( self, parent, None, 1, Qt.WGroupLeader )
      layout = QVBoxLayout( self )
      layout.setAutoAdd( 1 )
  
      p = os.path.join( neuroConfig.mainPath, 'diskitembox.ui' )
      self.ui = qtui.QWidgetFactory().create(p, None, self)
  
      if getattr( self, 'pixNew', None ) is None:
        setattr( self, 'pixNew', QPixmap( os.path.join( neuroConfig.iconPath, 'filenew.png' ) ) )
      
      # change the instruction bar title
      titleLabel = self.ui.child('BV_titleLabel')
      if not write:
          text = _t_('Select the datas to open from the database')
      else:
          text = _t_('Define attributes of the datas to put in the database')
      if multiple:
          text = text + " " + _t_('(multiple selection possible)')
      titleLabel.setText(text)
      
      attGroup = self.ui.child('BV_attributeFrame')
      attGroup.setTitle(_t_('Attributes filter : ') )
      
      resultFrame = self.ui.child('BV_ResultFrame')
      if not write:
          resultFrame.setTitle(_t_('Matching results : ') )
      else:
          resultFrame.setTitle(_t_('Suggested names : ') )
      
      # remove the existings ui-designer widgets
      attributeFrameLayout = attGroup.layout()
      widgetlist = [x for x in attGroup.children() if x.isWidgetType()]
      for x in widgetlist:
        attributeFrameLayout.remove(x)
        attributeFrameLayout.removeChild(x)
        del x
  
      self.list = self.ui.child('BV_filelist')
  
      self.connect( self.list, SIGNAL('currentChanged( QListBoxItem * )'), self.itemSelected )
        
      self.parameter = parameter
      self._write = write
      self._multiple = multiple
  
      if self._multiple:
        self.list.setSelectionMode( QListBox.Extended )
      if not multiple:
        QObject.connect( self.list, SIGNAL( 'doubleClicked( QListBoxItem * )' ), self, SLOT('accept()') )
  
      self.values = [] # list of DiskItems corresponding to self.list content
      self.attributes = {} # attribute name -> list of values corresponding to appropriate combo box
      self.combo = {} # Dictionary of attribute combos (attribute name -> QComboBox instance)
      self.attributesWidgets = [] # List of widgets to be destroyed on rescan
      self.types = [] # list of types corresponding to cmbTypes content
      self.formats = [] # list of formats corresponding to cmbFormats content
  
      self.cmbTypes = None
      self.cmbFormats = None
      
      self._preventRecursiveRescan = 0
      self.rescan( selectedType=selectedType, selectedFormat=selectedFormat, selectedAttributes=selectedAttributes )
  
  
      self.display = self.ui.child('BV_textBrowser')
  
      self.connect( self, PYSIGNAL( 'selected' ), self._selected )
      
      btn = self.ui.child('BV_Ok')
      btn.setText(_t_('Ok'))
      btn.setAutoDefault( False )
      self.connect( btn, SIGNAL( 'clicked()' ), self, SLOT( 'accept()' ) )
      btn = self.ui.child('BV_Cancel')
      btn.setText(_t_('Cancel'))
      btn.setAutoDefault( False )
      self.connect( btn, SIGNAL( 'clicked()' ), self, SLOT( 'reject()' ) )
      btn = self.ui.child('BV_Clear')
      btn.setText(_t_('Clear'))
      btn.setAutoDefault( False )
      self.connect( btn, SIGNAL( 'clicked()' ), self.reset )
  
      self.currentDiskItem = None
      self.itemSelected()
    
    def _selected( self, item ):
      self.currentDiskItem = item
      self.display.setText( diskItemDisplayText( item ) )
  
    def accept( self ):
      QDialog.accept( self )
      self.emit( PYSIGNAL( 'accept' ), () )
    
    def reset( self ):
      self.combo={}
      self.cmbTypes=None
      self.cmbFormats=None
      self.rescan()
  
  # selection method    
    def itemSelected( self ):
      if self.list.count():
        index = self.list.currentItem()
        if index >= 0:
          self.emit( PYSIGNAL('selected'), (self.values[ index ],) )
        else:
          self.emit( PYSIGNAL('selected'), ( None,) )
  
    def slotRescan( self ):
      # This function is necessary in order to avoid signals arguments to
      # polute rescan() optional arguments
      self.rescan()
    
    def rescan( self, preserveAttribute=None, selectedType=None, selectedFormat=None, selectedAttributes={},
                debug=0 ):
      """
      Rescan is called when clicking on the green loop and when the user change selected item in a combo box.
      It updates list of suggested values with files found in a hierarchy that match requested attributes.
      @type preserveAttribute : string
      @param preserveAttribute : attribute for wich the user has choosen a value with the combo box. Must keep this value for the parameter.
      @type selectedType: DiskItemType
      @param selectedType: type to use for the first search (if None the parameter type is used). Can be set if the parameter has a default value, due to linked parameters.
      @type selectedFormat: Format
      @param selectedFormat: format to use for the first search (if None the parameter formats are used). Can be set if the parameter has a default value due to linked parameters. 
      @type selectedAttributes : dict
      @param selectedAttributes : attribute name -> value from a linked parameter (default values for the combo boxes)
      """
      if self._preventRecursiveRescan: return
      if debug: print '!rescan! change cursor'
      QApplication.setOverrideCursor( Qt.waitCursor )
      try:
        self._preventRecursiveRescan = 1
        # Save current selected values for type
        if debug: print '!rescan! Save current selected values for type'
        if not selectedType:
          if self.cmbTypes:
            selectedType = self.types[ self.cmbTypes.currentItem() ]
          else:
            selectedType=self.parameter.type
        # Save current selected values for format
        if debug: print '!rescan! Save current selected values for format'
        if not selectedFormat:
          if self.cmbFormats:
            selectedFormat = self.formats[ self.cmbFormats.currentItem() ]
        currentAttributes = {}
        # Save current selected values for other attributes (choosen by user)
        if debug: print '!rescan! Save current selected values for other attributes'
        attributesToBeShown = []
        if preserveAttribute is not None:
          attributesToBeShown.append( preserveAttribute )
        for ( n, cmb ) in self.combo.items():
          if cmb.editable():
            v = unicode( cmb.currentText() )
            if not v: v = None
          else:
            v = self.attributes[ n ][ cmb.currentItem() ]
          # if there is a value for this attribute in selected attributes, replace
          v=selectedAttributes.get(n, v)
          if v is not None:
            currentAttributes[ n ] = v
            attributesToBeShown.append( n )
  
        # clear lists
        if debug: print '!rescan! clear lists'
        self.list.clear()
        self.values = []
        filename_variable = self.attributes.get( 'filename_variable' )
        if preserveAttribute is not None:
          values = self.attributes.get( preserveAttribute )
          self.attributes = {}
          if values: self.attributes[ preserveAttribute ] = values
        else:
          self.attributes = {}
        if filename_variable:
          self.attributes[ 'filename_variable' ] = filename_variable
        self.combo = {}
        if preserveAttribute != 'type':
          self.types = []
        if preserveAttribute != 'format':
          self.formats = [ None ]
        
        # Scan hierarchies to retrieve item values, types and formats
        if debug: print '!rescan! Scan hierarchies to retrieve item values, types and formats'
        values = []
        attributes = currentAttributes.copy()
        attributes.update( self.parameter.requiredAttributes )
        attributesValues = {}
        editableAttributes = {}
        global progressBarFactory, eventsCallback
        if progressBarFactory is not None:
          progressCounts = []
          i = 0
          for count in [len(h.childs()) for h in hierarchies()]:
            i += count
            progressCounts.append( i )
          progressBar = progressBarFactory( progressCounts[ -1 ] )
          hierarchyProgress = 0
        else:
          progressBar = None
        
        # save parameter type and formats before modifying them for the search, they will restored after.
        parameterType=self.parameter.type
        parameterFormats=self.parameter.formats
        self.parameter.type=selectedType
        if selectedFormat:
          self.parameter.formats=[selectedFormat]
        for h in hierarchies():
          values += self.parameter.findItems( h, {}, #selectedAttributes,
            requiredAttributes = attributes,
            attributesValues = attributesValues,
            fileNameAttributes = editableAttributes,
            eventsCallback = eventsCallback,
            progressBar = progressBar )
          if progressBar is not None:
            progressBar.setProgress( progressCounts[ hierarchyProgress ] )
            if eventsCallback is not None:
              eventsCallback()
            hierarchyProgress += 1
        # restore parameter type and formats
        self.parameter.type=parameterType
        self.parameter.formats=parameterFormats
        
        for a in editableAttributes.keys():
          if a == 'filename_variable': continue
          attributesValues.setdefault( a, [] )
        for item in values:
          #if currentType and not isSameDiskItemType( item.type, currentType ):
            #continue
          #if currentFormat and ( currentFormat is not item.format ): continue
          self.values.append( item )
        self.values.sort( lambda a,b: cmp( a.fileName(), b.fileName() ) )
        for item in self.values:
          self.list.insertItem( item.fileName() )
          if item.type and item.type not in self.types:
            self.types.append( item.type )
          if item.format and not item.format in self.formats:
            self.formats.append( item.format )
        if self.list.count():
          self.list.setCurrentItem( 0 )
        else:
          self.emit( PYSIGNAL('selected'), (None,) )
  
        # Build attributes values
        if debug: print '!rescan! Build attributes values'
        for attribute, values in attributesValues.items():
          # Try to see if the category can be edited
          if attribute[ 0 ] != '_':
            d = self.attributes.get( attribute )
            if d is None:
              d = [ None ]
            for v in values:
              if v and v not in d: d.append( v )
            if editableAttributes.get( attribute, 0 ) or \
              len( d ) > 2 or attribute in attributesToBeShown:
              self.attributes[ attribute ] = d
  
        maxComboWidth=400
        attGroup = self.ui.child('BV_attributeFrame')
  
        attributeFrameLayout = attGroup.layout().children()[0]
        attributeFrameLayout.setSpacing(2)
        attributeFrameLayout.setMargin(3)
        
        widgetsToDelete = self.attributesWidgets
        self.attributesWidgets = []
  
        # Build types combo
        if debug: print '!rescan! Build types combo'
        types = self.types
        types.sort( lambda a,b: cmp( a.name, b.name ) )
        # always keep parameter type in choices to be able to revert previous selection
        if selectedType is not self.parameter.type:
          self.types=[self.parameter.type, selectedType]
        else:
          self.types=[selectedType]
        for t in types:
          if t is not  self.parameter.type and t is not selectedType:
            self.types.append( t )
  
        lab = QLabel(_t_("Type"), attGroup, "labelType")
        attributeFrameLayout.addWidget(lab, 0, 0)
        self.attributesWidgets.append( lab )
        lab.show()
  
        spacer1 = QSpacerItem(60,20,QSizePolicy.Maximum,QSizePolicy.Minimum)
        attributeFrameLayout.addItem(spacer1, 0, 1)
  
        self.cmbTypes = SignalNameComboBox( 0, attGroup, 'type' )
        self.cmbTypes.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.Fixed,0))
        self.cmbTypes.show()
        attributeFrameLayout.addWidget(self.cmbTypes, 0, 2)
        self.attributesWidgets.append( self.cmbTypes )
        
        for t in self.types:
          self.cmbTypes.insertItem( _t_( t.name ) )
        self.connect( self.cmbTypes, PYSIGNAL( 'activated' ), self.rescan )
  
        # Build formats combo
        if debug: print '!rescan! Build formats combo'
        l=self.formats[1:]
        l.sort( lambda a,b: cmp( a.name, b.name ) )
        if selectedFormat:
          self.formats=[None, selectedFormat ]
        else:
          self.formats = [ None ]
        for f in l:
          if f is not  selectedFormat:
            self.formats.append( f )
  
        lab = QLabel(_t_("Format"), attGroup, "labelFormat")
        self.attributesWidgets.append( lab )
        lab.show()
        attributeFrameLayout.addWidget(lab, 1, 0)
  
        spacer1 = QSpacerItem(60,20,QSizePolicy.Maximum,QSizePolicy.Minimum)
        attributeFrameLayout.addItem(spacer1, 1, 1)
  
        self.cmbFormats = SignalNameComboBox( 0, attGroup, 'format' )
        self.cmbFormats.show()
        self.cmbFormats.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.Fixed,0))
        attributeFrameLayout.addWidget(self.cmbFormats, 1, 2)
        self.attributesWidgets.append( self.cmbFormats )
  
        self.cmbFormats.insertItem( '<'+_t_('any')+'>' )
        for f in self.formats[1:]:
            self.cmbFormats.insertItem( _t_( f.name ) )
        self.connect( self.cmbFormats, PYSIGNAL( 'activated' ), self.rescan )
  
        # Index in a list without exception if not found
        def index( sequence, value, default ):
          try:
            return sequence.index( value )
          except:
            return default
  
        # Destroy name_serie
        if debug: print '!rescan! Destroy name_serie'
        try: del self.attributes[ 'name_serie' ]
        except: pass
  
        # Other attributes combos
        if debug: print '!rescan! Other attributes combos'
        keys = self.attributes.keys()
        keys.sort()
        layoutline = 2
        for n in keys:
          if n == 'filename_variable': continue
          lab = QLabel(_t_(n), attGroup, 'label'+str(n))
          attributeFrameLayout.addWidget(lab, layoutline, 0)
          self.attributesWidgets.append( lab )
          lab.show()
  
          spacer1 = QSpacerItem(20,20,QSizePolicy.Maximum,QSizePolicy.Minimum)
          attributeFrameLayout.addItem(spacer1, layoutline, 1)
  
          cmb = SignalNameComboBox( 0, attGroup, n )
          if editableAttributes.get( n, False ):
            cmb.setEditable( True )
            cmb._modificationTimer = QLineEditModificationTimer( cmb.lineEdit() )
            cmb._modificationTimer.startInternalModification()
            cmb.insertItem( '' )
            self.connect( cmb._modificationTimer, PYSIGNAL( 'userModification' ), self.rescan )
          else:
            cmb.insertItem( '<'+_t_('any')+'>' )
          cmb.setMinimumWidth( 50 )          
          cmb.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.Fixed,0))
          cmb.show()
          attributeFrameLayout.addWidget(cmb, layoutline, 2)
          self.attributesWidgets.append( cmb )
  
          l = self.attributes[ n ][ 1: ]
          l.sort()
          self.attributes[ n ] = [ None ] + l
          for i in l:
            cmb.insertItem( str(i) )
          idx = index( self.attributes[ n ], selectedAttributes.get(n, currentAttributes.get(n, None)), 0 )
          cmb.setCurrentItem( idx )
          self.connect( cmb, PYSIGNAL( 'activated' ), self.rescan )
          self.combo[ n ] = cmb
          layoutline = layoutline + 1
          if editableAttributes.get( n, False ):
            cmb._modificationTimer.stopInternalModification()
            
        # Restore old values
        if debug: print '!rescan! Restore old values'
        #  Type
        self.cmbTypes.setCurrentItem( index( self.types, selectedType, 0 ) )
        #  Format
        self.cmbFormats.setCurrentItem( index( self.formats, selectedFormat, 0 ) )
        
        # Destroy widgets
        # dunno why there..
        if debug: print '!rescan! Destroy widgets'
        for widget in widgetsToDelete:
          widget.deleteLater()
          del widget
  
        attGroup.show()
  
      finally:
        if debug: print '!rescan! restore cursor'
        self._preventRecursiveRescan = 0
        QApplication.restoreOverrideCursor()
        if debug: print '!rescan! all done'
  
  
    def getValues( self ):
      result = []
      i = 0
      while i < self.list.count():
        if self.list.isSelected( i ):
          result.append( self.values[ i ] )
        i += 1
      return result
  
  
    #def newAttributePressed( self, attributeName ):
      #dialog = defaultContext().dialog( self, 1, _t_( 'Select a new value for <em>%s</em>' ) % ( attributeName, ), Signature( attributeName, String() ), 'Ok', 'Cancel' )
      #if dialog.call() == 0:
        #value = dialog.getValue( attributeName )
        ## Add and select new value
        #self.attributes[ attributeName ].append( value )
        #self.combo[ attributeName ].insertItem( value )
        #self.combo[ attributeName ].setCurrentItem( len(self.attributes[ attributeName ]) -1 )
        #self.rescan( preserveAttribute=attributeName )
  
  
  #----------------------------------------------------------------------------
  class RightClickablePushButton( QPushButton ):
    def mousePressEvent( self, e ):
      if e.button() == Qt.RightButton:
        self.emit( PYSIGNAL( 'rightPressed' ), () )
      else:
        QPushButton.mousePressEvent( self, e )
  
  
  #----------------------------------------------------------------------------
  class DiskItemEditor( QHBox, DataEditor ):
    def __init__( self, parameter, parent, name, write = 0, context = None ):
      if getattr( DiskItemEditor, 'pixShow', None ) is None:
        setattr( DiskItemEditor, 'pixShow', QPixmap( os.path.join( neuroConfig.iconPath, 'eye.png' ) ) )
        setattr( DiskItemEditor, 'pixEdit', QPixmap( os.path.join( neuroConfig.iconPath, 'pencil.png' ) ) )
        setattr( DiskItemEditor, 'pixFindRead', QPixmap( os.path.join( neuroConfig.iconPath, 'find_read.png' ) ) )
        setattr( DiskItemEditor, 'pixFindWrite', QPixmap( os.path.join( neuroConfig.iconPath, 'find_write.png' ) ) )
        setattr( DiskItemEditor, 'pixBrowseRead', QPixmap( os.path.join( neuroConfig.iconPath, 'browse_read.png' ) ) )
        setattr( DiskItemEditor, 'pixBrowseWrite', QPixmap( os.path.join( neuroConfig.iconPath, 'browse_write.png' ) ) )
      QHBox.__init__( self, parent, name )
      self.setSpacing( 4 )
      self._write = write
      self.parameter =  parameter
      self.led = QLineEdit( self )
      self.connect( self.led, SIGNAL( 'textChanged( const QString & )' ), self.textChanged )
      self.connect( self.led, SIGNAL( 'returnPressed()' ), self.checkValue )
      self.setFocusProxy( self.led )
      self.diskItem = None
      self.forceDefault = 0
      self._context = context
  
      self.btnShow = RightClickablePushButton( self )
      self.btnShow.setPixmap( self.pixShow )
      self.btnShow.setToggleButton( 1 )
      self.btnShow.setFocusPolicy( QWidget.NoFocus )
      self.btnShow.setEnabled( 0 )
      if not getViewer( (self.parameter.type, self.parameter.formats[0] ), 1 ):
        self.btnShow.hide()
      self._view = None
      self.connect( self.btnShow, SIGNAL( 'clicked()' ), self.showPressed )
      self.connect( self.btnShow, PYSIGNAL( 'rightPressed' ), self.openViewerPressed )
      self._edit = None
      self.btnEdit = RightClickablePushButton( self )
      self.btnEdit.setPixmap( self.pixEdit )
      self.btnEdit.setToggleButton( 1 )
      self.btnEdit.setFocusPolicy( QWidget.NoFocus )
      self.btnEdit.setEnabled( 0 )
      if not getDataEditor( (self.parameter.type, self.parameter.formats[0] ) ):
        self.btnEdit.hide()
      self.connect( self.btnEdit, SIGNAL( 'clicked()' ), self.editPressed )
      self.connect( self.btnEdit, PYSIGNAL( 'rightPressed' ),
                    self.openEditorPressed )
      self.btnFind = QPushButton( self )
      if write:
        self.btnFind.setPixmap( self.pixFindWrite )
        QToolTip.add(self.btnFind,_t_("Browse the database (save mode)"))
      else:
        self.btnFind.setPixmap( self.pixFindRead )
        QToolTip.add(self.btnFind,_t_("Browse the database (load mode)"))
      self.btnFind.setFocusPolicy( QWidget.NoFocus )
      self.connect( self.btnFind, SIGNAL( 'clicked()' ), self.findPressed )
      self.findDialog = None
      self.btnBrowse = QPushButton( self )
      if write:
        self.btnBrowse.setPixmap( self.pixBrowseWrite )
        QToolTip.add(self.btnBrowse,_t_("Browse the filesystem (save mode)"))
      else:
        self.btnBrowse.setPixmap( self.pixBrowseRead )
        QToolTip.add(self.btnBrowse,_t_("Browse the filesystem (load mode)"))
      self.btnBrowse.setFocusPolicy( QWidget.NoFocus )
      self.connect( self.btnBrowse, SIGNAL( 'clicked()' ), self.browsePressed )
      self.browseDialog = None
      self._textChanged = 0
  
      self._selectedAttributes = {}
      self.parameter.valueLinkedNotifier.add( self.valueLinked )
  
    def __del__( self ):
        self._ = None
          
    def setContext( self, newContext ):
      oldContext = ( self.btnShow.isOn(), self._view,
                    self.btnEdit.isOn(), self._edit )
      if newContext is None:
        self.btnShow.setOn( 0 )
        self.btnEdit.setOn( 0 )
        self._view = None
        self._edit = None
      else:
        if len( newContext ) >=4:
          o, v, z, e = newContext
        else:
          o, v = newContext
          z = e = 0
        self.btnShow.setOn( o )
        self._view = v
        self.btnEdit.setOn( z )
        self._edit = e
      return oldContext
    
  
    def getValue( self ):
      return self.diskItem
      
  
    def setValue( self, value, default = 0 ):
      self.forceDefault = default
      self.diskItem = self.parameter.findValue( value )
      if self.diskItem is None:
        if value is None: self.led.setText( '' )
        if self.btnShow: self.btnShow.setEnabled( 0 )
        if self.btnEdit: self.btnEdit.setEnabled( 0 )
        self.emit( PYSIGNAL('newValidValue'), ( self.name(), self.diskItem, ) )
      else:
        self.led.setText( self.diskItem.fullPath() )
        self.checkReadable()
        self.emit( PYSIGNAL('newValidValue'), ( self.name(), self.diskItem, ) )
      self._textChanged = 0
      self.forceDefault = 0
  
    def checkReadable( self ):
      if self.btnShow:
        enabled = 0
        v = getViewer( (self.parameter.type, self.parameter.formats[0] ), 1 )
        if v:
          self.btnShow.show()
        else:
          self.btnShow.hide()
        if self.diskItem:
          if v:
            enabled = self.diskItem.isReadable()
        self.btnShow.setEnabled( enabled )
      if self.btnEdit:
        enabled = 0
        v = getDataEditor( (self.parameter.type, self.parameter.formats[0] ) )
        if v:
          self.btnEdit.show()
        else:
          self.btnEdit.hide()
        if self.diskItem:
          if v:
            enabled = self.diskItem.isWriteable()
        self.btnEdit.setEnabled( enabled )
  
    def textChanged( self ):
      self._textChanged = 1
      if not self.forceDefault:
        self.emit( PYSIGNAL('noDefault'), ( self.name(),) )
  
    def checkValue( self ):
      if self._textChanged:
        self.setValue( unicode( self.led.text() ) )
    
    def showPressed( self ):
      if self.btnShow.isOn():
        self.btnShow.setEnabled( 0 )
        thread = threading.Thread( target = self._showThread,
          args = ( ExecutionContextGUI(), ) )
        thread.start()
      else:
        self._view = None
  
    def editPressed( self ):
      if self.btnEdit.isOn():
        self.btnEdit.setEnabled( 0 )
        thread = threading.Thread( target = self._editThread,
          args = ( ExecutionContextGUI(), ) )
        thread.start()
      else:
        self._edit = None
  
    def openViewerPressed( self ):
      v = self.getValue()
      viewer = getViewer( v, 1 )()
      win = ProcessView( viewer )
      win.setValue( viewer.signature.keys()[ 0 ], v )
      win.show()
  
    def openEditorPressed( self ):
      v = self.getValue()
      viewer = getDataEditor( v )()
      win = ProcessView( viewer )
      win.setValue( viewer.signature.keys()[ 0 ], v )
      win.show()
  
    def _showThread( self, context ):
      v = self.getValue()
      viewer = getViewer( v, 1 )()
      self._view = context.runProcess( viewer, v )
      mainThreadActions().push( self.btnShow.setEnabled, 1 )
  
    def _editThread( self, context ):
      v = self.getValue()
      viewer = getDataEditor( v )()
      self._edit = context.runProcess( viewer, v )
      mainThreadActions().push( self.btnEdit.setEnabled, 1 )
      mainThreadActions().push( self.btnEdit.setOn, 0 )
  
    def findPressed( self ):
      if self.findDialog is None or self.parameter._modified:
        self.parameter._modified = 0
        if self.diskItem: # this parameter has already a value, use it to initialize the browser
          self.findDialog = DiskItemBrowser( self.parameter, self, 
          write = self._write, selectedType=self.diskItem.type, selectedFormat=self.diskItem.format, selectedAttributes=self.diskItem.hierarchyAttributes() )
        else: # if there is no value, we could have some selected attributes from a linked value, use it to initialize the browser
          self.findDialog = DiskItemBrowser( self.parameter, self, 
          write = self._write, selectedAttributes= self._selectedAttributes)
          #selectedAttributes = self._selectedAttributes )
        self.findDialog.setCaption( _t_( self.parameter.type.name ) )
        self.connect( self.findDialog, PYSIGNAL( 'accept' ), self.findAccepted )
      else:
        if self.diskItem:
          self.findDialog.rescan(selectedType=self.diskItem.type, selectedFormat=self.diskItem.format, selectedAttributes=self.diskItem.hierarchyAttributes())
        else:
          self.findDialog.rescan( selectedAttributes=self._selectedAttributes)
      self.findDialog.show()
  
    def findAccepted( self ):
      self.setValue( self.findDialog.currentDiskItem )
  
    def browsePressed( self ):
      if self.browseDialog is None or self.parameter._modified:
        self.parameter._modified = 0
        self.browseDialog = FileDialog( self.topLevelWidget() )
        if self._write:
          mode = QFileDialog.AnyFile
        else:
          mode = QFileDialog.ExistingFile
        filters = QStringList()
        allPatterns = {}
        dirOnly = 1
        for f in self.parameter.formats:
          if f.fileOrDirectory() is not Directory:
            dirOnly = 0
          flt = f.getPatterns().unmatch( {}, { 'filename_variable': '*' } )[ 0 ]
          allPatterns[ flt ] = 1
          filters.append( _t_( f.name ) + ' (' + flt + ')' )
        filters.prepend( _t_( 'Recognized formats' ) + ' (' \
          + string.join( allPatterns.keys(), ';' ) + ')' )
        filters.append( _t_( 'All files' ) + ' (*)' )
        if dirOnly:
          mode = QFileDialog.Directory
        self.browseDialog.setMode( mode )
        self.browseDialog.setFilters( filters )
        self.connect( self.browseDialog, PYSIGNAL( 'accept' ), self.browseAccepted )
      # set current directory
      parent = self._context
      if hasattr( parent, '_currentDirectory' ) and parent._currentDirectory:
        self.browseDialog.setDir( parent._currentDirectory )
      self.browseDialog.show()
  
    def browseAccepted( self ):
      value = unicode( self.browseDialog.selectedFile() )
      parent = self._context
      if hasattr( parent, '_currentDirectory' ):
        parent._currentDirectory = unicode( self.browseDialog.dirPath() )
      self.setValue( unicode( self.browseDialog.selectedFile() ) )
      
    def valueLinked( self, parameterized, name, value ):
      if isinstance( value, DiskItem ):
        self._selectedAttributes = value.hierarchyAttributes()
  
    def releaseCallbacks( self ):
      self._view = None
      self._edit = None
  
  
  #----------------------------------------------------------------------------
  class FileDialog( QFileDialog ):
    def __init__( self, parent ):
      QFileDialog.__init__( self, parent )
  
    def accept( self ):
      QFileDialog.accept( self )
      self.emit( PYSIGNAL( 'accept' ), () )
  
  
  #----------------------------------------------------------------------------
  class DiskItemListEditor( QHBox, DataEditor ):
    
    class DiskItemListSelect( QWidget ): # Ex QSemiModal
  
  
      def __init__( self, dilEditor, name, write, context = None ):
        self._context = context
        if getattr( DiskItemListEditor.DiskItemListSelect, 'pixUp', None ) is None:
          setattr( DiskItemListEditor.DiskItemListSelect, 'pixUp', 
            QPixmap( os.path.join( neuroConfig.iconPath, 'up.png' ) ) )
          setattr( DiskItemListEditor.DiskItemListSelect, 'pixDown', 
            QPixmap( os.path.join( neuroConfig.iconPath, 'down.png' ) ) )
          setattr( DiskItemListEditor.DiskItemListSelect, 'pixFindRead', 
            QPixmap( os.path.join( neuroConfig.iconPath, 'find_read.png' ) ) )
          setattr( DiskItemListEditor.DiskItemListSelect, 'pixFindWrite', 
            QPixmap( os.path.join( neuroConfig.iconPath, 'find_write.png' ) ) )
          setattr( DiskItemListEditor.DiskItemListSelect, 'pixBrowseRead', 
            QPixmap( os.path.join( neuroConfig.iconPath, 'browse_read.png' ) ) )
          setattr( DiskItemListEditor.DiskItemListSelect, 'pixBrowseWrite', 
            QPixmap( os.path.join( neuroConfig.iconPath, 'browse_write.png' ) ) )
        QWidget.__init__( self, dilEditor.topLevelWidget(), name,
          Qt.WType_Dialog + Qt.WGroupLeader + Qt.WStyle_StaysOnTop + Qt.WShowModal )
        layout = QVBoxLayout( self )
        layout.setMargin( 10 )
        layout.setSpacing( 5 )
        
        self.dilEditor = dilEditor
        self.parameter = dilEditor.parameter
        self.values = []
        self.browseDialog = None
        self.findDialog = None
        
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
        hb.setSpacing( 6 )
  
        self.sle = StringListEditor( self, self.name() )
        hb.addWidget( self.sle )
  
        btn = QPushButton( self )
        if write:
          btn.setPixmap( self.pixFindWrite )
        else:
          btn.setPixmap( self.pixFindRead )
        self.connect( btn, SIGNAL( 'clicked()' ), self.findPressed )
        hb.addWidget( btn )
        
        btn = QPushButton( self )
        if write:
          btn.setPixmap( self.pixBrowseWrite )
        else:
          btn.setPixmap( self.pixBrowseRead )
        self.connect( btn, SIGNAL( 'clicked()' ), self.browsePressed )
        hb.addWidget( btn )
        
        layout.addLayout( hb )
              
  #      self.editor = self.parameter.editor( self, self.name() )
  #      layout.addWidget( self.editor )
        
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
          self.sle.setValue( [ self.values[ index ].fullPath() ] )
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
          self.sle.setValue( None )
          self.btnRemove.setEnabled( 0 )
          self.btnUp.setEnabled( 0 )
          self.btnDown.setEnabled( 0 )
  
      def _add( self ):
        try:
          for v in map( self.parameter.findValue, self.sle.getValue() ):
            self.values.append( v )
            if v is None:
              self.lbxValues.insertItem( '<' + _t_('None') + '>' )
            else:
              self.lbxValues.insertItem( v.fileName() )
          self.lbxValues.setCurrentItem( len( self.values ) - 1 )   
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
        if type( value ) in ( types.ListType, types.TupleType ):
          self.values = []
          self.lbxValues.clear()
          for v in value:
            self.values.append( v )
            if v is None:
              self.lbxValues.insertItem( '<' + _t_('None') + '>' )
            else:
              self.lbxValues.insertItem( v.fileName() )
        
      def _ok( self ):
        self.dilEditor._newValue( self.values )
        self.close( 1 )
        
      def _cancel( self ):
        self.close( 1 )
  
      def findPressed( self ):
        if self.findDialog is None:
          self.findDialog = DiskItemBrowser( self.parameter, self,
            write = isinstance( self.parameter, WriteDiskItem ),
            multiple = 1 )
          self.connect( self.findDialog, PYSIGNAL( 'accept' ), self.findAccepted )
        else:
          self.findDialog.rescan()
        self.findDialog.show()
  
      def findAccepted( self ):
        value = map( lambda x: x.fullPath(), self.findDialog.getValues() )
        if self.isVisible():
          self.sle.setValue( value )
          self._add()
        else:
          self.emit( PYSIGNAL( 'accept' ), ( value, ) )
  
      def browsePressed( self ):
        if self.browseDialog is None:
          self.browseDialog = FileDialog( self.topLevelWidget() )
          self.browseDialog.setMode( self.browseDialog.ExistingFiles )
          filters = QStringList()
          allPatterns = {}
          dirOnly = 1
          for f in self.parameter.formats:
            if f.fileOrDirectory() is not Directory:
              dirOnly = 0
            flt = f.getPatterns().unmatch( {}, { 'filename_variable': '*' } )[ 0 ]
            allPatterns[ flt ] = 1
            filters.append( _t_( f.name ) + ' (' + flt + ')' )
          filters.prepend( _t_( 'Recognized formats' ) + ' (' \
            + string.join( allPatterns.keys(), ';' ) + ')' )
          filters.append( _t_( 'All files' ) + ' (*)' )
          self.browseDialog.setFilters( filters )
          # self.connect( self.browseDialog, SIGNAL( 'fileSelected( const QString & )' ), self.browseAccepted )
          self.connect( self.browseDialog, PYSIGNAL( 'accept' ), self.browseAccepted )
          if dirOnly:
            self.browseDialog.setMode( self.browseDialog.Directory )
          parent = self._context
          if hasattr( parent, '_currentDirectory' ) and parent._currentDirectory:
            self.browseDialog.setDir( parent._currentDirectory )
        self.browseDialog.show()
  
      def browseAccepted( self ):
        parent = self._context
        if hasattr( parent, '_currentDirectory' ):
          parent._currentDirectory = unicode( self.browseDialog.dirPath() )
        l = [str(i) for i in self.browseDialog.selectedFiles()]
        if self.isVisible():
          self.sle.setValue( l ) 
          self._add()
        else:
          self.emit( PYSIGNAL( 'accept' ), ( l, ) )
  
  
    def __init__( self, parameter, parent, name, write = 0, context=None ):
      if getattr( DiskItemListEditor, 'pixFindRead', None ) is None:
        setattr( DiskItemListEditor, 'pixFindRead', QPixmap( os.path.join( neuroConfig.iconPath, 'find_read.png' ) ) )
        setattr( DiskItemListEditor, 'pixFindWrite', QPixmap( os.path.join( neuroConfig.iconPath, 'find_write.png' ) ) )
        setattr( DiskItemListEditor, 'pixBrowseRead', QPixmap( os.path.join( neuroConfig.iconPath, 'browse_read.png' ) ) )
        setattr( DiskItemListEditor, 'pixBrowseWrite', QPixmap( os.path.join( neuroConfig.iconPath, 'browse_write.png' ) ) )
      QHBox.__init__( self, parent, name )
      self._context = context
      self.parameter = parameter
      self.write = write
      self.sle = StringListEditor( self, name )
      self._value = None
      self.connect( self.sle, PYSIGNAL( 'newValidValue' ), self._newTextValue )
  
      self.btnFind = RightClickablePushButton( self )
      if write:
        self.btnFind.setPixmap( self.pixFindWrite )
      else:
        self.btnFind.setPixmap( self.pixFindRead )
      self.btnFind.setFocusPolicy( QWidget.NoFocus )
      self.connect( self.btnFind, SIGNAL( 'clicked()' ), self.findPressed )
      self.connect( self.btnFind, PYSIGNAL( 'rightPressed' ), self.findRightPressed )
      self.btnBrowse = RightClickablePushButton( self )
      if write:
        self.btnBrowse.setPixmap( self.pixBrowseWrite )
      else:
        self.btnBrowse.setPixmap( self.pixBrowseRead )
      self.btnBrowse.setFocusPolicy( QWidget.NoFocus )
      self.connect( self.btnBrowse, SIGNAL( 'clicked()' ), self.browsePressed )
      self.connect( self.btnBrowse, PYSIGNAL( 'rightPressed' ), self.browseRightPressed )
  
      self.setValue( None, 1 )
      
    def getValue( self ):
      return self._value
      
    def setValue( self, value, default = 0 ):
      self.forceDefault = default
      self._value = value
      if type( value ) in ( types.ListType, types.TupleType ):
        r = []
        for v in value:
          if v is None:
            r.append( '' )
          else:
            r.append( str( v ) )
        value = r
      self.sle.setValue( value, default )
      self.forceDefault = 0
    
    def findPressed( self ):
      w = self.DiskItemListSelect( self, self.name(), self.write )
      try:
        w.setValue( self.getValue() )
      except:
        showException( parent = self )
      self.connect( w, PYSIGNAL( 'accept' ), self._newValue )
      w.findPressed()
    
    def findRightPressed( self ):
      w = self.DiskItemListSelect( self, self.name(), self.write )
      try:
        w.setValue( self.getValue() )
      except:
        showException( parent = self )
      w.show()
      w.findPressed()
  
    def browsePressed( self ):
      w = self.DiskItemListSelect( self, self.name(), self.write, 
                                  context = self._context )
      try:
        w.setValue( self.getValue() )
      except:
        showException( parent = self )
      self.connect( w, PYSIGNAL( 'accept' ), self._newValue )
      w.browsePressed()
      
    def browseRightPressed( self ):
      w = self.DiskItemListSelect( self, self.name(), self.write,
                                    context = self._context )
      try:
        w.setValue( self.getValue() )
      except:
        showException( parent = self )
      w.show()
      w.browsePressed()
  
    def _newTextValue( self ):
      textValues = self.sle.getValue()
      if textValues is not None:
        self._newValue( [self.parameter.findValue( x ) for x in textValues] )
      return None
  
    def _newValue( self, v ):
      self.setValue( v )
      self.emit( PYSIGNAL('newValidValue'), ( self.name(), v, ) )
      if not self.forceDefault: self.emit( PYSIGNAL('noDefault'), ( self.name(),) )
  
    def checkValue( self ):
      self.sle.checkValue()
  
  #----------------------------------------------------------------------------
  class ReadDiskItemConstructorEditor( QVBox ):
    def __init__( self, parent = None, name = None ):
      QVBox.__init__( self, parent, name )
      self.type = ObjectSelection( getAllDiskItemTypes(), 
        map( lambda x: _t_( x.name ), getAllDiskItemTypes() ), self )
      self.formats = ObjectsSelection( getAllFormats(),
        map( lambda x: _t_( x.name ), getAllFormats() ), self )
  
  
  #----------------------------------------------------------------------------
  class WriteHierarchyDirectoryEditor( QHBox, DataEditor ):
    def __init__( self, parameter, parent, name, context ):
      if getattr( WriteHierarchyDirectoryEditor, 'pixNew', None ) is None:
        setattr( WriteHierarchyDirectoryEditor, 'pixNew', QPixmap( os.path.join( neuroConfig.iconPath, 'filenew.png' ) ) )
      DataEditor.__init__( self )    
      QHBox.__init__( self, parent, name )
      self.choiceEditor = OpenChoiceEditor( parameter, self, name )
      self.btnCreate = QPushButton( self )
      self.btnCreate.setPixmap( self.pixNew )
      self.connect( self.choiceEditor, PYSIGNAL( 'newValidValue' ),  PYSIGNAL( 'newValidValue' ))
      self.connect( self.choiceEditor, PYSIGNAL( 'noDefault' ),  PYSIGNAL( 'noDefault' ) )
      self.connect( self.btnCreate, SIGNAL( 'clicked()' ), self.createDirectory )
      
    def setValue( self, value, default = 0 ):
      print '!WriteHierarchyDirectoryEditor.setValue!', value
      self.choiceEditor.forceDefault = default
      i = self.choiceEditor.parameter.findIndex( value )
      if i >= 0:
        self.choiceEditor.value = self.choiceEditor.parameter.values[ i ][ 1 ]
        self.choiceEditor.setCurrentItem( i )
      else:
        self.choiceEditor.value = \
          self.choiceEditor.parameter._writeDiskItem.findValue( value )
        if self.choiceEditor.value is None:
          self.choiceEditor.setEditText( '' )
        else:
          self.choiceEditor.setEditText( self.choiceEditor.value.fullPath() )
      self.choiceEditor.forceDefault = 0
      print '!WriteHierarchyDirectoryEditor.setValue! done'
  
    def setContext( self, newContext ):
      return None
  
    def getValue( self ):
      return self.choiceEditor.value
  
    def createDirectory( self ):
      self.choiceEditor.checkValue()
      if self.choiceEditor.value is not None:
        if self.choiceEditor.parameter._linkedDirectory is None:
          raise RuntimeError( HTMLMessage(_t_( 'You must select a linked value for before creating a <em>%s</em>' ) % ( self.name(), )) )
        directory = self.choiceEditor.value.fullPath()
        if not os.path.exists( directory ):
          answer = defaultContext().ask( _t_( 'Do you want to create directory <em>%s</em> ?' ) % directory, _t_( 'Yes' ), _t_( 'No' ) )
          if answer == 0:
            os.mkdir( directory )
            self.choiceEditor.value = self.choiceEditor.parameter._writeDiskItem.findValue( directory )
            choices = self.choiceEditor.parameter.values + \
                  [ ( os.path.basename( directory ), self.choiceEditor.value ) ]
  #d#          print '!WriteHierarchyDirectoryEditor.createDirectory!', self.choiceEditor.parameter, choices
            self.choiceEditor.parameter.setChoices( *choices )
            self.emit( PYSIGNAL( 'newValidValue' ), ( self.name(), self.choiceEditor.value, ) )
  
  
  #----------------------------------------------------------------------------
  class HierarchyBrowser( QWidget ):
    """
    This widget enables to explore databases, get information about stored data, search and manage data.
    Data are shown in a list view with directories and files. The contextual menu offers some actions to perform on data : remove, view/hide (with Anatomist), convert (for graphs 3.0).
    The menu items shown in the contextual menu depend on the selected item in the list view. 
    To add a menu item and a condition function to show it : 
    idMenu=self.popupMenu.insertItem( qt.QIconSet(...), "menu text",  <function call back>)
    self.actionConditions[idMenu]=<condition function : QListViewItem -> boolean>
    
    """
    def __init__( self ):
      QWidget.__init__( self, None, None, qt.Qt.WDestructiveClose )
      if getattr( HierarchyBrowser, 'pixDirectory', None ) is None:
        setattr( HierarchyBrowser, 'pixDirectory', QPixmap( os.path.join( neuroConfig.iconPath, 'folder.png' ) ) )
        setattr( HierarchyBrowser, 'pixFile', QPixmap( os.path.join( neuroConfig.iconPath, 'file.png' ) ) )
        setattr( HierarchyBrowser, 'pixUnknown', QPixmap( os.path.join( neuroConfig.iconPath, 'unknown.png' ) ) )
        setattr( HierarchyBrowser, 'pixFind', QPixmap( os.path.join( neuroConfig.iconPath, 'find_read.png' ) ) )
        setattr( HierarchyBrowser, 'pixView', QPixmap( os.path.join( neuroConfig.iconPath, 'eye.png' ) ) )
        setattr( HierarchyBrowser, 'pixRemove', QPixmap( os.path.join( neuroConfig.iconPath, 'remove.png' ) ) )
        setattr( HierarchyBrowser, 'pixConvert', QPixmap( os.path.join( neuroConfig.iconPath, 'converter.png' ) ) )
  
      self.setCaption( _t_( 'Data browser' ) )
      layout = QVBoxLayout( self )
      layout.setSpacing( 5 )
      layout.setMargin( 10 )
  
      hl = QHBoxLayout( layout )
      hl.setSpacing( 5 )
  
      
      self.lstHierarchy = QListView( self )
      hl.addWidget( self.lstHierarchy )
      self.lstHierarchy.addColumn( _t_( 'name' ) )
      self.lstHierarchy.setRootIsDecorated( True )
      self.lstHierarchy.dragObject=self.dragObject
      self.lstHierarchy.setSorting(-1)
      # enable multiple selection
      self.lstHierarchy.setSelectionMode(QListView.Extended)
      self.refresh()
      
      self.textEditArea = QTextEdit(self)
      self.textEditArea.setReadOnly( True )
  
      hl.addWidget( self.textEditArea )
  
      hl = QHBoxLayout( layout )
      hl.setSpacing( 5 )
  
      spacer = QSpacerItem( 1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum )
      hl.addItem( spacer )
  
      self.btnClose = QPushButton( _t_( 'Close' ), self )
      hl.addWidget( self.btnClose )
      self.btnSearch = QPushButton( _t_( 'Search' ), self )
      hl.addWidget( self.btnSearch )
      self.connect( self.btnSearch, SIGNAL( 'clicked()' ), self.search )
  
      self.connect( self.btnClose, SIGNAL( 'clicked()' ), self.close )
      self.connect( self.lstHierarchy, SIGNAL( 'clicked( QListViewItem * )' ),
                    self.itemSelected )
      self.connect( self.lstHierarchy, SIGNAL( 'expanded( QListViewItem * )' ),
                    self.openItem )
      self.connect( self.lstHierarchy, SIGNAL( 'collapsed( QListViewItem * )' ),
                    self.closeItem )
  
      # add a right click menu to change action for a particular file
      self.popupMenu = qt.QPopupMenu()
      self.actionConditions={} # map id menuitem -> condition function(QListViewItem) : condition that all selected list view item must verify to show this menu item. 
      idView=self.popupMenu.insertItem( qt.QIconSet(self.pixView), "View",  self.menuViewEvent )
      # View menu is shown for diskitems that have a viewer
      self.actionConditions[idView]=self.viewCondition
      idHide=self.popupMenu.insertItem( qt.QIconSet(self.pixView), "Hide",  self.menuHideEvent )
      self.actionConditions[idHide]=self.hideCondition
      idRemove=self.popupMenu.insertItem( qt.QIconSet(self.pixRemove), "Remove",  self.menuRemoveEvent )
      self.actionConditions[idRemove]=self.removeCondition
      idConvert=self.popupMenu.insertItem( qt.QIconSet(self.pixConvert), "Convert to graph 3.1", self.menuConvertEvent )
      self.actionConditions[idConvert]=self.convertCondition
      self.graphConverter=neuroProcesses.getProcess("CorticalFoldsGraphUpgradeFromOld")
      self.graphType=neuroDiskItems.getDiskItemType("Graph")
      self.connect(self.lstHierarchy, qt.SIGNAL( 'contextMenuRequested ( QListViewItem *, const QPoint &, int )'), self.openContextMenu)
    
      self.resize( 800, 600 )
      self.searchResult=None
      neuroConfig.registerObject( self )
    
    def refresh( self ):
      self.lstHierarchy.clear()
      for h in hierarchies():
        item = QListViewItem( self.lstHierarchy )
        item.diskItem = h
        item.setText( 0, h.fileName() )
        item.setPixmap( 0, self.pixDirectory )
        item.setExpandable( bool( h.childs() ) )
        item.setDragEnabled(True)
  
    def close( self, alsoDelete=True ):
      neuroConfig.unregisterObject( self )
      return QVBox.close( self, alsoDelete )
    
    def selectedItems(self):
      """
      Gets items that are currently selected in the listview (as we are in extended selection mode).
      
      @rtype: list of QListViewItem
      @return: items currently selected
      """
      items=[]
      it = QListViewItemIterator(self.lstHierarchy, QListViewItemIterator.Selected)
      while it.current() :
          items.append( it.current() )
          it+=1
      return items
  
    # --------------------------------
    # Contextual menu functions
    # --------------------------------
    def openContextMenu(self):
      """
      Called on contextMenuRequested signal. It opens the popup menu at cursor position if there is an item at this position.
      Menu items visible in the contextual menu depends on the conditions verified by the selection.
      """
      #selection=self.lstHierarchy.selectedItem()
      selectedItems=self.selectedItems()
      if selectedItems:
        for idMenu, cond in self.actionConditions.items(): # show a menu if its condition is checked for all selected items
          showMenu=True
          for selection in selectedItems:
            if not cond(selection):
              showMenu=False
              break
          if showMenu:
            self.popupMenu.setItemVisible(idMenu, True)
          else:
            self.popupMenu.setItemVisible(idMenu, False)
        self.popupMenu.exec_loop(qt.QCursor.pos())
    
    def menuRemoveEvent(self):
      """
      Callback for remove menu. Remove all the selected disk items.
      """
      if qt.QMessageBox.warning(self, _t_("Remove"), _t_("Do you really want to remove these files ? "), qt.QMessageBox.Yes, qt.QMessageBox.No) == qt.QMessageBox.Yes :
        items=self.selectedItems()
        for item in items:
          if item and item.diskItem:
            os.chdir(item.diskItem.get("database"))
            p=FileProcess(item.diskItem.name, Remove(), diskItem=item.diskItem)
            p.doit()
            item.parent().takeItem(item)
    
    def removeCondition(self, item):
      return item and item.diskItem and item.diskItem.parent
            
    def menuViewEvent(self):
      items=self.selectedItems()
      for item in items:
        if item.diskItem:
          viewer=neuroProcesses.getViewer(item.diskItem)
          if viewer:
            item.viewer=neuroProcesses.defaultContext().runProcess(viewer, item.diskItem)
  
    def viewCondition(self, item):
      return item and item.diskItem and not getattr(item, "viewer", None) and neuroProcesses.getViewer(item.diskItem)
    
    def menuHideEvent(self):
      items=self.selectedItems()
      for item in items:
        item.viewer=None
  
    def hideCondition(self, item):
      return item and getattr(item, "viewer", None)
  
    def menuConvertEvent(self):
      items=self.selectedItems()
      for item in items:
        if item.diskItem and self.graphConverter:
          # params : Cortical folds graph, Cortex skeleton, commissure coordinates, transform raw T1 MRI to talairach-AC/PC-anatomist
          try:
            neuroProcesses.defaultContext().runProcess(self.graphConverter, item.diskItem)
          except Exception, e:
              neuroProcesses.defaultContext().error("Error during graph conversion : "+str(e))
      
    def convertCondition(self, item):
      return item and item.diskItem and item.diskItem.get("graph_version", None) == "3.0" and neuroDiskItems.isSameDiskItemType(item.diskItem.type, self.graphType) and self.graphConverter
  
    def search(self):
      """
      Opens a diskItemBrowser to set parameters to describe requested data. 
      """
      rd=neuroHierarchy.ReadDiskItem("Any Type", neuroDiskItems.getAllFormats())
      self.requestDialog=DiskItemBrowser( rd, None, write=0)
      self.requestDialog.setCaption( _t_( rd.type.name ) )
      self.requestDialog.connect( self.requestDialog, qt.PYSIGNAL( 'accept' ), self.requestDialogAccepted )
      self.requestDialog.show()
  
    def requestDialogAccepted(self):
      """
      Calls when the user has sent a data request. The search results are shown in the main listView.
      """
      if self.searchResult:
        self.lstHierarchy.takeItem(self.searchResult)
        del self.searchResult
      self.searchResult=QListViewItem( self.lstHierarchy, self.lstHierarchy.lastItem())
      self.searchResult.diskItem=None
      self.searchResult.setText( 0, "-- Search result --" )
      self.searchResult.setPixmap( 0, self.pixFind )
      self.searchResult.setExpandable( True )
      self.searchResult.setOpen(True)
      self.searchResult.setSelected(True)
      sitem=None
      for item in self.requestDialog.values:
        sitem = QListViewItem( self.searchResult, sitem )
        sitem.diskItem = item
        sitem.setText( 0, item.name )
        sitem.setPixmap( 0, self.pixFile )
        #sitem.setSelected(True)
        sitem.setDragEnabled(True)
  
    def openItem( self, item ):
      if item is not None and item.diskItem is not None:
        childs=item.diskItem.childs()
        childs.sort(lambda x, y: cmp(x.name, y.name))
        sitem=None
        for diskItem in childs:
          sitem = QListViewItem( item, sitem )
          sitem.diskItem = diskItem
          sitem.setText( 0, diskItem.fileName() )
          sitem.setDragEnabled(True)
          if isinstance( diskItem, Directory ):
            sitem.setPixmap( 0, self.pixDirectory )
            sitem.setExpandable( bool( diskItem.childs() ) )
          else:
            if diskItem.type is not None:
              sitem.setPixmap( 0, self.pixFile )
            else:
              sitem.setPixmap( 0, self.pixUnknown )
            sitem.setExpandable( False )
      
    def closeItem( self, item ):
      if item is not None and item.diskItem is not None:
        sitem = item.firstChild()
        while sitem is not None:
          item.takeItem( sitem )
          sitem = item.firstChild()
        item.setExpandable( bool( item.diskItem.childs() ) )
      
    def itemSelected( self, item ):
      if item is not None and item.diskItem is not None:
        t = diskItemDisplayText(item.diskItem)
        self.textEditArea.setText( t )
      else:
        self.textEditArea.setText( '' )
  
    def dragObject(self):
      """
      Called when the user start to drag an item of the listview. It returns a QUriDrag to enable diskitems to be dragged in the console or in a file explorer to move, copy or link files.
      """
      items=self.selectedItems()
      d=qt.QUriDrag(self.lstHierarchy)
      files=qt.QStringList()
      for item in items:
        if item.diskItem:
          for f in item.diskItem.fullPaths():
            files.append(f)
          minfFile=item.diskItem.minfFileName()
          if os.path.exists(minfFile) and minfFile !=item.diskItem.fullPath():
            files.append(minfFile)
      #d=qt.QTextDrag(item.text(0), self)
      d.setFileNames(files)
      # on peut ajouter une icone qui sera visible lors du drag
      # d.setPixmap( ... )
      return d
  
  #----------------------------------------------------------------------------
  class CancelException( Exception ):
    pass
  
  #----------------------------------------------------------------------------
  def eventsCallback():
    if eventsCallback._canceled:
      eventsCallback._canceled = False
      raise CancelException( _t_( 'User interruption' ) )
    # qApp.eventLoop().processEvents( QEventLoop.ExcludeUserInput )
    try:
      qApp.lock()
      qApp.processEvents()
    finally:
      qApp.unlock()
  
  eventsCallback._canceled = False
  
  #----------------------------------------------------------------------------
  def cancelInEventCallback():
    global eventsCallback
    eventsCallback._canceled = True
  
  #----------------------------------------------------------------------------
  class HierarchyProgressDialog( QProgressDialog ):
    def __init__( self, count ):
      QProgressDialog.__init__( self, _t_( 'Reading/updating database...' ),
                                _t_( 'Cancel' ),
                                count, None, 'hierarchyProgress', 1, 
                                Qt.WType_TopLevel )
      self.setCaption( _t_( 'Database' ) )      
      self.connect( self, SIGNAL( 'canceled()' ), cancelInEventCallback )
      self.setProgress( 0 )
    
    def step( self ):
      self.setProgress( self.progress() + 1 )
      
    def focusOutEvent( self, e ):
      self.setFocus()
  
  #----------------------------------------------------------------------------  
  class ProgressBarFactory:
    def __init__( self, count ):
      self._dialog = mainThreadActions().call( HierarchyProgressDialog, count )
    
    def step( self ):
      mainThreadActions().push( self._dialog.step )
      
    def setProgress( self, value ):
      mainThreadActions().push( self._dialog.setProgress, value )
      
    
  #----------------------------------------------------------------------------
  def initializeHierarchyGUI():
    ReadDiskItem.editor = lambda self, parent, name, context: DiskItemEditor( self, parent, name, context=context )
    ReadDiskItem.listEditor = lambda self, parent, name, context: DiskItemListEditor( self, parent, name, context=context )  
    WriteDiskItem.editor = lambda self, parent, name, context: DiskItemEditor( self, parent, name, write=1, context=context )
    WriteDiskItem.listEditor = lambda self, parent, name, context: DiskItemListEditor( self, parent, name, write=1, context=context )
    WriteHierarchyDirectory.editor = lambda self, parent, name, context: WriteHierarchyDirectoryEditor( self, parent, name, context=context )
  
    ReadDiskItem.constructorEditor = Static( ReadDiskItemConstructorEditor )
  
    global progressBarFactory
    if neuroConfig.gui:
      neuroHierarchy.eventsCallback = eventsCallback
      neuroHierarchy.progressBarFactory = ProgressBarFactory
      progressBarFactory = HierarchyProgressDialog
    else:
      progressBarFactory = None
