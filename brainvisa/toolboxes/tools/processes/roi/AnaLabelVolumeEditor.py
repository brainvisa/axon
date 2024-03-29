from brainvisa.processes import *
from brainvisa import anatomist
from brainvisa.processing.qtgui.neuroProcessesGUI import mainThreadActions

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
        ac.triggered.connect(self.save_roi)
        self.win_deleted = False
        self.local_event_loop = None
        win.getInternalRep().destroyed.connect(self.close_and_save)
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


def close_and_save(self, win):
    self.save_roi()
    self.win_deleted = True
    if self.local_event_loop is not None:
        # if a local event loop runs in the main thread, quit it
        self.local_event_loop.quit()


def save_roi(self, message=None):
    context = self.context
    if not isinstance(message, str) or not message:
        message = 'Save ROI ?'
    rep = context.ask(message, "OK", "Cancel", modal=0)
    if rep != 1:
        self.voigraphnum.save(self.voigraph)
        a = anatomist.Anatomist()
        a.sync()
               # make sure that anatomist has finished to process previous commands
        # a.getInfo()
        context.system('AimsGraphConvert',
                       '-i', self.voigraph,
                       '-o', self.finalgraph,
                       '--volume')
        if self.background_label != 'minimum':
            val = self.background_label
        else:
            val = 0
        context.system('AimsReplaceLevel', '-i',
                       os.path.join(
                           self.fgraphbase + '.data', 'roi_Volume'), '-o',
                       self.label_volume, '-g', -1, '-n', val)


def execution(self, context):
    a = anatomist.Anatomist()
    if self.pipeline_mask_nomenclature is not None:
        hie = a.loadObject(self.pipeline_mask_nomenclature)

    context.write('background:', self.background_label)
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
    voi = os.path.join(tmpdir.fullPath(), 'voi.ima')
    voigraph = os.path.join(tmpdir.fullPath(), 'voigraph.arg')
    fgraphbase = os.path.join(tmpdir.fullPath(), 'finalgraph')
    finalgraph = fgraphbase + '.arg'

    context.system('AimsGraphConvert',
                   '-i', mask.fullPath(),
                   '-o', voigraph,
                   '--bucket')

    imagenum = a.loadObject(vol)
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
    windownum.group.unSelect(children[1:])

    del children

    a.execute('SetControl', windows=[windownum], control='PaintControl')
    windownum.showToolbox(True)

    self.context = context
    self.voigraph = voigraph
    self.window = windownum
    self.fgraphbase = fgraphbase
    self.finalgraph = finalgraph
    self.voigraphnum = voigraphnum
    self.finished = False
    ac = mainThreadActions().call(self.add_save_button, windownum)
    if ac:
        self.wait_for_close(windownum)
        import threading
        from soma.qt_gui.qt_backend import Qt
        done = False
        while not done:
            if isinstance(threading.current_thread(), threading._MainThread):
                Qt.QApplication.instance().processEvents()
            time.sleep(0.1)
            done = mainThreadActions().call(getattr, self, 'win_deleted')
    else:
        # ac is None, probably socket mode
        self.save_roi(message='Click here when finished')

    # mainThreadActions().call(self.remove_save_button, windownum, ac)
    del self.context
    del self.voigraph
    del self.window
    del self.fgraphbase
    del self.finalgraph
    del self.voigraphnum


def wait_for_close(self, win):
    import threading
    from soma.qt_gui.qt_backend import Qt
    if isinstance(threading.current_thread(), threading._MainThread):
        # we are running in the main thread: use a local event loop to wait
        # for the editor window to be closed by the user. The destroyed
        # callback will take care of ending the loop.
        self.local_event_loop = Qt.QEventLoop()
        self.local_event_loop.exec()
    else:
        # we are running in a secondary thrad: poll in the main thread for
        # the editor window to be closed by the user
        done = False
        while not done:
            time.sleep(0.1)
            done = mainThreadActions().call(getattr, self, 'win_deleted')
