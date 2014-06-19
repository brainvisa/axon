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

from brainvisa.processes import *
from brainvisa.tools.spm_segmentation import writeVBMSegmentationMatFile
from brainvisa.tools.spm_utils import movePathToDiskItem, movePath
import brainvisa.tools.spm_run as spm

configuration = Application().configuration
spm8Path = spm.getSpm8Path(configuration)

# you should use this process because :
# - all types are generic : so can be used with any new hierarchy
# - no links between parameters : so can be easily used in pipelines (no need to remove links when using it)
name = 'segment/normalize (using VBM toolboxe - no links between parameters)' # no links between parameters so can be easily used in pipelines
userLevel = 2

def validation():
  return spm.validation(configuration)

# inputs/outputs definition
signature = Signature(
  'MRI_Nat', ReadDiskItem('4D Volume', 'Aims readable volume formats'),
  'MRI_Mni_tpmSeg', ReadDiskItem('4D Volume', 'Aims readable volume formats'), 
  'spmJobName', String(), 
  
  'ngaus', String(),
  'biasreg', Choice(('no regularisation (0)', '0'), ('extremely light regularisation (0.00001)', '0.00001'), ('very light regularisation (0.0001) *SPM default*', '0.0001')
                    , ('light regularisation (0.001)', '0.001'), ('medium regularisation (0.01)', '0.01'), ('heavy regularisation (0.1)', '0.1'), ('very heavy regularisation (1)', '1'), ('extremely heavy regularisation (10)', '10'),),
  'saveBias', Choice(('save bias corrected', '1'), ('None', '0')),
  'biasCorrected', WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'biasfwhm', Choice(('30mm cutoff', '30'), ('40mm cutoff', '40'), ('50mm cutoff', '50'), ('60mm cutoff', '60'), ('70mm cutoff', '70'), ('80mm cutoff', '80'), ('90mm cutoff', '90'), ('100mm cutoff', '100'), ('110mm cutoff', '110'), ('120mm cutoff', '120'), ('130mm cutoff', '130'), ('140mm cutoff', '140'), ('150mm cutoff', '150'), ('No correction', 'Inf')),
  'affreg', Choice(('No Affine Registration', ''), ("ICBM space template - European brains", 'mni'), ("ICBM space template - East Asian brains", 'eastern'), ("Average sized template", 'subj'), ("No regularisation", 'none')),
  'warpreg', String(),
  'samp', String(),
  'norm', Choice(('Low-dimensional: SPM default', """Low"""), ('High-dimensional: Dartel', """Dartel""")),
  'DartelTemplate', WriteDiskItem('Dartel Template', 'Aims readable volume formats'),
  'sanlm', Choice(('No denoising', '0'), ('Denoising', '1'), ('Denoising (multi-threaded)', '2')),
  'mrf', String(),
  'cleanup', Choice(('Dont do cleanup', '0'), ('Light Clean', '1'), ('Thorough Clean', '2')),
  'pprint', String(),
  
  'grey_native', Choice(('none', '0'), ('yes', '1')),
  'grey_nat', WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'grey_warped', Choice(('none', '0'), ('yes', '1')),
  'grey_Mni', WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'grey_modulated', Choice(('none', '0'), ('affiche + non-linear (SPM8 default)', '1'), ('non-linear only', '2')),
  'grey_dartel', Choice(('none', '0'), ('rigid (SPM8 default)', '1'), ('affine', '2')),

  'wm_native', Choice(('none', '0'), ('yes', '1')),
  'white_Nat', WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'wm_warped', Choice(('none', '0'), ('yes', '1')),
  'wm_modulated', Choice(('none', '0'), ('affiche + non-linear (SPM8 default)', '1'), ('non-linear only', '2')),
  'wm_dartel', Choice(('none', '0'), ('rigid (SPM8 default)', '1'), ('affine', '2')),

  'csf_native', Choice(('none', '0'), ('yes', '1')),
  'csf_Nat', WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'csf_warped', Choice(('none', '0'), ('yes', '1')),
  'csf_modulated', Choice(('none', '0'), ('affiche + non-linear (SPM8 default)', '1'), ('non-linear only', '2')),
  'csf_dartel', Choice(('none', '0'), ('rigid (SPM8 default)', '1'), ('affine', '2')),

  'deFld', WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'invDeFld', WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'deFld_segMat', WriteDiskItem('Matlab SPM file', 'Matlab file'),

  'generateJacobianDeterminant', Choice(('none', '0'), ('normalized', '1')),
  'jacobianDeterminant', WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  
  )

