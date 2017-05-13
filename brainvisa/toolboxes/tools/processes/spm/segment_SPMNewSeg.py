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
  'grey_native_space', Choice(('None', '[0 0]'), ('Native', '[1 0]'), ('DARTEL Imported', '[0 1]'), ('Native + DARTEL Imported', '[1 1]')),
  'grey_native', WriteDiskItem('T1 MRI Nat GreyProba', 'NIFTI-1 image'),
  'grey_dartel_imported', WriteDiskItem('T1 MRI Mni GreyProba Dartel imported', 'NIFTI-1 image', requiredAttributes={"transformation":"rigid"}),
  'grey_warped', Choice(('None', '[0 0]'), ('Modulated', '[0 1]'), ('Unmodulated', '[1 0]'), ('Modulated + Unmodulated', '[1 1]')),
  'grey_mni_unmodulated', WriteDiskItem('T1 MRI Mni GreyProba', 'NIFTI-1 image', requiredAttributes = {'modulated':'no', "normalization":"low-dimensional"}),
  'grey_mni_modulated', WriteDiskItem('T1 MRI Mni GreyProba', 'NIFTI-1 image', requiredAttributes = {'modulated':'yes', "modulation":"affine and non-linear", "normalization":"low-dimensional"}),

  'white_ngaus', Choice(('1', '1'), ('2', '2') , ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('Nonparametric', 'Inf')),
  'white_native_space', Choice(('None', '[0 0]'), ('Native', '[1 0]'), ('DARTEL Imported', '[0 1]'), ('Native + DARTEL Imported', '[1 1]')),
  'white_native', WriteDiskItem('T1 MRI Nat WhiteProba', 'NIFTI-1 image'),
  'white_dartel_imported', WriteDiskItem('T1 MRI Mni WhiteProba Dartel imported', 'NIFTI-1 image', requiredAttributes={"transformation":"rigid"}),
  'white_warped', Choice(('None', '[0 0]'), ('Modulated', '[0 1]'), ('Unmodulated', '[1 0]'), ('Modulated + Unmodulated', '[1 1]')),
  'white_mni_unmodulated', WriteDiskItem('T1 MRI Mni WhiteProba', 'NIFTI-1 image', requiredAttributes = {'modulated':'no', "normalization":"low-dimensional"}),
  'white_mni_modulated', WriteDiskItem('T1 MRI Mni WhiteProba', 'NIFTI-1 image', requiredAttributes = {'modulated':'yes', "modulation":"affine and non-linear", "normalization":"low-dimensional"}),

  'csf_ngaus', Choice(('1', '1'), ('2', '2') , ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('Nonparametric', 'Inf')),
  'csf_native_space', Choice(('None', '[0 0]'), ('Native', '[1 0]'), ('DARTEL Imported', '[0 1]'), ('Native + DARTEL Imported', '[1 1]')),
  'csf_native', WriteDiskItem('T1 MRI Nat CSFProba', 'NIFTI-1 image'),
  'csf_dartel_imported', WriteDiskItem('T1 MRI Mni CSFProba Dartel imported', 'NIFTI-1 image', requiredAttributes={"transformation":"rigid"}),
  'csf_warped', Choice(('None', '[0 0]'), ('Modulated', '[0 1]'), ('Unmodulated', '[1 0]'), ('Modulated + Unmodulated', '[1 1]')),
  'csf_mni_unmodulated', WriteDiskItem('T1 MRI Mni CSFProba', 'NIFTI-1 image', requiredAttributes = {'modulated':'no', "normalization":"low-dimensional"}),
  'csf_mni_modulated', WriteDiskItem('T1 MRI Mni CSFProba', 'NIFTI-1 image', requiredAttributes = {'modulated':'yes', "modulation":"affine and non-linear", "normalization":"low-dimensional"}),

  'bone_ngaus', Choice(('1', '1'), ('2', '2') , ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('Nonparametric', 'Inf')),
  'bone_native_space', Choice(('None', '[0 0]'), ('Native', '[1 0]'), ('DARTEL Imported', '[0 1]'), ('Native + DARTEL Imported', '[1 1]')),
  'bone_native', WriteDiskItem('T1 MRI Nat SkullProba', 'NIFTI-1 image'), # Skull = bone
  'bone_dartel_imported', WriteDiskItem('T1 MRI Mni SkullProba Dartel imported', 'NIFTI-1 image', requiredAttributes={"transformation":"rigid"}), # Skull = bone
  'bone_warped', Choice(('None', '[0 0]'), ('Modulated', '[0 1]'), ('Unmodulated', '[1 0]'), ('Modulated + Unmodulated', '[1 1]')),
  'bone_mni_unmodulated', WriteDiskItem('T1 MRI Mni SkullProba', 'NIFTI-1 image', requiredAttributes = {'modulated':'no', "normalization":"low-dimensional"}),
  'bone_mni_modulated', WriteDiskItem('T1 MRI Mni SkullProba', 'NIFTI-1 image', requiredAttributes = {'modulated':'yes', "modulation":"affine and non-linear", "normalization":"low-dimensional"}),

  'softTissue_ngaus', Choice(('1', '1'), ('2', '2') , ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('Nonparametric', 'Inf')),
  'softTissue_native_space', Choice(('None', '[0 0]'), ('Native', '[1 0]'), ('DARTEL Imported', '[0 1]'), ('Native + DARTEL Imported', '[1 1]')),
  'softTissue_native', WriteDiskItem('T1 MRI Nat ScalpProba', 'NIFTI-1 image'), # Scalp = soft tissues
  'softTissue_dartel_imported', WriteDiskItem('T1 MRI Mni ScalpProba Dartel imported', 'NIFTI-1 image', requiredAttributes={"transformation":"rigid"}), # Scalp = soft tissues
  'softTissue_warped', Choice(('None', '[0 0]'), ('Modulated', '[0 1]'), ('Unmodulated', '[1 0]'), ('Modulated + Unmodulated', '[1 1]')),
  'softTissue_mni_unmodulated', WriteDiskItem('T1 MRI Mni ScalpProba', 'NIFTI-1 image', requiredAttributes = {'modulated':'no', "normalization":"low-dimensional"}),
  'softTissue_mni_modulated', WriteDiskItem('T1 MRI Mni ScalpProba', 'NIFTI-1 image', requiredAttributes = {'modulated':'yes', "modulation":"affine and non-linear", "normalization":"low-dimensional"}),

  'airAndBackground_ngaus', Choice(('1', '1'), ('2', '2') , ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('Nonparametric', 'Inf')),
  'airAndBackground_native_space', Choice(('None', '[0 0]'), ('Native', '[1 0]'), ('DARTEL Imported', '[0 1]'), ('Native + DARTEL Imported', '[1 1]')),
  'airAndBackground_warped', Choice(('None', '[0 0]'), ('Modulated', '[0 1]'), ('Unmodulated', '[1 0]'), ('Modulated + Unmodulated', '[1 1]')),

  'write_field', Choice(('None', '[0 0]'), ('Inverse', '[1 0]'), ('Forward', '[0 1]'), ('Inverse + Forward', '[1 1]')),
  'deFld', WriteDiskItem('DefField T1 MRI from Native to Mni', 'NIFTI-1 image'),
  'invDeFld', WriteDiskItem('DefField T1 MRI from Mni to Native', 'NIFTI-1 image'),
  'deFld_segMat', WriteDiskItem('MatDefField T1 MRI from Native to Mni', 'Matlab file'),

  'c_write', Choice(('save nothing', '[0 0]'), ('save bias corrected', '[0 1]'), ('save bias field', '[1 0]'), ('save field and corrected', '[1 1]')),
  'biasCorrected', WriteDiskItem('T1 MRI Bias Corrected', 'NIFTI-1 image'),

  'w_mrf', String(),
  'w_reg', String(),
  'w_affreg', Choice(('No Affine Registration', ''), ('ICBM space template - European brains', 'mni'), ('ICBM space template - East Asian brains', 'eastern'), ('Average sized template', 'subj'), ('No regularisation', 'none')),
  'w_samp', String(),
)

