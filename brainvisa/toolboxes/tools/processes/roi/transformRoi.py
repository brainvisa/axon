# -*- coding: iso-8859-1 -*-
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

from __future__ import print_function
from __future__ import absolute_import
from brainvisa.processes import *
from brainvisa.processing.qtgui.neuroProcessesGUI import mainThreadActions

import anatomist.cpp as anatomist
import anatomist.api as ana
from soma.qt_gui.qt_backend import QtCore, QtGui, uic
from anatomist.cpp.paletteEditor import PaletteEditor
from soma.qt_gui.qtThread import MainThreadLife
from soma import aims
from soma.minf.api import *
import soma
from soma.subprocess import check_call
from tempfile import mkdtemp, mktemp
import glob
import numpy as np
import math
import six
from six.moves import range
# from brainvisa.tools.transformROI import transform_roi

name = 'Transform ROI'
userLevel = 0

signature = Signature(
    'images', ListOf(ReadDiskItem('4D Volume', 'NIFTI-1 image')),
  'inputRoi', ListOf(ReadDiskItem('ROI', ['Graph and data', 'NIFTI-1 image'])),
  'outputRoi', ListOf(
      WriteDiskItem('ROI', ['Graph and data', 'NIFTI-1 image'])),
)


def findExtraFile(filename, type):
    for dir in sorted(glob.glob(os.path.join(*(split_path(soma.__file__)[:-3] + ['share', 'axon-*', type])))):
        if os.path.exists(dir):
            filepath = os.path.join(dir, filename)
            if os.path.exists(filepath):
                return filepath
    return None


def initialization(self):
    self.setOptional('outputRoi')


def execution(self, context):
    objs = transform_roi(self.images,
                         self.inputRoi,
                         self.outputRoi,
                         context)

    return objs


def transform_roi(images,
                  inputRoi,
                  outputRoi=None,
                  context=None):
    _mw = mainThreadActions().call(_transform_roi_on_gui_thread,
                                   images,
                                   inputRoi,
                                   outputRoi,
                                   context)
    mw = MainThreadLife(_mw)
    return [mw]


def _transform_roi_on_gui_thread(images,
                                 inputRoi,
                                 outputRoi,
                                 context):
    transformRoi = TransformRoi(images=images,
                                inputRoi=inputRoi,
                                outputRoi=outputRoi,
                                parent=context)
    mw = transformRoi.display()
    return mw


class TransformRoi():

    def __init__(self, images, inputRoi, outputRoi, parent):
        self._temporaryObjects = []
        self._images = images
        self._inputRoi = []
        for i, r in enumerate(inputRoi):
            if os.path.splitext(r.fullPath())[1] == ".nii":
                tmpDir = mkdtemp()
                self._addTemporaryObjects(tmpDir)
                name = os.path.splitext(
                    os.path.basename(r.fullPath()))[0] + '.arg'
                check_call(
                    ['AimsGraphConvert', '-i', r.fullPath(), '--roi', '--bucket', '-o', os.path.join(tmpDir, name)])
                self._inputRoi.append(os.path.join(tmpDir, name))
            else:
                self._inputRoi.append(r.fullPath())
        self._outputRoi = {}
        for i in six.moves.xrange(len(self._inputRoi)):
            if not outputRoi:
                self._outputRoi.update({self._inputRoi[i]: self._inputRoi[i]})
            else:
                self._outputRoi.update({self._inputRoi[i]: outputRoi[i]})

        self._globalModeOn = True
        self._symmetricModeOn = False
        self._symmetricPlaneEditOn = False
        self._initRoiDict()
        self.symPlaneChangeTransmitter = SymPlaneChangeTransmitter()

    def display(self):
        self.a = ana.Anatomist('-b')
        self._addTrsfAction()
        self._loadData()
        self._loadUi()
        self._createViews()
        self._updateViews()
        self._roiSelectionChanged(0)
        self._init3dCursor()
        self._updateUi()
        self._updateControlMode()
        self._mainDiag.showMaximized()
        self._mainDiag.exec_()
        self._removeSymmetricPlaneAction()

        return [self._mainDiag]

    def _initRoiDict(self):
        self._roiDict = {}
        for r in self._inputRoi:
            translation = np.array([0., 0., 0., 1.])
            rotation = np.array([0., 0., 0.])
            rotationSym = 0.
            gap = 0.
            self._roiDict.update({r: {"global_transformation":
                                        {"translation": translation,
                                         "rotation": rotation,
                                         "rotationSym": rotationSym,
                                         "gap": gap
                                         },
                                      "sub_roi": {}}})
            roiIt = aims.getRoiIterator(r)

            while roiIt.isValid():
                translation = np.array([0., 0., 0., 1.])
                rotation = np.array([0., 0., 0.])
                rotationSym = 0.
                gap = 0.
                self._roiDict[r]["sub_roi"].update(
                    {roiIt.regionName():
                                    {"meshes": [],
                                     "transformation":
                                        {"translation": translation,
                                         "rotation": rotation,
                                         "rotationSym": rotationSym,
                                         "gap": gap
                                         }
                                     }
                     })
                next(roiIt)

    def _init3dCursor(self):
        aImg = self._aImages[self._getSelectedImage()]
        bbox = [aims.Point3df(x[:3]) for x in aImg.boundingbox()]
        position = (bbox[1] - bbox[0]) * 0.5
        t = self.a.getTransformation(aImg.getReferential(),
                                     self._aViews[0].getReferential())
        if t:
            position = t.transform(position)
        self.a.execute(
            'LinkedCursor', window=self._aViews[0], position=position)

    def _addTrsfAction(self):
        ad = anatomist.ActionDictionary.instance()
        cd = anatomist.ControlDictionary.instance()
        cm = anatomist.ControlManager.instance()
        if ad.getActionInstance("TrsfAction"):
            ad.removeAction('TrsfAction')
            cd.removeControl('TrsfControl')
            cm.removeControl('QAGLWidget3D', '', 'TrsfControl')
        if not ad.getActionInstance("TrsfAction"):
            ad.addAction('TrsfAction', lambda: TrsfAction(self))
            cd.addControl('TrsfControl', lambda: TrsfControl(), 25)
            cm.addControl('QAGLWidget3D', '', 'TrsfControl')
        else:
            ad.getActionInstance("TrsfAction").setMainProcess(self)
        del cd, cm, ad

    def _removeSymmetricPlaneAction(self):
        ad = anatomist.ActionDictionary.instance()
        cd = anatomist.ControlDictionary.instance()
        cm = anatomist.ControlManager.instance()
        if ad.getActionInstance("SymEditAction"):
            ad.removeAction('SymEditAction')
            cd.removeControl('SymEditControl')
            cm.removeControl('QAGLWidget3D', '', 'SymEditControl')

    def _addSymmetricPlaneAction(self):
        ad = anatomist.ActionDictionary.instance()
        cd = anatomist.ControlDictionary.instance()
        cm = anatomist.ControlManager.instance()
        if ad.getActionInstance("SymEditAction"):
            ad.removeAction('SymEditAction')
            cd.removeControl('SymEditControl')
            cm.removeControl('QAGLWidget3D', '', 'SymEditControl')
        if not ad.getActionInstance("SymEditAction"):
            ad.addAction('SymEditAction', lambda: SymEditAction(self))
            cd.addControl('SymEditControl', lambda: SymEditControl(), 25)
            cm.addControl('QAGLWidget3D', '', 'SymEditControl')
        else:
            ad.getActionInstance("SymEditAction").setMainProcess(self)
        del cd, cm, ad

    def _loadUi(self):
        self._mainDiag = uic.loadUi(findExtraFile("transformRoi.ui", "ui"))
        self._mainDiag.setWindowFlags(QtCore.Qt.WindowTitleHint |
                                      QtCore.Qt.WindowMinMaxButtonsHint |
                                      QtCore.Qt.WindowCloseButtonHint)
        palette = self._mainDiag.palette()
        palette.setColor(
            self._mainDiag.backgroundRole(), QtGui.QColor(255, 255, 255))
        self._mainDiag.setPalette(palette)

        self._mainDiag.imageCb.clear()
        for img in self._images:
            self._mainDiag.imageCb.addItem(
                os.path.splitext(os.path.basename(img.fullPath()))[0])
        self._setComboboxViewMinimumWidth(self._mainDiag.imageCb)
        self._mainDiag.imageCb.currentIndexChanged.connect(
            self._imageSelectionChanged)

        self._mainDiag.roiCb.clear()
        for roi in self._inputRoi:
            self._mainDiag.roiCb.addItem(
                os.path.splitext(os.path.basename(roi))[0])
        self._setComboboxViewMinimumWidth(self._mainDiag.roiCb)
        self._mainDiag.roiCb.currentIndexChanged.connect(
            self._roiSelectionChanged)
        self._roiCbPreviousIndex = 0
        self._mainDiag.subRoiList.itemClicked.connect(
            self._subRoiSelectionChanged)

        translationSp = [self._mainDiag.xSp, self._mainDiag.ySp,
                         self._mainDiag.zSp]
        for sp in translationSp:
            sp.valueChanged.connect(self._translationChanged)

        rotationSp = [self._mainDiag.axialSp,
            self._mainDiag.sagittalSp, self._mainDiag.coronalSp]
        for sp in rotationSp:
            sp.valueChanged.connect(self._rotationChanged)

        self._mainDiag.gapSp.valueChanged.connect(self._gapChanged)
        self._mainDiag.rotationSymSp.valueChanged.connect(
            self._rotationSymChanged)

        self._mainDiag.globalCb.setChecked(self._globalModeOn)
        self._mainDiag.globalCb.stateChanged.connect(self._globalStatusChanged)

        self._mainDiag.symmetricCb.setChecked(self._symmetricModeOn)
        self._mainDiag.symmetricCb.stateChanged.connect(
            self._symmetricStatusChanged)
        self._mainDiag.symmetricPlaneBt.toggled.connect(
            self._symmetricPlaneToggled)
        self._mainDiag.resetBt.clicked.connect(self._resetClicked)
        self._mainDiag.cancelBt.clicked.connect(self._accept)
        self._mainDiag.validBt.clicked.connect(self._validClicked)

        self._mainDiag.applyBt.setHidden(True)
        self._mainDiag.cursorMode.setIcon(
            QtGui.QIcon(findExtraFile("cursor3d.png", "icons")))
        self._mainDiag.transformMode.setIcon(
            QtGui.QIcon(findExtraFile("transformation.png", "icons")))
