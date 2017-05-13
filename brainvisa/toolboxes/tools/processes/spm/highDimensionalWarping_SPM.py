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
#
# Chap 27
#
# High-Dimensional Warping
# This toolbox is a Bayesian method for three dimensional registration of brain images [4] .
# A finite element approach is used to obtain a maximum a posteriori (MAP) estimate of the
# deformation field at every voxel of a template volume. The priors used by the MAP estimate
# penalize unlikely deformations and enforce a continuous one-to-one mapping. The deformations
# are assumed to have some form of symmetry, in that priors describing the probability distribution
# of the deformations should be identical to those for the inverses (i.e., warping brain A to brain
# B should not be different probablistically from warping B to A). A gradient descent algorithm is
# used to estimate the optimum deformations.
# Deformation fields are written with the same name as the moved image, but with ”y ” prefixed
# on to the filename. Jacobian determinant images are also written (prefixed by ”jy ”).
#------------------------------------------------------------------------------    

from __future__ import print_function
from brainvisa.processes import *
import brainvisa.tools.spm_run as spm
from brainvisa.tools.spm_registration import writeHighDimensionalWarpingMatFile, initializeHDWParameters_withSPM8DefaultValues
import shutil
from brainvisa.tools.spm_utils import moveSpmOutFiles


#------------------------------------------------------------------------------
configuration = Application().configuration
#------------------------------------------------------------------------------

def validation():
  return spm.validation(configuration)
  
name="High Dimensional Warping (using SPM8)"
userLevel = 1

signature = Signature(
    'reference', ReadDiskItem('4D Volume', ['NIFTI-1 image', 'SPM image', 'MINC image']),
    'moved_image', ReadDiskItem('4D Volume', ['NIFTI-1 image', 'SPM image', 'MINC image']),
    'bias_opts_nits', String(),
    'bias_opts_fwhm', Choice(('30mm cutoff',"""30"""),('40mm cutoff',"""40"""),('50mm cutoff',"""50"""),('60mm cutoff',"""60"""),('70mm cutoff',"""70"""),('80mm cutoff',"""80"""),('90mm cutoff',"""90"""),('100mm cutoff',"""100"""),('110mm cutoff',"""110"""),('120mm cutoff',"""120"""),('130mm cutoff',"""130"""),('140mm cutoff',"""140"""),('150mm cutoff',"""150"""),('No correction',"""Inf""")),
    'bias_opts_reg', Choice(('No regularisation',"""0"""),('Extremly light regularisation',"""1e-09"""),('Very light regularisation',"""1e-08"""),('Light regularisation',"""1e-07"""),('Medium regularisation',"""1e-06"""),('Heavy regularisation',"""1e-05"""),('Very heavy regularisation',"""0.0001"""),('Extremly heavy regularisation',"""0.001""")),
    'bias_opts_lmreg', Choice(('No regularisation',"""0"""),('Extremly light regularisation',"""1e-09"""),('Very light regularisation',"""1e-08"""),('Light regularisation',"""1e-07"""),('Medium regularisation',"""1e-06"""),('Heavy regularisation',"""1e-05"""),('Very heavy regularisation',"""0.0001"""),('Extremly heavy regularisation',"""0.001""")),
    'warp_opts_nits', String(),
    'warp_opts_reg', String(),
    'jacobian', WriteDiskItem('4D Volume', ['NIFTI-1 image', 'SPM image', 'MINC image']),
    'deformation_field', WriteDiskItem('4D Volume', ['NIFTI-1 image', 'SPM image', 'MINC image']),
    'batch_location', WriteDiskItem( 'Any Type', 'Matlab script' ),
                    
                      )

#----------------------------------------------------------------------------------------
def initialization(self):
      #Default values from SPM8
      initializeHDWParameters_withSPM8DefaultValues( self )
      
      self.setOptional( 'batch_location' )
      
      self.addLink( 'jacobian', 'moved_image', self.updateJacobianParameter )
      self.addLink( 'deformation_field', 'moved_image', self.updateDeformationFieldParameter )
      
      self.signature['bias_opts_nits'].userLevel = 1
      self.signature['bias_opts_fwhm'].userLevel = 1
      self.signature['bias_opts_reg'].userLevel = 1
      self.signature['bias_opts_lmreg'].userLevel = 1
      self.signature['warp_opts_nits'].userLevel = 1
      self.signature['warp_opts_reg'].userLevel = 1
      
    
#----------------------------------------------------------------------------------------

#
# Update Jacobian parameter value thanks to moved_image attributes
# (put jacobian of images to move in moved_images directories)
#
def updateJacobianParameter( self, proc ):
    if self.moved_image is None:
        return
    
    jacobianDiskItem = WriteDiskItem(self.signature['jacobian'].type, 'NIFTI-1 image').findValue(self.moved_image.globalAttributes())
    if jacobianDiskItem is not None:
        return jacobianDiskItem
    
    path = self.moved_image.fullPath()[:self.moved_image.fullPath().rindex('/')+1]
    filename = self.moved_image.fullPath()[self.moved_image.fullPath().rindex('/')+1:]
    return path + "jy_jacobian_" + filename
        
#----------------------------------------------------------------------------------------
#
# Update Deformation Field parameter value thanks to moved_image attributes 
# (put deformation field of images to move in moved_images directories)
#        
def updateDeformationFieldParameter( self, proc ):
    if self.moved_image is None:
        return
    
    defFieldDiskItem = WriteDiskItem(self.signature['deformation_field'].type, 'NIFTI-1 image').findValue(self.moved_image.globalAttributes())
    if defFieldDiskItem is not None:
        return defFieldDiskItem
    
    path = self.moved_image.fullPath()[:self.moved_image.fullPath().rindex('/')+1]
    filename = self.moved_image.fullPath()[self.moved_image.fullPath().rindex('/')+1:]
    return path + "y_deformation_field_" + filename

#----------------------------------------------------------------------------------------
def execution( self, context ):
    print("\n start ", name, "\n")
      
    moved_imagePath = self.moved_image.fullPath()
    inDir = moved_imagePath[:moved_imagePath.rindex('/')+1]  
  
    # Use of temporary file when no batch location entered
    if self.batch_location is None:
        spmJobFile = context.temporary( 'Matlab script' ).fullPath()
    else:
        spmJobFile = self.batch_location.fullPath()
   
    matfilePath = writeHighDimensionalWarpingMatFile(spmJobFile, self.reference.fullPath(), mov=self.moved_image.fullPath(),
                                    bias_opts_nits=self.bias_opts_nits, bias_opts_fwhm=self.bias_opts_fwhm, bias_opts_reg=self.bias_opts_reg, bias_opts_lmreg=self.bias_opts_lmreg, warp_opts_nits=self.warp_opts_nits, warp_opts_reg=self.warp_opts_reg) 
      
    spm.run(context, configuration, matfilePath, isMatlabMandatory=True)    
    
    # Move and rename jacobian and Deformation field images (by default, SPM creates Jacobian and Deformation field
    # in the images to move directory)
    moved_image_filename = moved_imagePath[moved_imagePath.rindex('/')+1:]  
    
    shutil.move( inDir + 'y_' + moved_image_filename, self.deformation_field.fullPath() )
    
    shutil.move( inDir + 'jy_' + moved_image_filename, self.jacobian.fullPath() )
    
    print("\n end ", name, "\n")
    
    
