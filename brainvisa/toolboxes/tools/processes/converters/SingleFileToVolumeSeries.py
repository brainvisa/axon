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

name = 'Single file to volume series'
roles = ('converter',)
userLevel=1

signature = Signature(
  'read', ReadDiskItem( '4D Volume', shfjGlobals.aimsVolumeFormats, 
                        enableConversion = 0 ),
  'write', WriteDiskItem( '4D Volume', map( lambda x: changeToFormatSeries( getFormat( x ) ), shfjGlobals.aimsWriteVolumeFormats ) ),
###  'preferedFormat', apply( Choice, [ ( '<auto>', None ) ] + map( lambda x: (x,getFormat(x)), shfjGlobals.aimsVolumeFormats ) ),
  'removeSource', Boolean(),
  'ascii', Boolean(),
  'voxelType', Choice( ( '<Same as input>', None), 'U8', 'S8', 'U16', 'S16', 'U32', 'S32', 'FLOAT', 'DOUBLE' ),
)

###def findAppropriateFormat( values, proc ):
###  if values.preferedFormat is None:
###    result = WriteDiskItem( '4D Volume', shfjGlobals.aimsWriteVolumeFormats ).findValue( values.read )
###  else:
###    result = WriteDiskItem( '4D Volume', values.preferedFormat ).findValue( values.read )
###  return result

def initialization( self ):
###  self.linkParameters( 'write', [ 'read', 'preferedFormat' ], findAppropriateFormat )
  self.linkParameters( 'write', 'read' )
  self.preferedFormat = None
###  self.setOptional( 'preferedFormat', 'voxelType' )
  self.setOptional( 'voxelType' )
  self.removeSource = 0
  self.ascii = 0
  self.voxelType = None

def execution( self, context ):
  convert = 0
  command = [ 'AimsFileConvert', '-i', '', '-o', '' ]
  if self.ascii:
    convert = 1
    command += [ '-a' ]
  if self.voxelType is not None:
    convert = 1
    command += [ '-t', self.voxelType ]

  voldim = shfjGlobals.aimsVolumeAttributes( self.read ).get( 'volume_dimension' )
  time_length = voldim[ 3 ]
  name_serie = self.write.get( 'name_serie' )
  if name_serie:
    if len( name_serie ) != time_length:
      raise ValueError( _t_( '<em>write</em> parameter must have <em>%d</em> files' ) % ( time_length, ) )
  else:
    nb_digit=len(str(time_length))
    if nb_digit < 4: # nb_digit for the serie zeros are added at the beginning of the number that doesn't have enough digits
      nb_digit=4
    for n in range( time_length ):
      n=str(n)
      while len(n) < nb_digit:
        n = "0"+n
      name_serie.append(n)
    #name_serie = map( str, range( time_length ) )
    
  self.write._setLocal( 'name_serie', name_serie )  

  command = [ 'AimsSubVolume', '--singleminf', '-i', self.read, '-o'] + \
            self.write.firstFullPathsOfEachSeries() + \
             [ '-t' ] + range( len( name_serie ) ) + \
             [ '-T' ] + range( len( name_serie ) )

  if apply( context.system, command ):
    raise Exception( _t_('Error while splitting <em>%s</em>') % \
                     ( self.read.fullPath(), ) )
  if convert:
    for f in self.write.firstFullPathsOfEachSeries():
      command[ 2 ] = f
      command[ 4 ] = f
      if apply( context.system, command ):
        raise Exception( _t_('Error while converting <em>%s</em> to <em>%s</em>') % \
                         ( command[ 2 ], command[ 4 ] ) )


  if self.removeSource:
    for f in self.read.fullPaths():
      shelltools.rm( f )
