from soma.qt_gui.qt_backend import QtCore, Qt, QtGui
from soma.qt_gui.qt_backend.QtGui import QRadioButton, QPalette, QButtonGroup, QLabel, QFrame, QVBoxLayout, QColor
from soma.qt_gui.qt_backend.uic import loadUi
from brainvisa.processing.qtgui.neuroProcessesGUI import mainThreadActions
from soma.qt_gui.qtThread import MainThreadLife
from functools import partial
import brainvisa.anatomist as ana
from anatomist.cpp.paletteEditor import PaletteEditor
import weakref
from six.moves import range
from six.moves import zip

#------------------------------------------------------------------------------


def displayTitledGrid(transformationManager, parent, inverseRawColumn,
                      objPathMatrix,
                      rowTitles=['raw_space', "MRI_native_space", "mask",
                                 "MNI_space", ],
                      rowColors=['darkOrange', 'blue', "MRI", 'blue',
                                 'magenta'],
                      colTitles=['PET', "MRI", "grey"],
                      windowTitle='View grid',
                      linkWindows='space',
                      overlaidImages=[],
                      mainColormap='B-W LINEAR',
                      overlayColormap='RAINBOW',
                      customOverlayColormap='Blue-White',
                      rowButtonSubTitles=None
                      ):
    '''Grid of Anatomist views

    Parameters:
    linkWindows: str
        possible values : 'all' | none | row
    rowColors: list
        default: ['darkOrange', 'blue', "MRI", 'blue', 'magenta']
        orange = rawSpace, blue = mri space, magenta = mni space
    '''
    _mw = mainThreadActions().call(_displayTitledGrid_onGuiThread,
                                   transformationManager, parent,
                                   inverseRawColumn,
                                   objPathMatrix, rowTitles=rowTitles,
                                   rowColors=rowColors, colTitles=colTitles,
                                   windowTitle=windowTitle,
                                   linkWindows=linkWindows,
                                   overlaidImages=overlaidImages,
                                   mainColormap=mainColormap,
                                   overlayColormap=overlayColormap,
                                   customOverlayColormap=customOverlayColormap,
                                   rowButtonSubTitles=rowButtonSubTitles)
    mw = MainThreadLife(
        _mw)  # ensure mw destruction takes place in the GUI thread
    return mw


def _displayTitledGrid_onGuiThread(transformationManager, parent,
                                   inverseRawColumn, objPathMatrix, rowTitles,
                                   rowColors, colTitles, windowTitle,
                                   linkWindows, overlaidImages, mainColormap,
                                   overlayColormap, customOverlayColormap,
                                   rowButtonSubTitles):
    # DisplayTitledGrid doit etre construit sur le thread de Gui pour etre sur
    # que la destruction de la mw se fasse sur le thread de Gui
    TitledGrid = DisplayTitledGrid(
        objPathMatrix, parent=parent, mainColormap=mainColormap,
      overlayColormap=overlayColormap,
      customOverlayColormap=customOverlayColormap)
    mw = TitledGrid.display(inverseRawColumn=inverseRawColumn,
                            windowFlag=QtCore.Qt.Window, windowTitle=windowTitle, rowTitles=rowTitles,
                            colTitles=colTitles, rowColors=rowColors, linkWindows=linkWindows,
                            overlaidImages=overlaidImages, rowButtonSubTitles=rowButtonSubTitles)[0]
    return TitledGrid

#------------------------------------------------------------------------------


