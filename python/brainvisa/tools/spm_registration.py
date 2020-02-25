
from __future__ import absolute_import
from brainvisa.tools.spm_basic_models import *

#------------------------------------------------------------------------------


def ititializeCoregisterParameters_withSPM8DefaultValues(process):
    process.others = []
    process.cost_fun = """'nmi'"""
    process.sep = """[4 2]"""
    process.tol = """[0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001]"""
    process.fwhm = """[7 7]"""
    process.interp = """1"""
    process.wrap = """[0 0 0]"""
    process.mask = """0"""


#
# Initialize SPM Coregister Estimate process parameters with default values from SPM8
# @in: process to initialize
def initializeCoregisterEstimateParameters_withSPM8DefaultValues(process):
    process.others = []
    process.cost_fun = """'nmi'"""
    process.sep = """[4 2]"""
    process.tol = """[0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001]"""
    process.fwhm = """[7 7]"""


#
# Create SPM Coregister Estimate batch job
#
def writeCoregisteredEstimateMatFile(context, sourcePath, refPath, spmJobFile, othersPath, cost_fun, sep, tol, fwhm):

    mat_file = open(spmJobFile, 'w')
    refFilesInScript = """{'""" + refPath + """,1'}"""
    sourceFilesInScript = """{'""" + sourcePath + """,1'}"""
    if(othersPath is None or len(othersPath) == 0):
        othersToWrite = """{''}"""
    else:
        othersToWrite = """{"""
        for otherPath in othersPath:
            othersToWrite += "\n\t'" + otherPath + ",1'"
        othersToWrite += """}"""

    mat_file.write("""matlabbatch{1}.spm.spatial.coreg.estimate.ref = %s;
matlabbatch{1}.spm.spatial.coreg.estimate.source = %s;
matlabbatch{1}.spm.spatial.coreg.estimate.other = %s;
matlabbatch{1}.spm.spatial.coreg.estimate.eoptions.cost_fun = %s;
matlabbatch{1}.spm.spatial.coreg.estimate.eoptions.sep = %s;
matlabbatch{1}.spm.spatial.coreg.estimate.eoptions.tol = %s;
matlabbatch{1}.spm.spatial.coreg.estimate.eoptions.fwhm = %s;
""" % (refFilesInScript, sourceFilesInScript, othersToWrite, cost_fun, sep, tol, fwhm))
    mat_file.close()
    return mat_file.name

#
# Create SPM Estimate&Reslice batch job
#


def writeCoregisteredMatFile(context, sourcePath, refPath, spmJobFile, othersPath, cost_fun, sep, tol, fwhm, interp, wrap, mask, prefix="""'spmCoregister_'"""):

    mat_file = open(spmJobFile, 'w')
    refFilesInScript = """{'""" + refPath + """,1'}"""
    sourceFilesInScript = """{'""" + sourcePath + """,1'}"""
    if(othersPath is None or len(othersPath) == 0):
        othersToWrite = """{''}"""
    else:
        othersToWrite = """{"""
        for otherPath in othersPath:
            othersToWrite += "\n\t'" + otherPath + ",1'"
        othersToWrite += """}"""

    mat_file.write("""matlabbatch{1}.spm.spatial.coreg.estwrite.ref = %s;
matlabbatch{1}.spm.spatial.coreg.estwrite.source = %s;
matlabbatch{1}.spm.spatial.coreg.estwrite.other = %s;
matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.cost_fun = %s;
matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.sep = %s;
matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.tol = %s;
matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.fwhm = %s;
matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.interp = %s;
matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.wrap = %s;
matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.mask = %s;
matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.prefix = %s;
""" % (refFilesInScript, sourceFilesInScript, othersToWrite, cost_fun, sep, tol, fwhm, interp, wrap, mask, prefix))
    mat_file.close()

    return mat_file.name

#------------------------------------------------------------------------------
#
# Initialize normalize with SPM8 parameters
#


def initializeNormalizeParameters_usingSPM8DefaultValues(process):
    process.wtsrc = """''"""
    process.weight = """''"""
    process.smosrc = """8"""
    process.smoref = """0"""
    process.regtype = """'mni'"""

    process.cutoff = """25"""
    process.nits = """16"""
    process.reg = """1"""
    process.preserve = """0"""
    process.bb = """[-78 -112 -50
                                                                        78 76 85]"""
    process.vox = """[2 2 2]"""  # bouding box and voxel size value used for PET modality
    process.interp = """1"""
    process.wrap = """[0 0 0]"""

#
# Create Normalize batch job
#


