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

#
# Create and launch SPM High-Dimensional Warping
# (See below for SPM8 documentation)
#

#------------------------------------------------------------------------------        
# FROM spm documentation (SPM8 manual: www.fil.ion.ucl.ac.uk/spm/doc/spm8_manual.pdf‎): 
# 6.2
# Normalise: Write
# Allows previously estimated warps (stored in imagename’ sn.mat’ files) to be applied to series of
# images.
# 
#------------------------------------------------------------------------------        

from brainvisa.processes import *
import brainvisa.tools.spm_run as spm
from brainvisa.tools.spm_registration import  initializeWriteNormalisation_withSPM8DefaultValues, writeNormalisationWriteBatch

#------------------------------------------------------------------------------
configuration = Application().configuration
#------------------------------------------------------------------------------

def validation():
  return spm.validation(configuration)
  
  

name="Normalisation: write (SPM8)"
userLevel = 1

signature = Signature(
    'parameter_file', ReadDiskItem( 'Transform Softmean to MNI', 'Matlab file' ),
#    'images_to_write', ListOf( ReadDiskItem( '4D Volume', 'Aims readable volume formats' )),
    'image_to_write', ReadDiskItem( '4D Volume', ['NIFTI-1 image', 'SPM image', 'MINC image']),
#    'normalised_images', ListOf( WriteDiskItem( '4D Volume', 'Aims readable volume formats' )),
    'normalised_image', WriteDiskItem( '4D Volume', ['NIFTI-1 image', 'SPM image', 'MINC image']),
    'preservation', Choice( ('Preserve Concentrations', """0"""), ('Preserve Amount', """1""")),
    'bounding_box', String(),
    'voxel_sizes', String(),
    'interpolation', Choice(('Nearest neighbour',"""0"""),('Trilinear',"""1"""),("""2nd Degree B-Spline""","""2"""),("""3rd Degree B-Spline""","""3"""),("""4th Degree B-Spline""","""4"""),("""5th Degree B-Spline""","""5"""),("""6th Degree B-Spline""","""6"""),("""7th Degree B-Spline""","""7""")),                
    'wrap', Choice(('No wrap', """[0 0 0]"""), ('Wrap X', """[1 0 0]"""), ('Wrap Y', """[0 1 0]"""), ('Wrap X & Y', """[1 1 0]"""), ('Wrap Z', """[0 0 1]"""), ('Wrap X & Z', """[1 0 1]"""), ('Wrap Y & Z', """[0 1 1]"""), ('Wrap X, Y, Z', """[1 1 1]""")),
    'prefix', String(),
    'batch_location', WriteDiskItem( 'Any Type', 'Matlab script' ), 
                      )

#----------------------------------------------------------------------
def initialization(self):
    # Default values from SPM8
    initializeWriteNormalisation_withSPM8DefaultValues( self ) 
    
    self.setOptional( 'batch_location' )

    self.prefix = """spm_normalised_"""  
    
    self.addLink( 'normalised_image', 'image_to_write', self.updateOutputImages )
    self.addLink( 'normalised_image', 'prefix', self.updateOutputImages )

    self.signature['bounding_box'].userLevel = 1
    self.signature['voxel_sizes'].userLevel = 1
    self.signature['interpolation'].userLevel = 1
    self.signature['wrap'].userLevel = 1
    self.signature['prefix'].userLevel = 1
    self.signature['batch_location'].userLevel = 1

#
# Update output images 
# location: same directory as images_to_write
# filename: same nom as images_to_write with prefix
#
def updateOutputImages( self, proc ):

    if self.image_to_write is None:
        return
    
    inDI = self.image_to_write   
    inFileName = inDI.fullPath()[inDI.fullPath().rindex('/') + 1:]
    inDir = inDI.fullPath()[:inDI.fullPath().rindex('/') + 1]
    return inDir + self.prefix.replace("'", "") + inFileName
          
        
#----------------------------------------------------------------------    
def execution( self, context ):
    print "\n start ", name, "\n"  
     
    if self.bounding_box.find('\n') == -1:
        context.error("Bounding box size does not match: required [2 3].") 
        return  
      
    inPath = self.parameter_file.fullPath()
    inDir = inPath[:inPath.rindex('/')]  
  
    # Use of temporary file when no batch location entered
    if self.batch_location is None:
        spmJobFile = context.temporary( 'Matlab script' ).fullPath()
    else:
        spmJobFile = self.batch_location.fullPath()
        
    
    matfilePath = writeNormalisationWriteBatch( context = context, spmJobFile=spmJobFile, 
                                                    parameter_file = self.parameter_file.fullPath(), 
                                                    images_to_write = self.image_to_write.fullPath(), 
                                                    preservation = self.preservation,
                                                    bounding_box = self.bounding_box,
                                                    voxel_sizes = self.voxel_sizes,
                                                    interpolation = self.interpolation,
                                                    wrap = self.wrap,
                                                    prefix = self.prefix )


    spm.run(context, configuration, matfilePath)    
       
    spm_image = self.image_to_write.fullPath()
    spm_image_dir = spm_image[:spm_image.rindex('/')]
    spm_image_fn = spm_image[spm_image.rindex('/') + 1:]
    
    shutil.move( spm_image_dir + "/"+ self.prefix + spm_image_fn , self.normalised_image.fullPath() )

    print "\n end ", name, "\n"
    
    
 
