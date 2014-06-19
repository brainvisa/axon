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
import brainvisa.tools.spm_run as spm
import brainvisa.tools.spm_segmentation as seg

configuration = Application().configuration
spm8Path = spm.getSpm8Path(configuration)

name = 'segment/normalize (using VBM toolboxe)'
userLevel = 0

def validation():
  return spm.validation(configuration)

signature = Signature(
  'MRI_Nat', ReadDiskItem('T1 MRI', 'NIFTI-1 image'),
  'analysis', WriteDiskItem('Analysis Dir', 'Directory'), # ce type ne dépend pas du sujet on peut donc donner une valeur par défaut à l'analyse. Inconvénient : cela créé un répertoire analysis à la racine
  'MRI_Mni_tpmSeg', ReadDiskItem('tissue probability map', 'NIFTI-1 image'),  
  'spmJobName', String(), 
  
  'ngaus', String(),
  'biasreg', Choice(('no regularisation (0)', '0'), ('extremely light regularisation (0.00001)', '0.00001'), ('very light regularisation (0.0001) *SPM default*', '0.0001')
                    , ('light regularisation (0.001)', '0.001'), ('medium regularisation (0.01)', '0.01'), ('heavy regularisation (0.1)', '0.1'), ('very heavy regularisation (1)', '1'), ('extremely heavy regularisation (10)', '10'),),

  'biasfwhm', Choice(('30mm cutoff', '30'), ('40mm cutoff', '40'), ('50mm cutoff', '50'), ('60mm cutoff', '60'), ('70mm cutoff', '70'), ('80mm cutoff', '80'), ('90mm cutoff', '90'), ('100mm cutoff', '100'), ('110mm cutoff', '110'), ('120mm cutoff', '120'), ('130mm cutoff', '130'), ('140mm cutoff', '140'), ('150mm cutoff', '150'), ('No correction', 'Inf')),
  'affreg', Choice(('No Affine Registration', """''"""), ("ICBM space template - European brains", """'mni'"""), ("ICBM space template - East Asian brains", """'eastern'"""), ("Average sized template", """'subj'"""), ("No regularisation", """'none'""")),
  'warpreg', String(),
  'samp', String(),
  'norm', Choice(('Low-dimensional: SPM default', """Low"""), ('High-dimensional: Dartel', """Dartel""")),
  'DartelTemplate', WriteDiskItem('Dartel Template', 'Aims readable volume formats'),
  'sanlm', Choice(('No denoising', '0'), ('Denoising', '1'), ('Denoising (multi-threaded)', '2')),
  'mrf', String(),
  'cleanup', Choice(('Dont do cleanup', '0'), ('Light Clean', '1'), ('Thorough Clean', '2')),
  'pprint', String(),
  
  'grey_native', Choice(('none', '0'), ('yes', '1')),
  'grey_nat', WriteDiskItem('T1 MRI Nat GreyProba', 'NIFTI-1 image'),
  'grey_warped', Choice(('none', '0'), ('yes', '1')),
  'grey_Mni', WriteDiskItem('T1 MRI Mni GreyProba', 'NIFTI-1 image'),
  'grey_modulated', Choice(('none', '0'), ('affiche + non-linear (SPM8 default)', '1'), ('non-linear only', '2')),
  'grey_dartel', Choice(('none', '0'), ('rigid (SPM8 default)', '1'), ('affine', '2')),

  'wm_native', Choice(('none', '0'), ('yes', '1')),
  'white_Nat', WriteDiskItem('T1 MRI Nat WhiteProba', 'NIFTI-1 image'),
  'wm_warped', Choice(('none', '0'), ('yes', '1')),
  'wm_modulated', Choice(('none', '0'), ('affiche + non-linear (SPM8 default)', '1'), ('non-linear only', '2')),
  'wm_dartel', Choice(('none', '0'), ('rigid (SPM8 default)', '1'), ('affine', '2')),

  'csf_native', Choice(('none', '0'), ('yes', '1')),
  'csf_Nat', WriteDiskItem('T1 MRI Nat CSFProba', 'NIFTI-1 image'),
  'csf_warped', Choice(('none', '0'), ('yes', '1')),
  'csf_modulated', Choice(('none', '0'), ('affiche + non-linear (SPM8 default)', '1'), ('non-linear only', '2')),
  'csf_dartel', Choice(('none', '0'), ('rigid (SPM8 default)', '1'), ('affine', '2')),

  'deFld', WriteDiskItem('DefField T1 MRI from Native to Mni', 'NIFTI-1 image'),
  'invDeFld', WriteDiskItem('DefField T1 MRI from Mni to Native', 'NIFTI-1 image'),
  'deFld_segMat', WriteDiskItem('MatDefField T1 MRI from Native to Mni', 'Matlab file'),
  
  'saveBias', Choice(('save bias corrected', '1'), ('None', '0')),
  'biasCorrected', WriteDiskItem('T1 MRI Bias Corrected', 'NIFTI-1 image'),

  'generateJacobianDeterminant', Choice(('none', '0'), ('normalized', '1')),
  'jacobianDeterminant', WriteDiskItem('JacobianDeterminant', 'Aims readable volume formats'),
)

