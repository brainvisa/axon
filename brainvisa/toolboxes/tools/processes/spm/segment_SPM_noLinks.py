# -*- coding: utf-8 -*-
#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
#      Equipe Cogimage
#      UPMC, CRICM, UMR-S975
#      CNRS, UMR 7225
#      INSERM, U975
#      Hopital Pitie Salpetriere
#      47 boulevard de l'Hopital
#      75651 Paris cedex 13
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
from brainvisa.tools.spm_segmentation import writeSegmentationMatFile
from brainvisa.tools.spm_utils import movePathToDiskItem, movePath
import brainvisa.tools.spm_run as spm

configuration = Application().configuration
spm8Path = spm.getSpm8Path(configuration)

# you should use this process because :
# - all types are generic : so can be used with any new hierarchy
# - no links between parameters : so can be easily used in pipelines (no need to remove links when using it)
name = 'segment/normalize (using SPM segmentation - no links between parameters)' 
userLevel = 2

spmJobName = 'segment'

def validation():
  return spm.validation(configuration)

signature = Signature(
  'MRI_Nat', ReadDiskItem('4D Volume', 'Aims readable volume formats'),
  'MRI_Mni_tpmSeg', ReadDiskItem('4D Volume', 'Aims readable volume formats'),
  'spmJobName', String(), 
  
  'GM', Choice(('None', """[0 0 0]"""), ('Native Space', """[0 0 1]"""), ('Unmodulated Normalised', """[0 1 0]"""), ('Modulated Normalised', """[1 0 0]""")
              , ('Native + Unmodulated Normalised', """[0 1 1]"""), ('Native + Modulated Normalised', """[1 0 1]"""), ('Native + Modulated + Unmodulated', """[1 1 1]""")
              , ('Modulated + Unmodulated Normalised', """[1 1 0]""")),
  'grey_Nat', WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'grey_Mni', WriteDiskItem('4D Volume', 'Aims readable volume formats'),

  'WM', Choice(('None', """[0 0 0]"""), ('Native Space', """[0 0 1]"""), ('Unmodulated Normalised', """[0 1 0]"""), ('Modulated Normalised', """[1 0 0]""")
              , ('Native + Unmodulated Normalised', """[0 1 1]"""), ('Native + Modulated Normalised', """[1 0 1]"""), ('Native + Modulated + Unmodulated', """[1 1 1]""")
              , ('Modulated + Unmodulated Normalised', """[1 1 0]""")),
  'white_Nat', WriteDiskItem('4D Volume', 'Aims readable volume formats'),

  'CSF', Choice(('None', """[0 0 0]"""), ('Native Space', """[0 0 1]"""), ('Unmodulated Normalised', """[0 1 0]"""), ('Modulated Normalised', """[1 0 0]""")
              , ('Native + Unmodulated Normalised', """[0 1 1]"""), ('Native + Modulated Normalised', """[1 0 1]"""), ('Native + Modulated + Unmodulated', """[1 1 1]""")
              , ('Modulated + Unmodulated Normalised', """[1 1 0]""")),
  'csf_Nat', WriteDiskItem('4D Volume', 'Aims readable volume formats'),

  'biasreg', Choice(('no regularisation (0)', '0'), ('extremely light regularisation (0.00001)', '0.00001'), ('very light regularisation (0.0001) *SPM default*', '0.0001')
                    , ('light regularisation (0.001)', '0.001'), ('medium regularisation (0.01)', '0.01'), ('heavy regularisation (0.1)', '0.1'), ('very heavy regularisation (1)', '1'), ('extremely heavy regularisation (10)', '10'),),
  'biascor', Choice(('save bias corrected', '1'), ("don't save bias corrected", '0')),
  'biasCorrected', WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'cleanup', Choice(('Dont do cleanup', '0'), ('Light Clean', '1'), ('Thorough Clean', '2')),
  'ngaus', String(),
  'regtype', Choice(('No Affine Registration', """"""), ("ICBM space template - European brains", """mni"""), ("ICBM space template - East Asian brains", """eastern"""), ("Average sized template", """subj"""), ("No regularisation", """none""")),
  'warpreg', String(),
  'warpco', String(),
  'biasfwhm', Choice(('30mm cutoff', '30'), ('40mm cutoff', '40'), ('50mm cutoff', '50'), ('60mm cutoff', '60'), ('70mm cutoff', '70'), ('80mm cutoff', '80'), ('90mm cutoff', '90'), ('100mm cutoff', '100'), ('110mm cutoff', '110'), ('120mm cutoff', '120'), ('130mm cutoff', '130'), ('140mm cutoff', '140'), ('150mm cutoff', '150'), ('No correction', 'Inf')),
  'samp', String(),
  'msk', String(),
  
  'snMat', WriteDiskItem('Any Type', 'Matlab file'),
  'snInvMat', WriteDiskItem('Any Type', 'Matlab file'),

)

def initialization(self):
  self.setOptional('grey_Nat', 'biasCorrected')

def execution(self, context):
  print("\n start ", name, "\n")
 
  inDir = self.MRI_Nat.fullPath()
  inDir = inDir[:inDir.rindex('/')]  
  spmJobFile = inDir + '/' + spmJobName + '_job.m'
      
  tpms = """{
                                                  """ + str(self.MRI_Mni_tpmSeg.fullPath()) + """
                                                  """ + str(spm8Path) + """/tpm/white.nii'
                                                  """ + str(spm8Path) + """/tpm/csf.nii'
                                                  }"""


  matfilePath = writeSegmentationMatFile(context, configuration, self.MRI_Nat.fullPath(), spmJobFile
                                             , self.GM, self.WM, self.CSF, self.biascor, self.cleanup
                                             , tpms, self.ngaus
                                             , self.regtype, self.warpreg, self.warpco, self.biasreg
                                             , self.biasfwhm, self.samp, self.msk)
    
  spm.run(context, configuration, matfilePath)    
  
  self.moveSpmOutFiles()
  print("\n stop ", name, "\n")


def moveSpmOutFiles(self):
  subjectName = os.path.basename(self.MRI_Nat.fullPath()).partition(".")[0]
  inDir = os.path.dirname(self.MRI_Nat.fullName())  
  outDir = os.path.dirname(self.grey_Nat.fullName())
  
  grey = inDir + "/c1" + subjectName + ".nii"
  movePathToDiskItem(grey, self.grey_Nat)
  grey = inDir + "/wc1" + subjectName + ".nii"
  movePathToDiskItem(grey, self.grey_Mni)
  white = inDir + "/c2" + subjectName + ".nii"
  movePathToDiskItem(white, self.white_Nat)
  csf = inDir + "/c3" + subjectName + ".nii"
  movePathToDiskItem(csf, self.csf_Nat)
  snMat = inDir + '/' + subjectName + "_seg_sn" + ".mat"
  movePathToDiskItem(snMat, self.snMat)  
  snInvMat = inDir + '/' + subjectName + "_seg_inv_sn" + ".mat"
  movePathToDiskItem(snInvMat, self.snInvMat)
  
  job = inDir + '/' + spmJobName + "_job.m"
  movePath(job, outDir + '/' + spmJobName + "_job.m")
  batch = inDir + '/' + spmJobName + ".m"
  movePath(batch, outDir + '/' + spmJobName + ".m")
  
  biasCorrected = inDir + "/m" + subjectName + ".nii"
  movePathToDiskItem(biasCorrected, self.biasCorrected)
