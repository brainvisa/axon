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

from neuroData import *
from neuroProcesses import *
from backwardCompatibleQt import *
from qtui import *
import qtui
import neuroConfig 
from neuroConfig import *
import neuroConfigGUI
import neuroLogGUI
from neuroException import *
from brainvisa.wip import newProcess
from brainvisa.history import ProcessExecutionEvent

import weakref
from soma.minf.xhtml import XHTML
from brainvisa.debug import debugHere
from soma.qtgui.api import QtThreadCall, FakeQtThreadCall, TextBrowserWithSearch
try:
  import sip
except:
  # for sip 3.x (does it work ??)
  import libsip as sip

import neuroProcesses
from soma.qtgui.api import EditableTreeWidget, TreeListWidget
from soma.notification import ObservableList, EditableTree

_mainThreadActions = FakeQtThreadCall()

#----------------------------------------------------------------------------
def startShell():
  neuroConfig.shell = True
  from qt import qApp
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
    _helpWidget.setCaption( _t_( 'BrainVISA help' ) )
    _helpWidget.resize( 800, 600 )
  sys.stdout.flush()
  _helpWidget.setSource( source )
  _helpWidget.show()
  _helpWidget.raiseW()


_aboutWidget = None
#----------------------------------------------------------------------------
class AboutWidget( QVBox ):
  def __init__( self, parent=None, name=None ):
    QVBox.__init__( self, parent, name )
    white = QColor( 'white' )
    self.setPaletteBackgroundColor( white )
    hb = QHBox( self )
    self.setMargin( 10 )
    self.setCaption( _t_( 'About') )
    if getattr( AboutWidget, 'pixIcon', None ) is None:
      setattr( AboutWidget, 'pixIcon', QPixmap( os.path.join( iconPath, 'icon.png' ) ) )
    self.setIcon( self.pixIcon )

    def buildImageWidget( parent, fileName, desiredHeight=0, white=white ):
      widget = QLabel( parent )
      widget.setPaletteBackgroundColor( white )
      widget.setAlignment( QLabel.AlignCenter )
      pixmap = QPixmap( os.path.join( iconPath, fileName ) )
      if desiredHeight:
        stretch = float( desiredHeight ) / pixmap.height()
        matrix = QWMatrix()
        matrix.scale( stretch, stretch )
        pixmap = pixmap.xForm( matrix )
      widget.setPixmap( pixmap )
      return widget

    widget = buildImageWidget( hb, 'brainvisa.png' )
    label = QLabel( versionText(), hb )
    label.setPaletteBackgroundColor( white )
    label.setMargin( 4 )
    font = QFont()
    font.setPointSize( 30 )
    label.setFont( font )

    vb = QVBox( hb )
    widget = buildImageWidget( vb, 'ifr49.png', desiredHeight=60 )
    widget.setMargin( 5 )
    widget = buildImageWidget( vb, 'neurospin.png', desiredHeight=40 )
    widget.setMargin( 5 )
    widget = buildImageWidget( vb, 'shfj.png', desiredHeight=40 )
    widget.setMargin( 5 )
    widget = buildImageWidget( vb, 'mircen.png', desiredHeight=40 )
    widget.setMargin( 5 )
    widget = buildImageWidget( vb, 'inserm.png', desiredHeight=40 )
    widget.setMargin( 5 )
    widget = buildImageWidget( vb, 'cnrs.png', desiredHeight=60 )
    widget.setMargin( 5 )
    widget = buildImageWidget( vb, 'chups.png', desiredHeight=40 )
    widget.setMargin( 5 )
    widget = buildImageWidget( vb, 'parietal.png', desiredHeight=40 )
    widget.setMargin( 5 )

    if parent is None:
      px = ( neuroConfig.qtApplication.desktop().width() - self.sizeHint().width() ) / 2
      py = ( neuroConfig.qtApplication.desktop().height() - self.sizeHint().height() ) / 2
      self.setGeometry( px, py, self.sizeHint().width(), self.sizeHint().height() )
      self.btnClose = QPushButton( _t_( 'Close' ), self )
      self.btnClose.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
      self.btnClose.setFocus()
      QObject.connect( self.btnClose, SIGNAL( 'clicked()' ), self, SLOT( 'close()' ) )

def aboutRequest():
  global _aboutWidget
  if _aboutWidget is None:
    _aboutWidget = AboutWidget()
  _aboutWidget.show()
  _aboutWidget.raiseW()

#----------------------------------------------------------------------------
def logRequest():
  neuroLogGUI.LogViewer( logFileName ).show()


#----------------------------------------------------------------------------
def addBrainVISAMenu( widget, menuBar ):
  bvMenu = QPopupMenu( widget )
  menuBar.insertItem( "&BrainVISA", bvMenu )

  bvMenu.insertItem( _t_( "&Help" ), helpRequest,  Qt.CTRL + Qt.Key_H )
  bvMenu.insertItem( _t_( "&About" ), aboutRequest, Qt.CTRL + Qt.Key_A )
  bvMenu.insertSeparator()
  bvMenu.insertItem( _t_( "&Preferences" ), editConfiguration, Qt.CTRL + Qt.Key_P )
  bvMenu.insertItem( _t_( "Show &Log" ), logRequest, Qt.CTRL + Qt.Key_L )
  bvMenu.insertItem( _t_( "&Open process..." ), ProcessView.open, Qt.CTRL + Qt.Key_O )
  bvMenu.insertItem( _t_( "Start &Shell" ), startShell, Qt.CTRL + Qt.Key_S )
  bvMenu.insertSeparator()
  if not isinstance( widget, ProcessSelectionWidget ):
    bvMenu.insertItem( _t_( "Close" ), widget.close, Qt.CTRL + Qt.Key_W )
  bvMenu.insertItem( _t_( "&Quit" ), quitRequest, Qt.CTRL + Qt.Key_Q )