# self._mainDiag.applyBt.setIcon(QtGui.QIcon(findExtraFile("save.png",
# "icons")))
        self._mainDiag.cancelBt.setIcon(
            QtGui.QIcon(findExtraFile("delete.png", "icons")))
        self._mainDiag.validBt.setIcon(
            QtGui.QIcon(findExtraFile("ok.png", "icons")))
        self._mainDiag.centerBt.setIcon(
            QtGui.QIcon(findExtraFile("target.png", "icons")))

        self._addPaletteEditor()

        controlBt = [self._mainDiag.cursorMode, self._mainDiag.transformMode]
        for bt in controlBt:
            bt.clicked.connect(self._updateControlMode)

        self._mainDiag.displayCursor.stateChanged.connect(
            self._displayCursorChecked)

        self._mainDiag.centerBt.clicked.connect(self._centerClicked)

    def _loadData(self):
        self._createAnatomistImages()
        self._createMeshes()

    def _updateUi(self):
        moreThanOneSubRoi = len(
            list(self._roiDict[self.getSelectedRoi()]["sub_roi"].keys())) > 1
        if not moreThanOneSubRoi:
            self._globalModeOn = True
        self._mainDiag.globalCb.blockSignals(True)
        self._mainDiag.globalCb.setEnabled(
            moreThanOneSubRoi and not self._symmetricPlaneEditOn)
        self._mainDiag.globalCb.setChecked(self._globalModeOn)
        self._mainDiag.globalCb.blockSignals(False)

        self._mainDiag.symmetricCb.setEnabled(self._globalModeOn)
        self._mainDiag.symmetricPlaneBt.setEnabled(
            self._globalModeOn and self._symmetricModeOn)
        self._mainDiag.mirrorGb.setEnabled(
            self._globalModeOn and self._symmetricModeOn)
        self._mainDiag.symmetricCb.blockSignals(True)
        self._mainDiag.symmetricCb.setChecked(
            self._globalModeOn and self._symmetricModeOn)
        self._mainDiag.symmetricCb.blockSignals(False)

        self.updateTransformationUi()

        self._mainDiag.subRoiList.setEnabled(not self._globalModeOn)

        self._mainDiag.hardResetBt.setHidden(True)

    def updateTransformationUi(self):
        self._mainDiag.translationGb.setEnabled(not self._symmetricPlaneEditOn)
        self._mainDiag.rotationGb.setEnabled(not self._symmetricPlaneEditOn)
        self._mainDiag.mirrorGb.setEnabled(
            not self._symmetricPlaneEditOn and self._globalModeOn and self._symmetricModeOn)
        self._mainDiag.resetBt.setEnabled(not self._symmetricPlaneEditOn)
        self._mainDiag.hardResetBt.setEnabled(not self._symmetricPlaneEditOn)

        if self._globalModeOn:
            currentTransformation = self._roiDict[
                self.getSelectedRoi()]["global_transformation"]
        else:
            currentTransformation = self._roiDict[self.getSelectedRoi()][
                "sub_roi"][self.getSelectedSubRoi()]["transformation"]

        translationSp = [
            self._mainDiag.xSp, self._mainDiag.ySp, self._mainDiag.zSp]
        for i in six.moves.xrange(len(translationSp)):
            translationSp[i].blockSignals(True)
            translationSp[i].setValue(currentTransformation["translation"][i])
            translationSp[i].blockSignals(False)

        rotationSp = [self._mainDiag.axialSp,
            self._mainDiag.sagittalSp, self._mainDiag.coronalSp]
        for i in six.moves.xrange(len(rotationSp)):
            rotationSp[i].blockSignals(True)
            rotationSp[i].setValue(currentTransformation["rotation"][i])
            rotationSp[i].blockSignals(False)

        if self._globalModeOn:
            self._mainDiag.gapSp.blockSignals(True)
            self._mainDiag.gapSp.setValue(currentTransformation["gap"])
            self._mainDiag.gapSp.blockSignals(False)
            self._mainDiag.gapSp.blockSignals(True)
            self._mainDiag.rotationSymSp.setValue(
                currentTransformation["rotationSym"])
            self._mainDiag.gapSp.blockSignals(False)

    def _setComboboxViewMinimumWidth(self, cb):
        longestText = ""
        for i in range(cb.count()):
            text = cb.itemText(i)
            if len(text) > len(longestText):
                longestText = text
        cb.view().setMinimumWidth(
            QtGui.QFontMetrics(cb.font()).width(longestText + "  "))

    def _createAnatomistImages(self):
        self._aImages = {}
        for img in self._images:
            aimsImg = aims.read(img.fullPath())
            aImg = self.a.loadObject(img.fullPath())
            try:
                if aimsImg.header()["modality"] == "PT":
                    aImg.setPalette('Rainbow', minVal=0, maxVal=1)
                elif aimsImg.header()["modality"] == "NM":
                    aImg.setPalette('French', minVal=0, maxVal=1)
            except:
                pass
            self._aImages.update({img: aImg})

    def _addPaletteEditor(self):
        paletteFilter = ['B-W LINEAR', 'Blue-Green-Red-Yellow',
                         'Blue-Red2', 'French', 'RAINBOW',
                         'RED TEMPERATURE', 'Rainbow2']
        self._paletteEditor = PaletteEditor(
            self._aImages[self._images[self._mainDiag.imageCb.currentIndex()]],
                                            parent=self._mainDiag.frame,
                                            default='B-W LINEAR',
                                            palette_filter=paletteFilter)
        layout = QtGui.QVBoxLayout(self._mainDiag.imagePalette)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._paletteEditor)

    def _imageSelectionChanged(self, index):
        self._paletteEditor.setImage(self._aImages[self._getSelectedImage()])
        self._updateViews()

    def _roiSelectionChanged(self, index):
        self._mainDiag.subRoiList.clear()
        for roiName in sorted(self._roiDict[self.getSelectedRoi()]["sub_roi"].keys()):
            self._mainDiag.subRoiList.addItem(roiName)
        self._forceSubRoiSelection(0)
        self._updateUi()
        self._updateViews()

        if self._symmetricPlaneEditOn:
            self._mainDiag.symmetricPlaneBt.setChecked(False)

        self._roiCbPreviousIndex = self._mainDiag.roiCb.currentIndex()

    def _subRoiSelectionChanged(self, item):
        self._updateUi()

    def _globalStatusChanged(self, value):
        self._globalModeOn = (value > 0)
        self._forceSubRoiSelection(0)
        self._updateUi()

    def _symmetricStatusChanged(self, value):
        self._symmetricModeOn = (value > 0)
        self._updateUi()

    def _symmetricPlaneToggled(self, value):
        self._symmetricPlaneEditOn = value
        if value:
            self._addSymmetricPlaneAction()
            roi = self.getSelectedRoi()
            self.a.setWindowsControl(
                windows=self._aViews, control="SymEditControl")
        else:
            self._updateControlMode()
        self._updateUi()

    def _resetClicked(self):
        translation = np.array([0., 0., 0., 1.])
        rotation = np.array([0., 0., 0.])
        rotationSym = 0.
        gap = 0.
        if self._globalModeOn:
            self._roiDict[self.getSelectedRoi()]\
                         ["global_transformation"].update({"translation": translation,
                                                           "rotation": rotation,
                                                           "rotationSym": rotationSym,
                                                           "gap": gap})
        else:
            self._roiDict[self.getSelectedRoi()]["sub_roi"][self.getSelectedSubRoi()]\
                         ["transformation"].update({"translation": translation,
                                                    "rotation": rotation,
                                                    "rotationSym": rotationSym,
                                                    "gap": gap})
        self.updateTransformationUi()
        self.updateTransformations()

    def _forceSubRoiSelection(self, index):
        if not self._globalModeOn:
            self._mainDiag.subRoiList.blockSignals(True)
            self._mainDiag.subRoiList.setCurrentRow(index)
            self._mainDiag.subRoiList.blockSignals(False)

    def _translationChanged(self, value):
        if self._globalModeOn:
            self._roiDict[self.getSelectedRoi()]\
                         ["global_transformation"]\
                         ["translation"] = np.array([self._mainDiag.xSp.value(),
                                                     self._mainDiag.ySp.value(
                                                     ),
                                                     self._mainDiag.zSp.value(
                                                     ),
                                                     1.])
        else:
            self._roiDict[self.getSelectedRoi()]["sub_roi"][self.getSelectedSubRoi()]\
                         ["transformation"]\
                         ["translation"] = np.array([self._mainDiag.xSp.value(),
                                                     self._mainDiag.ySp.value(
                                                     ),
                                                     self._mainDiag.zSp.value(
                                                     ),
                                                     1.])
        self.updateTransformations()

    def _rotationChanged(self, value):
        if self._globalModeOn:
            self._roiDict[self.getSelectedRoi()]\
                         ["global_transformation"]\
                         ["rotation"] = np.array([self._mainDiag.axialSp.value(),
                                                  self._mainDiag.sagittalSp.value(
                                                  ),
                                                  self._mainDiag.coronalSp.value()])
        else:
            self._roiDict[self.getSelectedRoi()]["sub_roi"][self.getSelectedSubRoi()]\
                         ["transformation"]\
                         ["rotation"] = np.array([self._mainDiag.axialSp.value(),
                                                  self._mainDiag.sagittalSp.value(
                                                  ),
                                                  self._mainDiag.coronalSp.value()])
        self.updateTransformations()

    def _gapChanged(self, value):
        self._roiDict[self.getSelectedRoi()]\
                         ["global_transformation"]\
                         ["gap"] = self._mainDiag.gapSp.value()
        self.updateTransformations()

    def _rotationSymChanged(self, value):
        self._roiDict[self.getSelectedRoi()]\
                         ["global_transformation"]\
                         ["rotationSym"] = self._mainDiag.rotationSymSp.value()
        self.updateTransformations()

    def _displayCursorChecked(self, value):
        for view in self._aViews:
            view.setHasCursor(value > 0)
            view.setChanged()
            view.notifyObservers()
        self.a.execute('WindowConfig', windows=self._aViews,
                        light={'background': [0., 0., 0., 1.]})

    def _centerClicked(self):
        centers = self.getCenters(self.getSelectedRoi())
        pos = None
        if self._globalModeOn:
            pos = centers["global"]
        else:
            pos = centers["locals"][self.getSelectedSubRoi()]
        pos = aims.Point3df(pos[:-1])
        self.a.execute('LinkedCursor', window=self._aViews[0], position=pos)

    def _updateControlMode(self):
        if self._mainDiag.cursorMode.isChecked():
            self.a.setWindowsControl(
                windows=self._aViews, control="Default 3D control")
            for v in self._aViews:
                v.setCursor(QtCore.Qt.ArrowCursor)
        elif self._mainDiag.transformMode.isChecked():
            self.a.setWindowsControl(
                windows=self._aViews, control="TrsfControl")
            for v in self._aViews:
                v.setCursor(QtCore.Qt.OpenHandCursor)

    def _validClicked(self):
        self._mainDiag.frame.setEnabled(False)
        QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)

        roiValidities = {}
        for roi in self._inputRoi:
