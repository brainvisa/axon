# -*- coding: utf-8 -*-
from brainvisa.processes import *
from six.moves import range

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
  'overlaid_images', ListOf(ReadDiskItem('4D Volume',
                                         'anatomist volume formats'), allowNone=True),
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
    self.setOptional(
        'overlaid_images', 'customOverlayColormap', 'img1', 'img2', 'img3', 'img4',
                     'img5', 'img6', 'img7', 'img8', 'img9', 'img10', 'img11', 'img12', 'rowButtonSubTitles')
    self.inverseRawColumn = False
    self.rowTitles = ["row_1", "row_2", "row_3", "row_4"]
    self.colTitles = ["col_1", "col_2", "col_3"]
    self.linkWindows = 'space'
    self.windowTitle = 'view grid'
    self.rowColors = ['darkOrange', 'blue', 'blue', 'magenta']
        # orange = rawSpace, blue = mri space, magenta = mni space
    self.mainColormap = 'B-W LINEAR'
    self.overlayColormap = 'RAINBOW'
    self.customOverlayColormap = 'Blue-White'

#------------------------------------------------------------------------------


def execution(self, context):

    images = [self.img1, self.img2, self.img3, self.img4, self.img5, self.img6,
              self.img7, self.img8, self.img9, self.img10, self.img11, self.img12]
    invalidImages = []
    for i in range(len(images)):
        img = images[i]
        if (img is not None and os.path.exists(img.fullPath()) == False):
            images[i] = None

    kwproc = {
        'images': images,
      'overlaid_images': self.overlaid_images,
      'windowTitle': self.windowTitle,
      'rowTitles': self.rowTitles,
      'rowColors': self.rowColors,
      'colTitles': self.colTitles,
      'linkWindows': self.linkWindows,
      'inverseRawColumn': self.inverseRawColumn,
      'mainColormap': self.mainColormap,
      'overlayColormap': self.overlayColormap,
      'customOverlayColormap': self.customOverlayColormap,
      'rowButtonSubTitles': self.rowButtonSubTitles,
    }
    return context.runProcess('displayTitledGrid_listinput', **kwproc)
