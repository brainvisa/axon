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
from backwardCompatibleQt import QLineEdit, SIGNAL, QPushButton, QToolButton, \
               Qt, QIcon, QWidget, QFileDialog, QStringList, QVBoxLayout, \
               QListWidget, QHBoxLayout, QSpacerItem, QSizePolicy, QSize
from soma.wip.application.api import findIconFile
from soma.qtgui.api import largeIconSize
from brainvisa.data.qtgui.diskItemBrowser import DiskItemBrowser
from neuroDataGUI import DataEditor, StringListEditor
from neuroProcesses import defaultContext
import neuroProcesses
import neuroProcessesGUI
from neuroDiskItems import DiskItem, Directory
import neuroConfig
from neuroException import showException, HTMLMessage

#----------------------------------------------------------------------------
class RightClickablePushButton( QPushButton ):
  def mousePressEvent( self, e ):
    if e.button() == Qt.RightButton:
      self.emit( SIGNAL( 'rightPressed' ) )
    else:
      QPushButton.mousePressEvent( self, e )

#----------------------------------------------------------------------------
class DiskItemEditor( QWidget, DataEditor ):
  def __init__( self, parameter, parent, name, write = False, context = None ):
    if getattr( DiskItemEditor, 'pixShow', None ) is None:
      setattr( DiskItemEditor, 'pixShow', QIcon( findIconFile( 'eye.png' )) )
      setattr( DiskItemEditor, 'pixEdit', QIcon( findIconFile( 'pencil.png' )) )
      setattr( DiskItemEditor, 'pixDatabaseRead', QIcon( findIconFile( 'database_read.png' )) )
      setattr( DiskItemEditor, 'pixDatabaseWrite', QIcon( findIconFile( 'database_write.png' )) )
      setattr( DiskItemEditor, 'pixBrowseRead', QIcon( findIconFile( 'browse_read.png' )) )
      setattr( DiskItemEditor, 'pixBrowseWrite', QIcon( findIconFile( 'browse_write.png' )) )
    QWidget.__init__( self, parent )
    if name:
      self.setObjectName(name)
    hLayout=QHBoxLayout()
    self.setLayout(hLayout)
    hLayout.setSpacing( 4 )
    hLayout.setMargin(0)
    self._write = write
    self.parameter =  parameter
    self.led = QLineEdit( )
    hLayout.addWidget(self.led)
    self.connect( self.led, SIGNAL( 'textChanged( const QString & )' ), self.textChanged )
    self.connect( self.led, SIGNAL( 'returnPressed()' ), self.checkValue )
    self.setFocusProxy( self.led )
    self.diskItem = None
    self.forceDefault = False
    self._context = context

    self.btnShow = RightClickablePushButton( )
    hLayout.addWidget(self.btnShow)
    self.btnShow.setCheckable(True)
    self.btnShow.setIcon( self.pixShow )
    self.btnShow.setIconSize(QSize(*largeIconSize))
    self.btnShow.setFocusPolicy( Qt.NoFocus )
    self.btnShow.setEnabled( False )
    if not neuroProcesses.getViewer( (self.parameter.type, self.parameter.formats[0] ), 1 ):
      self.btnShow.hide()
    self._view = None
    self.connect( self.btnShow, SIGNAL( 'clicked()' ), self.showPressed )
    self.connect( self.btnShow, SIGNAL( 'rightPressed' ), self.openViewerPressed )
    self._edit = None
    self.btnEdit = RightClickablePushButton( )
    hLayout.addWidget(self.btnEdit)
    self.btnEdit.setCheckable(True)
    self.btnEdit.setIcon( self.pixEdit )
    self.btnEdit.setIconSize(QSize(*largeIconSize))
    self.btnEdit.setFocusPolicy( Qt.NoFocus )
    self.btnEdit.setEnabled( 0 )
    if not neuroProcesses.getDataEditor( (self.parameter.type, self.parameter.formats[0] ) ):
      self.btnEdit.hide()
    self.connect( self.btnEdit, SIGNAL( 'clicked()' ), self.editPressed )
    self.connect( self.btnEdit, SIGNAL( 'rightPressed' ),
                  self.openEditorPressed )
    self.btnDatabase = QPushButton( )
    hLayout.addWidget(self.btnDatabase)
    if write:
      self.btnDatabase.setIcon( self.pixDatabaseWrite )
      self.btnDatabase.setIconSize(QSize(*largeIconSize))
      self.btnDatabase.setToolTip(_t_("Browse the database (save mode)"))
    else:
      self.btnDatabase.setIcon( self.pixDatabaseRead )
      self.btnDatabase.setIconSize(QSize(*largeIconSize))
      self.btnDatabase.setToolTip(_t_("Browse the database (load mode)"))
    self.btnDatabase.setFocusPolicy( Qt.NoFocus )
    if hasattr( parameter, 'databaseUserLevel' ):
      x = parameter.databaseUserLevel
      if x > neuroConfig.userLevel:
        self.btnDatabase.hide()
    self.connect( self.btnDatabase, SIGNAL( 'clicked()' ), self.databasePressed )
    self.databaseDialog = None
    self.btnBrowse = QPushButton( )
    hLayout.addWidget(self.btnBrowse)
    if write:
      self.btnBrowse.setIcon( self.pixBrowseWrite )
      self.btnBrowse.setIconSize(QSize(*largeIconSize))
      self.btnBrowse.setToolTip(_t_("Browse the filesystem (save mode)"))
    else:
      self.btnBrowse.setIcon( self.pixBrowseRead )
      self.btnBrowse.setIconSize(QSize(*largeIconSize))
      self.btnBrowse.setToolTip(_t_("Browse the filesystem (load mode)"))
    self.btnBrowse.setFocusPolicy( Qt.NoFocus )
    if hasattr( parameter, 'browseUserLevel' ):
      x = parameter.browseUserLevel
      if x > neuroConfig.userLevel:
        self.btnBrowse.hide()
    self.connect( self.btnBrowse, SIGNAL( 'clicked()' ), self.browsePressed )
    self.browseDialog = None
    self._textChanged = False

    self._selectedAttributes = {}
    self.parameter.valueLinkedNotifier.add( self.valueLinked )

  def __del__( self ):
      self._ = None

  def setContext( self, newContext ):
    oldContext = ( self.btnShow.isChecked(), self._view,
                   self.btnEdit.isChecked(), self._edit )
    if newContext is None:
      self.btnShow.setChecked( False )
      self.btnEdit.setChecked( False )
      self._view = None
      self._edit = None
    else:
      if len( newContext ) >=4:
        o, v, z, e = newContext
      else:
        o, v = newContext
        z = e = 0
      self.btnShow.setChecked( o )
      self._view = v
      self.btnEdit.setChecked( z )
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
      self.emit( SIGNAL('newValidValue'), unicode(self.objectName()), self.diskItem )
    else:
      self.led.setText( self.diskItem.fullPath() )
      self.checkReadable()
      self.emit( SIGNAL('newValidValue'), unicode(self.objectName()), self.diskItem )
    self._textChanged = 0
    self.forceDefault = 0

  def checkReadable( self ):
    if self.btnShow:
      enabled = 0
      v = neuroProcesses.getViewer( (self.parameter.type, self.parameter.formats[0] ), 1 )
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
      v = neuroProcesses.getDataEditor( (self.parameter.type, self.parameter.formats[0] ) )
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
      self.emit( SIGNAL('noDefault'), unicode(self.objectName()) )

  def checkValue( self ):
    if self._textChanged:
      self.setValue( unicode( self.led.text() ) )
  
  def showPressed( self ):
    if self.btnShow.isChecked():
      self.btnShow.setEnabled( 0 )
      v = self.getValue()
      try :
        viewer = neuroProcesses.getViewer( v, 1 )()
        defaultContext().runInteractiveProcess( self._viewerExited, viewer, v )
      except Exception, error :
        raise RuntimeError( HTMLMessage(_t_( 'No viewer could be found or launched for type =<em>%s</em> and format=<em>%s</em>' ) % (unicode( v.type ), unicode(v.format))) )
    else:
      self._view = None


  def _viewerExited( self, result ):
    if isinstance( result, Exception ):
      showException( parent=self )
    else:
      self._view = result
    neuroProcessesGUI.mainThreadActions().push( self.btnShow.setEnabled, 1 )


  def openViewerPressed( self ):
    v = self.getValue()
    viewer = neuroProcesses.getViewer( v, 1 )()
    neuroProcessesGUI.showProcess( viewer, v )

  
  def editPressed( self ):
    if self.btnEdit.isChecked():
      self.btnEdit.setEnabled( 0 )
      v = self.getValue()
      editor = neuroProcesses.getDataEditor( v )()
      defaultContext().runInteractiveProcess( self._editorExited, editor, v )
    else:
      self._edit = None
  
  
  def _editorExited( self, result ):
    if isinstance( result, Exception ):
      showException( parent=self )
    else:
      self._edit = result
    neuroProcessesGUI.mainThreadActions().push( self.btnEdit.setEnabled, True )
    neuroProcessesGUI.mainThreadActions().push( self.btnEdit.setChecked, False )

  
  def openEditorPressed( self ):
    v = self.getValue()
    editor = neuroProcesses.getDataEditor( v )()
    neuroProcessesGUI.showProcess( editor, v )


  def databasePressed( self ):
    if self.databaseDialog is None or self.parameter._modified:
      self.parameter._modified = 0
      if self.diskItem: # this parameter has already a value, use it to initialize the browser
        selection = self.diskItem.hierarchyAttributes()
        if self.diskItem.type is None :
          selection[ '_type' ] = None
        else :
          selection[ '_type' ] = self.diskItem.type.name
        if self.diskItem.format is None :
          selection[ '_format' ] = None
        else :
          selection[ '_format' ] = self.diskItem.format.name
        
        self.databaseDialog = DiskItemBrowser( self.parameter.database, selection=selection, required=self.parameter.requiredAttributes, parent=self, write = self._write,
        enableConversion=self.parameter.enableConversion )
      else: # if there is no value, we could have some selected attributes from a linked value, use it to initialize the browser
        self.databaseDialog = DiskItemBrowser( self.parameter.database, selection=self._selectedAttributes, required=self.parameter.requiredAttributes, parent=self, write = self._write, enableConversion=self.parameter.enableConversion )
      self.databaseDialog.setWindowTitle( _t_( self.parameter.type.name ) )
      self.connect( self.databaseDialog, SIGNAL( 'accepted()' ), self.databaseAccepted )
    else:
      if self.diskItem:
        self.databaseDialog.resetSelectedAttributes( self.diskItem )
        #self.databaseDialog.rescan(selectedType=self.diskItem.type, selectedFormat=self.diskItem.format, selectedAttributes=self.diskItem.hierarchyAttributes())
      else:
        self.databaseDialog.resetSelectedAttributes( self._selectedAttributes )
       #self.databaseDialog.rescan( selectedAttributes=self._selectedAttributes)
    self.databaseDialog.show()

  def databaseAccepted( self ):
    values=self.databaseDialog.getValues()
    if values:
      self.setValue( values[0] )

  def browsePressed( self ):
    if self.browseDialog is None or self.parameter._modified:
      self.parameter._modified = False
      self.browseDialog = QFileDialog( self )
      if self._write:
        mode = QFileDialog.AnyFile
      else:
        mode = QFileDialog.ExistingFile
      filters = QStringList()
      allPatterns = {}
      dirOnly = True
      for f in self.parameter.formats:
        if f.fileOrDirectory() is not Directory:
          dirOnly = False
        flt = f.getPatterns().unmatch( {}, { 'filename_variable': '*' } )[ 0 ]
        allPatterns[ flt ] = 1
        filters.append( _t_( f.name ) + ' (' + flt + ')' )
      filters.prepend( _t_( 'Recognized formats' ) + ' (' \
        + ' '.join( allPatterns.keys() ) + ')' )
      filters.append( _t_( 'All files' ) + ' (*)' )
      if dirOnly:
        mode = QFileDialog.Directory
      self.browseDialog.setFileMode( mode )
      self.browseDialog.setFilters( filters )
      self.connect( self.browseDialog, SIGNAL( 'accepted()' ), self.browseAccepted )
    # set current directory
    parent = self._context
    if hasattr( parent, '_currentDirectory' ) and parent._currentDirectory:
      self.browseDialog.setDirectory( parent._currentDirectory )
    self.browseDialog.show()

  def browseAccepted( self ):
    value = self.browseDialog.selectedFiles()
    if (len(value) > 0):
      value=unicode(value[0])
    else:
      value=None
    parent = self._context
    if hasattr( parent, '_currentDirectory' ):
      parent._currentDirectory = unicode( self.browseDialog.directory().path() )
    self.setValue( value )
    
  def valueLinked( self, parameterized, name, value ):
    if isinstance( value, DiskItem ):
      self._selectedAttributes = value.hierarchyAttributes()

  def releaseCallbacks( self ):
    self._view = None
    self._edit = None



