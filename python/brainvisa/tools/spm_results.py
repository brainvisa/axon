# -*- coding: utf-8 -*-
from tempfile import mkstemp
import os
from soma.path import locate_file


def createBrainMIPWithGridTextFiles(context,
                                    spm8_standalone_path,
                                    spm8_standalone_command,
                                    spm8_standalone_mcr_path,
                                    grid_file_path,
                                    mask_file_path):

    temp_mat_file_descriptor, temp_mat_file_path = mkstemp(suffix=".m")
    temp_mat_file = os.fdopen(temp_mat_file_descriptor, "w")
    temp_mat_file.write("""
spm_get_defaults('cmdline', true);
spm_jobman('initcfg');
load('%s');

[r,c,v] = find( grid_all > 0 );
fid = fopen( '%s', 'wt' );
for i=1:length( r )
fprintf( fid, '(%%d,%%d)\\n', r(i), c(i) );
end
fclose(fid);
[r,c,v] = find( mask_all > 0 )
fid = fopen( '%s', 'wt' );
for i=1:length( r )
fprintf( fid, '(%%d,%%d)\\n', r(i), c(i) );
end
fclose(fid);
  """ % (locate_file("MIP.mat", os.path.dirname(spm8_standalone_command)),
         grid_file_path,
         mask_file_path))
    temp_mat_file.close()
    mexe = spm8_standalone_command
    cmd = [mexe,
           spm8_standalone_mcr_path,
           'script',
           temp_mat_file_path]
    context.system(*cmd)
                   # momoTODO utiliser spm_run au lieu de dupliquer le code!!

# the following is use in
# nuclearimaging/processes/analyzes/alyDesignMatrix.py and
# alyDesignExploreFilesAndFactors.py


def writeBatchToLoadSpmMatFile(spm_batch_path, spm_mat_file_path):
    spm_batch_file = open(spm_batch_path, 'w')
    spm_batch_file.write("""
matlabbatch{1}.cfg_basicio.load_vars.matname = {'%s'};
matlabbatch{1}.cfg_basicio.load_vars.loadvars.allvars = true;
""" % (spm_mat_file_path))
    spm_batch_file.close()

# the following is use in
# nuclearimaging/processes/analyzes/alyDesignExploreFilesAndFactors.py


def writeBatchAboutDesignExploreFileAndFactor(matlab_batch_path,
                                              spm8_path,
                                              spm_batch_path,
                                              spm_mat_file_path,
                                              ps_file_name='spm_designExplore'):
    matlab_batch_file = open(matlab_batch_path, 'w')
    matlab_batch_file = addSPMRunScriptInBatch(
        matlab_batch_file, spm8_path, spm_batch_path)
    matlab_batch_file.write("""
load('%s')
spm_DesRep('Files&Factors', reshape(cellstr(SPM.xY.P),size(SPM.xY.VY)),SPM.xX.I,SPM.xC,SPM.xX.sF,SPM.xsDes)
saveas(gcf, '%s', 'ps')
""" % (spm_mat_file_path, ps_file_name))
    matlab_batch_file.write("exit\n")
    matlab_batch_file.close()

# the following is use in nuclearimaging/processes/analyzes/alyDesignMatrix.py


def writeBatchAboutDesignMatrix(matlab_batch_path,
                                spm8_path,
                                spm_batch_path,
                                spm_mat_file_path,
                                ps_file_name='spm_designMatrix'):
    matlab_batch_file = open(matlab_batch_path, 'w')
    matlab_batch_file = addSPMRunScriptInBatch(
        matlab_batch_file, spm8_path, spm_batch_path)
    matlab_batch_file.write("""
load('%s')
spm_DesRep('DesMtx',SPM.xX, reshape(cellstr(SPM.xY.P),size(SPM.xY.VY)), SPM.xsDes)
saveas(gcf, '%s', 'ps')
""" % (spm_mat_file_path, ps_file_name))
    matlab_batch_file.write("exit\n")
    matlab_batch_file.close()


def addSPMRunScriptInBatch(matlab_batch_file, spm8_path, spm_batch_path):
    matlab_batch_file.write("""
addpath('%s');
spm('pet');
jobid = cfg_util('initjob', '%s');
cfg_util('run', jobid);
""" % (spm8_path, spm_batch_path))
    return matlab_batch_file
