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
from brainvisa.tools.spm_registration import \
  ititializeCoregisterParameters_withSPM8DefaultValuesforPET, \
  writeCoregisteredMatFile
import brainvisa.tools.spm_run as spm
from brainvisa.tools.spm_utils import moveSpmOutFiles

#------------------------------------------------------------------------------
configuration = Application().configuration
#------------------------------------------------------------------------------

def validation():
  return spm.validation(configuration)

#------------------------------------------------------------------------------

userLevel = 0
name = 'Coregister (using SPM8)'

#------------------------------------------------------------------------------

signature = Signature(
    'source', ReadDiskItem('4D Volume', 'Aims readable volume formats'),
    'other', ReadDiskItem('4D Volume', 'Aims readable volume formats'),
    'reference', ReadDiskItem('4D Volume', 'Aims readable volume formats'),
    'prefix', String(),
    'spmSourceWarped', WriteDiskItem('4D Volume', 'Aims readable volume formats'),
    'spmOtherWarped', WriteDiskItem('4D Volume', 'Aims readable volume formats'),
    'sourceWarped', WriteDiskItem('4D Volume', 'Aims readable volume formats'),
    'otherWarped', WriteDiskItem('4D Volume', 'Aims readable volume formats'),
        
    'cost_fun', Choice(('Mutual Information', """'mi'"""), ('Normalized Mutual Information', """'nmi'"""), ('Entropy Correlation Coefficient', """'ecc'"""), ('Normalised Cross Correlation', """'ncc'""")),
    'sep', String(),
    'tol', String(),
    'fwhm', String(),
    'interp', Choice(('Nearest neighbour', """0"""), ('Trilinear', """1"""), ('2nd Degree B-spline', """2"""), ('3rd Degree B-spline', """3"""), ('4th Degree B-spline', """4"""), ('5th Degree B-spline', """5"""), ('6thd Degree B-spline', """6"""), ('7th Degree B-spline', """7""")),
    'wrap', Choice(('No wrap', """[0 0 0]"""), ('Wrap X', """[1 0 0]"""), ('Wrap Y', """[0 1 0]"""), ('Wrap X & Y', """[1 1 0]"""), ('Wrap Z', """[0 0 1]"""), ('Wrap X & Z', """[1 0 1]"""), ('Wrap Y & Z', """[0 1 1]"""), ('Wrap X, Y, Z', """[1 1 1]""")),
    'mask', Choice(('Mask images', """1"""), ('Dont maks images', """0""")),
  )

#------------------------------------------------------------------------------

def initialization(self):
  self.setOptional('other', 'spmSourceWarped', 'spmOtherWarped', 'sourceWarped', 'otherWarped')
  ititializeCoregisterParameters_withSPM8DefaultValuesforPET(self) 
  self.prefix = """'spmCoregister_'"""
  
  self.addLink('spmSourceWarped', 'source', self.update_spmSourceWarped)
  self.addLink('spmOtherWarped', 'other', self.update_spmOtherWarped)
  
  self.signature['other'].userLevel = 1
  self.signature['cost_fun'].userLevel = 1
  self.signature['sep'].userLevel = 1
  self.signature['tol'].userLevel = 1
  self.signature['fwhm'].userLevel = 1
  self.signature['interp'].userLevel = 1
  self.signature['wrap'].userLevel = 1
  self.signature['mask'].userLevel = 1
  self.signature['prefix'].userLevel = 1
  
#------------------------------------------------------------------------------
def update_spmSourceWarped(self, proc):
  if(self.source is not None):
    return self.update_spmWarped(self.source.fullPath())

def update_spmOtherWarped(self, proc):
  if(self.other is not None):
    return self.update_spmWarped(self.other.fullPath())
    
def update_spmWarped(self, inPath):
  inFileName = inPath[inPath.rindex('/') + 1:]
  inDir = inPath[:inPath.rindex('/') + 1]
  outPath = inDir + self.prefix.replace("'", "") + inFileName
  return outPath


#------------------------------------------------------------------------------
def execution(self, context):  
  print "\n start ", name, "\n"  
      
  sourcePath = self.source.fullPath()
  sourceWarpedPath = self.sourceWarped.fullPath()
  inDir = sourcePath[:sourcePath.rindex('/')]  
  
  spmJobFile = inDir + '/coregister_job.m'
  
  othersPath = None
  if(self.other is not None):
    othersPath = [self.other.fullPath()]
      
  matfilePath = writeCoregisteredMatFile(context, sourcePath, self.reference.fullPath(), spmJobFile
                                             , othersPath=othersPath, cost_fun=self.cost_fun, sep=self.sep, tol=self.tol, fwhm=self.fwhm
                                             , interp=self.interp, wrap=self.wrap, mask=self.mask, prefix=self.prefix)
    
  spm.run(context, configuration, matfilePath)    
  
  if(self.other is not None and self.otherWarped is not None):
    otherFileName = self.other.fullPath()[self.other.fullPath().rindex('/') + 1:]
    moveSpmOutFiles(inDir, self.otherWarped.fullPath(), spmPrefixes=[self.prefix[:-1] + otherFileName])

  if(self.source is not None and self.sourceWarped is not None):
    sourceFileName = sourcePath[sourcePath.rindex('/') + 1:]
    moveSpmOutFiles(inDir, sourceWarpedPath, spmPrefixes=[self.prefix[:-1] + sourceFileName])
    
  removeNan(sourceWarpedPath) 
  if(self.other is not None):
    removeNan(self.otherWarped.fullPath())    
    
  print "\n stop ", name, "\n"
  
#------------------------------------------------------------------------------        

def removeNan(filePath):
  os.system('AimsRemoveNaN' + ' -i ' + str(filePath) + ' -o ' + str(filePath) + '.noNan.nii')
  os.remove(filePath)
  os.rename(filePath + '.noNan.nii', filePath)
  os.rename(filePath + '.noNan.nii.minf', filePath + '.minf')
  
#------------------------------------------------------------------------------
# spm documentation : 

#Coregister: Estimate & Reslice
#The  registration  method  used  here  is  based  on  work  by  Collignon et al. 
#The original interpolation method described in this paper has been changed in order to give a smoother  cost  function.    
#The  images  are  also  smoothed  slightly,  as is the histogram.  
#This is all in order to make the cost function as smooth as possible, to give fasterconvergence and less chance of local minima.
#
#At  the  end  of  coregistration,  the  voxel-to-voxel  affine transformation matrix is displayed, along with the histograms for the images in the original orientations, and the final orientations.  
#The registered images are displayed at the bottom.
#
#Registration  parameters  are  stored  in  the headers of the "source" and the "other" images. 
#These images are also resliced to match the source image voxel-for-voxel. 
#The resliced images are named the same as the originals except that they are prefixed by 'r'.
#
#------------------------------------------------------------------------------
