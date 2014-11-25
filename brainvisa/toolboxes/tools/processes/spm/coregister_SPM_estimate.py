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
# Create and launch SPM8 Coregister (estimate only)
# (See below for SPM8 documentation)
#

#------------------------------------------------------------------------------        
# FROM spm documentation (SPM8 manual: www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf‎):
# Chap 4.1
# Coregister: Estimate
# The registration method used here is based on work by Collignon et al [19]. The original interpo-
# lation method described in this paper has been changed in order to give a smoother cost function.
# The images are also smoothed slightly, as is the histogram. This is all in order to make the cost
# function as smooth as possible, to give faster convergence and less chance of local minima.
# At the end of coregistration, the voxel-to-voxel affine transformation matrix is displayed, along
# with the histograms for the images in the original orientations, and the final orientations. The
# registered images are displayed at the bottom.
# Registration parameters are stored in the headers of the ”source” and the ”other” images.
#------------------------------------------------------------------------------


from brainvisa.processes import *
from brainvisa.tools.spm_registration import initializeCoregisterEstimateParameters_withSPM8DefaultValues,\
 writeCoregisteredEstimateMatFile
import brainvisa.tools.spm_run as spm
from brainvisa.tools.spm_utils import movePathToDiskItem
import shutil
import random

#------------------------------------------------------------------------------
configuration = Application().configuration
#------------------------------------------------------------------------------

def validation():
  return spm.validation(configuration)

#------------------------------------------------------------------------------

userLevel = 1
name = 'Coregister estimate only (using SPM8)'

#------------------------------------------------------------------------------

signature = Signature(
    'reference', ReadDiskItem('4D Volume',
                              ['NIFTI-1 image', 'SPM image', 'MINC image']),
    'source', ReadDiskItem('4D Volume',
                           ['NIFTI-1 image', 'SPM image', 'MINC image']),
    'others', ListOf(ReadDiskItem('4D Volume',
        ['NIFTI-1 image', 'SPM image', 'MINC image'])),
    'cost_fun', Choice(('Mutual Information', """'mi'"""), ('Normalized Mutual Information', """'nmi'"""), ('Entropy Correlation Coefficient', """'ecc'"""), ('Normalised Cross Correlation', """'ncc'""")),
    'sep', String(),
    'tol', String(),
    'fwhm', String(),
    'prefix', String(),
    'source_coreg_only', WriteDiskItem('4D Volume',
        ['NIFTI-1 image', 'SPM image', 'MINC image']),
    'others_coreg_only', ListOf( WriteDiskItem('4D Volume',
        ['NIFTI-1 image', 'SPM image', 'MINC image']) ),
    'batch_location', WriteDiskItem( 'Any Type', 'Matlab script' )
  )

#------------------------------------------------------------------------------

def initialization(self):
  self.setOptional( 'others', 'source_coreg_only', 'others_coreg_only', 'batch_location' )
  
  initializeCoregisterEstimateParameters_withSPM8DefaultValues( self )
  
  self.addLink( 'source_coreg_only', 'source', self.update_spmSourceCoregOnly )
  self.addLink( 'others_coreg_only', 'others', self.update_spmOthersCoregOnly )
  self.addLink( 'source_coreg_only', 'prefix', self.update_spmSourceCoregOnly )
  self.addLink( 'others_coreg_only', 'prefix', self.update_spmOthersCoregOnly )
  
  self.signature['cost_fun'].userLevel = 1
  self.signature['sep'].userLevel = 1
  self.signature['tol'].userLevel = 1
  self.signature['fwhm'].userLevel = 1
  
  self.prefix = """coregister_only_"""
 

#------------------------------------------------------------------------------
#
# Update source_coreg_only location 
# 
def update_spmSourceCoregOnly( self, proc ):
    if self.source is None:
        return
    
    return self.update_spmWarped( self.source.fullPath() )

#------------------------------------------------------------------------------
#
# Update others_coreg_only location
# 
def update_spmOthersCoregOnly( self, proc ):
    if(self.others is None):
        return
    
    outPaths=[]
    for inDI in self.others:
        outPath = self.update_spmWarped( inDI.fullPath())
        outPaths.append(outPath)
    return outPaths    

#------------------------------------------------------------------------------
#
# Get path of output images (input directory + prefix + input filename)
# 
def update_spmWarped(self, inPath):
    inFileName = inPath[inPath.rindex('/') + 1:]
    inDir = inPath[:inPath.rindex('/') + 1]
    outPath = inDir + self.prefix.replace("'", "") + inFileName
    return outPath
  
  
#------------------------------------------------------------------------------
def execution(self, context):  
  print "\n start ", name, "\n"  
      
  sourcePath = self.source.fullPath()
  referencePath = self.reference.fullPath()
  inDir = sourcePath[:sourcePath.rindex('/')]  
  inFileName = sourcePath[sourcePath.rindex('/') + 1:len(sourcePath)-(len(sourcePath)-sourcePath.rindex('.'))]
  
  # Use of temporary file when no batch location entered
  if self.batch_location is None:
      spmJobFile = context.temporary( 'Matlab script' ).fullPath()
  else:
      spmJobFile = self.batch_location.fullPath()
  
  
  # Create copy of source and others otherwise these 
  # images (theirs headers) are modified by SPM.
  # These copies are stored in the same directory as source images but with
  # 'tempo_SPM_coreg' as prefix in the filename
  numImg = 1
  sourceCopyPath = inDir + '/tempo_SPM_coreg_' + inFileName + '.nii'
  shutil.copyfile( sourcePath, sourceCopyPath )
  numImg += 1
      
  othersPath = None
  if(self.others is not None):
    othersPath = [other.fullPath() for other in self.others]
    othersCopyPath = []
    for other in othersPath:
        print other
        othersDir = other[:other.rindex('/')+1]    
        inFileName = other[other.rindex('/') + 1:len(other)-(len(other)-other.rindex('.'))]
        tempoOtherCopy = othersDir + 'tempo_SPM_coreg_' + inFileName + '.nii'
        
        shutil.copyfile( other, tempoOtherCopy )
        othersCopyPath.append( tempoOtherCopy )  
        numImg = numImg + 1
  
  matfilePath = writeCoregisteredEstimateMatFile(context, sourceCopyPath, self.reference.fullPath(), spmJobFile
                                           , othersPath=othersCopyPath, cost_fun=self.cost_fun, sep=self.sep, tol=self.tol, fwhm=self.fwhm)
  
  spm.run( context, configuration, matfilePath )
  
  # Move coregistered source file and other source files in the destination directory
  # specified by BV (by default, results of coregistration estimate only erase default
  # values of the transformation matrix of the source/other file) 
  movePathToDiskItem( sourceCopyPath, self.source_coreg_only )
  
  othersCoregOnlyPath = [other.fullPath() for other in self.others_coreg_only]
  for otherCopy, other in zip(othersCopyPath, othersCoregOnlyPath):
    shutil.move( otherCopy, other )
    #movePathToDiskItem( otherCopy, other ) 
         
  print "\n stop ", name, "\n"
  
#------------------------------------------------------------------------------        

