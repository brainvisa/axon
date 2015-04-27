# -*- coding: utf-8 -*-
from brainvisa.tools.spm_run import getSpm8Path 
    
def initializeUnifiedSegmentationParameters_usingSPM8DefaultValues(process):
  # WARNING please inform nuclear imaging team (morphologist team, and maybe others...) before changing this value
  process.write_field = """[1 0]"""
  process.c_biasreg = """0.0001""" 
  process.c_biasfwhm = """60""" 
  process.c_write = """[0 0]"""
  process.grey_ngaus = """2""" 
  process.white_ngaus = """2""" 
  process.csf_ngaus = """2""" 
  process.bone_ngaus = """3""" 
  process.softTissue_ngaus = """4""" 
  process.airAndBackground_ngaus = """2""" 
  process.w_mrf = """0""" 
  process.w_reg = """4""" 
  process.w_affreg = """'mni'""" 
  process.w_samp = """3""" 

#------------------------------------------------------------------------------
# Segmentation with SPM : 
# 1 Unified Segmentation ( in spm8 : newSegment)
# 2 Segmentation : for PET
# 3 VBM Segmentation : VBM toolboxe.

def writeUnifiedSegmentationMatFile(context, configuration, volsPath, spmJobFile
, c_biasreg = """0.0001""", c_biasfwhm = """60""", c_write = """[0 0]"""
, t1_tpm = None, t1_ngaus = """2""", t1_native = """[1 0]""", t1_warped = """[0 0]"""
, t2_tpm = None, t2_ngaus = """2""", t2_native = """[1 0]""", t2_warped = """[0 0]"""
, t3_tpm = None, t3_ngaus = """2""", t3_native = """[1 0]""", t3_warped = """[0 0]"""
, t4_tpm = None, t4_ngaus = """2""", t4_native = """[1 0]""", t4_warped = """[0 0]"""
, t5_tpm = None, t5_ngaus = """2""", t5_native = """[1 0]""", t5_warped = """[0 0]"""
, t6_tpm = None, t6_ngaus = """2""", t6_native = """[0 0]""", t6_warped = """[0 0]"""
, w_mrf = """0""", w_reg = """4""", w_affreg = """'mni'""", w_samp = """3""", w_write = """[0 0]"""
):
  mat_file = open(spmJobFile, 'w')
  spm8Path = getSpm8Path(configuration)
  if(t1_tpm is None):
    t1_tpm = spm8Path+'/toolbox/Seg/TPM.nii'
  if(t2_tpm is None):
    t2_tpm = spm8Path+'/toolbox/Seg/TPM.nii'
  if(t3_tpm is None):
    t3_tpm = spm8Path+'/toolbox/Seg/TPM.nii'
  if(t4_tpm is None):
    t4_tpm = spm8Path+'/toolbox/Seg/TPM.nii'
  if(t5_tpm is None):
    t5_tpm = spm8Path+'/toolbox/Seg/TPM.nii'
  if(t6_tpm is None):
    t6_tpm = spm8Path+'/toolbox/Seg/TPM.nii'
    
  vols = """{'""" + volsPath + """,1'}"""

  mat_file.write("""matlabbatch{1}.spm.tools.preproc8.channel.vols = %s;
matlabbatch{1}.spm.tools.preproc8.channel.biasreg = %s;
matlabbatch{1}.spm.tools.preproc8.channel.biasfwhm = %s;
matlabbatch{1}.spm.tools.preproc8.channel.write = %s;
matlabbatch{1}.spm.tools.preproc8.tissue(1).tpm = {'%s,1'};
matlabbatch{1}.spm.tools.preproc8.tissue(1).ngaus = %s;
matlabbatch{1}.spm.tools.preproc8.tissue(1).native = %s;
matlabbatch{1}.spm.tools.preproc8.tissue(1).warped = %s;
matlabbatch{1}.spm.tools.preproc8.tissue(2).tpm = {'%s,2'};
matlabbatch{1}.spm.tools.preproc8.tissue(2).ngaus = %s;
matlabbatch{1}.spm.tools.preproc8.tissue(2).native = %s;
matlabbatch{1}.spm.tools.preproc8.tissue(2).warped = %s;
matlabbatch{1}.spm.tools.preproc8.tissue(3).tpm = {'%s,3'};
matlabbatch{1}.spm.tools.preproc8.tissue(3).ngaus = %s;
matlabbatch{1}.spm.tools.preproc8.tissue(3).native = %s;
matlabbatch{1}.spm.tools.preproc8.tissue(3).warped = %s;
matlabbatch{1}.spm.tools.preproc8.tissue(4).tpm = {'%s,4'};
matlabbatch{1}.spm.tools.preproc8.tissue(4).ngaus = %s;
matlabbatch{1}.spm.tools.preproc8.tissue(4).native = %s;
matlabbatch{1}.spm.tools.preproc8.tissue(4).warped = %s;
matlabbatch{1}.spm.tools.preproc8.tissue(5).tpm = {'%s,5'};
matlabbatch{1}.spm.tools.preproc8.tissue(5).ngaus = %s;
matlabbatch{1}.spm.tools.preproc8.tissue(5).native = %s;
matlabbatch{1}.spm.tools.preproc8.tissue(5).warped = %s;
matlabbatch{1}.spm.tools.preproc8.tissue(6).tpm = {'%s,6'};
matlabbatch{1}.spm.tools.preproc8.tissue(6).ngaus = %s;
matlabbatch{1}.spm.tools.preproc8.tissue(6).native = %s;
matlabbatch{1}.spm.tools.preproc8.tissue(6).warped = %s;
matlabbatch{1}.spm.tools.preproc8.warp.mrf = %s;
matlabbatch{1}.spm.tools.preproc8.warp.reg = %s;
matlabbatch{1}.spm.tools.preproc8.warp.affreg = %s;
matlabbatch{1}.spm.tools.preproc8.warp.samp = %s;
matlabbatch{1}.spm.tools.preproc8.warp.write = %s;
""" % ( vols
       , c_biasreg, c_biasfwhm, c_write
       , t1_tpm, t1_ngaus, t1_native, t1_warped
       , t2_tpm, t2_ngaus, t2_native, t2_warped
       , t3_tpm, t3_ngaus, t3_native, t3_warped
       , t4_tpm, t4_ngaus, t4_native, t4_warped
       , t5_tpm, t5_ngaus, t5_native, t5_warped
       , t6_tpm, t6_ngaus, t6_native, t6_warped
       , w_mrf, w_reg, w_affreg, w_samp, w_write 
       ))
  mat_file.close()
  return mat_file.name

