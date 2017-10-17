
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
    'output_file', WriteDiskItem('Text File', ['HTML', 'PDF file']),
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
        dfilt['_database'] = self.database
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

    if self.output_file:
        self.save(context)
    else:
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
            label = Qt.QToolButton(parent)
            label.setText(self.text)
            l.addWidget(label)
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
            print('requestWidget')
            return self._widget


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
        chosen_action = None
        try:
            eye = Qt.QIcon(findIconFile('eye.png'))
            for i, element in enumerate(elements):
                #action = menu.addAction(element.fullPath())
                #action.setCheckable(True)
                has_view = hasattr(item, 'viewer_res') \
                    and item.viewer_res[i] is not None
                #action.number = i
                #action = menu.addAction(eye, element.fullPath())
                #action.number = -i - 1
                action = QActionWithViewer(element.fullPath(), has_view, item,
                                          i, menu)
                #action.number = i
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
        #if chosen_action is not None:
            #if chosen_action.number < 0:
                ## use viewer
                #self.run_element_viewer(item, -chosen_action.number - 1)
                #element = elements[-chosen_action.number - 1]
            #else:
                #element = elements[chosen_action.number]
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


def display_item(self, item, num):
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


def save(self, context):
    context.write('output format:', self.output_file.format)
    if self.output_file.format.name == 'HTML':
        self.save_html(context)
    elif self.output_file.format.name == 'PDF File':
        self.save_pdf(context)
    else:
        raise('Unrecognized output format')


def save_html(self, context):

    f = open(self.output_file.fullPath(), 'w')
    f.write('''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <style type="text/css">
    div.ok { width: 16px; height: 14px;
             background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAOCAYAAAAmL5yKAAAACXBIWXMAAAsOAAALDgFAvuFBAAAAB3RJTUUH0gEQFyIZJOsyvgAAAAZiS0dEAP8A/wD/oL2nkwAAAOxJREFUKM9jYBggwATFJAPGR3/3/V/xV+8/kC0OxJxkaW57wvA/YhoDyBB1Yp2GoVnHD2yAN4qCjX/9kJ3GiCpnha65AG4ASMHmv3b/J/xlAisCCmkAMTcQM8M0195D0VwMxKFgdSAB2yKG//nHGP5P/Mv2f8pfHrBioKQWSPOivzr/a54x/A/ow9CsCbWEgUFan+G/dR7D/6wjDGADJv5l+Q/T3PWG4b9vC07NMG8y6MMMAbmk8x8D2Nkgm4nRDAK8IAlkQ0DewONsRoxogkqADbEvwxpgODVjNQSquZBYzeiGgKLRB4o18GkGAPXUpkdmxKgBAAAAAElFTkSuQmCC");
           }
    div.no { width: 22px; height: 22px;
             background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABYAAAAWAgMAAAC52oSoAAAADFBMVEUAAACAgIDAAAD/AAAn4XKoAAAAAXRSTlMAQObYZgAAAFVJREFUeF6FyLENQFAYReH7QiMRA5jAABRC8Y/wlmMCjVupVRLbsMGruH8vTvMlBz+VYkQSw0l7ufZV1Jw0A6PAbSLjIap5c+IiemscFKJDEC28HF890u0OS04UwuwAAAAASUVORK5CYII=");
           }
    div.ml { width: 22px; height: 22px;
             background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABYAAAAWCAYAAADEtGw7AAAABGdBTUEAALGPC/xhBQAAAAlwSFlzAAALEgAACxIB0t1+/AAAAAd0SU1FB9EBBg0gDndZibAAAAAGYktHRAAAAAAAAPlDu38AAAHfSURBVDjL1ZXLLythGMbHpVVNpVS1wwSdjl50VKczoxckxIpENCJsLCyI+8mRHukJKxuXJkVELM4hVhZEbC2wsFBx2UhsJedPeY75EhJp0pkyG8/6e37v973v8+ajqPyCvyUErkUE4xPgaAqihg2gkuFQXl0H6hOCtcqG7asX9C/tg2/rhKs1DiYQQa1fRPPAJPjhlAKG0cZoLoCD7D8M/30A7W+DwWTOMRaVGtGb3IU8uQqb2EcKqFIbOS+B8olZNQOBC4snmsDYPH9Cd/IPzLWc6mEuKCO+fgN+egsWTzTveXJbcXwVBqtDFdzg9iCxewdhbg8Wbzw/uGs+g9CPAwQGZmC106i0O6F2EXl6B+WMX70dnrENhJeP0ZG+Rs/aJWyu5hxTONJOUiOmTrUN7w3ODibJE6WfhzlGQY6S5ETXL9A09AsmJ1tQpgnQzIY+mKRIjECl9C3YxDyM9vpPLcoH8SGRQOXMPbwjv1HmcH0dGhRE0tPY1iO4ocWCNi5vWxSokgApdVTQsFTBC0dZyOksfKMrKDZV6AeOvw4rOJUB3TMOqrhEN/B7Sspot67Qbyh3uAO0T0KFs0G/VtTzMpJnzyRuSo6pEoM+cAvNEmBsooAfQ6uUTTNU1WnO8H/WKe+4kZpEygAAAABJRU5ErkJggg==");
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
    tr:nth-child(even) {
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
      background-color: #ccf;
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
    <thead>
      <tr>
''')

    nrows, ncols = self.elements.shape
    nkeys = len(self.keys)

    labels = self.keys + self.type_labels \
        + self.data_types[len(self.type_labels):]
    for label in labels:
        f.write('        <td class="vert"><div>%s</div></td>\n' % label)
    f.write('''      </tr>
    </thead>
    <tbody>
''')

    row_ids = self.row_ids

    # sort items
    rows_order = zip(*sorted(zip(row_ids.keys(), range(nrows))))[1]

    for row in rows_order:
        row_id = max([rid for rid in row_ids if row_ids[rid] == row])
        f.write('      <tr>\n')
        for key in row_id:
            if key is None:
                key = ''
            f.write('        <td>%s</td>\n' % key)

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


def save_pdf(self, context):
    raise NotImplementedError('not done')

