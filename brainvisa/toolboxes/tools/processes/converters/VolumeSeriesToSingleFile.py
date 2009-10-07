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

name = 'Volume series to single file'
roles = ('converter',)
userLevel = 2

signature = Signature(
  'read', ReadDiskItem( '4D Volume', 
                        map( lambda x: changeToFormatSeries( getFormat( x ) ), 
                             shfjGlobals.aimsVolumeFormats ),
                        enableConversion = 0 ),
  'write', WriteDiskItem( '4D Volume',  shfjGlobals.aimsWriteVolumeFormats ),
  'preferedFormat', apply( Choice, [ ( '<auto>', None ) ] + map( lambda x: (x,getFormat(x)), shfjGlobals.aimsVolumeFormats ) ),
  'removeSource', Boolean(),
  'ascii', Boolean(),
  'voxelType', Choice( ( '<Same as input>', None), 'U8', 'S8', 'U16', 'S16', 'U32', 'S32', 'FLOAT', 'DOUBLE' ),
)

def findAppropriateFormat( values, proc ):
  if values.preferedFormat is None:
    result = WriteDiskItem( '4D Volume', shfjGlobals.aimsWriteVolumeFormats ).findValue( values.read )
  else:
    result = WriteDiskItem( '4D Volume', values.preferedFormat ).findValue( values.read )
  return result

def initialization( self ):
  self.linkParameters( 'write', [ 'read', 'preferedFormat' ], findAppropriateFormat )
  self.preferedFormat = None
  self.setOptional( 'preferedFormat', 'voxelType' )
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

  if apply( context.system, [ 'AimsTCat', '-o', self.write, '-i' ] + self.read.firstFullPathsOfEachSeries() ):
      raise Exception( _t_('Error while pulling <em>%s</em> to <em>%s</em>') % \
                       ( self.read.fullPath(), self.write.fullPath() ) )
  if convert:
    command[ 2 ] = self.write
    command[ 4 ] = self.write
    if apply( context.system, command ):
          raise Exception( _t_('Error while converting <em>%s</em> to <em>%s</em>') % \
                       ( command[ 2 ], command[ 4 ] ) )
  if self.removeSource:
    for f in self.read.fullPaths():
      shelltools.rm( f )
