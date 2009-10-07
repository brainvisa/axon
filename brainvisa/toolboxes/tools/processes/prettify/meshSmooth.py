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
name = 'Mesh smoothing'
userLevel = 3

signature = Signature(
    'mesh', ReadDiskItem( 'Mesh', [ 'Mesh Mesh', 'Tri Mesh' ] ), 
    'directory', ReadDiskItem( 'Directory', 'Directory' ), 
    'iterations', Integer(), 
    'rate', Float(), 
)


def initialization( self ):
    self.setOptional( 'mesh' )
    self.setOptional( 'directory' )
    self.setOptional( 'iterations' )
    self.setOptional( 'rate' )
    self.iterations = 10;
    self.rate = 0.2

def execution( self, context ):
    files = []
    if self.mesh is None:
        if not ( self.directory is None ):
            d = os.listdir( self.directory.fullPath() )
            p = self.directory.fullPath()
            for i in d:
                try:
                    msh = ReadDiskItem( 'Mesh', [ 'Mesh mesh', 'tri mesh' ] \
                                        ).findValue( os.path.join( p, i ) )
                    files.append( msh )
                except:
                    pass
        else:
            context.write( 'error: must specify one of "mesh" or "directory"' )
            return
    else:
        if not ( self.directory is None ):
            context.write( 'error: must specify only one of "mesh" or \
            "directory"' )
            return
        else:
            files = [ self.mesh ]
    tri = getFormat( 'tri mesh' )
    for i in files:
        cmd = [ 'AimsMeshSmoothing',  '-i', i.fullPath() ]
        if i.format is tri:
            cmd.append( '--tri' )
        if self.iterations is not None:
            cmd += [ '-n', str( self.iterations ) ]
        if self.rate is not None:
            cmd += [ '-I', '-r', str( self.rate ) ]
        context.system( *cmd )