#            meshValidity = self._checkMeshValidity(roi)
            meshValidity = [False]
            roiValidities.update({roi: meshValidity})
            if True in meshValidity:
                alertMessage = "Your transformation for " + \
                    os.path.splitext(os.path.basename(roi))[
                                     0] + " is not valid:"
                if meshValidity[0]:
                    alertMessage += "\n- meshes intersect"
                if meshValidity[1]:
                    alertMessage += "\n- the ROI is outside the image bounds"
                alertMessage += "\nTo valid it, you must adjust the parameters of the transformation."
                QtGui.QMessageBox.critical(
                    None, "ROI transformation", alertMessage)
                continue

            roiChanged = False
            meshes = []
            for k, v in six.iteritems(self._roiDict[roi]["sub_roi"]):
                meshes += v["meshes"]
            for mesh in meshes:
                if not self._previousMotions[mesh].isIdentity():
                    roiChanged = True
                    break
            if not roiChanged:
                continue

            images = []
            aimsRoi = aims.read(roi)
            labels = {}
            for v in aimsRoi.vertices():
                labels.update({v["name"]: int(v["roi_label"])})
            label = 1
            for k, v in six.iteritems(labels):
                imageFile = mktemp(suffix='.nii')
                self._addTemporaryObjects(imageFile)
                aims.write(self._getImageFromRoi(
                    roi, selectedLabel=label), imageFile)
                images.append(imageFile)
                trsfTmp = mktemp(suffix='.trm')
                self._addTemporaryObjects(trsfTmp)
                aims.write(self._previousMotions[
                           self._roiDict[roi]["sub_roi"][k]["meshes"][0]], trsfTmp)
                check_call(
                    ['AimsResample', '-i', imageFile, '-o', imageFile, '-m', trsfTmp, '-t', 'n'])
                label += 1

            firstImg = aims.read(images[0])
            firstArr = np.array(firstImg, copy=False)
            for img in images[1:]:
                currImg = aims.read(img)
                currArr = np.array(currImg, copy=False)
                firstArr[:] |= currArr[:]

            if os.path.splitext(self._outputRoi[roi].fullPath())[1] == ".nii":
                aims.write(firstImg, self._outputRoi[roi].fullPath())
            else:
                imageFile = mktemp(suffix='.nii')
                self._addTemporaryObjects(imageFile)
                aims.write(firstImg, imageFile)
                check_call(
                    ['AimsGraphConvert', '-i', imageFile, '--roi', '--bucket', '-o', self._outputRoi[roi].fullPath()])
                check_call(
                    ['AimsGraphMesh', '-i', self._outputRoi[roi].fullPath(), '-o', self._outputRoi[roi].fullPath()])

                g = aims.read(self._outputRoi[roi].fullPath())
                names = dict((j, i) for i, j in six.iteritems(labels))
                for v in g.vertices():
                    name = names.get(v['roi_label'])
                    if name:
                        v['name'] = name
                    else:
                        print('WARNING: label %s of graph %s does not have a name' %
                              str(v['roi_label']))
                aims.write(g, self._outputRoi[roi].fullPath())

            trsfDict = {
                "global_transformation": self._roiDict[roi]["global_transformation"],
                        "sub_roi_transformation": {}}
            trsfDict["global_transformation"]["translation"] = list(
                trsfDict["global_transformation"]["translation"])
            trsfDict["global_transformation"]["rotation"] = list(
                trsfDict["global_transformation"]["rotation"])
            for k, v in six.iteritems(self._roiDict[roi]["sub_roi"]):
                trsfDict["sub_roi_transformation"].update(
                    {k: v["transformation"]})
                trsfDict["sub_roi_transformation"][k]["translation"] = list(
                    trsfDict["sub_roi_transformation"][k]["translation"])
                trsfDict["sub_roi_transformation"][k]["rotation"] = list(
                    trsfDict["sub_roi_transformation"][k]["rotation"])
            minf = {}
            minfFile = self._outputRoi[roi].fullPath() + ".minf"
            try:
                minf = readMinf(minfFile)[0]
            except:
                pass
            minf.update(trsfDict)
            fd = open(minfFile, 'w')
            print("attributes = ", minf, file=fd)
            fd.close()

        QtGui.qApp.restoreOverrideCursor()
        self._mainDiag.frame.setEnabled(True)
        for k, v in six.iteritems(roiValidities):
            if True in v:
                return

        self._accept()

    def _checkMeshValidity(self, roi):
        meshes = []
        for k, v in six.iteritems(self._roiDict[roi]["sub_roi"]):
            meshes += v["meshes"]

        outsideImageBounds = False
        aImg = self._aImages[self._getSelectedImage()]
        [minImg, maxImg] = aImg.boundingbox()
        for mesh in meshes:
            [minMesh, maxMesh] = self._aMeshes[mesh].boundingbox()
            minMesh = self._previousMotions[mesh].transform(minMesh)
            maxMesh = self._previousMotions[mesh].transform(maxMesh)
            for i in six.moves.xrange(3):
                if maxMesh[i] > maxImg[i] or\
                   minMesh[i] < minImg[i]:
                    outsideImageBounds = True
                    break

        interExists = False
        for i in six.moves.xrange(len(meshes)):
            for mesh in meshes[i + 1:]:
                interExists = aims.SurfaceManip.checkMeshIntersect(
                    self._aimsMeshes[meshes[i]], self._aimsMeshes[mesh])

        return (interExists, outsideImageBounds)

    def _createViews(self):
        self._aViews = []
        orientation = ['Axial', 'Sagittal', 'Coronal']
        cellDict = {'Axial': (1, 0, self._mainDiag.axial),
                    'Sagittal': (0, 1, self._mainDiag.sagittal),
                    'Coronal': (0, 0, self._mainDiag.coronal)}
        for i in range(3):
            newWin = self.a.createWindow(orientation[i], no_decoration=True)
            layout = QtGui.QVBoxLayout(cellDict[orientation[i]][2])
            layout.setSpacing(0)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(newWin.getInternalRep())
            self.a.execute('WindowConfig', windows=[newWin],
                           light={'background': [0., 0., 0., 1.]})
            self._aViews.append(newWin)

    def _getSelectedImage(self):
        try:
            return self._images[self._mainDiag.imageCb.currentIndex()]
        except:
            return None

    def isGlobalModeOn(self):
        return self._globalModeOn

    def isSymmetricModeOn(self):
        return self._symmetricModeOn

    def getSymmetricPlanes(self):
        return self._symmetricPlanes

    def getSelectedRoi(self):
        try:
            return self._inputRoi[self._mainDiag.roiCb.currentIndex()]
        except:
            return None

    def getSelectedSubRoi(self):
        try:
            return self._mainDiag.subRoiList.currentItem().text()
        except:
            return None

    def _updateViews(self):
        try:
            self._aImages[self._currentImage].removeFromWindows(self._aViews)
        except:
            pass
        try:
            for mesh in self._currentMeshes:
                self._currentContourMesh.removeFromWindows(self._aViews)
        except:
            pass

        self._currentImage = self._getSelectedImage()
        if not self._currentImage:
            return

        self._currentRoi = self.getSelectedRoi()
        self._currentMeshes = []
        for subRoi in self._roiDict[self._currentRoi]["sub_roi"].keys():
            try:
                self._currentMeshes += self._roiDict[
                    self._currentRoi]["sub_roi"][subRoi]["meshes"]
            except:
                pass

        if len(self._currentMeshes) == 0:
            return

        self._aImages[self._currentImage].addInWindows(self._aViews)
        self._currentContourMesh = self.a.fusionObjects(
            [self._aMeshes[mesh] for mesh in self._currentMeshes], "Fusion2DMeshMethod")
        self._currentContourMesh.addInWindows(self._aViews)
        self._currentContourMesh.setVoxelSize(
            self._aImages[self._currentImage].VoxelSize())
        self._currentContourMesh.setMaterial(diffuse=[0., 0., 0., 1.])
        self.a.execute(
            'LinkedCursor', window=self._aViews[0], position=self.a.lastPosition())

    def _createMeshes(self):
        self._symmetricPlanes = {}
        self._aimsMeshes = {}
        self._aMeshes = {}
        self._previousMotions = {}
        self._previousGlobalMotions = {}
        self._sideMeshes = {}
        for roi in self._inputRoi:
            aimsRoi = aims.read(roi)
            labels = {}
            for v in aimsRoi.vertices():
                labels.update({v["name"]: int(v["roi_label"])})
            label = 1
            for k, v in six.iteritems(labels):
                imageFile = mktemp(suffix='.nii')
                self._addTemporaryObjects(imageFile)
                aims.write(self._getImageFromRoi(
                    roi, selectedLabel=v), imageFile)
                label += 1
                tmpDir = mkdtemp()
                self._addTemporaryObjects(tmpDir)
                check_call(['AimsMesh', '-i', imageFile,
                                        '-o', os.path.join(tmpDir, "roi"),
                                        '--smooth'])
                meshes = glob.glob(os.path.join(tmpDir, "*gii"))
                self._roiDict[roi]["sub_roi"][k]["meshes"] = meshes
                for mesh in meshes:
                    self._aimsMeshes.update({mesh: aims.read(mesh)})
                    self._aMeshes.update(
                        {mesh: self.a.toAObject(self._aimsMeshes[mesh])})
                    self._previousMotions.update({mesh: aims.Motion()})
            self._previousGlobalMotions.update({roi: aims.Motion()})

            self._defineRoiSides(roi)

            center = self.getCenters(roi)["global"]
            x = center[0]
            y = center[1]
            z = center[2]
            pt1 = [x, y, z]
            pt2 = [x, y + 1, z]
            pt3 = [x, y, z + 1]
            vn = [1., 0., 0.]
            self._symmetricPlanes.update({roi: {"normal": vn, "point": center,
                                                "axial_pts": (pt1, pt2),
                                                "coronal_pts": (pt1, pt3)}})

    def _getImageFromRoi(self, roi, selectedLabel=None):
        image = None
        labels = {}
        roi_it = aims.getRoiIterator(roi)
        image_size = None
        while roi_it.isValid():
            region_name = roi_it.regionName()
            label = labels.setdefault(region_name, len(labels) + 1)
            if label != selectedLabel:
                next(roi_it)
                continue
            mask_it = roi_it.maskIterator()
            if image_size is None:
                image_size = tuple(mask_it.volumeDimension())
                if image is None:
                    voxel_size = tuple(mask_it.voxelSize())
                    image = aims.Volume_S16(*image_size)
                    image.header()['voxel_size'] = voxel_size
                elif image_size != (image.getSizeX(), image.getSizeY(), image.getSizeZ()):
                    raise ValueError('Invalid volume dimension')
            while mask_it.isValid():
                pos = mask_it.value()
                image.setValue(label, *pos)
                next(mask_it)
            next(roi_it)

        return image

    def _defineRoiSides(self, roi):
        self._sideMeshes.update({roi: {}})
        centers = self.getCenters(roi)
        for k, v in six.iteritems(centers["locals"]):
            if v[0] < centers["global"][0]:
                self._sideMeshes[roi].update({k: "right"})
            else:
                self._sideMeshes[roi].update({k: "left"})

    def updateTransformations(self):
        roi = self.getSelectedRoi()

        centers = self.getCenters(roi)
        centers = self.getCenters(roi)

        for k, v in six.iteritems(self._roiDict[roi]["sub_roi"]):
            globalTrsf = self._getTransformation(
                self._roiDict[roi]["global_transformation"],
                                                 centers["global"],
                                                 side=self._sideMeshes[roi][k])
            localTrsf = self._getTransformation(v["transformation"],
                                                centers["locals"][k])
            totalTrsf = localTrsf * globalTrsf
