
from __future__ import print_function
from brainvisa.processes import *
from brainvisa.data import neuroHierarchy
from soma.wip.application.api import findIconFile
import numpy as np
import six

name = 'Database QC table'
userLevel = 2

signature = Signature(
    'database', Choice(),
    'data_types', ListOf(Choice('Any Type')),
    'data_filters', ListOf(String()),
    'keys', ListOf(String()),
    'type_labels', ListOf(String()),
)


def initialization(self):
    # list of possible databases, while respecting the ontology
    # ontology: brainvisa-3.2.0
    databases = [h.name for h in neuroHierarchy.hierarchies()]
    self.signature["database"].setChoices(*databases)
    if len(databases) >= 2:
        self.database = databases[1]
    else:
        self.signature["database"] = OpenChoice()

    possibleTypes = [t.name for t in getAllDiskItemTypes()]
    self.signature['data_types'].contentType.setChoices(*sorted(possibleTypes))

    self.keys = ['subject']


def execution(self, context):
    self.row_ids = {}
    self.elements = None
    # find data
    data = []
    #db = neuroHierarchy.databases.database(self.database)

    for i, dtype in enumerate(self.data_types):
        if len(self.data_filters) > i or len(self.data_filters) == 1:
            ifilt = i
            if len(self.data_filters) == 1:
                # broadcast filter
                ifilt = 0
            filt = self.data_filters[ifilt]
            if filt == '':
                dfilt = {}
            else:
                dfilt = eval(filt)
        else:
            dfilt = {}
        rdi = ReadDiskItem(dtype, getAllFormats(), exactType=True)
        items = list(rdi.findValues({}, requiredAttributes=dfilt))
        data.append((dtype, items))
        context.write(dtype, ':', len(items), 'items')

    nrows = max([len(values[1]) for values in data])
    ncols = len(self.data_types)
    elements = np.zeros((nrows, ncols), dtype=object)
    elements[:, :] = None

    keys = self.keys
    key_values = []
    for i in keys:
        key_values.append(set())
    row_ids = {}
    max_row = 0

    for elem_col, (dtype, items) in enumerate(data):
        for item in items:
            key_vals = [item.get(att) for att in keys]
            row, row_id, changed_id = self.get_row(key_vals, row_ids,
                                                   key_values)
            if changed_id:
                if row >= elements.shape[0]:
                    # should not happen if get_row() had no bug...
                    #print('warning: adding row', row, '>=', elements.shape[0])
                    #print('row_ids:', row_ids)
                    #print('row_id:', row_id)
                    old_nrow = elements.shape[0]
                    elements.resize((row + 1, ncols))
                    elements[old_nrow:, :] = None
                    print(elements)
                max_row = max((max_row, row))
            element = elements[row, elem_col]
            if isinstance(element, list):
                elements[row, elem_col].append(item)
            elif element is None:
                elements[row, elem_col] = item
            else:
                elements[row, elem_col] = [element, item]

    nrows = max_row + 1
    old_nrow = elements.shape[0]
    elements.resize((nrows, ncols))
    if nrows > old_nrow:
        elements[old_nrow:, :] = None
    self.elements = elements
    self.row_ids = row_ids

    return mainThreadActions().call(self.exec_mainthread, context)


def get_row(self, key_vals, row_ids, key_values):
    #print('get_row for:', key_vals)
    kvals = list(key_vals)
    for i, key in enumerate(key_vals):
        kvalues = key_values[i]
        if key is None:
            if len(kvalues) != 0:
                kvals[i] = next(iter(kvalues))
        elif key not in kvalues:
            kvalues.add(key)
            #print('add value for key:', i, ':', key)

    row_id = tuple(kvals)
    #print('row_id:', row_id)
    row = row_ids.get(row_id)
    if row is not None:
        changed_id = False
        #print('existing id:', row_id)
    else:
        #print('changed id:', row_id)
        changed_id = True
        row = None
        for id, i in six.iteritems(row_ids):
            kvals2 = list(id)
            for j, key in enumerate(id):
                if key is None:
                    kvalues = key_values[j]
                    if len(kvalues) != 0:
                        kvals2[j] = next(iter(kvalues))

            if kvals2 == kvals:
                #print('found old row:', i)
                row = i
                row_ids[row_id] = row
                break
        if row is None:
            if len(row_ids) == 0:
                row = 0
            else:
                row = max(row_ids.values()) + 1
            row_ids[row_id] = row
            #print('new row:', row)

    return row, row_id, changed_id


if neuroConfig.gui:
    from soma.qt_gui.qt_backend import Qt

    class RotatedHeaderView(Qt.QHeaderView):

        def __init__(self, orientation, parent=None):
            super(RotatedHeaderView, self).__init__(orientation, parent)
            self.setMinimumSectionSize(20)

        def paintSection(self, painter, rect, logicalIndex ):
            painter.save()
            # translate the painter such that rotate will rotate around the
            # correct point
            #painter.translate(rect.x()+rect.width(), rect.y())
            #painter.rotate(90)
            painter.translate(rect.x(), rect.y()+rect.height())
            painter.rotate(270)
            # and have parent code paint at this location
            newrect = Qt.QRect(0,0,rect.height(),rect.width())
            super(RotatedHeaderView, self).paintSection(painter, newrect,
                                                        logicalIndex)
            painter.restore()

        def minimumSizeHint(self):
            size = super(RotatedHeaderView, self).minimumSizeHint()
            size.transpose()
            return size

        def sectionSizeFromContents(self, logicalIndex):
            size = super(RotatedHeaderView, self).sectionSizeFromContents(
                logicalIndex)
            size.transpose()
            return Qt.QSize(size.width(), size.height() * 0.8)


