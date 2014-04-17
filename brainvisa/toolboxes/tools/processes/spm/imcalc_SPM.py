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
# Create and launch SPM Image Calculator batch
# (See below for SPM8 documentation)
#

#
#------------------------------------------------------------------------------        
# FROM spm documentation (SPM8 manual: www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf‎): 
# Chap 19 : Image Calculator
# The image calculator is for performing user-specified algebraic manipulations on a set of
# images, with the result being written out as an image. The user is prompted to supply images to
# work on, a filename for the output image, and the expression to evaluate. The expression should
# be a standard MATLAB expression, within which the images should be referred to as i1, i2, i3,...
# etc.
#------------------------------------------------------------------------------

from neuroProcesses import *
import brainvisa.tools.spm_run as spm

# As this process depends on nuclear imaging toolbox
# it is necessary to test if this is available in the 
# current context
try :
  from nuclearImaging.SPM import writeImgCalcMatFile
except :
  pass

#------------------------------------------------------------------------------
configuration = Application().configuration
#------------------------------------------------------------------------------

def validation():
  from nuclearImaging.SPM import writeImgCalcMatFile
  
  return spm.validation(configuration)
  
name="Image Calculator (imcalc - SPM8)"
userLevel = 1

signature = Signature(
    'input_images', ListOf(ReadDiskItem('4D Volume', 'Aims readable volume formats')),
    # In SPM, 2 options for the filename of the output and his location. Here they are gathered  in the output_filename variable.
    'output_filename', WriteDiskItem('4D Volume', 'Aims readable volume formats'),
    #'output_directory' , WriteDiskItem('Directory', 'Directory'),  
    'expression', String(),     
    'data_matrix', Choice(('No',"""0"""),('Yes', """1""")),
    'masking', Choice(('No implicit zero mask',"""0"""),('Implicit zero mask', """1"""), ('NaNs should be zeroed',"""-1""")),
    'interpolation', Choice(('Nearest neighbour', """0"""), ('Trilinear', """1"""), ('2nd Degree sync', """-2"""), ('3rd Degree sync', """-3"""), ('4th Degree sync', """-4"""), ('5th Degree sync', """-5"""), ('6thd Degree sync', """-6"""), ('7th Degree sync', """-7""")),                  
    'data_type', Choice(('UINT8', """2"""), ('INT16', """4"""), ('INT32', """8"""), ('FLOAT 32', """16"""), ('FLOAT 64', """64""")),                  
    )


def initialization(self):
   # SPM default values
    self.data_matrix = 'No'
    self.masking = 'No implicit zero mask'
    self.interpolation = 'Trilinear'
    self.data_type = 'INT16'
 


def execution( self, context ):
    print "\n start ", name, "\n"  
    
    output_filename = "'" + str(self.output_filename.fullPath()) + "'"
        
    spmJobFile = self.output_filename.fullPath()[:self.output_filename.fullPath().rindex('/')] + '/' + 'batch_imcalc_SPM.m'
    
    expr = "'" + str(self.expression) + "'"
    
    mat_file = open(spmJobFile, 'w')
    matfileDI = None
      
    subjectsPathList = [image.fullPath() for image in self.input_images]
      
    matfilePath = writeImgCalcMatFile(context, subjectsPathList=subjectsPathList, matfileDI=matfileDI, mat_file=mat_file                                            
                                      , output=output_filename, expression=expr
                                      , dmtx=self.data_matrix, mask=self.masking, interp=self.interpolation, dtype=self.data_type
                                      )
    
    spm.run(context, configuration, matfilePath)    
  
    print "\n end ", name, "\n"
    

