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
# FROM spm documentation (SPM8 manual: www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf‎): 
# Chap 23
# Deformation
# This is a utility for working with deformation fields. They can be loaded, inverted, combined
# etc, and the results either saved to disk, or applied to some image
# 
# Deformations can be thought of as vector fields. These can be represented by three-volume
# images.
#------------------------------------------------------------------------------        

from neuroProcesses import *
import brainvisa.tools.spm_run as spm
from brainvisa.tools.spm_registration import writeDeformationWithField, initializeDeformationWithField_withSPM8DefaultValues
from brainvisa.tools.spm_utils import moveSpmOutFiles, movePath

#------------------------------------------------------------------------------
configuration = Application().configuration
#------------------------------------------------------------------------------

def validation():
  return spm.validation(configuration)
  
  

name="Deformation using Deformation Field (SPM8)"
userLevel = 1

signature = Signature(
    'deformation_field', ReadDiskItem('4D Volume', 'Aims readable volume formats'),
    'save_as', String(),
    'images_to_deform', ListOf(ReadDiskItem('4D Volume', 'Aims readable volume formats')),
    'interpolation', Choice(('Nearest neighbour',"""0"""),('Trilinear',"""1"""),("""2nd Degree B-Spline""","""2"""),("""3rd Degree B-Spline""","""3"""),("""4th Degree B-Spline""","""4"""),("""5th Degree B-Spline""","""5"""),("""6th Degree B-Spline""","""6"""),("""7th Degree B-Spline""","""7""")),                
    'prefix', String(),
    'output_destination', ListOf(WriteDiskItem( '4D Volume', 'Aims readable volume formats' )),
    'batch_location', String(),
                      )

#----------------------------------------------------------------------
def initialization(self):
    # Default values from SPM8
    initializeDeformationWithField_withSPM8DefaultValues( self ) 
    
    self.setOptional( 'batch_location' )
    
    # BrainVISA prefix
    self.prefix = """spmDeformed_"""  
    
    self.addLink( 'output_destination', 'images_to_deform', self.updateOutputDestination )
    self.addLink( 'output_destination', 'prefix', self.updateOutputDestination )
    self.addLink( 'batch_location', 'output_destination', self.updateBatchLocation )
    
    self.signature['interpolation'].userLevel = 1
    self.signature['prefix'].userLevel = 1
    self.signature['save_as'].userLevel = 1

#
# Update batch location
# Write the batch in the same directory as the first image of the output_destination
# with the name 'batch_deform_using_deformation_field.m'
#
def updateBatchLocation( self, proc ):
    if len(self.output_destination):
        if self.output_destination[0] is not None:
            imgPath = str( self.output_destination[0] )
            imgDir = imgPath[:imgPath.rindex('/') + 1]
            return imgDir + 'batch_deform_using_deformation_field.m'

#
# update output_destination field
#
def updateOutputDestination( self, proc ):
    if self.images_to_deform is None:
        return
    
    images_to_deform_warped = []
    for img in self.images_to_deform:
         imgFileName = img.fullPath()[img.fullPath().rindex('/') + 1:]
         imgDir = img.fullPath()[:img.fullPath().rindex('/') + 1]
         images_to_deform_warped.append( imgDir + self.prefix + imgFileName )
    return images_to_deform_warped
            
        
#----------------------------------------------------------------------    
def execution( self, context ):
    print "\n start ", name, "\n"  
      
    dfPath = self.deformation_field.fullPath()
    inDir = dfPath[:dfPath.rindex('/')]  
  
    itdPath = [images_to_deform.fullPath() for images_to_deform in self.images_to_deform]
  
    spmJobFile = inDir + '/deformation_with_field_SPM_job.m'
    
    matfilePath = writeDeformationWithField( spmJobFile, dfPath, imagesToDeformPath=itdPath, save_as=self.save_as, output_dir=inDir, interpolation=self.interpolation ) 
       
    spm.run(context, configuration, matfilePath)    
    
    # Move warped files from source directory (spm default location) to the location of the process (output_destination)
    for in_img, dest in zip(itdPath, self.output_destination):
        in_img_path = in_img[:in_img.rindex('/')+1]
        in_img_filename = in_img[in_img.rindex('/')+1:]
          
        orig = inDir + '/w' + in_img_filename
        
        shutil.move( orig, dest.fullPath()  )
        
    shutil.move( spmJobFile, self.batch_location )
   
    print "\n end ", name, "\n"
    
    
 