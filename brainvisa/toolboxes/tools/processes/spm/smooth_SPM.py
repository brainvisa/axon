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
import brainvisa.tools.spm_run as spm
import brainvisa.tools.spm_utils as spmUtils

#------------------------------------------------------------------------------
configuration = Application().configuration
#------------------------------------------------------------------------------

def validation():
  return spm.validation(configuration)

#------------------------------------------------------------------------------

userLevel = 2
name = 'smooth one image (using SPM8)'

#------------------------------------------------------------------------------

signature = Signature(
    'img', ReadDiskItem('4D Volume', ['NIFTI-1 image', 'SPM image', 'MINC image']),
    'img_smoothed', WriteDiskItem('4D Volume', ['NIFTI-1 image', 'SPM image', 'MINC image']),
    'fwhm', ListOf(Integer()),
    'data_type', Choice(("SAME", """0"""), ("UINT8", """0"""), ("INT16", """0"""), 
                        ("INT32", """0"""), ("FLOAT32", """0"""), ("FLOAT64", """0""")),
    'implicit_masking', Boolean(),
    'prefix', String(),
    'batch_location', WriteDiskItem( 'Any Type', 'Matlab script' )
)

#------------------------------------------------------------------------------

def initialization(self):
    self.setOptional('batch_location')  

    self.signature['fwhm'].userLevel = 1
    self.signature['data_type'].userLevel = 1
    self.signature['prefix'].userLevel = 1
    self.signature['implicit_masking'].userLevel = 1
    
    self.addLink( 'img_smoothed', 'img', self.update_img_smoothed )
    self.addLink( 'img_smoothed', 'prefix', self.update_img_smoothed )
    self.linkParameters( 'batch_location', ('img', 'img_smoothed'), self.update_batch_location )
    
    self.fwhm = [8, 8, 8]
    self.data_type = """0"""
    self.implicit_masking = False
    self.prefix = 's'
    
#
# Update output image when the input and a prefix are defined
#    
def update_img_smoothed( self, proc ):
    if self.img is None or self.prefix is None:
        return
    
    img_in_path = str(self.img)
    img_in_dir = img_in_path[:img_in_path.rindex('/')]
    img_in_fn = img_in_path[img_in_path.rindex('/') + 1:]
    
    return img_in_dir + "/" + self.prefix + "_" + img_in_fn 
    
    
#
# Update batch location in the same directory as 
# the image to smooth
#
def update_batch_location( self, proc, dummy ):
    
    if not None in [self.img_smoothed, self.img ]:
        img_out_path = str( self.img_smoothed )
        img_out_dir = img_out_path[:img_out_path.rindex('/')+1]
        img_in_path = str( self.img ) 
        img_in_fn = img_in_path[img_in_path.rindex('/')+1:]
        img_in_ext = img_in_fn[img_in_fn.index('.'):]
        return img_out_dir + 'batch_smooth_' + img_in_path[img_in_path.rindex('/')+1:img_in_path.rindex('/')+1+len(img_in_fn)-len(img_in_ext)] + '.m'
    
    return ''
    

#------------------------------------------------------------------------------

def execution(self, context):  
    print "\n start ", name, "\n"
    
    # Use of temporary file when no batch location entered
    if self.batch_location is None:
        spmJobFile = context.temporary( 'Matlab script' ).fullPath()
    else:
        spmJobFile = self.batch_location.fullPath()
    
    inDir = self.img.fullPath()[:self.img.fullPath().rindex('/')]  
    
    mat_file = open(spmJobFile, 'w')
    matfileDI = None
        
    matfilePath = spmUtils.writeSmoothMatFile(context, self.img.fullPath()
                                              , matfileDI, mat_file
                                              , str(self.fwhm), self.data_type, str(self.implicit_masking), self.prefix)
     
    spm.run(context, configuration, matfilePath)    
    
    spmUtils.moveSpmOutFiles(inDir, self.img_smoothed.fullPath(), spmPrefixes=[ self.prefix.replace("""'""", '') + os.path.basename(self.img.fullPath()) ])
    
    print "\n stop ", name, "\n"

#------------------------------------------------------------------------------
