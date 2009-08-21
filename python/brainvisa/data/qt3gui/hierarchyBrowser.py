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
from backwardCompatibleQt import QWidget, QListView, QListViewItem, QListViewItemIterator, QPixmap, QImage, QHBoxLayout, QVBoxLayout, QVBox, QTextEdit, QSpacerItem, QSizePolicy, QPushButton, SIGNAL, qApp
import backwardCompatibleQt as qt
import os

from soma.wip.application.api import findIconFile
from soma.qtgui.api import defaultIconSize
import neuroHierarchy
import neuroDiskItems
import neuroConfig
from brainvisa.data.qt3gui.diskItemBrowser import DiskItemBrowser
from brainvisa.data.actions import FileProcess, Remove, Move
import neuroProcesses

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
      QWidget.__init__( self, None, None)#, qt.Qt.WDestructiveClose )
      if getattr( HierarchyBrowser, 'pixDirectory', None ) is None:
        setattr( HierarchyBrowser, 'pixDirectory', QPixmap( QImage(findIconFile( 'folder.png' )).smoothScale(*defaultIconSize) ) )
        setattr( HierarchyBrowser, 'pixFile', QPixmap( QImage(findIconFile( 'file.png' )).smoothScale(*defaultIconSize) ) )
        setattr( HierarchyBrowser, 'pixNew', QPixmap( QImage(findIconFile( 'filenew.png' )).smoothScale(*defaultIconSize) ) )
        setattr( HierarchyBrowser, 'pixUnknown', QPixmap( QImage(findIconFile( 'unknown.png' )).smoothScale(*defaultIconSize) ) )
        setattr( HierarchyBrowser, 'pixFind', QPixmap( QImage(findIconFile( 'database_read.png' )).smoothScale(*defaultIconSize) ) )
        setattr( HierarchyBrowser, 'pixView', QPixmap( QImage(findIconFile( 'eye.png' )).smoothScale(*defaultIconSize) ) )
        setattr( HierarchyBrowser, 'pixRemove', QPixmap( QImage(findIconFile( 'remove.png' )).smoothScale(*defaultIconSize) ) )
        setattr( HierarchyBrowser, 'pixConvert', QPixmap( QImage(findIconFile( 'converter.png' )).smoothScale(*defaultIconSize) ) )
        setattr( HierarchyBrowser, 'pixScan', QPixmap( QImage(findIconFile( 'find_read.png' )).smoothScale(*defaultIconSize) ) )
        
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
      #self.lstHierarchy.setSorting(-1)
      self.lstHierarchy.setSorting(0, True)
      # enable multiple selection
      self.lstHierarchy.setSelectionMode(QListView.Extended)
     
      self.tooltipsViewer=DiskItemToolTip( self.lstHierarchy.viewport() )
      
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
      self.connect( self.lstHierarchy, SIGNAL( 'expanded( QListViewItem * )' ), self.openItem )
      #self.connect( self.lstHierarchy, SIGNAL( 'collapsed( QListViewItem * )' ),
                    #self.closeItem )
  
      # add a right click menu to change action for a particular file
      self.popupMenu = qt.QPopupMenu()
      self.actionConditions={} # map id menuitem -> condition function(QListViewItem) : condition that all selected list view item must verify to show this menu item. 
      idView=self.popupMenu.insertItem( qt.QIconSet(self.pixView), _t_("View"),  self.menuViewEvent )
      # View menu is shown for diskitems that have a viewer
      self.actionConditions[idView]=self.viewCondition
      idHide=self.popupMenu.insertItem( qt.QIconSet(self.pixView), _t_("Hide"),  self.menuHideEvent )
      self.actionConditions[idHide]=self.hideCondition
      idRemove=self.popupMenu.insertItem( qt.QIconSet(self.pixRemove), _t_("Remove"),  self.menuRemoveEvent )
      self.actionConditions[idRemove]=self.removeCondition
      idConvert=self.popupMenu.insertItem( qt.QIconSet(self.pixConvert), _t_("Convert to graph 3.1"), self.menuConvertEvent )
      self.actionConditions[idConvert]=self.convertCondition
      self.graphConverter=neuroProcesses.getProcess("CorticalFoldsGraphUpgradeFromOld")
      self.graphType=neuroDiskItems.getDiskItemType("Graph")
      self.connect(self.lstHierarchy, qt.SIGNAL( 'contextMenuRequested ( QListViewItem *, const QPoint &, int )'), self.openContextMenu)
    
      self.resize( 800, 600 )
      self.searchResult=None
      neuroConfig.registerObject( self )
      self.lstHierarchy.clear()
      self.scanning=0 # count number of scanning items
      self.stop_scanning=False
      for db in neuroHierarchy.databases.iterDatabases():
        dbItem = QListViewItem( self.lstHierarchy )
        dbItem.database=db
        dbItem.path = db.name
        dbItem.diskItem = None
        dbItem.expand=True
        dbItem.setText( 0, db.name )
        dbItem.setPixmap( 0, self.pixDirectory )
        dbItem.setExpandable( True )
        dbItem.setDragEnabled(True)

    def openItem(self, dbItem):
      doscan = False
      try:
        if getattr(dbItem, "expand", True):
          doscan = True
          self.setCursor( qt.QCursor( qt.Qt.BusyCursor ) )
          self.scanning+=1
          dbItem.expand=False
          dbItem.setPixmap(0, self.pixScan)
          dbItem.iconTooltip=_t_("Directory scan in progress...")
          db=getattr(dbItem, "database", None)
          if db is not None:
            # scan database to fill the listview
            #print '!openItem!', dbItem.path
            gen=db.scanDatabaseDirectories( directoriesToScan=( dbItem.path,), recursion=False, includeUnknowns=True )
            for item in gen:
              #print '!openItem! -->', item
              if self.stop_scanning:
                break
              # create or retrieve items for directories in the item's path
              #path=item.relativePath()
              path=item.fullPath()
              if path.startswith( dbItem.path ):
                path = path[ len( dbItem.path ) + 1: ]
              splitted = neuroProcesses.pathsplit( path )
              #print '!openItem!   splitted =', splitted
              parentDir=dbItem
              for directory in splitted[ :-1 ]:
                dirItem=self.searchItem(parentDir, directory)
                if dirItem is None:
                  dirItem=QListViewItem(parentDir)
                  dirItem.database = parentDir.database
                  dirItem.diskItem=None
                  dirItem.path = os.path.join( parentDir.path, directory )
                  dirItem.setText(0, directory)
                  dirItem.setDragEnabled(True)
                  dirItem.setPixmap( 0, self.pixDirectory )
                  dirItem.setExpandable( True )
                parentDir=dirItem
              # now insert the item in its parent dir
              viewItem = QListViewItem( parentDir )
              viewItem.database = parentDir.database
              viewItem.diskItem = item
              viewItem.path = os.path.join( parentDir.path, splitted[ -1 ] )
              viewItem.setText( 0, splitted[ -1 ] )
              viewItem.setDragEnabled(True)
              # File or Directory
              if isinstance( item, neuroDiskItems.Directory ):
                viewItem.setPixmap( 0, self.pixDirectory )
                viewItem.setExpandable( True )
                viewItem.iconTooltip=_t_("Directory")
              else:
                if item.type is not None:
                  if db.getDiskItemFromFileName(item.fullPath(), None): # item identified and already in the database
                    viewItem.setPixmap( 0, self.pixFile )
                    viewItem.iconTooltip=_t_("Identified File in database")
                  else: # item identified but not in the database -> database should be updated
                    viewItem.setPixmap(0, self.pixNew)
                    viewItem.iconTooltip=_t_("Identified File not in database")
                else: # item not identified
                  viewItem.setPixmap( 0, self.pixUnknown )
                  viewItem.iconTooltip=_t_("Unidentified file")
                viewItem.setExpandable( False )
              qApp.processEvents()
            dbItem.setPixmap( 0, self.pixDirectory )
      finally: # can occur if the window is closed during this method execution, it is possible because it calls qApp.processEvents
        if doscan:
          self.scanning-=1
          if self.stop_scanning and  self.scanning == 0:
            # if I am the last item to process events, then destroy the
            # view, otherwise someone else will do so soon.
            self.deleteLater()
          else:
            self.unsetCursor()

    def searchItem(self, parentItem, searchedText):
      """
      Searches a QListViewItem which text is searchedText among parentItem's children
      """
      child=parentItem.firstChild()
      while child:
        if (child.text(0)==searchedText):
          break
        child=child.nextSibling()
      return child
  
    def close( self, alsoDelete=True ):
      ret=False
      if self.scanning == 0:
        neuroConfig.unregisterObject( self )
        ret= QVBox.close( self, alsoDelete )
      else:
        self.stop_scanning=True
      return ret
    
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
            # remove all files associated to this diskitem
            db=neuroHierarchy.databases.database(item.diskItem.get("_database"))
            for f in item.diskItem.existingFiles():
              self.remove(f, db)
            item.parent().takeItem(item)
    
    def remove(self, file, db=None):
      """
      If the file is a directory, recursive call to remove all its content before removing the directory.
      Corresponding diskitem is removed from the database if it exists.
      """
      if os.path.isdir(file):
        for f in os.listdir(file):
          self.remove(os.path.join(file, f), db)
        os.rmdir(file)
      else:
        os.remove(file)
      if db:
        diskItem=db.getDiskItemFromFileName(file, None)
        if diskItem:
          db.removeDiskItem(diskItem)

        
      
    def removeCondition(self, item):
      return item and item.diskItem
            
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
      self.requestDialog = DiskItemBrowser( neuroHierarchy.databases, selection={}, required={"_type" : "Any Type"} )
      self.requestDialog.setCaption( _t_( "Any Type" ) )
      self.requestDialog.connect( self.requestDialog, qt.PYSIGNAL( 'accept' ), self.requestDialogAccepted )
      self.requestDialog.show()
  
    def requestDialogAccepted(self):
      """
      Calls when the user has sent a data request. The search results are shown in the main listView.
      """
      if self.searchResult:
        self.lstHierarchy.takeItem(self.searchResult)
        del self.searchResult
      self.searchResult=SearchResultItem(self.lstHierarchy)
      sitem=None
      for item in self.requestDialog._items:
        sitem = QListViewItem( self.searchResult, sitem )
        sitem.diskItem = item
        sitem.setText( 0, os.path.basename(item.fullPath()) )
        sitem.setPixmap( 0, self.pixFile )
        #sitem.setSelected(True)
        sitem.setDragEnabled(True)
        
    def itemSelected( self, item ):
      if item is not None and item.diskItem is not None:
        t = DiskItemBrowser.diskItemDisplayText(item.diskItem)
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
  
