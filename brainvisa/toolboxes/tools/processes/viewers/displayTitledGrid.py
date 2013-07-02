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
from PyQt4 import QtCore
from brainvisa import registration
from brainvisa.tools.displayTitledGrid import displayTitledGrid
# DEBUG during development
#import brainvisa.tools.displayTitledGrid
#reload( brainvisa.tools.displayTitledGrid )
#displayTitledGrid = brainvisa.tools.displayTitledGrid.displayTitledGrid
# end DEBUG

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
    'anatomist volume formats' ) ),
  'windowTitle', String(),
  'rowTitles', ListOf(String()),
  'rowColors', ListOf(String()),
  'colTitles', ListOf(String()),
  'linkWindows', Choice(('all'), ('row'), ('space')),

  'inverseRawColumn', Boolean(),
)
  
#------------------------------------------------------------------------------

def initialization(self):
  self.setOptional('img1', 'img2', 'img3', 'img4', 'img5', 'img6', 'img7', 'img8', 'img9', 'img10', 'img11', 'img12') 
  self.inverseRawColumn = False
  self.rowTitles = ["row_1", "row_2", "row_3", "row_4"]
  self.colTitles = ["col_1", "col_2", "col_3"]
  self.linkWindows = 'space'
  self.windowTitle = 'view grid'
  self.rowColors = ['darkOrange', 'blue', 'blue', 'magenta']# orange = rawSpace, blue = mri space, magenta = mni space
   
#------------------------------------------------------------------------------

def execution(self, context):
  print "\n start ", name, "\n"
  
  # context will be mw's parent. This is essential if mw has connected buttons (or listen any signals)
  # so when context is closed -> delete -> delete child -> mw will be deleted
  context.setAttribute(QtCore.Qt.WA_DeleteOnClose) 
  # qd on relance le process, closed n'est pas envoyé, donc mw reste
  
  img = []
  for selfImg in [self.img1, self.img2, self.img3, self.img4, self.img5, self.img6, self.img7, self.img8, self.img9, self.img10, self.img11, self.img12 ]:
    if(selfImg is not None and os.path.exists(selfImg.fullPath())):
      img.append(selfImg.fullPath())
    else:
      img.append(None)

  overlaid_images = [ x.fullPath() for x in self.overlaid_images \
    if x is not None and os.path.exists(x.fullPath()) ]

  objs = displayTitledGrid(registration.getTransformationManager(), context,
                            self.inverseRawColumn
                            , [[img[0], img[1], img[2]]
                             , [img[3], img[4], img[5]]
                             , [img[6], img[7], img[8]]
                             , [img[9], img[10], img[11]]] 
                             , rowTitle=self.rowTitles,
                             rowColors=self.rowColors, colTitle=self.colTitles,
                             windowTitle=self.windowTitle
                             , linkWindows=self.linkWindows,
                             overlaid_images=overlaid_images
                            )

  print "\n stop ", name, "\n"
  return objs