def initialization(self):
  # WARNING please inform nuclear imaging team (morphologist team, and maybe others...) before changing this value

  self.setOptional('biasCorrected')

  self.spmJobName = 'newSegment'
  self.MRI_Mni_tpmSeg = self.signature['MRI_Mni_tpmSeg'].findValue({})
  seg.initializeUnifiedSegmentationParameters_usingSPM8DefaultValues(self)
  generateInNativeSpace = """[1 0]"""
  NOgeneration = """[0 0]"""
  Unmodulated = """[1 0]"""
  self.grey_native_space = generateInNativeSpace
  self.grey_warped = Unmodulated
  self.white_native_space = generateInNativeSpace
  self.white_warped = NOgeneration
  self.csf_native_space = generateInNativeSpace
  self.csf_warped = NOgeneration
  self.bone_native_space = NOgeneration
  self.bone_warped = NOgeneration
  self.softTissue_native_space = NOgeneration
  self.softTissue_warped = NOgeneration
  self.airAndBackground_native_space = NOgeneration
  self.airAndBackground_warped = NOgeneration

  self.addLink( 'analysis', 'MRI_Nat', self.updateAnalysis )
  self.addLink('grey_native', ( 'MRI_Nat', 'analysis' ), self.update_grey_Nat)

  self.addLink('grey_dartel_imported', 'grey_native')
  self.addLink('grey_mni_unmodulated', 'grey_native')
  self.addLink('grey_mni_modulated', 'grey_native')
  self.addLink('white_native', 'grey_native')
  self.addLink('white_dartel_imported', 'grey_native')
  self.addLink('white_mni_unmodulated', 'grey_native')
  self.addLink('white_mni_modulated', 'grey_native')
  self.addLink('csf_native', 'grey_native')
  self.addLink('csf_dartel_imported', 'grey_native')
  self.addLink('csf_mni_unmodulated', 'grey_native')
  self.addLink('csf_mni_modulated', 'grey_native')
  self.addLink('bone_native', 'grey_native')
  self.addLink('bone_dartel_imported', 'grey_native')
  self.addLink('bone_mni_unmodulated', 'grey_native')
  self.addLink('bone_mni_modulated', 'grey_native')
  self.addLink('softTissue_native', 'grey_native')
  self.addLink('softTissue_dartel_imported', 'grey_native')
  self.addLink('softTissue_mni_unmodulated', 'grey_native')
  self.addLink('softTissue_mni_modulated', 'grey_native')
  self.addLink('biasCorrected', 'grey_native')
  self.addLink('deFld', 'grey_native')
  self.addLink('deFld_segMat', 'grey_native')
  self.addLink('invDeFld', 'grey_native')

