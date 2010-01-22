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

import distutils, os, sys, re
import types
from backwardCompatibleQt import *
from PyQt4 import uic
from PyQt4.QtGui import QKeySequence
import neuroConfig 
import neuroConfigGUI
import neuroLogGUI
import neuroData
from brainvisa.wip import newProcess
from brainvisa.history import ProcessExecutionEvent
from neuroProcesses import procdocToXHTML, writeProcdoc, generateHTMLProcessesDocumentation

import weakref
from soma.minf.xhtml import XHTML
from brainvisa.debug import debugHere
from soma.qtgui.api import QtThreadCall, FakeQtThreadCall, TextBrowserWithSearch, bigIconSize, defaultIconSize
import threading
try:
  import sip
except:
  # for sip 3.x (does it work ??)
  import libsip as sip

import neuroConfig
import neuroProcesses
import neuroException
from soma.qtgui.api import EditableTreeWidget, TreeListWidget
from soma.notification import ObservableList, EditableTree

_mainThreadActions = FakeQtThreadCall()

#----------------------------------------------------------------------------
def startShell():
  neuroConfig.shell = True
  from PyQt4.QtGui import qApp
  mainThreadActions().push( qApp.exit )


#----------------------------------------------------------------------------
def quitRequest():
  a = QMessageBox.warning( None, _t_('Quit'),_t_( 'Do you really want to quit BrainVISA ?' ), QMessageBox.Yes | QMessageBox.Default, QMessageBox.No )
  if a == QMessageBox.Yes:
    if neuroConfig.shell:
      sys.exit()
    else:
      qApp.exit()

#----------------------------------------------------------------------------
_helpWidget = None
def helpRequest():
  sep = '//'
  if neuroConfig.platform == 'windows':
    # I definitely don't understand what is a good file URL like...
    sep = '/'
  url = 'file:' + sep + neuroConfig.getDocFile(os.path.join( 'help', 'index.html' ) )
  openWeb(url)

def openWeb(source):
  try:
    browser = neuroConfig.HTMLBrowser
    if browser is not None:
      browser = distutils.spawn.find_executable( browser )
      if browser:
        if os.spawnl( os.P_NOWAIT, browser, browser, source ) > 0:
          return
  except:
    pass
  global _helpWidget
  if _helpWidget is None:
    _helpWidget = HTMLBrowser( None )
    _helpWidget.setWindowTitle( _t_( 'BrainVISA help' ) )
    _helpWidget.resize( 800, 600 )
  sys.stdout.flush()
  _helpWidget.setSource( source )
  _helpWidget.show()
  _helpWidget.raise_()


_aboutWidget = None
#----------------------------------------------------------------------------
class AboutWidget( QWidget ):
  def __init__( self, parent=None, name=None ):
    QWidget.__init__( self, parent )
    if name :
       self.setObjectName( name )
    layout=QVBoxLayout()
    self.setLayout(layout)
    self.setBackgroundRole( QPalette.Base )
    self.setAutoFillBackground(True)
    hb = QHBoxLayout( )
    layout.addLayout(hb)
    layout.setMargin( 10 )
    self.setWindowTitle( _t_( 'About') )
    if getattr( AboutWidget, 'pixIcon', None ) is None:
      setattr( AboutWidget, 'pixIcon', QIcon( os.path.join( neuroConfig.iconPath, 'icon.png' ) ) )
    self.setWindowIcon( self.pixIcon )

    def buildImageWidget( parent, fileName, desiredHeight=0 ):
      widget = QLabel( parent )
      #widget.setBackgroundRole( QPalette.Base )
      widget.setAlignment( Qt.AlignCenter )
      pixmap = QPixmap( os.path.join( neuroConfig.iconPath, fileName ) )
      if desiredHeight:
        stretch = float( desiredHeight ) / pixmap.height()
        matrix = QMatrix()
        matrix.scale( stretch, stretch )
        pixmap = pixmap.transformed( matrix )
      widget.setPixmap( pixmap )
      return widget

    widget = buildImageWidget( None, 'brainvisa.png' )
    hb.addWidget(widget)
    label = QLabel( neuroConfig.versionText() )
    hb.addWidget(label)
    #label.setBackgroundRole( QPalette.Base )
    label.setMargin( 4 )
    font = QFont()
    font.setPointSize( 30 )
    label.setFont( font )

    vb = QVBoxLayout( )
    hb.addLayout(vb)
    widget = buildImageWidget( None, 'ifr49.png', desiredHeight=60 )
    vb.addWidget(widget)
    widget.setMargin( 5 )
    widget = buildImageWidget( None, 'neurospin.png', desiredHeight=40 )
    vb.addWidget(widget)
    widget.setMargin( 5 )
    widget = buildImageWidget( None, 'shfj.png', desiredHeight=40 )
    vb.addWidget(widget)
    widget.setMargin( 5 )
    widget = buildImageWidget( None, 'mircen.png', desiredHeight=40 )
    vb.addWidget(widget)
    widget.setMargin( 5 )
    widget = buildImageWidget( None, 'inserm.png', desiredHeight=40 )
    vb.addWidget(widget)
    widget.setMargin( 5 )
    widget = buildImageWidget( None, 'cnrs.png', desiredHeight=60 )
    vb.addWidget(widget)
    widget.setMargin( 5 )
    widget = buildImageWidget( None, 'chups.png', desiredHeight=40 )
    vb.addWidget(widget)
    widget.setMargin( 5 )
    widget = buildImageWidget( None, 'parietal.png', desiredHeight=40 )
    vb.addWidget(widget)
    widget.setMargin( 5 )

    if parent is None:
      px = ( neuroConfig.qtApplication.desktop().width() - self.sizeHint().width() ) / 2
      py = ( neuroConfig.qtApplication.desktop().height() - self.sizeHint().height() ) / 2
      self.setGeometry( px, py, self.sizeHint().width(), self.sizeHint().height() )
      self.btnClose = QPushButton( _t_( 'Close' ) )
      layout.addWidget(self.btnClose)
      self.btnClose.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
      self.btnClose.setFocus()
      QObject.connect( self.btnClose, SIGNAL( 'clicked()' ), self, SLOT( 'close()' ) )

def aboutRequest():
  global _aboutWidget
  if _aboutWidget is None:
    _aboutWidget = AboutWidget()
  _aboutWidget.show()
  _aboutWidget.raise_()

#----------------------------------------------------------------------------
def logRequest():
  neuroLogGUI.LogViewer( neuroConfig.logFileName ).show()


#----------------------------------------------------------------------------
def addBrainVISAMenu( widget, menuBar ):
  bvMenu = menuBar.addMenu( "&BrainVISA" )

  bvMenu.addAction( _t_( "&Help" ), helpRequest,  Qt.CTRL + Qt.Key_H )
  bvMenu.addAction( _t_( "&About" ), aboutRequest, Qt.CTRL + Qt.Key_A )
  bvMenu.addSeparator()
  bvMenu.addAction( _t_( "&Preferences" ), neuroConfig.editConfiguration, Qt.CTRL + Qt.Key_P )
  bvMenu.addAction( _t_( "Show &Log" ), logRequest, Qt.CTRL + Qt.Key_L )
  bvMenu.addAction( _t_( "&Open process..." ), ProcessView.open, Qt.CTRL + Qt.Key_O )
  bvMenu.addAction( _t_( "Start &Shell" ), startShell, Qt.CTRL + Qt.Key_S )
  bvMenu.addSeparator()
  if not isinstance( widget, ProcessSelectionWidget ):
    bvMenu.addAction( _t_( "Close" ), widget.close, Qt.CTRL + Qt.Key_W )
  bvMenu.addAction( _t_( "&Quit" ), quitRequest, Qt.CTRL + Qt.Key_Q )


#----------------------------------------------------------------------------
class HTMLBrowser( QWidget ):

  class BVTextBrowser( TextBrowserWithSearch ):
    def __init__( self, parent, name=None ):
      TextBrowserWithSearch.__init__( self, parent )
      if name:
        self.setObjectName(name)
      #self.mimeSourceFactory().setExtensionType("py", "text/plain")
      

    def setSource( self, url ):
      text=url.toString()
      bvp = unicode( text )
      if bvp.startswith( 'bvshowprocess://' ):
        bvp = bvp[16:]
        # remove tailing '/'
        if bvp[ -1 ] == '/':
          bvp = bvp[ : -1 ]
        proc = neuroProcesses.getProcess( bvp )
        if proc is None:
          print 'No process of name', bvp
        else:
          win = ProcessView( proc() )
          win.show()
      elif bvp.startswith( 'http://' ) or bvp.startswith( 'mailto:' ):
        try:
          openWeb(bvp)
        except:
          neuroException.showException()
      else:
        TextBrowserWithSearch.setSource( self, url )
        
    def customMenu(self):
      menu=TextBrowserWithSearch.customMenu(self)
      # accelerator key doesn't work, I don't know why...
      menu.addAction("Open in a web browser", self.openWeb, Qt.CTRL + Qt.Key_O )
      return menu
      
    def openWeb(self):
      openWeb(self.source().toString())
      

  def __init__( self, parent = None, name = None, fl = Qt.WindowFlags() ):
    QWidget.__init__( self, parent, fl )
    if name :
      self.setObjectName( name )

    vbox = QVBoxLayout( self )
    self.setLayout(vbox)
    vbox.setSpacing( 2 )
    vbox.setMargin( 3 )

    if getattr( HTMLBrowser, 'pixHome', None ) is None:
      setattr( HTMLBrowser, 'pixIcon', QIcon( os.path.join( neuroConfig.iconPath, 'icon_help.png' ) ) )
      setattr( HTMLBrowser, 'pixHome', QIcon( os.path.join( neuroConfig.iconPath, 'top.png' ) ) )
      setattr( HTMLBrowser, 'pixBackward', QIcon( os.path.join( neuroConfig.iconPath, 'back.png' ) ) )
      setattr( HTMLBrowser, 'pixForward', QIcon( os.path.join( neuroConfig.iconPath, 'forward.png' ) ) )

    self.setWindowIcon( HTMLBrowser.pixIcon )

    hbox = QHBoxLayout()
    hbox.setSpacing(6)
    hbox.setMargin(0)

    btnHome = QPushButton( )
    btnHome.setSizePolicy( QSizePolicy( QSizePolicy.Minimum, QSizePolicy.Minimum ) )
    btnHome.setIcon( self.pixHome )
    hbox.addWidget( btnHome )

    btnBackward = QPushButton( )
    btnBackward.setSizePolicy( QSizePolicy( QSizePolicy.Minimum, QSizePolicy.Minimum ) )
    btnBackward.setIcon( self.pixBackward )
    btnBackward.setEnabled( 0 )
    hbox.addWidget( btnBackward )

    btnForward = QPushButton( )
    btnForward.setSizePolicy( QSizePolicy( QSizePolicy.Minimum, QSizePolicy.Minimum ) )
    btnForward.setIcon( self.pixForward )
    btnForward.setEnabled( 0 )
    hbox.addWidget( btnForward )

    vbox.addLayout( hbox )

    browser = self.BVTextBrowser( self )
    browser.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding ) )
    vbox.addWidget( browser )

    self.connect( btnHome, SIGNAL('clicked()'), browser, SLOT( 'home()' ) )
    self.connect( btnBackward, SIGNAL('clicked()'), browser, SLOT( 'backward()' ) )
    self.connect( browser, SIGNAL('backwardAvailable(bool)'), btnBackward, SLOT('setEnabled(bool)') )
    self.connect( btnForward, SIGNAL('clicked()'), browser, SLOT( 'forward()' ) )
    self.connect( browser, SIGNAL('forwardAvailable(bool)'), btnForward, SLOT('setEnabled(bool)') )

    self.browser = browser
    
    neuroConfig.registerObject( self )

  def setSource( self, source ):
    self.browser.setSource( QUrl(source) )

  def setText( self, text ):
    self.browser.setText( text )
    
  def openWeb(self):
    openWeb(self.browser.source())
    
  def showCategoryDocumentation( self, category ):
    """
    Searches for a documentation file associated to this category and opens it  in this browser. 
    Documentation files are in docPath/processes/categories/category. Category is a relative path, so if no documentation is found with the entire path, it removes the first item and retries. 
    For example, if "t1 mri/viewers" doesn't exists, tries "viewers".
    If there is no documentation file, the browser page is empty. 
    """
    categoryPath=category.lower().split("/")
    found =False
    while ((len(categoryPath) > 0) and not found):
      html = neuroConfig.getDocFile(os.path.join(os.path.join( 'processes', 'categories', *categoryPath), 'category_documentation.html' ) )
      if os.path.exists( html ):
        self.setSource( html )
        found=True
      categoryPath=categoryPath[1:]
        
    if not found:
      self.setText( '' )

  def closeEvent( self, event ):
    neuroConfig.unregisterObject( self )
    QWidget.closeEvent( self, event )