#             totalTrsf = globalTrsf * localTrsf
            motion = self._getMotion(totalTrsf)
            for mesh in v["meshes"]:
                aimsMesh = self._aimsMeshes[mesh]
                if self._previousMotions[mesh] and not self._previousMotions[mesh].isIdentity():
                    aims.SurfaceManip.meshTransform(
                        aimsMesh, self._previousMotions[mesh].inverse())
                aims.SurfaceManip.meshTransform(aimsMesh, motion)
                self._previousMotions.update({mesh: motion})
            for mesh in v["meshes"]:
                self._aMeshes[mesh].setChanged()
                self._aMeshes[mesh].notifyObservers()

    def getCenters(self, roi):
        centers = {"global": None,
                   "locals": {}}
        rightMeshes = []
        leftMeshes = []
        meshes = []
        for k, v in six.iteritems(self._roiDict[roi]["sub_roi"]):
            centers["locals"].update({k: self._getCenter(v["meshes"])})
            meshes += v["meshes"]
            try:
                if self._sideMeshes[roi][k] == "right":
                    rightMeshes += v["meshes"]
                elif self._sideMeshes[roi][k] == "left":
                    leftMeshes += v["meshes"]
            except:
                pass
        centers.update({"global": self._getCenter(meshes)})
        if len(rightMeshes) > 0 and len(leftMeshes) > 0:
            centers.update({"right": self._getCenter(rightMeshes)})
            centers.update({"left": self._getCenter(leftMeshes)})

        return centers

    def _getTransformation(self, transformation, roiCenter, side=None):
        roi = self.getSelectedRoi()

        resultTrsf = self._getRotation(transformation["rotation"])
        resultTrsf[:, 3] = np.asmatrix(transformation["translation"]).T

        rotationSym = None
        if self._symmetricModeOn and side:
            withGap = np.asmatrix(np.identity(4))
            normal = self._symmetricPlanes[roi]["normal"]
            if side == "left":
                gapTranslation = [n * transformation["gap"] for n in normal]
            else:
                gapTranslation = [n * -transformation["gap"] for n in normal]
            gapTranslation = np.array(gapTranslation + [1.])
            withGap[:, 3] = np.asmatrix(gapTranslation).T
            resultTrsf = resultTrsf * withGap
            center = np.asmatrix(np.diag([1, 1, 1, 1]))
            revCenter = np.asmatrix(np.diag([1, 1, 1, 1]))
            center[:, 3] = np.asmatrix(self.getCenters(roi)[side]).T
            revCenter[:, 3] = np.asmatrix(-self.getCenters(roi)[side]).T
            revCenter[3, 3] = 1
            rotationSym = self._getRotation(
                transformation["rotationSym"], side)
            rotationSym = center * rotationSym * revCenter

        center = np.asmatrix(np.diag([1, 1, 1, 1]))
        revCenter = np.asmatrix(np.diag([1, 1, 1, 1]))
        center[:, 3] = np.asmatrix(roiCenter).T
        revCenter[:, 3] = np.asmatrix(-roiCenter).T
        revCenter[3, 3] = 1
        resultTrsf = center * resultTrsf * revCenter
        if rotationSym is not None:
            resultTrsf = resultTrsf * rotationSym

        return resultTrsf

    def _getCenter(self, meshes):
        bmin = None
        bmax = None
        for mesh in meshes:
            bbox = [aims.Point3df(x[:3])
                    for x in self._aMeshes[mesh].boundingbox()]
            if bmin == None:
                bmin = bbox[0]
                bmax = bbox[1]
            else:
                for i in six.moves.xrange(len(bbox[0])):
                    if bbox[0][i] < bmin[i]:
                        bmin[i] = bbox[0][i]
                    if bbox[1][i] > bmax[i]:
                        bmax[i] = bbox[1][i]
        tmp = (bmin + bmax) * 0.5
        center = tmp.list()
        center.append(1)

        return np.array(center)

    def _getRotation(self, rotation, side=None):
        if side == "left":
            rotationRad = rotation * math.pi / 180
        elif side == "right":
            rotationRad = -rotation * math.pi / 180
        else:
            rotationRad = []
            for a in rotation:
                rotationRad.append(a * math.pi / 180)

        if side:
            c1, s1 = np.cos(rotationRad), np.sin(rotationRad)
            c2, s2 = 1.0, 0.0
            c3, s3 = 1.0, 0.0
        else:
            c1, s1 = np.cos(rotationRad[0]), np.sin(rotationRad[0])
            c2, s2 = np.cos(rotationRad[1]), np.sin(rotationRad[1])
            c3, s3 = np.cos(rotationRad[2]), np.sin(rotationRad[2])

        m1 = np.matrix(
              [[c1, -s1, 0, 0],
                [s1,  c1, 0, 0],
                [0,    0, 1, 0],
                [0,    0, 0, 1]])
        m2 = np.matrix(
              [[1,  0,   0, 0],
                [0, c2, -s2, 0],
                [0, s2,  c2, 0],
                [0,  0,   0, 1]])
        m3 = np.matrix(
              [[c3, 0, -s3, 0],
                [0, 1,   0, 0],
                [s3, 0,  c3, 0],
                [0, 0,   0, 1]])
        return m1 * m2 * m3

    def _getMotion(self, transformation):
        return aims.Motion(np.asarray(transformation).flatten())

    def _addTemporaryObjects(self, obj):
        self._temporaryObjects.append(obj)

    def _cleanTemporaryObjects(self):
        for o in self._temporaryObjects:
            try:
                if os.path.isdir(o):
                    shutil.rmtree(o)
                else:
                    os.remove(o)
            except:
                pass

    def _accept(self):
        self._cleanTemporaryObjects()
        self._mainDiag.accept()