def writeNormalizeMatFile(context, configuration, src, imgToWrite, spmJobFile, tmp, wtsrc, weight, smosrc, smoref, regtype, cutoff, nits, reg, preserve, bb, vox, interp, wrap, prefix):
    mat_file = open(spmJobFile, 'w')
    mat_file.write("""matlabbatch{1}.spm.spatial.normalise.estwrite.subj.source = {'%s,1'};
matlabbatch{1}.spm.spatial.normalise.estwrite.subj.wtsrc = %s;
matlabbatch{1}.spm.spatial.normalise.estwrite.subj.resample = {'%s,1'};
matlabbatch{1}.spm.spatial.normalise.estwrite.eoptions.template = {'%s,1'};
matlabbatch{1}.spm.spatial.normalise.estwrite.eoptions.weight = %s;
matlabbatch{1}.spm.spatial.normalise.estwrite.eoptions.smosrc = %s;
matlabbatch{1}.spm.spatial.normalise.estwrite.eoptions.smoref = %s;
matlabbatch{1}.spm.spatial.normalise.estwrite.eoptions.regtype = %s;
matlabbatch{1}.spm.spatial.normalise.estwrite.eoptions.cutoff = %s;
matlabbatch{1}.spm.spatial.normalise.estwrite.eoptions.nits = %s;
matlabbatch{1}.spm.spatial.normalise.estwrite.eoptions.reg = %s;
""" % (src
        , wtsrc, imgToWrite, tmp, weight, smosrc, smoref, regtype, cutoff, nits, reg
       ))

    if preserve is not None:
        mat_file.write(
            """matlabbatch{1}.spm.spatial.normalise.estwrite.roptions.preserve = %s;
""" % (preserve))

    if bb is not None:
        mat_file.write(
            """matlabbatch{1}.spm.spatial.normalise.estwrite.roptions.bb = %s;
""" % (bb) )

    mat_file.write("""matlabbatch{1}.spm.spatial.normalise.estwrite.roptions.vox = %s;
matlabbatch{1}.spm.spatial.normalise.estwrite.roptions.interp = %s;
matlabbatch{1}.spm.spatial.normalise.estwrite.roptions.wrap = %s;
matlabbatch{1}.spm.spatial.normalise.estwrite.roptions.prefix = %s;
""" % ( vox, interp, wrap, prefix ))
    mat_file.close()
    return mat_file.name


def writeNormalizeEstimationMatFile(spmJobFile, src, template,
                                    wtsrc, weight, smosrc, smoref, regtype, cutoff, nits, reg):
    matFile = open(spmJobFile, 'w')
    matFile.write("""
matlabbatch{1}.spm.spatial.normalise.est.subj.source = {'%s,1'};
matlabbatch{1}.spm.spatial.normalise.est.subj.wtsrc = '%s';
matlabbatch{1}.spm.spatial.normalise.est.eoptions.template = {'%s,1'};
matlabbatch{1}.spm.spatial.normalise.est.eoptions.weight = '%s';
matlabbatch{1}.spm.spatial.normalise.est.eoptions.smosrc = %s;
matlabbatch{1}.spm.spatial.normalise.est.eoptions.smoref = %s;
matlabbatch{1}.spm.spatial.normalise.est.eoptions.regtype = '%s';
matlabbatch{1}.spm.spatial.normalise.est.eoptions.cutoff = %s;
matlabbatch{1}.spm.spatial.normalise.est.eoptions.nits = %s;
matlabbatch{1}.spm.spatial.normalise.est.eoptions.reg = %s;
""" % (src, wtsrc, template, weight, smosrc, smoref, regtype, cutoff, nits, reg))
    matFile.close()
    return matFile.name


#
# Initialize SPM High Dimensional Warping parameters with default values from SPM8
# @in: process to initialize
def initializeHDWParameters_withSPM8DefaultValues(process):
    process.bias_opts_nits = """8"""
    process.bias_opts_fwhm = """60"""
    process.bias_opts_reg = """1e-06"""
    process.bias_opts_lmreg = """1e-06"""
    process.warp_opts_nits = """8"""
    process.warp_opts_reg = """4"""


#
# Create SPM High-Dimensional Warping job batch
#
def writeHighDimensionalWarpingMatFile(spmJobFile, ref, mov,
                                       bias_opts_nits, bias_opts_fwhm, bias_opts_reg, bias_opts_lmreg, warp_opts_nits, warp_opts_reg):
    matFile = open(spmJobFile, 'w')

    matFile.write("""
matlabbatch{1}.spm.tools.hdw.data.ref = {'%s,1'};
matlabbatch{1}.spm.tools.hdw.data.mov = {'%s,1'};
matlabbatch{1}.spm.tools.hdw.bias_opts.nits = %s;
matlabbatch{1}.spm.tools.hdw.bias_opts.fwhm = %s;
matlabbatch{1}.spm.tools.hdw.bias_opts.reg = %s;
matlabbatch{1}.spm.tools.hdw.bias_opts.lmreg = %s;
matlabbatch{1}.spm.tools.hdw.warp_opts.nits = %s;
matlabbatch{1}.spm.tools.hdw.warp_opts.reg = %s;
""" % ( ref, mov, bias_opts_nits, bias_opts_fwhm, bias_opts_reg, bias_opts_lmreg, warp_opts_nits, warp_opts_reg  ))
    matFile.close()
    return matFile.name


