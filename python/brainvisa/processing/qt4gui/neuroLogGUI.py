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

from __future__ import absolute_import
import time
import os
from brainvisa.processing.qtgui.backwardCompatibleQt import QWidget, QVBoxLayout, QIcon, QSplitter, Qt, QSizePolicy, QSize, QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator, QHBoxLayout, QPushButton, QObject, QFileDialog, QKeySequence, QInputDialog, QLineEdit, qApp
from brainvisa.processing import neuroLog
from brainvisa.processing import neuroException
from brainvisa.configuration import neuroConfig
from soma.qtgui.api import TextEditWithSearch
from soma.qt_gui import qt_backend
import sys
import sip
import six

if sys.version_info[0] >= 3:
    six.text_type = str

    #def next(iterable):
        #return iterable.__next__()
#else:
    #def next(iterable):
        #return iterable.next()


class LogItemsViewer(QWidget):

    """
    Widget to visualize a list of :py:class:`neuroLog.LogFile.Item`.
    It is compound of a splitter with the list of items displayed as a QTreeWidget at the left
    and the text of the content of the selected item at the right side.
    A contextual menu is available on the content panel to search a string in the text.
    """

    def __init__(self, logitems=[], parent=None):
        QWidget.__init__(self, parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self._pixmaps = {}

        splitter = QSplitter(Qt.Horizontal)
        splitter.setSizePolicy(
            QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addWidget(splitter)

        self._list = QTreeWidget(splitter)
        self._list.setColumnCount(2)
        self._list.setHeaderLabels([_t_('Description'), _t_('Date')])
        self._list.setAllColumnsShowFocus(1)
        self._list.setIconSize(QSize(32, 32))
        self._list.setSizePolicy(
            QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding))
        self._list.setRootIsDecorated(1)

        self.searchResults = None
        self.searchText = ""

        self._content = TextEditWithSearch(splitter)  # QTextView( splitter )
        self._content.setReadOnly(True)
        self._content.setSizePolicy(
            QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding))
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        self._list.currentItemChanged.connect(self._updateContent)

        self.refresh(logitems)

        firstItem = self._list.topLevelItem(0)
        if firstItem:
            self._updateContent(firstItem)

    def refresh(self, logitems):
        # Save list state
        itemIndex = 0
        currentItemIndex = -1
        listState = []
        it = QTreeWidgetItemIterator(self._list)
        while it.value():
            currentItem = it.value()
            listState.append(currentItem.isExpanded())
            if self._list.currentItem() is currentItem:
                currentItemIndex = itemIndex
            it += 1
            itemIndex += 1
        # Erase list
        self._list.clear()
        self._contents = {}
        # Reread log and restore list state
        after = None
        currentItemList = []
        itemIndex = -1
        for item in logitems:
            (after, itemIndex) = self._addLogItem(item, self._list, after,
                                                  itemIndex, listState, currentItemIndex, currentItemList)

        if currentItemList:
            self._list.setCurrentItem(currentItemList[0])
        self._list.resizeColumnToContents(0)

    def _addLogItem(self, item, parent, after, itemIndex, listState, currentItemIndex, currentItemList):
        viewItem = QTreeWidgetItem(parent)
        if viewItem.__class__.__hash__ is None:
            viewItem.__class__.__hash__ = lambda self: sip.unwrapinstance(self)
        viewItem.setText(0, item.what())
        viewItem.setText(1, time.asctime(time.localtime(item.when())))
        if item.icon():
            pixmap = self._pixmaps.get(item.icon())
            if pixmap is None:
                pixmap = QIcon(
                    os.path.join(neuroConfig.iconPath, item.icon()))
                self._pixmaps[item.icon()] = pixmap
            viewItem.setIcon(0, pixmap)
        content = item.html()
        if content:
            self._contents[viewItem] = content

        itemIndex += 1
        isOpen = 0
        if itemIndex < len(listState):
            isOpen = listState[itemIndex]
            if itemIndex == currentItemIndex:
                currentItemList.append(viewItem)

        for child in item.children():
            (after, itemIndex) = self._addLogItem(child, viewItem, after,
                                                  itemIndex, listState, currentItemIndex, currentItemList)
        viewItem.setExpanded(isOpen)
        return (viewItem, itemIndex)

    def _updateContent(self, item):
        self._content.setText(six.text_type(self._contents.get(item, '')))

    def keyPressEvent(self, keyEvent):
        if (self._list.hasFocus()):
            if (keyEvent.matches(QKeySequence.Find)):
                (res, ok) = QInputDialog.getText(
                    self, "Find", "Text to find :", QLineEdit.Normal, self.searchText)
                if ok:
                    self.searchText = res
                if self.searchText and ok:
                    self.searchResults = self.findItem(self.searchText)
                    if (self.searchResults):
                        try:
                            item = next(self.searchResults)
                        except StopIteration:
                            item = None
            elif (keyEvent.matches(QKeySequence.FindNext)):
                if (self.searchResults is not None):
                    if (self.searchResults):
                        try:
                            item = next(self.searchResults)
                        except StopIteration:
                            item = None
                        if item is None:
                            self.searchResults.close()
                            self.searchResults = None
            else:
                QWidget.keyPressEvent(self, keyEvent)
        else:
            QWidget.keyPressEvent(self, keyEvent)

    def findItem(self, name):
        """
        Find items that contain the string given in parameters in their name. Each found item is selected and yield (and replace previous selection).
        Wide search.
        @type name: string
        @param name: string searched in items names.

        @rtype:  generator
        @return: a generator
        """
        it = QTreeWidgetItemIterator(self._list)
        lastSelection = None
        while it.value():
            item = it.value()
            if item.text(0).lower().find(name.lower()) >= 0:
                self._list.setCurrentItem(item)
                if lastSelection:
                    lastSelection.setSelected(False)
                lastSelection = item
                yield item
            it += 1
        yield None


