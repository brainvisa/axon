# -*- coding: utf-8 -*-
#
# Functions called by processes allowing SPM Statistical models creation
# (initialization, batch creation,...)
#

#
# SPM8 default parameters for paired t-test analysis
#
from __future__ import print_function
from __future__ import absolute_import
from six.moves import range


def initialize_pairedTTest_SPM8_default_parameters(process):
    process.grandMeanScaling = 'No'
    process.ancova = 'No'
    process.ThresholdMasking = 'None'
    process.threshold_masking_value = ''
    process.implicitMask = 'Yes'
    process.explicitMask = ''
    process.GlobalCalculation = 'Omit'
    process.globalNormalisation_grandMeanScaledValue = """1"""
    process.globalNormalisation = 'None'


#
# Write paired t-test batch file using SPM8
#
def write_pairedTTest_matFile(context, pairsPathList, matfileDI, mat_file                                  , outDir, gmsca="""0""", ancova="""0"""
                              , tm="""tm_none = 1""", im="""1""", em="""{''}"""
                              , g_omit="""1""", gmsca_no="""1""", gmsca_yes_gmscv="""0""", glonorm="""1"""
                              , cov="""struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {})"""
                              ):

    mat_file.write("""matlabbatch{1}.spm.stats.factorial_design.dir = {'%s/'};

    """ % (outDir) )

    if len(pairsPathList) == 1:
        scans1 = convertPathList(pairsPathList[0])
        mat_file.write("""matlabbatch{1}.spm.stats.factorial_design.des.pt.pair.scans = {%s
                                                                 };
        """ % ( scans1 ) )

    else:
        for ind in range(len(pairsPathList)):
            scans = convertPathList(pairsPathList[ind])
            mat_file.write("""matlabbatch{1}.spm.stats.factorial_design.des.pt.pair(%d).scans = {%s
                                                                 };
        """ % (ind + 1, scans) )

    mat_file.write("""matlabbatch{1}.spm.stats.factorial_design.des.pt.gmsca = %s;
            matlabbatch{1}.spm.stats.factorial_design.des.pt.ancova = %s;
            """ % (gmsca, ancova))

    writeCovariables_inMatFile(mat_file, cov)
    writeMasking_inMatfile(mat_file, tm, im, em)
    writeGlobalCalculation_inMatfile(mat_file, g_omit)
    writeGlobalNormalization_inMatfile(
        context, mat_file, gmsca_no, gmsca_yes_gmscv, glonorm)
    mat_file.close()

    return mat_file.name


#
# Write covariables of paired t test
#
def writeCovariables_inMatFile(mat_file, cov):
    if (cov is None):
        cov = """struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {})"""
        mat_file.write("""matlabbatch{1}.spm.stats.factorial_design.cov = %s;
        """ % (cov))
    elif (len(cov) == 1):
        mat_file.write("""matlabbatch{1}.spm.stats.factorial_design.cov.c = [%s];
        matlabbatch{1}.spm.stats.factorial_design.cov.cname = '%s';
        matlabbatch{1}.spm.stats.factorial_design.cov.iCFI = %s;
        matlabbatch{1}.spm.stats.factorial_design.cov.iCC = %s;
        """ % (cov[0][0], cov[0][1], cov[0][2], cov[0][3]))
    elif (len(cov) > 1):
        for i in range(len(cov)):
            mat_file.write("""matlabbatch{1}.spm.stats.factorial_design.cov(%s).c = [%s];
            matlabbatch{1}.spm.stats.factorial_design.cov(%s).cname = '%s';
            matlabbatch{1}.spm.stats.factorial_design.cov(%s).iCFI = %s;
            matlabbatch{1}.spm.stats.factorial_design.cov(%s).iCC = %s;
            """ % (i + 1, cov[i][0], i + 1, cov[i][1], i + 1, cov[i][2], i + 1, cov[i][3]))


def writeMasking_inMatfile(mat_file, tm_none, im, em):
    return mat_file.write(
        """matlabbatch{1}.spm.stats.factorial_design.masking.tm.%s;
                             matlabbatch{1}.spm.stats.factorial_design.masking.im = %s;
                             matlabbatch{1}.spm.stats.factorial_design.masking.em = %s;
                          """ % (tm_none, im, em))


def writeGlobalCalculation_inMatfile(mat_file, g_omit):
    return mat_file.write("""matlabbatch{1}.spm.stats.factorial_design.globalc.g_omit = %s;
                          """ % (g_omit))


def writeGlobalNormalization_inMatfile(context, mat_file, gmsca_no, gmsca_yes_gmscv, glonorm):
    if (gmsca_no == """1"""):
        if (glonorm != """1"""):
            msg = 'no global normalization (gmsca_no == 1) so Normalization must be None (but is' + \
                glonorm + ')'
            print(msg)
            context.error(msg)
            raise Exception(msg)
        mat_file.write("""matlabbatch{1}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;
                    matlabbatch{1}.spm.stats.factorial_design.globalm.glonorm = %s;
                    """ % (glonorm))
    else:

        mat_file.write("""matlabbatch{1}.spm.stats.factorial_design.globalm.gmsca.gmsca_yes.gmscv = %s;
        matlabbatch{1}.spm.stats.factorial_design.globalm.glonorm = %s;
        """ % (gmsca_yes_gmscv, glonorm))


def convertPathList(subjectsPathList):
    subjectsPathListForSPM = ["\n\t\t\t\t\t\t\t\t" + "'" + str(
        group1Path) + ",1'" for group1Path in subjectsPathList]
    scans1 = ' '.join(subjectsPathListForSPM)
    return scans1

#
# SPM8 default parameters for contrast manager (T-Test only)
#


def initialize_SPM8_default_contrastParameters(process):
    process.contrast_name = """'contrast'"""
    process.contrast_vector = """'1'"""
    process.session_replication = """'none'"""
    process.delete = '0'


#
# Write SPM8 contrast batch
#
def write_contrast_MatFile(context, spmmat, spmJobFile, convname, convec, sessrep, delete):
    mat_file = open(spmJobFile, 'w')
    # spm('defaults', 'PET'); # is necessary for spm8_standalone
    # mat_file.write("""spm('defaults', 'PET');
    #    spm_jobman('initcfg');
    mat_file.write("""matlabbatch{1}.spm.stats.con.spmmat = {'%s'};
        matlabbatch{1}.spm.stats.con.consess{1}.tcon.name = %s;
        matlabbatch{1}.spm.stats.con.consess{1}.tcon.convec = %s;
        matlabbatch{1}.spm.stats.con.consess{1}.tcon.sessrep = %s;
        matlabbatch{1}.spm.stats.con.delete = %s;
        """ % (spmmat, convname, convec, sessrep, delete,
               ))
    mat_file.close()
    return mat_file.name
