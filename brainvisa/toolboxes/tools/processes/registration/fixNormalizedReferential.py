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

from neuroProcesses import *
import registration
from soma import aims

name = 'Fix normalized image referential'
userLevel = 0


signature=Signature(
  'input', ReadDiskItem( '4D Volume', 'Aims readable volume formats' ),
  #'output', WriteDiskItem( '4D Volume', 'Aims writable volume formats',
  #  exactType = 1 ),
  'normalization_template', Choice(  ( 'FSL 182x218x218, 1x1x1 mm', 0 ),
        ( 'FSL or SPM5 91x109x91, 2x2x2 mm', 1 ),
        ( 'SPM 157x189x136, 1x1x1 mm', 2 ),
        ),
       # ( 'Take info from input (NIFTI) file', 1000 ), ),
  # 'normalization_template_file', ReadDiskItem( '', 'Aims readable volume formats' ),
)

def inizialization( self ):
  pass


def fixtransformation( self, trans, context ):
  transformations = self.input.get( 'transformations' )
  refs = self.input.get( 'referentials' )
  mot = aims.read( list( trans )[0][0].fullPath() )
  mni = aims.StandardReferentials.mniTemplateReferential()
  if refs is None:
    refs = [ mni ]
    transformations = [ mot.toVector().list() ]
  else:
    if mni in refs:
      transformations[ refs.index( mni ) ] = mot.toVector().list()
    else:
      refs.insert( 0, mni )
      transformations.insert( 0, mot.toVector().list() )
  self.input.setMinf( 'transformations', transformations )
  self.input.setMinf( 'referentials', refs )
  self.input.saveMinf()
  if self.input.format in map( getFormat,
                             ( 'NIFTI-1 image', 'GZ Compressed NIFTI-1 image' ) ):
    # re-write image
    context.system( 'AimsFileConvert', self.input, self.input )

def execution( self, context ):
  if not self.input.isWriteable():
    raise RuntimeError( self.input.fullPath() + ' is not writeable' )
  tm = registration.getTransformationManager()
  if self.normalization_template == 0:
    ref = '49e6b349-b115-211a-c8b9-20d0ece9846d'
    trans = tm.findPaths( ref, registration.talairachMNIReferentialId )
    tm.setReferentialTo( self.input, ref )
    self.fixtransformation( trans, context )
  elif self.normalization_template == 1:
    ref = '19bfee8e-51b1-4d9e-8721-990b9f88b12f'
    trans = tm.findPaths( ref, registration.talairachMNIReferentialId )
    tm.setReferentialTo( self.input, ref )
    self.fixtransformation( trans, context )
  elif self.normalization_template == 2:
    ref = 'f3848046-b581-cae4-ecb9-d80ada0278d5'
    trans = tm.findPaths( ref, registration.talairachMNIReferentialId )
    tm.setReferentialTo( self.input, ref )
    self.fixtransformation( trans, context )
  else:
    pass # TODO
