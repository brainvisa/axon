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

from brainvisa.processes import *
from soma.qt_gui.qt_backend import QtCore
from brainvisa import registration
from brainvisa.tools.displayTitledGrid import displayTitledGrid

userLevel = 2 
name = 'view images in a titled grid'

#------------------------------------------------------------------------------

signature = Signature(
  'img1', ReadDiskItem('4D Volume', 'anatomist volume formats'),
  'img2', ReadDiskItem('4D Volume', 'anatomist volume formats'),
  'img3', ReadDiskItem('4D Volume', 'anatomist volume formats'),
  'img4', ReadDiskItem('4D Volume', 'anatomist volume formats'),
  'img5', ReadDiskItem('4D Volume', 'anatomist volume formats'),
  'img6', ReadDiskItem('4D Volume', 'anatomist volume formats'),
  'img7', ReadDiskItem('4D Volume', 'anatomist volume formats'),
  'img8', ReadDiskItem('4D Volume', 'anatomist volume formats'),
  'img9', ReadDiskItem('4D Volume', 'anatomist volume formats'),
  'img10', ReadDiskItem('4D Volume', 'anatomist volume formats'),
  'img11', ReadDiskItem('4D Volume', 'anatomist volume formats'),
  'img12', ReadDiskItem('4D Volume', 'anatomist volume formats'),
  'overlaid_images', ListOf( ReadDiskItem( '4D Volume',
    'anatomist volume formats' ), allowNone=True ),
  'windowTitle', String(),
  'rowTitles', ListOf(String()),
  'rowButtonSubTitles', ListOf(String()),
  'rowColors', ListOf(String()),
  'colTitles', ListOf(String()),
  'linkWindows', Choice(('all'), ('row'), ('space')),
  'inverseRawColumn', Boolean(),
  'mainColormap', String(),
  'overlayColormap', String(),
  'customOverlayColormap', String(),
)

#------------------------------------------------------------------------------

def initialization(self):
  self.setOptional('overlaid_images', 'customOverlayColormap', 'img1', 'img2', 'img3', 'img4', 'img5', 'img6', 'img7', 'img8', 'img9', 'img10', 'img11', 'img12', 'rowButtonSubTitles') 
  self.inverseRawColumn = False
  self.rowTitles = ["row_1", "row_2", "row_3", "row_4"]
  self.colTitles = ["col_1", "col_2", "col_3"]
  self.linkWindows = 'space'
  self.windowTitle = 'view grid'
  self.rowColors = ['darkOrange', 'blue', 'blue', 'magenta']# orange = rawSpace, blue = mri space, magenta = mni space
  self.mainColormap = 'B-W LINEAR'
  self.overlayColormap = 'RAINBOW'
  self.customOverlayColormap = 'Blue-White'

#------------------------------------------------------------------------------

def execution(self, context):

  images = [ self.img1, self.img2, self.img3, self.img4, self.img5, self.img6, self.img7, self.img8, self.img9, self.img10, self.img11, self.img12 ]
  invalidImages = []
  for i in range(len(images)):
    img = images[i]
    if (img is not None and os.path.exists(img.fullPath()) == False):
      images[i]=None

  kwproc = {
    'images' : images,
    'overlaid_images' : self.overlaid_images,
    'windowTitle' : self.windowTitle,
    'rowTitles' : self.rowTitles,
    'rowColors' : self.rowColors,
    'colTitles' : self.colTitles,
    'linkWindows' : self.linkWindows,
    'inverseRawColumn' : self.inverseRawColumn,
    'mainColormap' : self.mainColormap,
    'overlayColormap' : self.overlayColormap,
    'customOverlayColormap' : self.customOverlayColormap,
    'rowButtonSubTitles':self.rowButtonSubTitles,
  }
  return context.runProcess( 'displayTitledGrid_listinput', **kwproc )