def updateAnalysis( self, proc ):
  if self.MRI_Nat is not None:
    if self.analysis is not None:
      return self.analysis
    else:
      d = {'_database':self.MRI_Nat.hierarchyAttributes()['_database']}
      d['analysis'] = 'SpmNewSegmentation'
      return self.signature['analysis'].findValue( d )

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
  return self.analysis.hierarchyAttributes().get('analysis')

def getDatabase(self):
  return self.analysis.hierarchyAttributes().get('_database')

def execution(self, context):
  print("\n start ", name, "\n")

  #momoTODO : c vraiment pas terrible de passer tous ces paramètres... faire de l'héritage de signature entre process?
  context.runProcess('segment_SPMNewSeg_noLinks',
                     MRI_Nat=self.MRI_Nat, MRI_Mni_tpmSeg=self.MRI_Mni_tpmSeg,
                     spmJobName=self.spmJobName,
                     c_biasreg=self.c_biasreg, c_biasfwhm=self.c_biasfwhm,
                     c_write=self.c_write, biasCorrected=self.biasCorrected,
                     grey_ngaus=self.grey_ngaus,
                     grey_native_space=self.grey_native_space,
                     grey_native=self.grey_native,
                     grey_dartel_imported=self.grey_dartel_imported,
                     grey_warped=self.grey_warped,
                     grey_mni_unmodulated=self.grey_mni_unmodulated,
                     grey_mni_modulated=self.grey_mni_modulated,
                     write_field=self.write_field, deFld=self.deFld,
                     invDeFld=self.invDeFld, deFld_segMat=self.deFld_segMat,
                     white_ngaus=self.white_ngaus,
                     white_native_space=self.white_native_space,
                     white_native=self.white_native,
                     white_dartel_imported=self.white_dartel_imported,
                     white_warped=self.white_warped,
                     white_mni_unmodulated=self.white_mni_unmodulated,
                     white_mni_modulated=self.white_mni_modulated,
                     csf_ngaus=self.csf_ngaus,
                     csf_native_space=self.csf_native_space,
                     csf_native=self.csf_native,
                     csf_dartel_imported=self.csf_dartel_imported,
                     csf_warped=self.csf_warped,
                     csf_mni_unmodulated=self.csf_mni_unmodulated,
                     csf_mni_modulated=self.csf_mni_modulated,
                     bone_ngaus=self.bone_ngaus,
                     bone_native_space=self.bone_native_space,
                     bone_native=self.bone_native,
                     bone_dartel_imported=self.bone_dartel_imported,
                     bone_warped=self.bone_warped,
                     bone_mni_unmodulated=self.bone_mni_unmodulated,
                     bone_mni_modulated=self.bone_mni_modulated,
                     softTissue_ngaus=self.softTissue_ngaus,
                     softTissue_native_space=self.softTissue_native_space,
                     softTissue_native=self.softTissue_native,
                     softTissue_dartel_imported=self.softTissue_dartel_imported,
                     softTissue_warped=self.softTissue_warped,
                     softTissue_mni_unmodulated=self.softTissue_mni_unmodulated,
                     softTissue_mni_modulated=self.softTissue_mni_modulated,
                     airAndBackground_ngaus=self.airAndBackground_ngaus,
                     airAndBackground_native_space=self.airAndBackground_native_space,
                     airAndBackground_warped=self.airAndBackground_warped,
                     w_mrf=self.w_mrf, w_reg=self.w_reg,
                     w_affreg=self.w_affreg, w_samp=self.w_samp)

  print("\n stop ", name, "\n")
