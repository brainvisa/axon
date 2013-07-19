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

configuration = Application().configuration

name = 'Compare Grey Segmentations'
userLevel = 0

#------------------------------------------------------------------------------

def validation():
  return spm.validation(configuration)

# inputs/outputs definition
signature = Signature(
  'MRI_onDisk', ReadDiskItem( 'Raw T1 MRI', 'Aims readable volume formats' ),
  
  'MRI_Raw', WriteDiskItem( 'Raw T1 MRI', [ 'GIS image', 'NIFTI-1 image', 'gz compressed NIFTI-1 image' ] ),
  'MRI_Nat_reseted', WriteDiskItem('T1 MRI Nat reseted', 'gz compressed NIFTI-1 image'),  
  'MRI_Nat_grey_seg', WriteDiskItem('T1 MRI Nat GreyProba', 'NIFTI-1 image'),#SpmSegmentation   
  'MRI_Nat_grey_newSeg', WriteDiskItem('T1 MRI Nat GreyProba', 'NIFTI-1 image'),#SpmNewSegmentation
  'MRI_Nat_grey_vbmSeg', WriteDiskItem('T1 MRI Nat GreyProba', 'NIFTI-1 image'),#VBMSegmentation

)

#------------------------------------------------------------------------------

def initialization(self):
  self.setOptional('MRI_onDisk', 'MRI_Raw', 'MRI_Nat_reseted', 'MRI_Nat_grey_seg', 'MRI_Nat_grey_newSeg', 'MRI_Nat_grey_vbmSeg')
  
  eNode = SerialExecutionNode(self.name, parameterized=self, optional=1)
  
  add_ImportT1MRI_process(eNode) 
  add_resetInternalImageTransformation_process(eNode) 
  add_SegmentGrey_process(eNode,'SpmSegmentation')  
  add_fdgSegmentNewSeg_process(eNode, 'SpmNewSegmentation')  
  add_SegmentVBM_process(eNode, 'VBMSegmentation')
  add_DisplayGreySegmentations_process(eNode) 
  
  self.setExecutionNode(eNode)

#------------------------------------------------------------------------------

def add_ImportT1MRI_process(eNode):
  eNode.addChild('imp', ProcessExecutionNode('ImportT1MRI', optional=True, selected=False))
  eNode.addDoubleLink('MRI_onDisk', 'imp.input')
  eNode.addDoubleLink('MRI_Raw', 'imp.output')

def add_resetInternalImageTransformation_process(eNode):
  eNode.addChild('res', ProcessExecutionNode('resetInternalImageTransformation', optional=True, selected=True))
  eNode.addDoubleLink('MRI_Raw', 'res.input_image')
  eNode.addDoubleLink('MRI_Nat_reseted', 'res.output_image')  
  
def add_SegmentGrey_process(eNode, analysis):
  eNode.addChild('seg', ProcessExecutionNode('segment_SPM', optional=True, selected=True))
  eNode.addDoubleLink('MRI_Nat_reseted', 'seg.MRI_Nat')
  eNode.addDoubleLink('MRI_Nat_grey_seg', 'seg.grey_nat')
  eNode.seg.biascor = '1' # save bias corrected

def add_fdgSegmentNewSeg_process(eNode, analysis):
  eNode.addChild('newSeg', ProcessExecutionNode('segment_SPMNewSeg', optional=True, selected=True))
  eNode.addDoubleLink('MRI_Nat_reseted', 'newSeg.MRI_Nat')
  eNode.addDoubleLink('MRI_Nat_grey_newSeg', 'newSeg.grey_nat')
  eNode.newSeg.c_write = '[0 1]' # save bias corrected

def add_SegmentVBM_process(eNode, analysis):
  eNode.addChild('vbmSeg', ProcessExecutionNode('segment_VBM', optional=True, selected=True))
  eNode.addDoubleLink('MRI_Nat_reseted', 'vbmSeg.MRI_Nat')
  eNode.addDoubleLink('MRI_Nat_grey_vbmSeg', 'vbmSeg.grey_nat')
  eNode.vbmSeg.saveBias = '1' # save bias corrected

def add_DisplayGreySegmentations_process(eNode):
  eNode.addChild('viw', ProcessExecutionNode('displayTitledGrid', optional=True, selected=True))
  eNode.addDoubleLink('MRI_Nat_grey_seg', 'viw.img4')
  eNode.addDoubleLink('seg.biasCorrected', 'viw.img1')
  eNode.addDoubleLink('MRI_Nat_grey_newSeg', 'viw.img5')
  eNode.addDoubleLink('newSeg.biasCorrected', 'viw.img2')
  eNode.addDoubleLink('MRI_Nat_grey_vbmSeg', 'viw.img6')
  eNode.addDoubleLink('vbmSeg.biasCorrected', 'viw.img3')
  eNode.viw.rowTitles = ["bias corrected", "grey"]
  eNode.viw.colTitles = ["SpmSegmentation", "SpmNewSegmentation", "VBMSegmentation"]
  eNode.viw.windowTitle = 'compare segmentations'
  eNode.viw.rowColors = ['blue', 'blue']  
  
  
#------------------------------------------------------------------------------