class SearchResultItem(QListViewItem):
  def __init__(self, parent):
    super(SearchResultItem, self).__init__(parent)
    self.diskItem=None
    self.setText( 0, "-- Search result --" )
    self.setPixmap( 0, HierarchyBrowser.pixFind )
    self.setExpandable( True )
    self.setOpen(True)
    self.setSelected(True)
  
  # to have the search result always at the end of the list view
  def key(self, column, ascending):
    if ascending:
      return "z"
    return "a"

###################################
class DiskItemToolTip(qt.QToolTip):
  """
  This class enables to show a tooltip when the mouse is on action icon.
  """
  def __init__(self, parent):
    qt.QToolTip.__init__(self, parent)

  def maybeTip(self, pos):
    """Called when the mouse stay at a point of this object's parent."""
    # this object is a child of the viewport, not directly of the listview otherwise this method isn't called when the mouse is on the list content.
    viewport=self.parentWidget()
    listview=viewport.parent()
    #cursorPos=w.toContentsPoint(pos)
    currentItem=listview.itemAt(pos) #item under the mouse cursor
    if (currentItem != None) and (getattr(currentItem, "iconTooltip", None) != None) :
      rect=listview.itemRect(currentItem)
      offset=(currentItem.depth()+1)*listview.treeStepSize()
      iconRect=qt.QRect(rect.left()+offset, rect.top(), defaultIconSize[0], rect.height())
      rect.setLeft(iconRect.right())
      
      #set tooltips
      self.tip(iconRect, currentItem.iconTooltip)
      self.tip(rect, currentItem.text(0))
