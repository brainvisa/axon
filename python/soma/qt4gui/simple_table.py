# -*- coding: utf-8 -*-

__docformat__ = "restructuredtext en"


from soma.qt_gui.qt_backend.QtCore import Qt, QAbstractTableModel, QModelIndex
from soma.qt_gui.qt_backend.QtGui import QBrush
from soma.qt_gui.qt_backend import QtCore, get_qt_backend
use_qvariant = False
if get_qt_backend() == 'PyQt4':
    try:
        from soma.qt_gui.qt_backend import sip
        use_qvariant = sip.getapi('QVariant') < 2
        if use_qvariant:
            from soma.qt_gui.qt_backend.QtCore import QVariant
    except Exception:
        pass  # PySide doesn't have QVariant at all.
import operator


class SimpleTable(QAbstractTableModel):

    '''
    A simple read-only table model allowing to display data with
    soma.qt_gui.qt_backend.QtGui.QTableView

    Example
    -------
      from soma.qt_gui.qt_backend.uic import loadUi
      from soma.qt_gui.qt_backend.QtGui import QWidget
      from soma.qt4gui.api import SimpleTable

      def clicked( index ):
        global m
        print('Selected', m.row( index.row() )[ index.column() ], 'in', m.row( index.row() ))

      m = SimpleTable( ( 'a', 'b', 'c' ), ( ( 1, 2, 3 ), ( 4, 5, 6 ) ) )
      w = QWidget()
      loadUi( '/tmp/test.ui', w )
      w.tableView.setModel( m )
      w.tableView.clicked.connect(clicked)
      w.show()
    '''

    def __init__(self, header, data=(), parent=None):
        '''header = series of unicode
        '''
        QAbstractTableModel.__init__(self, parent)
        self._header = tuple(header)
        self._data = []
        self._background = {}
        for row in data:
            self.addRow(row)

    def addRow(self, row):
        parent = QModelIndex()
        index = len(self._data)
        self.beginInsertRows(parent, index, index)
        self._data.append(tuple(row) + (index, ))
        self.endInsertRows()

    def clear(self):
        parent = QModelIndex()
        last = len(self._data) - 1
        self.beginRemoveRows(parent, 0, last)
        # Remove all elements from self._data
        self._data[:] = []
        self._background = {}
        self.endRemoveRows()

    def setRow(self, index, row):
        self._data[index] = tuple(row) + (self._data[index][-1], )
        self.dataChanged.emit(
            self.createIndex(index, 0), self.createIndex(index, len(row) - 1))

    def row(self, index):
        return self._data[index][:-1]

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        return len(self._header)

    def setRowBackgroundColor(self, index, color):
        if color is None:
            self._background.pop(index, None)
        else:
            self._background[index] = color
        self.dataChanged.emit(
            self.createIndex(index, 0), self.createIndex(index, len(self._data[index]) - 2))

    def data(self, index, role=Qt.DisplayRole):
        if use_qvariant:
            result = QVariant()
        else:
            result = None
        if index.isValid():
            if role == Qt.DisplayRole:
                value = self._data[index.row()][index.column()]
                if value is not None:
                    if use_qvariant:
                        result = QVariant(value)
                    else:
                        result = value
            elif role == Qt.BackgroundRole:
                background = self._background.get(index.row())
                if background is not None:
                    if use_qvariant:
                        result = QVariant(QBrush(background))
                    else:
                        result = QBrush(background)
        return result

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if use_qvariant:
                return QVariant(self._header[col])
            else:
                return self._header[col]
        if use_qvariant:
            return QVariant()
        else:
            return None

    def sort(self, column, order):
        """Sort table by given column number.
        """
        class str_itemgetter:
            def __init__(self, col):
                self.col = col
            def __call__(self, l):
                item = l[self.col]
                if item is None:
                    return ''
                return item

        self.layoutAboutToBeChanged.emit()
        self._data.sort(key=str_itemgetter( #operator.itemgetter(
            column), reverse=(order == Qt.DescendingOrder))
        self.layoutChanged.emit()

    def sortedIndex(self, index):
        return self._data[index][-1]
