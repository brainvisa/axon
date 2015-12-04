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
#
#
# Createad by Moana Reynal (05/2013)
# Updated by Malo Gaubert (05/2014)
# 
#

from brainvisa.processes import *
from brainvisa.tools.spm_segmentation import writeVBM8MatFile, initializeVBMParameters_usingVBM8DefaultValues
from brainvisa.tools.spm_utils import movePathToDiskItem, movePath
import brainvisa.tools.spm_run as spm

configuration = Application().configuration
spm8Path = spm.getSpm8Path(configuration)

# you should use this process because :
# - all types are generic : so can be used with any new hierarchy
# - no links between parameters : so can be easily used in pipelines (no need to remove links when using it)
name = 'segment/normalize (using VBM8 toolbox - no links between parameters)' # no links between parameters so can be easily used in pipelines
userLevel = 2


def validation():
  return spm.validation(configuration)

# inputs/outputs definition
signature = Signature(
  'Volume_to_segment', ReadDiskItem('4D Volume', 'Aims readable volume formats'),#Input volume
   
  #Estimation Options
  'MRI_Mni_tpmSeg', ReadDiskItem('4D Volume', 'Aims readable volume formats'),
  'gaussian_classes', String(),
  'bias_reg', Choice(('no regularisation (0)', '0'), ('extremely light regularisation (0.00001)', '0.00001'), ('very light regularisation (0.0001) *SPM default*', '0.0001')
                    , ('light regularisation (0.001)', '0.001'), ('medium regularisation (0.01)', '0.01'), ('heavy regularisation (0.1)', '0.1'), ('very heavy regularisation (1)', '1'), ('extremely heavy regularisation (10)', '10'),),
  'bias_fwhm', Choice(('30mm cutoff', '30'), ('40mm cutoff', '40'), ('50mm cutoff', '50'), ('60mm cutoff', '60'), ('70mm cutoff', '70'), ('80mm cutoff', '80'), ('90mm cutoff', '90'), ('100mm cutoff', '100'), ('110mm cutoff', '110'), ('120mm cutoff', '120'), ('130mm cutoff', '130'), ('140mm cutoff', '140'), ('150mm cutoff', '150'), ('No correction', 'Inf')),
  'affine_reg', Choice(('No Affine Registration', """''"""), ("ICBM space template - European brains", """'mni'"""), ("ICBM space template - East Asian brains", """eastern"""), ("Average sized template", """subj"""), ("No regularisation", """none""")),
  'warping_reg', String(),
  'samp', String(),
  
  #Extended Options
  'norm', Choice(('Low-dimensional: SPM default', """Low"""), ('High-dimensional: Dartel', """Dartel""")),
  'DARTEL_template', WriteDiskItem('Dartel Template', 'Aims readable volume formats'),
  'sanlm', Choice(('No denoising', '0'), ('Denoising', '1'), ('Denoising (multi-threaded)', '2')),
  'mrf', String(),
  'clean_up', Choice(('Dont do cleanup', '0'), ('Light Clean', '1'), ('Thorough Clean', '2')),
  'print_results', Choice(('No',"""0"""), ('Yes', """1""")),
  
  # Writing Options
    #Grey Matter
  'grey_native',            Choice(('none', '0'), ('yes', '1')),
  'grey_native_fn',         WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'grey_normalized',        Choice(('none', '0'), ('yes', '1')),
  'grey_normalized_fn',     WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'grey_modulated',         Choice(('none', '0'), ('affiche + non-linear (SPM8 default)', '1'), ('non-linear only', '2')),
  'grey_modulated_fn',      WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'grey_dartel',            Choice(('none', '0'), ('rigid (SPM8 default)', '1'), ('affine', '2')),
  'grey_dartel_fn',         WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  
    #White Matter
  'white_native',           Choice(('none', '0'), ('yes', '1')),
  'white_native_fn',        WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'white_normalized',       Choice(('none', '0'), ('yes', '1')),
  'white_normalized_fn',    WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'white_modulated',        Choice(('none', '0'), ('affiche + non-linear (SPM8 default)', '1'), ('non-linear only', '2')),
  'white_modulated_fn',     WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'white_dartel',           Choice(('none', '0'), ('rigid (SPM8 default)', '1'), ('affine', '2')),
  'white_dartel_fn',        WriteDiskItem('4D Volume', 'Aims readable volume formats'),

    #CSF
  'csf_native',             Choice(('none', '0'), ('yes', '1')),
  'csf_native_fn',          WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'csf_normalized',         Choice(('none', '0'), ('yes', '1')),
  'csf_normalized_fn',      WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'csf_modulated',          Choice(('none', '0'), ('affiche + non-linear (SPM8 default)', '1'), ('non-linear only', '2')),
  'csf_modulated_fn',       WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'csf_dartel',             Choice(('none', '0'), ('rigid (SPM8 default)', '1'), ('affine', '2')),
  'csf_dartel_fn',          WriteDiskItem('4D Volume', 'Aims readable volume formats'),

  #Bias Correction
  'bias_native',            Choice(('none', '0'), ('yes', '1')),
  'bias_native_fn',         WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'bias_normalized',        Choice(('none', '0'), ('yes', '1')),
  'bias_normalized_fn',     WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'bias_affine',            Choice(('none', '0'), ('yes', '1')),
  'bias_affine_fn',         WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  
  #PVE label image
  'pve_native',             Choice(('none', '0'), ('yes', '1')),
  'pve_native_fn',          WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'pve_normalized',         Choice(('none', '0'), ('yes', '1')),
  'pve_normalized_fn',      WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'pve_dartel',             Choice(('none', '0'), ('rigid (SPM8 default)', '1'), ('affine', '2')),
  'pve_dartel_fn',          WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  
  #Jacobian Determinant
  'jacobian_normalized',    Choice(('none', '0'), ('normalized', '1')),
  'jacobian_normalized_fn', WriteDiskItem('4D Volume', 'Aims readable volume formats'),

  #Deformation Fields
  'deformation_fields',     Choice(('None', '[0 0]'),('Image->Template (forward)', '[1 0]'),('Template->Image (inverse)', '[0 1]'),('inverse + forward', '[1 1]')),
  'forward_DF_fn',          WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'inverse_DF_fn',          WriteDiskItem('4D Volume', 'Aims readable volume formats'),
  'DF_transformation_matrix', WriteDiskItem('Matlab SPM file', 'Matlab file'),
  
  #pfile.txt: GM, WM and CSF volume 
  'GM_WM_CSF_volumes_txt',  WriteDiskItem('CSV file', 'CSV file'),

  #Batch
  'batch_location', WriteDiskItem( 'Any Type', 'Matlab script' )
  )