class DisplayTitledGrid(QtGui.QWidget):

    def __init__(self, objPathMatrix, parent=None,
                 mainColormap='B-W LINEAR',
                 overlayColormap='RAINBOW',
                 customOverlayColormap='Blue-White'):
        super(DisplayTitledGrid, self).__init__(parent)
        self._main_colormap = mainColormap
        self._overlay_colormap = overlayColormap
        self._custom_overlay_colormap = customOverlayColormap
        self._loadObjectInAnatomist(objPathMatrix, interpolation=False)
        self._overlaid_images = []
        self._overlay_fusions = []
        self._custom_overlay_fusions = []
            # momoTODO : pas besoin d'une liste, un seul suffit sinon
            # l'utilisateur s'y perd (selection avec row et column).
        self._selectedRow = -1
        self._selectedColumn = -1
        self._row_titles = []
        self._col_titles = []
        self._paletteEditor = None

    def __del__(self):
        # make sure mw is deleted first, otherwise its connected signals still point
        # to slots (in c++) in self, when self is already destroyed, which
        # generally results in a crash
        self.mw.close()
        del self.mw

    def display(self, inverseRawColumn=False, windowFlag=QtCore.Qt.Window,
                windowTitle='Compare',
                rowTitles=['row_1', 'row_2', 'row_3', 'row_4'],
                colTitles=['col_1', 'col_2', 'col_3'],
                rowColors=['darkOrange', 'blue', 'blue', 'magenta'],
                linkWindows='space',
                overlaidImages=[],
                rowButtonSubTitles=None):

        layout = QtGui.QVBoxLayout(self)
        self.setLayout(layout)
        self.mw = self._loadUserInterface()  # create self.mw.gridLayout
        self.mw.setWindowTitle(windowTitle)
        layout.addWidget(self.mw)

        self._row_titles = rowTitles
        self._col_titles = colTitles
        # self._custom_row_titles = [ x for x in rowTitles ]

        # load overlay (fusionned) images, and make fusions
        self._loadOverlayImages(overlaidImages)
        self._createOverlayFusions()

        self._addColumnButton(colTitles, inverseRawColumn)
        self._addRowButton(
            rowTitles, rowColors, inverseRawColumn, rowButtonSubTitles)

        # self._createWinFrame(self.mw, self.mw.selectedReferenceLabel) #
        # momoTODO : meme cadre autour de selected reference

        self._createAndLinkAnatomistWindowsInMainLayout(
            linkWindows, inverseRawColumn, 'Sagittal', rowTitles)

        self.mw.anatomistObjectList = self.anatomistObjectList  # momo  :ca sert a quoi?

        # replace individual objects by overlays fusions when applicable
        self._addObjectOrFusion_inAnatomistWindows()

        self.mw.comboBox.currentIndexChanged.connect(self._onComboBox_changed)
        self.mw.mixingSlider.valueChanged.connect(self._onMixingRateChanged)
        self.mw.maximizeButton.clicked.connect(self._onMaximizeButtonClicked)

        self.show()

        return [self.mw]

