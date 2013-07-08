#! /usr/bin/env python
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
#import anatomist.threaded.api as ana

from PyQt4 import QtCore, Qt
from PyQt4.QtCore import SIGNAL
from PyQt4.QtGui import QPushButton, QPalette, QButtonGroup
from PyQt4.uic import loadUi
from brainvisa.processing.qtgui.neuroProcessesGUI import mainThreadActions
from brainvisa.tools.mainthreadlife import MainThreadLife
from functools import partial
import anatomist.threaded.api as ana

#------------------------------------------------------------------------------
def displayTitledGrid(transformationManager, context, inverseRawColumn,
                      objPathMatrix,
                      rowTitle=['raw_space', "MRI_native_space", "mask",
                        "MNI_space", ],
                      rowColors=['darkOrange', 'blue', "MRI", 'blue',
                        'magenta'], # orange = rawSpace, blue = mri space, magenta = mni space
                      colTitle=['PET', "MRI", "grey"],
                      windowTitle='View grid',
                      linkWindows='space', # linkWindows possible values : 'all' | none | row
                      overlaidImages=[],
                      mainColormap = 'B-W LINEAR',
                      overlayColormap = 'RAINBOW',
                      customOverlayColormap='Blue-White'
                     ):
  _mw = mainThreadActions().call(_displayTitledGrid_onGuiThread,
                                 transformationManager, context,
                                 inverseRawColumn,
                                 objPathMatrix, rowTitle=rowTitle,
                                 rowColors=rowColors, colTitle=colTitle,
                                 windowTitle=windowTitle,
                                 linkWindows=linkWindows,
                                 overlaidImages=overlaidImages,
                                 mainColormap=mainColormap,
                                 overlayColormap=overlayColormap,
                                 customOverlayColormap=customOverlayColormap)
  mw = MainThreadLife(_mw)# pour etre sure que la destruction de la mw se fasse sur le thread de Gui
  return [mw]

def _displayTitledGrid_onGuiThread(transformationManager, context,
                                   inverseRawColumn, objPathMatrix, rowTitle,
                                   rowColors, colTitle, windowTitle,
                                   linkWindows, overlaidImages, mainColormap,
                                   overlayColormap, customOverlayColormap):
  # DisplayTitledGrid doit etre construit sur le thread de Gui pour etre sure que la destruction de la mw se fasse sur le thread de Gui
  TitledGrid = DisplayTitledGrid(objPathMatrix, parent=context,
    mainColormap=mainColormap, overlayColormap=overlayColormap)
  mw = TitledGrid.display(inverseRawColumn=inverseRawColumn,
    windowFlag=QtCore.Qt.Window, windowTitle=windowTitle, rowTitle=rowTitle,
    colTitle=colTitle, rowColors=rowColors, linkWindows=linkWindows,
    overlaidImages=overlaidImages)[0]
  return mw

#------------------------------------------------------------------------------

class DisplayTitledGrid():

  def __init__(self, objPathMatrix, parent=None,
               mainColormap='B-W LINEAR',
               overlayColormap='RAINBOW',
               customOverlayColormap='Blue-White'):
    self.parent = parent
    self._main_colormap = mainColormap
    self._overlay_colormap = overlayColormap
    self._custom_overlay_colormap = customOverlayColormap
    self._loadObjectInAnatomist(objPathMatrix)
    self._overlaid_images = []
    self._overlay_fusions = []
    self._custom_overlay_fusions = []
    self._selectedRow = -1
    self._row_titles = []
    self._col_titles = []

  def display(self, inverseRawColumn=False, windowFlag=QtCore.Qt.Window
              , windowTitle='Compare'
              , rowTitle=["row_1", "row_2", "row_3", "row_4"]
              , colTitle=["col_1", "col_2", "col_3"]
              , rowColors=['darkOrange', 'blue', 'blue', 'magenta']# orange = rawSpace, blue = mri space, magenta = mni space
              , linkWindows='space'# linkWindows possible values : 'all' | none | row, default value : space
              , overlaidImages=[] ): 

    self.mw = self._loadUserInterface()  # create self.mw.gridLayout  
    self.mw.setWindowTitle(windowTitle)    
    self.mw.setParent(self.parent, windowFlag)# if the mw.parent is destroyed, mw is destroyed first
    self.mw.setAttribute(QtCore.Qt.WA_DeleteOnClose)# if the mw is closed ( by user with X ) then mw will be destroyed

    self._row_titles = rowTitle
    self._col_titles = colTitle
    self._custom_row_titles = [ x for x in rowTitle ]

    # load overlay (fusionned) images, and make fusions
    self._loadOverlayImages( overlaidImages )
    self._createOverlayFusions()

    self._addColumnButton(colTitle, inverseRawColumn)
    self._addRowButton(rowTitle, rowColors, inverseRawColumn)

    self._createAndLinkAnatomistWindowsInMainLayout(
      linkWindows, inverseRawColumn, 'Sagittal', rowTitle)

    self.mw.anatomistObjectList = self.anatomistObjectList # momo  :ca sert a quoi?

    # replace individual objects by overlays fusions when applicable
    self._displayFusions()

    self.mw.comboBox.currentIndexChanged.connect(
      partial(self._onComboBox_changed) )
    self.mw.mixingSlider.valueChanged.connect( self._onMixingRateChanged )

    self.mw.show()

    return [self.mw]

