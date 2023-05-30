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

'''
@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
from __future__ import print_function
from __future__ import absolute_import
__docformat__ = "restructuredtext en"


from soma.qt_gui.qt_backend.QtCore import Qt, QAbstractTableModel, QModelIndex
from soma.qt_gui.qt_backend.QtGui import QBrush
from soma.qt_gui.qt_backend import QtCore, get_qt_backend
use_qvariant = False
if get_qt_backend() == 'PyQt4':
    try:
        import sip
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
