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
from brainvisa.data.neuroHierarchy import databases
import brainvisa.tools.spm_run as spm
from brainvisa.tools.spm_basic_models import initialize_pairedTTest_SPM8_default_parameters, write_pairedTTest_matFile

# As this process depends on nuclear imaging toolbox
# it is necessary to test if this is available in the 
# current context
try :
  from nuclearImaging.subjectDataBase import computeCovariateForSPM
except :
  pass


#------------------------------------------------------------------------------
configuration = Application().configuration
#------------------------------------------------------------------------------

def validation():
  return spm.validation(configuration)

#------------------------------------------------------------------------------

userLevel = 1
name = 'Paired T-test (using SPM8)'

#------------------------------------------------------------------------------

signature = Signature(
    'imagesInGroup1',             ListOf( ReadDiskItem('4D Volume', 'NIFTI-1 image') ),
    'imagesInGroup2',             ListOf( ReadDiskItem('4D Volume', 'NIFTI-1 image') ),
    'grandMeanScaling',           Choice( ('No', '0'), ('Yes', '1'), ),
    'ancova',                     Choice( ('No', '0'), ('Yes', '1'), ),
    'covariates',                 ListOf( ReadDiskItem('Text file', 'Text file') ),
    'ThresholdMasking',           Choice( ('None', 'tm_none = 1'),('Absolute', 'tma.athresh = '),('Relative', 'tmr.rthresh = '), ),
    'threshold_masking_value',    String(),
    'implicitMask',               Choice( ('No', '0'), ('Yes', '1'), ),
    'explicitMask',               ReadDiskItem( '4D Volume', 'NIFTI-1 image' ), 
    'GlobalCalculation',          Choice( ('Omit', '1'),('User','2'),('Mean','3'), ),
    'globalNormalisation_grandMeanScaledValue', String(),
    'globalNormalisation',        Choice( ('None', '1'), ('Proportional', '2'), ('ANCOVA', '3'), ),
    'pairedTTest_matFile',        WriteDiskItem( 'Matlab SPM file', 'Matlab file' ),
    'batch_location',             String(),
  
                      )

#------------------------------------------------------------------------------

def initialization(self):
    self.setOptional( 'covariates', 'explicitMask', 'batch_location' )
    
    initialize_pairedTTest_SPM8_default_parameters(self)
      
    self.addLink( 'threshold_masking_value', 'ThresholdMasking', self.update_threshold_masking_value )
    self.addLink( 'batch_location', 'imagesInGroup1', self.update_batch_location )
    self.addLink( 'batch_location', 'imagesInGroup2', self.update_batch_location  )
    self.addLink( 'pairedTTest_matFile', 'imagesInGroup1' )
    self.addLink( 'pairedTTest_matFile', 'imagesInGroup2' )
    
    
    
#------------------------------------------------------------------------------
#
# Update SPM batch location when imagesInGroup1 and imagesInGroup2 are filled. 
# By default, batch has a generic name (batch_paired_t_test_analysis.m') and is 
# stored in the same directory as first image of imagesInGroup1 
#    
def update_batch_location( self, context ):
    if len(self.imagesInGroup1) > 0 and len(self.imagesInGroup2)>0:
        imgPath = str( self.imagesInGroup1[0] )
        imgDir = imgPath[:imgPath.rindex('/') + 1]
        return imgDir + 'batch_paired_t_test_analysis.m'
    
    
       
#------------------------------------------------------------------------------
#
# Update threshold masking value with SPM8 default value.
#
def update_threshold_masking_value(self, proc):
    if(self.ThresholdMasking == 'tm_none = 1'):
      return 'None'
    elif(self.ThresholdMasking == 'tmr.rthresh = '):# relative
      return '0.8'
    elif(self.ThresholdMasking == 'tma.athresh = '):# absolute
      return '100'
  
#------------------------------------------------------------------------------

