
from brainvisa import processes
from brainvisa.processes import (
    Signature, ReadDiskItem, WriteDiskItem, ListOf, Choice, Float, Integer,
    String, getProcessInstance, formatLists, getAllFormats, mainThreadActions)
import math
import json


userLevel = 0


def get_viewers():
    viewers = set()
    for procset in processes._viewers.values():
        viewers.update(procset)
    return sorted(viewers)


presets = {
    'Sulci': 'AnatomistShowFoldGraph',
    'Brain mask': 'AnatomistShowBrainMask',
    'Bias correction': 'AnatomistShowBiasCorrection',
    'Histogram analysis': 'histo_analysis_viewer',
}


signature = Signature(
    'snapshot', WriteDiskItem('2D Image',
                              formatLists['aims image formats']
                              + ['PDF file']),
    'preset', Choice(*(sorted(presets.keys()) + ['Any'])),
    'viewer_type', Choice(*get_viewers()),
    'input_data', ListOf(ReadDiskItem('Any type', getAllFormats())),
    'displayed_attributes', ListOf(String()),
    'page_size_ratio', Float(),
    'max_views_per_page', Integer(),
    'indiv_width', Integer(),
    'indiv_height', Integer(),
    'referential', Choice('Talairach', 'MNI', 'Native'),
    'view_config', String(),
    'background_color', ListOf(Float()),
    'text_color', ListOf(Float()),
    'text_offset', ListOf(Integer()),
)


def link_preset(self, preset):
    vtype = presets.get(preset, 'Any')
    if [x for x in self.signature['viewer_type'].values if x[0] == vtype]:
        return presets[preset]
    return self.viewer_type


def set_input_data_type(self, viewer_type):
    try:
        viewer = getProcessInstance(viewer_type)
    except Exception as e:
        print(e)
        return
    if viewer is not None:
        main_input = viewer.signature.values()[0]
        itype = main_input
        # clear value (which will become incopatible)
        self.setValue('input_data', None, True)
        # then chage type
        self.signature['input_data'] = ListOf(itype)
        self.changeSignature(self.signature)


def initialization(self):
    self.signature['viewer_type'].setChoices(*get_viewers())
    self.preset = 'Sulci'
    self.displayed_attributes = ['subject']
    self.page_size_ratio = 1.33
    self.max_views_per_page = 0
    self.indiv_width = 500
    self.indiv_height = 400
    self.background_color = [0., 0., 0.]
    self.text_color = [0.5, 0.5, 0.5]
    self.text_offset = [10, 10]
    self.setOptional('view_config')
    self.addLink('viewer_type', 'preset', self.link_preset)
    self.addLink(None, 'viewer_type', self.set_input_data_type)


def save_pdf_page(self, current_page, page, context):
    from reportlab.pdfgen import canvas

    # print('save PDF')
    if self.pdf is None:
        self.pdf = canvas.Canvas(self.snapshot.fullPath())
    timage = context.temporary('JPEG image')
    current_page.save(timage.fullPath())
    pw = 560
    ph = 800
    w = pw
    h = int(current_page.height() * w / current_page.width())
    if h > ph:
        h = ph
        w = int(current_page.width() * h / current_page.height())
    context.write(w, h)
    y = 20
    if h < ph:
        y += ph - h
    self.pdf.drawImage(timage.fullPath(), 20, y, width=w, height=h)
    self.pdf.showPage()


def save_page(self, current_page, page, context):
    # print('save_page', current_page)
    if self.snapshot.format.name == 'PDF File':
        self.save_pdf_page(current_page, page, context)
    if current_page is None:
        return
    fname = self.snapshot.fullPath()
    if page != 0:
        fname = self.snapshot.fullName() + '_%d' % page \
            + self.snapshot.fullPath()[len(self.snapshot.fullName()):]
    # print('fname:', fname)
    current_page.save(fname)


def save_pdf(self):
    if self.pdf is not None:
        self.pdf.save()


