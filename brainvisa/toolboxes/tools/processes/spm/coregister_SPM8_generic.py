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

from __future__ import print_function
from brainvisa.processes import *
from brainvisa.tools.spm_registration import \
  ititializeCoregisterParameters_withSPM8DefaultValues, \
  writeCoregisteredMatFile
import brainvisa.tools.spm_run as spm
from brainvisa.tools.spm_utils import moveSpmOutFiles, removeNan
import shutil

#------------------------------------------------------------------------------
configuration = Application().configuration
#------------------------------------------------------------------------------

def validation():
  return spm.validation(configuration)

#------------------------------------------------------------------------------

userLevel = 0
name = 'Coregister estimate & reslice (SPM8)'

#------------------------------------------------------------------------------

signature = Signature(
    'source', ReadDiskItem('4D Volume', ['NIFTI-1 image', 'SPM image', 'MINC image']),
    'others', ListOf(ReadDiskItem('4D Volume', ['NIFTI-1 image', 'SPM image', 'MINC image'])),
    'reference', ReadDiskItem('4D Volume', ['NIFTI-1 image', 'SPM image', 'MINC image']),
    'prefix', String(),
    'sourceWarped', WriteDiskItem('4D Volume', ['NIFTI-1 image', 'SPM image', 'MINC image']),
    'othersWarped', ListOf(WriteDiskItem('4D Volume', ['NIFTI-1 image', 'SPM image', 'MINC image'])),
        
    'cost_fun', Choice(('Mutual Information', """'mi'"""), ('Normalized Mutual Information', """'nmi'"""), ('Entropy Correlation Coefficient', """'ecc'"""), ('Normalised Cross Correlation', """'ncc'""")),
    'sep', String(),
    'tol', String(),
    'fwhm', String(),
    'interp', Choice(('Nearest neighbour', """0"""), ('Trilinear', """1"""), ('2nd Degree B-spline', """2"""), ('3rd Degree B-spline', """3"""), ('4th Degree B-spline', """4"""), ('5th Degree B-spline', """5"""), ('6thd Degree B-spline', """6"""), ('7th Degree B-spline', """7""")),
    'wrap', Choice(('No wrap', """[0 0 0]"""), ('Wrap X', """[1 0 0]"""), ('Wrap Y', """[0 1 0]"""), ('Wrap X & Y', """[1 1 0]"""), ('Wrap Z', """[0 0 1]"""), ('Wrap X & Z', """[1 0 1]"""), ('Wrap Y & Z', """[0 1 1]"""), ('Wrap X, Y, Z', """[1 1 1]""")),
    'mask', Choice(('Mask images', """1"""), ('Dont maks images', """0""")),
    'batch_location', WriteDiskItem( 'Any Type', 'Matlab script' ),
  )

#------------------------------------------------------------------------------

def initialization(self):
  self.setOptional('others', 'sourceWarped', 'othersWarped', 'batch_location')
  ititializeCoregisterParameters_withSPM8DefaultValues(self) 
  self.prefix = """spmCoregister_"""
  
  self.addLink('sourceWarped', 'source', self.update_spmSourceWarped)
  self.addLink('othersWarped', 'others', self.update_spmOthersWarped)
  
  self.signature['others'].userLevel = 1
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

def update_spmOthersWarped(self, proc):
  if(self.others is not None):
    outPaths=[]
    for inDI in self.others:
      outPath=self.update_spmWarped( inDI.fullPath())
      outPaths.append(outPath)
    return outPaths    
  
def update_spmWarped(self, inPath):
  inFileName = inPath[inPath.rindex('/') + 1:]
  inDir = inPath[:inPath.rindex('/') + 1]
  outPath = inDir + self.prefix.replace("'", "") + inFileName
  return outPath

#------------------------------------------------------------------------------
def execution(self, context):  
    print("\n start ", name, "\n")
    
    sourcePath = self.source.fullPath()
    inDir = sourcePath[:sourcePath.rindex('/')]  
  
    # Use of temporary file when no batch location entered
    if self.batch_location is None:
        spmJobFile = context.temporary( 'Matlab script' ).fullPath()
    else:
        spmJobFile = self.batch_location.fullPath()
      
    othersPath = None
    if(self.others is not None):
      othersPath = [other.fullPath() for other in self.others]
        
    matfilePath = writeCoregisteredMatFile(context, sourcePath, self.reference.fullPath(), spmJobFile
                                               , othersPath=othersPath, cost_fun=self.cost_fun, sep=self.sep, tol=self.tol, fwhm=self.fwhm
                                               , interp=self.interp, wrap=self.wrap, mask=self.mask, prefix="'"+self.prefix+"'")
      
    spm.run(context, configuration, matfilePath)    
    
    for other, otherWarped in zip( self.others, self.othersWarped):
      otherPathName = other.fullPath()
      otherDir = otherPathName[:otherPathName.rindex('/') + 1]  
      otherFileName = otherPathName[otherPathName.rindex('/') + 1:]
      spmOtherWarpedFileName = self.prefix + otherFileName
      
      shutil.move( otherDir  + spmOtherWarpedFileName , otherWarped.fullPath() )
    
    sourcePathName = self.source.name
    sourceFileName = sourcePathName[sourcePathName.rindex('/') + 1:]
    spmSourceWarpedFileName = self.prefix[:-1] + sourceFileName
    if(self.sourceWarped is not None):
      sourceWarpedPath = self.sourceWarped.fullPath()
      self.source.fullPath
      sourceFilename = sourcePath[sourcePath.rindex('/')+1:]  
      
      shutil.move( inDir + "/" + self.prefix + sourceFilename , sourceWarpedPath )
   
    print("\n stop ", name, "\n")
  
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