#-----------------------------------------------------------------------------
# private : begins with _
#-----------------------------------------------------------------------------

    def _loadObjectInAnatomist(self, objPathMatrix, interpolation=True):
        a = ana.Anatomist()
        self.anatomistObjectList = []
        for r in range(0, len(objPathMatrix)):
            objPathRow = objPathMatrix[r]
            anaObjRow = []
            for c in range(0, len(objPathRow)):
                objPath = objPathRow[c]
                if (objPath is not None):
                    obj = a.loadObject(objPath, forceReload=False)
                    if not interpolation:
                        obj.attributed()['volumeInterpolation'] = False
                    obj.setPalette(self._main_colormap)
                    anaObjRow.append(obj)
                else:
                    anaObjRow.append(None)

            self.anatomistObjectList.append(anaObjRow)

    def _loadUserInterface(self):
        dotIdx = __file__.rindex('.')
        uiFileName = __file__[:dotIdx] + '.ui'
        mw = loadUi(uiFileName)
        mw.mixRate.setText('50 %')
        return mw

    def _addColumnButton(self, buttonTitles, inverseRawColumn):
        for buttonIndex in range(0, len(buttonTitles)):
            title = buttonTitles[buttonIndex]
            button = QRadioButton(title)

            if (inverseRawColumn):
                self.mw.gridLayout.addWidget(
                    button, buttonIndex + 1, 0, QtCore.Qt.AlignHCenter)
                self.mw.gridLayout.setRowStretch(buttonIndex + 1, 10)
            else:
                self.mw.gridLayout.addWidget(
                    button, 0, buttonIndex + 1, QtCore.Qt.AlignHCenter)
                self.mw.gridLayout.setColumnStretch(buttonIndex + 1, 10)
            button.clicked.connect(partial(
                                   self.__class__._onColumnButtonClicked, weakref.proxy(
                                       self),
                                   buttonIndex))

    def _addRowButton(self, buttonTitles, buttonColors, inverseRawColumn, rowButtonSubTitles=None):
        self.rowsButtonGroup = QButtonGroup(self.mw)
        self.rowsButtonGroup.setExclusive(True)
        for buttonIndex in range(0, len(buttonTitles)):
            title = buttonTitles[buttonIndex]
            NotNoneCount = len(
                [x for x in self.anatomistObjectList[buttonIndex] if x != None])
            isFusionPossibleOnRow = NotNoneCount > 1 or len(
                self._overlaid_images) > 0
            widget = DisplayTitledGrid._createColoredButton(
                title, buttonColors[buttonIndex])
            self.rowsButtonGroup.addButton(widget, buttonIndex)
            widget.setToolTip(
                '<p>Click on this button to superimpose a different image. To do so, click on this row button, then click on a column button to display the column main image as overlay on this row.<p><p>Click again on the tow button to go back to the initial views.</p>')
            widget.clicked.connect(partial(
                                   self.__class__._onRowButtonClicked, weakref.proxy(
                                       self),
                                   buttonIndex))
            if(rowButtonSubTitles is not None and buttonIndex < len(rowButtonSubTitles)):
                subTitle = rowButtonSubTitles[buttonIndex]
                vLay = QVBoxLayout()
                vLay.insertStretch(0, 2)
                vLay.addWidget(widget)
                vLay.addWidget(QLabel(subTitle))
                vLay.addStretch(2)
                if (inverseRawColumn):
                    self.mw.gridLayout.addLayout(vLay, 0, buttonIndex + 1)
                    self.mw.gridLayout.setColumnStretch(buttonIndex + 1, 10)
                else:
                    self.mw.gridLayout.addLayout(vLay, buttonIndex + 1, 0)
                    self.mw.gridLayout.setRowStretch(buttonIndex + 1, 10)
            else:
                if (inverseRawColumn):
                    self.mw.gridLayout.addWidget(widget, 0, buttonIndex + 1)
                    self.mw.gridLayout.setColumnStretch(buttonIndex + 1, 10)
                else:
                    self.mw.gridLayout.addWidget(widget, buttonIndex + 1, 0)
                    self.mw.gridLayout.setRowStretch(buttonIndex + 1, 10)

    @staticmethod
    def _createColoredButton(title, color):
        button = QRadioButton(title)
        buttonPalette = QPalette()
        buttonPalette.setColor(QPalette.ButtonText, Qt.QColor(color))
        button.setPalette(buttonPalette)
        # button.setDisabled(True)
        button.setCheckable(True)
        return button

    def _createAndLinkAnatomistWindowsInMainLayout(self, linkWindows, inverseRawColumn, initialView, spaceNames):
        mw = self.mw
        mw.anaWinMatrix = []
        for r in range(0, len(self.anatomistObjectList)):
            anaWinRow = self._createAnatomistWindows_InMainLayout(
                inverseRawColumn, initialView, r)
            DisplayTitledGrid._linkAnatomistWindows(
                linkWindows, anaWinRow, spaceNames)

    def _createAnatomistWindows_InMainLayout(self, inverseRawColumn, view, rowIndex):
        mw = self.mw
        a = ana.Anatomist()
        anaObjRow = self.anatomistObjectList[rowIndex]
        anaWinRow = []
        anatomistConfig = a.config()
        isWindowSizeFactorExistInConfig = False
        if 'windowSizeFactor' in anatomistConfig:
            sizefac = a.config()['windowSizeFactor']
            isWindowSizeFactorExistInConfig = True
        a.config()['windowSizeFactor'] = 1.
        for c in range(0, len(anaObjRow)):
            anaObj = anaObjRow[c]
            if (anaObj is not None):
                w = a.createWindow(view, no_decoration=True)
                anaObj.addInWindows([w])
                anaWinRow.append(w)
                frame = self._createWinFrame(mw, w.getInternalRep())
                if (inverseRawColumn):
                    mw.gridLayout.addWidget(frame, c + 1, rowIndex + 1)
                else:
                    mw.gridLayout.addWidget(frame, rowIndex + 1, c + 1)
            else:
                anaWinRow.append(None)
        if(isWindowSizeFactorExistInConfig):
            a.config()['windowSizeFactor'] = sizefac
        mw.anaWinMatrix.append(anaWinRow)
        return mw.anaWinMatrix

    def _createWinFrame(self, mw, widget):
        mw.frame = QFrame()
        mw.flay = QVBoxLayout(mw.frame)
        mw.flay.addWidget(widget)
        mw.frame.setObjectName('winborder')
        mw.frame.setStyleSheet(
            'QFrame#winborder { border: 0px solid; border-radius: 4px; }')
        pal = mw.frame.palette()
        pal.setColor(QPalette.Dark, QColor(255, 192, 0))
        pal.setColor(QPalette.Midlight, QColor(192, 255, 0))
        pal.setColor(QPalette.Shadow, QColor(192, 0, 255))
        pal.setColor(QPalette.Light, QColor(0, 255, 192))
        pal.setColor(QPalette.Mid, QColor(0, 192, 255))
        return mw.frame

    @staticmethod
    def _linkAnatomistWindows(linkWindows, anaWinRow, spaceNames):
        if (linkWindows == 'all'):
            DisplayTitledGrid._linkAnatomistWindows_all(anaWinRow)
        elif (linkWindows == 'row'):
            DisplayTitledGrid._linkAnatomistWindows_byRow(anaWinRow)
        elif (linkWindows == 'space'):
            DisplayTitledGrid._linkAnatomistWindows_bySpace(
                anaWinRow, spaceNames)

    @staticmethod
    def _linkAnatomistWindows_all(anaWinMatrix):
        a = ana.Anatomist()
        wins = []
        for anaWinRow in anaWinMatrix:
            for w in anaWinRow:
                if (w is not None):
                    wins.append(w)

        a.linkWindows(wins, group=None)
        a.execute('WindowConfig', windows=wins,
                  linkedcursor_on_slider_change=1)

    @staticmethod
    def _linkAnatomistWindows_byRow(anaWinMatrix):
        a = ana.Anatomist()
        for anaWinRow in anaWinMatrix:
            wins = []
            for w in anaWinRow:
                if (w is not None):
                    wins.append(w)

            a.linkWindows(wins, group=None)
            a.execute('WindowConfig', windows=wins,
                      linkedcursor_on_slider_change=1)

    @staticmethod
    def _linkAnatomistWindows_bySpace(anaWinMatrix, spaceNames):
        a = ana.Anatomist()
        winsDico = {}
        for anaWinRow, spaceName in zip(anaWinMatrix, spaceNames):
            isRawSpace = spaceName.lower().count('raw') != 0
            if (isRawSpace is False):  # inutile de lier les fenetres si leur images sont des raw, donc dans leur propre espace. Par exemple, ne pas lier la pet avec l'irm
                keySpace = DisplayTitledGrid._convertSpaceName_to_key(
                    spaceName)
                for w in anaWinRow:
                    if (w is not None):
                        if keySpace in winsDico:
                            prevWins = winsDico[keySpace]
                            prevWins.append(w)
                            winsDico.update({keySpace: prevWins})
                        else:
                            winsDico.update({keySpace: [w]})

        for _k, wins in winsDico.items():
            a.linkWindows(wins, group=None)
            a.execute('WindowConfig', windows=wins,
                      linkedcursor_on_slider_change=1)

    @staticmethod
    def _convertSpaceName_to_key(spaceName):
        isMRISpace = spaceName.lower().count('mri') > 0
        isPETSpace = spaceName.lower().count('pet') > 0
        isMNISpace = spaceName.lower().count('mni') > 0
        keySpace = spaceName
        if (isMRISpace):
            keySpace = 'mri'
        elif (isPETSpace):
            keySpace = 'pet'
        elif (isMNISpace):
            keySpace = 'mni'
        return keySpace

    def _onComboBox_changed(self):
        for anaWinRow in self.mw.anaWinMatrix:
            for w in anaWinRow:
                if(w is not None):
                    if(self.mw.comboBox.currentText() == 'Axial'):
                        w.muteAxial()
                    elif(self.mw.comboBox.currentText() == 'Sagittal'):
                        w.muteSagittal()
                    elif(self.mw.comboBox.currentText() == 'Coronal'):
                        w.muteCoronal()

    def _loadOverlayImages(self, overlaidImages):
        a = ana.Anatomist()
        images = []
        for filename in overlaidImages:
            if filename:  # may be None to leave an un-overlayed row
                image = a.loadObject(filename, forceReload=False)
                images.append(image)
                image.setPalette(palette=self._overlay_colormap)
            else:  # None
                images.append(None)
        self._overlaid_images = images

    def _createOverlayFusions(self):
        if len(self._overlaid_images) == 0:
            # no overlays, nothing to be done.
            return

        matriceFusions = []
        if len(self._overlaid_images) == len(self.anatomistObjectList) \
                * len(self.anatomistObjectList[0]):
            indiv_index = 0
            for row, objRow in enumerate(self.anatomistObjectList):
                overlays = []
                for col, objCol in enumerate(objRow):
                    index = indiv_index
                    indiv_index += 1
                    overlayimage = self._overlaid_images[index]
                    overlays.append(overlayimage)
                rowFusions = self._createFusionsWithOverlay(objRow, overlays)
                matriceFusions.append(rowFusions)
        else:
            for row, objRow in enumerate(self.anatomistObjectList):
                index = row
                if index >= len(self._overlaid_images):
                    overlayimage = self._overlaid_images[-1]
                else:
                    overlayimage = self._overlaid_images[index]
                rowFusions = self._createFusionsWithOverlay(
                    objRow, overlayimage)
                matriceFusions.append(rowFusions)
        self._overlay_fusions = matriceFusions

    def _createCustomOverlayFusions(self, row, column):
        if row >= 0 and column >= 0:
            overlayimage = self.anatomistObjectList[row][column]
            if overlayimage is not None:
                newoverlay = self._setPaletteOfOverlay(overlayimage)
                rowFusions = self._createFusionsWithOverlay(
                    self.anatomistObjectList[row], newoverlay, overlayimage)
                if len(self._custom_overlay_fusions) <= row:
                    self._custom_overlay_fusions.extend(
                        [[]] * (row + 1 - len(self._custom_overlay_fusions)))
                self._custom_overlay_fusions[row] = rowFusions
                a = ana.Anatomist()
                a.execute('TexturingParams', objects=[
                          x for x in rowFusions if x], texture_index=1, rate=float(self.mw.mixingSlider.value()) / 100)
            elif(row < len(self._custom_overlay_fusions)):
                self._custom_overlay_fusions[row] = None

    def _createFusionsWithOverlay(self, objects, overlayimages,
                                  imageWithoutFusion=None):
        if not isinstance(overlayimages, list):
            overlayimages = [overlayimages]
        a = ana.Anatomist()
        rowFusions = []
        for index, obj in enumerate(objects):
            if index < len(overlayimages):
                overlayimage = overlayimages[index]
            else:
                overlayimage = overlayimages[-1]
            if obj and overlayimage and obj != overlayimage and (not imageWithoutFusion or imageWithoutFusion != obj):
                fusion = a.fusionObjects(
                    objects=[obj, overlayimage], method='Fusion2DMethod')
                rowFusions.append(fusion)
            else:
                rowFusions.append(None)
        return rowFusions

    def _setPaletteOfOverlay(self, overlayimage):
        a = ana.Anatomist()
        if (self._custom_overlay_colormap is not None):
            newoverlay = a.duplicateObject(overlayimage)
            newoverlay.setPalette(self._custom_overlay_colormap)
        else:
            newoverlay = overlayimage
            overlayimagepalette = overlayimage.palette().refPalette()
            paletteName = overlayimagepalette.name()
            newoverlay.setPalette(paletteName)
        return newoverlay

    def _addObjectOrFusion_inAnatomistWindows(self):
        if len(self._overlay_fusions) == len(self.mw.anaWinMatrix):
            byrow = False
        else:
            byrow = True
        indiv_index = 0
        for row, _anaWinRow in enumerate(self.mw.anaWinMatrix):
            if byrow:
                index = row
            else:
                index = indiv_index
                indiv_index += 1
            if index < len(self._overlay_fusions):
                fusRow = self._overlay_fusions[index]
                self._addObjectOrFusion_inAnatomistWindowsRow(row, fusRow)

    def _addObjectOrFusion_inAnatomistWindowsRow(self, rowIndex, rowFusions):  # rowFusions can be self._overlay_fusions or self._custom_overlay_fusions
        if(rowIndex >= 0):
            anaWinRow = self.mw.anaWinMatrix[rowIndex]
            objRow = self.anatomistObjectList[rowIndex]
            for col, win in enumerate(anaWinRow):
                if win:
                    if win.objects:
                        win.removeObjects(win.objects)
                    if rowFusions and rowFusions[col]:
                        win.addObjects(rowFusions[col])
                    elif objRow and objRow[col]:
                        win.addObjects(objRow[col])

    def _removeCustomOverlays(self, row):
        self._custom_overlay_fusions[row] = []
        self._addObjectOrFusion_inAnatomistWindowsRow(
            row, self._overlay_fusions[row])

    def _onMixingRateChanged(self, value):
        self.mw.mixRate.setText(str(value) + ' %')
        a = ana.Anatomist()
        objects = []
        for fusRow in self._overlay_fusions:
            if(fusRow):
                objects.extend([x for x in fusRow if x])
        for fusRow in self._custom_overlay_fusions:
            if(fusRow):
                objects.extend([x for x in fusRow if x])
        a.execute('TexturingParams', objects=objects, texture_index=1,
                  rate=float(value) / 100)

    def _onColumnButtonClicked(self, column):
        oldcolumn = self._selectedColumn
        self._selectedColumn = column
        row = self.rowsButtonGroup.checkedId()
        self._removeWinFrame(row, oldcolumn)
        self._createCustomOverlayFusions(row, column)
        if(0 <= row and row < len(self._custom_overlay_fusions)):
            self._addObjectOrFusion_inAnatomistWindowsRow(
                row, self._custom_overlay_fusions[row])
            self._highlightWinFrame(row, column)
        self._updatePalette()
        self._updateSelectedReferenceName()

    def _onRowButtonClicked(self, row):
        self._createCustomOverlayFusions(row, self._selectedColumn)
        self._addObjectOrFusion_inAnatomistWindowsRow(self._selectedRow, self._selectRowForFusions(
            self._selectedRow, thisRowIsSelected=False))  # reset previous selectedRow
        self._removeWinFrame(self._selectedRow, self._selectedColumn)
        isRowUnselected = self._selectedRow == row
        if (isRowUnselected):
            self._unselectRowForFusion(row)
        else:
            self._addObjectOrFusion_inAnatomistWindowsRow(
                row, self._selectRowForFusions(row))
            self._highlightWinFrame(row, self._selectedColumn)
        self._updatePalette()
        self._updateSelectedReferenceName()

    def _removeWinFrame(self, row, column):
        if row >= 0 and row < len(self.mw.anaWinMatrix) and column >= 0:
            winrow = self.mw.anaWinMatrix[row]
            if column < len(winrow):
                anatomistWindow = winrow[column]
                if(anatomistWindow is not None):
                    anatomistWindow.parent().setStyleSheet(
                        'QFrame#winborder { border: 0px; }')  # momoTODO : il n'y a pas de parent!

    def _highlightWinFrame(self, row, column):
        if row >= 0 and row < len(self.mw.anaWinMatrix) and column >= 0:
            winrow = self.mw.anaWinMatrix[row]
            if column < len(winrow):
                if(winrow[column] is not None):
                    winrow[column].parent().setStyleSheet(
                        'QFrame#winborder { border: 2px solid #c06000; border-radius: 4px; }')

    def _updatePalette(self):
        if (self._selectedColumn >= 0 and self._selectedRow >= 0):
            if (self._paletteEditor is not None):
                self._paletteEditor.close()
            selectedImage = self.anatomistObjectList[
                self._selectedRow][self._selectedColumn]
            if(selectedImage is not None):
                self._paletteEditor = PaletteEditor(
                    selectedImage, parent=self.mw, real_max=10000, sliderPrecision=10000, zoom=1)
                self.mw.horizontalLayout.insertWidget(3, self._paletteEditor)

    def _updateSelectedReferenceName(self):
        if (self._selectedColumn >= 0 and self._selectedRow >= 0):
            self.mw.selectedReferenceName.setText('<b><font color=#c06000>' + self._col_titles[
                                                  self._selectedColumn] + '_' + self._row_titles[self._selectedRow] + '</font></b>')
            self.mw.selectedReferenceName.setStyleSheet(
                '#selectedReferenceName { border: 2px solid #c06000; border-radius: 4px; padding: 4px; }')
        else:
            self.mw.selectedReferenceName.setText('None')
            self.mw.selectedReferenceName.setStyleSheet(
                '#selectedReferenceName { border: 0px; }')

    def _unselectRowForFusion(self, row):
        self._selectedRow = -1
        self._unselectButtonInGroup(self.rowsButtonGroup, row)