#----------------------------------------------------------------------------
class HTMLBrowser( QWidget ):

  class BVTextBrowser( TextBrowserWithSearch ):
    def __init__( self, parent, name=None ):
      TextBrowserWithSearch.__init__( self, parent, name )
      self.mimeSourceFactory().setExtensionType("py", "text/plain")
      

    def setSource( self, src ):
      src = unicode( src )
      if not src.startswith( 'bvshowprocess://' ) \
         and not src.startswith( 'http://' ) \
         and not src.startswith( 'mailto:' ) :
        TextBrowserWithSearch.setSource( self, src )
        
    def createPopupMenu(self, pos):
      menu=TextBrowserWithSearch.createPopupMenu(self, pos)
      # accelerator key doesn't work, I don't know why...
      menu.insertItem("Open in a web browser", self.openWeb)#, qt.Qt.CTRL + qt.Qt.Key_F )
      return menu
      
    def openWeb(self):
      openWeb(self.source())
      

  def __init__( self, parent = None, name = None, fl = 0 ):
    QWidget.__init__( self, parent, name, fl )
    vbox = QVBoxLayout( self )
    vbox.setSpacing( 2 )
    vbox.setMargin( 3 )

    if getattr( HTMLBrowser, 'pixHome', None ) is None:
      setattr( HTMLBrowser, 'pixIcon', QPixmap( os.path.join( neuroConfig.iconPath, 'icon_help.png' ) ) )
      setattr( HTMLBrowser, 'pixHome', QPixmap( os.path.join( neuroConfig.iconPath, 'top.png' ) ) )
      setattr( HTMLBrowser, 'pixBackward', QPixmap( os.path.join( neuroConfig.iconPath, 'back.png' ) ) )
      setattr( HTMLBrowser, 'pixForward', QPixmap( os.path.join( neuroConfig.iconPath, 'forward.png' ) ) )
      setattr( HTMLBrowser, 'pixReload', QPixmap( os.path.join( neuroConfig.iconPath, 'reload.png' ) ) )

    self.setIcon( HTMLBrowser.pixIcon )

    hbox = QHBoxLayout()
    hbox.setSpacing(6)
    hbox.setMargin(0)

    btnHome = QPushButton( self )
    btnHome.setSizePolicy( QSizePolicy( QSizePolicy.Minimum, QSizePolicy.Minimum ) )
    btnHome.setPixmap( self.pixHome )
    hbox.addWidget( btnHome )

    btnBackward = QPushButton( self )
    btnBackward.setSizePolicy( QSizePolicy( QSizePolicy.Minimum, QSizePolicy.Minimum ) )
    btnBackward.setPixmap( self.pixBackward )
    btnBackward.setEnabled( 0 )
    hbox.addWidget( btnBackward )

    btnForward = QPushButton( self )
    btnForward.setSizePolicy( QSizePolicy( QSizePolicy.Minimum, QSizePolicy.Minimum ) )
    btnForward.setPixmap( self.pixForward )
    btnForward.setEnabled( 0 )
    hbox.addWidget( btnForward )

    btnReload = QPushButton( self )
    btnReload.setSizePolicy( QSizePolicy( QSizePolicy.Minimum, QSizePolicy.Minimum ) )
    btnReload.setPixmap( self.pixReload )
    btnReload.setEnabled( 1 )
    hbox.addWidget( btnReload )

    vbox.addLayout( hbox )

    browser = self.BVTextBrowser( self )
    browser.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding ) )
    vbox.addWidget( browser )

    self.connect( btnHome, SIGNAL('clicked()'), browser, SLOT( 'home()' ) )
    self.connect( btnBackward, SIGNAL('clicked()'), browser, SLOT( 'backward()' ) )
    self.connect( browser, SIGNAL('backwardAvailable(bool)'), btnBackward, SLOT('setEnabled(bool)') )
    self.connect( btnForward, SIGNAL('clicked()'), browser, SLOT( 'forward()' ) )
    self.connect( browser, SIGNAL('forwardAvailable(bool)'), btnForward, SLOT('setEnabled(bool)') )
    self.connect( browser, SIGNAL('linkClicked( const QString & )'), self.clickLink )
    self.connect( btnReload, SIGNAL('clicked()'), browser, SLOT( 'reload()' ) )

    self.browser = browser
    
    neuroConfig.registerObject( self )

  def setSource( self, source ):
    self.browser.setSource( source )

  def setText( self, text ):
    self.browser.setText( text )

  def clickLink( self, text ):
    # Oh well, OK, we should handle this with a proper MimeType, but...
    # fake protocol bvshowprocess:
  
    bvp = unicode( text )
    if bvp.startswith( 'bvshowprocess://' ):
      bvp = bvp[16:]
      # remove tailing '/'
      if bvp[ -1 ] == '/':
        bvp = bvp[ : -1 ]
      proc = getProcess( bvp )
      if proc is None:
        print 'No process of name', bvp
      else:
        showProcess( proc() )
    elif bvp.startswith( 'http://' ) or bvp.startswith( 'mailto:' ):
      try:
        openWeb(bvp)
      except:
          showException()
    else:
      self.browser.setSource( text )

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

  def close( self, alsoDelete ):
    neuroConfig.unregisterObject( self )
    return QWidget.close( self, alsoDelete )


#----------------------------------------------------------------------------
class NamedPushButton( QPushButton ):
  def __init__( self, parent, name ):
    QPushButton.__init__( self, parent, name )
    self.connect( self, SIGNAL( 'clicked()' ), self._pyClicked )

  def _pyClicked( self ):
    self.emit( PYSIGNAL( 'clicked' ), ( unicode( self.name()), ) )


#----------------------------------------------------------------------------
class WidgetScrollV( QScrollView ):
  class VBox( QVBox ):
    def __init__( self, parent, ws ):
      QVBox.__init__( self, parent )
      self.setSpacing( 5 )
      self.ws = ws

    def sizeHint( self ):
      return QSize( self.ws.visibleWidth(), QVBox.sizeHint( self ).height() )

  def __init__( self, parent = None, name = None ):
    self.box = None
    QScrollView.__init__( self, parent, name, self.WResizeNoErase )
    self.setHScrollBarMode( self.AlwaysOff )
    self.setFrameStyle( self.NoFrame )
    self.box = self.VBox( self.viewport(), self )

    self.addChild( self.box, 0, 0 )
    self.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Maximum ) )

    self.box.resize( self.visibleWidth(), self.box.height() )

  def show( self ):
    self.setMaximumSize( self.maximumWidth(), self.box.size().height() )
    return QScrollView.show( self )

  def resizeEvent( self, e ):
    result = QScrollView.resizeEvent( self, e )
    if self.box:
      self.box.resize( self.visibleWidth(), self.box.height() )
      #self.updateGeometry()
      self.setMaximumSize( self.maximumWidth(), self.box.sizeHint().height() )
      if self.box.width() != self.visibleWidth():
        self.box.resize( self.visibleWidth(), self.box.height() )
        self.updateGeometry()
    return result

  def sizeHint( self ):
    if self.box:
      return QVBox.sizeHint( self.box )
    else:
      return QScrollView.sizeHint( self )


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
      QWidget.__init__(self, parent )
      layout = QVBoxLayout( self, 5, 4 )
      self.parameterizedWidget = ParameterizedWidget( parameterized, self )
      layout.addWidget( self.parameterizedWidget )
      spacer = QSpacerItem(0,0,QSizePolicy.Minimum,QSizePolicy.Expanding)
      layout.addItem( spacer )

  def close( self, alsoDelete=False ):
    self.parameterizedWidget.close(alsoDelete)
    return QWidget.close( self, alsoDelete )

#----------------------------------------------------------------------------
class VoidClass:
  pass


