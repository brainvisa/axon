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
from brainvisa import shelltools
import glob
import registration

name = 'Dicom to Nifti Converter Using MRICRON'
roles = ('converter',)
userLevel = 0

def validation():
  mricron = distutils.spawn.find_executable( 'dcm2nii' )
  if not mricron:
    raise ValidationError( 'MRICRON dcm2nii program not found' )

signature = Signature(
  'read', ReadDiskItem( '4D Volume', 'DICOM image',
                        enableConversion = 0 ),
  'write', WriteDiskItem( '4D Volume',
                          [ 'NIFTI-1 image', 'gz compressed NIFTI-1 image' ] ),
  'removeSource', Boolean(),
)


def initialization( self ):
  #self.linkParameters( 'write', 'read' )
  self.removeSource = 0


def execution( self, context ):
  mricron = distutils.spawn.find_executable( 'dcm2nii' )
  outdir = os.path.dirname( self.write.fullPath() )
  #context.write( 'dcm2nii:', mricron )
  fname = os.path.basename( self.read.fullName() )
  while fname[-1] in ( '0', '1', '2', '3', '4', '5', '6', '7', '8', '9' ):
    fname = fname[:-1]
  ofname = os.path.basename( self.write.fullName() )
  while ofname[-1] in ( '0', '1', '2', '3', '4', '5', '6', '7', '8', '9' ):
    ofname = ofname[:-1]
  ext = '.nii'
  print self.write.format, type( self.write.format )
  if str( self.write.format ).startswith( 'gz compressed' ):
    ext += '.gz'
    gopt = 'y'
  else:
    gopt = 'n'
  efiles = glob.glob( os.path.join( outdir, fname + '*' + ext ) )
  context.system( mricron, '-n', 'y', '-f', 'y', '-g', gopt, '-d', 'n', '-e',
                  'n', '-p', 'n', '-i', 'n', '-o', outdir, self.read )
  ofiles = glob.glob( os.path.join( outdir, fname + '*' + ext ) )
  ofiles = [ f for f in ofiles if f not in efiles ]
  for f in ofiles:
    bname = os.path.basename( f )
    bname = bname[ len(fname) : ]
    e = bname.find( '.' )
    if e >= 0:
      bname = ofname + bname[ e: ]
    else:
      bname = ofname + ext
    oname = os.path.join( os.path.dirname( f ), bname )
    if f != oname:
      shelltools.mv( f, oname )
      #shelltools.rm( f )

  registration.getTransformationManager().copyReferential( self.read,
    self.write )

  if self.removeSource:
    for f in self.read.fullPaths():
      shelltools.rm( f )
