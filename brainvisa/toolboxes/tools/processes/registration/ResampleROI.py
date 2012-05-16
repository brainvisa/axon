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
import shfjGlobals

name = 'Resample ROI graph'
userLevel = 1

signature = Signature(
   'source_graph', ReadDiskItem( 'ROI','Graph and Data' ),
   'transformation', ReadDiskItem( 'Transformation matrix', 
                                   'Transformation matrix' ),
   'destination_image', ReadDiskItem( '3D volume', shfjGlobals.aimsVolumeFormats ),
   'result_graph', WriteDiskItem( 'ROI', 'Graph and data' ),
)


def initialization( self ):

  self.setOptional( 'transformation' )


def execution( self, context ):
  tmp = context.temporary( 'Graph and data' )
  context.system( 'AimsGraphConvert', '-i', self.source_graph, '-o', tmp, 
    '--volume' )
  volume = os.path.join( tmp.fullName() + '.data', 'roi_Volume.ima' )
  if not os.path.exists( volume ):
    volume = os.path.join( tmp.fullName() + '.data', 'cluster_Volume.ima' )
    if not os.path.exists( volume ):
      raise RuntimeError( _t_( 'Can only resample ROI or Cluster graphs' ) )
  context.system( 'AimsLinearComb', '-i', volume, '-e', 1, '-o', volume )
  if ( self.transformation is None ):
    context.system( 'VipSplineResamp', '-i', volume, '-o', volume, '-w', 't',
      '-t', self.destination_image.fullName(), '-did',
      '-or', 0 )
  else:
    context.system( 'VipSplineResamp', '-i', volume, '-o', volume, '-w', 't',
      '-t', self.destination_image.fullName(), '-d', self.transformation,
      '-or', 0 )
  context.system( 'AimsLinearComb', '-i', volume, '-e', -1, '-o', volume )
  file = open( tmp.fullPath() )
  lines = file.readlines()
  file.close()
  file = open( tmp.fullPath(), 'w' )
  for l in lines:
    if l[ :10 ] == 'voxel_size':
      print >> file, 'voxel_size\t', string.join( map( str, self.destination_image.get( 'voxel_size' ) ) )
    elif l[ :15 ] == 'boundingbox_max':
      vd = self.destination_image.get( 'volume_dimension' )
      print >> file, 'boundingbox_max\t', vd[0]-1, vd[1]-1, vd[2]-1
    else:
     print >> file, l
  file.close()
  context.system( 'AimsGraphConvert', '-i', tmp, '-o', self.result_graph,
    '--bucket' )