#----------------------------------------------------------------------------
class NodeCheckListItem( QCheckListItem ):
  def __init__( self, node, *args ):
    QCheckListItem.__init__( self, *args )
    self._node = node
    self.setOn( node._selected )
    node._selectionChange.add( self.nodeStateChanged )

  def stateChange( self, selected ):
    self._node.setSelected( selected )

  def nodeStateChanged( self, node ):
    self.setOn( node._selected )
    self.repaint()

  def cleanup( self ):
    self._node._selectionChange.remove( self.nodeStateChanged )
    self._node = None

  def paintCell( self, painter, cg, column, width, align ):
    if self._node is not None:
      if self.type() != QCheckListItem.Controller or not self._node._optional:
        QCheckListItem.paintCell( self, painter, cg, column, width, align )
      else:
        painter.save()
        pix = self.pixmap( 0 )
        if pix and not pix.isNull():
          # I think this is a QCheckListItem bug...
          painter.translate( pix.width() + 3, 0 )
        QCheckListItem.paintCell( self, painter, cg, column, width, align )
        painter.restore()
        # translation of Qt C++ source code
        lv = self.listView()
        parentControl = 0
        if self.parent() and self.parent().rtti() == 1 and \
          sip.cast( self.parent(), QCheckListItem ).type() \
          == QCheckListItem.RadioButtonController:
          parentControl = 1
        fm = QFontMetrics( lv.fontMetrics() )
        boxsize = lv.style().pixelMetric( QStyle.PM_CheckListControllerSize,
                                          lv )
        marg = lv.itemMargin();
  
        styleflags = QStyle.Style_Default
        if self.state() == QCheckListItem.On:
          styleflags |= QStyle.Style_On
        elif self.state() == QCheckListItem.NoChange:
          if not self.isTristate():
            styleflags |= QStyle.Style_Off
          else:
            styleflags |= QStyle.Style_NoChange
        else:
          styleflags |= QStyle.Style_Off
        if self.isSelected():
          styleflags |= QStyle.Style_Selected
        if self.isEnabled() and lv.isEnabled():
          styleflags |= QStyle.Style_Enabled
  
        x = 0
        y = 0
        if not parentControl:
          x += 3
        if align & Qt.AlignVCenter:
          y = ( ( self.height() - boxsize ) / 2 ) + marg
        else:
          y = (fm.height() + 2 + marg - boxsize) / 2
        #print 'dims:', x, y, boxsize, fm.height() + 2 + marg
        # cli = QCheckListItem( self, 'toto', QCheckListItem.CheckBox ) #sip.cast(self,QCheckListItem)
        #opt = QStyleOption( cli )
        #opt = QStyleOption( self )
        # QStyleOption is buggy: listViewItem() and checkListItem() are not
        # both initialized
        # SIP is buggy: QStyleOption.__init__( QCheckListItem ) calls
        # QStyleOption::QStyleOption( QListViewItem * ) instead of
        # QStyleOption::QStyleOption( QCheckListItem * )
  ##      print 'opt:', opt
  ##      item = opt.checkListItem()
  ##      print 'item:', item, 'cli:', cli, 'lvitem:', opt.listViewItem(), 'self:', self
  ##      print 'cli.listview:', cli.listView(), ', self.lv:', self.listView()
  ##      if item:
  ##        print 'item not None'
  ##        print 'listview:', item.listView()
  ##      lv.style().drawPrimitive(QStyle.PE_CheckListIndicator, painter,
  ##                               QRect(x, y, boxsize,
  ##                                     fm.height() + 2 + marg),
  ##                               cg, styleflags, opt )
  ##      print 'drawPrim done'
  
        # copied/translated from QCommonStyle.cpp:
        r = QRect(x, y, boxsize, fm.height() + 2 + marg)
        w = r.width()
        h = r.width()
        p = painter
        item = self
  
        #p.fillRect( 0, 0, x + marg + w + 4, item.height(),
        #            QBrush( cg.background() ) )
        lv.paintEmptyArea( p, r )
        if styleflags & QStyle.Style_Enabled:
          p.setPen( QPen( cg.text(), 2 ) )
        else:
          p.setPen( QPen( lv.palette().color( QPalette.Disabled,
                                              QColorGroup.Text ), 2 ) )
        if styleflags & QStyle.Style_Selected and not lv.rootIsDecorated() and \
          not parentControl:
          p.fillRect( 0, 0, x + marg + w + 4, item.height(),
                      cg.brush( QColorGroup.Highlight ) )
          if item.isEnabled():
            p.setPen( QPen( cg.highlightedText(), 2 ) )
  
        if styleflags & QStyle.Style_NoChange:
          p.setBrush( cg.brush( QColorGroup.Button ) )
        p.drawRect( x+marg, y+2, w-4, h-4 )
        x+=1
        y+=1
        if ( styleflags & QStyle.Style_On) or \
              ( styleflags & QStyle.Style_NoChange ):
          a = QPointArray( 7*2 )
          xx = x+1+marg
          yy=y+5
          for i in range(3):
            a.setPoint( 2*i,   xx, yy )
            a.setPoint( 2*i+1, xx, yy+2 )
            xx+=1
            yy+=1
          yy -= 2;
          for i in range(3,7):
            a.setPoint( 2*i,   xx, yy )
            a.setPoint( 2*i+1, xx, yy+2 );
            xx+=1
            yy-=1
          p.drawLineSegments( a )

  def activate( self ):
    if self.type() == QCheckListItem.Controller and self._node._optional:
      # translation of Qt C++ source code
      lv = self.listView()
      if lv and not lv.isEnabled() or not self.isEnabled():
        return
      boxsize = lv.style().pixelMetric( QStyle.PM_CheckListButtonSize, lv )
      pos = QPoint()
      if self.activatedPos( pos ):
        parentControl = 0
        if self.parent() and self.parent().rtti() == 1 and \
           sip.cast( self.parent(), QCheckListItem).type() \
           == QCheckListItem.RadioButtonController:
          parentControl = 1
        x = 3
        if parentControl:
          x = 0
        align = lv.columnAlignment( 0 )
        marg = lv.itemMargin()
        y = 0
        if align & Qt.AlignVCenter:
          y = ( ( self.height() - boxsize ) / 2 ) + marg
        else:
          y = (lv.fontMetrics().height() + 2 + marg - boxsize) / 2
        r = QRect( x, y, boxsize-3, boxsize-3 )
        r.moveBy( lv.header().sectionPos( 0 ), 0 )
        if not r.contains( pos ):
          return
      if self.state() == QCheckListItem.On:
        self.setState( QCheckListItem.Off )
      elif self.state() == QCheckListItem.Off:
        if not self.isTristate():
          self.setState( QCheckListItem.On )
        else:
          self.setState( QCheckListItem.NoChange )
          if self.state() != QCheckListItem.NoChange:
            self.setState( QCheckListItem.On )
      else: # NoChange
        self.setState( QCheckListItem.On )
    else:
      QCheckListItem.activate( self )

  def setState( self, s ):
    if self.type() == QCheckListItem.Controller:
      self.stateChange( s != 0 );
##      if self.parent() and self.parent().rtti() == 1 \
##         and sip.cast( self.parent(), QCheckListItem ).type() \
##         == QCheckListItem.CheckBoxController:
##        sip.cast( self.parent(), QCheckListItem ).updateController( update,
##                                                                    store )
    else:
      QCheckListItem.setState( self, s )

  def state( self ):
    if self.type() == QCheckListItem.Controller:
      if self._node._selected:
        return QCheckListItem.On
      else:
        return QCheckListItem.Off
    return QCheckListItem.state( self )

  def setOn( self, b ):
    if b:
      self.setState( QCheckListItem.On )
    else:
      self.setState( QCheckListItem.Off )

  def isOn( self ):
    if self.state() == QCheckListItem.Off:
      return False
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
    self.contextMenu = QPopupMenu()
    self.contextMenu.setCheckable( True )
    self.default_id = self.contextMenu.insertItem( _t_( 'default value' ),
                                                   self.defaultChanged )
    self.contextMenu.setItemChecked( self.default_id, True )

  def contextMenuEvent( self, e ):
    self.contextMenu.exec_loop( e.globalPos() )
    e.accept()

  def defaultChanged( self, menuId ):
    if self.contextMenu.isItemChecked( self.default_id ):
      self.contextMenu.setItemChecked( self.default_id, False )
    else:
      self.contextMenu.setItemChecked( self.default_id, True )
    self.emit( PYSIGNAL( 'toggleDefault' ), ( self.parameterName, ) )

  def setDefault( self, default ):
    self.contextMenu.setItemChecked( self.default_id, default )


#------------------------------------------------------------------------------
class ParameterizedWidget( QWidget ):
  def __init__( self, parameterized, parent ):
    debugHere()
#lock#    if getattr( ParameterizedWidget, 'pixDefault', None ) is None:
#lock#      setattr( ParameterizedWidget, 'pixDefault', QPixmap( os.path.join( neuroConfig.iconPath, 'lock.png' ) ) )
#lock#      setattr( ParameterizedWidget, 'pixCustom', QPixmap( os.path.join( neuroConfig.iconPath, 'unlock.png' ) ) )

    QWidget.__init__( self, parent )

    self.connect( self, SIGNAL( 'destroyed()' ), self.cleanup )

    layout = QVBoxLayout( self, 0, 4 )
    self.scrollWidget = WidgetScrollV( self )
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
    for k, p in self.parameterized.signature.items():
      if neuroConfig.userLevel >= p.userLevel:
        hb = QHBox( self.scrollWidget.box )
        hb.setSpacing( 4 )
        l = ParameterLabel( k, p.mandatory, hb )
        l.setDefault(self.parameterized.isDefault( k ))
        self.connect( l, PYSIGNAL( 'toggleDefault' ), self._toggleDefault )
        l.setFixedWidth( maxwidth )
        self.labels[ k ] = l
        e = p.editor( hb, k, weakref.proxy( self ) )

        self.parameterized.addParameterObserver( k, self.parameterChanged )

        self.editors[ k ] = e
        if first is None: first = e
        v = getattr( self.parameterized, k, None )
        if v is not None: 
          e.setValue( v, 1 )
        e.connect( e, PYSIGNAL('noDefault'), self.removeDefault )
        e.connect( e, PYSIGNAL('newValidValue'), self.updateParameterValue )
#lock#        btn = NamedPushButton( hb, k )
#lock#        btn.setPixmap( self.pixCustom )
#lock#        btn.setFocusPolicy( QWidget.NoFocus )
#lock#        btn.setToggleButton( 1 )
#lock#        btn.hide()
#lock#        self.connect( btn, PYSIGNAL( 'clicked' ), self._toggleDefault )
#lock#        self.btnLock[ k ] = btn

    if first: first.setFocus()
    self._doUpdateParameterValue = True

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

  def close( self, alsoDelete=False ):
    for k, p in self.parameterized.signature.items():
      try:
        self.parameterized.removeParameterObserver( k, self.parameterChanged )
      except ValueError:
        pass
    self.cleanup()
    return QWidget.close( self, alsoDelete )

  def setParameterToolTip( self, parameterName, text ):
    QToolTip.add( self.labels[ parameterName ],
                  self.parameterized.signature[ parameterName ].toolTipText( parameterName, text ) )

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
  def __init__( self, parent ):
    QLabel.__init__( self, parent )
    self.mmovie = QMovie( os.path.join( neuroConfig.iconPath, 'rotatingBrainVISA.gif' ), 1024*10 )
    self.setMovie( self.mmovie )
    #self.mmovie.setSpeed( 500 )
    #qApp.processEvents()
    self.mmovie.pause()

  def start( self ):
    self.mmovie.unpause()

  def stop( self ):
    self.mmovie.restart()
    qApp.processEvents()
    self.mmovie.pause()

