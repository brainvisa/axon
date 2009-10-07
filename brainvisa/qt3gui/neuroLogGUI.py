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

import time

import os
from backwardCompatibleQt import *
import neuroLog
import neuroException
import neuroConfig
from soma.qtgui.api import TextEditWithSearch

class LogViewer( QVBox ):

  def __init__( self, fileName, parent=None, name=None ):
    QVBox.__init__( self, parent, name )
    if getattr( LogViewer, 'pixIcon', None ) is None:
      setattr( LogViewer, 'pixIcon', QPixmap( os.path.join( neuroConfig.iconPath, 'icon_log.png' ) ) )
    self.setIcon( self.pixIcon )
    self._pixmaps = {}

    splitter = QSplitter( Qt.Horizontal, self )
    splitter.setSizePolicy( QSizePolicy( QSizePolicy.Minimum, QSizePolicy.Expanding ) )

    self._list = QListView( splitter )
    self._list.addColumn( _t_('Description') )
    self._list.addColumn( _t_('Date') )
    self._list.setSorting( -1 )
    self._list.setAllColumnsShowFocus( 1 )
    self._list.setSizePolicy( QSizePolicy( QSizePolicy.Preferred, QSizePolicy.Expanding ) )
    self._list.setRootIsDecorated( 1 )
    splitter.setResizeMode( self._list, QSplitter.KeepSize )

    self._content = TextEditWithSearch(splitter)#QTextView( splitter )
    self._content.setReadOnly(True)
    self._content.setSizePolicy( QSizePolicy( QSizePolicy.Minimum, QSizePolicy.Expanding ) )
    splitter.setResizeMode( self._content, QSplitter.Stretch )
    #self._content.setReadOnly( 1 )
    QObject.connect( self._list, SIGNAL( 'currentChanged( QListViewItem * )' ),
                     self._updateContent )

    hb = QHBox( self )
    hb.setMargin( 5 )
    btn = QPushButton( _t_( '&Refresh' ), hb )
    btn.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    QObject.connect( btn, SIGNAL( 'clicked()' ), self.refresh )
    btn = QPushButton( _t_( '&Close' ), hb )
    btn.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    QObject.connect( btn, SIGNAL( 'clicked()' ), self.close )
    btn = QPushButton( _t_( '&Open...' ), hb )
    btn.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    QObject.connect( btn, SIGNAL( 'clicked()' ), self.open )

    neuroConfig.registerObject( self )
    self.setLogFile( fileName )
    self.resize( 800, 600 )
    firstItem = self._list.firstChild()
    if firstItem:
      self._updateContent( firstItem )

  def setLogFile( self, fileName ):
    self._fileName = fileName
    self.setCaption( self._fileName )
    self.refresh()

  def close( self, alsoDelete=1 ):
    self.emit( PYSIGNAL( 'close' ), () )
    neuroConfig.unregisterObject( self )
    return QVBox.close( self, alsoDelete )

  def _addLogItem( self, item, parent, after, itemIndex, listState, currentItemIndex, currentItemList ):
    viewItem = QListViewItem( parent, after )
    viewItem.setText( 0, item.what() )
    viewItem.setText( 1, time.asctime( time.localtime( item.when() ) ) )
    if item.icon():
      pixmap = self._pixmaps.get( item.icon() )
      if pixmap is None:
        pixmap = QPixmap( os.path.join( neuroConfig.iconPath, item.icon() ) )
        self._pixmaps[ item.icon() ] = pixmap
      viewItem.setPixmap( 0, pixmap )
    content = item.html()
    if content:
      self._contents[ viewItem ] = content

    itemIndex += 1
    isOpen = 0
    if itemIndex < len( listState ):
      isOpen = listState[ itemIndex ]
      if itemIndex == currentItemIndex:
        currentItemList.append( viewItem )
 
    for child in item.children():
      ( after, itemIndex ) = self._addLogItem( child, viewItem, after, itemIndex, listState, currentItemIndex, currentItemList)
    self._list.setOpen( viewItem, isOpen )
    return ( viewItem, itemIndex )

  def _updateContent( self, item ):
    self._content.setText( unicode( self._contents.get( item, '' ) ) )


  def refresh( self ):
    try:
      reader = neuroLog.LogFileReader( self._fileName )
    except IOError:
      neuroException.showException()
      reader = None
    # Save list state
    itemIndex = -1
    currentItemIndex = -1
    listState = []
    stack = [ self._list ]
    while stack:
      currentItem = stack.pop( 0 )
      childs = []
      currentChild = currentItem.firstChild()
      while currentChild is not None:
        childs.append( currentChild )
        currentChild = currentChild.nextSibling()
      stack = childs + stack

      if currentItem is not self._list:
        itemIndex += 1
        listState.append( self._list.isOpen( currentItem ) )
        if self._list.currentItem() is currentItem:
          currentItemIndex = itemIndex
    # Erase list
    self._list.clear()
    self._contents = {}
    # Reread log and restore list state
    after=None
    currentItemList = []
    if reader is not None:
      itemIndex = -1
      item = reader.readItem()
      while item is not None:
        ( after, itemIndex ) = self._addLogItem( item, self._list, after, itemIndex, listState, currentItemIndex, currentItemList )
        item = reader.readItem()
    if currentItemList:
      self._list.setCurrentItem( currentItemList[ 0 ] )


  def open( self ):
    logFileName = unicode( QFileDialog.getOpenFileName( self._fileName, '', None, None, _t_( 'Open log file' ) ) )
    if logFileName:
      self.setLogFile( logFileName )

  def keyPressEvent( self, e ):
    if e.state() == Qt.ControlButton and e.key() == Qt.Key_W:
      e.accept()
      self.close()
    else:
      e.ignore()
      QVBox.keyPressEvent( self, e )

def showLog( fileName ):
  l = LogViewer( fileName )
  l.show()