#-----------------------------------------------------------------------------            
# private : begins with _
#-----------------------------------------------------------------------------    

  def _loadObjectInAnatomist(self, objPathMatrix):
    a = ana.Anatomist()
    self.anatomistObjectList = []
    for r in range(0, len(objPathMatrix)):
      objPathRow = objPathMatrix[r]
      anaObjRow = []
      for c in range(0, len(objPathRow)):
        objPath = objPathRow[c]
        if (objPath is not None):
          obj = a.loadObject(objPath, forceReload=False)
          obj.setPalette( self._main_colormap )
          anaObjRow.append( obj )
        else:
          anaObjRow.append(None)

      self.anatomistObjectList.append(anaObjRow)

  def _loadUserInterface(self):
    dotIdx = __file__.rindex('.')
    uiFileName = __file__[:dotIdx] + '.ui'
    mw = loadUi(uiFileName)
    mw.mixRate.setText( '50 %' )
    return mw

  def _addColumnButton(self, buttonTitles, inverseRawColumn):
    for buttonIndex in range(0, len(buttonTitles)):
      title = buttonTitles[buttonIndex]
      button = QPushButton(title)
      #button.setDisabled(True)
      if (inverseRawColumn):
        self.mw.gridLayout.addWidget(button, buttonIndex + 1, 0)
        self.mw.gridLayout.setRowStretch(buttonIndex + 1, 10)
      else:
        self.mw.gridLayout.addWidget(button, 0, buttonIndex + 1)
        self.mw.gridLayout.setColumnStretch(buttonIndex + 1, 10)
      button.clicked.connect(
        partial( self._onColumnButtonClicked, buttonIndex ) )

  def _addRowButton(self, buttonTitles, buttonColors, inverseRawColumn):
    bg = QButtonGroup( self.mw )
    self.rowsButtonGroup = bg
    bg.setExclusive( True )
    for buttonIndex in range(0, len(buttonTitles)):
      title = buttonTitles[buttonIndex]
      button = DisplayTitledGrid._createColoredButton(title, buttonColors[buttonIndex])
      bg.addButton( button, buttonIndex )
      if (inverseRawColumn):
        self.mw.gridLayout.addWidget(button, 0, buttonIndex + 1)
        self.mw.gridLayout.setColumnStretch(buttonIndex + 1, 10)
      else:
        self.mw.gridLayout.addWidget(button, buttonIndex + 1, 0)
        self.mw.gridLayout.setRowStretch(buttonIndex + 1, 10)
      button.setToolTip( '<p>Click on this button to superimpose a different image. To do so, click on this row button, then click on a column button to display the column main image as overlay on this row.<p><p>Click again on the tow button to go back to the initial views.</p>' )
    bg.buttonClicked[int].connect( self._onRowButtonClicked )

  @staticmethod
  def _createColoredButton(title, color):
    button = QPushButton(title)
    buttonPalette = QPalette()
    buttonPalette.setColor(QPalette.ButtonText, Qt.QColor(color))
    button.setPalette(buttonPalette)
    #button.setDisabled(True)
    button.setCheckable( True )
    return button

  def _createAndLinkAnatomistWindowsInMainLayout(
      self, linkWindows, inverseRawColumn, initialView, spaceNames):

    mw = self.mw
    mw.anaWinMatrix = []
    for r in range(0, len(self.anatomistObjectList)):
      anaWinRow = self._createAnatomistWindows_InMainLayout(inverseRawColumn, initialView, r)
      DisplayTitledGrid._linkAnatomistWindows(linkWindows, anaWinRow, spaceNames)

  def _createAnatomistWindows_InMainLayout(
      self, inverseRawColumn, view, rowIndex):

    mw = self.mw
    a = ana.Anatomist()
    anaObjRow = self.anatomistObjectList[rowIndex]
    anaWinRow = []
    for c in range(0, len(anaObjRow)):
      anaObj = anaObjRow[c]
      if (anaObj is not None):
        w = a.createWindow(view, no_decoration=True)
        anaObj.addInWindows([w])
        anaWinRow.append(w)
        if (inverseRawColumn):
          mw.gridLayout.addWidget(w.getInternalRep(), c + 1, rowIndex + 1)
        else:
          mw.gridLayout.addWidget(w.getInternalRep(), rowIndex + 1, c + 1)
      else:
        anaWinRow.append(None)
    mw.anaWinMatrix.append(anaWinRow)
    return mw.anaWinMatrix

  @staticmethod
  def _linkAnatomistWindows(linkWindows, anaWinRow, spaceNames):
    if (linkWindows == 'all'):
      DisplayTitledGrid._linkAnatomistWindows_all(anaWinRow)
    elif (linkWindows == 'row'):
      DisplayTitledGrid._linkAnatomistWindows_byRow(anaWinRow)
    elif (linkWindows == 'space'):
      DisplayTitledGrid._linkAnatomistWindows_bySpace(anaWinRow, spaceNames)

  @staticmethod  
  def _linkAnatomistWindows_all(anaWinMatrix):
    a = ana.Anatomist()
    wins = []
    for anaWinRow in anaWinMatrix:
      for w in anaWinRow:
        if (w is not None):
          wins.append(w)

    a.linkWindows(wins, group=None)
    a.execute('WindowConfig', windows=wins, linkedcursor_on_slider_change=1)


  @staticmethod
  def _linkAnatomistWindows_byRow(anaWinMatrix):
    a = ana.Anatomist()
    for anaWinRow in anaWinMatrix:
      wins = []
      for w in anaWinRow:
        if (w is not None):
          wins.append(w)

      a.linkWindows(wins, group=None)
      a.execute('WindowConfig', windows=wins, linkedcursor_on_slider_change=1)  

  @staticmethod
  def _linkAnatomistWindows_bySpace(anaWinMatrix, spaceNames):
    a = ana.Anatomist()
    winsDico = {}
    for anaWinRow, spaceName in zip(anaWinMatrix, spaceNames):
      isRawSpace = spaceName.lower().count('raw') != 0
      if (isRawSpace is False): # inutile de lier les fenetres si leur images sont des raw, donc dans leur propre espace. Par exemple, ne pas lier la pet avec l'irm
        keySpace = DisplayTitledGrid._convertSpaceName_to_key(spaceName)
        for w in anaWinRow:
          if (w is not None):
            if (winsDico.has_key(keySpace)):
              prevWins = winsDico[keySpace]
              prevWins.append(w)
              winsDico.update({keySpace:prevWins})
            else:
              winsDico.update({keySpace:[w]})

    for _k, wins in winsDico.items():
      a.linkWindows(wins, group=None)
      a.execute('WindowConfig', windows=wins, linkedcursor_on_slider_change=1)

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

  def _loadOverlayImages( self, overlaidImages ):
    a = ana.Anatomist()
    images = []
    for filename in overlaidImages:
      if filename: # may be None to leave an un-overlayed row
        image = a.loadObject( filename )
        images.append( image )
        image.setPalette( palette=self._overlay_colormap )
      else: # None
        images.append( None )
    self._overlaid_images = images

  def _createOverlayFusions( self ):
    if len( self._overlaid_images ) == 0:
      # no overlays, nothing to be done.
      return

    a = ana.Anatomist()
    fusions = []
    for line, objRow in enumerate( self.anatomistObjectList ):
      fusline = []
      if line >= len( self._overlaid_images ):
        overlayimage = self._overlaid_images[-1]
      else:
        overlayimage = self._overlaid_images[line]
      for obj in objRow:
        if obj and overlayimage:
          fusion = a.fusionObjects( objects=[obj, overlayimage],
            method='Fusion2DMethod' )
          fusline.append( fusion )
        else:
          fusline.append( None )
      fusions.append( fusline )
    self._overlay_fusions = fusions

  def _createCustomOverlayFusions( self, row, overlayimage ):
    a = ana.Anatomist()
    newoverlay = a.duplicateObject( overlayimage )
    newoverlay.setPalette( self._custom_overlay_colormap )
    fusline = []
    for obj in self.anatomistObjectList[ row ]:
      if obj and obj is not overlayimage:
        fusion = a.fusionObjects( objects=[obj, newoverlay],
            method='Fusion2DMethod' )
        fusline.append( fusion )
      else:
        fusline.append( None )
    if len( self._custom_overlay_fusions ) <= row:
      self._custom_overlay_fusions.extend(
        [ [] ] * ( row + 1 - len( self._custom_overlay_fusions ) ) )
    self._custom_overlay_fusions[ row ] = fusline
    a.execute( 'TexturingParams', objects=[ x for x in fusline if x ],
      texture_index=1, rate=float(self.mw.mixingSlider.value())/100 )

  def _displayFusions( self ):
    for row, anaWinRow in enumerate( self.mw.anaWinMatrix ):
      if row < len( self._overlay_fusions ):
        fusRow = self._overlay_fusions[ row ]
        self._displayFusionsRow( row, fusRow )

  def _displayFusionsRow( self, row, fusRow ):
    anaWinRow = self.mw.anaWinMatrix[ row ]
    objRow = self.anatomistObjectList[ row ]
    for col, win in enumerate( anaWinRow ):
      if win:
        if win.objects:
          win.removeObjects( win.objects )
        if fusRow and fusRow[ col ]:
          win.addObjects( fusRow[ col ] )
        elif objRow and objRow[ col ]:
          win.addObjects( objRow[ col ] )

  def _removeCustomOverlays( self, row ):
    self._custom_overlay_fusions[ row ] = []
    self._displayFusionsRow( row, self._overlay_fusions[ row ] )

  def _onMixingRateChanged( self, value ):
    self.mw.mixRate.setText( str( value ) + ' %' )
    a = ana.Anatomist()
    objects = []
    for fusRow in self._overlay_fusions:
      objects.extend( [ x for x in fusRow if x ] )
    for fusRow in self._custom_overlay_fusions:
      objects.extend( [ x for x in fusRow if x ] )
    a.execute( 'TexturingParams', objects=objects, texture_index=1,
      rate=float(value)/100 )

  def _onColumnButtonClicked( self, column ):
    row = self.rowsButtonGroup.checkedId()
    if row < 0:
      return # no row selected, do nothing
    overlayimage = self.anatomistObjectList[ row ][ column ]
    if overlayimage is None:
      return
    self._createCustomOverlayFusions( row, overlayimage )
    self._displayFusionsRow( row, self._custom_overlay_fusions[ row ] )
    self._custom_row_titles[ row ] = 'with ' + self._col_titles[column]
    self.rowsButtonGroup.button( row ).setText(
      self._custom_row_titles[ row ] )

  def _onRowButtonClicked( self, row ):
    isRowAlreadySelected=self._selectedRow == row
    fusions=None
    if (isRowAlreadySelected == True):
      self._unselectRowForFusion(row)
    else:
      fusions=self._selectRowForFusions(row)
    self._displayFusionsRow(row, fusions)
      
  def _unselectRowForFusion(self, row):    
    self._selectedRow = -1
    button = self.rowsButtonGroup.button( row )
    self.rowsButtonGroup.setExclusive(False)
    button.setChecked(False) # momoTODO : utiliser un radio button car meilleur feedback pour l'utilisateur
    self.rowsButtonGroup.setExclusive(True)
    button.setText(self._row_titles[self._selectedRow])# momoTODO : pas besoin de changer le text si c'est un radio bouton. Le text peut contenir une information d'espace (mni, mri...) à ne pas mélanger avec la fusion

  def _selectRowForFusions(self, row):
    self._selectedRow = row
    button = self.rowsButtonGroup.button( row )
    fusions=None
    if len(self._custom_overlay_fusions) > self._selectedRow:
      fusions = self._custom_overlay_fusions[self._selectedRow]
      if(fusions):
        button.setText(self._custom_row_titles[self._selectedRow]) # momoTODO : pas besoin de changer le text si c'est un radio bouton. Le text peut contenir une information d'espace (mni, mri...) à ne pas mélanger avec la fusion
    return fusions