#----------------------------------------------------------------------------
class ProcessView( QVBox, ExecutionContextGUI ):
  def __init__( self, processId, parent = None, externalInfo = None ):
    ExecutionContextGUI.__init__( self )
    QVBox.__init__( self, parent, None, Qt.WGroupLeader )
    if getattr( ProcessView, 'pixIcon', None ) is None:
      setattr( ProcessView, 'pixIcon', QPixmap( os.path.join( neuroConfig.iconPath, 'icon_process.png' ) ) )
      setattr( ProcessView, 'pixDefault', QPixmap( os.path.join( neuroConfig.iconPath, 'lock.png' ) ) )
      setattr( ProcessView, 'pixInProcess', QPixmap( os.path.join( neuroConfig.iconPath, 'forward.png' ) ) )
      setattr( ProcessView, 'pixProcessFinished', QPixmap( os.path.join( neuroConfig.iconPath, 'ok.png' ) ) )
      setattr( ProcessView, 'pixProcessError', QPixmap( os.path.join( neuroConfig.iconPath, 'abort.png' ) ) )
      setattr( ProcessView, 'pixNone', QPixmap() )

    self.setIcon( self.pixIcon )
    self.setMargin( 5 )
    self.setSpacing( 4 )

    self.connect( self, SIGNAL( 'destroyed()' ), self.cleanup )

    process = getProcessInstance( processId )
    if process is None:
      raise RuntimeError( HTMLMessage(_t_( 'Cannot open process <em>%s</em>' ) % ( str(processId), )) )
    self.process = process
    self.process.guiContext = weakref.proxy( self )
    self._runningProcess = 0
    self.process.signatureChangeNotifier.add( self.signatureChanged )
    self.btnRun = None
    self.btnInterruptStep=None
    self._running = False

    procdoc = readProcdoc( process )
    documentation = procdoc.get( neuroConfig.language )
    if documentation is None:
      documentation = procdoc.get( 'en', {} )

    t = _t_(process.name) + ' ' + unicode( process.instance )
    self.setCaption( t )
    hb = QHBox( self )

    self.labName = QLabel( t , hb )
    self.labName.setFrameStyle( QFrame.Panel | QFrame.Raised )
    self.labName.setLineWidth( 1 )
    self.labName.setMargin( 5 )
    self.labName.setAlignment( Qt.AlignHCenter )
    font = self.labName.font()
    font.setPointSize( QFontInfo( font ).pointSize() + 4 )
    self.labName.setFont( font )
    self.labName.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Maximum ) )
    doc =  XHTML.html( documentation.get( 'short', '' ) )
    if doc:
      QToolTip.add( self.labName, '<center><b>' + _t_(process.name) + '</b></center><hr><b>' + _t_('Description') + ':</b><br/>' + doc )

    if externalInfo is None:
      self.movie = BrainVISAAnimation( hb )
      hb.setSpacing(3)
      splitter = QSplitter( Qt.Vertical, self )
      self.parametersWidget = QVBox( splitter )
      # splitter.setResizeMode( self.parametersWidget, QSplitter.FollowSizeHint )
      splitter.setResizeMode( self.parametersWidget, QSplitter.Auto )
      container = self.parametersWidget
      self.isMainWindow = True
    else:
      self.movie = None
      splitter = None
      self.parametersWidget = self
      container = self
      self.isMainWindow = False
    self.splitter = splitter

    self._widgetStack = None
    eNode = getattr( process, '_executionNode', None )
    self._executionNodeLVItems = {}
    if eNode is not None and self.isMainWindow:
      self.parameterizedWidget = None
      vb = QVBox( container )
      eTreeWidget = QSplitter( QSplitter.Horizontal, vb )
      self.inlineGUI = self.process.inlineGUI( self.process, self, vb,
                                               externalRunButton = True )
      if self.inlineGUI is None and externalInfo is None:
        self.inlineGUI = self.defaultInlineGUI( vb )

      self.executionTree = QListView( eTreeWidget )
      self.executionTree.setSizePolicy( QSizePolicy( QSizePolicy.Preferred, QSizePolicy.Preferred ) )
      self.executionTree.addColumn( 'Name' )
      self.executionTree.setAllColumnsShowFocus( 1 )
      self.executionTree.setRootIsDecorated( 1 )
      self.executionTree.setSorting( -1 )
      eTreeWidget.setResizeMode( self.executionTree, QSplitter.KeepSize )

      # self.info must be created before ExecutionNode GUIs because they may
      # need it.
      if externalInfo is None:
        self.info = QTextEdit( splitter )
        self.info.setReadOnly( True )
        self.info.setTextFormat( Qt.RichText )
        self.info.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Preferred, 0, 50 ) )
        self.infoCounter = None
        splitter.setResizeMode( self.info, splitter.Stretch )
      else:
        self.info = externalInfo

      self._widgetStack = QWidgetStack( eTreeWidget )
      self._widgetStack._children = []
      blank = QWidget( self._widgetStack )
      self._widgetStack.addWidget( blank, -2 )

      self._guiId = 0
      self._executionNodeExpanded( self.executionTree, ( eNode, (eNode,) ) )
      self.connect( self.executionTree,
                    SIGNAL( 'expanded( QListViewItem * )' ),
                    self._executionNodeExpanded )
      
      #nodes = [ ( eNode, self.executionTree ) ]
      #previous = None
      #guiId = 0
      #while nodes:
        #n, p = nodes.pop( 0 )
        #if isinstance( n, ProcessExecutionNode ):
          #en = n._executionNode
        #else:
          #en = n
        #if getattr( n, '_radioButton', False ):
          #item = NodeCheckListItem( n, p, previous, '', QCheckListItem.RadioButton )
        #elif isinstance( en, SelectionExecutionNode ):
          #item = NodeCheckListItem( n, p, previous, '', QCheckListItem.Controller )
        #elif n._optional:
          #item = NodeCheckListItem( n, p, previous, '', QCheckListItem.CheckBox )
        #else:
          #item = QListViewItem( p, previous )
        #previous = item
        #item.setText( 0, _t_( n.name() ) )
        #gui = n.gui( self._widgetStack, processView=self )
        #if gui is not None:
          #item._guiId = guiId
          #self._widgetStack.addWidget( gui, guiId )
          #self._widgetStack._children.append( gui )
        #else:
          #item._guiId = 1000000
          #if not self._widgetStack.widget( item._guiId ):
            #self._emptyWidget = QWidget( self._widgetStack )
            #self._widgetStack.addWidget( self._emptyWidget, item._guiId )
        #children = map( lambda k,n=n,p=item: (n.child( k ), p), n.childrenNames() )
        #if isinstance( en, SelectionExecutionNode ):
          #for node in children:
            #node[0]._radioButton = True
        #nodes += children
        #guiId += 1
        ##
        #if isinstance( n, ProcessExecutionNode ):
          #self._executionNodeLVItems[ n._process ] = item
      
      self.connect( self.executionTree,
                    SIGNAL( 'selectionChanged( QListViewItem * )' ),
                    self.executionNodeSelected )
      
      # Select and open the first item
      item = self.executionTree.firstChild()
      item.setOpen( True )
      #self.executionTree.setCurrentItem( item )
      self.executionTree.setSelected( item, True )

      ##--##
      if neuroDistributedProcesses():
        self.remote = RemoteContext()

        self.remoteWidget = RemoteContextGUI(splitter)
        splitter.setResizeMode( self.remoteWidget.listView(),
          QSplitter.KeepSize )
        self.connect(self.remote, PYSIGNAL("SIG_addIP"), self.remoteWidget.addIP)
        self.connect(self.remote, PYSIGNAL("SIG_addProcess"), self.remoteWidget.addProcess)
        self.connect(self.remote, PYSIGNAL("SIG_addMessage"), self.remoteWidget.addMessage)
        self.connect(self.remote, PYSIGNAL("SIG_setProcessStatus"), self.remoteWidget.setProcessStatus)
        self.connect(self.remote, PYSIGNAL("SIG_setCurrentMessage"), self.remoteWidget.setCurrentMessage)
        self.connect(self.remote, PYSIGNAL("SIG_clear"), self.remoteWidget.clear)
      ##--##

    else:
      self.executionTree = None
      self.createSignatureWidgets( documentation )
      if externalInfo is None:
        self.info = QTextView( splitter )
        self.info.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Preferred, 0, 50 ) )
        self.infoCounter = None
        splitter.setResizeMode( self.info, splitter.Stretch )
      else:
        self.info = externalInfo

    self._iterationDialog = None

    if parent is None:
      neuroConfig.registerObject( self )
      menu = QMenuBar( self )
      addBrainVISAMenu( self, menu )
      processMenu = QPopupMenu( self )
      menu.insertItem( "&Process", processMenu )

      processMenu.insertItem( _t_( '&Save...' ), self.saveAs,  Qt.CTRL + Qt.Key_S )
      processMenu.insertItem( _t_( '&Clone...' ), self.clone,  Qt.CTRL + Qt.Key_C )

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
    signatureWidget=None
    if eNode and self.isMainWindow:
      parent = self._widgetStack
      if self.process.signature:
        signatureWidget = eNode.gui( parent, processView=self )
    else:
      parent = self.parametersWidget
      if self.process.signature:
        signatureWidget = ParameterizedWidget( self.process, parent )
      self.parameterizedWidget=signatureWidget

    if eNode is None or not self.isMainWindow:
      self.inlineGUI = self.process.inlineGUI( self.process, self, parent )
      if self.inlineGUI is None and self.isMainWindow:
        self.inlineGUI = self.defaultInlineGUI( parent )
    else:
      self._widgetStack.removeWidget( self._widgetStack._children[ 0 ] )
      self._widgetStack._children[ 0 ].close()
      self._widgetStack._children[ 0 ].deleteLater()
      if signatureWidget is not None:
        self._widgetStack.addWidget( signatureWidget, 0 )
      self._widgetStack._children[ 0 ] = signatureWidget
      self._widgetStack.raiseWidget( 0 )
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
      container = QHBox( parent )
      container.setMargin( 5 )

    if not externalRunButton:
      self.btnRun = QPushButton( _t_( 'Run' ), container )
      self.btnRun.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
      QObject.connect( self.btnRun, SIGNAL( 'clicked()' ), self._runButton )
      
      if (self.process.__class__ == neuroProcesses.IterationProcess):
        self.btnInterruptStep = QPushButton( _t_('Interrupt current step'), container )
        self.btnInterruptStep.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
        self.btnInterruptStep.setHidden(True)
        QObject.connect( self.btnInterruptStep, SIGNAL( 'clicked()' ), self._interruptStepButton )
      
    self.btnIterate = QPushButton( _t_('Iterate'), container )
    self.btnIterate.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    QObject.connect( self.btnIterate, SIGNAL( 'clicked()' ), self._iterateButton )

    if neuroDistributedProcesses():
      self.btnDistribute = QPushButton( _t_( 'Distribute' ), container )
      self.btnDistribute.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
      QObject.connect( self.btnDistribute, SIGNAL( 'clicked()' ), self._distributeButton )

    container.setSizePolicy( QSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Fixed ) )
    container.setMaximumHeight( container.sizeHint().height() )
    return container


  def getEditor( self, parameterName ):
    if self.parameterizedWidget is not None:
      return self.parameterizedWidget.editors.get( parameterName )
    return None

  def close( self, alsoDelete ):
    debugHere()
    self.cleanup()
    return QVBox.close( self, True )
  
  
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
      stack = [ self.executionTree ]
      while stack:
        item = stack.pop()
        child = item.firstChild()
        while child is not None:
          stack.append( child )
          child = child.nextSibling()
        cleanup = getattr( item, 'cleanup', None )
        if cleanup is not None:
          cleanup()
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
        showException()
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
      pp = getProcess( p )
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
        self.process = getProcessInstanceFromProcessEvent( event )
        self.process.signatureChangeNotifier.add( self.signatureChanged )
        procdoc = readProcdoc( self.process )
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
      item.setPixmap( 0, self.pixNone )
    self._lastProcessRaisedException = False
    try:
      self._startProcess( self.process, executionFunction )
      self._running = True
    except:
      self._lastProcessRaisedException = True
      showException()

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
          _mainThreadActions.push(self.btnInterruptStep.setHidden, False)
        _mainThreadActions.push( self.btnRun.setEnabled, True )
        _mainThreadActions.push( self.btnRun.setText, _t_( 'Interrupt' ) )

    #Adds an icon on the ListViewItem corresponding to the current process
    # if any
    p = self._currentProcess()
    eNodeItem = self._executionNodeLVItems.get( p )
    if eNodeItem is not None:
      _mainThreadActions.push( eNodeItem.setPixmap, 0, self.pixInProcess )

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
        _mainThreadActions.push( eNodeItem.setPixmap, 0, self.pixProcessError )
      else:
        _mainThreadActions.push( eNodeItem.setPixmap, 0,
                                 self.pixProcessFinished )

    if self._depth() == 1:
      if self.movie is not None:
        _mainThreadActions.push( self.movie.stop )
      if self.btnRun:
        _mainThreadActions.push( self.btnRun.setEnabled, True )
        _mainThreadActions.push( self.btnRun.setText, _t_( 'Run' ) )
        if self.btnInterruptStep:
          _mainThreadActions.push(self.btnInterruptStep.setHidden, True)
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

  def executionNodeSelected( self, item ):
    if item is not None:
      self._widgetStack.raiseWidget( item._guiId )
      # Trick to have correct slider
      size = self.size()
      #self.resize( size.width()+1, size.height() )
      #qApp.processEvents()
      #self.resize( size )
  
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
        if isinstance( childNode, ProcessExecutionNode ):
          en = childNode._executionNode
          if en is None:
            en = childNode
        else:
          en = childNode
        if eNode is not childNode \
          and ( isinstance( eNode, SelectionExecutionNode ) \
            or ( isinstance( eNode, ProcessExecutionNode ) \
            and isinstance( eNode._executionNode, SelectionExecutionNode ) ) ):
          newItem = NodeCheckListItem( childNode, item, previous, '', QCheckListItem.RadioButton )
        elif isinstance( en, SelectionExecutionNode ):
          newItem = NodeCheckListItem( childNode, item, previous, '', QCheckListItem.Controller )
        elif childNode._optional:
          newItem = NodeCheckListItem( childNode, item, previous, '', QCheckListItem.CheckBox )
        else:
          newItem = QListViewItem( item, previous )
        newItem._executionNode = childNode
        previous = newItem
        newItem.setText( 0, _t_( childNode.name() ) )
        newItem.setExpandable( en.hasChildren() )
        if isinstance( childNode, ProcessExecutionNode ):
          self._executionNodeLVItems[ childNode._process ] = newItem
        gui = childNode.gui( self._widgetStack, processView=self )
        if gui is not None:
          newItem._guiId = self._guiId
          self._widgetStack.addWidget( gui, newItem._guiId )
          self._widgetStack._children.append( gui )
          self._guiId += 1
        else:
          newItem._guiId = 1000000
          if not self._widgetStack.widget( newItem._guiId ):
            self._emptyWidget = QWidget( self._widgetStack )
            self._widgetStack.addWidget( self._emptyWidget, newItem._guiId )
      if self._depth():
        p = self._currentProcess()
        eNodeItem = self._executionNodeLVItems.get( p )
        if eNodeItem is not None:
          eNodeItem.setPixmap( 0, self.pixInProcess )
  
  
  def _distributeButton( self ):
    self.readUserValues()
    self._iterationDialog = IterationDialog( self, self.process, self )
    self.connect( self._iterationDialog, PYSIGNAL( 'accept' ), 
                  self._distributeAccept )
    self._iterationDialog.show()

  def _distributeAccept( self ):
    try:
      params = self._iterationDialog.getLists()
      processes = apply( self.process._iterate, (), params )
      showProcess( DistributedProcess( self.process.name, processes ) )
    except:
      showException()
      self._iterationDialog.show()

  def _iterateButton( self ):
    self.readUserValues()
    self._iterationDialog = IterationDialog( self, self.process, self )
    self.connect( self._iterationDialog, PYSIGNAL( 'accept' ),
                  self._iterateAccept )
    self._iterationDialog.show()

  def _iterateAccept( self ):
    try:
      params = self._iterationDialog.getLists()
      processes = self.process._iterate( **params )
      iterationProcess = IterationProcess( self.process.name, processes )
      showProcess( iterationProcess )
    except:
        showException()
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
    minf = unicode( QFileDialog.getSaveFileName( minf, 'BrainVISA process (*.bvproc);;All files (*)', None, None, 'Open a process file', ) )
    if minf:
      if not minf.endswith( '.bvproc' ):
        minf += '.bvproc'
      self.readUserValues()
      event = self.createProcessExecutionEvent()
      self.process._savedAs = minf
      event.save( minf )

  
  def clone( self ):
    self.readUserValues()
    clone = getProcessInstanceFromProcessEvent( self.createProcessExecutionEvent() )
    return showProcess( clone )
  

  @staticmethod
  def open():
    minf = unicode( QFileDialog.getOpenFileName( '', 'BrainVISA process (*.bvproc);;All files (*)', None, None, 'Open a process file', ))
    if minf:
      showProcess( getProcessInstance( minf ) )


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
    process = getProcessInstance( process )
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
    QDialog.__init__( self, parent, None, 0 )
    layout = QVBoxLayout( self )
    layout.setAutoAdd( 1 )
    layout.setMargin( 10 )
    self.setCaption( _t_('%s iteration') % unicode( parent.caption() ) )

    params = []
    for ( n, p ) in parameterized.signature.items():
      if neuroConfig.userLevel >= p.userLevel:
        params += [ n, ListOf( p ) ]
    self.parameterized = Parameterized( Signature( *params ) )
    for n in self.parameterized.signature.keys():
      setattr( self.parameterized, n, None )

    self.parameterizedWidget = ParameterizedWidget( self.parameterized, self )

    hb = QHBox( self )
    hb.setMargin( 5 )
    hb.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Fixed ) )
    btn = QPushButton( _t_('Ok'), hb )
    btn.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    self.connect( btn, SIGNAL( 'clicked()' ), self, SLOT( 'accept()' ) )
    btn = QPushButton( _t_('Cancel'), hb )
    btn.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    self.connect( btn, SIGNAL( 'clicked()' ), self, SLOT( 'reject()' ) )

  def polish( self ):
    desk = QDesktopWidget()
    geom = desk.screenGeometry( desk.screenNumber( self ) )
    h = geom.height() - 100
    if h < 50:
      h = 50
    if self.height() > h:
      self.resize( self.width(), h )

  def getLists( self ):
    result = {}
    for n in self.parameterized.signature.keys():
        result[ n ] = getattr( self.parameterized, n, None )
    return result

  def accept( self ):
    QDialog.accept( self )
    self.parameterizedWidget.readUserValues()
    self.emit( PYSIGNAL( 'accept' ), () )