#----------------------------------------------------------------------------
class NamedPushButton( QPushButton ):
  def __init__( self, parent, name ):
    QPushButton.__init__( self, parent, name )
    self.connect( self, SIGNAL( 'clicked()' ), self._pyClicked )

  def _pyClicked( self ):
    self.emit( SIGNAL( 'clicked' ), unicode( self.name()) )


#----------------------------------------------------------------------------
class WidgetScrollV( QScrollArea ):
  #class VBox( QWidget ):
    #def __init__( self, parent, ws ):
      #QWidget.__init__( self, parent )
      #layout=QVBoxLayout()
      #self.setLayout(layout)
      #layout.setSpacing( 5 )
      #self.ws = ws

    #def sizeHint( self ):
      #return QSize( self.ws.visibleWidth(), QWidget.sizeHint( self ).height() )

  def __init__( self, parent = None, name = None ):
    #self.box = None
    QScrollArea.__init__( self, parent)
    if name:
      self.setObjectName( name )
    self.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
    self.setFrameStyle( self.NoFrame )
    #self.box = self.VBox( None, self )
    #self.setWidget( self.box )
    self.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Maximum ) )
    self.setWidgetResizable(True)
    #self.box.resize( self.visibleWidth(), self.box.height() )

  #def show( self ):
    #self.setMaximumSize( self.maximumWidth(), self.box.size().height() )
    #return QScrollArea.show( self )

  #def resizeEvent( self, e ):
    #result = QScrollArea.resizeEvent( self, e )
    #if self.widget():
      #self.widget().resize( self.visibleWidth(), self.box.height() )
      ##self.updateGeometry()
      #self.setMaximumSize( self.maximumWidth(), self.box.sizeHint().height() )
      #if self.box.width() != self.visibleWidth():
        #self.box.resize( self.visibleWidth(), self.box.height() )
        #self.updateGeometry()
    #return result

  #def sizeHint( self ):
    #if self.box:
      #return QWidget.sizeHint( self.box )
    #else:
      #return QScrollArea.sizeHint( self )

  #def visibleWidth(self):
    #return self.viewport().width()

#----------------------------------------------------------------------------
class ExecutionContextGUI( neuroProcesses.ExecutionContext):
  def __init__( self ):
    neuroProcesses.ExecutionContext.__init__( self )

  def ask( self, message, *buttons, **kwargs ):
    modal=kwargs.get("modal", 1)
    dlg = apply( self.dialog, (modal, message, None) + buttons )
    return dlg.call()

  def dialog( self, parentOrFirstArgument, *args, **kwargs ):
    if isinstance( parentOrFirstArgument, QWidget ) or \
       parentOrFirstArgument is None:
      return self._dialog( parentOrFirstArgument, *args, **kwargs )
    else:
      return self._dialog( *((None,parentOrFirstArgument)+args), **kwargs )

  def _dialog( self, parent, modal, message, signature, *buttons ):
    return _mainThreadActions.call( UserDialog, parent, modal,
      message, signature, buttons )

  
  def mainThreadActions( self ):
    return mainThreadActions()


  @staticmethod
  def createContext():
    return ExecutionContextGUI()

#----------------------------------------------------------------------------
class ExecutionNodeGUI(QWidget):
  
  def __init__(self, parent, parameterized):
    QWidget.__init__(self, parent)
    layout = QVBoxLayout()
    layout.setMargin( 5 )
    layout.setSpacing( 4 )
    self.setLayout(layout)
    self.parameterizedWidget = ParameterizedWidget( parameterized, None ) 
    layout.addWidget(self.parameterizedWidget)
    spacer = QSpacerItem(0,0,QSizePolicy.Minimum,QSizePolicy.Expanding)
    layout.addItem( spacer )

#----------------------------------------------------------------------------
class VoidClass:
  pass


#----------------------------------------------------------------------------
class RadioItem(QWidget):
  """An custom item to replace a QTreeWidgetItem for the representation of a SelectionExecutionNode item with a radio button. 
  QTreeWidgetItem enables only check box items."""
  def __init__(self, text, group, parent=None):
    QWidget.__init__(self, parent)
    layout=QHBoxLayout()
    layout.setMargin(0)
    layout.setSpacing(0)
    self.setLayout(layout)
    self.radio=QRadioButton()
    self.radio.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
    layout.addWidget(self.radio)
    group.addButton(self.radio)
    self.icon=QLabel()
    layout.addWidget(self.icon)
    self.label=QLabel(text)
    layout.addWidget(self.label)
    layout.addStretch(1)
    #self.setAutoFillBackground(True)
    self.show()
  
  def setChecked(self, checked):
    self.radio.setChecked(checked)
    
  def isChecked(self):
    return self.radio.isChecked()
  
  def setIcon(self, icon):
    self.icon.setPixmap(icon.pixmap(*defaultIconSize))
  
#----------------------------------------------------------------------------
class NodeCheckListItem( QTreeWidgetItem ):
  
  def __init__( self, node, parent, after=None, text=None, itemType=None ):
    QTreeWidgetItem.__init__( self, parent )
    self._node = node
    self.itemType=itemType
    if itemType == "radio":
      # if the item type is radio, create a custom item RadioItem to replace the current QTreeWidgetItem at display
      # the radio button is included in a button group that is registred in the parent item
      buttonGroup=getattr(self.parent(), "buttonGroup", None)
      if not buttonGroup:
        buttonGroup=QButtonGroup()
        self.parent().buttonGroup=buttonGroup
      self.widget=RadioItem(text, buttonGroup)
      self.treeWidget().setItemWidget(self, 0, self.widget)
      QWidget.connect(self.widget.radio, SIGNAL("clicked(bool)"), self.itemClicked)
      QWidget.connect(self.widget.radio, SIGNAL("toggled(bool)"), self.itemToggled)
    else:# not a radio button, show text directly in the qtreeWidgetItem
      if text:
        self.setText(0, text)
    self.setOn( node._selected )
    node._selectionChange.add( self.nodeStateChanged )

  def itemClicked(self, checked):
    self.treeWidget().setCurrentItem(self)

  def itemToggled(self, checked):
    self.stateChange( checked )

  def setIcon(self, col, icon):
    if self.itemType=="radio":
      self.widget.setIcon(icon)
    else:
      QTreeWidgetItem.setIcon(self, col, icon)
    
  def stateChange( self, selected ):
    self._node.setSelected( selected )

  def nodeStateChanged( self, node ):
    self.setOn( node._selected )

  def cleanup( self ):
    self._node._selectionChange.remove( self.nodeStateChanged )
    self._node = None

  def setOn( self, b ):
    if self.itemType=="radio":
      self.widget.setChecked(b)
    elif self.itemType=="check":
      if b:
        self.setCheckState( 0, Qt.Checked )
      else:
        self.setCheckState( 0, Qt.Unchecked )
        
  def isOn( self ):
    if self.itemType=="radio":
      return self.widget.isChecked()
    elif self.itemType=="check":
      return self.checkState() == Qt.Checked
    return True

#------------------------------------------------------------------------------
class ParameterLabel( QLabel ):
  '''A QLabel that emits PYSIGNAL( 'contextMenuEvent' ) whenever a
  contextMenuEvent occurs'''
  def __init__( self, parameterName, mandatory, parent ):
    if mandatory:
      QLabel.__init__( self, '<b>' + parameterName + ':</b>',
                                              parent )
    else:
      QLabel.__init__( self, parameterName + ':', parent )

    #Save parameter name
    self.parameterName = parameterName

    # Create popup menu
    self.contextMenu = QMenu()
    #self.contextMenu.setCheckable( True )
    self.default_id = self.contextMenu.addAction( _t_( 'default value' ),
                                                   self.defaultChanged )
    self.default_id.setCheckable(True)
    self.default_id.setChecked( True )

  def contextMenuEvent( self, e ):
    self.contextMenu.exec_( e.globalPos() )
    e.accept()

  def defaultChanged( self, checked ):
    self.default_id.toggle()
    self.emit( SIGNAL( 'toggleDefault' ), self.parameterName )

  def setDefault( self, default ):
    self.default_id.setChecked( default )


#------------------------------------------------------------------------------
class ParameterizedWidget( QWidget ):
  def __init__( self, parameterized, parent ):
    debugHere()
#lock#    if getattr( ParameterizedWidget, 'pixDefault', None ) is None:
#lock#      setattr( ParameterizedWidget, 'pixDefault', QPixmap( os.path.join( neuroConfig.iconPath, 'lock.png' ) ) )
#lock#      setattr( ParameterizedWidget, 'pixCustom', QPixmap( os.path.join( neuroConfig.iconPath, 'unlock.png' ) ) )

    QWidget.__init__( self, parent )
    self.connect( self, SIGNAL( 'destroyed()' ), self.cleanup )

    layout = QVBoxLayout( )
    layout.setMargin(0)
    layout.setSpacing(4)
    self.setLayout(layout)
    # the scroll widget will contain parameters widgets
    self.scrollWidget = WidgetScrollV( )
    layout.addWidget( self.scrollWidget )
    spacer = QSpacerItem( 0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding )
    layout.addItem( spacer )

    # Using weakref here because self.parameterized may contain a reference
    # to self.parameterChanged (see below) which is a bound method that contains
    # a reference to self. If nothing is done self is never destroyed.
    
    self.parameterized = weakref.proxy( parameterized )
    self.parameterized.deleteCallbacks.append( self.parameterizedDeleted )
    self.labels={}
    self.editors={}
#lock#    self.btnLock={}
    self._currentDirectory = None

    self._doUpdateParameterValue = False
    first = None
    maxwidth = 0
    for ( k, p ) in self.parameterized.signature.items():
      if neuroConfig.userLevel >= p.userLevel:
        txtwidth = self.fontMetrics().boundingRect(k).width()
        if p.mandatory:
          txtwidth = txtwidth * 1.2 # (bold text)
        if txtwidth > maxwidth:
          maxwidth = txtwidth
    # the widget that will contain parameters, it will be put in the scroll widget
    parametersWidget=QWidget()
    parametersWidgetLayout=QVBoxLayout()
    parametersWidgetLayout.setMargin(0)
    parametersWidget.setLayout(parametersWidgetLayout)
    # create a widget for each parameter
    for k, p in self.parameterized.signature.items():
      if neuroConfig.userLevel >= p.userLevel:
        hb = QHBoxLayout( )
        parametersWidgetLayout.addLayout(hb)
        hb.setSpacing( 4 )
        # in a QHBoxLayout : a label and an editor for each parameter
        l = ParameterLabel( k, p.mandatory, None )
        hb.addWidget(l)
        l.setDefault(self.parameterized.isDefault( k ))
        self.connect( l, SIGNAL( 'toggleDefault' ), self._toggleDefault )
        l.setFixedWidth( maxwidth )
        self.labels[ k ] = l
        e = p.editor( None, k, weakref.proxy( self ) )
        hb.addWidget(e)

        self.parameterized.addParameterObserver( k, self.parameterChanged )

        self.editors[ k ] = e
        if first is None: first = e
        v = getattr( self.parameterized, k, None )
        if v is not None: 
          e.setValue( v, 1 )
        e.connect( e, SIGNAL('noDefault'), self.removeDefault )
        e.connect( e, SIGNAL('newValidValue'), self.updateParameterValue )
