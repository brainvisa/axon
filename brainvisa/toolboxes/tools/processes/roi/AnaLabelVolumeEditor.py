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
                                  'aims writable Volume Formats'),
  'support_volume', ReadDiskItem('Raw T1 MRI',
                                 'anatomist Volume Formats',
                                 exactType=True),
  'pipeline_mask_nomenclature', ReadDiskItem('Nomenclature', 'Hierarchy'),
  'background_label', OpenChoice('minimum'),
)


def initialization(self):
    self.linkParameters('support_volume', 'label_volume')
    self.pipeline_mask_nomenclature = self.signature['pipeline_mask_nomenclature'].findValue(
        {"filename_variable": "pipeline_masks"}, requiredAttributes={"filename_variable": "pipeline_masks"})
    self.setOptional('pipeline_mask_nomenclature')
    self.setOptional('support_volume')


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
        # import sip
        # sip.transferbacck(ac)


def close_and_save(self, win):
    self.save_roi()
    self.win_deleted = True


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
        done = False
        while not done:
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
