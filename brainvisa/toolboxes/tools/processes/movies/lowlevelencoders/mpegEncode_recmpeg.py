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
from brainvisa.validation import ValidationError
from brainvisa.configuration import mpegConfig
import os, shfjGlobals

name = 'Recmpeg MPEG encoder'
userLevel = 2

def validation():
  if 'recmpeg' not in mpegConfig.encoders:
    raise ValidationError( _t_( 'Recmpeg not present' ) )


def codecs():
  c = mpegConfig.codecs.get( 'recmpeg' )
  if c is not None:
    return c
  return {}


signature = Signature(
  'images', ListOf( ReadDiskItem( '2D Image', shfjGlobals.aimsImageFormats,
                                  ignoreAttributes=1 ) ),
  'animation', WriteDiskItem( 'MPEG film', mpegConfig.mpegFormats ),
  'encoding', Choice( *codecs() ),
  'quality', Integer(), 
  'framesPerSecond', Integer(), 
  'coding', String(),
)


def initialization( self ):
  self.quality = 75
  self.framesPerSecond = 25
  self.coding = 'IPPPPPPPPP'


def execution( self, context ):
  #context.write( 'encoder:', self.encoder )
  attrs = shfjGlobals.aimsVolumeAttributes( self.images[ 0 ], forceFormat=1 )
  width = attrs[ 'volume_dimension' ][ 0 ]

  mod16 = width % 16
  if mod16:
    raise RuntimeError( _t_('Image width must be a multiple of 16. Actual width is %d, closest good values are %d and %d.' ) % ( width, width-mod16, width+16-mod16))
    return
  size = str( attrs[ 'volume_dimension' ][ 0 ] ) + 'x' \
         + str( attrs[ 'volume_dimension' ][ 1 ] )
  dir = context.temporary( 'Directory' )
  yuvImage = os.path.join( dir.fullPath(), 'yuvImage.yuv' )
  yuvImages = os.path.join( dir.fullPath(), 'yuvImages.yuv' )
  for image in self.images:
    context.system( 'convert', image.fullPath(), yuvImage, outputLevel=-1 )
    #for n in xrange( self.frameRepetition ):
    context.system( 'cat "' + yuvImage + '" >> "' + yuvImages + '"',
                    outputLevel=-1 )
  context.system( 'recmpeg', '-P', self.encoding, '--coding', self.coding,
                  '--quality', self.quality, '--fps', self.framesPerSecond, 
                  '--picture', size, self.animation.fullPath(), yuvImages )

