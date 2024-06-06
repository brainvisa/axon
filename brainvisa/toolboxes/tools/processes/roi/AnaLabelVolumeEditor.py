from brainvisa.processes import *
from brainvisa import anatomist
from brainvisa.processing.qtgui.neuroProcessesGUI import mainThreadActions
from soma.qt_gui.qtThread import MainThreadLife
import threading
import os


name = 'Label volume editor'
roles = ('editor',)
userLevel = 0


def validation():
    anatomist.validation()


signature = Signature(
    'label_volume', WriteDiskItem('Label volume',
                                  'Aims writable volume formats'),
    'support_volume', ReadDiskItem('Raw T1 MRI',
                                   'Anatomist volume formats',
                                   exactType=True),
    'pipeline_mask_nomenclature', ReadDiskItem('Nomenclature', 'Hierarchy'),
    'background_label', OpenChoice('minimum'),
)


def initialization(self):
    self.linkParameters('support_volume', 'label_volume', self.linkSupportVolume)
    self.pipeline_mask_nomenclature = self.signature['pipeline_mask_nomenclature'].findValue(
        {"filename_variable": "pipeline_masks"}, requiredAttributes={"filename_variable": "pipeline_masks"})
    self.setOptional('pipeline_mask_nomenclature')
    self.setOptional('support_volume')


def linkSupportVolume(self, *args):
    """Find a T1 that is guaranteed to be from the same acquisition."""
    label_vol_attrs = self.label_volume.hierarchyAttributes()
    required_attrs = {
        'center': label_vol_attrs.get('center'),
        'subject': label_vol_attrs.get('subject'),
        'acquisition': label_vol_attrs.get('acquisition'),
    }
    if 'normalization' in label_vol_attrs:
        required_attrs['normalization'] = label_vol_attrs['normalization']
    if None in required_attrs.values():
        # Give up: findValue could match anything, including images from a
        # different subject
        return None
    wdi = self.signature['support_volume']
    return wdi.findValue(self.label_volume,
                         requiredAttributes=required_attrs)


def add_save_button(self, win):
    if neuroConfig.anatomistImplementation == 'socket':
        return None  # cannot add buttons via socket API
    from soma.wip.application.api import findIconFile
    from soma.qt_gui.qt_backend import QtGui, QtCore

    toolbar = win.findChild(QtGui.QToolBar, 'mutations')
    if toolbar is None:
        toolbar = win.findChild(QtGui.QToolBar)
        if toolbar is None:
            toolbar = win.addToolBar('BV toolbar')
            if win.toolBarsVisible():
                toolbar.show()
    if toolbar is not None:
        toolbar.addSeparator()
        icon = QtGui.QIcon(findIconFile('save.png'))
        ac = QtGui.QAction(icon,
                           win.tr('Save ROI', 'QAWindow'), win.getInternalRep())
        toolbar.addAction(ac)
        data = self.data.ref()
        ac.triggered.connect(data.save_roi)
        data.win_deleted = False
        win.getInternalRep().destroyed.connect(data.close_and_save)
        return ac


# def remove_save_button(self, win, ac):
    # if neuroConfig.anatomistImplementation == 'socket':
        # return None # cannot add buttons via socket API
    # from soma.wip.application.api import findIconFile
    # from soma.qt_gui.qt_backend import QtGui, QtCore

    # toolbar = win.findChild( QtGui.QToolBar, 'mutations' )
    # if toolbar is None:
        # toolbar = win.findChild( QtGui.QToolBar )
        # if toolbar is None:
            # toolbar = win.addToolBar( 'BV toolbar' )
            # if win.toolBarsVisible():
                # toolbar.show()
    # if toolbar is not None:
        # from soma.qt_gui.qt_backend import sip
        # sip.transferbacck(ac)