def snapshot_size(self, n):
    if self.max_views_per_page != 0 and n > self.max_views_per_page:
        n = self.max_views_per_page
    sw = self.indiv_width
    sh = self.indiv_height
    spacing = 10
    nr = 1
    width = 0
    height = 0
    while True:
        nc = math.ceil(n / nr)
        rwidth = nc * sw + spacing * (nc - 1)
        rheight = nr * sh + spacing * (nr - 1)
        if rwidth / rheight < self.page_size_ratio:
            break
        nr += 1
    if nr > 1:
        nr -= 1
    nc = math.ceil(n / nr)
    nr = math.ceil(n / nc)
    width = nc * sw + spacing * (nc - 1)
    height = nr * sh + spacing * (nr - 1)
    return width, height, nr, nc, spacing


def merge_dicts(d1, d2):
    for k, v in d2.items():
        if not isinstance(v, dict) or k not in d1:
            d1[k] = v
        else:
            merge_dicts(d1[k], v)


def setup_view(self, w, config, data):
    import anatomist.direct.api as ana

    wconfig = config.get(w.windowType, config)
    a = ana.Anatomist()
    if self.referential == 'Talairach':
        w.setReferential(a.centralReferential())
    elif self.referential == 'MNI':
        w.setReferential(ana.cpp.Referential.mniTemplateReferential())
    w.focusView()

    base_configs = {
        'Talairach': {
            'all': {
                'all': {
                    'observer_position': [0, 17, -20],
                    'boundingbox_max': (120, 100, 90),
                    'boundingbox_min': (-120, -100, -20),
                },
            },
            'left': {
                'all': {
                    'cursor_position': [33, 17, -8],
                },
                '3D': {
                    'view_quaternion': [0.5, 0.5, 0.5, 0.5]
                }
            },
            'right': {
                'all': {
                    'cursor_position': [-33, 17, -8],
                },
                '3D': {
                    'view_quaternion': [0.5, -0.5, -0.5, 0.5]
                }
            }
        },
        'MNI': {
            'all': {
                'all': {
                    'observer_position': [0., -22., 14.],
                    #'cursor_position': [33, 17, -8],
                    'boundingbox_max': (37., 93., 72.),
                    'boundingbox_min': (-37., -93., -72.),
                },
            },
            'left': {
                '3D': {
                    'view_quaternion': [0.5, -0.5, -0.5, 0.5]
                }
            },
            'right': {
                '3D': {
                    'view_quaternion': [0.5, 0.5, 0.5, 0.5]
                }
            }
        },
        'Native': {
            'all': {
                'all': {
                    'observer_position': [0., 130., 95.],
                    'boundingbox_max': (40., 55., 90.),
                    'boundingbox_min': (-40., -55., -90.),
                    'zoom': 0.65,
                },
            },
            'left': {
                '3D': {
                    'view_quaternion': [0.5, 0.5, 0.5, 0.5]
                }
            },
            'right': {
                '3D': {
                    'view_quaternion': [0.5, -0.5, -0.5, 0.5]
                }
            }
        },
    }
    side = data.get('side')
    refconf = base_configs.get(self.referential, {}).get('all', {})
    merge_dicts(refconf, base_configs.get(self.referential, {}).get(side, {}))
    camera = {'cursor_position': (0, 0, 0), 'zoom': 1}
    merge_dicts(camera, refconf.get('all', {}))
    merge_dicts(camera, refconf.get(w.windowType, {}))
    bbox = camera.get('boundingbox_max')
    bbmin = camera.get('boundingbox_min')
    if bbox and bbmin and 'observer_position' not in camera:
        obs_pos = tuple((x+y)/2 for x, y in zip(bbox, bbmin))
        camera['observer_position'] = obs_pos
    swconfig = {'cursor_visibility': 0,
                'light': {'background': self.background_color + [1.]}}

    sconfig = wconfig.get(side, wconfig)
    merge_dicts(camera, sconfig.get('camera', {}))
    if camera:
        w.camera(**camera)
    swconfig.update(sconfig.get('window_config', {}))
    if swconfig:
        w.windowConfig(**swconfig)


