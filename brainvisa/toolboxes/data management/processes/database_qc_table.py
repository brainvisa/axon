
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
    # find data
    data = {}
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
        data[dtype] = list(rdi.findValues({}, requiredAttributes=dfilt))
        context.write(dtype, ':', len(list(data[dtype])), 'items')

    nrows = max([len(values) for values in data.values()])
    ncols = len(self.data_types)
    elements = np.zeros((nrows, ncols), dtype=object)
    elements[:, :] = None

    cols = {}
    keys = self.keys
    for i, dtype in enumerate(self.data_types):
        cols[dtype] = i
    key_values = []
    for i in keys:
        key_values.append(set())
    row_ids = {}
    max_row = 0

    for dtype, items in six.iteritems(data):
        elem_col = cols[dtype]
        col = elem_col + len(keys)
        for item in items:
            key_vals = [item.get(att) for att in keys]
            row, row_id, changed_id = self.get_row(key_vals, row_ids,
                                                   key_values)
            if changed_id:
                max_row = max((max_row, row))
            element = elements[row, elem_col]
            if isinstance(element, list):
                elements[row, elem_col].append(item)
            elif element is None:
                elements[row, elem_col] = item
            else:
                elements[row, elem_col] = [element, item]

    nrows = max_row + 1
    elements.resize((nrows, ncols))
    self.elements = elements
    self.row_ids = row_ids

    return mainThreadActions().call(self.exec_mainthread, context)


def get_row(self, key_vals, row_ids, key_values):
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
    row = row_ids.get(row_id)
    if row is not None:
        changed_id = False
        #print('existing id:', row_id)
    else:
        #print('changed id:', row_id)
        changed_id = True
        row = -1
        for id, i in six.iteritems(row_ids):
            kvals2 = list(id)
            for i, key in enumerate(id):
                if key is None:
                    kvalues = key_values[i]
                    if len(kvalues) != 0:
                        kvals2[i] = next(iter(kvalues))

            if kvals2 == kvals:
                row = i
                break
        if row < 0:
            row = len(row_ids)
            row_ids[row_id] = row

    return row, row_id, changed_id


def exec_mainthread(self, context):
    from soma.qt_gui.qt_backend import Qt

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

    tablew.setColumnCount(ncols + nkeys)
    tablew.setHorizontalHeaderLabels(self.keys + self.data_types)
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
    tablew.resizeColumnToContents(0)
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
            element = elements[abs(action.number)]
            if action.number < 0:
                # use viewer
                self.run_element_viewer(item, -action.number - 1)
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
        else:
            viewers = getViewers(element)
            for viewer in viewers:
                try:
                    res = defaultContext().runProcess(viewer, element)
                    viewer_res[num] = res
                    break
                except:
                    pass
