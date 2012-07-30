# -*- coding: utf-8 -*-
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
import registration
import shfjGlobals
from soma import aims


name = 'IsTheSameScannerBasedReferential'
userLevel = 2

signature = Signature( 
  'Volume_1', ReadDiskItem( "T1 MRI", getAllFormats() ),
  'Volume_2', ReadDiskItem( "T1 MRI", getAllFormats() ),
 )
  

#def initialization( self ):
  #pass

  
def execution( self, context ):
  context.write('Under development')
  
  #update the scanner based referential A by the the scanner based referential B
  #if A has already a scanner based referential included in other transformation, update them too.
  #to update a scanner based referential, change the 'destination_referential' in the .trmMinf file
 
  #Check if there is not a soma-wkf using
  #databases=[h.name for h in neuroHierarchy.hierarchies()]
  #print databases


  #for each volume, check if there is a scanner based referential
  #tm = registration.getTransformationManager()
  #vol1 = tm.referential( self.Volume_1 )
  #vol2 = tm.referential( self.Volume_2 )
  #if (vol1 is None or vol1 is None ) :
    #context.write("One of both volume doesn't have a Scanner Based Referential")
    
    


  
  
  
  


  
  