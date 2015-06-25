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

from brainvisa.processes import *
from brainvisa.tools.spm_registration import writeNormalizeEstimationMatFile, \
  initializeNormalizeEstimateParameters_usingSPM8DefaultValues
from brainvisa.tools.spm_utils import spm_today
import brainvisa.tools.spm_run as spm
#from brainvisa.tools.spm_utils import moveSpmOutFiles, removeNan
from shutil import rmtree, move
import os


#------------------------------------------------------------------------------
configuration = Application().configuration
spm8Path = spm.getSpm8Path(configuration)
#------------------------------------------------------------------------------

def validation():
  return spm.validation(configuration)

#------------------------------------------------------------------------------

userLevel = 0
name = 'Normalize (estimate) (using SPM8)'

#------------------------------------------------------------------------------

signature = Signature(
    'source', ReadDiskItem('4D Volume', ['NIFTI-1 image', 'SPM image', 'MINC image']),
    'source_weighting', ReadDiskItem( '4D Volume', ['NIFTI-1 image', 'SPM image', 'MINC image']),
    'template', ReadDiskItem('4D Volume', ['NIFTI-1 image', 'SPM image', 'MINC image']),
    'template_weighting', ReadDiskItem( '4D Volume', ['NIFTI-1 image', 'SPM image', 'MINC image']),
    'source_image_smoothing', String(),
    'template_image_smoothing', String(),
    'affine_regularisation', Choice( ('ICBM space template','mni'), ('Average sized template','subj'), ('No regularisation','none') ), 
    'nonlinear_frequency_cutoff', String(),
    'nonlinear_iterations', String(),
    'nonlinear_regularisation', String(),
    'deformation_field', WriteDiskItem( 'Matlab SPM file', 'Matlab file' ),
    'results_resume', WriteDiskItem( 'Any Type', 'PS file' ),
    'batch_location', WriteDiskItem( 'Any Type', 'Matlab script' ),
    
     )
#------------------------------------------------------------------------------

def initialization(self):
    initializeNormalizeEstimateParameters_usingSPM8DefaultValues(self)
    self.setOptional( 'source_weighting', 'template_weighting', 'batch_location', 'results_resume' )
 
    signature['template_weighting'].userLevel = 3
    signature['source_image_smoothing'].userLevel = 3
    signature['template_image_smoothing'].userLevel = 3
    signature['affine_regularisation'].userLevel = 3
    signature['nonlinear_frequency_cutoff'].userLevel = 3
    signature['nonlinear_iterations'].userLevel = 3
    signature['nonlinear_regularisation'].userLevel = 3

#------------------------------------------------------------------------------

def execution(self, context):            
    inDir = self.source.fullPath()[:self.source.fullPath().rindex('/')]  
    inFilename = self.source.fullPath()[self.source.fullPath().rindex('/')+1:]
    inFilename = inFilename[:inFilename.rindex('.')]
    
    # Use of temporary file when no batch location entered
    if self.batch_location is None:
        spmJobFile = context.temporary( 'Matlab script' ).fullPath()
    else:
        spmJobFile = self.batch_location.fullPath()
        
    if self.source_weighting is not None:
        source_weighting_path = self.source_weighting.fullPath()
    else:
        source_weighting_path = ''

    if self.template_weighting is not None:
        template_weighting_path = self.template_weighting.fullPath()
    else:
        template_weighting_path = ''

    matfilePath = writeNormalizeEstimationMatFile( spmJobFile, 
                                        self.source, 
                                        self.template,
                                        source_weighting_path, 
                                        template_weighting_path,
                                        self.source_image_smoothing,
                                        self.template_image_smoothing,
                                        self.affine_regularisation,
                                        self.nonlinear_frequency_cutoff,
                                        self.nonlinear_iterations,
                                        self.nonlinear_regularisation,
                                            )  
    
    spm.run(context, configuration, matfilePath)#, useMatlabFirst=True)# matlab version is the version to generate .ps file to check the registration  
    
    # Remove or move ps file generated by SPM Normalize process 
    dirResults = spmJobFile[:spmJobFile.rindex('/')]
    psFile = dirResults + '/spm_' + spm_today() + '.ps'
    if self.results_resume is not None:
        move( psFile, self.results_resume.fullPath() )
    else:
        # When using SPM standalone, no ps file is created
        if os.path.exists( psFile ):
            os.remove( psFile )
    
    # Move deformation field
    move( inDir + '/' + inFilename + '_sn.mat', self.deformation_field.fullPath() )
       
#------------------------------------------------------------------------------
# spm documentation : 

#Normalise: Estimate & Write
#Computes  the warp that best registers a source image (or series of source images) to match a template, saving it to the file imagename'_sn.mat'. 
#This option also allows the contents of the imagename'_sn.mat' files to be applied to a series of images.
#------------------------------------------------------------------------------
    


