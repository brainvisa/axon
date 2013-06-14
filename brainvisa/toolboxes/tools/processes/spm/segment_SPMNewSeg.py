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

name = 'segment/normalize (using SPM New Segmentation)'
userLevel = 0

spmJobName = 'newSegment'
def validation():
  return spm.validation(configuration)

# inputs/outputs definition
signature = Signature(
  'MRI_Nat', ReadDiskItem('T1 MRI', 'NIFTI-1 image'),
  'analysis', WriteDiskItem('Analysis Dir', 'Directory'), # ce type ne dépend pas du sujet on peut donc donner une valeur par défaut à l'analyse. Inconvénient : cela créé un répertoire analysis à la racine
  'MRI_Mni_tpmSeg', ReadDiskItem('tissue probability map', 'NIFTI-1 image'),
  'spmJobName', String(),
  
  'c_biasreg', Choice(('no regularisation (0)', '0'), ('extremely light regularisation (0.00001)', '0.00001'), ('very light regularisation (0.0001) *SPM default*', '0.0001')
                    , ('light regularisation (0.001)', '0.001'), ('medium regularisation (0.01)', '0.01'), ('heavy regularisation (0.1)', '0.1'), ('very heavy regularisation (1)', '1'), ('extremely heavy regularisation (10)', '10'),),
  'c_biasfwhm', Choice(('30mm cutoff', '30'), ('40mm cutoff', '40'), ('50mm cutoff', '50'), ('60mm cutoff', '60'), ('70mm cutoff', '70'), ('80mm cutoff', '80'), ('90mm cutoff', '90'), ('100mm cutoff', '100'), ('110mm cutoff', '110'), ('120mm cutoff', '120'), ('130mm cutoff', '130'), ('140mm cutoff', '140'), ('150mm cutoff', '150'), ('No correction', 'Inf')),

  'grey_ngaus', Choice(('1', '1'), ('2', '2') , ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('Nonparametric', 'Inf')),
  'grey_native', Choice(('None', '[0 0]'), ("Native", '[1 0]'), ("DARTEL Imported", '[0 1]'), ("Native + DARTEL Imported", '[1 1]')),
  'grey_nat', WriteDiskItem('T1 MRI Nat GreyProba', 'NIFTI-1 image'),
  'grey_warped', Choice(('None', '[0 0]'), ("Modulated", '[0 1]'), ("UnModulated", '[1 0]'), ("Modulated + UnModulated", '[1 1]')),
  'grey_Mni', WriteDiskItem('T1 MRI Mni GreyProba', 'NIFTI-1 image'),
  
  'white_ngaus', Choice(('1', '1'), ('2', '2') , ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('Nonparametric', 'Inf')),
  'white_native', Choice(('None', '[0 0]'), ("Native", '[1 0]'), ("DARTEL Imported", '[0 1]'), ("Native + DARTEL Imported", '[1 1]')),
  'white_probability', WriteDiskItem('T1 MRI Nat WhiteProba', 'NIFTI-1 image'),
  'white_warped', Choice(('None', '[0 0]'), ("Modulated", '[0 1]'), ("UnModulated", '[1 0]'), ("Modulated + UnModulated", '[1 1]')),

  'csf_ngaus', Choice(('1', '1'), ('2', '2') , ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('Nonparametric', 'Inf')),
  'csf_native', Choice(('None', '[0 0]'), ("Native", '[1 0]'), ("DARTEL Imported", '[0 1]'), ("Native + DARTEL Imported", '[1 1]')),
  'csf_probability', WriteDiskItem('T1 MRI Nat CSFProba', 'NIFTI-1 image'),
  'csf_warped', Choice(('None', '[0 0]'), ("Modulated", '[0 1]'), ("UnModulated", '[1 0]'), ("Modulated + UnModulated", '[1 1]')),

  'bone_ngaus', Choice(('1', '1'), ('2', '2') , ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('Nonparametric', 'Inf')),
  'bone_native', Choice(('None', '[0 0]'), ("Native", '[1 0]'), ("DARTEL Imported", '[0 1]'), ("Native + DARTEL Imported", '[1 1]')),
  'bone_probability', WriteDiskItem('T1 MRI Nat SkullProba', 'NIFTI-1 image'), # Skull = bone
  'bone_warped', Choice(('None', '[0 0]'), ("Modulated", '[0 1]'), ("UnModulated", '[1 0]'), ("Modulated + UnModulated", '[1 1]')),

  'softTissuengaus', Choice(('1', '1'), ('2', '2') , ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('Nonparametric', 'Inf')),
  'softTissuenative', Choice(('None', '[0 0]'), ("Native", '[1 0]'), ("DARTEL Imported", '[0 1]'), ("Native + DARTEL Imported", '[1 1]')),
  'softTissue_probability', WriteDiskItem('T1 MRI Nat ScalpProba', 'NIFTI-1 image'), # Scalp = soft tissus
  'softTissuewarped', Choice(('None', '[0 0]'), ("Modulated", '[0 1]'), ("UnModulated", '[1 0]'), ("Modulated + UnModulated", '[1 1]')),

  'airAndBackground_ngaus', Choice(('1', '1'), ('2', '2') , ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('Nonparametric', 'Inf')),
  'airAndBackground_native', Choice(('None', '[0 0]'), ("Native", '[1 0]'), ("DARTEL Imported", '[0 1]'), ("Native + DARTEL Imported", '[1 1]')),
  'airAndBackground_warped', Choice(('None', '[0 0]'), ("Modulated", '[0 1]'), ("UnModulated", '[1 0]'), ("Modulated + UnModulated", '[1 1]')),

  'write_field', Choice(('None', '[0 0]'), ("Inverse", '[1 0]'), ("Forward", '[0 1]'), ("Inverse + Forward", '[1 1]')),
  'deFld', WriteDiskItem('DefField T1 MRI from Native to Mni', 'NIFTI-1 image'),
  'invDeFld', WriteDiskItem('DefField T1 MRI from Mni to Native', 'NIFTI-1 image'),
  'deFld_segMat', WriteDiskItem('MatDefField T1 MRI from Native to Mni', 'Matlab file'),

  'c_write', Choice(('save nothing', '[0 0]'), ("save bias corrected", '[0 1]'), ("save bias field", '[1 0]'), ("save field and corrected", '[1 1]')),
  'biasCorrected', WriteDiskItem('T1 MRI Bias Corrected', 'NIFTI-1 image'),

  'w_mrf', String(),
  'w_reg', String(),
  'w_affreg', Choice(('No Affine Registration', """''"""), ("ICBM space template - European brains", """'mni'"""), ("ICBM space template - East Asian brains", """'eastern'"""), ("Average sized template", """'subj'"""), ("No regularisation", """'none'""")),
  'w_samp', String(),
)