def initializeSegmentationParameters_usingSPM8DefaultValues(process):
  dontCleanUp = """0"""
  process.cleanup = dontCleanUp
  process.ngaus = """[2
                  2
                  2
                  4]"""
  process.regtype = """'mni'"""
  process.warpreg = """1"""
  process.warpco = """25"""
  process.biasreg = """0.0001"""
  process.biasfwhm = """60"""
  process.samp = """3"""
  process.msk = """{''}"""
      
def writeSegmentationMatFile(context, configuration, sourcePath, spmJobFile
, GM = """[0 1 0]""", WM = """[0 0 0]""", CSF = """[0 0 0]""", biascor = """0""", cleanup = """0"""
, tpm = None
, ngaus = """[2
                                        2
                                        2
                                        4]"""
, regtype = """'mni'""", warpreg = """1""", warpco = """25""", biasreg = """0.0001"""
, biasfwhm = """60""", samp = """3""", msk = """{''}"""
):
  mat_file = open(spmJobFile, 'w')
  spm8Path = getSpm8Path(configuration)
  if(tpm is None):
    tpm = """{
                                        '"""+str(spm8Path)+"""/tpm/grey.nii'
                                        '"""+str(spm8Path)+"""/tpm/white.nii'
                                        '"""+str(spm8Path)+"""/tpm/csf.nii'
            }"""

    
  sourceFilesInScript = """{'""" + str(sourcePath) + """,1'}"""
  mat_file.write("""matlabbatch{1}.spm.spatial.preproc.data = %s;
matlabbatch{1}.spm.spatial.preproc.output.GM = %s;
matlabbatch{1}.spm.spatial.preproc.output.WM = %s;
matlabbatch{1}.spm.spatial.preproc.output.CSF = %s;
matlabbatch{1}.spm.spatial.preproc.output.biascor = %s;
matlabbatch{1}.spm.spatial.preproc.output.cleanup = %s;
matlabbatch{1}.spm.spatial.preproc.opts.tpm = %s;
matlabbatch{1}.spm.spatial.preproc.opts.ngaus = %s;
matlabbatch{1}.spm.spatial.preproc.opts.regtype = %s;
matlabbatch{1}.spm.spatial.preproc.opts.warpreg = %s;
matlabbatch{1}.spm.spatial.preproc.opts.warpco = %s;
matlabbatch{1}.spm.spatial.preproc.opts.biasreg = %s;
matlabbatch{1}.spm.spatial.preproc.opts.biasfwhm = %s;
matlabbatch{1}.spm.spatial.preproc.opts.samp = %s;
matlabbatch{1}.spm.spatial.preproc.opts.msk = %s;
""" % (sourceFilesInScript
    , GM, WM, CSF, biascor, cleanup
    , tpm, ngaus, regtype, warpreg, warpco, biasreg, biasfwhm, samp, msk
       ))
  mat_file.close()
  return mat_file.name