def initialization(self):  
  self.setOptional( 'DARTEL_template', 'batch_location' )
  
  self.setOptional( 'grey_native_fn', 'grey_normalized_fn', 'grey_modulated_fn', 'grey_dartel_fn' )
  self.setOptional( 'white_native_fn', 'white_normalized_fn', 'white_modulated_fn', 'white_dartel_fn' )
  self.setOptional( 'csf_native_fn', 'csf_normalized_fn', 'csf_modulated_fn', 'csf_dartel_fn' )
  self.setOptional( 'bias_native_fn', 'bias_normalized_fn', 'bias_affine_fn' )
  self.setOptional( 'pve_native_fn', 'pve_normalized_fn', 'pve_dartel_fn' )
  self.setOptional( 'jacobian_normalized_fn', 'forward_DF_fn', 'inverse_DF_fn', 'DF_transformation_matrix', 'GM_WM_CSF_volumes_txt' )
  
  #Options
  self.signature['gaussian_classes'].userLevel = 1
  self.signature['bias_reg'].userLevel = 1
  self.signature['bias_fwhm'].userLevel = 1
  self.signature['affine_reg'].userLevel = 1
  self.signature['warping_reg'].userLevel = 1
  self.signature['samp'].userLevel = 1
  self.signature['norm'].userLevel = 1
  self.signature['DARTEL_template'].userLevel = 1
  self.signature['sanlm'].userLevel = 1
  self.signature['mrf'].userLevel = 1
  self.signature['clean_up'].userLevel = 1
  self.signature['print_results'].userLevel = 1
  
  #Output
  self.signature['bias_native'].userLevel = 1
  self.signature['bias_native_fn'].userLevel = 1
  self.signature['bias_normalized'].userLevel = 1
  self.signature['bias_normalized_fn'].userLevel = 1
  self.signature['bias_affine'].userLevel = 1
  self.signature['bias_affine_fn'].userLevel = 1
  self.signature['pve_native'].userLevel = 1
  self.signature['pve_native_fn'].userLevel = 1
  self.signature['pve_normalized'].userLevel = 1
  self.signature['pve_normalized_fn'].userLevel = 1
  self.signature['pve_dartel'].userLevel = 1
  self.signature['pve_dartel_fn'].userLevel = 1
  
  initializeVBMParameters_usingVBM8DefaultValues( self )

  self.addLink( 'batch_location', 'Volume_to_segment', self.update_batch_location )
  
def update_batch_location( self, proc ):
    if self.Volume_to_segment is not None:
        sourcePath = self.Volume_to_segment.fullPath()
        inDir = sourcePath[:sourcePath.rindex('/')]  
        inFileName = sourcePath[sourcePath.rindex('/') + 1:len(sourcePath)-(len(sourcePath)-sourcePath.rindex('.'))]
        return inDir + '/vbm8_' +  inFileName +'_job.m'
  