#lock#        btn = NamedPushButton( hb, k )
#lock#        btn.setPixmap( self.pixCustom )
#lock#        btn.setFocusPolicy( QWidget.NoFocus )
#lock#        btn.setToggleButton( 1 )
#lock#        btn.hide()
#lock#        self.connect( btn, PYSIGNAL( 'clicked' ), self._toggleDefault )
#lock#        self.btnLock[ k ] = btn
    self.scrollWidget.setWidget(parametersWidget)
    if first: first.setFocus()
    self._doUpdateParameterValue = True
    #self.scrollWidget.widget().resize(600, 200) 
    self.scrollWidget.show()
    
  def parameterizedDeleted( self, parameterized ):
    debugHere()
    for k, p in parameterized.signature.items():
      try:
        parameterized.removeParameterObserver( k, self.parameterChanged )
      except ValueError:
        pass
    self.parameterized = None
    for x in self.editors.keys():
      self.editors[x].releaseCallbacks()

  def __del__( self ):
    debugHere()
    if self.parameterized is not None:
      self.parameterizedDeleted( self.parameterized )
    #QWidget.__del__( self )

  def cleanup( self ):
    debugHere()
    for x in self.editors.keys():
      self.editors[x].releaseCallbacks()

  def closeEvent( self, event ):
    for k, p in self.parameterized.signature.items():
      try:
        self.parameterized.removeParameterObserver( k, self.parameterChanged )
      except ValueError:
        pass
    self.cleanup()
    QWidget.closeEvent( self, event )

  def setParameterToolTip( self, parameterName, text ):
    self.labels[ parameterName ].setToolTip(self.parameterized.signature[ parameterName ].toolTipText( parameterName, text ))

  def parameterChanged( self, parameterized, parameterName, value ):
    """This method is called when an attribute has changed in the model. 
    A parameter can change in the model because it is links to another parameter that has changed or because the user changed it in the GUI."""
    # It is necessary to read user values before applying changes,
    # otherwise selected data are reset
    self.readUserValues()
    self._doUpdateParameterValue = False
    default=parameterized.isDefault( parameterName )
    self.editors[ parameterName ].setValue( value,
                                            default = default)
    self.labels[ parameterName ].setDefault( default )
    self._doUpdateParameterValue = True

  def updateParameterValue( self, name, value ):
    if self._doUpdateParameterValue:
      setattr( self.parameterized, name, value )

  def removeDefault( self, name ):
    self.parameterized.setDefault( name, False )
    self.labels[ name ].setDefault( False )
#lock#    self.btnLock[ name ].setPixmap( self.pixDefault )
#lock#    self.btnLock[ name ].setOn( 1 )
#lock#    self.btnLock[ name ].show()

  def _toggleDefault( self, name ):
    if self.parameterized.isDefault( name ):
      self.parameterized.setDefault( name, False )
#lock#      self.btnLock[ name ].setPixmap( self.pixDefault )
#lock#      self.btnLock[ name ].setOn( 1 )
#lock#      self.btnLock[ name ].show()
    else:
      self.parameterized.setDefault( name, True )
#lock#      self.btnLock[ name ].setPixmap( self.pixCustom )
#lock#      self.btnLock[ name ].setOn( 0 )
#lock#      self.btnLock[ name ].hide()

  def checkReadable( self ):
    for ( n, p ) in self.parameterized.signature.items():
      if p.checkReadable( getattr( self.parameterized, n, None ) ):
        e = self.editors.get( n )
        if e is not None: e.checkReadable()

  def readUserValues( self ):
    'Ensure that values typed by the user are taken into account'
    for n in self.parameterized.signature.keys():
      e = self.editors.get( n )
      if e is not None:
        e.checkValue()

  def setValue( self, parameterName, value, default=0 ):
    'Set the value of a parameter'
    self.editors[ parameterName ].setValue( value, default = default )


#----------------------------------------------------------------------------
class BrainVISAAnimation( QLabel ):
  def __init__( self, parent=None ):
    QLabel.__init__( self, parent )
    self.mmovie = QMovie( os.path.join( neuroConfig.iconPath, 'rotatingBrainVISA.gif' ) ) #, 1024*10 )
    self.setMovie( self.mmovie )
    #self.mmovie.setSpeed( 500 )
    #qApp.processEvents()
    self.mmovie.stop()

  def start( self ):
    self.mmovie.start()

  def stop( self ):
    self.mmovie.start()
    qApp.processEvents()
    self.mmovie.stop()

