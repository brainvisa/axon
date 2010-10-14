# -*- coding: utf-8 -*-
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
rolePriority = 10 # override Aims converter
userLevel = 0

def validation():
  mricron = distutils.spawn.find_executable( 'dcm2nii' )
  if not mricron:
    raise ValidationError( 'MRICRON dcm2nii program not found' )

signature = Signature(
  'input_file', ReadDiskItem( '4D Volume', 'DICOM image',
                        enableConversion = 0 ),
  'write', WriteDiskItem( '4D Volume',
                          [ 'NIFTI-1 image', 'gz compressed NIFTI-1 image' ] ),
  'input_directory', ReadDiskItem( 'Directory', 'Directory' ),
  'removeSource', Boolean(),
)


def initialization( self ):
  #self.linkParameters( 'write', 'read' )
  self.removeSource = 0
  self.setOptional( 'input_file' )
  self.setOptional( 'input_directory' )

def execution( self, context ):
  self.read=None
  if self.input_file:
    self.read=self.input_file
  elif self.input_directory:
    self.read=self.input_directory
  else:
    context.error("You must give a valid value for input_file or input_directory.")
  if self.read:
    mricron = distutils.spawn.find_executable( 'dcm2nii' )
    # creating a temporary directory to write the output nifti file, as we cannot choose the name of the output file with dcm2nii command
    outdir = context.temporary('Directory')
    ext = '.nii'
    if str( self.write.format ).startswith( 'gz compressed' ):
      ext += '.gz'
      gopt = 'y'
    else:
      gopt = 'n'
    
    context.system( mricron, '-n', 'y', '-f', 'y', '-g', gopt, '-d', 'n', '-e',
                    'n', '-p', 'n', '-i', 'n', '-o', outdir, self.read )
    
    outputFile=None
    outputFiles=glob.glob( os.path.join( outdir.fullPath(), '*' + ext ) )
    if len(outputFiles) == 1:
      outputFile = outputFiles[0]
      
    if outputFile and os.path.exists(outputFile):
      if (self.write.fullPath() != outputFile):
        shelltools.mv( outputFile, self.write.fullPath() )
        context.write("Output file ", outputFile, " moved to ", self.write.fullPath())
    else:
      context.error("Problem during the conversion, no output file generated.")
  
  
    registration.getTransformationManager().copyReferential( self.read,
      self.write )
  
    if self.removeSource:
      for f in self.read.fullPaths():
        shelltools.rm( f )