class EditData:
    glob_lock = threading.RLock()
    edited_data = set()

    def __del__(self):
        self.close_and_save(self.window)

    def close_and_save(self, win):
        self.save_roi()
        self.win_deleted = True
        if self.label_volume is not None:
            with self.glob_lock:
                self.edited_data.remove(self.label_volume.fullPath())

        self.label_volume = None
        self.tmpdir = None
        self.context = None
        self.voigraph = None
        self.window = None
        self.fgraphbase = None
        self.finalgraph = None
        self.voigraphnum = None
        self.ana_objects = None

    def save_roi(self, message=None):
        data = self
        if self.win_deleted:
            return  # nothing to do
        context = data.context
        if not isinstance(message, str) or not message:
            message = 'Save ROI {0} ?'.format(data.label_volume)
        modified = (os.stat(data.label_volume.fullPath()).st_mtime != data.m_date)
        if modified:
            message += '<br/><b style="color: #c00000;">WARNING: the file has ' \
                'been modified after it has been loaded, thus saving it may ' \
                'overwrite other modifications !</b>'
        rep = context.ask(message, "OK", "Cancel", modal=0)
        if rep != 1:
            data.voigraphnum.save(data.voigraph)
            a = anatomist.Anatomist()
            a.sync()
                # make sure that anatomist has finished to process previous commands
            # a.getInfo()
            context.system('AimsGraphConvert',
                           '-i', data.voigraph,
                           '-o', data.finalgraph,
                           '--volume')
            if self.background_label != 'minimum':
                val = self.background_label
            else:
                val = 0
            context.system('AimsReplaceLevel', '-i',
                        os.path.join(
                            data.fgraphbase + '.data', 'roi_Volume'), '-o',
                        data.label_volume, '-g', -1, '-n', val)
            # update loaded date
            data.m_date = os.stat(data.label_volume.fullPath()).st_mtime


def execution(self, context):
    data = EditData()
    already_edited = False
    with data.glob_lock:
        if self.label_volume.fullPath() in data.edited_data:
            already_edited = True
        data.edited_data.add(self.label_volume.fullPath())
    if already_edited:
        raise RuntimeError(
            'The file {0} is already edited in another editor in the same '
            'BrainVisa/Anatomist session.'.format(
                self.label_volume.fullPath()))
    self.data = MainThreadLife(data)
    data.m_date = os.stat(self.label_volume.fullPath()).st_mtime

    a = anatomist.Anatomist()
    ana_objects = []
    if self.pipeline_mask_nomenclature is not None:
        hie = a.loadObject(self.pipeline_mask_nomenclature)
        ana_objects.append(hie)

    if self.background_label != 'minimum':
        mask = context.temporary('GIS image', 'Label Volume')
        context.write('not min')
        context.system('AimsReplaceLevel', '-i', self.label_volume, '-o', mask,
                       '-g', int(self.background_label), '-g', -
                       32767, '-n', -32767, '-n',
                       -32766)
    else:
        mask = self.label_volume
    if self.support_volume:
        vol = self.support_volume
    else:
        vol = mask
    tmpdir = context.temporary('directory')
    voigraphname = os.path.basename(self.label_volume.fullName())
    voigraph = os.path.join(tmpdir.fullPath(), '{0}.arg'.format(voigraphname))
    fgraphbase = os.path.join(tmpdir.fullPath(),
                              'finalgraph_{0}'.format(voigraphname))
    finalgraph = fgraphbase + '.arg'

    context.system('AimsGraphConvert',
                   '-i', mask.fullPath(),
                   '-o', voigraph,
                   '--bucket')

    imagenum = a.loadObject(vol)
    ana_objects.append(imagenum)
    voigraphnum = a.loadObject(voigraph)
    ref = imagenum.referential
    if ref != a.centralRef:
        voigraphnum.assignReferential(ref)
        windownum = a.createWindow('Axial')
        windownum.assignReferential(ref)
    else:
        windownum = a.createWindow('Axial')
    a.addObjects(objects=[voigraphnum, imagenum], windows=[windownum])

    voigraphnum.setMaterial(a.Material(diffuse=[0.8, 0.8, 0.8, 0.5]))
    # selects the graph
    children = voigraphnum.children
    windownum.group.addToSelection(children)
    if len(children) > 1:
        windownum.group.unSelect(children[1:])

    del children

    a.execute('SetControl', windows=[windownum], control='PaintControl')
    windownum.showToolbox(True)

    data.tmpdir = tmpdir
    data.label_volume = self.label_volume
    data.context = context
    data.voigraph = voigraph
    data.window = windownum
    data.fgraphbase = fgraphbase
    data.finalgraph = finalgraph
    data.voigraphnum = voigraphnum
    data.background_label = self.background_label
    data.ana_objects = ana_objects
    data.win_deleted = False

    ac = mainThreadActions().call(self.add_save_button, windownum)

    res = self.data
    del self.data
    return res