#----------------------------------------------------------------------------
class ProcessView( QWidget, ExecutionContextGUI ):
  def __init__( self, processId, parent = None, externalInfo = None ):
    ExecutionContextGUI.__init__( self )
    QWidget.__init__( self, parent )
    if getattr( ProcessView, 'pixIcon', None ) is None:
      setattr( ProcessView, 'pixIcon', QIcon( os.path.join( neuroConfig.iconPath, 'icon_process.png' ) ) )
      setattr( ProcessView, 'pixDefault', QIcon( os.path.join( neuroConfig.iconPath, 'lock.png' ) ) )
      setattr( ProcessView, 'pixInProcess', QIcon( os.path.join( neuroConfig.iconPath, 'forward.png' ) ) )
      setattr( ProcessView, 'pixProcessFinished', QIcon( os.path.join( neuroConfig.iconPath, 'ok.png' ) ) )
      setattr( ProcessView, 'pixProcessError', QIcon( os.path.join( neuroConfig.iconPath, 'abort.png' ) ) )
      setattr( ProcessView, 'pixNone', QIcon() )
    
    # ProcessView cannot be a QMainWindow because it have to be included in a QStackedWidget in pipelines. 
    #centralWidget=QWidget()
    #self.setCentralWidget(centralWidget)
    
    centralWidgetLayout=QVBoxLayout()
    self.setLayout(centralWidgetLayout)
    centralWidgetLayout.setMargin( 5 )
    centralWidgetLayout.setSpacing( 4 )

    self.setWindowIcon( self.pixIcon )

    if parent is None:
      neuroConfig.registerObject( self )
      # menu bar
      menu = QMenuBar()
      addBrainVISAMenu( self, menu )
      processMenu=menu.addMenu("&Process")
      processMenu.addAction( _t_( '&Save...' ), self.saveAs,  Qt.CTRL + Qt.Key_S )
      processMenu.addAction( _t_( '&Clone...' ), self.clone,  Qt.CTRL + Qt.Key_C )
      centralWidgetLayout.addWidget(menu)

    self.connect( self, SIGNAL( 'destroyed()' ), self.cleanup )

    process = neuroProcesses.getProcessInstance( processId )
    if process is None:
      raise RuntimeError( HTMLMessage(_t_( 'Cannot open process <em>%s</em>' ) % ( str(processId), )) )
    self.process = process
    self.process.guiContext = weakref.proxy( self )
    self._runningProcess = 0
    self.process.signatureChangeNotifier.add( self.signatureChanged )
    self.btnRun = None
    self.btnInterruptStep=None
    self._running = False

    procdoc = neuroProcesses.readProcdoc( process )
    documentation = procdoc.get( neuroConfig.language )
    if documentation is None:
      documentation = procdoc.get( 'en', {} )

    t = _t_(process.name) + ' ' + unicode( process.instance )
    self.setWindowTitle( t )
    
    # title of the process : label + rotating icon when it's running
    titleLayout = QHBoxLayout( )
    centralWidgetLayout.addLayout(titleLayout)
    self.labName = QLabel( t, self )
    titleLayout.addWidget(self.labName)
    self.labName.setFrameStyle( QFrame.Panel | QFrame.Raised )
    self.labName.setLineWidth( 1 )
    self.labName.setMargin( 5 )
    self.labName.setAlignment( Qt.AlignCenter )
    self.labName.setWordWrap(True)
    font = self.labName.font()
    font.setPointSize( QFontInfo( font ).pointSize() + 4 )
    self.labName.setFont( font )
    self.labName.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Preferred ) )
    doc =  XHTML.html( documentation.get( 'short', '' ) )
    if doc:
      self.labName.setToolTip('<center><b>' + _t_(process.name) + '</b></center><hr><b>' + _t_('Description') + ':</b><br/>' + doc)

    if externalInfo is None:
      
      self.movie = BrainVISAAnimation( )
      titleLayout.addWidget(self.movie)
      titleLayout.setSpacing(3)
      
      # vertical splitter : parameters, log text widget 
      splitter = QSplitter( Qt.Vertical )
      centralWidgetLayout.addWidget(splitter)
      
      # at the top of the splitter : the parameters
      self.parametersWidget = QWidget(splitter)
      parametersWidgetLayout = QVBoxLayout( )
      parametersWidgetLayout.setMargin(0)
      self.parametersWidget.setLayout(parametersWidgetLayout)
      
      # at the bottom of the splitter : the text widget to log information about process execution
      self.info = QTextEdit( splitter )
      self.info.setReadOnly( True )
      self.info.setAcceptRichText( True )
      sizePolicy=QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Preferred)
      sizePolicy.setHorizontalStretch(0)
      sizePolicy.setVerticalStretch(50)
      self.info.setSizePolicy( sizePolicy )
      self.infoCounter = None
      #splitter.setResizeMode( self.info, splitter.Stretch )
      # splitter.setResizeMode( self.parametersWidget, QSplitter.FollowSizeHint )
      #splitter.setResizeMode( self.parametersWidget, QSplitter.Auto )
      container = self.parametersWidget
      self.isMainWindow = True
    else:
      self.movie = None
      splitter = None
      self.parametersWidget = self
      container = self
      self.isMainWindow = False
      self.info = externalInfo

    self.splitter = splitter
    self._widgetStack = None
    eNode = getattr( process, '_executionNode', None )
    self._executionNodeLVItems = {}
    # process composed of several processes
    if eNode is not None and self.isMainWindow:
      self.parameterizedWidget = None
      #vb = QVBoxLayout( )
      #container.layout().addLayout(vb)
      vb=container.layout()
      
      # splitter that shows the composition of the process on the left and the parameters of each step on the right
      eTreeWidget = QSplitter( Qt.Horizontal )
      vb.addWidget(eTreeWidget)
      
      # Run and iterate buttons
      self.inlineGUI = self.process.inlineGUI( self.process, self, None,
                                               externalRunButton = True )
      if self.inlineGUI is None and externalInfo is None:
        self.inlineGUI = self.defaultInlineGUI( None )
      vb.addWidget(self.inlineGUI)
      
      # composition of the pipeline
      self.executionTree = QTreeWidget( eTreeWidget )
      self.executionTree.setSizePolicy( QSizePolicy( QSizePolicy.Preferred, QSizePolicy.Preferred ) )
      self.executionTree.setColumnCount(1)
      self.executionTree.setHeaderLabels( ['Name'] )
      self.executionTree.setAllColumnsShowFocus( 1 )
      self.executionTree.setRootIsDecorated( 1 )
      #self.executionTree.setSortingEnabled( -1 )
      #eTreeWidget.setResizeMode( self.executionTree, QSplitter.KeepSize )

      # parameters of a each step of the pipeline
      self._widgetStack = QStackedWidget( eTreeWidget )
      self._widgetStack.setSizePolicy( QSizePolicy( QSizePolicy.Preferred,
      QSizePolicy.Preferred ) )
      self._widgetStack._children = []
      #blank = QWidget( )
      #self._widgetStack.addWidget( blank )

      self._guiId = 0
      self._executionNodeExpanded( self.executionTree, ( eNode, (eNode,) ) )
      self.connect( self.executionTree,
                    SIGNAL( 'itemExpanded( QTreeWidgetItem * )' ),
                    self._executionNodeExpanded )
      
      self.connect( self.executionTree,
                    SIGNAL( 'currentItemChanged( QTreeWidgetItem *, QTreeWidgetItem * )' ),
                    self.executionNodeSelected )
      self.connect( self.executionTree,
                    SIGNAL( 'itemClicked( QTreeWidgetItem *, int )' ),
                    self.executionNodeClicked )
      
      # Select and open the first item
      item = self.executionTree.topLevelItem(0)
      item.setExpanded( True )
      self.executionTree.setCurrentItem( item )

      ##--##
      if neuroProcesses.neuroDistributedProcesses():
        self.remote = neuroProcesses.RemoteContext()

        self.remoteWidget = RemoteContextGUI(splitter)
        #splitter.setResizeMode( self.remoteWidget.listView(), QSplitter.KeepSize )
        self.connect(self.remote, SIGNAL("SIG_addIP"), self.remoteWidget.addIP)
        self.connect(self.remote, SIGNAL("SIG_addProcess"), self.remoteWidget.addProcess)
        self.connect(self.remote, SIGNAL("SIG_addMessage"), self.remoteWidget.addMessage)
        self.connect(self.remote, SIGNAL("SIG_setProcessStatus"), self.remoteWidget.setProcessStatus)
        self.connect(self.remote, SIGNAL("SIG_setCurrentMessage"), self.remoteWidget.setCurrentMessage)
        self.connect(self.remote, SIGNAL("SIG_clear"), self.remoteWidget.clear)
      ##--##
    
    # simple process : only a signature, no sub-processes
    else:
      self.executionTree = None
      self.createSignatureWidgets( documentation )

    self._iterationDialog = None

    self._logDialog = None
    # It is necessary to call show() before resize() to have a correct layout.
    # Otherwize,  vertical sliders may be superimposed to widgets. But some
    # window managers compute the window location according to its size during
    # show(). If the window become larger after show() call, part of it will be
    # off screen. Therefore set the widget size before show() ensure that
    # window location is correct and changing size after show() ensure that
    # layout is correct.
    if parent is None:
      self.show()
      self.resize( 600, 801 )
      #qApp.processEvents()

    initGUI = getattr( self.process, 'initializationGUI', None )
    if initGUI is not None:
      initGUI( self )
  

  def createSignatureWidgets( self, documentation=None ):
    eNode = getattr( self.process, '_executionNode', None )
    if eNode and self.isMainWindow:
      parent = self._widgetStack
    else:
      parent = self.parametersWidget.layout()
    # if the process has a signature, creates a widget for the parameters : ParameterizedWidget
    if self.process.signature:
      self.parameterizedWidget = ParameterizedWidget( self.process, None )
      self.parameterizedWidget.show()
      parent.addWidget(self.parameterizedWidget)
    else:
      self.parameterizedWidget = None 
    if eNode is None or not self.isMainWindow:
      self.inlineGUI = self.process.inlineGUI( self.process, self, None )
      if self.inlineGUI is None and self.isMainWindow:
        self.inlineGUI = self.defaultInlineGUI( None )
      if self.inlineGUI is not None:
        parent.addWidget(self.inlineGUI)
    else:
      self._widgetStack.removeWidget( self._widgetStack._children[ 0 ] )
      self._widgetStack._children[ 0 ].close()
      self._widgetStack._children[ 0 ].deleteLater()
      if self.parameterizedWidget is not None:
        self._widgetStack.addWidget( self.parameterizedWidget, 0 )
      self._widgetStack._children[ 0 ] = self.parameterizedWidget
      self._widgetStack.setCurrentIndex( 0 )
    if self.parameterizedWidget is not None:
      if documentation is not None:
        for ( k, p ) in self.process.signature.items():
          if neuroConfig.userLevel >= p.userLevel:
            self.parameterizedWidget.setParameterToolTip( k, 
              XHTML.html( documentation.get( 'parameters', {} ).get( k, '' ) ) )
      self.parameterizedWidget.show()
    if self.inlineGUI is not None:
      self.inlineGUI.show()

  def eraseSignatureWidgets( self ):
    if self.parameterizedWidget is not None:
      self.parameterizedWidget.close()
      self.parameterizedWidget.deleteLater()
    eNode = getattr( self.process, '_executionNode', None )
    if eNode is None and self.inlineGUI is not None:
      self.inlineGUI.close()
      self.inlineGUI.deleteLater()

  def signatureChanged( self, process ):
    self.eraseSignatureWidgets()
    self.createSignatureWidgets( None )

  def defaultInlineGUI( self, parent, externalRunButton = False, container = None ):
    if container is None:
      container = QWidget( )
      layout=QHBoxLayout()
      container.setLayout(layout)
      layout.setMargin( 5 )
    else:
      layout=container.layout()

    if not externalRunButton:
      self.btnRun = QPushButton( _t_( 'Run' ) )
      layout.addWidget(self.btnRun)
      self.btnRun.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
      QObject.connect( self.btnRun, SIGNAL( 'clicked()' ), self._runButton )
      
      if (self.process.__class__ == neuroProcesses.IterationProcess):
        self.btnInterruptStep = QPushButton( _t_('Interrupt current step') )
        layout.addWidget(self.btnInterruptStep)
        self.btnInterruptStep.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
        self.btnInterruptStep.setVisible(False)
        QObject.connect( self.btnInterruptStep, SIGNAL( 'clicked()' ), self._interruptStepButton )
      
    self.btnIterate = QPushButton( _t_('Iterate') )
    layout.addWidget(self.btnIterate)
    self.btnIterate.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    QObject.connect( self.btnIterate, SIGNAL( 'clicked()' ), self._iterateButton )

    if neuroProcesses.neuroDistributedProcesses():
      self.btnDistribute = QPushButton( _t_( 'Distribute' ) )
      layout.addWidget(self.btnDistribute)
      self.btnDistribute.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
      QObject.connect( self.btnDistribute, SIGNAL( 'clicked()' ), self._distributeButton )

    container.setSizePolicy( QSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Fixed ) )
    container.setMaximumHeight( container.sizeHint().height() )
    return container


  def getEditor( self, parameterName ):
    if self.parameterizedWidget is not None:
      return self.parameterizedWidget.editors.get( parameterName )
    return None

  def closeEvent( self, event ):
    debugHere()
    self.cleanup()
    QWidget.closeEvent( self, event )
  
  
  def __del__( self ):
    debugHere()
  
  def cleanup( self ):
    debugHere( 1, self.process.name )
    self.process.cleanup()
    if self.parameterizedWidget is not None:
      debugHere()
      self.parameterizedWidget.cleanup()
    if self._widgetStack is not None:
      for gui in  self._widgetStack._children:
        cleanup = getattr( gui, 'cleanup', None )
        if cleanup is not None:
          cleanup()
        if gui is not None:
          gui.deleteLater()
      self._widgetStack = None
    if self.executionTree is not None:
      it = QTreeWidgetItemIterator(self.executionTree)
      while it.value():
        cleanup = getattr( it.value(), 'cleanup', None )
        if cleanup is not None:
          cleanup()
        it+=1
      self.executionTree = None
    neuroConfig.unregisterObject( self )
    self.process.signatureChangeNotifier.remove( self.signatureChanged )
    self._executionNodeLVItems.clear()
    self.parametersWidget = None
    self.info = None
    self.process._lastResult = None

  def _runButton( self, executionFunction=None ):
    try:
      try:
        # disable run button when clicked to avoid several successive clicks
        # it is enabled when the process starts, the label of the button switch to interrupt
        if self.btnRun:
          self.btnRun.setEnabled(False)
        if self._running:
          self._setInterruptionRequest( neuroProcesses.ExecutionContext.UserInterruption() )
        else:
          processView = self._checkReloadProcess()
          if processView is None:
            processView = self
            processView.info.setText( '' )
          else:
            processView.info.setText( '' )
            processView.warning( _t_('processes %s updated') % _t_(processView.process.name) )
          processView._runningProcess = 0
          processView._startCurrentProcess( executionFunction )
      except:
        neuroException.showException()
    finally:
      if self.btnRun:
        self.btnRun.setEnabled(True)
  
  def _interruptStepButton( self, executionFunction=None ):
    if self._running:
          self._setInterruptionRequest( neuroProcesses.ExecutionContext.UserInterruptionStep() )

  def _checkReloadProcess( self ):
    self.readUserValues()
    reload = False
    for p in self.process.allProcesses():
      pp = neuroProcesses.getProcess( p )
      if pp is not p and pp is not p.__class__:
        reload = True
        break
    result = None
    if reload:
      eNode = getattr( self.process, '_executionNode', None )
      if eNode is None:
        # Get current process arguments values
        event = ProcessExecutionEvent()
        event.setProcess( self.process )
        # Forget about old process
        self.process.signatureChangeNotifier.remove( self.signatureChanged )
        self.eraseSignatureWidgets()
        # Care about new process
        self.process = neuroProcesses.getProcessInstanceFromProcessEvent( event )
        self.process.signatureChangeNotifier.add( self.signatureChanged )
        procdoc = neuroProcesses.readProcdoc( self.process )
        documentation = procdoc.get( neuroConfig.language )
        if documentation is None:
          documentation = procdoc.get( 'en', {} )
        self.createSignatureWidgets( documentation )
        result = self
      else:
        result = self.clone()
        self.deleteLater()
    return result
  
  
  
  def _startCurrentProcess( self, executionFunction ):
    #Remove icon from all ListView items
    for item in self._executionNodeLVItems.values():
      item.setIcon( 0, self.pixNone )
    self._lastProcessRaisedException = False
    try:
      self._startProcess( self.process, executionFunction )
      self._running = True
    except:
      self._lastProcessRaisedException = True
      neuroException.showException()

  def _write( self, html ):
    _mainThreadActions.push( self._appendInfo, html )

  def _appendInfo( self, msg ):
    self.info.append( msg  )

  def _processStarted( self ):
    if self._depth() == 1:
      if self.movie is not None:
        _mainThreadActions.push( self.movie.start )
      if self.btnRun:
        if self.btnInterruptStep:
          _mainThreadActions.push(self.btnInterruptStep.setVisible, True)
        _mainThreadActions.push( self.btnRun.setEnabled, True )
        _mainThreadActions.push( self.btnRun.setText, _t_( 'Interrupt' ) )

    #Adds an icon on the ListViewItem corresponding to the current process
    # if any
    p = self._currentProcess()
    eNodeItem = self._executionNodeLVItems.get( p )
    if eNodeItem is not None:
      _mainThreadActions.push( eNodeItem.setIcon, 0, self.pixInProcess )

    ExecutionContextGUI._processStarted( self )

  def _processFinished( self, result ):
    self.process._lastResult = result
    ExecutionContextGUI._processFinished( self, result )

    #Remove icon from the ListViewItem corresponding to the current process
    # if any
    p = self._currentProcess()
    eNodeItem = self._executionNodeLVItems.get( p )
    if eNodeItem is not None:
      if self._lastProcessRaisedException:
        _mainThreadActions.push( eNodeItem.setIcon, 0, self.pixProcessError )
      else:
        _mainThreadActions.push( eNodeItem.setIcon, 0,
                                 self.pixProcessFinished )

    if self._depth() == 1:
      if self.movie is not None:
        _mainThreadActions.push( self.movie.stop )
      if self.btnRun:
        _mainThreadActions.push( self.btnRun.setEnabled, True )
        _mainThreadActions.push( self.btnRun.setText, _t_( 'Run' ) )
        if self.btnInterruptStep:
          _mainThreadActions.push(self.btnInterruptStep.setVisible, False)
      _mainThreadActions.push( self._checkReadable )
      self._running = False
    else:
      _mainThreadActions.push( self._checkReadable )
  
  
  def system( self, *args, **kwargs ):
    ret = apply( ExecutionContextGUI.system, (self,) + args, kwargs )
    _mainThreadActions.push( self._checkReadable )
    return ret

  def _checkReadable( self ):
    if self.parameterizedWidget is not None:
      self.parameterizedWidget.checkReadable()
    if self.executionTree is not None:
      for gui in self._widgetStack._children:
        checkReadable = getattr( gui, '_checkReadable', None )
        if checkReadable is not None:
          checkReadable()

  def dialog( self, modal, message, signature, *buttons ):
    return _mainThreadActions.call( UserDialog, self, modal,
      message, signature, buttons )

  #def showCallScript( self ):
    #text = "defaultContext().runProcess( '" + self.process.id() + "'"
    #text2 = ''
    #for n in self.process.signature.keys():
      #if not self.process.isDefault( n ):
        #text2 += '  ' + n + ' = ' + repr( self.editors[ n ].getValue() ) + ',\n'
    #if text2:
      #text += ',\n' + text2
    #text += ')\n'

    #txt = TextEditor( text )
    #txt.resize( 800, 600 )
    #txt.show()

  def executionNodeSelected( self, item, previous ):
    if item is not None:
      self._widgetStack.setCurrentIndex( item._guiId )
      # Trick to have correct slider
      size = self.size()
      #self.resize( size.width()+1, size.height() )
      #qApp.processEvents()
      #self.resize( size )

  def executionNodeClicked( self, item, column ):
    item.stateChange( item.checkState( 0 ) )
    

  def _executionNodeExpanded( self, item, eNodeAndChildren=None ):
    if item is not None and getattr( item, '_notExpandedYet', True ):
      item._notExpandedYet = False
      previous = None
      if eNodeAndChildren is None:
        eNode = item._executionNode
        eNodeChildren = (eNode.child( k ) for k in  eNode.childrenNames())
      else:
        eNode, eNodeChildren = eNodeAndChildren
      for childNode in eNodeChildren:
        if isinstance( childNode, neuroProcesses.ProcessExecutionNode ):
          en = childNode._executionNode
          if en is None:
            en = childNode
        else:
          en = childNode
        if eNode is not childNode \
          and ( isinstance( eNode, neuroProcesses.SelectionExecutionNode ) \
            or ( isinstance( eNode, neuroProcesses.ProcessExecutionNode ) \
            and isinstance( eNode._executionNode, neuroProcesses.SelectionExecutionNode ) ) ):
          itemType="radio"
        elif childNode._optional:
          itemType="check"
        else:
          itemType=None
        newItem=NodeCheckListItem( childNode, item, previous, _t_( childNode.name() ), itemType )
        newItem._executionNode = childNode
        previous = newItem
        if en.hasChildren():
          newItem.setChildIndicatorPolicy(newItem.ShowIndicator)
        #newItem.setExpandable( en.hasChildren() )
        if isinstance( childNode, neuroProcesses.ProcessExecutionNode ):
          self._executionNodeLVItems[ childNode._process ] = newItem
        gui = childNode.gui( self._widgetStack, processView=self )
        if gui is not None:
          newItem._guiId=self._widgetStack.addWidget( gui )
          self._widgetStack._children.append( gui )
          self._guiId += 1
        else:
          self._emptyWidget = QWidget( self._widgetStack )
          newItem._guiId=self._widgetStack.addWidget( self._emptyWidget )
      if self._depth():
        p = self._currentProcess()
        eNodeItem = self._executionNodeLVItems.get( p )
        if eNodeItem is not None:
          eNodeItem.setIcon( 0, self.pixInProcess )
  
  def _executionNodeActivated(self, item):
    if getattr(item, "activate", None):
      item.activate()
    
  def _distributeButton( self ):
    self.readUserValues()
    self._iterationDialog = IterationDialog( self, self.process, self )
    self.connect( self._iterationDialog, SIGNAL( 'accept' ), 
                  self._distributeAccept )
    self._iterationDialog.show()
  
  def _distributeAccept( self ):
    try:
      params = self._iterationDialog.getLists()
      processes = apply( self.process._iterate, (), params )
      showProcess( DistributedProcess( self.process.name, processes ) )
    except:
      neuroException.showException()
      self._iterationDialog.show()

  def _iterateButton( self ):
    self.readUserValues()
    self._iterationDialog = IterationDialog( self, self.process, self )
    self.connect( self._iterationDialog, SIGNAL( 'accept' ),
                  self._iterateAccept )
    self._iterationDialog.show()

  def _iterateAccept( self ):
    try:
      params = self._iterationDialog.getLists()
      processes = self.process._iterate( **params )
      iterationProcess = neuroProcesses.IterationProcess( self.process.name, processes )
      showProcess( iterationProcess )
    except:
        neuroException.showException()
        self._iterationDialog.show()

  def setValue( self, name, value ):
    setattr( self.process, name, value )

  def readUserValues( self ):
    if self.parameterizedWidget is not None:
      self.parameterizedWidget.readUserValues()
    if self._widgetStack is not None:
      for pw in self._widgetStack._children:
        ruv = getattr( pw, 'readUserValues', None )
        if ruv is None:
          ruv = getattr( getattr( pw, 'parameterizedWidget', None ),  'readUserValues', None )
        if ruv is not None:
          ruv()


  def createProcessExecutionEvent( self ):
    event = super( ProcessView, self ).createProcessExecutionEvent()
    mainThreadActions().call( event.setWindow, self )
    return event
  
  
  def saveAs( self ):
    minf = getattr( self.process, '_savedAs', '' )
    minf = unicode( QFileDialog.getSaveFileName( None, 'Open a process file', minf, 'BrainVISA process (*.bvproc);;All files (*)' ) )
    if minf:
      if not minf.endswith( '.bvproc' ):
        minf += '.bvproc'
      self.readUserValues()
      event = self.createProcessExecutionEvent()
      self.process._savedAs = minf
      event.save( minf )

  
  def clone( self ):
    self.readUserValues()
    clone = neuroProcesses.getProcessInstanceFromProcessEvent( self.createProcessExecutionEvent() )
    return showProcess( clone )
  

  @staticmethod
  def open():
    minf = unicode( QFileDialog.getOpenFileName( None, 'Open a process file', '', 'BrainVISA process (*.bvproc);;All files (*)' ))
    if minf:
      showProcess( neuroProcesses.getProcessInstance( minf ) )