# button.setText(self._row_titles[self._selectedRow])# momoTODO : pas
# besoin de changer le text si c'est un radio bouton. Le text peut
# contenir une information d'espace (mni, mri...) à ne pas mélanger avec
# la fusion

    def _unselectButtonInGroup(self, group, buttonId):
        if(buttonId >= 0):
            button = group.button(buttonId)
            group.setExclusive(False)
            button.setChecked(False)
            group.setExclusive(True)

    def _selectRowForFusions(self, row, thisRowIsSelected=True):
        self._selectedRow = row
        fusions = None
        isCustomFusionsExist = len(self._custom_overlay_fusions) > 0 and len(
            self._custom_overlay_fusions) > self._selectedRow
        isFusionsExist = len(self._overlay_fusions) > 0 and len(
            self._overlay_fusions) > self._selectedRow
        if isCustomFusionsExist and thisRowIsSelected:
            fusions = self._custom_overlay_fusions[self._selectedRow]
        elif isFusionsExist:
            fusions = self._overlay_fusions[self._selectedRow]
        return fusions

    def _onMaximizeButtonClicked(self):
        print("_onMaximizeButtonClicked")
              # momoTODO utiliser display fusion et afficher la fusion de tous
              # les objets de la ligne sélectionnée

# momoTODO : encadrer la reference utiliser pour la fusion
#    painter = QPainter(mw)
#    painter.setPen(Qt.QColor('yellow'))
#    cellRect = mw.gridLayout.cellRect (rowIndex + 1, c + 1 )
#    cellRectWidth = cellRect.width()
#    cellRect.setWidth(cellRectWidth+200)
#    painter.fillRect(cellRect, Qt.QColor('yellow'))
#    painter.drawRect(cellRect)