def print_attributes(self, qimage, att_dict):
    from soma.qt_gui.qt_backend import Qt

    painter = Qt.QPainter(qimage)
    painter.setFont(Qt.QFont('Arial', 18))
    painter.setPen(Qt.QColor(*[int(x*255.9) for x in self.text_color]))
    n = len(att_dict)
    for i, v in enumerate(att_dict.values()):
        painter.drawText(self.text_offset[0],
                         qimage.height() - self.text_offset[1]
                         - (n - i - 1) * 20, v)


def execution_mainthread(self, context):
    import anatomist.headless as hana

    hana.setup_headless()

    import anatomist.direct.api as ana
    from soma.qt_gui.qt_backend import Qt

    config = {}
    if self.view_config:
        config = json.loads(self.view_config)

    viewer = getProcessInstance(self.viewer_type)
    current_page = None
    n = 0
    page = 0
    r = 0
    c = 0
    self.pdf = None  # PDF doc if written in this format

    try:
        for ni, in_data in enumerate(self.input_data):
            res = context.runProcess(viewer, in_data)
            w = None
            qwid = None
            todo = [res]
            while todo:
                item = todo.pop(0)
                if isinstance(item, (list, tuple)):
                    todo += list(item)
                elif isinstance(item, ana.Anatomist.AWindow) \
                        and item.windowType != 'Browser':
                    # print('AWINDOW')
                    w = item
                    break
                elif isinstance(item, dict):
                    todo += item.values()
                elif isinstance(item, Qt.QWidget):
                    if qwid is None:
                        qwid = item
                elif hasattr(item, 'ref') \
                        and hasattr(item.ref, '__call__') \
                        and isinstance(item.ref(), Qt.QWidget):
                    if qwid is None:
                        qwid = item.ref()

            if w is None:
                if qwid is not None:
                    context.write('uging widget')
                else:
                    context.write('Viewer returns no Anatomist window and '
                                  'no widget.')
                # print(repr(res))

            if w is not None:
                self.setup_view(w, config, in_data)
                qimage = w.snapshotImage(self.indiv_width, self.indiv_height)
                scale = 1.
            elif qwid is not None:
                qwid.resize(self.indiv_width, self.indiv_height)
                qimage = qwid.grab()
                scale = self.indiv_width / qimage.width()
                if qimage.height() * scale > self.indiv_height:
                    scale = self.indiv_height / qimage.height()
                w = True
            if w:
                att_dict = {k: in_data.get(k)
                            for k in self.displayed_attributes}
                self.print_attributes(qimage, att_dict)

                if self.max_views_per_page != 0 \
                        and n == self.max_views_per_page:
                    n = 0
                    self.save_page(current_page, page, context)
                    current_page = None
                    page += 1
                if current_page is None:
                    width, height, nrows, ncols, spacing \
                        = self.snapshot_size(len(self.input_data) - ni)
                    current_page = Qt.QImage(width, height,
                                             Qt.QImage.Format_RGB32)
                    current_page.fill(Qt.QColor(*[
                        int(x * 255.9) for x in self.background_color]))
                    c = 0
                    r = 0
                painter = Qt.QPainter(current_page)
                painter.scale(scale, scale)
                x = c * (self.indiv_width + spacing)
                y = r * (self.indiv_height + spacing)
                # print('paint', c, r, x, y)
                if isinstance(qimage, Qt.QPixmap):
                    painter.drawPixmap(int(x / scale), int(y / scale), qimage)
                else:
                    painter.drawImage(x, y, qimage)
                del painter
                n += 1
                c += 1
                if c == ncols:
                    c = 0
                    r += 1
        self.save_page(current_page, page, context)
        self.save_pdf()

    finally:
        del self.pdf


def execution(self, context):
    return mainThreadActions().call(self.execution_mainthread, context)