#----------------------------------------------------------------------------
def showProcess( process, *args, **kwargs ):
  '''Opens a process window and set the corresponding arguments'''
  global _mainWindow
  if isinstance( process, type ) and issubclass( process, newProcess.NewProcess ):
    process = process()
  if isinstance( process, newProcess.NewProcess ):
    # Opening a new style process
    process.show( *args, **kwargs )
  else:
    process = neuroProcesses.getProcessInstance( process )
    if process is None:
      raise RuntimeError( HTMLMessage(_t_( 'Invalid process <em>%s</em>' ) % ( str(process), )) )
    for i in xrange( len( args ) ):
      k, p = process.signature.items()[ i ]
      process.setValue( k, args[ i ] )
    for k, v in kwargs.items():
      process.setValue( k, v )
    gui = getattr( process, 'overrideGUI', None )
    if gui is None:
      view = ProcessView( process )
    else:
      view = gui()
    windowGeometry = getattr( process, '_windowGeometry', None )
    if windowGeometry is not None:
      view.move( *windowGeometry[ 'position' ] )
      view.resize( *windowGeometry[ 'size' ] )
    view.show()
    return view


#----------------------------------------------------------------------------
class IterationDialog( QDialog ):
  def __init__( self, parent, parameterized, context ):
    QDialog.__init__( self, parent )
    self.setModal(True)
    layout = QVBoxLayout( )
    self.setLayout(layout)
    layout.setMargin( 10 )
    self.setWindowTitle( _t_('%s iteration') % unicode( parent.windowTitle() ) )

    params = []
    for ( n, p ) in parameterized.signature.items():
      if neuroConfig.userLevel >= p.userLevel:
        params += [ n, neuroData.ListOf( p ) ]
    self.parameterized = neuroProcesses.Parameterized( neuroData.Signature( *params ) )
    for n in self.parameterized.signature.keys():
      setattr( self.parameterized, n, None )

    self.parameterizedWidget = ParameterizedWidget( self.parameterized, None )
    layout.addWidget(self.parameterizedWidget)
  
    w=QWidget()
    hb = QHBoxLayout( )
    w.setLayout(hb)
    layout.addWidget(w)
    hb.setMargin( 5 )
    w.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Fixed ) )
    btn = QPushButton( _t_('Ok') )
    hb.addWidget(btn)
    btn.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    self.connect( btn, SIGNAL( 'clicked()' ), self, SLOT( 'accept()' ) )
    btn = QPushButton( _t_('Cancel') )
    hb.addWidget(btn)
    btn.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    self.connect( btn, SIGNAL( 'clicked()' ), self, SLOT( 'reject()' ) )

  def getLists( self ):
    result = {}
    for n in self.parameterized.signature.keys():
        result[ n ] = getattr( self.parameterized, n, None )
    return result

  def accept( self ):
    QDialog.accept( self )
    self.parameterizedWidget.readUserValues()
    self.emit( SIGNAL( 'accept' ) )

#----------------------------------------------------------------------------

class UserDialog( QDialog ): # Ex QSemiModal
  def __init__( self, parent, modal, message, signature, buttons ):
    flags =  Qt.Window | Qt.Dialog | Qt.WA_DeleteOnClose
    QDialog.__init__( self, parent, flags )
    self.setWindowModality(Qt.WindowModal)
    layout = QVBoxLayout( )
    self.setLayout(layout)
    layout.setMargin( 10 )
    layout.setSpacing( 5 )

    self.condition = None
    self.signature = signature
    self._currentDirectory = None
    if message is not None:
      lab = QLabel( unicode(message) )
      layout.addWidget(lab)
      lab.setSizePolicy( QSizePolicy( QSizePolicy.Preferred, QSizePolicy.Fixed ) )

    self.editors = {}
    if signature is not None:
      sv = WidgetScrollV( )
      layout.addWidget(sv)
      first = None
      svWidget=QWidget()
      svWidgetLayout=QVBoxLayout()
      svWidget.setLayout(svWidgetLayout)
      for ( k, p ) in self.signature.items():
        hb = QHBoxLayout( )
        svWidgetLayout.addLayout(hb)
        l=QLabel( k + ': ' )
        hb.addWidget(l)
        e = p.editor( None, k, self )
        hb.addWidget(e)
        self.editors[ k ] = e
        if first is None: first = e
      sv.setWidget(svWidget)
      
    self.group1 = QButtonGroup( )
    group1Widget=QWidget()
    group1Layout=QHBoxLayout()
    group1Widget.setLayout(group1Layout)
    layout.addWidget(group1Widget)
    self._actions = {}
    self.group2 = QButtonGroup( )
    group2Widget=QWidget()
    group2Layout=QHBoxLayout()
    group2Widget.setLayout(group2Layout)
    layout.addWidget(group2Widget)
    deleteGroup1 = 1
    i=0
    for b in buttons:
      if type( b ) in ( types.TupleType, types.ListType ):
        caption, action = b
        btn = QPushButton( unicode( caption ) )
        group1Layout.addWidget(btn)
        self.group1.addButton(btn, i)
        btn.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
        self._actions[ group1.id( btn ) ] = action
        deleteGroup1 = 0
      else:
        btn = QPushButton( unicode( b ) )
        group2Layout.addWidget(btn)
        self.group2.addButton(btn, i)
        btn.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
      i+=1
    if deleteGroup1:
      group1Widget.close( )
    else:
      group1Widget.setSizePolicy( QSizePolicy( QSizePolicy.Minimum, QSizePolicy.Fixed ) )
      self.connect( self.group1, SIGNAL( 'buttonClicked(int)' ), self._doAction )
    group2Widget.setSizePolicy( QSizePolicy( QSizePolicy.Minimum, QSizePolicy.Fixed ) )
    self.connect( self.group2, SIGNAL( 'buttonClicked(int)' ), self.select )

  def select( self, value ):
    for e in self.editors.values():
      e.checkValue()
    if self.condition is not None:
      condition = self.condition
      self.condition = None
      condition.result = value
      condition.acquire()
      condition.notify()
      condition.release()
      self.close( )
    if self._exitLoop:
      self._result = value
      self._exitLoop = 0
      self.close( )
      #qApp.exit()

  def setValue( self, name, value ):
    mainThreadActions().push( self.editors[ name ].setValue, value )

  def getValue( self, name ):
    return mainThreadActions().call( self.editors[ name ].getValue )

  def _doAction( self, index ):
    self._actions[ index ]( self )

  def call( self ):
    if neuroConfig.gui:
      if _mainThreadActions.isInMainThread():
        # Actually, this function cannot be called from the
        # main thread
        #raise Exception( _t_("can't call <code>UserDialog.call()</code> from main thread") )
        self._result = None
        self._exitLoop = 1
        self.show()
        #qApp.enter_loop()
        self.exec_()
        result = self._result
        del self._result
        return result
      else:
        self.condition = threading.Condition()
        condition = self.condition
        condition.result = -1
        self._exitLoop = 0
        _mainThreadActions.push( self.show )
        condition.acquire()
        condition.wait()
        condition.release()
        result = condition.result
        self.condition = None
        return result
    return -1

  def closeEvent( self, e ):
    QWidget.closeEvent( self, e )
    self.done( -1 )