def exec_mainthread(self, context):
    from soma.qt_gui import qt_backend
    from soma.qt_gui.qt_backend import Qt
    qt5 = qt_backend.get_qt_backend() == 'PyQt5'

    wid = Qt.QWidget()
    lay = Qt.QVBoxLayout()
    wid.setLayout(lay)
    tablew = Qt.QTableWidget()
    lay.addWidget(tablew)

    vlay = Qt.QVBoxLayout()
    lay.addLayout(vlay)
    vlay.addWidget(Qt.QLabel('Selected item:'))
    item_view = Qt.QLineEdit()
    vlay.addWidget(item_view)
    self.item_view = item_view
    item_view.setReadOnly(True)

    nrows, ncols = self.elements.shape
    nkeys = len(self.keys)

    tablew.setHorizontalHeader(RotatedHeaderView(Qt.Qt.Horizontal, tablew))

    header = tablew.horizontalHeader()
    if qt5:
        header.setSectionsClickable(True)
    else:
        header.setClickable(True)
    header.setMovable(True)

    tablew.setColumnCount(ncols + nkeys)
    header.setDefaultSectionSize(32)
    header.setDefaultAlignment(Qt.Qt.AlignLeft)
    labels = self.keys + self.type_labels \
        + self.data_types[len(self.type_labels):]
    tablew.setHorizontalHeaderLabels(labels)
    tablew.setSortingEnabled(True)
    tablew.setEditTriggers(tablew.NoEditTriggers)

    tablew.setRowCount(nrows)

    ok_icon = Qt.QIcon(findIconFile('ok.png'))
    no_icon = Qt.QIcon(findIconFile('abort.png'))
    mult_icon = Qt.QIcon(findIconFile('help.png'))

    row_ids = self.row_ids

    for row_id, row in six.iteritems(row_ids):
        for c, key in enumerate(row_id):
            if key is not None:
                tablew.setItem(row, c, Qt.QTableWidgetItem(key))

    for col in range(ncols):
        for row in range(nrows):
            elem = self.elements[row, col]
            if elem is None:
                titem = Qt.QTableWidgetItem(no_icon, '')
            elif isinstance(elem, list):
                titem = Qt.QTableWidgetItem(mult_icon, '')
                titem.position = (row, col)
            else:
                titem = Qt.QTableWidgetItem(ok_icon, '')
                titem.position = (row, col)
            tablew.setItem(row, col + nkeys, titem)

    tablew.itemClicked.connect(self.item_clicked)
    tablew.itemDoubleClicked.connect(self.item_double_clicked)

    tablew.sortByColumn(0, Qt.Qt.AscendingOrder)
    for col in range(nkeys):
        tablew.resizeColumnToContents(col)
    wid.resize(800, 800)
    wid.show()

    return [wid]


def item_clicked(self, item):
    from soma.qt_gui.qt_backend import Qt

    if not hasattr(item, 'position'):
        # no data under this item
        self.item_view.setText('')
        return
    row, col = item.position
    elements = self.elements[row, col]
    element = None
    if isinstance(elements, list):
        menu = Qt.QMenu()
        eye = Qt.QIcon(findIconFile('eye.png'))
        for i, element in enumerate(elements):
            action = menu.addAction(element.fullPath())
            action.number = i
            action = menu.addAction(eye, element.fullPath())
            action.number = -i - 1
        element = None
        action = menu.exec_(Qt.QCursor.pos())
        if action is not None:
            if action.number < 0:
                # use viewer
                self.run_element_viewer(item, -action.number - 1)
                element = elements[-action.number - 1]
            else:
                element = elements[action.number]
    else:
        element = elements

    if element is not None:
        self.item_view.setText(element.fullPath())


def item_double_clicked(self, item):
    from soma.qt_gui.qt_backend import Qt

    if not hasattr(item, 'position'):
        # no data under this item
        return
    row, col = item.position
    elements = self.elements[row, col]
    element = None
    if isinstance(elements, list):
        element = elements[0]
    else:
        element = elements

    if element is not None:
        self.run_element_viewer(item)


def run_element_viewer(self, item, num=0):
    if not hasattr(item, 'position'):
        # no data under this item
        return
    row, col = item.position
    elements = self.elements[row, col]
    element = None
    if isinstance(elements, list):
        element = elements[num]
        if not hasattr(item, 'viewer_res'):
            item.viewer_res = [None] * len(elements)
        viewer_res = item.viewer_res
    else:
        element = elements
        if not hasattr(item, 'viewer_res'):
            item.viewer_res = [None]
        viewer_res = item.viewer_res
        num = 0
    if element is not None:
        if viewer_res[num] is not None:
            viewer_res[num] = None
            if not any(viewer_res):
                item.setBackground(Qt.QBrush(Qt.QColor(255, 255, 255)))
        else:
            viewers = getViewers(element)
            for viewer in viewers:
                try:
                    res = defaultContext().runProcess(viewer, element)
                    viewer_res[num] = res
                    item.setBackground(Qt.QBrush(Qt.QColor(210, 210, 230)))
                    break
                except:
                    pass
