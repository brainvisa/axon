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
import nuclearImaging.SPM as spm

#------------------------------------------------------------------------------
configuration = Application().configuration
spm8Path = spm.getSpm8Path(configuration)
#------------------------------------------------------------------------------

def validation():
  return spm.validation(configuration)

#------------------------------------------------------------------------------

userLevel = 0
name = 'Normalize to MNI space (using SPM)'

#------------------------------------------------------------------------------

signature = Signature(
    'source', ReadDiskItem('4D Volume', 'Aims readable volume formats'),
    'imageToWrite', ReadDiskItem('4D Volume', 'Aims readable volume formats'),
    'warpedInMni', WriteDiskItem('4D Volume', 'Aims readable volume formats'),
    'template', ReadDiskItem('4D Volume', 'Aims readable volume formats'),
    'checkReg', WriteDiskItem('Postscript file', 'PS file'),
    'wtsrc', String(),
    'weight', String(),
    'smosrc', String(),
    'smoref', String(),
    'regtype', String(),
    'cutoff', String(),
    'nits', String(),
    'reg', String(),
    'preserve', String(),
    'bb', String(),
    'vox', String(),
    'interp', String(),
    'wrap', String(),
    'prefix', String(),
     )
#------------------------------------------------------------------------------

def initialization(self):
 
  self.template = str(spm8Path) + """/templates/T1.nii""" # could be also : PET or SPECT etc...
  spm.initializeNormalizeParameters_usingSPM8DefaultValuesForPET(self)
  self.prefix = """'spmNormalized_'""" 

#------------------------------------------------------------------------------

def execution(self, context):            
  inDir = self.imageToWrite.fullPath()
  inDir = inDir[:inDir.rindex('/')]  
  spmJobFile = inDir + '/' + 'normalize_job.m'
      
  matfilePath = spm.writeNormalizeMatFile(context, configuration, self.source.fullPath(), self.imageToWrite.fullPath(), spmJobFile
                                          , self.template.fullPath(), self.wtsrc, self.weight, self.smosrc, self.smoref, self.regtype, self.cutoff, self.nits, self.reg
                                          , self.preserve, self.bb, self.vox, self.interp, self.wrap, self.prefix 
                                          )  
      
  spm.run(context, configuration, matfilePath)    
    
  warpedPath = self.warpedInMni.fullPath()
  spm.moveSpmOutFiles(inDir, warpedPath, [self.prefix])

  psFileName = 'spm_' + spm.spm_today()
  spm.moveSpmOutFiles(inDir, self.checkReg.fullPath(), [psFileName], ext='.ps')
  
  os.system('AimsRemoveNaN' + ' -i ' + str(warpedPath) + ' -o ' + str(warpedPath) + '.noNan.nii')
  os.remove(warpedPath)
  os.rename(warpedPath + '.noNan.nii', warpedPath)
  os.remove(warpedPath + '.noNan.nii.minf')    

  #sdb.insertDiskItemInDataBase(self.warpedInMni) # insert DI in DB so the minf will be created ( essential to write roi mean )


#------------------------------------------------------------------------------
# spm documentation : 

#Normalise: Estimate & Write
#Computes  the warp that best registers a source image (or series of source images) to match a template, saving it to the file imagename'_sn.mat'. 
#This option also allows the contents of the imagename'_sn.mat' files to be applied to a series of images.
#------------------------------------------------------------------------------