#----------------------------------------------------------------------------
class ProcessEdit( QDialog ):
  def __init__( self, process ):
    QDialog.__init__( self, None )
    layout = QVBoxLayout( )
    self.setLayout(layout)
    layout.setMargin( 10 )
    layout.setSpacing( 5 )
    neuroConfig.registerObject( self )

    self.process = process
    t = _t_(process.name)
    self.setWindowTitle( t )
    
    spl = QSplitter( Qt.Vertical )
    layout.addWidget(spl)
    w=QWidget(spl)
    vb = QVBoxLayout( )
    w.setLayout(vb)
    
    self.labName = QLabel( '<center><h3>' + t + '</h3></center>', spl )
    vb.addWidget(self.labName)

    hb = QHBoxLayout( )
    vb.addLayout(hb)
    l=QLabel( _t_('HTML Path')+': ' )
    hb.addWidget(l)
    self.leHTMLPath = QLineEdit( )
    hb.addWidget(self.leHTMLPath)
    hb = QHBoxLayout( )
    vb.addLayout(hb)
    l=QLabel( _t_('Language')+': ' )
    hb.addWidget(l)
    self.cmbLanguage = QComboBox( )
    self.cmbLanguage.setEditable(False)
    hb.addWidget(self.cmbLanguage)
    for i in neuroConfig._languages:
      self.cmbLanguage.addItem( i )
      if i == neuroConfig.language:
        self.cmbLanguage.setCurrentIndex( self.cmbLanguage.count() - 1 )
    self.connect( self.cmbLanguage, SIGNAL( 'activated(int)' ), self.changeLanguage )

    l=QLabel( _t_('Short description') + ':' )
    vb.addWidget(l)
    self.mleShort = QTextEdit( )
    self.mleShort.setAcceptRichText(False)
    vb.addWidget(self.mleShort)

    w=QWidget(spl)
    vb = QVBoxLayout()
    w.setLayout(vb)
    #spl.setLayout(vb)
    hb = QHBoxLayout( )
    vb.addLayout(hb)
    l=QLabel( _t_('Parameter')+': ' )
    hb.addWidget(l)
    self.cmbParameter = QComboBox( )
    self.cmbParameter.setEditable(False)
    hb.addWidget(self.cmbParameter)
    stack = QStackedWidget( )
    vb.addWidget(stack)
    self.mleParameters = {}
    for n in self.process.signature.keys():
      mle = QTextEdit(  )
      mle.setAcceptRichText(False)
      vb.addWidget(mle)
      stack.addWidget( mle )
      self.mleParameters[ self.cmbParameter.count() ] = mle
      self.cmbParameter.addItem( n )
      self.connect( self.cmbParameter, SIGNAL( 'activated(int)' ), stack, SLOT( 'setCurrentIndex(int)' ) )
    stack.setCurrentIndex( 0 )

    w=QWidget(spl)
    vb = QVBoxLayout( )
    w.setLayout(vb)
    l=QLabel( _t_('Long description') + ':' )
    vb.addWidget(l)
    self.mleLong = QTextEdit( )
    self.mleLong.setAcceptRichText(False)
    vb.addWidget(self.mleLong)

    self.readDocumentation()
    self.setLanguage( unicode( self.cmbLanguage.currentText() ) )
    
    w=QWidget()
    hb = QHBoxLayout( )
    w.setLayout(hb)
    vb.addWidget(w)
    hb.setMargin( 5 )
    w.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Fixed ) )
    btn = QPushButton( _t_('apply') )
    hb.addWidget(btn)
    btn.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    self.connect( btn, SIGNAL( 'clicked()' ), self.applyChanges )

    btn = QPushButton( _t_('Ok') )
    hb.addWidget(btn)
    btn.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    self.connect( btn, SIGNAL( 'clicked()' ), self, SLOT( 'accept()' ) )

    btn = QPushButton( _t_('Cancel') )
    hb.addWidget(btn)
    btn.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    self.connect( btn, SIGNAL( 'clicked()' ), self, SLOT( 'reject()' ) )

    self.resize( 800, 600 )

  def closeEvent( self, event ):
    neuroConfig.unregisterObject( self )
    QWidget.closeEvent(self, event)

  def readDocumentation( self ):
    self.documentation = neuroProcesses.readProcdoc( self.process )

  def writeDocumentation( self ):
    procdocToXHTML( self.documentation )
    self.setLanguage( self.language )
    writeProcdoc( self.process, self.documentation )

  def setLanguage( self, lang ):
    self.leHTMLPath.setText(XHTML.html(self.documentation.get( 'htmlPath', '' )) )
    self.language = lang
    d = self.documentation.get( lang, {} )
    self.mleShort.setPlainText( XHTML.html( d.get( 'short', '' ) ) )
    self.mleLong.setPlainText( XHTML.html( d.get( 'long', '' ) ) )
    p = d.get( 'parameters', {} )
    for i,j in self.mleParameters.items():
      j.setPlainText( XHTML.html( p.get( unicode( self.cmbParameter.itemText( i ) ), '' ) ) )

  def saveLanguage( self ):
    d = {}
    d[ 'short' ] = self.escapeXMLEntities( unicode( self.mleShort.toPlainText() ) )
    d[ 'long' ] = self.escapeXMLEntities( unicode( self.mleLong.toPlainText() ) )
    d[ 'parameters' ] = p = {}
    for i,j in self.mleParameters.items():
      p[ unicode( self.cmbParameter.itemText( i ) ) ] = self.escapeXMLEntities( unicode( j.toPlainText() ) )
    self.documentation[ self.language ] = d
    htmlPath = unicode( self.leHTMLPath.text() )
    if htmlPath:
      self.documentation[ 'htmlPath' ] = htmlPath
    else:
      try:
        del self.documentation[ 'htmlPath' ]
      except KeyError:
        pass

  @staticmethod
  def escapeXMLEntities( s ):
    return re.sub( r'&([a-z]+);', lambda m: '&amp;'+m.group(1)+';', s )
  
  
  def changeLanguage( self ):
    self.saveLanguage()
    self.setLanguage( unicode( self.cmbLanguage.currentText() ) )

  def applyChanges( self ):
    self.saveLanguage()
    self.writeDocumentation()
    generateHTMLProcessesDocumentation( self.process )

  def accept( self ):
    self.applyChanges()
    QDialog.accept( self )


