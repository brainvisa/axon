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
import shfjGlobals
import registration

name = 'FSL Normalization to AIMS converter'
userLevel=2

def validation():
  try:
    from soma import aims
  except:
    raise ValidationError( 'aims module not here' )

signature = Signature(
  'read', ReadDiskItem( 'FSL Transformation', 'Matlab file',
                        enableConversion = 0 ),
  'source_volume', ReadDiskItem( '4D Volume',
                                 shfjGlobals.aimsVolumeFormats ),
  'write', WriteDiskItem( 'Transform Raw T1 MRI to Talairach-MNI template-SPM', 'Transformation matrix' ),
  'registered_volume', ReadDiskItem( '4D Volume',
                                    shfjGlobals.aimsVolumeFormats ),
  'template_resolution', Choice( ( '1x1x1 mm', 0 ), ( '2x2x2 mm', 1 ), ),
  # 'removeSource', Boolean(),
)

def initialization( self ):
  self.linkParameters( 'source_volume', 'read' )
  self.linkParameters( 'write', 'source_volume' )
  self.linkParameters( 'registered_volume', 'read' )
  self.setOptional( 'registered_volume' )
  #self.removeSource = 0

def execution( self, context ):
  from soma import aims
  from soma.aims import fslTransformation
  if self.registered_volume is None:
    if self.template_resolution == 1:
      tmplimg = { 'voxel_size' : [ 2, 2, 2 ],
        'volume_dimension' : [ 91, 109, 91 ] }
    else:
      tmplimg = { 'voxel_size' : [ 1, 1, 1 ],
        'volume_dimension' : [ 182, 218, 182 ] }
  else:
    tmplimg = self.registered_volume.fullPath()
  # get aims -> aims matrix from read to template
  trm = fslTransformation.fslMatToTrm( self.read.fullPath(),
    self.source_volume.fullPath(), tmplimg )
  # now go to the MNI template coords
  rp = list( registration.getTransformationManager().findPaths( \
    'f3848046-b581-cae4-ecb9-d80ada0278d5',
    registration.talairachMNIReferentialId ) )
  if len( rp ) != 1 or len( rp[0] ) != 1:
    raise RuntimeError( 'Could not find standard transformation for MNI ' \
      'template' )
    return
  context.write( rp )
  aimsToMni = aims.read( rp[0][0].fullPath() )
  trm = aimsToMni * trm
  aims.write( trm, self.write.fullPath() )
  # if self.removeSource: TODO