#----------------------------------------------------------------------------

class UserDialog( QWidget ): # Ex QSemiModal
  def __init__( self, parent, modal, message, signature, buttons ):
    flags =  Qt.WType_TopLevel + Qt.WType_Dialog + Qt.WGroupLeader
    if modal: flags += Qt.WShowModal
    QWidget.__init__( self, parent, None, flags )
    layout = QVBoxLayout( self )
    layout.setAutoAdd( 1 )
    layout.setMargin( 10 )
    layout.setSpacing( 5 )

    self.condition = None
    self.signature = signature
    self._currentDirectory = None
    if message is not None:
      lab = QLabel( unicode(message), self )
      lab.setSizePolicy( QSizePolicy( QSizePolicy.Preferred, QSizePolicy.Fixed ) )

    self.editors = {}
    if signature is not None:
      sv = WidgetScrollV( self )
      first = None
      for ( k, p ) in self.signature.items():
        hb = QHBox( sv.box )
        QLabel( k + ': ', hb )
        e = p.editor( hb, k, self )
        self.editors[ k ] = e
        if first is None: first = e

    group1 = QButtonGroup( 1, Qt.Vertical, self )
    self._actions = {}
    group2 = QButtonGroup( 1, Qt.Vertical, self )
    group2.setFrameShape( QFrame.NoFrame )
    deleteGroup1 = 1
    for b in buttons:
      if type( b ) in ( types.TupleType, types.ListType ):
        caption, action = b
        btn = QPushButton( unicode( caption ), group1 )
        btn.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
        self._actions[ group1.id( btn ) ] = action
        deleteGroup1 = 0
      else:
        btn = QPushButton( unicode( b ), group2 )
        btn.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    if deleteGroup1:
      group1.close( 1 )
    else:
      group1.setSizePolicy( QSizePolicy( QSizePolicy.Minimum, QSizePolicy.Fixed ) )
      self.connect( group1, SIGNAL( 'clicked(int)' ), self._doAction )
    group2.setSizePolicy( QSizePolicy( QSizePolicy.Minimum, QSizePolicy.Fixed ) )
    self.connect( group2, SIGNAL( 'clicked(int)' ), self.done )

  def done( self, value ):
    for e in self.editors.values():
      e.checkValue()
    if self.condition is not None:
      condition = self.condition
      self.condition = None
      condition.result = value
      condition.acquire()
      condition.notify()
      condition.release()
      self.close( 1 )
    if self._exitLoop:
      self._result = value
      self._exitLoop = 0
      self.close( 1 )
      qApp.exit_loop()

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
        qApp.enter_loop()
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
    QDialog.__init__( self, None, None, 0, Qt.WGroupLeader )
    layout = QVBoxLayout( self )
    layout.setAutoAdd( 1 )
    layout.setMargin( 10 )
    layout.setSpacing( 5 )
    neuroConfig.registerObject( self )

    self.process = process
    t = _t_(process.name)
    self.setCaption( t )
    spl = QSplitter( QSplitter.Vertical, self )
    vb = QVBox( spl )
    self.labName = QLabel( '<center><h3>' + t + '</h3></center>', vb )

    hb = QHBox( vb )
    QLabel( _t_('HTML Path')+': ', hb )
    self.leHTMLPath = QLineEdit( hb )
    hb = QHBox( vb )
    QLabel( _t_('Language')+': ', hb )
    self.cmbLanguage = QComboBox( 0, hb )
    for i in neuroConfig._languages:
      self.cmbLanguage.insertItem( i )
      if i == neuroConfig.language:
        self.cmbLanguage.setCurrentItem( self.cmbLanguage.count() - 1 )
    self.connect( self.cmbLanguage, SIGNAL( 'activated(int)' ), self.changeLanguage )

    QLabel( _t_('Short description') + ':', vb )
    self.mleShort = QMultiLineEdit( vb )

    vb = QVBox( spl )
    hb = QHBox( vb )
    QLabel( _t_('Parameter')+': ', hb )
    self.cmbParameter = QComboBox( 0, hb )
    stack = QWidgetStack( vb )
    self.mleParameters = {}
    for n in self.process.signature.keys():
      mle = QMultiLineEdit( vb )
      stack.addWidget( mle, self.cmbParameter.count() )
      self.mleParameters[ self.cmbParameter.count() ] = mle
      self.cmbParameter.insertItem( n )
      self.connect( self.cmbParameter, SIGNAL( 'activated(int)' ), stack, SLOT( 'raiseWidget(int)' ) )
    stack.raiseWidget( 0 )

    vb = QVBox( spl )
    QLabel( _t_('Long description') + ':', vb )
    self.mleLong = QMultiLineEdit( vb )

    self.readDocumentation()
    self.setLanguage( unicode( self.cmbLanguage.currentText() ) )

    hb = QHBox( vb )
    hb.setMargin( 5 )
    hb.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Fixed ) )
    btn = QPushButton( _t_('apply'), hb )
    btn.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    self.connect( btn, SIGNAL( 'clicked()' ), self.applyChanges )

    btn = QPushButton( _t_('Ok'), hb )
    btn.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    self.connect( btn, SIGNAL( 'clicked()' ), self, SLOT( 'accept()' ) )

    btn = QPushButton( _t_('Cancel'), hb )
    btn.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    self.connect( btn, SIGNAL( 'clicked()' ), self, SLOT( 'reject()' ) )

    self.resize( 800, 600 )

  def close( self, alsoDelete ):
    neuroConfig.unregisterObject( self )
    return 1

  def readDocumentation( self ):
    self.documentation = readProcdoc( self.process )

  def writeDocumentation( self ):
    procdocToXHTML( self.documentation )
    self.setLanguage( self.language )
    writeProcdoc( self.process, self.documentation )

  def setLanguage( self, lang ):
    self.leHTMLPath.setText(XHTML.html(self.documentation.get( 'htmlPath', '' )) )
    self.language = lang
    d = self.documentation.get( lang, {} )
    self.mleShort.setText( XHTML.html( d.get( 'short', '' ) ) )
    self.mleLong.setText( XHTML.html( d.get( 'long', '' ) ) )
    p = d.get( 'parameters', {} )
    for i,j in self.mleParameters.items():
      j.setText( XHTML.html( p.get( unicode( self.cmbParameter.text( i ) ), '' ) ) )

  def saveLanguage( self ):
    d = {}
    d[ 'short' ] = unicode( self.mleShort.text() )
    d[ 'long' ] = unicode( self.mleLong.text() )
    d[ 'parameters' ] = p = {}
    for i,j in self.mleParameters.items():
      p[ unicode( self.cmbParameter.text( i ) ) ] = unicode( j.text() )
    self.documentation[ self.language ] = d
    htmlPath = unicode( self.leHTMLPath.text() )
    if htmlPath:
      self.documentation[ 'htmlPath' ] = htmlPath
    else:
      try:
        del self.documentation[ 'htmlPath' ]
      except KeyError:
        pass
  
  
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
class ProcessSelectionWidget( QVBox ):
  """
  This widget is the main window in brainvisa.
  Provides navigation among processes and creation of user profiles (sub group of processes).
  """

  def __init__( self ):
    QVBox.__init__( self, None, None, Qt.WGroupLeader )

    if getattr( ProcessSelectionWidget, '_pixmapCache', None ) is None:
      ProcessSelectionWidget._pixmapCache = {}
      for file in ( 'icon_process_0.png', 'icon_process_1.png', 'icon_process_2.png', 'icon_process_3.png', 'folder.png' ):
        fullPath = os.path.join( neuroConfig.iconPath, file )
        ProcessSelectionWidget._pixmapCache[ fullPath ] = QPixmap( fullPath )

    self.setMargin( 10 )
    hb = QSplitter( self )
    splitter = hb

    vb = QVBox(hb)
    self.currentProcessId = None
    self.processTrees=ProcessTreesWidget(None, vb)
    self.processTrees.setSizePolicy( QSizePolicy( QSizePolicy.Preferred,
      QSizePolicy.Preferred ) )
    QObject.connect(self.processTrees, PYSIGNAL('selectionChanged'), self.itemSelected )
    QObject.connect(self.processTrees, PYSIGNAL('doubleClicked'), self.openProcess )
    QObject.connect(self.processTrees, PYSIGNAL('openProcess'), self.openProcess )
    QObject.connect(self.processTrees, PYSIGNAL('editProcess'), self.editProcess )
    QObject.connect(self.processTrees, PYSIGNAL('iterateProcess'), self.iterateProcess )
    
    self.info = HTMLBrowser( hb )
    hb.setResizeMode( self.info, QSplitter.Stretch )
    x = hb

    hb = QHBox( self )
    hb.setSizePolicy( QSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Fixed ) )
    hb.setMargin( 5 )
    self.btnOpen = QPushButton( _t_('Open'), hb )
    self.btnOpen.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    self.btnOpen.setEnabled( 0 )
    QObject.connect( self.btnOpen, SIGNAL( 'clicked()' ), self.openProcess )
    
    if neuroConfig.userLevel >= 1:
      self.btnEdit = QPushButton( _t_('Edit'), hb )
      self.btnEdit.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
      self.btnEdit.setEnabled( 0 )
      QObject.connect( self.btnEdit, SIGNAL( 'clicked()' ), self.editProcess )
    else:
      self.btnEdit = None

    # the hacked search box
    p = os.path.join( neuroConfig.mainPath, 'qt3gui', 'searchbox.ui' )
    self.searchbox = qtui.QWidgetFactory().create(p, None, vb)
    self.searchboxSearchB = self.searchbox.child('BV_search')
    self.matchedProcs = []
    self.searchboxResetSearchB = self.searchbox.child('BV_resetsearch')
    self.searchboxLineEdit = self.searchbox.child('BV_searchlineedit')
    self._continueSearching = 0
    QObject.connect(self.searchboxSearchB, SIGNAL('clicked()'), self.buttonSearch)
    QObject.connect(self.searchboxResetSearchB, SIGNAL('clicked()'), self.resetSearch )

    # Menu setup
    menu = QMenuBar( self )
    addBrainVISAMenu( self, menu )
    neuroConfigGUI.addSupportMenu( self, menu )

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
        self.searchboxSearchB.setText('next')
      except:
        self.resetSearch()
        
  def resetSearch(self):
    """
    Called at the end of a search or when the user click on reset button.
    """
    self.matchedProcs = None
    self.searchboxSearchB.setText('search')
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
          documentation = readProcdoc( self.currentProcessId )
          source = getHTMLFileName( self.currentProcessId )
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
      item=self.processTrees.treeStack.visibleWidget().currentItem()
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
    win = ProcessEdit( getProcessInstance( processId ) )
    win.show()

  def iterateProcess( self, item=None ):
    processId=None
    if item is not None:
      if item.isLeaf():
        processId=item.id
    else:
      processId=self.currentProcessId
    self.currentProcess=getProcessInstance(processId)
    #print "iterate process", processId
    self._iterationDialog = IterationDialog( self, self.currentProcess, self )
    self.connect( self._iterationDialog, PYSIGNAL( 'accept' ),
                  self._iterateAccept )
    self._iterationDialog.show()
    
  def _iterateAccept( self ):
    """
    Call back when accepting iteration dialog. Iterates the selected process.
    """
    try:
      params = self._iterationDialog.getLists()
      processes = self.currentProcess._iterate( **params )
      iterationProcess = IterationProcess( self.currentProcess.name, processes )
      showProcess( iterationProcess )
    except:
      showException()
      self._iterationDialog.show()

  def updateList(self):
    """
    Reloads the list of process trees.
    """
    self.processTrees.setModel( neuroProcesses.updatedMainProcessTree() )

  def close( self, alsoDelete ):
    quitRequest()
    return False

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
    self.treeIndex=TreeListWidget(None, self, iconSize=(32,32))
    self.treeIndex.setSizePolicy( QSizePolicy( QSizePolicy.Preferred, QSizePolicy.Preferred ) )
    # signals
    self.connect(self.treeIndex, SIGNAL( 'selectionChanged( QListViewItem * )' ), self.setCurrentTree)
    # on clicking on a tree, emit a pysignal for transmitting the signal to the parent. The shown documentation may need to be changed. (clicked instead of selectionChanged because the documentation may need to be changed event if the item was already selected)
    self.connect(self.treeIndex, SIGNAL( 'clicked( QListViewItem * )' ), self.selectionChanged)
    self.connect(self.treeIndex, SIGNAL( 'contextMenuRequested ( QListViewItem *, const QPoint &, int )'), self.openContextMenu)
    # help tooltip
    QToolTip.add(self.treeIndex, _t_("Create your own lists of processes choosing new in contextual menu.<br>To add items in a list, open an existing list and move items in the new list.<br>If you set a list as default, it will selected the next time you run brainvisa."))

    self.treeStack=QWidgetStack(self)
    self.treeStackIdentifiers = {}
    self.treeStack.setSizePolicy( QSizePolicy( QSizePolicy.Preferred,
      QSizePolicy.Preferred ) )
    self.setResizeMode( self.treeIndex, QSplitter.FollowSizeHint )
    self.widgets=[]
    self.openedTreeWidget=None
    
    # Popup Menu for toolboxes
    self.popupMenu = QPopupMenu()
    self.popupMenu.insertItem( _t_("New"),  self.menuNewTabEvent )
    self.popupMenu.insertItem( _t_("Delete"),  self.menuDelTabEvent )
    self.popupMenu.insertItem( _t_("Open"), self.menuOpenTabEvent)
    self.popupMenu.insertItem( _t_("Set as default list"), self.menuSetDefaultEvent)
    
    # Popup Menu for processes
    self.processMenu = QPopupMenu()
    self.processMenu.insertItem( _t_("Open"),  self.menuOpenProcessEvent )
    self.processMenu.insertItem( _t_("Edit"),  self.menuEditProcessEvent )
    self.processMenu.insertItem( _t_("Iterate"), self.menuIterateProcessEvent)

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
      item=self.treeIndex.firstChild()
      found=False
      while item and not found: # search selected tree corresponding item in treeIndex widget
        if item.model==self.model.selectedTree:
          found=True
          self.treeIndex.setSelected(item, True)
        item=item.nextSibling()
    
    # Create a timer to delay model saves in minf file : it speeds up execution when there is several modification at the same time (drag&drop several elements)
    self.savesTimer=QTimer()
    self.connect(self.savesTimer, SIGNAL("timeout()"), self.model.save)

  
  def addProcessTree(self, processTree):
    """
    Add elements in the widget to add a representation of this process tree. 
    @type processTree: ProcessTree
    @param processTree: new process tree for which the widget must be completed.
    """
    treeWidget=EditableTreeWidget( processTree, self.treeStack )
    if processTree.modifiable:
      QToolTip.add(treeWidget, _t_("This list is customizable. You can :<br>- move items by drag and drop,<br>- delete item with del key,<br>- copy items by drag and drop and ctrl key,<br>- create new category with contextual menu."))
    # signals 
    # selectionChanged doesn't work with multiple selection
    # currentChanged isn't emited when click on an item that has already keyboeard focus and is not emited when click on an already selected item altought it may be necessary to update documentation because several items can be selected at the same time
    # -> so use clicked signal instead
    self.connect(treeWidget, SIGNAL( 'clicked( QListViewItem * )' ), self.selectionChanged)
    self.connect(treeWidget, SIGNAL( 'doubleClicked( QListViewItem * )' ), self.doubleClicked)
    self.connect(treeWidget, SIGNAL( 'contextMenuRequested ( QListViewItem *, const QPoint &, int )'), lambda i, p, c : self.openProcessMenu(treeWidget, i, p, c))
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
    
  def openContextMenu(self, item, point, col):
    """
    Called on contextMenuRequested signal. It opens the popup menu at cursor position.
    """
    self.popupMenu.exec_loop(QCursor.pos())

  def openProcessMenu(self, listView, item, point, col):
    """
    Called on contextMenuRequested signal on the list of processes of a toolbox. It opens the process menu at cursor position if the current item represents a process.
    """
    if item and item.model and item.model.isLeaf():
      self.processMenu.exec_loop(QCursor.pos())
    else:
      listView.openContextMenu(item, point, col)

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
      self.savesTimer.start(0, True)
    #self.model.save()

  def selectionChanged(self, item):
    """
    Called when selected item has changed in current process tree. 
    This method emits a signal that must be caught by parent widget. 
    """
    if item is not None:
      self.emit(PYSIGNAL("selectionChanged"), (item.model, ))

  def doubleClicked(self, item):
    """
    Called on double click on an item of current process tree. 
    This method emits a signal that must be caught by parent widget. 
    """
    self.emit(PYSIGNAL("doubleClicked"), (item.model, ))

  def setCurrentTree(self, item):
    """
    Changes the visible widget in the stack.
    """
    self.treeStack.raiseWidget( self.treeStackIdentifiers.get( object.__hash__( item.model ) ) )

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
      item=widget.firstChild()
      toExplore=[]
      lastSelection=None
      while item or toExplore:
        if not item:
          item=toExplore.pop(0)
        if item.isVisible():
          if item.model.isLeaf(): # for a leaf (process) search string in name
            if item.model.name.lower().find(name) > -1:
              self.select(widget, item, lastSelection)
              lastSelection=(widget, item)
              yield item
          else: # branch is put in toExplore list, it will be explored later.
            item2 = item.firstChild()
            if item2:
              toExplore.append(item2)
        item = item.nextSibling()

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
    widget.ensureItemVisible( item ) # show item (open parents...)
    widget.setSelected( item, 1 ) # select item
    if lastSelection:# undo last selection
      lastSelection[0].setSelected(lastSelection[1], 0)
 
  def selectIndex(self, model):
    """
    Select a process tree in the left panel (toolboxes).
    
    @type model : ProcessTree
    @param model: the process tree to select
    """
    item=self.treeIndex.firstChild()
    found=False
    while item and not found: # search selected tree corresponding item in treeIndex widget
      if item.model==model:
        found=True
        self.treeIndex.setSelected(item, True)
      item=item.nextSibling()

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
    item=self.treeIndex.selectedItem()
    if item:
      self.model.selectedTree=item.model

  def menuOpenProcessEvent(self):
    """
    Called on click on open option in process menu.
    Emits a signal for the parent window which will open the process.
    """
    item=self.treeStack.visibleWidget().currentItem()
    if item:
      self.emit(PYSIGNAL("openProcess"), (item.model, ))
  
  def menuEditProcessEvent(self):
    """
    Called on click on edit option in process menu.
    Emits a signal for the parent window which will edit the process.
    """
    item=self.treeStack.visibleWidget().currentItem()
    if item:
      self.emit(PYSIGNAL("editProcess"), (item.model, ))

  def menuIterateProcessEvent(self):
    """
    Called on click on iterate option in process menu.
    Emits a signal for the parent window which will iterate the process.
    """
    item=self.treeStack.visibleWidget().currentItem()
    if item:
      self.emit(PYSIGNAL("iterateProcess"), (item.model, ))

