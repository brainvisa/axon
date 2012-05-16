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
name = 'Morphomaths basic'
userLevel = 3


signature = Signature(
  'type'             , Choice(('Closing',1),
                              ('Opening',2),
                              ('Errosion',3),
                              ('Dilation',4)),
  'image_in'         , ReadDiskItem( 'Label Volume',shfjGlobals.anatomistVolumeFormats),
  'radius'           , Number(),
  'image_out'        , WriteDiskItem('Label Volume', shfjGlobals.anatomistVolumeFormats)
  )

def initialization( self ):
  self.linkParameters('image_out', 'image_in')
  self.radius=1;

def execution( self, context ):
    if self.type==1:
      context.write('AimsClosing',
                     "-i",self.image_in.fullPath(),
                     "-o",self.image_out.fullPath(),
                     "-r",str(self.radius)
                     )
      context.system('AimsClosing',
                     "-i",self.image_in.fullPath(),
                     "-o",self.image_out.fullPath(),
                     "-r",str(self.radius)
                     )
    if self.type==2:
      context.write('AimsOpening',
                     "-i",self.image_in.fullPath(),
                     "-o",self.image_out.fullPath(),
                     "-e",str(self.radius)
                     )
      context.system('AimsOpening',
                     "-i",self.image_in.fullPath(),
                     "-o",self.image_out.fullPath(),
                     "-e",str(self.radius)
                     )
    if self.type==3:
      context.write('AimsErosion',
                     "-i",self.image_in.fullPath(),
                     "-o",self.image_out.fullPath(),
                     "-e",str(self.radius)
                     )
      context.system('AimsErosion',
                     "-i",self.image_in.fullPath(),
                     "-o",self.image_out.fullPath(),
                     "-e",str(self.radius)
                     )
    if self.type==4:
      context.write('AimsDilation',
                     "-i",self.image_in.fullPath(),
                     "-o",self.image_out.fullPath(),
                     "-e",str(self.radius)
                     )
      context.system('AimsDilation',
                     "-i",self.image_in.fullPath(),
                     "-o",self.image_out.fullPath(),
                     "-e",str(self.radius)
                     )
            