#----------------------------------------------------------------------------
class DiskItemListEditor( QWidget, DataEditor ):
  
  class DiskItemListSelect( QWidget ): # Ex QSemiModal


    def __init__( self, dilEditor, name, write, context = None,
      databaseUserLevel=0, browseUserLevel=0 ):
      self._context = context
      if getattr( DiskItemListEditor.DiskItemListSelect, 'pixUp', None ) is None:
        setattr( DiskItemListEditor.DiskItemListSelect, 'pixUp', 
          QIcon( findIconFile( 'up.png' )) )
        setattr( DiskItemListEditor.DiskItemListSelect, 'pixDown', 
          QIcon( findIconFile( 'down.png' )) )
        setattr( DiskItemListEditor.DiskItemListSelect, 'pixFindRead', 
          QIcon( findIconFile( 'database_read.png' )) )
        setattr( DiskItemListEditor.DiskItemListSelect, 'pixFindWrite', 
          QIcon( findIconFile( 'database_write.png' )) )
        setattr( DiskItemListEditor.DiskItemListSelect, 'pixBrowseRead', 
          QIcon( findIconFile( 'browse_read.png' )) )
        setattr( DiskItemListEditor.DiskItemListSelect, 'pixBrowseWrite', 
          QIcon( findIconFile( 'browse_write.png' )) )
      QWidget.__init__( self, dilEditor.topLevelWidget(), Qt.Dialog  | Qt.WindowStaysOnTopHint  )
      if name:
        self.setObjectName(name)
      self.setAttribute(Qt.WA_DeleteOnClose, True)
      self.setWindowModality(Qt.WindowModal)
      layout = QVBoxLayout( )
      layout.setMargin( 10 )
      layout.setSpacing( 5 )
      self.setLayout(layout)
      
      self.dilEditor = dilEditor
      self.parameter = dilEditor.parameter
      self.values = []
      self.browseDialog = None
      self.findDialog = None
      
      self.lbxValues = QListWidget( )
      self.connect( self.lbxValues, SIGNAL('currentItemChanged( QListWidgetItem * )'), self._currentChanged )
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
      self.btnDown.setEnabled( 0 )
      self.connect( self.btnDown, SIGNAL( 'clicked()' ), self._down )
      hb.addWidget( self.btnDown )

      spacer = QSpacerItem( 10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum )
      hb.addItem( spacer )

      layout.addLayout( hb )

      hb = QHBoxLayout()
      hb.setSpacing( 6 )

      self.sle = StringListEditor( None, unicode(self.objectName()) )
      hb.addWidget( self.sle )

      btn = QPushButton( )
      if write:
        btn.setIcon( self.pixFindWrite )
      else:
        btn.setIcon( self.pixFindRead )
      btn.setIconSize(QSize(*largeIconSize))
      if databaseUserLevel > neuroConfig.userLevel:
        btn.hide()
      self.connect( btn, SIGNAL( 'clicked()' ), self.findPressed )
      hb.addWidget( btn )

      btn = QPushButton( )
      if write:
        btn.setIcon( self.pixBrowseWrite )
      else:
        btn.setIcon( self.pixBrowseRead )
      btn.setIconSize(QSize(*largeIconSize))
      if browseUserLevel > neuroConfig.userLevel:
        btn.hide()
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
      index = self.lbxValues.currentRow()
      tmp = self.values[ index ]
      self.values[ index ] = self.values[ index - 1 ]
      self.values[ index - 1 ] = tmp
      tmp = self.lbxValues.currentItem().text( 0 )
      item=self.lbxValues.takeItem(index)
      self.lbxValues.insertItem(index-1, item)
      
    def _down( self ):
      index = self.lbxValues.currentRow()
      tmp = self.values[ index ]
      self.values[ index ] = self.values[ index + 1 ]
      self.values[ index + 1 ] = tmp
      tmp = self.lbxValues.text( index )
      item=self.lbxValues.takeItem(index)
      self.lbxValues.insertItem(index+1)
    
    def setValue( self, value ):
      if isinstance( value, ( list, tuple ) ):
        self.values = []
        self.lbxValues.clear()
        for v in value:
          self.values.append( v )
          if v is None:
            self.lbxValues.addItem( '<' + _t_('None') + '>' )
          else:
            self.lbxValues.addItem( v.fileName() )
      
    def _ok( self ):
      self.dilEditor._newValue( self.values )
      self.close( )
      
    def _cancel( self ):
      self.close( )

    def findPressed( self ):
      if self.findDialog is None:
        self.findDialog = DiskItemBrowser( self.parameter.database, 
          required=self.parameter.requiredAttributes, 
          parent=self,
          write = self.parameter._write,
          enableConversion=self.parameter.enableConversion,
          multiple = True )
        self.connect( self.findDialog, SIGNAL( 'accepted()' ), self.findAccepted )
      else:
        self.findDialog.rescan()
      self.findDialog.show()

    def findAccepted( self ):
      value = map( lambda x: x.fullPath(), self.findDialog.getValues() )
      if self.isVisible():
        self.sle.setValue( value )
        self._add()
      else:
        self.emit( SIGNAL( 'accepted' ), value )

    def browsePressed( self ):
      if self.browseDialog is None:
        self.browseDialog = QFileDialog( self.topLevelWidget() )
        self.browseDialog.setFileMode( self.browseDialog.ExistingFiles )
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
          + ' '.join( allPatterns.keys() ) + ')' )
        filters.append( _t_( 'All files' ) + ' (*)' )
        self.browseDialog.setFilters( filters )
        # self.connect( self.browseDialog, SIGNAL( 'fileSelected( const QString & )' ), self.browseAccepted )
        self.connect( self.browseDialog, SIGNAL( 'accepted()' ), self.browseAccepted )
        if dirOnly:
          self.browseDialog.setFileMode( self.browseDialog.Directory )
        parent = self._context
        if hasattr( parent, '_currentDirectory' ) and parent._currentDirectory:
          self.browseDialog.setDir( parent._currentDirectory )
      self.browseDialog.show()

    def browseAccepted( self ):
      parent = self._context
      if hasattr( parent, '_currentDirectory' ):
        parent._currentDirectory = unicode( self.browseDialog.directory().path() )
      l = [str(i) for i in self.browseDialog.selectedFiles()]
      if self.isVisible():
        self.sle.setValue( l ) 
        self._add()
      else:
        self.emit( SIGNAL( 'accepted' ), l )


  def __init__( self, parameter, parent, name, write = 0, context=None ):
    if getattr( DiskItemListEditor, 'pixFindRead', None ) is None:
      setattr( DiskItemListEditor, 'pixFindRead', QIcon( findIconFile( 'database_read.png' )) )
      setattr( DiskItemListEditor, 'pixFindWrite', QIcon( findIconFile( 'database_write.png' )) )
      setattr( DiskItemListEditor, 'pixBrowseRead', QIcon( findIconFile( 'browse_read.png' )) )
      setattr( DiskItemListEditor, 'pixBrowseWrite', QIcon( findIconFile( 'browse_write.png' )) )
    QWidget.__init__( self, parent )
    if name:
      self.setObjectName(name)
    hb=QHBoxLayout()
    self.setLayout(hb)
    hb.setMargin(0)
    hb.setSpacing(4)
    self._context = context
    self.parameter = parameter
    self.write = write
    self.sle = StringListEditor( None, name )
    hb.addWidget(self.sle)
    self._value = None
    self.connect( self.sle, SIGNAL( 'newValidValue' ), self._newTextValue )

    self.btnFind = RightClickablePushButton( )
    hb.addWidget(self.btnFind)
    if write:
      self.btnFind.setIcon( self.pixFindWrite )
    else:
      self.btnFind.setIcon( self.pixFindRead )
    self.btnFind.setIconSize(QSize(*largeIconSize))
    self.btnFind.setFocusPolicy( Qt.NoFocus )
    if hasattr( parameter, 'databaseUserLevel' ):
      x = parameter.databaseUserLevel
      if x > neuroConfig.userLevel:
        self.btnFind.hide()
    self.connect( self.btnFind, SIGNAL( 'clicked()' ), self.findPressed )
    self.connect( self.btnFind, SIGNAL( 'rightPressed' ), self.findRightPressed )
    self.btnBrowse = RightClickablePushButton( )
    hb.addWidget(self.btnBrowse)
    if write:
      self.btnBrowse.setIcon( self.pixBrowseWrite )
    else:
      self.btnBrowse.setIcon( self.pixBrowseRead )
    self.btnBrowse.setIconSize(QSize(*largeIconSize))
    self.btnBrowse.setFocusPolicy( Qt.NoFocus )
    if hasattr( parameter, 'browseUserLevel' ):
      x = parameter.browseUserLevel
      if x > neuroConfig.userLevel:
        self.btnBrowse.hide()
    self.connect( self.btnBrowse, SIGNAL( 'clicked()' ), self.browsePressed )
    self.connect( self.btnBrowse, SIGNAL( 'rightPressed' ), self.browseRightPressed )

    self.setValue( None, 1 )
    
  def getValue( self ):
    return self._value
    
  def setValue( self, value, default = 0 ):
    self.forceDefault = default
    self._value = value
    if isinstance( value, ( list, tuple ) ):
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
    dul = 0
    bul = 0
    if hasattr( self.parameter, 'databaseUserLevel' ):
      dul = self.parameter.databaseUserLevel
    if hasattr( self.parameter, 'browseUserLevel' ):
      bul = self.parameter.browseUserLevel
    w = self.DiskItemListSelect( self, unicode(self.objectName()), self.write,
      databaseUserLevel=dul, browseUserLevel=bul )
    try:
      w.setValue( self.getValue() )
    except:
      showException( parent = self )
    self.connect( w, SIGNAL( 'accepted' ), self._newValue )
    w.findPressed()

  def findRightPressed( self ):
    dul = 0
    bul = 0
    if hasattr( self.parameter, 'databaseUserLevel' ):
      dul = self.parameter.databaseUserLevel
    if hasattr( self.parameter, 'browseUserLevel' ):
      bul = self.parameter.browseUserLevel
    w = self.DiskItemListSelect( self, unicode(self.objectName()), self.write,
      databaseUserLevel=dul, browseUserLevel=bul )
    try:
      w.setValue( self.getValue() )
    except:
      showException( parent = self )
    w.show()
    w.findPressed()

  def browsePressed( self ):
    dul = 0
    bul = 0
    if hasattr( self.parameter, 'databaseUserLevel' ):
      dul = self.parameter.databaseUserLevel
    if hasattr( self.parameter, 'browseUserLevel' ):
      bul = self.parameter.browseUserLevel
    w = self.DiskItemListSelect( self, unicode(self.objectName()), self.write,
      context = self._context, databaseUserLevel=dul, browseUserLevel=bul )
    try:
      w.setValue( self.getValue() )
    except:
      showException( parent = self )
    self.connect( w, SIGNAL( 'accepted' ), self._newValue )
    w.browsePressed()

  def browseRightPressed( self ):
    dul = 0
    bul = 0
    if hasattr( self.parameter, 'databaseUserLevel' ):
      dul = self.parameter.databaseUserLevel
    if hasattr( self.parameter, 'browseUserLevel' ):
      bul = self.parameter.browseUserLevel
    w = self.DiskItemListSelect( self, unicode(self.objectName()), self.write,
      context = self._context, databaseUserLevel=dul, browseUserLevel=bul )
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
    self.emit( SIGNAL('newValidValue'), unicode(self.objectName()), v )
    if not self.forceDefault: self.emit( SIGNAL('noDefault'), unicode(self.objectName()) )

  def checkValue( self ):
    self.sle.checkValue()
