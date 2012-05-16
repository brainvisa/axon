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
from brainvisa import shelltools
import shfjGlobals
import os
import registration

name = 'SHFJ: Import GEMS reconstructed T1 MRI'
userLevel = 0

def validation():
  if distutils.spawn.find_executable( 'NmrGemsSignaArchiverGet' ) is None:
    raise ValidationError( _t_( 'Nmr command(s) not found' ) )

signature=Signature(
  'exam_number', Integer(),
  'series', Integer (),
  'anatomy', WriteDiskItem("Raw T1 MRI", "GIS image"),
)

def initialization( self ):
  self.signature[ 'anatomy' ].browseUserLevel = 3


def execution( self, context ):
  if self.exam_number <= 10342:
    raise ValueError( _t_( '<em>%d</em> is not a valid exam number' ) % ( self.exam_number, ) )

  CWD = os.getcwd()
  tmpDir = context.temporary( 'Directory' )
  tmpDirPath = tmpDir.fullPath()
  if os.path.exists(tmpDirPath ) is None:
    os.mkdir( tmpDirPath )
  os.chdir( tmpDirPath)
  tmpDirPath = tmpDir.fullPath()

  if self.series is not None:
    cmd_getSeries = ['NmrGemsSignaArchiverGet', '-e', self.exam_number, '-s', \
     self.series,'-d', tmpDirPath , '-verbose' ]
  context.write( "get recontructed anatomy" )
  context.write( str( cmd_getSeries ) )
  context.system( *cmd_getSeries )
  
  Strseries = 'Exam' + str(self.exam_number) + '_Series00' + str(self.series)
  shelltools.cp(  os.path.join( tmpDirPath, Strseries + '.ima' ) , self.anatomy.fullPath( 0 ) ) 
  shelltools.cp(  os.path.join( tmpDirPath, Strseries + '.dim' ), self.anatomy.fullPath( 1 ) ) 
  shelltools.cp(  os.path.join( tmpDirPath, Strseries + '.ima.minf' ), self.anatomy.fullPath( 0 ) + '.minf') 

  registration.getTransformationManager().createNewReferentialFor( self.anatomy )
