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
from brainvisa.tools import aimsGlobals
from brainvisa import shelltools

name = 'Aims Texture Converter'
roles = ('converter',)
userLevel = 0

signature = Signature(
  'read', ReadDiskItem( 'Texture', 'Aims texture formats',
                        enableConversion = 0 ),
  'write', WriteDiskItem( 'Texture',  'Aims texture formats' ),
  'preferedFormat', apply( Choice, [ ( '<auto>', None ) ] + map( lambda x: (x,getFormat(x)), aimsGlobals.aimsTextureFormats ) ),
  'removeSource', Boolean(),
  'ascii', Boolean(),
)

def findAppropriateFormat( values, proc ):
  if values.preferedFormat is None:
    result = WriteDiskItem( 'Texture', 'Aims texture formats' ).findValue( values.read )
  else:
    result = WriteDiskItem( 'Texture', values.preferedFormat ).findValue( values.read )
  return result

def initialization( self ):
  self.linkParameters( 'write', [ 'read', 'preferedFormat' ], findAppropriateFormat )
  self.preferedFormat = None
  self.setOptional( 'preferedFormat' )
  self.removeSource = 0
  self.ascii = 0


def execution( self, context ):
  convert = 0
  command = [ 'AimsFileConvert', '-i', self.read, '-o', self.write ]
  if self.ascii:
    convert = 1
    command += [ '-a' ]

  if apply( context.system, command ):
    raise Exception( _t_('Error while converting <em>%s</em> to <em>%s</em>') % \
                         ( command[ 2 ], command[ 4 ] ) )
  if self.removeSource:
    for f in self.read.fullPaths():
      shelltools.rm( f )
