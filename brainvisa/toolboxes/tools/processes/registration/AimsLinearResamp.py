# Copyright IFR 49 (1995-2009)
#
#  This software and supporting documentation were developed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL-B license under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the 
# terms of the CeCILL-B license as circulated by CEA, CNRS
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
# knowledge of the CeCILL-B license and that you accept its terms.

from neuroProcesses import *
from brainvisa import shelltools
import shfjGlobals




name = 'Resampling'
userLevel = 2

signature = Signature( 
  'image_input', ReadDiskItem( '4D Volume', shfjGlobals.aimsVolumeFormats ),
  'image_output', WriteDiskItem( '4D Volume', shfjGlobals.anatomistVolumeFormats ),
  'template', ReadDiskItem( '4D Volume', shfjGlobals.aimsVolumeFormats ),
  'motion', ReadDiskItem ('Transformation matrix', 'Transformation matrix'),
  'dimX', Integer(),
  'dimY', Integer(),
  'dimZ', Integer(),
  'sizeX', Float(),
  'sizeY', Float(),
  'sizeZ', Float(),
 )
  

def initialization( self ):
  self.linkParameters( 'image_output', 'image_input' )
  self.setOptional('dimX', 'dimY', 'dimZ', 'sizeX', 'sizeY', 'sizeZ', 'motion', 'template')
  

def execution( self, context ):
  
  command = [ 'AimsResample', '-i', self.image_input, '-o', self.image_output ]
  
  if self.template is not None :
    template = str(self.template)
    command += [ '-r', template]


  if (self.dimX is None) and (self.dimY is None) and (self.dimZ is None) and (self.sizeX is None) and (self.sizeY is None) and (self.sizeZ is None) and (self.motion is None) :
    context.write('One field is mandatory (dimX or dimY or dimZ or SizeX or SizeY or SizeZ or motion)')
  else :  
    if self.dimX is not None :
      command += [ '--dx', self.dimX]

    if self.dimY is not None :
      command += [ '--dy', self.dimY]

    if self.dimZ is not None :
      command += [ '--dz', self.dimZ]

    if self.sizeX is not None :
      command += [ '--sx', self.sizeX]

    if self.sizeY is not None :
      command += [ '--sy', self.sizeY]

    if self.sizeZ is not None :
      command += [ '--sz', self.sizeZ]

    if self.motion is not None :
      command += [ '-m', self.motion]


    context.system( *command )


  