#
# Initialize SPM Deformation tool (with Deformation Field) parameters with default values from SPM8
# @in: process to initialize
def initializeDeformationWithField_withSPM8DefaultValues(process):
    process.save_as = """''"""
    process.interpolation = '1'


#
# Create SPM Deformation using deformation field job batch
#
def writeDeformationWithField(spmJobFile, deformationField, imagesToDeformPath, save_as, output_dir, interpolation):
    matFile = open(spmJobFile, 'w')

    imagesToDeform = """{"""
    for itdPath in imagesToDeformPath:
        imagesToDeform += "\n\t'" + itdPath + ",1'"
    imagesToDeform += """}"""

    matFile.write("""
matlabbatch{1}.spm.util.defs.comp{1}.def = {'%s'};
matlabbatch{1}.spm.util.defs.ofname = %s;
matlabbatch{1}.spm.util.defs.fnames = %s;
matlabbatch{1}.spm.util.defs.savedir.saveusr = {'%s'};
matlabbatch{1}.spm.util.defs.interp = %s;
""" % ( deformationField, save_as, imagesToDeform, output_dir, interpolation ))
    matFile.close()
    return matFile.name


#
# Initialize Normalisation Estimate  parameters with default values from SPM8
# @in: process to initialize
def initializeNormalizeEstimateParameters_usingSPM8DefaultValues(process):
    process.source_image_smoothing = """8"""
    process.template_image_smoothing = """0"""
    process.affine_regularisation = """mni"""
    process.nonlinear_frequency_cutoff = """25"""
    process.nonlinear_iterations = """16"""
    process.nonlinear_regularisation = """1"""


#
# Initialize Normalisation Estimate  parameters with default values from SPM8
# @in: process to initialize
def initializeCoregisterResliceParameters_withSPM8DefaultValues(process):
    process.prefix = """r"""
    process.interp = """4"""
    process.wrap = """[0 0 0]"""
    process.mask = """0"""

#
# Create SPM Coregister reslice batch
#


def writeCoregisteredResliceMatFile(context, image_space, image_to_reslice, spmJobFile                                , prefix="""r"""
                                    , interp="""4"""
                                    , wrap="""[0 0 0]"""
                                    , mask="""0"""
                                    ):

 #   scans = convertPathList(images_to_reslice)
    mat_file = open(spmJobFile, 'w')
    mat_file.write("""
        matlabbatch{1}.spm.spatial.coreg.write.ref = {'%s'};
        matlabbatch{1}.spm.spatial.coreg.write.source = {'%s'};
        matlabbatch{1}.spm.spatial.coreg.write.roptions.interp = %s;
        matlabbatch{1}.spm.spatial.coreg.write.roptions.wrap = %s;
        matlabbatch{1}.spm.spatial.coreg.write.roptions.mask = %s;
        matlabbatch{1}.spm.spatial.coreg.write.roptions.prefix = '%s';
    """ % (image_space, image_to_reslice
           , interp, wrap, mask, prefix)
    )
    mat_file.close()
    return mat_file.name


#
# Initialize Normalisation: write  parameters with default values from SPM8
# @in: process to initialize
def initializeWriteNormalisation_withSPM8DefaultValues(process):
    process.preservation = """0"""
    process.bounding_box = """[-78 -112 -50 \n 78 76 85]"""
    process.voxel_sizes = """[2 2 2]"""
    process.interpolation = """1"""
    process.wrap = """[0 0 0]"""
    process.prefix = """'w'"""


#
# Create SPM Normalize write batch
#
def writeNormalisationWriteBatch(context, parameter_file, images_to_write, spmJobFile                                , preservation="""0"""
                                 , bounding_box="""[-78 -112 -50 \n 78 76 85]"""
                                 , voxel_sizes="""[2 2 2]"""
                                 , interpolation="""1"""
                                 , wrap="""[0 0 0]"""
                                 , prefix="""w"""
                                 ):

#    scans = convertPathList( images_to_write )
    mat_file = open(spmJobFile, 'w')

    mat_file.write("""
matlabbatch{1}.spm.spatial.normalise.write.subj.matname = {'%s'};
matlabbatch{1}.spm.spatial.normalise.write.subj.resample = {'%s'};
matlabbatch{1}.spm.spatial.normalise.write.roptions.preserve = %s;
matlabbatch{1}.spm.spatial.normalise.write.roptions.bb = %s;
matlabbatch{1}.spm.spatial.normalise.write.roptions.vox = %s;
matlabbatch{1}.spm.spatial.normalise.write.roptions.interp = %s;
matlabbatch{1}.spm.spatial.normalise.write.roptions.wrap = %s;
matlabbatch{1}.spm.spatial.normalise.write.roptions.prefix = '%s';
    """ % ( parameter_file, images_to_write, preservation, bounding_box, voxel_sizes, interpolation, wrap, prefix ))
#        """% ( parameter_file, scans, preservation, bounding_box, voxel_sizes, interpolation, wrap, prefix ))

    mat_file.close()
    return mat_file.name
