
from __future__ import print_function
from brainvisa.processes import *
from brainvisa.data import neuroHierarchy
from soma.wip.application.api import findIconFile
from soma.qt_gui.qtThread import MainThreadLife
import numpy as np
import os
import tempfile
import six


name = 'Database QC table'
userLevel = 2

wkhtmltopdf = findInPath('wkhtmltopdf')


signature = Signature(
    'database', Choice(),
    'data_types', ListOf(Choice('Any Type')),
    'data_filters', ListOf(String()),
    'keys', ListOf(String()),
    'type_labels', ListOf(String()),
    'output_file', WriteDiskItem('Text File', 'HTML PDF'),
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

    self.setOptional('output_file')

    self.keys = ['subject']


def execution(self, context):
    self.row_ids = {}
    self.elements = None
    # find data
    data = []
    # db = neuroHierarchy.databases.database(self.database)

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
        dfilt['_database'] = self.database
        items = list(rdi.findValues({}, requiredAttributes=dfilt))
        data.append((dtype, items))
        context.write(dtype, ':', len(items), 'items')

    nrows = max([len(values[1]) for values in data])
    ncols = len(self.data_types)
    elements = np.zeros((nrows, ncols), dtype=object)
    elements[:,:] = None

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
                    # print('warning: adding row', row, '>=', elements.shape[0])
                    # print('row_ids:', row_ids)
                    # print('row_id:', row_id)
                    old_nrow = elements.shape[0]
                    elements.resize((row + 1, ncols))
                    elements[old_nrow:,:] = None
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
        elements[old_nrow:,:] = None
    self.elements = elements
    self.row_ids = row_ids

    if self.output_file:
        self.save(context)
        # if self.output_file.format.name == 'HTML':
            # context.write(open(self.output_file.fullPath()).read())
    else:
        return mainThreadActions().call(self.exec_mainthread, context)


def get_row(self, key_vals, row_ids, key_values):
    # print('get_row for:', key_vals)
    kvals = list(key_vals)
    for i, key in enumerate(key_vals):
        kvalues = key_values[i]
        if key is None:
            if len(kvalues) != 0:
                kvals[i] = next(iter(kvalues))
        elif key not in kvalues:
            kvalues.add(key)
            # print('add value for key:', i, ':', key)

    row_id = tuple(kvals)
    # print('row_id:', row_id)
    row = row_ids.get(row_id)
    if row is not None:
        changed_id = False
        # print('existing id:', row_id)
    else:
        # print('changed id:', row_id)
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
                # print('found old row:', i, 'for id:', row_id, ':', kvals2, id)
                row = i
                row_ids[row_id] = row
                break
        if row is not None:
            # delete key with None values to avoid ambiguities with other
            # different key values which may come later
            del row_ids[id]
        else:
            if len(row_ids) == 0:
                row = 0
            else:
                row = max(row_ids.values()) + 1
            row_ids[row_id] = row
            # print('new row:', row, 'for id:', row_id)

    return row, row_id, changed_id


if neuroConfig.gui:
    from soma.qt_gui.qt_backend import Qt

    class RotatedHeaderView(Qt.QHeaderView):

        def __init__(self, orientation, parent=None):
            super(RotatedHeaderView, self).__init__(orientation, parent)
            self.setMinimumSectionSize(20)

        def paintSection(self, painter, rect, logicalIndex ):
            import sip
            if sip.isdeleted(self):
                return
            painter.save()
            # translate the painter such that rotate will rotate around the
            # correct point
            # painter.translate(rect.x()+rect.width(), rect.y())
            # painter.rotate(90)
            painter.translate(rect.x(), rect.y()+rect.height())
            painter.rotate(270)
            # and have parent code paint at this location
            newrect = Qt.QRect(0, 0, rect.height(), rect.width())
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
            return Qt.QSize(size.width(), size.height() * 0.9)


    class QActionWithViewer(Qt.QWidgetAction):

        action_triggered = Qt.Signal(QTableWidgetItem, int)
        viewer_triggered = Qt.Signal(QTableWidgetItem, int)

        def __init__(self, text, checked, item, num, parent):
            super(QActionWithViewer, self).__init__(parent)
            self._widget = None
            self._view_button = None
            self.text = text
            self._checked = checked
            self._item = item
            self.number = num

        def createWidget(self, parent):
            if self._widget is not None:
                return self._widget

            eye = Qt.QPixmap(findIconFile('eye.png')).scaledToHeight(
                20, Qt.Qt.SmoothTransformation)
            eye = Qt.QIcon(eye)
            w = Qt.QWidget(parent)
            l = Qt.QHBoxLayout()
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(5)
            w.setLayout(l)
            b = Qt.QToolButton(parent)
            b.setCheckable(True)
            b.setChecked(self._checked)
            l.addWidget(b)
            b.setIcon(eye)
            b.setSizePolicy(Qt.QSizePolicy.Fixed, Qt.QSizePolicy.Fixed)
            label = Qt.QToolButton(parent)
            label.setText(self.text)
            # label.setTextAlignment(Qt.Qt.LeftAlignment)
            l.addWidget(label)
            l.addStretch(1.)
            self._view_button = b
            self._widget = w
            label.clicked.connect(self._action_triggered)
            label.clicked.connect(self.triggered)
            b.toggled.connect(self._viewer_triggered)
            return w

        def _action_triggered(self):
            self.action_triggered.emit(self._item, self.number)

        def _viewer_triggered(self, state):
            self.viewer_triggered.emit(self._item, self.number)

        def requestWidget(self, parent):
            return self._widget


def exec_mainthread(self, context):
    from soma.qt_gui import qt_backend
    from soma.qt_gui.qt_backend import Qt
    from brainvisa.data.qt4gui.readdiskitemGUI import RightClickablePushButton
    qt5 = qt_backend.get_qt_backend() == 'PyQt5'

    mw = Qt.QMainWindow()
    wid = Qt.QWidget()
    mw.setCentralWidget(wid)
    lay = Qt.QVBoxLayout()
    wid.setLayout(lay)
    tablew = Qt.QTableWidget()
    lay.addWidget(tablew)

    eye = Qt.QIcon(findIconFile('eye.png'))
    pen = Qt.QIcon(findIconFile('pencil.png'))

    vlay = Qt.QVBoxLayout()
    lay.addLayout(vlay)
    vlay.addWidget(Qt.QLabel('Selected item:'))
    hlay = Qt.QHBoxLayout()
    vlay.addLayout(hlay)
    self.view_btn = RightClickablePushButton()
    self.view_btn.setIcon(eye)
    self.view_btn.setCheckable(True)
    hlay.addWidget(self.view_btn)
    self.edit_btn = RightClickablePushButton()
    self.edit_btn.setIcon(pen)
    self.edit_btn.setCheckable(True)
    hlay.addWidget(self.edit_btn)
    item_view = Qt.QLineEdit()
    hlay.addWidget(item_view)
    self.item_view = item_view
    item_view.setReadOnly(True)
    self.view_btn.setEnabled(False)
    self.edit_btn.setEnabled(False)
    self.current_item = None
    self._viewer = None
    self._editor = None
    self.context = context

    nrows, ncols = self.elements.shape
    nkeys = len(self.keys)

    tablew.setHorizontalHeader(RotatedHeaderView(Qt.Qt.Horizontal, tablew))

    header = tablew.horizontalHeader()
    if qt5:
        header.setSectionsClickable(True)
        header.setSectionsMovable(True)
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
    no_icon = Qt.QIcon(findIconFile('absent.png'))
    mult_icon = Qt.QIcon(findIconFile('multiple.png'))

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

    self.view_btn.toggled.connect(self.viewer_clicked)
    self.edit_btn.toggled.connect(self.editor_clicked)
    self.view_btn.rightPressed.connect(self.viewer_right_clicked)
    self.edit_btn.rightPressed.connect(self.editor_right_clicked)

    menu = Qt.QMenuBar()
    fmenu = menu.addMenu('File')
    action = fmenu.addAction('Save HTML or PDF...')
    action.triggered.connect(self.save_gui)
    mw.setMenuBar(menu)

    mw.resize(800, 800)
    mw.show()

    return MainThreadLife(mw)


def item_clicked(self, item):
    from soma.qt_gui.qt_backend import Qt

    if not self._viewer:
        self.view_btn.setEnabled(False)
    if not self._editor:
        self.edit_btn.setEnabled(False)

    if not hasattr(item, 'position'):
        # no data under this item
        self.item_view.setText('')
        self.current_item = None
        return
    row, col = item.position
    elements = self.elements[row, col]
    element = None
    if isinstance(elements, list):
        menu = Qt.QMenu()
        chosen_action = None
        try:
            eye = Qt.QIcon(findIconFile('eye.png'))
            for i, element in enumerate(elements):
                # action = menu.addAction(element.fullPath())
                # action.setCheckable(True)
                has_view = hasattr(item, 'viewer_res') \
                    and item.viewer_res[i] is not None
                # action.number = i
                # action = menu.addAction(eye, element.fullPath())
                # action.number = -i - 1
                action = QActionWithViewer(element.fullPath(), has_view, item,
                                          i, menu)
                # action.number = i
                menu.addAction(action)
                action.action_triggered.connect(self.display_item)
                action.viewer_triggered.connect(self.run_element_viewer)
                action.triggered.connect(menu.close)
            element = None
            chosen_action = menu.exec_(Qt.QCursor.pos())
        except:
            import traceback
            traceback.print_exc()
            return
        # if chosen_action is not None:
            # if chosen_action.number < 0:
                # use viewer
                # self.run_element_viewer(item, -chosen_action.number - 1)
                # element = elements[-chosen_action.number - 1]
            # else:
                # element = elements[chosen_action.number]
    else:
        element = elements

    if element is not None:
        self.item_view.setText(element.fullPath())
        self.current_item = element
        viewers = getViewers(element, process=self, check_values=True)
        if viewers:
            self.view_btn.setEnabled(True)
        editors = getDataEditors(element, process=self, check_values=True)
        if editors:
            self.edit_btn.setEnabled(True)


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


def display_item(self, item, num):
    if not self._viewer:
        self.view_btn.setEnabled(False)
    if not self._editor:
        self.edit_btn.setEnabled(False)
    if not hasattr(item, 'position'):
        # no data under this item
        return
    row, col = item.position
    elements = self.elements[row, col]
    element = None
    if isinstance(elements, list):
        element = elements[num]

    if element is not None:
        self.item_view.setText(element.fullPath())
        self.current_item = element
        viewers = getViewers(element, process=self, check_values=True)
        if viewers:
            self.view_btn.setEnabled(True)
        editors = getDataEditors(element, process=self, check_values=True)
        if editors:
            self.edit_btn.setEnabled(True)


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
            viewers = getViewers(element, process=self, check_values=True)
            for viewer in viewers:
                try:
                    viewer = getProcessInstance(viewer)
                    viewer.reference_process = self
                    res = defaultContext().runProcess(viewer, element)
                    viewer_res[num] = res
                    item.setBackground(Qt.QBrush(Qt.QColor(210, 210, 230)))
                    break
                except:
                    pass


def viewer_clicked(self, checked):
    if checked:
        element = self.current_item
        if element is None:
            return
        viewers = getViewers(element, process=self, check_values=True)
        for viewer in viewers:
            try:
                viewer = getProcessInstance(viewer)
                viewer.reference_process = self
                res = defaultContext().runProcess(viewer, element)
                self._viewer = res
                break
            except:
                pass
    else:
        self._viewer = None
        if self.current_item is None:
            self.view_btn.setEnabled(False)


def editor_clicked(self, checked):
    if checked:
        element = self.current_item
        if element is None:
            return
        editors = getDataEditors(element, process=self, check_values=True)
        for editor in editors:
            try:
                editor = getProcessInstance(editor)
                editor.reference_process = self
                import threading
                print('run editor from thread:', threading.current_thread())
                res = defaultContext().runProcess(editor, element)
                print('res:', res)
                self._editor = res
                break
            except:
                pass
    else:
        self._editor = None
        if self.current_item is None:
            self.edit_btn.setEnabled(False)


def viewer_right_clicked(self, pos):
    element = self.current_item
    if element is None:
        return
    viewers = getViewers(element, process=self, check_values=True)
    self.show_interactive_viewers(element, viewers)


def editor_right_clicked(self, pos):
    element = self.current_item
    if element is None:
        return
    viewers = getDataEditors(element, process=self, check_values=True)
    self.show_interactive_viewers(element, viewers)


def show_interactive_viewers(self, element, viewers):
    if len(viewers) != 0:
        menu = Qt.QMenu()
        for i, viewer in enumerate(viewers):
            action = Qt.QAction(viewer.name, menu)
            action.viewer = viewer
            menu.addAction(action)
            #action.triggered.connect(self.run_interactive_viewer)
        chosen_action = menu.exec_(Qt.QCursor.pos())
        del menu
        if chosen_action is not None:
            viewer = chosen_action.viewer
            try:
                viewer = getProcessInstance(viewer)
                viewer.reference_process = self
                showProcess(viewer, element)
            except:
                showException()


def save_gui(self):
    from soma.qt_gui import qt_backend
    if wkhtmltopdf is None:
        filters = 'Supported files (*.html);; HTML files (*.html)'
    else:
        filters = 'Supported files (*.html *.pdf);; HTML files (*.html);; ' \
            'PDF files (*.pdf)'
    filename = qt_backend.getSaveFileName(
        None, 'Save QC table', '', filters)
    if filename is not None and filename != '':
        try:
            self.save_file(filename)
        except:
            import traceback
            traceback.print_exc()


def save(self, context=None):
    self.save_file(self.output_file.fullPath(), context)


def save_file(self, filename, context=None):
    if filename.endswith('.html'):
        self.save_html(filename, context)
    elif filename.endswith('.pdf'):
        self.save_pdf(filename, context)
    else:
        raise('Unrecognized output format')


def save_html(self, filename, context=None):

    f = open(filename, 'w')
    f.write('''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <style type="text/css">
    div.ok { width: 16px; height: 14px;
             background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAOCAYAAAAmL5yKAAAACXBIWXMAAAsOAAALDgFAvuFBAAAAB3RJTUUH0gEQFyIZJOsyvgAAAAZiS0dEAP8A/wD/oL2nkwAAAOxJREFUKM9jYBggwATFJAPGR3/3/V/xV+8/kC0OxJxkaW57wvA/YhoDyBB1Yp2GoVnHD2yAN4qCjX/9kJ3GiCpnha65AG4ASMHmv3b/J/xlAisCCmkAMTcQM8M0195D0VwMxKFgdSAB2yKG//nHGP5P/Mv2f8pfHrBioKQWSPOivzr/a54x/A/ow9CsCbWEgUFan+G/dR7D/6wjDGADJv5l+Q/T3PWG4b9vC07NMG8y6MMMAbmk8x8D2Nkgm4nRDAK8IAlkQ0DewONsRoxogkqADbEvwxpgODVjNQSquZBYzeiGgKLRB4o18GkGAPXUpkdmxKgBAAAAAElFTkSuQmCC");
           }
    div.no { width: 15px; height: 16px;
             background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAQAgMAAAC0OM2XAAAADFBMVEVlLWeAgIDAAAD/AADpI7RpAAAAAXRSTlMAQObYZgAAAAFiS0dEAIgFHUgAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAHdElNRQfhChEICCvZr2gsAAAASklEQVQI12NggABmBgZ+BrsGBr4PryYwWK1bFcDAtmqpAwND1hSgpNUFIPFqA1DV0jVAYoomAwNfABeQcGByYOB1YAASIDMYgRgAgEcOCf2eaP8AAAAASUVORK5CYII=");
           }
    div.ml { width: 22px; height: 22px;
             background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABYAAAAWCAYAAADEtGw7AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsOAAALDgFAvuFBAAAAB3RJTUUH4QoRCBERhKMYhgAAAjpJREFUOMvtk8tLlFEYh59vLs5oaSPpJIWTxoBZYBBEuAzKdkJQ/0MoaEbLWfgXtJSgiBZBLVzo6MJLfbTJRWAwjmaOZ4bm4mViupjOaPNdTgu/Yr7JgUyX/uBszuE873nOeQ8c5YBxWOPQohhClcbDDgmcAqoPFZrpQQ51IYG2SjaOf1RUDKGahO+xJuYIC5hIABDco7ABNDpsk8+6DaDRUlRs0MmQDRoWDFQqPNTFugPAEKrJ9CAsjpPpYR04C9QATl2oppwMkYzOlEIfACtAvJKN0h1EBuvhdhtcba4CZxXJ3BbnHnFRF+qCMtpHNjHPy0V4k4KxOCEpWQaiQNoQ6iaTIdYWbIUHXGGB0uFH6iaYskhnaxUBnwtdTC0oo318S87zNArvVsHr9eCv5/TXH8VpTZcreuz1JpbNRMJu4wTI5hnZMbib18DnLhKoNSG3TDY2y+O5XWhDrQfd6eF6QLkS+WK+2IpOf1TG+snGZhleglef/kBTwLzLuvxE5DMXgA9Yr9a0McNIbBe6+tOL2+vgZJ2LzjM6oaFxVRnrt9mUQoGU0wJrQCGb5/mOQa9uQm579xRTKceTJl/1ZZ+7yK2WPDeaNTwbCZtNORQoOEtaRv8N39LozRUgLLgvJaKmzv1+O69d03STxhowvqcZXoK3mb2hgFTKP4LVZs0lzR+vPe7aKBaNhvM+GbnZCi0nbA/1F3Rf3xk4BrRf8iO7g0hgALgDtFtrSvmG/cDLbQSQ/p+THuXg+QUn/kKA+EqPswAAAABJRU5ErkJggg==");
           }
    .vert div {
        transform: rotate(-90deg);
        text-align: center;
        vertical-align: middle;
        white-space: nowrap;
        margin-bottom: -50px;
        #padding-left: 100px;
        #padding-bottom: -50px;
        #margin-right: 0px;
        #margin-left: 100px;
        position: relative;
        left: 143px;
        bottom: -80px;
        height: 300px;
        width: 24px;
    }
    table {
        border: 1px solid #99b;
        border-spacing: 0px;
        padding: 2px;
    }
    tr {
        border: none;
    }
    tbody tr:nth-child(4n) {
        background-color: #ddd;
    }
    tbody tr:nth-child(4n+3) {
        background-color: #ddd;
    }
    td {
        border-collapse: collapse;
        border: none;
        padding: 1px;
        margin: 0px;
        vertical-align: middle;
        position:relative;

        a {
            height: 100%;
            display: block;
            position: absolute;
            top:0;
            bottom:0;
            right:0;
            left:0;
          }

        .item-container {
            padding: 0px;
            margin: 0px;
            border: none;
        }
    }
    thead tr {
        background-color: #ddf;
        font-weight: bold;
    }
    .key_col:nth-child(even) {
        background-color: #f0f0f8;
    }

    .key_cell {
        padding-left: 5px;
        padding-right: 5px;
    }
  </style>
  <!-- script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js"></script>
  <script>
    $(document).ready(function() {
  $('.vert').css('height', $('.vert').width());
});
  </script -->
</head>
<body>
  <table>
    <colgroup>
''')

    nrows, ncols = self.elements.shape
    nkeys = len(self.keys)

    labels = self.keys + self.type_labels \
        + self.data_types[len(self.type_labels):]
    for label in self.keys:
        f.write('      <col class="key_col" />\n')
    for label in self.type_labels:
        f.write('      <col />\n')
    f.write('''    </colgroup>
    <thead>
      <tr>
''')
    for label in labels:
        f.write('        <td class="vert"><div>%s</div></td>\n' % label)
    f.write('''      </tr>
    </thead>
    <tbody>
''')

    row_ids = self.row_ids

    # eliminate duplicate rows by keeping most complete id for each
    rev_row_ids = {}
    for row_id, row in six.iteritems(row_ids):
        rev_row_ids.setdefault(row, []).append(row_id)
    rev_row_ids = dict([(row, max(row_id))
                        for row, row_id in six.iteritems(rev_row_ids)])

    # sort items
    rows_order = zip(*sorted(zip(rev_row_ids.values(), range(nrows))))[1]

    for row in rows_order:
        row_id = max([rid for rid in row_ids if row_ids[rid] == row])
        f.write('      <tr>\n')
        for key in row_id:
            if key is None:
                key = ''
            f.write('        <td class="key_cell">%s</td>\n' % key)

        for elem in self.elements[row]:
            if elem is None:
                f.write('        <td><div class="no" /></td>\n')
            elif isinstance(elem, list):
                f.write('        <td><div class="ml" /></td>\n')
            else:
                f.write('        <td><a href="file://%s"><div class="item-container"><div class="ok" /></div></a></td>\n' % elem)

    f.write('''    </tbody>
  </table>
</body>
</html>
''')


def save_pdf(self, filename, context=None):
    if context is not None:
        temp = context.temporary('HTML')
        temp_file = temp.fullPath()
    else:
        temp = tempfile.mkstemp(prefix='bv_', suffix='.html')
        os.close(temp[0])
        temp_file = temp[1]
    self.save_html(temp_file)
    if context is not None:
        context.system('wkhtmltopdf', temp_file, filename)
    else:
        soma.subprocess.check_call(['wkhtmltopdf', temp_file, filename])

