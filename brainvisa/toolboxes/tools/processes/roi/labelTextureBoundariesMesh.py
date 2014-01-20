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
from brainvisa import registration
try:
    from soma import aims
except:
    pass

name = 'Label Texture Boundaries Mesh'
userLevel = 0

def validation():
    try:
        from soma import aims
    except:
        raise ValidationError( 'soma.aims module cannot be imported' )

signature = Signature(
    'label_texture', ReadDiskItem( 'Label Texture', 'aims texture formats' ),
    'mesh', ReadDiskItem( 'Mesh', 'aims mesh formats' ),
    'output_boundaries_mesh', WriteDiskItem( 'Mesh',
        [ 'Mesh mesh', 'Texture' ] ),
    'line_width', Float(),
    'mesh_color', ListOf( Float() ),
)


def initialization( self ):
    self.line_width = 5.
    self.linkParameters( 'mesh', 'label_texture' )


def execution( self, context ):
    tex = aims.read( self.label_texture.fullPath() )
    mesh = aims.read( self.mesh.fullPath() )
    outmesh = aims.SurfaceManip.meshTextureBoundary( mesh, tex, -1 )
    diffuse = [ 1., 0, 0., 1. ]
    ncomp = min( len( self.mesh_color ), 4 )
    diffuse[ : ncomp ] = self.mesh_color[ : ncomp ]
    context.write( self.mesh_color )
    outmesh.header()[ 'material' ] = \
        { 'line_width' : self.line_width, 'diffuse' : diffuse }
    aims.write( outmesh, self.output_boundaries_mesh.fullPath() )
    tm = registration.getTransformationManager()
    tm.copyReferential( self.mesh, self.output_boundaries_mesh )

