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

name = 'segment/normalize (using SPM segmentation)'
userLevel = 0

def validation():
  return spm.validation(configuration)

# inputs/outputs definition
signature = Signature(
  'MRI_Nat', ReadDiskItem('T1 MRI Nat reseted', 'NIFTI-1 image'),
  'analysis', WriteDiskItem('Analysis Dir', 'Directory'), # ce type ne dépend pas du sujet on peut donc donner une valeur par défaut à l'analyse. Inconvénient : cela créé un répertoire analysis à la racine
  'MRI_Mni_tpmSeg', ReadDiskItem('grey probability map', 'NIFTI-1 image'),
  'spmJobName', String(),
  
  'GM', Choice(('None', """[0 0 0]"""), ('Native Space', """[0 0 1]"""), ('Unmodulated Normalised', """[0 1 0]"""), ('Modulated Normalised', """[1 0 0]""")
              , ('Native + Unmodulated Normalised', """[0 1 1]"""), ('Native + Modulated Normalised', """[1 0 1]"""), ('Native + Modulated + Unmodulated', """[1 1 1]""")
              , ('Modulated + Unmodulated Normalised', """[1 1 0]""")),
  'grey_nat', WriteDiskItem('T1 MRI Nat GreyProba', 'NIFTI-1 image'),
  'grey_Mni', WriteDiskItem('T1 MRI Mni GreyProba', 'NIFTI-1 image'),

  'WM', Choice(('None', """[0 0 0]"""), ('Native Space', """[0 0 1]"""), ('Unmodulated Normalised', """[0 1 0]"""), ('Modulated Normalised', """[1 0 0]""")
              , ('Native + Unmodulated Normalised', """[0 1 1]"""), ('Native + Modulated Normalised', """[1 0 1]"""), ('Native + Modulated + Unmodulated', """[1 1 1]""")
              , ('Modulated + Unmodulated Normalised', """[1 1 0]""")),
  'white_Nat', WriteDiskItem('T1 MRI Nat WhiteProba', 'NIFTI-1 image'),

  'CSF', Choice(('None', """[0 0 0]"""), ('Native Space', """[0 0 1]"""), ('Unmodulated Normalised', """[0 1 0]"""), ('Modulated Normalised', """[1 0 0]""")
              , ('Native + Unmodulated Normalised', """[0 1 1]"""), ('Native + Modulated Normalised', """[1 0 1]"""), ('Native + Modulated + Unmodulated', """[1 1 1]""")
              , ('Modulated + Unmodulated Normalised', """[1 1 0]""")),
  'csf_Nat', WriteDiskItem('T1 MRI Nat CSFProba', 'NIFTI-1 image'),

  'biasreg', Choice(('no regularisation (0)', '0'), ('extremely light regularisation (0.00001)', '0.00001'), ('very light regularisation (0.0001) *SPM default*', '0.0001')
                    , ('light regularisation (0.001)', '0.001'), ('medium regularisation (0.01)', '0.01'), ('heavy regularisation (0.1)', '0.1'), ('very heavy regularisation (1)', '1'), ('extremely heavy regularisation (10)', '10'),),
  'biascor', Choice(('save bias corrected', '1'), ("don't save bias corrected", '0')),
  'biasCorrected', WriteDiskItem('T1 MRI Bias Corrected', 'NIFTI-1 image'),
  'cleanup', Choice(('Dont do cleanup', '0'), ('Light Clean', '1'), ('Thorough Clean', '2')),
  'ngaus', String(),
  'regtype', Choice(('No Affine Registration', """''"""), ("ICBM space template - European brains", """'mni'"""), ("ICBM space template - East Asian brains", """'eastern'"""), ("Average sized template", """'subj'"""), ("No regularisation", """'none'""")),
  'warpreg', String(),
  'warpco', String(),
  'biasfwhm', Choice(('30mm cutoff', '30'), ('40mm cutoff', '40'), ('50mm cutoff', '50'), ('60mm cutoff', '60'), ('70mm cutoff', '70'), ('80mm cutoff', '80'), ('90mm cutoff', '90'), ('100mm cutoff', '100'), ('110mm cutoff', '110'), ('120mm cutoff', '120'), ('130mm cutoff', '130'), ('140mm cutoff', '140'), ('150mm cutoff', '150'), ('No correction', 'Inf')),
  'samp', String(),
  'msk', String(),
  
  'snMat', WriteDiskItem('Mat T1 MRI from Native to Mni', 'Matlab file'),
  'snInvMat', WriteDiskItem('Mat T1 MRI from Mni to Native', 'Matlab file'),

)

def initialization(self):

  self.setOptional('grey_nat', 'biasCorrected')
  
  self.spmJobName = 'segment'
  self.analysis = self.signature["analysis"].findValue({'analysis':'SpmSegmentation'})
  self.MRI_Mni_tpmSeg = self.signature["MRI_Mni_tpmSeg"].findValue({})
  seg.initializeSegmentationParameters_usingSPM8DefaultValuesForPET(self)  
  nativeSpace= """[0 0 1]"""
  NativeAndUnmodulatedNormalised= """[0 1 1]"""
  self.GM = NativeAndUnmodulatedNormalised
  self.WM = nativeSpace
  self.CSF = nativeSpace
  dontSave = """0"""
  self.biascor = dontSave
    
  self.addLink("grey_nat", "MRI_Nat", self.update_grey_Nat)
  self.addLink("grey_nat", "analysis", self.update_grey_Nat)
  
  self.addLink('grey_Mni', 'grey_nat')
  self.addLink("white_Nat", "grey_nat")
  self.addLink("csf_Nat", "grey_nat")        
  self.addLink("biasCorrected", "grey_nat")  
  self.addLink('snMat', "grey_nat")
  self.addLink('snInvMat', "grey_nat")    
  
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
    
  context.runProcess('segment_SPM_noLinks', MRI_Nat=self.MRI_Nat, MRI_Mni_tpmSeg=self.MRI_Mni_tpmSeg, spmJobName=self.spmJobName
                   , GM=self.GM, grey_Nat=self.grey_nat, grey_Mni=self.grey_Mni
                   , WM=self.WM, white_Nat=self.white_Nat, CSF=self.CSF, csf_Nat=self.csf_Nat, biasreg=self.biasreg, biascor=self.biascor
                   , biasCorrected=self.biasCorrected, cleanup=self.cleanup, ngaus=self.ngaus, regtype=self.regtype, warpreg=self.warpreg
                   , warpco=self.warpco, biasfwhm=self.biasfwhm, samp=self.samp, msk=self.msk
                   , snMat=self.snMat, snInvMat=self.snInvMat)  
  print "\n stop ", name, "\n"