class TrsfAction(anatomist.Action):
    _prevX = 0
    _prevY = 0
    _prevPos = None

    def __init__(self, process):
        anatomist.Action.__init__(self)
        self._mainProcess = process

    def setMainProcess(self, process):
        self._mainProcess = process
        self._prevX = 0
        self._prevY = 0
        self._prevPos = None

    def name(self):
        return 'TrsfAction'

    def _pressedCursor(self):
        self.view().aWindow().setCursor(QtCore.Qt.ClosedHandCursor)

    def _releasedCursor(self):
        self.view().aWindow().setCursor(QtCore.Qt.OpenHandCursor)

    def _getPos(self, x, y):
        v = self.view()
        pos = aims.Point3df()
        v.positionFromCursor(x, y, pos)
        return pos

    def _getViewType(self, globx, globy):
        try:
            return self.view().aWindow().viewType()
        except:
            return -1

    def moveTranslation(self, x, y, globx, globy):
        pos = self._getPos(x, y)
        roi = self._mainProcess.getSelectedRoi()
        if self._mainProcess.isGlobalModeOn():
            translation = self._mainProcess._roiDict[
                roi]["global_transformation"]["translation"]
            self._mainProcess._roiDict[roi]\
                                     ["global_transformation"]\
                                     ["translation"] = translation + np.array([pos[0] - self._prevPos[0],
                                                                                pos[1] - self._prevPos[
                                                                                    1],
                                                                                pos[2] - self._prevPos[
                                                                                    2],
                                                                                0.])
        else:
            subRoi = self._mainProcess.getSelectedSubRoi()
            translation = self._mainProcess._roiDict[roi][
                "sub_roi"][subRoi]["transformation"]["translation"]
            self._mainProcess._roiDict[roi]\
                                     ["sub_roi"][subRoi]\
                                     ["transformation"]\
                                     ["translation"] = translation + np.array([pos[0] - self._prevPos[0],
                                                                                pos[1] - self._prevPos[
                                                                                    1],
                                                                                pos[2] - self._prevPos[
                                                                                    2],
                                                                                0.])
        self._mainProcess.updateTransformationUi()
        self._mainProcess.updateTransformations()
        self._prevPos = pos
        self._prevX = x
        self._prevY = y

    def beginTranslation(self, x, y, globx, globy):
        self._prevX = x
        self._prevY = y
        self._prevPos = self._getPos(x, y)
        self._pressedCursor()

    def endTranslation(self, x, y, globx, globy):
        self._releasedCursor()

    def moveRotation(self, x, y, globx, globy):
        pos = self._getPos(x, y)
        roi = self._mainProcess.getSelectedRoi()
        center = self._mainProcess.getCenters(roi)["global"][:-1]
        deltaAngle = 1
        deltaX = x - self._prevX
        deltaY = y - self._prevY
        viewType = self._getViewType(globx, globy)
        rotIndex = -1
        xIndex = -1
        yIndex = -1
        if viewType == 1:
            rotIndex = 0
            xIndex = 0
            yIndex = 1
        elif viewType == 2:
            rotIndex = 1
            xIndex = 1
            yIndex = 2
        elif viewType == 3:
            rotIndex = 2
            xIndex = 0
            yIndex = 2
        else:
            return

        if ( pos[yIndex] > center[yIndex] and deltaX > 0 ) or \
           ( pos[yIndex] < center[yIndex] and deltaX < 0 ) or \
           ( pos[xIndex] < center[xIndex] and deltaY > 0 ) or \
           (pos[xIndex] > center[xIndex] and deltaY < 0):
            deltaAngle *= -1

        roi = self._mainProcess.getSelectedRoi()
        if self._mainProcess.isGlobalModeOn():
            self._mainProcess._roiDict[roi]\
                                     ["global_transformation"]\
                                     ["rotation"][rotIndex] += deltaAngle
        else:
            subRoi = self._mainProcess.getSelectedSubRoi()
            self._mainProcess._roiDict[roi]\
                                     ["sub_roi"][subRoi]\
                                     ["transformation"]\
                                     ["rotation"][rotIndex] += deltaAngle

        self._mainProcess.updateTransformationUi()
        self._mainProcess.updateTransformations()
        self._prevPos = pos
        self._prevX = x
        self._prevY = y

    def beginRotation(self, x, y, globx, globy):
        self._prevX = x
        self._prevY = y
        self._prevPos = self._getPos(x, y)
        self._pressedCursor()

    def endRotation(self, x, y, globx, globy):
        self._releasedCursor()

    def moveGap(self, x, y, globx, globy):
        if not self._mainProcess.isSymmetricModeOn():
            return

        pos = self._getPos(x, y)
        viewType = self._getViewType(globx, globy)
        if viewType != 1 and viewType != 3:
            return

        roi = self._mainProcess.getSelectedRoi()
        rotation = self._mainProcess._roiDict[
            roi]["global_transformation"]["rotation"]
        rotX = rotation[0] * math.pi / 180
        cosRotX, sinRotX = np.cos(rotX), np.sin(rotX)
        prevXRot = self._prevX * cosRotX - self._prevY * sinRotX
        xRot = x * cosRotX - y * sinRotX

        if prevXRot < xRot:
            self._mainProcess._roiDict[roi][
                "global_transformation"]["gap"] += 1
        elif prevXRot > xRot:
            self._mainProcess._roiDict[roi][
                "global_transformation"]["gap"] -= 1

        self._mainProcess.updateTransformationUi()
        self._mainProcess.updateTransformations()
        self._prevPos = pos
        self._prevX = x
        self._prevY = y

    def beginGap(self, x, y, globx, globy):
        self._prevX = x
        self._prevY = y
        self._prevPos = self._getPos(x, y)
        self._pressedCursor()

    def endGap(self, x, y, globx, globy):
        self._releasedCursor()

    def moveRotSym(self, x, y, globx, globy):
        if not self._mainProcess.isSymmetricModeOn():
            return

        pos = self._getPos(x, y)
        roi = self._mainProcess.getSelectedRoi()
        center = self._mainProcess.getCenters(roi)["global"][:-1]
        deltaX = x - self._prevX
        deltaY = y - self._prevY
        deltaAngle = 2
        viewType = self._getViewType(globx, globy)
        rotIndex = -1
        xIndex = -1
        yIndex = -1
        if viewType == 1:
            rotIndex = 0
            xIndex = 0
            yIndex = 1
        else:
            return

        if ( pos[yIndex] > center[yIndex] and deltaX > 0 ) or \
           ( pos[yIndex] < center[yIndex] and deltaX < 0 ) or \
           ( pos[xIndex] < center[xIndex] and deltaY > 0 ) or \
           (pos[xIndex] > center[xIndex] and deltaY < 0):
            deltaAngle *= -1

        self._mainProcess._roiDict[roi]\
                                  ["global_transformation"]\
                                  ["rotationSym"] += deltaAngle

        self._mainProcess.updateTransformationUi()
        self._mainProcess.updateTransformations()
        self._prevPos = pos
        self._prevX = x
        self._prevY = y

    def beginRotSym(self, x, y, globx, globy):
        self._prevX = x
        self._prevY = y
        self._prevPos = self._getPos(x, y)
        self._pressedCursor()

    def endRotSym(self, x, y, globx, globy):
        self._releasedCursor()