def execution(self, context):  
    print "\n start ", name, "\n"
    
    context.write('Paired T-Test (using SPM8)')
    checkFilePaths(context, self.imagesInGroup1, 'group 1')
    checkFilePaths(context, self.imagesInGroup2, 'group 2')
    checkFilePaths(context, self.covariates, 'covariates')
    context.write('   Threshold Masking : '+str(self.thresholdMasking_decode()))
    context.write('   Threshold value : '+str(self.threshold_masking_value))
    
    if(os.path.exists(self.pairedTTest_matFile.fullPath())):
        os.remove(self.pairedTTest_matFile.fullPath())
    
    # Check the two lists have the same size  
    if len( self.imagesInGroup1 ) != len( self.imagesInGroup2 ):
        context.error( "The two groups need to have the same size! (", len(self.imagesInGroup1)," subjects in the first group, ", len( self.imagesInGroup2 )  , " subjects in the second one )\n"  )
        
    else:
      
        pairsPathList_time_point_1 = [image.fullPath() for image in self.imagesInGroup1]
        pairsPathList_time_point_2 = [image.fullPath() for image in self.imagesInGroup2]
        
        #making paired list for SPM
        pairsPathList = []
        for ind in range( len( pairsPathList_time_point_1 ) ):
            pairsPathList.append( [ pairsPathList_time_point_1[ind],pairsPathList_time_point_2[ind] ] )
        
        covariatesForSPM, subjectsWithoutCovariates = computeCovariateForSPM(self.covariates, pairsPathList_time_point_1, pairsPathList_time_point_2)#To do verification about it
        
        for suj, covName in subjectsWithoutCovariates:
            msg = "missing covariate " + covName + " for subject " + suj
            print msg
            context.error(msg)
          
        outDir = self.pairedTTest_matFile.fullPath()[:self.pairedTTest_matFile.fullPath().rindex('/')]  
        spmJobFile = self.batch_location
        
        mat_file = open(spmJobFile, 'w')
        matfileDI = None  
        
        ThresholdMasking=self.ThresholdMasking
        if(ThresholdMasking != 'tm_none = 1'):
            ThresholdMasking += self.threshold_masking_value
        
        if(self.explicitMask is None):
            explicitMaskSpmValue = """{''}"""
        else:
            explicitMaskSpmValue = """{'"""+self.explicitMask.fullPath()+""",1'}"""
        
        matfilePath = write_pairedTTest_matFile(context, pairsPathList=pairsPathList, matfileDI=matfileDI, mat_file=mat_file                                            
                                              , outDir=outDir, gmsca=self.grandMeanScaling, ancova=self.ancova
                                              , tm=ThresholdMasking, im=self.implicitMask, em=explicitMaskSpmValue
                                              , g_omit=self.GlobalCalculation, gmsca_no=self.globalNormalisation_grandMeanScaledValue, gmsca_yes_gmscv=self.globalNormalisation_grandMeanScaledValue
                                              , glonorm=self.globalNormalisation, cov=covariatesForSPM
                                              )
        spm.run(context, configuration, matfilePath)#, isMatlabMandatory=True)   
        
        if(os.path.exists( outDir + "/SPM.mat")):
            os.system("mv " + outDir + "/SPM.mat " + self.pairedTTest_matFile.fullPath())
    
    print "\n stop ", name, "\n"

#------------------------------------------------------------------------------

def checkFilePaths(context, filePaths, msg):
    for filePath in filePaths:
        if (os.path.exists(filePath.fullPath()) == False):
            context.error("filePath.fullPath() does not exists! check "+msg)
            raise Exception  
    context.write('   '+msg+' : '+str(len(filePaths)) + ' elements')


def thresholdMasking_decode(self):
    if(self.ThresholdMasking == 'tm_none = 1'):
        return 'None'
    elif(self.ThresholdMasking == 'tma.athresh = '):
        return 'Absolute'
    elif(self.ThresholdMasking == 'tmr.rthresh = '):
        return 'Relative'