class LogViewer(QWidget):

    """
    A viewer for a log file. The file is read and its items are displayed in a LogItemsViewer.
    Buttons are available at the bottom of the window to refresh the display,
    close the window or open a new log file.
    """

    def __init__(self, fileName, parent=None, name=None):
        QWidget.__init__(self, parent)
        if name:
            self.setObjectName(name)
        layout = QVBoxLayout()
        self.setLayout(layout)
        if getattr(LogViewer, 'pixIcon', None) is None:
            setattr(LogViewer, 'pixIcon', QIcon(
                os.path.join(neuroConfig.iconPath, 'icon_log.png')))
        self.setWindowIcon(self.pixIcon)

        self.logitems_viewer = LogItemsViewer([], self)
        layout.addWidget(self.logitems_viewer)

        hb = QHBoxLayout()
        layout.addLayout(hb)
        hb.setContentsMargins(5, 5, 5, 5)
        btn = QPushButton(_t_('&Refresh'))
        btn.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        hb.addWidget(btn)
        btn.clicked.connect(self.refresh)
        btn = QPushButton(_t_('&Close'))
        hb.addWidget(btn)
        btn.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        btn.clicked.connect(self.close)
        btn = QPushButton(_t_('&Open...'))
        hb.addWidget(btn)
        btn.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        btn.clicked.connect(self.open)

        neuroConfig.registerObject(self)
        self.setLogFile(fileName)
        ds = qApp.desktop().size()
        self.resize(min(1200, ds.width()), min(800, ds.height()))

    def setLogFile(self, fileName):
        self._fileName = fileName
        self.setWindowTitle(self._fileName)
        self.refresh()

    def closeEvent(self, event):
        neuroConfig.unregisterObject(self)
        QWidget.closeEvent(self, event)
        event.accept()

    def refresh(self):
        try:
            reader = neuroLog.LogFileReader(self._fileName)
        except IOError:
            neuroException.showException()
            reader = None

        # Reread log and restore list state
        logitems = reader.read()
        self.logitems_viewer.refresh(logitems)

    def open(self):
       # QFileDialog.getOpenFileName( QWidget * parent = 0, const QString & caption = QString(), const QString & dir = QString(), const QString & filter = QString(), QString * selectedFilter = 0, Options options = 0)
       # workaround a bug in PyQt ? Param 5 doesn't work; try to use kwargs
        import sipconfig
        if sipconfig.Configuration().sip_version >= 0x040a00:
            logFileName = six.text_type(qt_backend.getOpenFileName(
                None, _t_('Open log file'), self._fileName, '', options=QFileDialog.DontUseNativeDialog))
        else:
            logFileName = six.text_type(qt_backend.getOpenFileName(
                None, _t_('Open log file'), self._fileName, '', None, QFileDialog.DontUseNativeDialog))
        if logFileName:
            try:
                self.setLogFile(logFileName)
            except Exception:
                neuroException.showException()


def showLog(fileName):
    l = LogViewer(fileName)
    l.show()