class TrsfControl(anatomist.Control):

    def __init__(self, prio=25):
        anatomist.Control.__init__(self, prio, 'TrsfControl')

    def eventAutoSubscription(self, pool):
        self.mouseLongEventSubscribe(
             QtCore.Qt.LeftButton, QtCore.Qt.NoModifier,
             pool.action("TrsfAction").beginTranslation,
             pool.action("TrsfAction").moveTranslation,
             pool.action("TrsfAction").endTranslation, True)
        self.mouseLongEventSubscribe(
             QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier,
             pool.action("TrsfAction").beginRotation,
             pool.action("TrsfAction").moveRotation,
             pool.action("TrsfAction").endRotation, True)
        self.mouseLongEventSubscribe(
             QtCore.Qt.MidButton, QtCore.Qt.NoModifier,
             pool.action("TrsfAction").beginGap,
             pool.action("TrsfAction").moveGap,
             pool.action("TrsfAction").endGap, True)
        self.mouseLongEventSubscribe(
             QtCore.Qt.MidButton, QtCore.Qt.ControlModifier,
             pool.action("TrsfAction").beginRotSym,
             pool.action("TrsfAction").moveRotSym,
             pool.action("TrsfAction").endRotSym, True)


class SymEditControl(anatomist.Control):

    def __init__(self, prio=150):
        anatomist.Control.__init__(self, prio, 'SymEditControl')

    def eventAutoSubscription(self, pool):
        self.mouseLongEventSubscribe(
            QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier,
            pool.action('SymEditAction').startDistance,
            pool.action('SymEditAction').moveDistance,
            pool.action('SymEditAction').stopDistance, True)

    def doAlsoOnSelect(self, actionpool):
        anatomist.Control.doAlsoOnSelect(self, actionpool)
        actionpool.action('SymEditAction').initPositions()

    def doAlsoOnDeselect(self, actionpool):
        anatomist.Control.doAlsoOnDeselect(self, actionpool)
        actionpool.action('SymEditAction').accept()


