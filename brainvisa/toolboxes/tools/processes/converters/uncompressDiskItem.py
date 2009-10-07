#  This software and supporting documentation are distributed by
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
import neuroDiskItems
import gzip

name = 'uncompress any disk item'
roles = ('converter',)
userLevel=1

def possibleConversions():
  any = getDiskItemType( 'Any type' )
  for format in neuroDiskItems.getAllFormats():
    for start in ( 'gz compressed ', 'Z compressed ' ):
      if format.name.startswith( start ):
        destFormat = getFormat( format.name[ len(start): ], None )
        if destFormat is not None:
          yield ( ( any, format ), ( any, destFormat ) )


signature = Signature(
  'read', ReadDiskItem( 'Any type',
                        [i[0][1] for i in possibleConversions()],
                        enableConversion = False ),
  'write', WriteDiskItem( 'Any type', [i[1][1] for i in possibleConversions()] ),
  'removeSource', Boolean(),
)

# cleanup
def initialization( self ):
  def updateformat( self, proc ):
    if self.read is None:
      return None
    fmt = str( getFormat( self.read.format ) )
    if fmt.startswith( 'Z compressed ' ):
      fmts = fmt[ 13: ]
    else:
      fmts = fmt[ 14: ] # gz
    tp = getDiskItemType( self.read.type )
    proc.signature[ 'write' ] = WriteDiskItem( tp, fmts )
    x = WriteDiskItem( tp, fmts )
    return x.findValue( self.read )
  self.linkParameters( 'write', 'read', updateformat )
  self.removeSource = 0


def execution( self, context ):
  source = self.read.fullPaths()
  dest = [] + self.write.fullPaths() # force copy
  for i in xrange( len( source ) ):
    d = dest[ 0 ]
    s = os.path.basename( source[i] )
    x = s.rfind( '.' )
    if x:
      y = s.rfind( '.', 0, x-1 )
      if y:
        ext = s[ y:x ]
        k = filter( lambda z: z.endswith( ext ), dest )
        if len( k ) > 0:
          d = k[ 0 ]
    f = gzip.open( source[i], 'rb' )
    g = open( d, 'wb' )
    while 1:
      buf = f.read( 1000 )
      if len( buf ) == 0:
        break
      g.write( buf )
    f.close()
    g.close()
    dest.remove( d )
    if self.removeSource:
      os.unlink( source[ i ] )
  # copy minf file
  if os.path.exists( self.read.minfFileName() ):
    shutil.copyfile( self.read.minfFileName(), self.write.minfFileName() )
