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
import shfjGlobals
from brainvisa import anatomist

name = 'Anatomist Show Twins'
userLevel = 3

def validation():
    anatomist.validation()

signature = Signature(
    'graph', ReadDiskItem( 'Roi Graph', 'Graph' ),
    'nomenclature', ReadDiskItem( 'Nomenclature', 'Hierarchy' ), 
    'anatomy', ReadDiskItem( 'T1 MRI', shfjGlobals.anatomistVolumeFormats ),
    'meshes', ListOf( ReadDiskItem( 'Mesh',
                                    shfjGlobals.anatomistMeshFormats ) ),
    )

def initialization( self ):
    def change_meshes( self, proc ):
        meshes = []
        m = ReadDiskItem( 'Hemisphere mesh', 
                          shfjGlobals.anatomistMeshFormats ). \
                          findValue( self.graph )
        if m is not None:
            meshes.append( m )
        return meshes

    self.setOptional( 'nomenclature' )
    self.setOptional( 'anatomy' )
    self.setOptional( 'meshes' )
    self.linkParameters( 'anatomy', 'graph' )
    self.nomenclature = '/usr/local/SHFJ/nomenclature/hierarchy/Twins.hie'
    self.linkParameters( 'meshes', 'graph', change_meshes )

def execution( self, context ):
    a = anatomist.Anatomist()
    selfdrestroy = []
    if self.nomenclature is not None:
        hie = a.loadObject( self.nomenclature.fullPath() )
        selfdestroy.append(hie)
        #a.neverDestroyItem( hie ) 
    selfdestroy.append( a.loadObject( self.graph ) )
    if self.anatomy is not None:
        selfdestroy.append( a.loadObject( self.anatomy ) )
    if self.meshes is not None:
        msh = map( lambda x : a.loadObject( x ), self.meshes )
        selfdestroy += msh
    if self.nomenclature is not None:
        br = a.createWindow( 'Browser' )
        selfdestroy.append( br )
        br.addObjects( [hie] )
        
    win3 = a.createWindow( '3D' )
    selfdestroy.append( win3 )
    #win3.addObjects( [obj] ) # pas de variable obj?
    return selfdestroy