class SymPlaneChangeTransmitter(QtCore.QObject):
    symPlaneChanged = QtCore.Signal()

    def trigger(self):
        self.symPlaneChanged.emit()


class SymEditAction(anatomist.Action, QtCore.QObject):

    def name(self):
        return 'SymEditAction'

    def __init__(self, process):
        anatomist.Action.__init__(self)
        QtCore.QObject.__init__(self)

        self._mainProcess = process
        self._items = []
        self._startPos = aims.Point3df()
        self._currentPos = None
        self._pt1 = aims.Point3df()
        self._pt2 = aims.Point3df()
        self._blockUpdates = False
        self._mainProcess.symPlaneChangeTransmitter.symPlaneChanged.connect(
            self.symPlaneChanged)

    def setMainProcess(self, process):
        self._mainProcess = process
        self.initPositions()

    def accept(self):
        self.cleanup()

    def symPlaneChanged(self):
        if self._blockUpdates:
            return

        self.updatePositions()

    def cleanup(self):
        self._removeGraphicsView(self.view())

    def update(self):
        self._drawDistanceInGraphicsView(self.view())

    def updateSymmetricPlane(self):
        viewType = self._getViewType()
        if viewType != 1 and viewType != 3:
            return

        roi = self._mainProcess.getSelectedRoi()
        vn = self._mainProcess.getSymmetricPlanes()[roi]["normal"]

        if viewType == 1:
            axialPts = (self._pt1, self._pt2)
            coronalPts = self._mainProcess.getSymmetricPlanes()[
                                                              roi]["coronal_pts"]
        elif viewType == 3:
            axialPts = self._mainProcess.getSymmetricPlanes()[roi]["axial_pts"]
            coronalPts = (self._pt1, self._pt2)

        ab = [axialPts[1][i] - axialPts[0][i] for i in six.moves.xrange(3)]
        cd = [coronalPts[1][i] - coronalPts[0][i] for i in six.moves.xrange(3)]
        vn = [ab[1] * cd[2] - ab[2] * cd[1],
              ab[2] * cd[0] - ab[0] * cd[2],
              ab[0] * cd[1] - ab[1] * cd[0]]
        n = math.sqrt(vn[0] * vn[0] + vn[1] * vn[1] + vn[2] * vn[2])
        vn = [v / n for v in vn]

        self._mainProcess.getSymmetricPlanes(
        )[roi].update({"normal": [vn[0], vn[1], vn[2]],
                                                        "point": np.array([axialPts[0][0], axialPts[0][1], axialPts[0][2], 1.]),
                                                        "axial_pts": axialPts,
                                                        "coronal_pts": coronalPts})

        self._blockUpdates = True
        self._mainProcess.symPlaneChangeTransmitter.trigger()
        self._blockUpdates = False

    def startDistance(self, x, y, globx, globy):
        winSize = self.view().aWindow().size()
        self._updateCursors()
        self._startPos = aims.Point3df()
        self.view().positionFromCursor(x, y, self._startPos)
        self._showGraphicsView(self.view())

    def moveDistance(self, x, y, globx, globy):
        self._currentPos = aims.Point3df()
        self.view().positionFromCursor(x, y, self._currentPos)
        winSize = self.view().aWindow().size()
        center = (winSize.width() * 0.5, winSize.height() * 0.5)
        if y < center[1]:
            self._pt1 = self._currentPos
            self._updateCursors(True, False)
        else:
            self._pt2 = self._currentPos
            self._updateCursors(False, True)

        self.update()
        self.updateSymmetricPlane()

    def stopDistance(self, x, y, globx, globy):
        self.update()

    def _getViewType(self):
        try:
            return self.view().aWindow().viewType()
        except:
            return -1

    def _graphicsViewOnWindow(self, view):
        glw = view.qglWidget()
        parent = glw.parent()
        if isinstance(parent, QtGui.QGraphicsView):
            return parent
        gv = glw.findChild(QtGui.QGraphicsView)
        if gv is not None:
            return gv
        l = QtGui.QVBoxLayout()
        glw.setLayout(l)
        gv = QtGui.QGraphicsView(glw)
        l.addWidget(gv, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        gv.setFrameStyle(QtGui.QFrame.NoFrame)
        return gv

    def _showGraphicsView(self, view):
        gv = self._graphicsViewOnWindow(view)
        gv.show()

    def _removeGraphicsView(self, view):
        gv = self._graphicsViewOnWindow(view)
        scene = gv.scene()
        if scene:
            for item in self._items:
                scene.removeItem(item)
        self._items = []
        self._segments = []
        if view.qglWidget().parent() is not gv:
            gv.hide()

    def _updateCursors(self, startChanged=True, endChanged=True):
        if startChanged:
            self.view().cursorFromPosition(self._pt1, self._startCursor)
        if endChanged:
            self.view().cursorFromPosition(self._pt2, self._endCursor)

        winSize = self.view().aWindow().size()
        if self._endCursor[0] - self._startCursor[0] == 0:
            if startChanged:
                self._startCursor[1] = 0.
            if endChanged:
                self._endCursor[1] = winSize.height()
        else:
            slope = (self._endCursor[1] - self._startCursor[1]) / (
                self._endCursor[0] - self._startCursor[0])
            intercept = self._endCursor[1] - slope * self._endCursor[0]
            if startChanged:
                self._startCursor[1] = 0
                self._startCursor[0] = -intercept / slope
            if endChanged:
                self._endCursor[1] = winSize.height()
                self._endCursor[0] = (self._endCursor[1] - intercept) / slope

    def _winSliderChanged(self, value):
        self.updatePositions()

    def updatePositions(self):
        viewType = self._getViewType()
        if viewType != 1 and viewType != 3:
            return

        roi = self._mainProcess.getSelectedRoi()
        vn = self._mainProcess.getSymmetricPlanes()[roi]["normal"]
        pt = self._mainProcess.getSymmetricPlanes()[roi]["point"]
        a = vn[0]
        b = vn[1]
        c = vn[2]
        d = (a * pt[0] + b * pt[1] + c * pt[2]) * -1

        initX = 10
        line1 = [0, 0, 0]
        line2 = [0, 0, 0]

        sliderValue = self.view().aWindow().getSliceSlider().value()

        if viewType == 1:
            if b == 0:
                line1 = [-(d + sliderValue * c) / a, -initX, sliderValue]
                line2 = [-(d + sliderValue * c) / a, initX, sliderValue]
            elif a == 0:
                line1 = [-initX, -(d + sliderValue * c) / b, sliderValue]
                line2 = [initX, -(d + sliderValue * c) / b, sliderValue]
            else:
                line1 = [
                    initX, -(d + a * initX + sliderValue * c) / b, sliderValue]
                line2 = [
                    -initX, -(d + a * (-initX) + sliderValue * c) / b, sliderValue]
        else:
            if c == 0:
                line1 = [-(d + sliderValue * b) / a, sliderValue, -initX]
                line2 = [-(d + sliderValue * b) / a, sliderValue, initX]
            elif a == 0:
                line1 = [-initX, sliderValue, -(d + sliderValue * b) / c]
                line2 = [initX, sliderValue, -(d + sliderValue * b) / c]
            else:
                line1 = [initX, sliderValue, -(
                    d + a * initX + sliderValue * b) / c]
                line2 = [-initX, sliderValue, -(
                    d + a * (-initX) + sliderValue * b) / c]

        self._pt1 = aims.Point3df(line1)
        self._pt2 = aims.Point3df(line2)

        self._startCursor = aims.Point3df()
        self._endCursor = aims.Point3df()

        self._updateCursors(True, True)
        self.update()

    def initPositions(self):
        viewType = self._getViewType()
        if viewType != 1 and viewType != 3:
            return

        try:
            self.view().aWindow().getSliceSlider().valueChanged.disconnect(
                self._winSliderChanged)
        except:
            pass

        try:
            self.view().aWindow().getSliceSlider().valueChanged.connect(
                self._winSliderChanged)
        except:
            pass

        self.updatePositions()

    def _drawDistanceInGraphicsView(self, view):
        viewType = self._getViewType()
        if viewType != 1 and viewType != 3:
            return

        gv = self._graphicsViewOnWindow(view)
        scene = gv.scene()

        paintpen = QtGui.QPen(QtGui.QColor(0, 0, 0))
        black_color = QtGui.QColor(0, 0, 0)
        white_color = QtGui.QColor(255, 255, 255)
        red_color = QtGui.QColor(255, 0, 0)

        if scene is None:
            scene = QtGui.QGraphicsScene(gv)
            gv.setScene(scene)

        for item in self._items:
            scene.removeItem(item)

        self._items = []

        roi = self._mainProcess.getSelectedRoi()

        startX = int(self._startCursor[0])
        startY = int(self._startCursor[1])
        endX = int(self._endCursor[0])
        endY = int(self._endCursor[1])

        distanceLine = QtGui.QGraphicsLineItem(startX, startY, endX, endY)
        color = QtGui.QColor(255, 255, 255)
        distanceLine.setPen(QtGui.QPen(color))
        scene.addItem(distanceLine)
        self._items.append(distanceLine)

        diameter = 15
        startDot = QtGui.QGraphicsEllipseItem(
            startX - diameter * 0.5, startY - diameter * 0.5, diameter, diameter, distanceLine)
        color = QtGui.QColor(255, 0, 0)
        startDot.setPen(QtGui.QPen(color))
        startDot.setBrush(QtGui.QBrush(color))
        endDot = QtGui.QGraphicsEllipseItem(
            endX - diameter * 0.5, endY - diameter * 0.5, diameter, diameter, distanceLine)
        color = QtGui.QColor(255, 0, 0)
        endDot.setPen(QtGui.QPen(color))
        endDot.setBrush(QtGui.QBrush(color))
