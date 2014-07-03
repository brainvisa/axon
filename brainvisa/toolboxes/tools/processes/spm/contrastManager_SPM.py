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
# Process allowing to create T contrasts for SPM8 from SPM.mat.
#------------------------------------------------------------------------------

from neuroProcesses import *
import brainvisa.tools.spm_run as spm
from  brainvisa.tools.spm_basic_models import initialize_SPM8_default_contrastParameters, write_contrast_MatFile


#------------------------------------------------------------------------------
configuration = Application().configuration
#------------------------------------------------------------------------------

def validation():
  return spm.validation(configuration)

#------------------------------------------------------------------------------

userLevel = 1
name = 'T-Contrast Manager (using SPM8)'


signature = Signature(
  'basicModelMatFile', ReadDiskItem('Matlab SPM file', 'Matlab file'),
  'contrast_name', String(),
  'contrast_vector', String(),
  'session_replication', Choice( ('Dont replicate', """'none'"""), ('Replicate', """'repl'"""), ('Replicate&Scale', """'replsc'"""), ('Create per session', """'sess'"""), ('Both: Replicate + Create per session', """'both'"""), ('Both: Replicate&Scale + Create per session', """'bothsc'"""), ),
  'delete', Choice( ('No', '0'), ('Yes', '1') ),
  'batch_location', String(),
                      )


#------------------------------------------------------------------------------

def initialization(self):
  initialize_SPM8_default_contrastParameters( self )
  
  self.addLink( 'batch_location', 'basicModelMatFile', self.update_batch_location )
  
  
  
#------------------------------------------------------------------------------
#
# Write the batch of Contrasts manager in the same directory as SPM.mat
# Default file namem: batch_contrast_manager.m
#
def update_batch_location( self, proc ):
    if self.basicModelMatFile is not None:
        modelPath = str( self.basicModelMatFile )
        modelDir = modelPath[:modelPath.rindex('/') + 1]
        return modelDir + 'batch_contrast_manager.m'
        

def execution(self, context):  
  print "\n start ", name, "\n"
      
  spmJobFile = self.batch_location
    
  matfilePath = write_contrast_MatFile(context, self.basicModelMatFile.fullPath(), spmJobFile, self.contrast_name, self.contrast_vector, self.session_replication, self.delete)
  
  spm.run(context, configuration, matfilePath)#, isMatlabMandatory=True) 
  
  print "\n stop ", name, "\n"

#------------------------------------------------------------------------------