def execution(self, context):
    print "\n start ", name, "\n"
 
    if self.batch_location is None:
      spmJobFile = context.temporary( 'Matlab script' ).fullPath()
    else:
      spmJobFile = self.batch_location.fullPath()
     
    if(self.norm == "Dartel"):
      norm="""high.darteltpm = {"""+self.DartelTemplate.fullPath()+"""}"""
    else:
      norm = """low = struct([])"""
 
    matfilePath = writeVBM8MatFile(context, configuration, self.Volume_to_segment.fullPath(), spmJobFile
                                , self.MRI_Mni_tpmSeg, self.gaussian_classes, self.bias_reg, self.bias_fwhm, self.affine_reg, self.warping_reg, self.samp
                                , norm, self.sanlm, self.mrf, self.clean_up, self.print_results
                                , self.grey_native, self.grey_normalized, self.grey_modulated, self.grey_dartel
                                , self.white_native, self.white_normalized, self.white_modulated, self.white_dartel
                                , self.csf_native, self.csf_normalized, self.csf_modulated, self.csf_dartel
                                , self.bias_native, self.bias_normalized, self.bias_affine
                                , self.pve_native, self.pve_normalized, self.pve_dartel
                                , self.jacobian_normalized, self.deformation_fields
                                )    
    spm.run(context, configuration, matfilePath, isMatlabMandatory=True)
    
    self.moveSpmOutFiles()
    
    print "\n stop ", name, "\n"
    

def moveSpmOutFiles( self ):
    subjectName = os.path.basename(self.Volume_to_segment.fullPath()).partition(".")[0]
    ext = os.path.basename(self.Volume_to_segment.fullPath()).partition(".")[2]
    inDir = os.path.dirname(self.Volume_to_segment.fullName())
    #outDir = os.path.dirname(self.grey_native_fn.fullName())
 
    #Move tissues in native space
    grey = inDir + "/p1" + subjectName + ".nii"
    movePathToDiskItem( grey, self.grey_native_fn )
    white = inDir + "/p2" + subjectName + ".nii"
    movePathToDiskItem( white, self.white_native_fn )
    csf = inDir + "/p3" + subjectName + ".nii"
    movePathToDiskItem( csf, self.csf_native_fn )
    
    #Move tissues in normalized space
    grey = inDir + "/wp1" + subjectName + ".nii"
    movePathToDiskItem( grey, self.grey_normalized_fn )
    white = inDir + "/wp2" + subjectName + ".nii"
    movePathToDiskItem( white, self.white_normalized_fn )
    csf = inDir + "/wp3" + subjectName + ".nii"
    movePathToDiskItem( csf, self.csf_normalized_fn )
    
    #Move modulated tissues in normalized spaces (affine+non-linear)
    grey = inDir + "/mwp1" + subjectName + ".nii"
    movePathToDiskItem( grey, self.grey_modulated_fn )
    white = inDir + "/mwp2" + subjectName + ".nii"
    movePathToDiskItem( white, self.white_modulated_fn )
    csf = inDir + "/mwp3" + subjectName + ".nii"
    movePathToDiskItem( csf, self.csf_modulated_fn )
    
    #Move tissues for dartel (rigid)
    grey = inDir + "/rwp1" + subjectName + ".nii"
    movePathToDiskItem( grey, self.grey_dartel_fn )
    white = inDir + "/rwp2" + subjectName + ".nii"
    movePathToDiskItem( white, self.white_dartel_fn )
    csf = inDir + "/rwp3" + subjectName + ".nii"
    movePathToDiskItem( csf, self.csf_dartel_fn )
    
    #Move bias corrected file
    native_bias= inDir + "/m" + subjectName + ".nii"
    movePathToDiskItem(native_bias, self.bias_native_fn )
    normalized_bias = inDir + "/wm" + subjectName + ".nii"
    movePathToDiskItem(normalized_bias, self.bias_normalized_fn )
    affine_bias = inDir + "/wm" + subjectName + "_affine.nii"
    movePathToDiskItem(affine_bias, self.bias_affine_fn )
    
    #Move PVE label image
    native_pve= inDir + "/p0" + subjectName + ".nii"
    movePathToDiskItem( native_pve, self.pve_native_fn )
    normalized_pve = inDir + "/wp0" + subjectName + ".nii"
    movePathToDiskItem( normalized_pve, self.pve_normalized_fn )
    dartel_pve = inDir + "/rp0" + subjectName + ".nii"
    movePathToDiskItem( dartel_pve, self.pve_dartel_fn )
    dartel_pve = inDir + "/rp0" + subjectName + "_affine.nii"
    movePathToDiskItem( dartel_pve, self.pve_dartel_fn )
   
    #Move Jacobian Determinant
    jacobian= inDir + "/jy" + subjectName + ".nii"
    movePathToDiskItem( jacobian, self.jacobian_normalized_fn )
    
    #Move deformations fields
    forward_DF = inDir + "/y_" + subjectName + ".nii"
    movePathToDiskItem( forward_DF, self.forward_DF_fn )
    inverse_DF = inDir + "/iy_" + subjectName + ".nii"
    movePathToDiskItem( inverse_DF, self.inverse_DF_fn )
    transfo_DF = inDir + "/" + subjectName + "_seg8.mat"
    movePathToDiskItem( transfo_DF, self.DF_transformation_matrix )
    
    #Move pfile.txt: GM, WM and CSF volume 
    pfile = inDir + "/p_" + subjectName + "_seg8.txt"
    movePathToDiskItem( pfile, self.GM_WM_CSF_volumes_txt )
    

    
