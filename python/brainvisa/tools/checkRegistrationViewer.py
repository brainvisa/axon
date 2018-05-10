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

from brainvisa.processing.qtgui.neuroProcessesGUI import mainThreadActions
from soma.qt_gui.qtThread import MainThreadLife
import anatomist.api as ana
from anatomist.cpp.paletteEditor import PaletteEditor
import soma
from soma import aims
from soma.qt_gui.qt_backend import QtCore, QtGui, uic, Qt
import glob
import os
import six


def check_registration(images,
                       overlays,
                       configuration):
    _mw = mainThreadActions().call(_check_registration_on_gui_thread,
                                   images,
                                   overlays,
                                   configuration)
    mw = MainThreadLife(_mw)
    return [mw]


def _check_registration_on_gui_thread(images,
                                      overlays,
                                      configuration):
    checkReg = CheckRegistration(images=images,
                                 overlays=overlays,
                                 configuration=configuration)
    mw = checkReg.display()
    return mw


def _findExtraFile(filename, type):
    """
    Finds extra files.
    """
    for dir in sorted(glob.glob(os.path.join(*(soma.path.split_path(soma.__file__)[:-3] + ['share', 'axon-*', type])))):
        if os.path.exists(dir):
            filepath = os.path.join(dir, filename)
            if os.path.exists(filepath):
                return filepath
    return None


class CheckRegistration():

    def __init__(self, images, overlays, configuration):
        self._configuration = configuration
        self._images = []
        self._rowFrames = {}
        self._initImageLists(images, overlays)

    def display(self):
        """
        Launches the check registration display
        """
        self._anatomist = ana.Anatomist('-b')

        if len(self._images) == 0:
            allowedExt = [".nii", ".img"]
            files = self._openFileDialog()
            imagesToLoad = []
            for f in files:
                if os.path.splitext(f)[1] not in allowedExt:
