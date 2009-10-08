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
from brainvisa import anatomist

name = 'Anatomist Show 3D Fusion'
userLevel = 0

def validation():
  anatomist.validation()

signature = Signature(
  'functional_volume',
  ReadDiskItem(  '4D Volume', shfjGlobals.anatomistVolumeFormats ),
  'mesh', ReadDiskItem( "Mesh", shfjGlobals.anatomistMeshFormats ),
  'calculation_method', Choice( ( _t_( 'Point' ), 'point' ),
                                ( _t_( 'Point shifted inside' ),
                                  'point_offset_internal' ),
                                ( _t_( 'Point shifted outside' ),
                                  'point_offset_external' ),
                                ( _t_( 'Line' ), 'line' ),
                                ( _t_( 'Line internal' ), 'line_internal' ),
                                ( _t_( 'Sphere' ), 'sphere' ),
                                ),
  'submethod', Choice( ( _t_( 'Maximum' ), 'max' ),
                       ( _t_( 'Minimum' ), 'min' ),
                       ( _t_( 'Mean' ), 'mean' ),
                       ( _t_( 'Corrected mean' ), 'mean_corrected' ),
                       ( _t_( 'Enhanced mean' ), 'mean_enhanced' ),
                       ), 
  'depth', Float(), 
  'step', Float(), 
  )
	
def initialization( self ):
  self.setOptional( 'depth' )
  self.setOptional( 'step' )

def execution( self, context ):
  a = anatomist.Anatomist()
  mesh = a.loadObject( self.mesh )
  func = a.loadObject( self.functional_volume )
  func.setPalette( a.getPalette("Rainbow1-fusion") )
  fusion = a.fusionObjects( [mesh, func], method='Fusion3DMethod' )
  if self.functional_volume is not None \
    and self.functional_volume.type.isA( 'Label Volume' ):
      a.execute("TexturingParams", objects=[fusion], interpolation = 'rgb' )
  context.write( self.calculation_method )
  if self.calculation_method != 'point' or self.submethod != 'max' \
         or self.depth is not None or self.step is not None:
    a.execute("Fusion3DParams", object=fusion, method = self.calculation_method,
                             submethod = self.submethod,
                             depth = self.depth, step =self.step )
  win = a.createWindow( '3D' )
  win.addObjects( [fusion] )
  return [ mesh, func, fusion, win ]