def initialization(self):  
  self.setOptional('biasCorrected', 'DartelTemplate')
  self.spmJobName = 'vbmSegment'
      
def execution(self, context):
  print "\n start ", name, "\n"
 
  inDir = self.MRI_Nat.fullPath()
  inDir = inDir[:inDir.rindex('/')]  
  spmJobFile = inDir + '/' + self.spmJobName+'_job.m'
  
  if(self.norm == "Dartel"):
    norm="""high.darteltpm = {'"""+self.DartelTemplate.fullPath()+"""'}"""
  else:
    norm = """low = struct([])"""

  matfilePath = writeVBMSegmentationMatFile(context, configuration, self.MRI_Nat.fullPath(), spmJobFile
                              , self.MRI_Mni_tpmSeg, self.ngaus, self.biasreg, self.biasfwhm, "'"+self.affreg+"'", self.warpreg, self.samp
                              , norm, self.sanlm, self.mrf, self.cleanup, self.pprint
                              , self.grey_native, self.grey_warped, self.grey_modulated, self.grey_dartel
                              , self.wm_native, self.wm_warped, self.wm_modulated, self.wm_dartel
                              , self.csf_native, self.csf_warped, self.csf_modulated, self.csf_dartel
                              , self.saveBias, self.generateJacobianDeterminant
                              )    
  spm.run(context, configuration, matfilePath, isMatlabMandatory=True)   
  self.moveSpmOutFiles()
  
  print "\n stop ", name, "\n"

def moveSpmOutFiles(self):
  subjectName = os.path.basename(self.MRI_Nat.fullPath()).partition(".")[0]
  ext = os.path.basename(self.MRI_Nat.fullPath()).partition(".")[2]
  inDir = os.path.dirname(self.MRI_Nat.fullName())
  outDir = os.path.dirname(self.grey_nat.fullName())
  
  grey = inDir + "/p1" + subjectName + "." + ext
  movePathToDiskItem(grey, self.grey_nat)
  grey = inDir + "/wp1" + subjectName + "." + ext
  movePathToDiskItem(grey, self.grey_Mni)
  white = inDir + "/p2" + subjectName + ".nii"
  movePathToDiskItem(white, self.white_Nat)
  csf = inDir + "/p3" + subjectName + ".nii"
  movePathToDiskItem(csf, self.csf_Nat)
  jacobianDeterminant = inDir + "/jac_wrp1" + subjectName + ".nii"
  movePathToDiskItem(jacobianDeterminant, self.jacobianDeterminant)
    
  imDefField = inDir + "/y_" + subjectName + ".nii" # /iy is inverse deformation field
  movePathToDiskItem(imDefField, self.deFld)
  imInvDefField = inDir + "/iy_" + subjectName + "." + ext # /iy is inverse deformation field
  movePathToDiskItem(imInvDefField, self.invDeFld)
  trSeg8Mat = inDir + "/" + subjectName + "_seg8.mat"  
  movePathToDiskItem(trSeg8Mat, self.deFld_segMat)

  movePath(inDir + "/p" + subjectName + "_seg8.txt", outDir + "/p" + subjectName + "_seg8.txt")
    
  job = inDir + '/' + self.spmJobName + "_job.m"
  movePath(job, outDir + '/' + self.spmJobName + "_job.m")
  batch = inDir + '/' + self.spmJobName + ".m"
  movePath(batch, outDir + '/' + self.spmJobName + ".m")  
  
  biasCorrected = inDir + "/m" + subjectName + ".nii"
  movePathToDiskItem(biasCorrected, self.biasCorrected)
  
