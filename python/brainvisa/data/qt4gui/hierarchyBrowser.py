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
from __future__ import absolute_import
from soma.qt_gui.qt_backend.Qt import QWidget, QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator, QIcon, QHBoxLayout, QVBoxLayout, QTextEdit, QSpacerItem, QSizePolicy, QSize, QPushButton, qApp, QMenu, QCursor, QDrag, QPixmap, QMimeData, Qt, QMessageBox, QPoint, QApplication, QUrl, QSplitter, QBrush, QColor
import os

from soma.wip.application.api import findIconFile
from soma.qtgui.api import defaultIconSize
from brainvisa.data import neuroHierarchy, neuroDiskItems
from brainvisa.configuration import neuroConfig
from brainvisa.data.qt4gui.diskItemBrowser import DiskItemBrowser
from brainvisa.data.actions import FileProcess, Remove, Move
import brainvisa.processes
from brainvisa.processing.neuroException import showException
from brainvisa.data.qt4gui.history import DataHistoryWindow
from brainvisa.data.qt4gui import lockFilesGUI
import six


class HierarchyBrowser(QWidget):

    """
    This widget enables to explore databases, get information about stored data, search and manage data.
    Data are shown in a list view with directories and files. The contextual menu offers some actions to perform on data : remove, view/hide (with Anatomist), convert (for graphs 3.0).
    The menu items shown in the contextual menu depend on the selected item in the list view.
    To add a menu item and a condition function to show it :
    idMenu=self.popupMenu.insertItem( qt.QIconSet(...), "menu text",  <function call back>)
    self.actionConditions[idMenu]=<condition function : QListViewItem -> boolean>

    """

    def __init__(self):
        QWidget.__init__(self, None)
        if getattr(HierarchyBrowser, 'pixDirectory', None) is None:
            setattr(HierarchyBrowser, 'pixDirectory',
                    QIcon(findIconFile('folder.png')))
            setattr(HierarchyBrowser, 'pixFile',
                    QIcon(findIconFile('file.png')))
            setattr(HierarchyBrowser, 'pixNew',
                    QIcon(findIconFile('filenew.png')))
            setattr(HierarchyBrowser, 'pixUnknown',
                    QIcon(findIconFile('unknown.png')))
            setattr(HierarchyBrowser, 'pixFind',
                    QIcon(findIconFile('database_read.png')))
            setattr(HierarchyBrowser, 'pixView',
                    QIcon(findIconFile('eye.png')))
            setattr(HierarchyBrowser, 'pixRemove',
                    QIcon(findIconFile('remove.png')))
            setattr(HierarchyBrowser, 'pixConvert',
                    QIcon(findIconFile('converter.png')))
            setattr(HierarchyBrowser, 'pixScan',
                    QIcon(findIconFile('find_read.png')))
            setattr(HierarchyBrowser, 'pixHistory',
                    QIcon(findIconFile('history.png')))
            setattr(HierarchyBrowser, 'pixLock',
                    QIcon(findIconFile('lock.png')))
            setattr(HierarchyBrowser, 'pixBknDirectory',
                    QIcon(findIconFile('folder_broken.png')))

        self.setWindowTitle(_t_('Data browser'))
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)
        self.setAttribute(Qt.WA_DeleteOnClose)

        hl = QSplitter(Qt.Horizontal)
        layout.addWidget(hl)

        self.lstHierarchy = QTreeWidget()
        hl.addWidget(self.lstHierarchy)
        self.lstHierarchy.setColumnCount(1)
        self.lstHierarchy.setHeaderLabels([_t_('name')])
        self.lstHierarchy.setRootIsDecorated(True)
        self.lstHierarchy.setSortingEnabled(True)
        self.lstHierarchy.sortByColumn(0, Qt.AscendingOrder)
        self.lstHierarchy.setIconSize(QSize(*defaultIconSize))
        # enable multiple selection
        self.lstHierarchy.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.lstHierarchy.setContextMenuPolicy(
            Qt.CustomContextMenu)  # enables customContextMenuRequested signal to be emited
        self.lstHierarchy.mousePressEvent = self.mousePressEvent
        self.lstHierarchy.mouseMoveEvent = self.mouseMoveEvent
        # self.tooltipsViewer=DiskItemToolTip( self.lstHierarchy.viewport() )

        self.textEditArea = QTextEdit()
        self.textEditArea.setReadOnly(True)
        hl.addWidget(self.textEditArea)

        hl = QHBoxLayout()
        layout.addLayout(hl)
        hl.setSpacing(5)

        spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)
        hl.addItem(spacer)

        self.btnClose = QPushButton(_t_('Close'))
        hl.addWidget(self.btnClose)
        self.btnSearch = QPushButton(_t_('Search'))
        hl.addWidget(self.btnSearch)
        self.btnSearch.clicked.connect(self.search)

        self.btnClose.clicked.connect(self.close)
        self.lstHierarchy.itemClicked.connect(self.itemSelected)
        self.lstHierarchy.itemExpanded.connect(self.openItem)
        # self.lstHierarchy.collapsed.connect(self.closeItem)

        # add a right click menu to change action for a particular file
        self.popupMenu = QMenu()
        self.actionConditions = {}
            # map id menuitem -> condition function(QListViewItem) : condition
            # that all selected list view item must verify to show this menu
            # item.
        idView = self.popupMenu.addAction(
            self.pixView, _t_("View"),  self.menuViewEvent)
        # View menu is shown for diskitems that have a viewer
        self.actionConditions[idView] = self.viewCondition
        idHide = self.popupMenu.addAction(
            self.pixView, _t_("Hide"),  self.menuHideEvent)
        self.actionConditions[idHide] = self.hideCondition
        idRemove = self.popupMenu.addAction(
            self.pixRemove, _t_("Remove"),  self.menuRemoveEvent)
        self.actionConditions[idRemove] = self.removeCondition
        idConvert = self.popupMenu.addAction(
            self.pixConvert, _t_("Convert to graph 3.1"), self.menuConvertEvent)
        self.actionConditions[idConvert] = self.convertCondition
        self.graphConverter = brainvisa.processes.getProcess(
            "CorticalFoldsGraphUpgradeFromOld")
        self.graphType = neuroDiskItems.getDiskItemType("Graph")

        idHistory = self.popupMenu.addAction(
            self.pixHistory, _t_("Show history"), self.menuHistoryEvent)
        self.actionConditions[idHistory] = self.historyCondition

        idBvProc = self.popupMenu.addAction(
            self.pixView, _t_("Show bvproc"), self.menuBvProcEvent)
        self.actionConditions[idBvProc] = self.bvProcCondition

        idLockItem = self.popupMenu.addAction(self.pixLock, _t_('Lock item'),
                                              self.menuLockItem)
        self.actionConditions[idLockItem] = self.lockItemCondition
        idUnLockItem = self.popupMenu.addAction(self.pixLock,
                                                _t_('Unlock item'), self.menuUnlockItem)
        self.actionConditions[idUnLockItem] = self.unlockItemCondition
        idLockAll = self.popupMenu.addAction(self.pixLock,
                                             _t_('Lock all items'), self.menuLockAll)
        self.actionConditions[idLockAll] = self.lockAllCondition
        idUnlockAll = self.popupMenu.addAction(self.pixLock,
                                               _t_('Unlock all items'), self.menuUnlockAll)
        self.actionConditions[idUnlockAll] = self.unlockAllCondition

        self.lstHierarchy.customContextMenuRequested.connect(
            self.openContextMenu)

        self.resize(800, 600)
        self.searchResult = None
        neuroConfig.registerObject(self)
        self.lstHierarchy.clear()
        self.scanning = 0  # count number of scanning items
        self.stop_scanning = False
        self.close_on_stop = False
        self.dragStartPosition = 0

        for db in neuroHierarchy.databases.iterDatabases():
            dbItem = QTreeWidgetItem(self.lstHierarchy)
            dbItem.database = db
            dbItem.path = db.name
            dbItem.diskItem = None
            dbItem.expand = True
            dbItem.setText(0, db.name)
            dbItem.setIcon(0, self.pixDirectory)
            dbItem.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
            # dbItem.setExpandable( True )
            # dbItem.setDragEnabled(True)

    def openItem(self, dbItem):
        doscan = False
        self.close_on_stop = False
        self.stop_scanning = False
        try:
            if getattr(dbItem, "expand", True):
                doscan = True
                self.setCursor(QCursor(Qt.BusyCursor))
                self.scanning += 1
                dbItem.expand = False
                dbItem.setIcon(0, self.pixScan)
                dbItem.setToolTip(0, _t_("Directory scan in progress..."))
                db = getattr(dbItem, "database", None)
                if db is not None:
                    # scan database to fill the listview
                    gen = db.scanDatabaseDirectories(
                        directoriesToScan=(dbItem.path,), recursion=False, includeUnknowns=True)
                    for item in gen:
                        # print('!openItem! -->', item)
                        if self.stop_scanning:
                            break
                        # create or retrieve items for directories in the item's path
                        # path=item.relativePath()
                        path = item.fullPath()
                        if path.endswith('.lock'):
                            continue  # skip .lock files
                        if path.startswith(dbItem.path):
                            path = path[len(dbItem.path) + 1:]
                        splitted = brainvisa.processes.pathsplit(path)
                        # print('!openItem!   splitted =', splitted)
                        parentDir = dbItem
                        for directory in splitted[:-1]:
                            dirItem = self.searchItem(parentDir, directory)
                            if dirItem is None:
                                dirItem = QTreeWidgetItem(parentDir)
                                dirItem.database = parentDir.database
                                dirItem.diskItem = None
                                dirItem.path = os.path.join(
                                    parentDir.path, directory)
                                dirItem.setText(0, directory)
                                # dirItem.setDragEnabled(True)
                                dirItem.setIcon(0, self.pixDirectory)
                                dirItem.setChildIndicatorPolicy(
                                    QTreeWidgetItem.ShowIndicator)
                            parentDir = dirItem
                        # now insert the item in its parent dir
                        viewItem = QTreeWidgetItem(parentDir)
                        viewItem.database = parentDir.database
                        viewItem.diskItem = item
                        viewItem.path = os.path.join(
                            parentDir.path, splitted[-1])
                        text = splitted[-1]
                        viewItem.setText(0, splitted[-1])
                        if item.isLockData():
                            viewItem.setBackground(
                                0, QBrush(QColor(255, 230, 230)))
                        # viewItem.setDragEnabled(True)
                        # File or Directory
                        if isinstance(item, neuroDiskItems.Directory) or (item.type and
                           item.type.name == 'Directory') or (item.format and
                           item.format.name == 'Directory'):
                            viewItem.setIcon(0, self.pixDirectory)
                            viewItem.setChildIndicatorPolicy(
                                QTreeWidgetItem.ShowIndicator)
                            viewItem.setToolTip(
                                0, _t_("Directory") + " " + viewItem.text(0))
                        else:
                            if item.type is not None:
                                if db.getDiskItemFromFileName(item.fullPath(), None):  # item identified and already in the database
                                    viewItem.setIcon(0, self.pixFile)
                                    viewItem.setToolTip(
                                        0, _t_("Identified File in database") + " " + viewItem.text(0))
                                else:  # item identified but not in the database -> database should be updated
                                    viewItem.setIcon(0, self.pixNew)
                                    viewItem.setToolTip(
                                        0, _t_("Identified File not in database") + " " + viewItem.text(0))
                            else:  # item not identified
                                viewItem.setIcon(0, self.pixUnknown)
                                viewItem.setToolTip(
                                    0, _t_("Unidentified file") + " " + viewItem.text(0))
                            # viewItem.setExpandable( False )
                        qApp.processEvents()
                    dbItem.setIcon(0, self.pixDirectory)
                    dbItem.setToolTip(
                        0, _t_("Directory") + " " + dbItem.text(0))
        finally:  # can occur if the window is closed during this method execution, it is possible because it calls qApp.processEvents
            if doscan:
                self.scanning -= 1
                if self.stop_scanning:
                    dbItem.setIcon(0, self.pixBknDirectory)
                if self.stop_scanning and self.scanning == 0 and self.close_on_stop:
                    # if I am the last item to process events, then destroy the
                    # view, otherwise someone else will do so soon.
                    self.deleteLater()
                else:
                    self.unsetCursor()

    def searchItem(self, parentItem, searchedText):
        """
        Searches a QListViewItem which text is searchedText among parentItem's children
        """
        i = 0
        child = None
        while i < parentItem.childCount():
            child = parentItem.child(i)
            if (child.text(0) == searchedText):
                break
            i += 1
        return child

    def closeEvent(self, event):
        if self.scanning == 0:
            neuroConfig.unregisterObject(self)
            event.accept()
        else:
            self.close_on_stop = True
            self.stop_scanning = True
            event.ignore()

    def selectedItems(self):
        """
        Gets items that are currently selected in the listview (as we are in extended selection mode).

        @rtype: list of QListViewItem
        @return: items currently selected
        """
        return self.lstHierarchy.selectedItems()

    def close_viewers(self):
        it = QTreeWidgetItemIterator(self.lstHierarchy)
        while it.value():
            item = it.value()
            item.viewer = None
            it += 1

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close_on_stop = False
            self.stop_scanning = True
            event.accept()
        elif event.key() == Qt.Key_F5:
            self.refreshSelectedItems()
            event.accept()
        elif event.key() == Qt.Key_W and event.modifiers() & Qt.ControlModifier:
            self.close()
            event.accept()
        else:
            QWidget.keyPressEvent(self, event)

    def refreshSelectedItems(self):
        selected = self.selectedItems()
        for item in selected:
            if hasattr(item, 'expand') and not item.expand:
                item.expand = True
                item.takeChildren()
                self.openItem(item)
                if self.stop_scanning:
                    break  # abort requested

    # --------------------------------
    # Contextual menu functions
    # --------------------------------
    def openContextMenu(self, point):
        """
        Called on contextMenuRequested signal. It opens the popup menu at cursor position if there is an item at this position.
        Menu items visible in the contextual menu depends on the conditions verified by the selection.
        """
        # selection=self.lstHierarchy.selectedItem()
        selectedItems = self.selectedItems()
        if selectedItems:
            for action, cond in self.actionConditions.items():  # show a menu if its condition is checked for all selected items
                showMenu = True
                for selection in selectedItems:
                    if not cond(selection):
                        showMenu = False
                        break
                if showMenu:
                    action.setVisible(True)
                else:
                    action.setVisible(False)
            self.popupMenu.exec_(QCursor.pos())

    def menuRemoveEvent(self):
        """
        Callback for remove menu. Remove all the selected disk items.
        """
        if QMessageBox.warning(self, _t_("Remove"), _t_("Do you really want to remove these files ? "), QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
            items = self.selectedItems()
            for item in items:
                if item and item.diskItem:
                    try:
                        # remove all files associated to this diskitem
                        db = neuroHierarchy.databases.database(
                            item.diskItem.get("_database"))
                        for f in item.diskItem.existingFiles():
                            self.remove(f, db)
                        item.parent().takeChild(
                            item.parent().indexOfChild(item))
                    except Exception:
                        showException(
                            beforeError="Error when trying to remove " + item.diskItem.fileName())

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
            diskItem = db.getDiskItemFromFileName(file, None)
            if diskItem:
                db.removeDiskItem(diskItem)

    def removeCondition(self, item):
        return item and item.diskItem

    def menuViewEvent(self):
        items = self.selectedItems()
        for item in items:
            if item.diskItem:
                try:
                    viewer = brainvisa.processes.getViewer(item.diskItem)
                except Exception:
                    viewer = None
                if viewer:
                    try:
                        item.viewer = brainvisa.processes.defaultContext().runProcess(
                            viewer, item.diskItem)
                    except Exception:
                        showException()
                        brainvisa.processes.showProcess(viewer, item.diskItem)

    def viewCondition(self, item):
        try:
            return item and item.diskItem and not getattr(item, "viewer", None) and brainvisa.processes.getViewer(item.diskItem, checkUpdate=False)
        except Exception:
            return False

    def menuHideEvent(self):
        items = self.selectedItems()
        for item in items:
            item.viewer = None

    def hideCondition(self, item):
        return item and getattr(item, "viewer", None)

    def menuConvertEvent(self):
        items = self.selectedItems()
        for item in items:
            if item.diskItem and self.graphConverter:
                # params : Cortical folds graph, Cortex skeleton, commissure
                # coordinates, transform raw T1 MRI to
                # talairach-AC/PC-anatomist
                try:
                    brainvisa.processes.defaultContext().runProcess(
                        self.graphConverter, item.diskItem)
                except Exception as e:
                    brainvisa.processes.defaultContext().error(
                        "Error during graph conversion : " + str(e))

    def convertCondition(self, item):
        return item and item.diskItem and item.diskItem.get("graph_version", None) == "3.0" and neuroDiskItems.isSameDiskItemType(item.diskItem.type, self.graphType) and self.graphConverter

    def menuHistoryEvent(self):
        items = self.selectedItems()
        for item in items:
            if item.diskItem:
                bvproc_uuid = item.diskItem.get("lastHistoricalEvent", None)
                # print('!menuHistoryEvent : type item.diskitem ',
                # type(item.diskItem)) #<class
                # 'brainvisa.data.neuroDiskItems.File'>
                if bvproc_uuid is not None:
                    history_window = DataHistoryWindow(
                        item.diskItem, bvproc_uuid,
                                                       parent=self)
                    history_window.setAttribute(Qt.WA_DeleteOnClose)
                    history_window.show()

    def historyCondition(self, item):
        return item and item.diskItem and item.diskItem.get("lastHistoricalEvent", None) is not None

    def bvProcCondition(self, item):
        return item and item.diskItem \
            and str(item.diskItem.type) == "Process execution event"

    def menuBvProcEvent(self):
        items = self.selectedItems()
        for item in items:
            if item.diskItem:
                bvproc_uuid = item.diskItem._uuid
                if bvproc_uuid is not None:
                    history_window = DataHistoryWindow(
                        item.diskItem, bvproc_uuid, parent=self)
                    history_window.show()

    def lockItemCondition(self, item):
        return item and item.diskItem and item.diskItem.isWriteable() \
            and not item.diskItem.isLockData()

    def unlockItemCondition(self, item):
        return item and item.diskItem and item.diskItem.isWriteable() \
            and item.diskItem.isLockData()

    def lockAllCondition(self, item):
        return item and item.diskItem and item.diskItem.isWriteable() \
            and os.path.isdir(item.diskItem.fullPath())

    def unlockAllCondition(self, item):
        return item and item.diskItem and item.diskItem.isWriteable() \
            and os.path.isdir(item.diskItem.fullPath())

    def menuLockItem(self):
        items = self.selectedItems()
        for item in items:
            if item.diskItem:
                item.diskItem.lockData()
                if item.diskItem.isLockData():
                    item.setBackground(0, QBrush(QColor(255, 230, 230)))

    def menuUnlockItem(self):
        items = self.selectedItems()
        for item in items:
            if item.diskItem:
                item.diskItem.unlockData()
                if not item.diskItem.isLockData():
                    item.setBackground(0, QBrush(QColor(255, 255, 255)))

    def _updateSelectedItemsChildren(self):
        items = self.selectedItems()
        while items:
            item = items.pop()
            if item.diskItem:
                locked = item.diskItem.isLockData()
                if locked:
                    if item.background(0).color() != QColor(255, 230, 230):
                        item.setBackground(0, QBrush(QColor(255, 230, 230)))
                else:
                    if item.background(0).color() != QColor(255, 255, 255):
                        item.setBackground(0, QBrush(QColor(255, 255, 255)))
            for i in six.moves.xrange(item.childCount()):
                items.append(item.child(i))

    def _menuLockAll(self, setLock):
        items = self.selectedItems()
        ditems = []
        files = set()
        dirs = []
        if setLock:  # ensure real booleans
            setLock = True
        else:
            setLock = False
        for item in items:
            di = item.diskItem
            if di:
                f = di.fullPath()
                if di.isWriteable() and di.isLockData() != setLock \
                        and f not in files:
                    files.add(f)
                    ditems.append(di)
                if os.path.isdir(f):
                    dirs.append(f)
        while dirs:
            cdir = dirs.pop()
            for f in os.listdir(cdir):
                fname = os.path.join(cdir, f)
                try:
                    di = neuroHierarchy.databases.getDiskItemFromFileName(
                        fname)
                except Exception:
                    di = None
                if di is not None and di.isWriteable() \
                        and di.isLockData() != setLock:
                    ff = di.fullPath()
                    if ff not in files:
                        ditems.append(di)
                        files.add(ff)
                if os.path.isdir(fname):
                    dirs.append(fname)
        dialog = lockFilesGUI.LockedFilesListEditor(self, ditems, setLock)
        if dialog.exec_():
            ditems = dialog.selectedDiskItems()
            if ditems:
                if setLock:
                    print('Locking...')
                    for f in ditems:
                        try:
                            f.lockData()
                        except IOError:
                            pass  # probably not writeable
                    print('done.')
                else:
                    print('Unlocking...')
                    for f in ditems:
                        try:
                            f.unlockData()
                        except IOError:
                            pass
                    print('done.')
            self._updateSelectedItemsChildren()

    def menuLockAll(self):
        self._menuLockAll(True)

    def menuUnlockAll(self):
        self._menuLockAll(False)

    def search(self):
        """
        Opens a diskItemBrowser to set parameters to describe requested data.
        """
        self.requestDialog = DiskItemBrowser(
            neuroHierarchy.databases, selection={}, required={"_type": "Any Type"})
        self.requestDialog.setWindowTitle(_t_("Any Type"))
        self.requestDialog.accepted.connect(self.requestDialogAccepted)
        self.requestDialog.show()

    def requestDialogAccepted(self):
        """
        Calls when the user has sent a data request. The search results are shown in the main listView.
        """
        if self.searchResult:
            self.lstHierarchy.takeTopLevelItem(
                self.lstHierarchy.indexOfTopLevelItem(self.searchResult))
            del self.searchResult
        self.searchResult = SearchResultItem(self.lstHierarchy)
        sitem = None
        for item in self.requestDialog.getAllValues():
            sitem = QTreeWidgetItem(self.searchResult, sitem)
            sitem.diskItem = item
            sitem.setText(0, os.path.basename(item.fullPath()))
            sitem.setIcon(0, self.pixFile)
            # sitem.setSelected(True)
            # sitem.setDragEnabled(True)

    def itemSelected(self, item):
        # print("!hierarchyBrowser ! : itemSelected ")
        if item is not None and item.diskItem is not None:
            t = DiskItemBrowser.diskItemDisplayText(item.diskItem)
            self.textEditArea.setHtml(t)
        else:
            self.textEditArea.setText('')

    #------ Drag&Drop ------
    def mousePressEvent(self, event):
        # print("!hierarchyBrowser ! : mousePressEvent ")
        if (event.button() == Qt.LeftButton):
            self.dragStartPosition = QPoint(event.pos())
        QTreeWidget.mousePressEvent(self.lstHierarchy, event)

    def mouseMoveEvent(self, event):
        """
        The QDrag object is shown during the drag.
        This method is called when the mouse moves, this can be the beginning of a drag if the left button is clicked and the distance between the current position and the dragStartPosition is sufficient.
        The QDrag object contains as a MimeData the urls of the files associated to items dragged. This enables diskitems to be dragged in the console or in a file explorer to move, copy or link files.
        """
        if (not (event.buttons() & Qt.LeftButton)):
            return
        if ((event.pos() - self.dragStartPosition).manhattanLength()
           < QApplication.startDragDistance()):
            return

        items = self.selectedItems()
        # keep a reference to the current dragged item
        d = None
        if items != []:
            files = []
            for item in items:
                if item.diskItem:
                    for f in item.diskItem.fullPaths():
                        files.append(QUrl(f))
                    minfFile = item.diskItem.minfFileName()
                    if os.path.exists(minfFile) and minfFile != item.diskItem.fullPath():
                        files.append(QUrl(minfFile))
            d = QDrag(self)
            # icon = findIconFile( items[0].icon )
            # if icon: # adding an icon which will be visible on drag move, it will be the first item's icon
                # d.setPixmap(QPixmap(icon))
            mimeData = QMimeData()
            mimeData.setUrls(files)
            d.setMimeData(mimeData)
            dropAction = d.exec_()


class SearchResultItem(QTreeWidgetItem):

    def __init__(self, parent):
        super(SearchResultItem, self).__init__(parent)
        self.diskItem = None
        self.setText(0, "-- Search result --")
        self.setIcon(0, HierarchyBrowser.pixFind)
        # self.setExpandable( True )
        self.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
        self.setExpanded(True)
        self.setSelected(True)

    # to have the search result always at the end of the list view
    def key(self, column, ascending):
        if ascending:
            return "z"
        return "a"

#
# class DiskItemToolTip(qt.QToolTip):
    #"""
    # This class enables to show a tooltip when the mouse is on action icon.
    #"""
    # def __init__(self, parent):
        # qt.QToolTip.__init__(self, parent)

    # def maybeTip(self, pos):
        #"""Called when the mouse stay at a point of this object's parent."""
        # this object is a child of the viewport, not directly of the listview otherwise this method isn't called when the mouse is on the list content.
        # viewport=self.parentWidget()
        # listview=viewport.parent()
        # cursorPos=w.toContentsPoint(pos)
        # currentItem=listview.itemAt(pos) #item under the mouse cursor
        # if (currentItem != None) and (getattr(currentItem, "iconTooltip", None) != None) :
            # rect=listview.itemRect(currentItem)
            # offset=(currentItem.depth()+1)*listview.treeStepSize()
            # iconRect=qt.QRect(rect.left()+offset, rect.top(), defaultIconSize[0], rect.height())
            # rect.setLeft(iconRect.right())

            # set tooltips
            # self.tip(iconRect, currentItem.iconTooltip)
            # self.tip(rect, currentItem.text(0))