#----------------------------------------------------------------------------
class ProcessSelectionWidget( QMainWindow ):
  """
  This widget is the main window in brainvisa.
  Provides navigation among processes and creation of user profiles (sub group of processes).
  """

  def __init__( self ):
    QMainWindow.__init__( self )
    
    if getattr( ProcessSelectionWidget, '_pixmapCache', None ) is None:
      ProcessSelectionWidget._pixmapCache = {}
      for file in ( 'icon_process_0.png', 'icon_process_1.png', 'icon_process_2.png', 'icon_process_3.png', 'folder.png' ):
        fullPath = os.path.join( neuroConfig.iconPath, file )
        ProcessSelectionWidget._pixmapCache[ fullPath ] = QIcon( fullPath )
    
    centralWidget=QWidget()
    self.setCentralWidget(centralWidget)
    
    # Menu setup
    menu = self.menuBar()
    addBrainVISAMenu( self, menu )
    neuroConfigGUI.addSupportMenu( self, menu )

    # the main layout contains vertically : a QSplitter (processes | doc) and a QHBoxLayout (open and edit buttons)
    layout=QVBoxLayout()
    centralWidget.setLayout(layout)
    layout.setMargin( 10 )

    # the splitter contains the processes on the left and the documentation on the right
    splitter = QSplitter( )
    layout.addWidget(splitter)

    # left part of the splitter : QVBoxLayout : processTrees and the search box
    w=QWidget(splitter)
    vb = QVBoxLayout()
    vb.setMargin(0)
    w.setLayout(vb)
    self.currentProcessId = None
    self.processTrees=ProcessTreesWidget()
    vb.addWidget(self.processTrees)
    self.processTrees.setSizePolicy( QSizePolicy( QSizePolicy.Preferred,
      QSizePolicy.Preferred ) )
    QObject.connect(self.processTrees, SIGNAL('selectionChanged'), self.itemSelected )
    QObject.connect(self.processTrees, SIGNAL('doubleClicked'), self.openProcess )
    QObject.connect(self.processTrees, SIGNAL('openProcess'), self.openProcess )
    QObject.connect(self.processTrees, SIGNAL('editProcess'), self.editProcess )
    QObject.connect(self.processTrees, SIGNAL('iterateProcess'), self.iterateProcess )
    # the hacked search box
    p = os.path.join( neuroConfig.mainPath, 'qt4gui', 'searchbox.ui' )
    self.searchbox = QWidget()
    uic.loadUi(p, self.searchbox)
    vb.addWidget(self.searchbox)
    self.searchboxSearchB = self.searchbox.BV_search
    self.searchboxSearchB.setShortcut( QKeySequence.Find )
    self.matchedProcs = []
    self.searchboxResetSearchB = self.searchbox.BV_resetsearch
    self.searchboxLineEdit = self.searchbox.BV_searchlineedit
    self._continueSearching = 0
    QObject.connect(self.searchboxSearchB, SIGNAL('clicked()'), self.buttonSearch)
    QObject.connect(self.searchboxResetSearchB, SIGNAL('clicked()'), self.resetSearch )

    # right part of the splitter : documentation panel
    self.info = HTMLBrowser( splitter )
    #hb.setResizeMode( self.info, QSplitter.Stretch )
    #x = hb

    # bottom of the central widget : buttons open and edit
    hb = QHBoxLayout()
    layout.addLayout(hb)
    self.setSizePolicy( QSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Fixed ) )
    hb.setMargin( 5 )
    self.btnOpen = QPushButton( _t_('Open') )
    hb.addWidget(self.btnOpen)
    self.btnOpen.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    self.btnOpen.setEnabled( 0 )
    QObject.connect( self.btnOpen, SIGNAL( 'clicked()' ), self.openProcess )
    
    if neuroConfig.userLevel >= 1:
      self.btnEdit = QPushButton( _t_('Edit') )
      hb.addWidget(self.btnEdit)
      self.btnEdit.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
      self.btnEdit.setEnabled( 0 )
      QObject.connect( self.btnEdit, SIGNAL( 'clicked()' ), self.editProcess )
    else:
      self.btnEdit = None

    self.updateList()

    # try to start with a doc opened
    sep = '//'
    if neuroConfig.platform == 'windows':
      sep = '/'
    self.info.setSource( 'file:' + sep + neuroConfig.getDocFile(os.path.join( 'help','index.html' ) ) )
    self.resize( 800, 600 )
    splitter.setSizes( [ 400, 400 ] )

  def buttonSearch(self):
    """
    Called when user click on search / next button. 
    The text written in the search box is searched in tree leaves names (processes). 
    The first item found which name contains the searched string becomes selected. If the user click another time on the search / next button, next item is searched...
    """
    # new search
    if not self.matchedProcs :
        # searched string
        s = unicode(self.searchboxLineEdit.text()).lower()
        if s == "":
            self.matchedProcs = None
        else:
          # search for items which name contains the string -> generator
          self.matchedProcs = self.processTrees.findItem(s)
    # next search
    if self.matchedProcs:
      try:# an exception will occur when there is no more items
        item=self.matchedProcs.next() 
        self.searchboxLineEdit.setEnabled(False)
        self.searchboxSearchB.setText( 'next' )
        self.searchboxSearchB.setShortcut( QKeySequence.FindNext )
      except:
        self.resetSearch()
        
  def resetSearch(self):
    """
    Called at the end of a search or when the user click on reset button.
    """
    self.matchedProcs = None
    self.searchboxSearchB.setText('search')
    self.searchboxSearchB.setShortcut( QKeySequence.Find )
    self.searchboxLineEdit.setEnabled(True)

  def itemSelected( self, item ):
    """
    Called when a tree item becomes selected. currentProcessId is updated and associated documentation is shown.
    @type item: ProcessTree.Item
    @param item: the newly selected item
    """
    if item:
      if item.isLeaf():
        processId = item.id
        if isinstance( processId, type ) and issubclass( processId, newProcess.NewProcess ):
          source = processId.onlineDocumentationSource()
          if source is None:
            self.info.setText( processId.onlineDocumentationHTML() )
          else:
            self.info.setSource( source )
          self.btnOpen.setEnabled( True )
          if self.btnEdit is not None: self.btnEdit.setEnabled( False )
        else:
          self.currentProcessId = processId
          self.btnOpen.setEnabled( 1 )
          documentation = neuroProcesses.readProcdoc( self.currentProcessId )
          source = neuroProcesses.getHTMLFileName( self.currentProcessId )
          if os.path.exists( source ):
            self.info.setSource( source )
          else:
            self.info.setText( '' )
          if self.btnEdit is not None: self.btnEdit.setEnabled( 1 )
      else:
        self.currentProcessId = None
        self.btnOpen.setEnabled( 0 )
        if self.btnEdit is not None: self.btnEdit.setEnabled( 0 )
        # Construct categroy HTML documentation file name
        self.info.showCategoryDocumentation( item.id )
    else:
     self.info.setText( '' )

  def openProcess( self, item=None ):
    """
    Called to open current process. 
    If the process is not given, selected process in current tree is opened.
    
    @type item: ProcessTree.Item
    @param item: the process to open
    """
    processId=None
    if item is not None: # open given item
      if item.isLeaf():
        processId=item.id
        showProcess(processId)
    else: # if it is not given (open button), open selected item in current process tree
      item=self.processTrees.treeStack.currentWidget().currentItem()
      if item is not None:
        item=item.model
        if item.isLeaf():
          processId=item.id
          showProcess(processId)
    if processId != self.currentProcessId:
      self.itemSelected(item) 

  def editProcess( self, item=None ):
    processId=None
    if item is not None:
      if item.isLeaf():
        processId=item.id
    else:
      processId=self.currentProcessId
    win = ProcessEdit( neuroProcesses.getProcessInstance( processId ) )
    win.show()

  def iterateProcess( self, item=None ):
    processId=None
    if item is not None:
      if item.isLeaf():
        processId=item.id
    else:
      processId=self.currentProcessId
    self.currentProcess=neuroProcesses.getProcessInstance(processId)
    #print "iterate process", processId
    self._iterationDialog = IterationDialog( self, self.currentProcess, self )
    self.connect( self._iterationDialog, SIGNAL( 'accept' ),
                  self._iterateAccept )
    self._iterationDialog.show()
    
  def _iterateAccept( self ):
    """
    Call back when accepting iteration dialog. Iterates the selected process.
    """
    try:
      params = self._iterationDialog.getLists()
      processes = self.currentProcess._iterate( **params )
      iterationProcess = neuroProcesses.IterationProcess( self.currentProcess.name, processes )
      showProcess( iterationProcess )
    except:
      neuroException.showException()
      self._iterationDialog.show()

  def updateList(self):
    """
    Reloads the list of process trees.
    """
    self.processTrees.setModel( neuroProcesses.updatedMainProcessTree() )

  def closeEvent ( self, event ):
    quitRequest()
    event.ignore()

