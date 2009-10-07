# -*- coding: iso-8859-1 -*-

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


#Interface de la serie de script fusionXContrastes datant de la version 
#d'anatomist 1.24 environ.


from neuroProcesses import *
import shfjGlobals

name = 'Fusion Linear Contrastes'
userLevel=2

signature = Signature(
  'read', ListOf( ReadDiskItem( '3D Volume', shfjGlobals.anatomistVolumeFormats) ),
  'levels', ListOf( Number() ),
  'write', WriteDiskItem( '3D Volume',shfjGlobals.aimsWriteVolumeFormats ),
)

def initialization( self ):
  self.levels= [ 5, 10, 20, 40, 80 ]

def execution( self, context ):
  list_write = []
  i = 0
  level = 1
  for read in self.read:
    if i < len( self.levels ):
      level = self.levels[ i ]
    else:
      level = level + 1
    write = context.temporary( 'File' )
    context.system( 'VipSingleThreshold', '-i' , read.fullName(), '-o', write.fullName(), '-m', 'gt', '-t', '0', '-c', 'b')
    context.system( 'AimsReplaceLevel', '-i' , write, '-g', '255', '-n', level, '-o', write )
    list_write.append( write )
    i = i + 1
    
  for i in xrange( len( list_write ) - 2 ):
    context.system( 'AimsLinearComb', '-i' , list_write[ 0 ], '-j', list_write[ i + 1 ], '-o', list_write[0] )
  context.system( 'AimsLinearComb', '-i' , list_write[ 0 ], '-j', list_write[ -1 ], '-o', self.write )
  
  context.system( 'VipSplineResamp', '-i' ,  write.fullName(), '-t',  write.fullName(), '-did', '-or', '0', '-o', write.fullName() )  