#----------------------------------------------------------------------------
class MainWindow( QWidget ):
  def __init__( self ):
    QWidget.__init__( self )
    self.myLayout = QVBoxLayout( self )
    self.mainModules = []
    self.subLayouts = []
    neuroConfig.registerObject( self )

  def close( self, alsoDelete ):
    neuroConfig.unregisterObject( self )
    return QWidget.close( self, alsoDelete )

  def addMainModule( self, identifier, name, image, description ):
    # Create main module widget
    w = QVBox( self )
    l = QLabel( _t_( name ), w )
    hb = QHBox( w )
    l = QLabel( hb )
    l.setPixmap( QPixmap( os.path.join( neuroConfig.mainPath, 'doc', 'images', image ) ) ),
    l.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    l.resize( 320, 200 )
    l = QTextEdit( hb )
    l.setText( description )
    l.setReadOnly( True )

    if ( len( self.mainModules ) % 2 == 0 ):
      self.subLayouts.append( QHBoxLayout( self.layout() ) )
    self.subLayouts[ -1 ].addWidget( w )
    w.show()
    self.mainModules.append( w )



#----------------------------------------------------------------------------
class RemoteContextGUI( QListViewItem ):
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

    remoteView = QListView(parent)
    remoteView.setSizePolicy( QSizePolicy( QSizePolicy.Expanding,
      QSizePolicy.Preferred ) )

    remoteView.setCaption('Remote messages')
    remoteView.addColumn('IP')
    remoteView.addColumn('ID')
    remoteView.addColumn('Status')
    remoteView.addColumn('Message')
    
    
    apply(QListViewItem.__init__,(self, remoteView, name ))
    #apply(RemoteContext.__init__,(self) )
    
    self.setOpen(True)
    
    self.processList = {}
    self.ipList = {}
  
  def addIP(self, ip):
    i_item = QListViewItem(self, ip)
    self.ipList[str(ip)] = i_item
    self.insertItem(i_item)
    i_item.setOpen(True)
    
  def addProcess(self, ip, pid, status=' Starting...', message=''):
    p_item = QListViewItem(self.ipList[str(ip)], 'Process', '%03d'%pid, status, message)
    self.processList[str(pid)] = p_item
    self.ipList[str(ip)].insertItem(p_item)
      
  def addMessage(self, pid, message):
    m_item = QListViewItem(self.processList[str(pid)], 'Message', '', '', message)  
    self.processList[str(pid)].insertItem(m_item)
            
  def setProcessStatus(self, pid, status):
    self.processList[str(pid)].setText(2, status)

  def setCurrentMessage(self, pid, message):
    self.processList[str(pid)].setText(3, message)

  def clear(self):
    for item in self.ipList.values():
      self.takeItem(item)
      del(item)
      
    self.processList = {}
    self.ipList = {}

  def sort(self):
    pass

  def sortChildItems(self, col, asc):
    pass

  def setup(self):
    self.setExpandable(True)
    QListViewItem.setup(self)

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
        w.raiseW()
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