def initializeVBMSegmentationParameters_usingSPM8DefaultValues(process):
  process.ngaus = """[2 2 2 3 4 2]"""
  process.biasreg = """0.0001"""
  process.biasfwhm = """60"""
  process.affreg = """'mni'"""
  process.warpreg = """4"""
  process.samp = """3"""
  process.norm = """Low"""
  process.sanlm = """2"""
  process.mrf = """0.15"""
  process.cleanup = """1"""
  process.pprint = """1"""
  process.generateJacobianDeterminant = """0"""

def writeVBMSegmentationMatFile(context, configuration, sourcePath, spmJobFile
, tpm, ngaus = """[2 2 2 3 4 2]""", biasreg = """0.0001""", biasfwhm = """60""", affreg = """'mni'""", warpreg = """4""", samp = """3"""
, norm = """low = struct([])""", sanlm = """2""", mrf = """0.15""", cleanup = """1""", pprint = """1"""
, native = """1""", warped = """0""", modulated = """0""", dartel = """0"""
, wm_native = """1""", wm_warped = """0""", wm_modulated = """0""", wm_dartel = """0"""
, csf_native = """1""", csf_warped = """0""", csf_modulated = """0""", csf_dartel = """0"""
, saveBias = """0""",generateJacobianDeterminant="""0"""
):
  mat_file = open(spmJobFile, 'w')
  mat_file.write("""matlabbatch{1}.spm.tools.vbm8.estwrite.data = {'%s,1'}
matlabbatch{1}.spm.tools.vbm8.estwrite.opts.tpm = {'%s'};
matlabbatch{1}.spm.tools.vbm8.estwrite.opts.ngaus = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.opts.biasreg = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.opts.biasfwhm = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.opts.affreg = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.opts.warpreg = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.opts.samp = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.extopts.dartelwarp.norm%s;
matlabbatch{1}.spm.tools.vbm8.estwrite.extopts.sanlm = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.extopts.mrf = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.extopts.cleanup = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.extopts.print = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.GM.native = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.GM.warped = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.GM.modulated = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.GM.dartel = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.WM.native = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.WM.warped = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.WM.modulated = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.WM.dartel = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.CSF.native = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.CSF.warped = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.CSF.modulated = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.CSF.dartel = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.bias.native = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.bias.warped = 0;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.bias.affine = 0;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.label.native = 0;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.label.warped = 0;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.label.dartel = 0;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.jacobian.warped = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.warps = [1 1];

""" % (sourcePath
, tpm, ngaus, biasreg, biasfwhm, affreg, warpreg, samp
, norm, sanlm, mrf, cleanup, pprint
, native, warped, modulated, dartel
, wm_native, wm_warped, wm_modulated, wm_dartel
, csf_native, csf_warped, csf_modulated, csf_dartel
, saveBias, generateJacobianDeterminant
       ))
  mat_file.close()
  return mat_file.name
        
