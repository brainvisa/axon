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

from __future__ import absolute_import
from brainvisa.processing.qtgui.neuroProcessesGUI import mainThreadActions
from soma.qt_gui.qtThread import MainThreadLife
import anatomist.cpp as anatomist
from anatomist.cpp.paletteEditor import PaletteEditor
import anatomist.direct.api as ana
from brainvisa.configuration.neuroConfig import iconPath, uiPath
from soma import aims
from soma.path import locate_file
from soma.qt_gui.qt_backend import QtCore, QtGui, uic
import numpy as np
import math
from tempfile import mkstemp
from soma.subprocess import check_call
import os
import six
from six.moves import range


def manual_registration(image1, image2, context=None):
    _mw = mainThreadActions().call(_manual_registration_on_gui_thread,
                                   image1,
                                   image2,
                                   context)
    mw = MainThreadLife(_mw)
    return [mw]


def _manual_registration_on_gui_thread(image1, image2,
                                       context):
    manualReg = ManualRegistration(image1, image2,
                                   parent=context)
    mw = manualReg.display()
    return mw


class ManualRegistration(object):

    def __init__(self, movingImage, fixedImage, parent):
        self._movingImage = movingImage
        self._fixedImage = fixedImage
        self._defaultMixingRate = 50.

    def display(self):
        """
        Launches the manual registration display.
        """
        self._anatomist = ana.Anatomist('-b')
        try:
            self._anatomist.config()['setAutomaticReferential'] = 0
        except Exception:
            pass
        self._loadData()
        self._loadUi()
        self._createViews()
        self._addInViews()
        self._addImageWidgets()
        self._init3dCursor()
        self._updateControlMode()
        self._transformationChanged()
        self._mainDiag.showMaximized()
        self._mainDiag.exec()
        self._clear()

    def _clear(self):
        """
        Clears all data on exit.
        """
        for v in self._aViewButtons:
            del v
        for v in self._aViews:
            v.removeObjects(v.objects)
            del v
        self._anatomist.deleteObjects(
            list(self._aImages.values()) + [self._fusion, self._winGroup])
        for el in self._spinBoxTimers.values():
            del el
        self._mainDiag.close()
        del self._mainDiag

    def _loadData(self):
        """
        Loads image data and sets the LUT.
        """
        self._aImages = {}
        for img in [self._fixedImage, self._movingImage]:
            aimsImg = aims.read(img)
            aImg = self._anatomist.loadObject(img)
            aImg.attributed()["volumeInterpolation"] = 0
            try:
                if aimsImg.header()["modality"] == "PT":
                    aImg.setPalette('Rainbow', minVal=0, maxVal=1)
                elif aimsImg.header()["modality"] == "NM":
                    aImg.setPalette('French', minVal=0, maxVal=1)
            except Exception:
                pass
            self._aImages.update({img: aImg})

    def _loadUi(self):
        """
        Loads the UI and sets the connections.
        """
        self._mainDiag = uic.loadUi(
            locate_file("manualRegistration.ui", uiPath))
        self._mainDiag.setWindowTitle("Manual registration")

        palette = self._mainDiag.palette()
        palette.setColor(
            self._mainDiag.backgroundRole(), QtGui.QColor(255, 255, 255))
        self._mainDiag.setPalette(palette)

        self._previousTranslationValues = {}
        self._spinBoxTimers = {}
        translationSp = [
            self._mainDiag.xSp, self._mainDiag.ySp, self._mainDiag.zSp]
        rotationSp = [self._mainDiag.axialSp,
                      self._mainDiag.sagittalSp, self._mainDiag.coronalSp]
        slots = {}
        for sp in translationSp:
            slots.update({sp: self._translationChanged})
            self._previousTranslationValues.update({sp: 0.})
        for sp in rotationSp:
            slots.update({sp: self._rotationChanged})
            self._previousTranslationValues.update({sp: 0.})
        slots.update({self._mainDiag.scaleSp: self._scaleChanged})
        self._previousTranslationValues.update({self._mainDiag.scaleSp: 1.})

        for sp in translationSp + rotationSp + [self._mainDiag.scaleSp]:
            sp.valueChanged.connect(self._spinChanged)
            self._spinBoxTimers.update({sp: QtCore.QTimer()})
            self._spinBoxTimers[sp].setInterval(1)
            self._spinBoxTimers[sp].setSingleShot(True)
            self._spinBoxTimers[sp].timeout.connect(slots[sp])

        self._mainDiag.alignCentersBt.clicked.connect(self._alignCenters)
        self._mainDiag.goToRotationCenterBt.clicked.connect(
            self._goToRotationCenter)
        self._mainDiag.setRotationCenterBt.clicked.connect(
            self._setRotationCenter)
        self._mainDiag.focusBt.clicked.connect(self._focusViews)
        self._mainDiag.undoBt.clicked.connect(self._undo)
        self._mainDiag.redoBt.clicked.connect(self._redo)
        self._mainDiag.resetBt.clicked.connect(self._resetTransform)
        self._mainDiag.control3dRb.clicked.connect(self._updateControlMode)
        self._mainDiag.trsfControlRb.clicked.connect(self._updateControlMode)
        self._mainDiag.saveBt.clicked.connect(self._saveTransformationClicked)
        self._mainDiag.resampleBt.clicked.connect(self._resampleImageClicked)
        self._mainDiag.closeBt.clicked.connect(self._mainDiag.accept)

    def _addImageWidgets(self):
        """
        Adds the image widgets: palette editor and fusion mixer.
        """
        paletteFilter = ['B-W LINEAR', 'Blue-Green-Red-Yellow',
                         'Blue-Red2', 'French', 'RAINBOW',
                         'RED TEMPERATURE', 'Rainbow2']
        paletteEditor = PaletteEditor(self._aImages[self._fixedImage],
                                      palette_filter=paletteFilter,
                                      title='Fixed image')
        layout = QtGui.QVBoxLayout(self._mainDiag.fixedImagePalette)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(paletteEditor)
        paletteEditor = PaletteEditor(self._aImages[self._movingImage],
                                      palette_filter=paletteFilter,
                                      title='Moving image')
        layout = QtGui.QVBoxLayout(self._mainDiag.movingImagePalette)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(paletteEditor)

        self._mainDiag.mixingRateSlider.valueChanged.connect(
            self._mixingRateChanged)
        self._mainDiag.mixingRateSlider.setValue(self._defaultMixingRate)

    def _mixingRateChanged(self, value):
        """
        Updates the texturing parameters according to the new value.
        :param int value:
            The new value.
        """
        self._mainDiag.mixingRateLabel.setText("%d" % int(value) + "%")
        self._anatomist.execute(
            'TexturingParams', objects=[self._fusion], texture_index=1,
                                rate=float(value) / 100)

    def _createViews(self):
        """
        Creates the image views
        """
        self._aViews = []
        self._aViewButtons = []
        orientation = ['Axial', 'Sagittal', 'Coronal']
        cellDict = {'Axial': (1, 0, self._mainDiag.axial, '_viewBtAxial'),
                    'Sagittal': (0, 1, self._mainDiag.sagittal, '_viewBtSagittal'),
                    'Coronal': (0, 0, self._mainDiag.coronal, '_viewBtCoronal')}
        for i in range(3):
            newWin = self._anatomist.createWindow(
                orientation[i], no_decoration=True)
            layout = QtGui.QVBoxLayout(cellDict[orientation[i]][2])
            layout.setSpacing(0)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(newWin.getInternalRep())
            self._anatomist.execute('WindowConfig', windows=[newWin],
                                    light={'background': [0., 0., 0., 1.]})
            self._aViews.append(newWin)
            trsfAction = newWin.view().controlSwitch().getAction('Transformer')
            trsfAction.toggleDisplayInfo()
            viewBt = ViewButtons(
                newWin.view(), orientation[i], self._viewBtClicked)
            self._aViewButtons.append(viewBt)

        for ac in self._allActions():
            ac.transformationChanged.connect(self._transformationChanged)

        self._winGroup = self._anatomist.linkWindows(self._aViews)

    def _addInViews(self):
        """
        Creates the image fusion and adds it to the views
        """
        self._fusion = self._anatomist.fusionObjects(
            [self._aImages[self._fixedImage], self._aImages[self._movingImage]], 'Fusion2DMethod')
        self._fusion.addInWindows(self._aViews)
        self._anatomist.execute(
            'TexturingParams', objects=[self._fusion], texture_index=1,
                                rate=float(self._defaultMixingRate) / 100)
        self._winGroup.setSelection([self._aImages[self._movingImage]])
        bBox = [aims.Point3df(x[:3])
                for x in self._aImages[self._movingImage].boundingbox()]
        center = (bBox[1] - bBox[0]) * 0.5
        for v in self._aViews:
            v.focusView()
            v.view().setRotationCenter(center)

    def _transformationChanged(self):
        """
        Updates the UI according to the current tranformation.
        """
        trsfAction = self._aViews[
            0].view().controlSwitch().getAction('Transformer')
        mot = aims.Motion()
        trsfAction.getCurrentMotion(mot)
        translation = mot.translation()
        rot = mot.rotation()
        scale = math.sqrt(rot.value(0, 0) * rot.value(0, 0) +
                          rot.value(0, 1) * rot.value(0, 1) +
                          rot.value(0, 2) * rot.value(0, 2))
        rotX = math.atan2(rot.value(2, 1) / scale, rot.value(2, 2) / scale)
        rotY = -np.arcsin(rot.value(2, 0))
        rotZ = math.atan2(rot.value(1, 0) / scale, rot.value(0, 0) / scale)
        rotationXYZ = (
            math.degrees(rotZ), math.degrees(rotX), math.degrees(rotY))

        translationSp = [
            self._mainDiag.xSp, self._mainDiag.ySp, self._mainDiag.zSp]
        for i, sp in enumerate(translationSp):
            sp.blockSignals(True)
            sp.setValue(translation[i])
            self._previousTranslationValues.update({sp: translation[i]})
            sp.blockSignals(False)

        rotationSp = [self._mainDiag.axialSp,
                      self._mainDiag.sagittalSp, self._mainDiag.coronalSp]
        for i, sp in enumerate(rotationSp):
            sp.blockSignals(True)
            sp.setValue(rotationXYZ[i])
            self._previousTranslationValues.update({sp: rotationXYZ[i]})
            sp.blockSignals(False)

        self._mainDiag.scaleSp.blockSignals(True)
        self._mainDiag.scaleSp.setValue(scale)
        self._previousTranslationValues.update({self._mainDiag.scaleSp: scale})
        self._mainDiag.scaleSp.blockSignals(False)

        self._mainDiag.undoBt.setEnabled(trsfAction.undoable())
        self._mainDiag.redoBt.setEnabled(trsfAction.redoable())
        self._mainDiag.saveBt.setEnabled(not mot.isIdentity())
        self._mainDiag.resampleBt.setEnabled(not mot.isIdentity())

    def _spinChanged(self, value):
        """
        Launches spinbox timers.
        """
        self._spinBoxTimers[self._mainDiag.sender()].stop()
        self._spinBoxTimers[self._mainDiag.sender()].start()

    def _translationChanged(self):
        """
        Updates the translation of the transformation according to the UI.
        """
        trsf = anatomist.Transformation(None, None)
        trsfAction = self._aViews[
            0].view().controlSwitch().getAction('Transformer')
        trsfAction.selectTransformations(trsfAction.tadView().aWindow())
        translationSp = [
            self._mainDiag.xSp, self._mainDiag.ySp, self._mainDiag.zSp]
        for i, sp in enumerate(translationSp):
            trsf.SetTranslation(
                i, sp.value() - self._previousTranslationValues[sp])
        trsfAction.setTransformData(trsf, False, True)
        translationSp = [
            self._mainDiag.xSp, self._mainDiag.ySp, self._mainDiag.zSp]
        for i, sp in enumerate(translationSp):
            self._previousTranslationValues.update({sp: sp.value()})

    def _rotationChanged(self):
        """
        Updates the rotation of the transformation according to the UI.
        """
        if self._mainDiag.sender() == self._spinBoxTimers[self._mainDiag.axialSp]:
            index = 0
            sp = self._mainDiag.axialSp
        elif self._mainDiag.sender() == self._spinBoxTimers[self._mainDiag.sagittalSp]:
            index = 1
            sp = self._mainDiag.sagittalSp
        elif self._mainDiag.sender() == self._spinBoxTimers[self._mainDiag.coronalSp]:
            index = 2
            sp = self._mainDiag.coronalSp
        else:
            return

        trsfAction = self._aViews[
            index].view().controlSwitch().getAction('Transformer')
        trsfAction.selectTransformations(trsfAction.tadView().aWindow())
        axis = self._aViews[index].sliceQuaternion().transformInverse(
            aims.Point3df(0, 0, -1))
        angle = sp.value() - self._previousTranslationValues[sp]
        angle = angle * math.pi / 180
        q = aims.Quaternion()
        q.fromAxis(axis, angle)
        q.norm()
        trsf = anatomist.Transformation(None, None)
        trsf.setQuaternion(q.inverse())
        rotationCenter = self._aViews[index].view().rotationCenter()
        rotationCenter -= trsf.transform(rotationCenter)
        trsf.SetTranslation(0, rotationCenter[0])
        trsf.SetTranslation(1, rotationCenter[1])
        trsf.SetTranslation(2, rotationCenter[2])
        trsfAction.setTransformData(trsf, False, True)
        self._previousTranslationValues.update({sp: sp.value()})

    def _scaleChanged(self):
        """
        Updates the scale of the transformation according to the UI.
        """
        trsfAction = self._aViews[
            0].view().controlSwitch().getAction('Transformer')
        trsfAction.selectTransformations(trsfAction.tadView().aWindow())
        rotationCenter = self._aViews[0].view().rotationCenter()
        scale = self._mainDiag.scaleSp.value()
        prevScale = self._previousTranslationValues[self._mainDiag.scaleSp]
        if scale == 0.:
            self._mainDiag.scaleSp.blockSignals(True)
            self._mainDiag.scaleSp.setValue(prevScale)
            self._mainDiag.scaleSp.blockSignals(False)
            return

        scale /= prevScale
        trsf = anatomist.Transformation(None, None)
        trsf.SetRotation(0, 0, scale)
        trsf.SetRotation(1, 1, scale)
        trsf.SetRotation(2, 2, scale)
        trsf.SetTranslation(0, rotationCenter[0] * (1. - scale))
        trsf.SetTranslation(1, rotationCenter[1] * (1. - scale))
        trsf.SetTranslation(2, rotationCenter[2] * (1. - scale))
        trsfAction.setTransformData(trsf, False, True)
        self._previousTranslationValues.update(
            {self._mainDiag.scaleSp: self._mainDiag.scaleSp.value()})

    def _alignCenters(self):
        """
        Updates the transformation in order to align image centers.
        """
        trsfAction = self._aViews[
            0].view().controlSwitch().getAction('Transformer')
        trsfAction.selectTransformations(trsfAction.tadView().aWindow())
        currentTrsf = trsfAction.mainTransformation()
        movingBBox = [aims.Point3df(x[:3])
                      for x in self._aImages[self._movingImage].boundingbox()]
        fixedBBox = [aims.Point3df(x[:3])
                     for x in self._aImages[self._fixedImage].boundingbox()]
        movingCenter = (movingBBox[1] - movingBBox[0]) * 0.5
        movingCenter = currentTrsf.transform(movingCenter)
        fixedCenter = (fixedBBox[1] - fixedBBox[0]) * 0.5
        translation = fixedCenter - movingCenter
        trsf = anatomist.Transformation(None, None)
        for i in six.moves.xrange(3):
            trsf.SetTranslation(i, translation[i])
        trsfAction.setTransformData(trsf, False, True)
        for v in self._aViews:
            v.focusView()
        self._goToRotationCenter()

    def _resetTransform(self):
        """
        Resets the tranformation.
        """
        self._allActions()[0].resetTransform()

    def _goToRotationCenter(self):
        """
        Sets the 3D cursor to the rotation center coordinates.
        """
        rotationCenter = self._aViews[0].view().rotationCenter()
        self._anatomist.execute(
            'LinkedCursor', window=self._aViews[0], position=rotationCenter)

    def _setRotationCenter(self):
        """
        Sets the rotation center with the 3D cursor coordinates.
        """
        position = self._aViews[0].getPosition()
        for v in self._aViews:
            v.view().setRotationCenter(position)
            v.refreshNow()

    def _focusViews(self):
        """
        Updates the focus of the views.
        """
        rotationCenter = self._aViews[0].view().rotationCenter()
        for v in self._aViews:
            v.focusView()

    def _undo(self):
        """
        Undo the last transformation.
        """
        trsfAction = self._aViews[
            0].view().controlSwitch().getAction('Transformer')
        trsfAction.undo()

    def _redo(self):
        """
        Redo the last transformation.
        """
        trsfAction = self._aViews[
            0].view().controlSwitch().getAction('Transformer')
        trsfAction.redo()

    def _flipLR(self):
        """
        Updates the transformation in order to X flip the image (left/right).
        """
        self._flip(0)

    def _flipAP(self):
        """
        Updates the transformation in order to Y flip the image (anterior/posterior).
        """
        self._flip(1)

    def _flipUD(self):
        """
        Updates the transformation in order to Z flip the image (up/down).
        """
        self._flip(2)

    def _flip(self, index):
        """
        Updates the transformation in order to flip the image.
        """
        trsf = anatomist.Transformation(None, None)
        trsfAction = self._aViews[
            0].view().controlSwitch().getAction('Transformer')
        trsfAction.selectTransformations(trsfAction.tadView().aWindow())
        mat = np.identity(4)
        mat[index][index] = -1
        trsf.motion().fromMatrix(mat)
        rotationCenter = self._aViews[0].view().rotationCenter()
        rotationCenter -= trsf.transform(rotationCenter)
        trsf.SetTranslation(0, rotationCenter[0])
        trsf.SetTranslation(1, rotationCenter[1])
        trsf.SetTranslation(2, rotationCenter[2])
        trsfAction.setTransformData(trsf, False, True)

    def _viewBtClicked(self, orientation, action):
        """
        Updates the UI according to the view button clicked.
        """
        if (orientation == 'Axial' and action == 'up') or \
           (orientation == 'Sagittal' and action == 'left'):
            self._mainDiag.ySp.setValue(
                self._mainDiag.ySp.value() - self._mainDiag.ySp.singleStep())
        elif (orientation == 'Axial' and action == 'down') or \
             (orientation == 'Sagittal' and action == 'right'):
            self._mainDiag.ySp.setValue(
                self._mainDiag.ySp.value() + self._mainDiag.ySp.singleStep())
        elif (orientation == 'Axial' and action == 'left') or \
             (orientation == 'Coronal' and action == 'left'):
            self._mainDiag.xSp.setValue(
                self._mainDiag.xSp.value() - self._mainDiag.xSp.singleStep())
        elif (orientation == 'Axial' and action == 'right') or \
             (orientation == 'Coronal' and action == 'right'):
            self._mainDiag.xSp.setValue(
                self._mainDiag.xSp.value() + self._mainDiag.xSp.singleStep())
        elif (orientation == 'Sagittal' and action == 'up') or \
             (orientation == 'Coronal' and action == 'up'):
            self._mainDiag.zSp.setValue(
                self._mainDiag.zSp.value() - self._mainDiag.zSp.singleStep())
        elif (orientation == 'Sagittal' and action == 'down') or \
             (orientation == 'Coronal' and action == 'down'):
            self._mainDiag.zSp.setValue(
                self._mainDiag.zSp.value() + self._mainDiag.zSp.singleStep())
        elif (orientation == 'Axial' and action == 'rotation_left'):
            self._mainDiag.axialSp.setValue(
                self._mainDiag.axialSp.value() - self._mainDiag.axialSp.singleStep())
        elif (orientation == 'Axial' and action == 'rotation_right'):
            self._mainDiag.axialSp.setValue(
                self._mainDiag.axialSp.value() + self._mainDiag.axialSp.singleStep())
        elif (orientation == 'Sagittal' and action == 'rotation_left'):
            self._mainDiag.sagittalSp.setValue(
                self._mainDiag.sagittalSp.value() - self._mainDiag.sagittalSp.singleStep())
        elif (orientation == 'Sagittal' and action == 'rotation_right'):
            self._mainDiag.sagittalSp.setValue(
                self._mainDiag.sagittalSp.value() + self._mainDiag.sagittalSp.singleStep())
        elif (orientation == 'Coronal' and action == 'rotation_left'):
            self._mainDiag.coronalSp.setValue(
                self._mainDiag.coronalSp.value() + self._mainDiag.coronalSp.singleStep())
        elif (orientation == 'Coronal' and action == 'rotation_right'):
            self._mainDiag.coronalSp.setValue(
                self._mainDiag.coronalSp.value() - self._mainDiag.coronalSp.singleStep())
        elif (orientation == 'Axial' and action == 'flip_horizontal') or \
             (orientation == 'Coronal' and action == 'flip_horizontal'):
            self._flipLR()
        elif (orientation == 'Axial' and action == 'flip_vertical') or \
             (orientation == 'Sagittal' and action == 'flip_horizontal'):
            self._flipAP()
        elif (orientation == 'Coronal' and action == 'flip_vertical') or \
             (orientation == 'Sagittal' and action == 'flip_vertical'):
            self._flipUD()

    def _init3dCursor(self):
        """
        Inits the 3D cursor coordinates.
        """
        aImg = self._aImages[self._fixedImage]
        bbox = [aims.Point3df(x[:3])
                for x in aImg.boundingbox()]
        position = (bbox[1] - bbox[0]) * 0.5
        t = self._anatomist.getTransformation(aImg.getReferential(),
                                              self._aViews[0].getReferential())
        if t:
            position = t.transform(position)
        self._anatomist.execute(
            'LinkedCursor', window=self._aViews[0], position=position)

    def _updateControlMode(self):
        """
        Updates the view control mode.
        """
        if self._mainDiag.control3dRb.isChecked():
            self._anatomist.setWindowsControl(
                windows=self._aViews, control='Default 3D control')
        elif self._mainDiag.trsfControlRb.isChecked():
            self._anatomist.setWindowsControl(
                windows=self._aViews, control='TransformControl')

    def _saveTransformationClicked(self):
        """
        Launches the browser to select the file where to save the transformation.
        """
        saveFilename = QtGui.QFileDialog.getSaveFileName(
            self._mainDiag, caption='Save transformation as...',
            directory=os.path.dirname(self._movingImage),
            filter='Transformation file (*.trm)',
            options=QtGui.QFileDialog.DontUseNativeDialog)
        if saveFilename == "" or saveFilename is None:
            return
        self._saveTransformation(saveFilename)

    def _saveTransformation(self, outputFile):
        """
        Saves the transformation.
        """
        trsfAction = self._aViews[
            0].view().controlSwitch().getAction('Transformer')
        mot = aims.Motion()
        trsfAction.getCurrentMotion(mot)
        aims.write(mot, outputFile)

    def _resampleImageClicked(self):
        """
        Resamples the moving image according to the transformation.
        """
        saveFilename = QtGui.QFileDialog.getSaveFileName(
            self._mainDiag, caption='Save resample image as...',
            directory=os.path.dirname(self._movingImage),
            filter='NIfTI-1 image file (*.nii)',
            options=QtGui.QFileDialog.DontUseNativeDialog)
        if saveFilename == "" or saveFilename is None:
            return
        tmpTrsf = mkstemp()[1]
        self._saveTransformation(tmpTrsf)
        check_call(['AimsApplyTransform',
                    '-i', self._movingImage, '-o', saveFilename,
                    '-m', tmpTrsf, '-r', self._fixedImage])

    def _allActions(self, view=None):
        """
        Gets all control actions.
        :param AWindow view:
            The selected view.
        :returns:
            All view control actions.
        """
        if view == None:
            views = self._aViews
        else:
            views = [view]

        actionNames = (
            'Transformer', 'PlanarTransformer', 'TranslaterAction', 'ResizerAction')
        actions = []
        for v in views:
            for ac in actionNames:
                actions.append(v.view().controlSwitch().getAction(ac))

        return actions