#                    try:
#                        dicom.read_file(f)
#                    except:
                        continue
                imagesToLoad.append(f)
            if len(imagesToLoad) == 0:
                return
            self._initImageLists(imagesToLoad, [])

        self._loadData()
        self._loadUi()
        self._init3dCursor()
        self._mainDiag.showMaximized()
        self._mainDiag.exec_()

        return [self._mainDiag]

    def _initImageLists(self, images, overlays):
        for i in images:
            if isinstance(i, basestring):
                self._images.append(i)
            else:
                self._images.append(str(i))
        self._overlays = []
        for i in overlays:
            if isinstance(i, basestring):
                self._overlays.append(i)
            else:
                self._overlays.append(str(i))

    def _openFileDialog(self):
        fileDialog = QtGui.QFileDialog()
        fileDialog.setFileMode(QtGui.QFileDialog.ExistingFiles)
        fileDialog.exec_()
        return fileDialog.selectedFiles()

    def _loadData(self):
        """
        Loads Anatomist image data
        """
        self._aImages = {}
        for img in self._images + self._overlays:
            aimsImg = aims.read(img)
            aImg = self._anatomist.loadObject(img)
            aImg.attributed()["volumeInterpolation"] = 0
            try:
                if aimsImg.header()["modality"] == "PT":
                    aImg.setPalette('Rainbow', minVal=0, maxVal=1)
                elif aimsImg.header()["modality"] == "NM":
                    aImg.setPalette('French', minVal=0, maxVal=1)
            except:
                pass
            self._aImages.update({img: aImg})

    def _loadUi(self):
        """
        Loads the Qt UI
        """
        self._rowFrames.clear()
        self._mainDiag = uic.loadUi(
            _findExtraFile("checkRegistrationViewer.ui", "ui"))
        self._mainDiag.setWindowFlags(QtCore.Qt.WindowTitleHint |
                                      QtCore.Qt.WindowMinMaxButtonsHint |
                                      QtCore.Qt.WindowCloseButtonHint)
        palette = self._mainDiag.palette()
        palette.setColor(
            self._mainDiag.backgroundRole(), QtGui.QColor(255, 255, 255))
        self._mainDiag.setPalette(palette)

        self._mainDiag.closeBt.setIcon(
            QtGui.QIcon(_findExtraFile("check_gray.png", "icons")))
        self._mainDiag.closeBt.setIconSize(QtCore.QSize(24, 24))
        self._mainDiag.closeBt.setAutoRaise(True)
        self._mainDiag.printBt.setIcon(
            QtGui.QIcon(_findExtraFile("print_gray.png", "icons")))
        self._mainDiag.printBt.setIconSize(QtCore.QSize(24, 24))
        self._mainDiag.printBt.setAutoRaise(True)

        self._mainDiag.displayRowOptionsCb.stateChanged.connect(
            self._displayRowOptionsChecked)
        self._mainDiag.display3DCursorCb.stateChanged.connect(
            self._displayCursorChecked)
        self._mainDiag.printBt.clicked.connect(self._printClicked)
        self._mainDiag.closeBt.clicked.connect(self._mainDiag.accept)

        self._loadAddRowFrame()
        self._loadPaletteFrame()

        self._mainFrameVLayout = QtGui.QVBoxLayout(self._mainDiag.mainFrame)
        self._mainFrameVLayout.setContentsMargins(0, 0, 0, 0)
        self._mainFrameVLayout.setSpacing(0)

        if not self._configuration:
            if len(self._images) >= 2:
                self._addRow(image1=self._images[0])
                self._addRow(image1=self._images[1])
                self._addRow(image1=self._images[0], image2=self._images[1])
            elif len(self._images) == 1:
                self._addRow(image1=self._images[0])
        else:
            self._loadRowConfiguration()
            try:
                self._mainDiag.displayRowOptionsCb.setChecked(
                    self._configuration["showRowOptions"])
            except:
                pass

    def _init3dCursor(self):
        """
        Inits the 3D cursor position according to the image of the first row
        """
        try:
            frame = self._rowFrames.keys()[0]
            view = self._rowFrames[frame]["views"][0]
            aImg = self._aImages[self._rowFrames[frame]["image"][1]]
        except:
            return

        bbox = [aims.Point3df(x[:3]) for x in aImg.boundingbox()]
        position = (bbox[1] - bbox[0]) * 0.5
        t = self._anatomist.getTransformation(aImg.getReferential(),
                                              view.getReferential())
        if t:
            position = t.transform(position)
        self._anatomist.execute('LinkedCursor', window=view, position=position)

    def _loadRowConfiguration(self):
        """
        Loads and reads the configuration dictionnary
        """
        try:
            rowConfig = self._configuration["rows"]
        except:
            return
        for row in rowConfig:
            image1 = row["image1"]
            if image1 in self._images:
                image1 = self._images[self._images.index(image1)]
            else:
                image1 = self._overlays[self._overlays.index(image1)]
            if "image1Palette" in row:
                self._aImages[image1].setPalette(row["image1Palette"]["name"],
                                                 minVal=row[
                                                     "image1Palette"]["min"],
                                                 maxVal=row["image1Palette"]["max"])
            image2 = None
            fusionRate = None
            if "image2" in row:
                image2 = row["image2"]
                if image2 in self._images:
                    image2 = self._images[self._images.index(image2)]
                else:
                    image2 = self._overlays[self._overlays.index(image2)]
                if "image2Palette" in row:
                    self._aImages[image2].setPalette(
                        row["image2Palette"]["name"],
                                                     minVal=row[
                                                         "image2Palette"]["min"],
                                                     maxVal=row["image2Palette"]["max"])
                if "fusionRate" in row:
                    fusionRate = row["fusionRate"]
            self._addRow(image1=image1,
                         image2=image2,
                         fusionRate=fusionRate)

    def _addRow(self, image1=None, image2=None, fusionRate=None):
        """
        Adds a row with axial, coronal and sagittal views.

        :param string image1:
            The reference image.

        :param string image2:
            The additional image.

        :param float fusionRate:
            The fusion rate between image1 and image2.
        """
        frame = QtGui.QFrame()
        frame.setFrameStyle(QtGui.QFrame.Box | QtGui.QFrame.Plain)
        frame.setLineWidth(1)
        frame.setContentsMargins(0, 0, 0, 1)

        self._rowFrames.update({frame:
                                {"image": {1: None, 2: None},
                                 "tool_frame": None,
                                 "combobox": {1: None, 2: None},
                                 "slider": None,
                                 "anatomist_objects": [],
                                 "views": [],
                                 "layout_position": len(self._rowFrames.keys()),
                                 "buttons": {"down": None,
                                             "up": None}
                                 }
                                })

        self._mainFrameVLayout.addWidget(frame)
        hLay = QtGui.QHBoxLayout(frame)
        hLay.setContentsMargins(0, 0, 0, 0)
        hLay.setSpacing(0)

        toolFrame = QtGui.QFrame()
        self._rowFrames[frame]["tool_frame"] = toolFrame

        hLay.addWidget(toolFrame)
        vLay = QtGui.QVBoxLayout(toolFrame)

        buttonHLay = QtGui.QHBoxLayout()
        buttonHLay.setContentsMargins(0, 0, 0, 0)
        buttonHLay.setSpacing(0)
        vLay.addLayout(buttonHLay)

        deleteBt = QtGui.QToolButton()
        deleteBt.setIcon(
            QtGui.QIcon(_findExtraFile("close_gray.png", "icons")))
        deleteBt.setIconSize(QtCore.QSize(24, 24))
        deleteBt.setAutoRaise(True)
        deleteBt.clicked.connect(self._deleteRow)
        buttonHLay.addWidget(deleteBt)

        downBt = QtGui.QToolButton()
        self._rowFrames[frame]["buttons"]["down"] = downBt
        downBt.setIcon(QtGui.QIcon(_findExtraFile("down_gray.png", "icons")))
        downBt.setIconSize(QtCore.QSize(24, 24))
        downBt.setAutoRaise(True)
        downBt.clicked.connect(self._downClicked)
        buttonHLay.addWidget(downBt)

        upBt = QtGui.QToolButton()
        self._rowFrames[frame]["buttons"]["up"] = upBt
        upBt.setIcon(QtGui.QIcon(_findExtraFile("up_gray.png", "icons")))
        upBt.setIconSize(QtCore.QSize(24, 24))
        upBt.setAutoRaise(True)
        upBt.clicked.connect(self._upClicked)
        buttonHLay.addWidget(upBt)
        buttonHLay.addSpacerItem(
            QtGui.QSpacerItem(20, 20, hPolicy=QtGui.QSizePolicy.Expanding))
        vLay.addSpacerItem(
            QtGui.QSpacerItem(20, 20, vPolicy=QtGui.QSizePolicy.Expanding))

        paramHLay = QtGui.QHBoxLayout()
        vLay.addLayout(paramHLay)
        paramHLay.setContentsMargins(0, 0, 0, 0)
        slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        slider.setOrientation(QtCore.Qt.Vertical)
        if fusionRate is not None:
            slider.setValue(fusionRate * 100)
        else:
            slider.setValue(50)
        self._rowFrames[frame]["slider"] = slider
        slider.valueChanged.connect(self._mixingRateValueChanged)
        paramHLay.addWidget(slider)

        paramVLay = QtGui.QVBoxLayout()
        paramHLay.addLayout(paramVLay)
        paramVLay.setContentsMargins(0, 0, 0, 0)
        for i in [1, 2]:
            imageCb = self._createComboBoxFromImages(secondary=(i == 2))
            if i == 2:
                paramVLay.addSpacerItem(
                    QtGui.QSpacerItem(20, 20, vPolicy=QtGui.QSizePolicy.Expanding))

            paramVLay.addWidget(imageCb)
            imageCb.currentIndexChanged.connect(self._imageSelectionChanged)
            self._rowFrames[frame]["combobox"][i] = imageCb

        vLay.addSpacerItem(
            QtGui.QSpacerItem(20, 20, vPolicy=QtGui.QSizePolicy.Expanding))

        toolFrame.setHidden(not self._mainDiag.displayRowOptionsCb.isChecked())

        aViews = []
        orientation = ['Axial', 'Coronal', 'Sagittal']
        for ori in orientation:
            newWin = self._anatomist.createWindow(ori, no_decoration=True)
            hLay.addWidget(newWin.getInternalRep())
            self._anatomist.execute('WindowConfig', windows=[newWin],
                                    light={'background': [0., 0., 0., 1.]})
            aViews.append(newWin)
        self._rowFrames[frame]["views"] = aViews

        self._rowFrames[frame]["combobox"][1].blockSignals(True)
        self._rowFrames[frame]["combobox"][2].blockSignals(True)
        self._rowFrames[frame]["combobox"][1].setCurrentIndex(
            self._getIndexAccordingToImage(image1))
        self._rowFrames[frame]["combobox"][2].setCurrentIndex(
            self._getIndexAccordingToImage(image2, secondary=True))
        self._rowFrames[frame]["combobox"][1].blockSignals(False)
        self._rowFrames[frame]["combobox"][2].blockSignals(False)

        self._updateFrameViews(frame)
        self._updateButtons()

        hLay.setStretch(0, 1)
        for i in range(1, hLay.count()):
            hLay.setStretch(i, 100)

    def _imageSelectionChanged(self, index):
        """
        Updates the current frame views
        """
        self._updateFrameViews(self._mainDiag.sender().parent().parent())

    def _getIndexAccordingToImage(self, image, secondary=False):
        """
        Gets a list index according to an image path
        """
        index = -1
        if image in self._images:
            index = self._images.index(image)
        elif image in self._overlays:
            index = self._overlays.index(image)
            index += len(self._images)
        if secondary:
            # the secondary combobox contains a "None" item
            index += 1

        return index

    def _getImageAccordingToIndex(self, index, secondary=False):
        """
        Gets an image path according to a list index
        """
        if secondary:
            # the secondary combobox contains a "None" item
            index -= 1
        if index < 0:
            return None
        if index < len(self._images):
            return self._images[index]
        else:
            return self._overlays[index - len(self._images)]

    def _deleteRow(self):
        """
        Deletes the current row
        """
        sender = self._mainDiag.sender()
        frame = sender.parent().parent()
        frame.setParent(None)
        pos = self._rowFrames[frame]["layout_position"]
        for v in self._rowFrames.values():
            if v["layout_position"] > pos:
                v["layout_position"] -= 1
        del self._rowFrames[frame]
        self._updateButtons()

    def _upClicked(self):
        """
        Switches the current row with its top row
        """
        frame1 = self._mainDiag.sender().parent().parent()
        currentPosition = self._rowFrames[frame1]["layout_position"]
        if currentPosition == 0:
            return
        newPosition = currentPosition - 1
        for k, v in six.iteritems(self._rowFrames):
            if v["layout_position"] == newPosition:
                frame2 = k
                break
        self._switchFrames(frame1, frame2)

    def _downClicked(self):
        """
        Switches the current row with its bottom row
        """
        frame1 = self._mainDiag.sender().parent().parent()
        currentPosition = self._rowFrames[frame1]["layout_position"]
        if currentPosition == len(self._rowFrames.keys()) - 1:
            return
        newPosition = currentPosition + 1
        for k, v in six.iteritems(self._rowFrames):
            if v["layout_position"] == newPosition:
                frame2 = k
                break
        self._switchFrames(frame2, frame1)

    def _switchFrames(self, frame1, frame2):
        """
        Switches frame1 and frame2
        """
        oldPos = self._rowFrames[frame1]["layout_position"]
        newPos = self._rowFrames[frame2]["layout_position"]
        layout = frame1.parent().layout()
        layout.insertWidget(newPos, frame1)
        self._rowFrames[frame1]["layout_position"] = newPos
        self._rowFrames[frame2]["layout_position"] = oldPos
        self._updateButtons()

    def _updateButtons(self):
        """
        Enables/disables the up and down buttons according to their row position
        """
        for v in self._rowFrames.values():
            upEnabled = True
            downEnabled = True
            if v["layout_position"] == 0:
                upEnabled = False
            if v["layout_position"] == len(self._rowFrames.keys()) - 1:
                downEnabled = False
            v["buttons"]["down"].setEnabled(downEnabled)
            v["buttons"]["up"].setEnabled(upEnabled)

    def _updateFrameViews(self, frame):
        """
        Updates the views of a given frame
        """
        self._removeFromViews(frame)
        self._addInViews(frame)
        img1 = self._getSelectedFrameImage(frame, 1)
        img2 = self._getSelectedFrameImage(frame, 2)
        self._rowFrames[frame]["slider"].setEnabled(
            img2 is not None and img1 != img2)

    def _removeFromViews(self, frame):
        """
        Removes the Anatomist objects from frame views
        """
        for o in self._rowFrames[frame]["anatomist_objects"]:
            if o:
                try:
                    o.removeFromWindows(self._rowFrames[frame]["views"])
                except:
                    pass

    def _addInViews(self, frame):
        """
        Adds Anatomist objects to frame views
        """
        self._rowFrames[frame]["anatomist_objects"] = []
        img1 = self._getSelectedFrameImage(frame, 1)
        img2 = self._getSelectedFrameImage(frame, 2)
        self._rowFrames[frame]["image"][1] = img1
        self._rowFrames[frame]["image"][2] = img2
        if not img2 or img1 == img2:
            aImg1 = self._aImages[img1]
            aImg1.addInWindows(self._rowFrames[frame]["views"])
            self._rowFrames[frame]["anatomist_objects"].append(aImg1)
        else:
            fusion = self._anatomist.fusionObjects(
                [self._aImages[img1], self._aImages[img2]], 'Fusion2DMethod')
            self._rowFrames[frame]["anatomist_objects"].append(fusion)
            fusion.addInWindows(self._rowFrames[frame]["views"])
            self._setFrameFusion(
                frame, self._rowFrames[frame]["slider"].value())

    def _getSelectedFrameImage(self, frame, number):
        """
        Gets the selected image of a frame
        """
        return self._getImageAccordingToIndex(
            self._rowFrames[frame]["combobox"][number].currentIndex(),
                                              secondary=(number == 2))

    def _mixingRateValueChanged(self, value):
        """
        Updates the mixing rate according to value
        """
        self._setFrameFusion(self._mainDiag.sender().parent().parent(), value)

    def _setFrameFusion(self, frame, value):
        """
        Updates the mixing rate of the frame views according to value
        """
        img1 = self._rowFrames[frame]["image"][1]
        img2 = self._rowFrames[frame]["image"][2]
        if img2 and img1 != img2:
            fusion = self._rowFrames[frame]["anatomist_objects"][0]
            fusionMode = self._getFusionMode(img1, img2)
            if fusionMode is None:
                self._anatomist.execute(
                    'TexturingParams', objects=[fusion], texture_index=1,
                                        rate=float(value) / 100)
            else:
                self._anatomist.execute(
                    'TexturingParams', objects=[fusion], texture_index=1,
                                        rate=float(value) / 100,
                                        mode=fusionMode)

    def _getFusionMode(self, img1, img2):
        """
        Gets the fusion mode according to img1 and img2 types (image or overlay)
        """
        if (self._isImageOverlay(img1) and self._isImageOverlay(img2)) or\
           (self._isImageImage(img1) and self._isImageImage(img2)):
            return None
        if self._isImageOverlay(img1):
            overlay = img1
        else:
            overlay = img2
        rgb = self._aImages[
            overlay].getOrCreatePalette().refPalette().value(0, 0)
        black = (rgb.red() == 0 and rgb.green() == 0 and rgb.blue() == 0)
        white = (rgb.red() == 255 and rgb.green()
                 == 255 and rgb.blue() == 255)
        if white:
            if img1 == overlay:
                return "linear_B_if_A_white"
            else:
                return "linear_A_if_B_white"
        elif black:
            if img1 == overlay:
                return "linear_B_if_A_black"
            else:
                return "linear_A_if_B_black"
        else:
            return None

    def _isImageOverlay(self, image):
        """
        Returns True if image is an overlay
        """
        return (image in self._overlays)

    def _isImageImage(self, image):
        """
        Returns True if image is a simple image
        """
        return (image in self._images)

    def _loadAddRowFrame(self):
        """
        Loads the "Add row" Qt UI
        """
        hLay = QtGui.QHBoxLayout(self._mainDiag.addRowGroupBox)
        vLay = QtGui.QVBoxLayout()
        hLay.addLayout(vLay)
        self._newRowImage1Cb = self._createComboBoxFromImages()
        vLay.addWidget(self._newRowImage1Cb)
        self._newRowImage2Cb = self._createComboBoxFromImages(secondary=True)
        vLay.addWidget(self._newRowImage2Cb)
        bt = QtGui.QToolButton()
        bt.setIcon(QtGui.QIcon(_findExtraFile("plus_gray.png", "icons")))
        bt.setIconSize(QtCore.QSize(24, 24))
        bt.setAutoRaise(True)
        bt.clicked.connect(self._addRowClicked)
        hLay.addWidget(bt)

    def _loadPaletteFrame(self):
        """
        Loads the palette editor Qt UI
        """
        hLay = QtGui.QHBoxLayout(self._mainDiag.paletteFrame)
        self._paletteImageCb = self._createComboBoxFromImages(secondary=True)
        self._paletteImageCb.removeItem(0)
        hLay.addWidget(self._paletteImageCb)
        self._paletteImageCb.currentIndexChanged.connect(
            self._paletteImageChanged)
        paletteFilter = ['B-W LINEAR', 'Blue-Green-Red-Yellow',
                         'Blue-Red2', 'French', 'RAINBOW',
                         'RED TEMPERATURE', 'Rainbow2',
                         'Talairach']
        self._paletteEditor = PaletteEditor(self._aImages[self._images[0]],
                                            parent=self._mainDiag.paletteFrame,
                                            default='B-W LINEAR',
                                            palette_filter=paletteFilter)
        self._paletteEditor.paletteMinMaxChanged.connect(
            self._paletteMinMaxChanged)
        hLay.addWidget(self._paletteEditor)

    def _addRowClicked(self):
        """
        Adds a row
        """
        img1 = self._getImageAccordingToIndex(
            self._newRowImage1Cb.currentIndex())
        img2 = self._getImageAccordingToIndex(
            self._newRowImage2Cb.currentIndex(),
                                              secondary=True)
        self._addRow(img1, img2)

    def _paletteImageChanged(self, index):
        """
        Changes the palette editor image
        """
        self._paletteEditor.setImage(
            self._aImages[self._getImageAccordingToIndex(index)])

    def _paletteMinMaxChanged(self, aImage):
        """
        Updates the frame fusion parameters
        """
        image = None
        for k, v in six.iteritems(self._aImages):
            if v == aImage:
                image = k
                break
        if not image or image not in self._overlays:
            return

        for k, v in six.iteritems(self._rowFrames):
            if v["image"][2] == image:
                self._setFrameFusion(k, v["slider"].value())

    def _displayRowOptionsChecked(self, state):
        """
        Hides/shows the row options
        """
        for v in self._rowFrames.values():
            v["tool_frame"].setHidden(state == 0)

    def _displayCursorChecked(self, state):
        """
        Hides/shows the 3D cursor
        """
        for v in self._rowFrames.values():
            for view in v["views"]:
                view.setHasCursor(state > 0)
                view.setChanged()
                view.notifyObservers()
            self._anatomist.execute('WindowConfig', windows=v["views"],
                                    light={'background': [0., 0., 0., 1.]})

    def _createComboBoxFromImages(self, secondary=False):
        """
        Creates a combobox with the image list
        """
        cb = QtGui.QComboBox()
        cb.setFixedSize(130, 23)
        if secondary:
            cb.addItem("None")
        for img in self._images:
            cb.addItem(os.path.splitext(os.path.basename(img))[0])
        for img in self._overlays:
            cb.addItem(os.path.splitext(os.path.basename(img))[0])
        longestText = ""
        for i in range(cb.count()):
            text = cb.itemText(i)
            if len(text) > len(longestText):
                longestText = text
        cb.view().setMinimumWidth(
            QtGui.QFontMetrics(cb.font()).width(longestText + "  "))

        return cb

    def _printClicked(self):
        """
        Opens a dialog box to print the current views
        """
        pix = QtGui.QPixmap.grabWindow(self._mainDiag.mainFrame.winId())
        printer = Qt.QPrinter()
        printer.setOrientation(Qt.QPrinter.Landscape)
        printer.setPageMargins(0., 0., 0., 0., Qt.QPrinter.Millimeter)
        pdfPath = "/tmp"
        pdfName = "testBv"
        pdfName += ".pdf"
        printer.setOutputFileName(os.path.join(pdfPath, pdfName))
        print_dialog = Qt.QPrintDialog(printer)
        print_dialog.setOption(
            QtGui.QAbstractPrintDialog.PrintPageRange, False)
        if print_dialog.exec_() != QtGui.QDialog.Accepted:
            return
        pix = pix.scaled(printer.pageRect().size(),
                         aspectRatioMode=QtCore.Qt.KeepAspectRatio,
                         transformMode=QtCore.Qt.SmoothTransformation)
        painter = QtGui.QPainter(printer)
        painter.drawPixmap(QtGui.QPoint(0, 0), pix)
        painter.end()