# e.g. writeRealignMatFile(None, False, '/home_local/mreynal/MEMENTO_RAW_Subjects/Toulouse/005_0036_GUJE_M00', '/0050036GUJEM00-20120224-PT-MEMENTO_AC-CHU_Toulouse', None, open(spmJobFile, 'w'))

#------------------------------------------------------------------------------
def writeVBM8MatFile(context, configuration, sourcePath, spmJobFile
, tpm, ngaus = """[2 2 2 3 4 2]""", biasreg = """0.0001""", biasfwhm = """60""", affreg = """'mni'""", warpreg = """4""", samp = """3"""
, norm = """low = struct([])""", sanlm = """2""", mrf = """0.15""", cleanup = """1""", pprint = """1"""
, gm_native = """0""", gm_normalized = """0""", gm_modulated = """2""", gm_dartel = """0"""
, wm_native = """0""", wm_normalized = """0""", wm_modulated = """2""", wm_dartel = """0"""
, csf_native = """0""", csf_normalized = """0""", csf_modulated = """0""", csf_dartel = """0"""
, bias_native = """0""", bias_normalized = """1""", bias_affine = """0"""
, pve_native = """0""", pve_normalized = """0""", pve_dartel = """0"""
, generateJacobianDeterminant="""0""", deformation_fields = """[0 0]"""
):
  mat_file = open(spmJobFile, 'w')
  mat_file.write("""matlabbatch{1}.spm.tools.vbm8.estwrite.data = {'%s,1'};
matlabbatch{1}.spm.tools.vbm8.estwrite.opts.tpm = {'%s'};
matlabbatch{1}.spm.tools.vbm8.estwrite.opts.ngaus = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.opts.biasreg = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.opts.biasfwhm = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.opts.affreg = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.opts.warpreg = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.opts.samp = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.extopts.dartelwarp.norm%s;
matlabbatch{1}.spm.tools.vbm8.estwrite.extopts.sanlm = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.extopts.mrf = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.extopts.cleanup = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.extopts.print = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.GM.native = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.GM.warped = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.GM.modulated = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.GM.dartel = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.WM.native = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.WM.warped = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.WM.modulated = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.WM.dartel = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.CSF.native = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.CSF.warped = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.CSF.modulated = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.CSF.dartel = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.bias.native = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.bias.warped = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.bias.affine = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.label.native = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.label.warped = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.label.dartel = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.jacobian.warped = %s;
matlabbatch{1}.spm.tools.vbm8.estwrite.output.warps = %s;

""" % (sourcePath
, tpm, ngaus, biasreg, biasfwhm, affreg, warpreg, samp
, norm, sanlm, mrf, cleanup, pprint
, gm_native, gm_normalized, gm_modulated, gm_dartel
, wm_native, wm_normalized, wm_modulated, wm_dartel
, csf_native, csf_normalized, csf_modulated, csf_dartel
, bias_native, bias_normalized, bias_affine
, pve_native, pve_normalized, pve_dartel
, generateJacobianDeterminant, deformation_fields

       ))
  mat_file.close()
  return mat_file.name

#
# Initialize VBM parameters (estimation optins & extended options) with VBM8 Default values
#
def initializeVBMParameters_usingVBM8DefaultValues(process):
  process.gaussian_classes = """[2 2 2 3 4 2]"""
  process.bias_reg = """0.0001"""
  process.bias_fwhm = """60"""
  process.affine_reg = """'mni'"""
  process.warping_reg = """4"""
  process.samp = """3"""
  process.norm = """Low"""
  process.sanlm = """2"""
  process.mrf = """0.15"""
  process.clean_up = """1"""
  process.print_results = """1"""
 