#----------------------------------------------------------------------------
class ProcessTreesWidget(QSplitter):
  """
  A widget that shows a list of ProcessTree.
  Each process tree presents a sub group of existing processes.
  It's composed of two parts : 
    - the list of process trees (use profiles)
    - a view of currently selected tree
  Each process tree can be opened in another window in order to enable drag and drop from one tree to another. 

  @type treeIndex: TreeListWidget
  @ivar treeIndex: Widget containing items representing each process tree
  @type treeStack: QWidgetStack
  @ivar treeStack: A stack of EditableTreeWidget, representing the content of each processTree
  @type treeStackIdentifiers: dict
  @ivar treeStackIdentifiers: associates a processTree to an unique integer identifier used with the widget stack.
  Only the selected processTree widget of the stack is visible.
  @type widgets: list
  @ivar widgets: list of EditableTreeWidget currently in the stack.
  Usefull because QWidgetStack doesn't provide iterator on its content.
  @type openedTreeWidget: EditableTreeWidget
  @ivar openedTreeWidget: Currently opened process tree. It is in a window independant from the main window.
  @type model: ProcessTrees
  @ivar model: list of ProcessTree which this widget represents
  @type popupMenu: QPopupMenu
  @ivar popupMenu: contextual menu associated to the list of process trees.
  @type savesTimer: QTimer
  @param savesTimer: a timer started when the model has changed. When the timer times out, the model is saved. Used to delay model saves : it speeds up execution when there is several modification at the same time (drag&drop several elements). 
  """

  def __init__(self, processTrees=None, parent=None ):
    """
    @type processTrees: ProcessTrees
    @param processTrees: the list of process trees which this widget represents
    @type parent: QWidget
    @param parent: container of this widget
    """
    QSplitter.__init__(self, parent)
    self.treeIndex=TreeListWidget(None, self, iconSize=bigIconSize)
    self.treeIndex.setSizePolicy( QSizePolicy( QSizePolicy.Preferred, QSizePolicy.Preferred ) )
    # signals
    self.connect(self.treeIndex, SIGNAL( 'currentItemChanged ( QTreeWidgetItem *, QTreeWidgetItem * )' ), self.setCurrentTree)
    # on clicking on a tree, emit a pysignal for transmitting the signal to the parent. The shown documentation may need to be changed. (clicked instead of selectionChanged because the documentation may need to be changed event if the item was already selected)
    self.connect(self.treeIndex, SIGNAL( 'itemClicked( QTreeWidgetItem *, int )' ), self.selectionChanged)
    self.connect(self.treeIndex, SIGNAL( 'customContextMenuRequested ( const QPoint & )'), self.openContextMenu)
    # help tooltip
    self.treeIndex.setToolTip(_t_("Create your own lists of processes choosing new in contextual menu.<br>To add items in a list, open an existing list and move items in the new list.<br>If you set a list as default, it will selected the next time you run brainvisa.") )

    self.treeStack=QStackedWidget(self)
    self.treeStackIdentifiers = {}
    self.treeStack.setSizePolicy( QSizePolicy( QSizePolicy.Preferred,
      QSizePolicy.Preferred ) )
    #self.setResizeMode( self.treeIndex, QSplitter.FollowSizeHint )
    self.widgets=[]
    self.openedTreeWidget=None
    
    # Popup Menu for toolboxes
    self.popupMenu = QMenu()
    self.popupMenu.addAction( _t_("New"),  self.menuNewTabEvent )
    self.popupMenu.addAction( _t_("Delete"),  self.menuDelTabEvent )
    self.popupMenu.addAction( _t_("Open"), self.menuOpenTabEvent)
    self.popupMenu.addAction( _t_("Set as default list"), self.menuSetDefaultEvent)
    
    # Popup Menu for processes
    self.processMenu = QMenu()
    self.processMenu.addAction( _t_("Open"),  self.menuOpenProcessEvent )
    self.processMenu.addAction( _t_("Edit"),  self.menuEditProcessEvent )
    self.processMenu.addAction( _t_("Iterate"), self.menuIterateProcessEvent)

    if processTrees:
      self.setModel(processTrees)

  def setModel(self, processTrees):
    """
    The widget is initialized with the given list of process tree. 
    For each process tree, an item is added in treeIndex. A widget is created to represent each process tree and added to treeStack.
    @type processTrees: ProcessTrees
    @param processTrees: the list of process trees which this widget represents
    """
    # clear widgets
    self.treeIndex.clear()
    for w in self.widgets:
      self.treeStack.removeWidget(w)
    self.treeStackIdentifiers = {}
    self.widgets=[]
    # register model and add listener
    self.model=processTrees
    self.model.addListener(self.updateContent)
    # listens the change of selectedTree attribute in model
    self.model.onAttributeChange("selectedTree", self.updateSelectedTree)
    self.model.onAttributeChange("selectedTree", self.modelChanged)
    self.model.addListener(self.modelChanged)
    # for each processTree, create an EditableTreeWidget which is added to the widget stack
    # and add an element to the list index of trees
    for processTree in processTrees.values():
      self.addProcessTree(processTree)
    self.treeIndex.setModel(processTrees)
    
    # if there's a selected tree by default, the corresponding item in widget is selected
    if self.model.selectedTree != None:
      found=False
      i=0
      while i <self.treeIndex.topLevelItemCount() and not found: # search selected tree corresponding item in treeIndex widget
        item=self.treeIndex.topLevelItem(i)
        i+=1
        if item.model==self.model.selectedTree:
          found=True
          self.treeIndex.setCurrentItem(item)
    
    # Create a timer to delay model saves in minf file : it speeds up execution when there is several modification at the same time (drag&drop several elements)
    self.savesTimer=QTimer()
    self.savesTimer.setSingleShot(True)
    self.connect(self.savesTimer, SIGNAL("timeout()"), self.model.save)

  
  def addProcessTree(self, processTree):
    """
    Add elements in the widget to add a representation of this process tree. 
    @type processTree: ProcessTree
    @param processTree: new process tree for which the widget must be completed.
    """
    treeWidget=EditableTreeWidget( processTree, self.treeStack )
    if processTree.modifiable:
      treeWidget.setToolTip(_t_("This list is customizable. You can :<br>- move items by drag and drop,<br>- delete item with del key,<br>- copy items by drag and drop and ctrl key,<br>- create new category with contextual menu."))
    # signals 
    # selectionChanged doesn't work with multiple selection
    # currentChanged isn't emited when click on an item that has already keyboeard focus and is not emited when click on an already selected item altought it may be necessary to update documentation because several items can be selected at the same time
    # -> so use clicked signal instead
    self.connect(treeWidget, SIGNAL( 'itemClicked( QTreeWidgetItem *, int )' ), self.selectionChanged)
    self.connect(treeWidget, SIGNAL( 'itemDoubleClicked( QTreeWidgetItem *, int )' ), self.doubleClicked)
    self.connect(treeWidget, SIGNAL( 'customContextMenuRequested ( const QPoint & )'), lambda p : self.openProcessMenu(treeWidget, p))
    # the new widget representing the process tree is added in treeStack and in widgets
    stackIdentifier = self.treeStack.addWidget( treeWidget )
    self.treeStackIdentifiers.setdefault( object.__hash__( processTree ), stackIdentifier )
    self.widgets.append(treeWidget)
    # listens changes in the process tree (for saving each change in minf file)
    processTree.addListenerRec(self.modelChanged)
    processTree.onAttributeChangeRec("name", self.modelChanged)

  def showTreeIndex(self):
    if self.treeIndex.isHidden():
      self.treeIndex.show()
    else:
      self.treeIndex.hide()
    
  def openContextMenu(self, point):
    """
    Called on contextMenuRequested signal. It opens the popup menu at cursor position.
    """
    self.popupMenu.exec_(QCursor.pos())

  def openProcessMenu(self, listView, point):
    """
    Called on contextMenuRequested signal on the list of processes of a toolbox. It opens the process menu at cursor position if the current item represents a process.
    """
    item=listView.itemAt(point)
    if item and item.model and item.model.isLeaf():
      self.processMenu.exec_(QCursor.pos())
    else:
      listView.openContextMenu(point)

  def updateContent(self, action=None, items=None, position=None):
    """
    Called on model change (list of process trees). The widget must update itself to reflect the change.
    """
    # treeIndex is a TreeListWidget and has already a listener which update the view on model changes
    # but some changes imply modification of treeStack -> add a widget in the stack or remove a widget
    if action==ObservableList.INSERT_ACTION:# add a new process tree in the list
      for processTree in items:
        self.addProcessTree(processTree)
    elif action==ObservableList.REMOVE_ACTION:# remove a process tree
      for processTree in items:
        w=self.treeStack.widget( self.treeStackIdentifiers.get( object.__hash__( processTree ) ) )
        self.treeStack.removeWidget(w)
        self.widgets.remove(w)
  
  def updateSelectedTree(self, newSelection):
    """
    Called when the selected tree changes. 
    """
    pass # maybe set a graphical element to show it is the default list...

  def modelChanged(self, action=None, items=None, position=None):
    """
    Method registred to be called when a process tree has changed or when the list of tree has changed.
    New ProcessTree list must be saved in a minf file.
    If change is insertion of a new item in a tree, registers listeners on this new item.
    """
    #print "model changed", action, "write to minf file processTrees.minf"
    if action==ObservableList.INSERT_ACTION:
      for item in items:
        # on insertion in a tree, listen changes of the new element
        # on insertion of a tree in the tree list, nothing to do, listeners are already registred
        if not issubclass(item.__class__, neuroProcesses.ProcessTree):
          if not item.isLeaf():
            item.addListenerRec(self.modelChanged)
            item.onAttributeChangeRec("name", self.modelChanged)
          else:
            item.onAttributeChange("name", self.modelChanged)
    # instead of systematic model save for each change, start a timer wich will timeout when current event is finished
    # So if there is several modification due to the same event (drag and drop several elements), the model will be saved only one time when all changes are done. (speedier)
    if not self.savesTimer.isActive(): # if the timer is already started nothing to do, the change will be save anyway
      self.savesTimer.start(0)
    #self.model.save()

  def selectionChanged(self, item, col=0):
    """
    Called when selected item has changed in current process tree. 
    This method emits a signal that must be caught by parent widget. 
    """
    if item is not None:
      self.emit(SIGNAL("selectionChanged"), item.model)

  def doubleClicked(self, item, col):
    """
    Called on double click on an item of current process tree. 
    This method emits a signal that must be caught by parent widget. 
    """
    self.emit(SIGNAL("doubleClicked"), item.model)

  def setCurrentTree(self, item, previous=None):
    """
    Changes the visible widget in the stack.
    """
    self.treeStack.setCurrentIndex( self.treeStackIdentifiers.get( object.__hash__( item.model ) ) )

  def findItem( self, name):
    """
    Find items that contain the string given in parameters in their name. Each found item is selected and yield (and replace previous selection).
    Wide search.
    @type name: string
    @param name: string searched in items names. 
    
    @rtype:  generator
    @return: a generator
    """
    for widget in self.widgets: # for all process trees widgets
      it=QTreeWidgetItemIterator(widget)
      lastSelection=None
      while it.value():
        item=it.value()
        if not item.isHidden():
          if item.model.isLeaf(): # for a leaf (process) search string in name
            if item.model.name.lower().find(name) > -1:
              self.select(widget, item, lastSelection)
              lastSelection=(widget, item)
              yield item
        it+=1

  def select(self, widget, item, lastSelection):
    """
    Select a process tree and an item in it. Undo last selection.
    @type widget: EditableTreeWidget
    @param widget:  the tree widget that contains the item to select. 
    @type item: EditableTreeItem
    @param item: the item (process) to select
    @type lastSelection: tuple (EditableTreeWidget, EditableTreeItem)
    @param lastSelection: previous selected item and its container, to be unselected.
    """
    self.selectIndex(widget.model) # select in left panel (toolbox name)
    self.setCurrentTree(widget) # raise widget of toolbox content
    item.setHidden(False)
    #widget.ensureItemVisible( item ) # show item (open parents...)
    widget.setCurrentItem( item ) # select item
    if lastSelection:# undo last selection
      lastSelection[1].setSelected(False)
      #lastSelection[0].setSelected(lastSelection[1], 0)
 
  def selectIndex(self, model):
    """
    Select a process tree in the left panel (toolboxes).
    
    @type model : ProcessTree
    @param model: the process tree to select
    """
    i=0
    found=False
    while i<self.treeIndex.topLevelItemCount() and not found: # search selected tree corresponding item in treeIndex widget
      item=self.treeIndex.topLevelItem(i)
      if item.model==model:
        found=True
        self.treeIndex.setCurrentItem(item)
      i+=1

  #------ context menu events ------
  def menuNewTabEvent(self):
    """
    Called on click on new option in contextual menu. 
    Adds a new empty tree in the model.
    """
    processTree=neuroProcesses.ProcessTree()
    processTree.new=True
    self.model.add(processTree)

  def menuDelTabEvent(self):
    """
    Called on click on del option in contextual menu.
    Removes the selected tree from the model.
    """
    item=self.treeIndex.selectedItem()
    if item:
      if item.model.modifiable:
        del self.model[item.model.id]

  def menuOpenTabEvent(self):
    """
    Called on click on open option in contextual menu.
    Opens selected tree in a new window.
    """
    item=self.treeIndex.selectedItem()
    if item:
      self.openedTreeWidget=EditableTreeWidget(item.model)
      self.openedTreeWidget.resize(400,600)
      self.openedTreeWidget.show()

  def menuSetDefaultEvent(self):
    """
    Called on click on set default option in contextual menu.
    Sets the selected tree as the default selected tree. So on next run of brainvisa, this tree will be selected.
    """
    item=self.treeIndex.currentItem()
    if item:
      self.model.selectedTree=item.model

  def menuOpenProcessEvent(self):
    """
    Called on click on open option in process menu.
    Emits a signal for the parent window which will open the process.
    """
    item=self.treeStack.currentWidget().currentItem()
    if item:
      self.emit(SIGNAL("openProcess"), item.model )
  
  def menuEditProcessEvent(self):
    """
    Called on click on edit option in process menu.
    Emits a signal for the parent window which will edit the process.
    """
    item=self.treeStack.currentWidget().currentItem()
    if item:
      self.emit(SIGNAL("editProcess"), item.model )

  def menuIterateProcessEvent(self):
    """
    Called on click on iterate option in process menu.
    Emits a signal for the parent window which will iterate the process.
    """
    item=self.treeStack.currentWidget().currentItem()
    if item:
      self.emit(SIGNAL("iterateProcess"), item.model )

#----------------------------------------------------------------------------
class MainWindow( QWidget ):
  def __init__( self ):
    QWidget.__init__( self )
    self.myLayout = QVBoxLayout( self )
    self.setLayout(self.myLayout)
    self.mainModules = []
    self.subLayouts = []
    neuroConfig.registerObject( self )

  def closeEvent(self, event):
    neuroConfig.unregisterObject( self )
    QWidget.closeEvent( self, event )

  def addMainModule( self, identifier, name, image, description ):
    # Create main module widget
    w=QWidget(self)
    layout=QVBoxLayout(w)
    w.setLayout(layout)
    l = QLabel( _t_( name ),self )
    layout.addWidget(l)
    hb = QHBoxLayout( )
    layout.addLayout(hb)
    l = QLabel(  )
    hb.addWidget(l)
    l.setIcon( QIcon( os.path.join( neuroConfig.mainPath, 'doc', 'images', image ) ) ),
    l.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    l.resize( 320, 200 )
    l = QTextEdit(  )
    hb.addWidget(l)
    l.setText( description )
    l.setReadOnly( True )

    if ( len( self.mainModules ) % 2 == 0 ):
      self.subLayouts.append( QHBoxLayout( self.layout() ) )
    self.subLayouts[ -1 ].addWidget( w )
    w.show()
    self.mainModules.append( w )



#----------------------------------------------------------------------------
class RemoteContextGUI( QTreeWidgetItem ):
  """
  Specific GUI to display messages returned by processes executed remotely.
  """
  
  def __init__(self, parent, name='Remote Hosts:'):
    """
    The specific GUI is a QListView. It is composed of an arborescence of QListViewItems that sorts
    the messages according to the process and the host they belong to::
    
    Remote Hosts:
    |
    --host
      |
      --process
        |
        --message
        --message
      --process
        |
        --message
        
    @param parent: the QListView.
    @param name: name 
    """

    remoteView = QTreeWidget(parent)
    remoteView.setSizePolicy( QSizePolicy( QSizePolicy.Expanding,
      QSizePolicy.Preferred ) )

    remoteView.setWindowTitle('Remote messages')
    remoteView.setColumnCount(4)
    remoteView.setHeaderLabels( ['IP', 'ID', 'Status', 'Messages'] )
    
    apply(QTreeWidgetItem.__init__,(self, remoteView, name ))
    #apply(RemoteContext.__init__,(self) )
    
    self.setExpanded(True)
    
    self.processList = {}
    self.ipList = {}
  
  def addIP(self, ip):
    i_item = QTreeWidgetItem(self, ip)
    self.ipList[str(ip)] = i_item
    i_item.setExpanded(True)
    
  def addProcess(self, ip, pid, status=' Starting...', message=''):
    p_item = QTreeWidgetItem(self.ipList[str(ip)], 'Process', '%03d'%pid, status, message)
    self.processList[str(pid)] = p_item
    self.ipList[str(ip)].insertItem(p_item)
      
  def addMessage(self, pid, message):
    m_item = QTreeWidgetItem(self.processList[str(pid)], 'Message', '', '', message)  
    self.processList[str(pid)].insertItem(m_item)
            
  def setProcessStatus(self, pid, status):
    self.processList[str(pid)].setText(2, status)

  def setCurrentMessage(self, pid, message):
    self.processList[str(pid)].setText(3, message)

  def clear(self):
    for item in self.ipList.values():
      self.takeChild(self.indexOfChild(item))
      del(item)
      
    self.processList = {}
    self.ipList = {}

  def sort(self):
    pass

  def sortChildItems(self, col, asc):
    pass

#----------------------------------------------------------------------------
def showMainWindow():
  global _mainWindow
  if neuroConfig.openMainWindow:
    #_mainWindow = ProcessSelection()
    # window with customizable lists of processes
    _mainWindow = ProcessSelectionWidget()
    _mainWindow.show()
    for w in qApp.topLevelWidgets():
      if w is not _mainWindow:

        w.raise_()
  else:
    _mainWindow = None
    
#----------------------------------------------------------------------------
def updateProcessList():
  _mainWindow.updateList()

#----------------------------------------------------------------------------
def mainThreadActions():
  return _mainThreadActions

#----------------------------------------------------------------------------

def initializeProcessesGUI():
  global _mainThreadActions
  _mainThreadActions = QtThreadCall()
  import neuroProcesses
  if neuroConfig.gui:
    exec 'from neuroProcessesGUI import *' in neuroProcesses.__dict__
    neuroProcesses._defaultContext = ExecutionContextGUI()
  else:
    exec 'from neuroProcessesGUI import mainThreadActions' in neuroProcesses.__dict__