def initialization(self):

  self.setOptional('biasCorrected')

  self.spmJobName = 'newSegment'
  self.analysis = self.signature["analysis"].findValue({'analysis':'SpmNewSegmentation'})
  self.MRI_Mni_tpmSeg = self.signature["MRI_Mni_tpmSeg"].findValue({})
  seg.initializeUnifiedSegmentationParameters_usingSPM8DefaultValuesForPET(self)
  generateInNativeSpace = """[1 0]"""
  NOgeneration = """[0 0]"""
  UnModulated = """[1 0]"""
  self.grey_native = generateInNativeSpace 
  self.grey_warped = UnModulated
  self.white_native = generateInNativeSpace
  self.white_warped = NOgeneration
  self.csf_native = generateInNativeSpace 
  self.csf_warped = NOgeneration
  self.bone_native = NOgeneration
  self.bone_warped = NOgeneration
  self.softTissuenative = NOgeneration
  self.softTissuewarped = NOgeneration
  self.airAndBackground_native = NOgeneration 
  self.airAndBackground_warped = NOgeneration  
  
  self.addLink('grey_nat', 'MRI_Nat', self.update_grey_Nat)
  self.addLink('grey_nat', 'analysis', self.update_grey_Nat)

  self.addLink('grey_Mni', 'grey_nat')    
  self.addLink("white_probability", "grey_nat")
  self.addLink("csf_probability", "grey_nat")
  self.addLink("bone_probability", "grey_nat")
  self.addLink("softTissue_probability", "grey_nat")
  self.addLink("biasCorrected", "grey_nat")
  self.addLink('deFld', 'grey_nat')
  self.addLink('deFld_segMat', 'grey_nat')
  self.addLink('invDeFld', 'grey_nat')

def update_grey_Nat(self, proc):
  return self.update_WriteDiskItem('T1 MRI Nat GreyProba', 'NIFTI-1 image')

def update_WriteDiskItem(self, typeToCreate, formatToCreate):
  if(self.analysis is not None and self.MRI_Nat is not None):    
    attributes = self.MRI_Nat.hierarchyAttributes()
    attributes.update({'_database':self.getDatabase(), 'analysis':self.getAnalysis()})
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
  context.runProcess('newSegment_SPM_noLinks', MRI_Nat=self.MRI_Nat, MRI_Mni_tpmSeg=self.MRI_Mni_tpmSeg, spmJobName=self.spmJobName
                     , c_biasreg=self.c_biasreg, c_biasfwhm=self.c_biasfwhm, c_write=self.c_write, biasCorrected=self.biasCorrected
                     , grey_ngaus=self.grey_ngaus, grey_native=self.grey_native, grey_nat=self.grey_nat, grey_warped=self.grey_warped, grey_Mni=self.grey_Mni
                     , write_field=self.write_field, deFld=self.deFld, invDeFld=self.invDeFld, deFld_segMat=self.deFld_segMat
                     , white_ngaus=self.white_ngaus, white_native=self.white_native, white_probability=self.white_probability, white_warped=self.white_warped
                     , csf_ngaus=self.csf_ngaus, csf_native=self.csf_native, csf_probability=self.csf_probability, csf_warped=self.csf_warped                     
                     , bone_ngaus=self.bone_ngaus, bone_native=self.bone_native, bone_probability=self.bone_probability, bone_warped=self.bone_warped
                     , softTissuengaus=self.softTissuengaus, softTissuenative=self.softTissuenative, softTissue_probability=self.softTissue_probability, softTissuewarped=self.softTissuewarped
                     , airAndBackground_ngaus=self.airAndBackground_ngaus, airAndBackground_native=self.airAndBackground_native, airAndBackground_warped=self.airAndBackground_warped
                     , w_mrf=self.w_mrf, w_reg=self.w_reg, w_affreg=self.w_affreg, w_samp=self.w_samp
                     )
    
  print "\n stop ", name, "\n"
