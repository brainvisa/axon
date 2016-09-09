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
import shfjGlobals, neuroConfig

name = 'FSL to AIMS transformation converter'
roles = ( 'converter', )
userLevel=1

def validation():
  try:
    from soma import aims
  except:
    raise ValidationError( 'aims module not here' )

signature = Signature(
  'read', ReadDiskItem( 'FSL Transformation', 'Matlab file',
                        enableConversion = 0 ),
  'write', WriteDiskItem( 'Transformation matrix', 'Transformation matrix' ),
  'source_volume', ReadDiskItem( '4D Volume',
                                 shfjGlobals.aimsVolumeFormats ),
  'registered_volume', ReadDiskItem( '4D Volume',
                                    shfjGlobals.aimsVolumeFormats ), 
  # 'removeSource', Boolean(),
)

def initialization( self ):
  def writeName( self, proc ):
    if self.registered_volume and self.read:
      file = WriteDiskItem( 'Transformation matrix',
                            'Transformation matrix' ).findValue( self.read )
      name = file.fullPath()
      i = name.rfind( '.' )
      ext = ''
      if i >= 0:
        ext = name[i:]
        name = name[:i]
      name += 'TO' + self.registered_volume.fileName()
      i = name.rfind( '.' )
      if i >= 0:
        name = name[:i]
      name += ext
      # il manque une fonction pour fixer ca...
      file.name = name
      return file
    else:
      return WriteDiskItem( 'Transformation matrix',
                            'Transformation matrix' ).findValue( self.read )
  self.linkParameters( 'write', 'read' )
  self.linkParameters( 'source_volume', 'read' )
  self.linkParameters( 'registered_volume', 'read' )
  self.removeSource = 0

def execution( self, context ):
  from soma import aims
  from soma.aims import fslTransformation
  trm = fslTransformation.fslMatToTrm( self.read.fullPath(),
    self.source_volume.fullPath(), self.registered_volume.fullPath() )
  aims.write( trm, self.write.fullPath() )
  # if self.removeSource: TODO