def initialization(self):
  
  self.setOptional('biasCorrected','DartelTemplate')

  self.spmJobName = 'vbmSegment'
  self.analysis = self.signature["analysis"].findValue({'analysis':'VBMSegmentation'})
  self.MRI_Mni_tpmSeg = self.signature["MRI_Mni_tpmSeg"].findValue({})
  seg.initializeVBMSegmentationParameters_usingSPM8DefaultValues(self) 
  generate = """1"""
  NOgeneration = """0"""
  self.grey_native = generate
  self.grey_warped = generate
  self.grey_modulated = NOgeneration
  self.grey_dartel = NOgeneration
  self.wm_native = generate
  self.wm_warped = NOgeneration
  self.wm_modulated = NOgeneration
  self.wm_dartel = NOgeneration
  self.csf_native = generate
  self.csf_warped = NOgeneration
  self.csf_modulated = NOgeneration
  self.csf_dartel = NOgeneration
  self.saveBias = NOgeneration
    
  self.addLink('grey_nat', ( 'MRI_Nat', 'analysis' ), self.update_grey_Nat)
  
  self.addLink("grey_Mni", "grey_nat")
  self.addLink("white_Nat", "grey_nat")
  self.addLink("csf_Nat", "grey_nat")
  self.addLink("biasCorrected", "grey_nat")    
  self.addLink('deFld', 'grey_nat')
  self.addLink('invDeFld', 'grey_nat')
  self.addLink('deFld_segMat', 'grey_nat')  
  self.addLink('jacobianDeterminant', 'grey_nat')  

def update_grey_Nat(self, proc, dummy):
  return self.update_WriteDiskItem('T1 MRI Nat GreyProba', 'NIFTI-1 image')

def update_WriteDiskItem(self, typeToCreate, formatToCreate):
  if(self.analysis is not None and self.MRI_Nat is not None):    
    attributes = self.MRI_Nat.hierarchyAttributes()
    db = self.getDatabase()
    if db is not None:
        attributes[ '_database' ] = db
    analysis = self.getAnalysis()
    if analysis is not None:
        attributes[ 'analysis' ] = analysis
    return createDiskItem(typeToCreate, formatToCreate, attributes)
  
def createDiskItem(typeToCreate, formatToCreate, attributes):
    DIFinder = WriteDiskItem(typeToCreate, formatToCreate)
    DI = DIFinder.findValue(attributes)
    return DI

def getAnalysis(self):
  return self.analysis.hierarchyAttributes()['analysis']

def getDatabase(self):
  return self.analysis.hierarchyAttributes()['_database']
      
def execution(self, context):
  print "\n start ", name, "\n"
  #momoTODO : c vraiment pas terrible de passer tous ces paramètres... faire de l'héritage de signature entre process?
  context.runProcess('segment_VBM_noLinks', MRI_Nat=self.MRI_Nat, MRI_Mni_tpmSeg=self.MRI_Mni_tpmSeg, spmJobName = self.spmJobName
                    , ngaus=self.ngaus, biasreg=self.biasreg, saveBias=self.saveBias, biasCorrected=self.biasCorrected
                    , biasfwhm=self.biasfwhm, affreg=self.affreg, warpreg=self.warpreg, samp=self.samp
                    , norm=self.norm, DartelTemplate=self.DartelTemplate, sanlm=self.sanlm, mrf=self.mrf, cleanup=self.cleanup, pprint=self.pprint
                    , grey_native=self.grey_native, grey_nat=self.grey_nat, grey_warped=self.grey_warped, grey_Mni=self.grey_Mni,grey_modulated=self.grey_modulated, grey_dartel=self.grey_dartel
                    , wm_native=self.wm_native, white_Nat=self.white_Nat, wm_warped=self.wm_warped, wm_modulated=self.wm_modulated, wm_dartel=self.wm_dartel
                    , csf_native=self.csf_native, csf_Nat=self.csf_Nat, csf_warped=self.csf_warped, csf_modulated=self.csf_modulated, csf_dartel=self.csf_dartel
                    , deFld=self.deFld, invDeFld=self.invDeFld, deFld_segMat=self.deFld_segMat
                    , generateJacobianDeterminant=self.generateJacobianDeterminant, jacobianDeterminant=self.jacobianDeterminant)
    
  print "\n stop ", name, "\n"