class ViewButtons(object):

    """
    Builds a group of control buttons to add on an image view.
    """

    def __init__(self, view, orientation, slot):
        self._items = []
        self._view = view
        self._orientation = orientation
        self._slot = slot
        self._createButtons()

    def show(self):
        """
        Shows the view buttons.
        """
        self._graphicsViewOnWindow().show()

    def hide(self):
        """
        Hides the view buttons.
        """
        self._graphicsViewOnWindow().hide()

    def buttons(self):
        """
        Gets all the buttons.
        :returns:
            All the buttons.
        """
        return list(self._buttons.values())

    def _graphicsViewOnWindow(self):
        """
        Gets the QGraphicsView instance.
        :returns:
            The QGraphicsView instance.
        """
        glw = self._view.qglWidget()
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

    def _removeGraphicsView(self):
        """
        Removes all items from the scene.
        """
        gv = self._graphicsViewOnWindow()
        scene = gv.scene()
        if scene:
            for item in self._items:
                scene.removeItem(item)
                del item
        self._items = []
        if view.qglWidget().parent() is not gv:
            gv.hide()

    def _createButtons(self):
        """
        Creates the view buttons.
        """
        gv = self._graphicsViewOnWindow()
        scene = gv.scene()

        if scene is None:
            scene = QtGui.QGraphicsScene(gv)
            gv.setScene(scene)

        scene.changed.connect(self._update)

        self._buttons = {}

        self._rigidFrame = QtGui.QFrame()
        self._rigidFrame.setGeometry(QtCore.QRect(0, 0, 54, 36))
        self._rigidFrame.setStyleSheet("background: transparent; border: none")
        gLay = QtGui.QGridLayout(self._rigidFrame)
        gLay.setContentsMargins(0, 0, 0, 0)
        gLay.setSpacing(0)
        proxy = scene.addWidget(
            self._rigidFrame, QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        tr = proxy.transform()
        tr.translate(10, 10)
        proxy.setTransform(tr)

        index = 0
        btList = ('rotation_left', 'up',
                  'rotation_right', 'left', 'down', 'right')
        for btName in btList:
            bt = QtGui.QToolButton()
            bt.setAutoRepeat(True)
            bt.clicked[()].connect(lambda orientation=self._orientation,
                                   action=btName: self._slot(orientation, action))
            bt.setText(btName)
            self._buttons.update({btName: bt})
            bt.setIcon(
                QtGui.QIcon(locate_file(btName + "_arrow_64x64.png", iconPath)))
            bt.setIconSize(QtCore.QSize(18, 18))
            bt.setAutoRaise(True)
            bt.setStyleSheet("background: transparent; border: none")
            gLay.addWidget(bt, index / 3, index % 3)
            index += 1

        self._flipFrame = QtGui.QFrame()
        self._flipFrame.setStyleSheet("background: transparent; border: none")
        hLay = QtGui.QHBoxLayout(self._flipFrame)
        hLay.setContentsMargins(0, 0, 0, 0)
        hLay.setSpacing(0)
        proxy = scene.addWidget(
            self._flipFrame, QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        tr = proxy.transform()
        tr.translate(10, 10)
        proxy.setTransform(tr)

        btList = ('flip_horizontal', 'flip_vertical')
        for btName in btList:
            bt = QtGui.QToolButton()
            bt.setAutoRepeat(True)
            bt.clicked[()].connect(lambda orientation=self._orientation,
                                   action=btName: self._slot(orientation, action))
            bt.setText(btName)
            self._buttons.update({btName: bt})
            bt.setIcon(
                QtGui.QIcon(locate_file(btName + "_64x64.png", iconPath)))
            bt.setIconSize(QtCore.QSize(32, 32))
            bt.setAutoRaise(True)
            bt.setStyleSheet("background: transparent; border: none")
            hLay.addWidget(bt)
            index += 1

    def _update(self):
        """
        Updates the flip frame geometry.
        """
        gv = self._graphicsViewOnWindow()
        scene = gv.scene()
        self._flipFrame.setGeometry(
            QtCore.QRect(
                scene.sceneRect().right() -
                                80, scene.sceneRect().bottom() - 50,
                                                 64, 32))
