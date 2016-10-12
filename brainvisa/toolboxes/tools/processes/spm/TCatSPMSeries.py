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
from brainvisa.tools import aimsGlobals
import os.path

name = 'Create a 4D volume from a list of 3D Volumes'

signature = Signature(
  'SPM_files', ListOf( ReadDiskItem( '3D volume', 'Aims readable volume formats', 
                       ignoreAttributes=1 ) ),
  'SPM4D_volume',  WriteDiskItem( '4D volume', 'Aims writable volume formats'),                    
  'display_with_anatomist', Boolean(),
)

def initialization( self ):
  self.display_with_anatomist = False

def execution( self, context ):
  self.SPM_files[0].setMinf( 'series_filenames', [item.fullPath() for item in self.SPM_files] )

  VolumeDimensions  = self.SPM_files[0].get('volume_dimension')
  if VolumeDimensions is not None:
    self.SPM4D_volume.setMinf( 'volume_dimension', VolumeDimensions  )
  else:
    AimsFileInfo = aimsGlobals.aimsVolumeAttributes( self.SPM_files[0] )
    volume_dimensionXYZ =  AimsFileInfo[ 'volume_dimension' ][ :3 ]
    context.write( volume_dimensionXYZ )
    self.SPM4D_volume.setMinf( 'volume_dimension',  volume_dimensionXYZ  + [ len( self.SPM_files ) ] )

  series_filenames = ""
  for i in  xrange( len( self.SPM_files ) ):
    series_filenames +=  "'" + self.SPM_files[i].fullPath() + "'," 
  series_filenames = series_filenames[:-1]

  # perform the temporal concatenation 
  cmd = ["AimsTCat", "-i" ] + self.SPM_files + [ "-o", self.SPM4D_volume.fullPath() ]
  context.write( str(cmd) )
  context.system( *cmd )

  self.SPM4D_volume.saveMinf()

  if self.display_with_anatomist:
    return context.runProcess( 'AnatomistShowVolume', self.SPM_files[0] )
