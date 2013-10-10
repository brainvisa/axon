# -*- coding: utf-8 -*-
from tempfile import mkstemp
import os
from soma.path import locate_file

def writeResultsJob(spmJobPath, spmMatPath, title, pvalue_adjustment, pvalue_threshold, pvalue_extent_threshold):
  matFileFd = open(spmJobPath, 'w')
  matFileFd.write("""
spm_get_defaults('stats.topoFDR', 0);
spm_get_defaults('cmdline', true);
spm_jobman('initcfg');
matlabbatch{1}.spm.stats.results.spmmat = { '%s' };
matlabbatch{1}.spm.stats.results.conspec.titlestr = '%s';
matlabbatch{1}.spm.stats.results.conspec.contrasts = 1;
matlabbatch{1}.spm.stats.results.conspec.threshdesc = '%s';
matlabbatch{1}.spm.stats.results.conspec.thresh = %s;
matlabbatch{1}.spm.stats.results.conspec.extent = %s;
matlabbatch{1}.spm.stats.results.conspec.mask = struct('contrasts', {}, 'thresh', {}, 'mtype', {});
matlabbatch{1}.spm.stats.results.units = 1;
matlabbatch{1}.spm.stats.results.print = true;
""" % (spmMatPath, title, pvalue_adjustment, pvalue_threshold, pvalue_extent_threshold))
  matFileFd.close()
  
def writeSpmWriteFilteredBatch(matlabBatchPath, spm8_path, spmJobFilePath, result_image_type, resultMap, statsCsv, threshInfo):
  matlabBatchFile = open(matlabBatchPath, 'w')
  matlabBatchFile = write_RunJob_inBatch(matlabBatchFile, spm8_path, spmJobFilePath)
  matlabBatchFile.write(
    """ 
XYZ = xSPM.XYZ;
switch lower( '%s' )
case 'thresh'
    Z = xSPM.Z;

case 'binary'
    Z = ones(size(xSPM.Z));

case 'n-ary'
    Z       = spm_clusters(XYZ);
    num     = max(Z);
    [n, ni] = sort(histc(Z,1:num), 2, 'descend');
    n       = size(ni);
    n(ni)   = 1:num;
    Z       = n(Z);
end

spm_write_filtered( Z, XYZ, xSPM.DIM, xSPM.M, '', '%s' );

tmpfile = [ '%s' ];
fid = fopen(tmpfile,'wt');
fprintf(fid,[repmat('%%s,',1,11) '%%d,,\\n'],TabDat.hdr{1,:});
fprintf(fid,[repmat('%%s,',1,12) '\\n'],TabDat.hdr{2,:});
fmt = TabDat.fmt;
[fmt{2,:}] = deal(','); fmt = [fmt{:}];
fmt(end:end+1) = '\\n'; fmt = strrep(fmt,' ',',');
for i=1:size(TabDat.dat,1)
  fprintf(fid,fmt,TabDat.dat{i,:});
end
fclose(fid);

tmpfile = [ '%s' ];
fid = fopen(tmpfile, 'wt');
fprintf(fid, '%%s', sprintf('Height threshold %%c = %%0.2f {%%s}', xSPM.STAT, xSPM.u, xSPM.thresDesc));
fprintf(fid, '\\n' );
fprintf(fid, '%%s', sprintf('Extent threshold k = %%0.0f voxels', xSPM.k));
fclose(fid);

""" % (result_image_type, resultMap, statsCsv, threshInfo))
  matlabBatchFile.write("exit\n")
  matlabBatchFile.close()

def createBrainMIPWithGridTextFiles(context, spm8_standalone_path, spm8_standalone_command, spm8_standalone_mcr_path, gridFilePath, maskFilePath):
  matFileFi, matFile = mkstemp(suffix=".m")
  matFileFd = os.fdopen(matFileFi, "w")
  matFileFd.write("""
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
         gridFilePath, maskFilePath))
  matFileFd.close()
  mexe = spm8_standalone_command
  cmd = [mexe,
    spm8_standalone_mcr_path,
    'script',
    matFile]
  context.system(*cmd) # momoTODO utiliser spm_run au lieu de dupliquer le code!!

def write_LoadSpmMatFile_Job(spmJobPath, spmMatPath):
  matFileFd = open(spmJobPath, 'w')
  matFileFd.write("""
matlabbatch{1}.cfg_basicio.load_vars.matname = {'%s'};
matlabbatch{1}.cfg_basicio.load_vars.loadvars.allvars = true;
""" % (spmMatPath))
  matFileFd.close()

def write_DesignExploreFileAndFactor_Batch(matlabBatchPath, spm8_path, spmJobFilePath, spmMatPath, psFileName='spm_designExplore'):
  matlabBatchFile = open(matlabBatchPath, 'w')
  matlabBatchFile = write_RunJob_inBatch(matlabBatchFile, spm8_path, spmJobFilePath)
  matlabBatchFile.write(""" 
load('%s')
spm_DesRep('Files&Factors', reshape(cellstr(SPM.xY.P),size(SPM.xY.VY)),SPM.xX.I,SPM.xC,SPM.xX.sF,SPM.xsDes)
saveas(gcf, '%s', 'ps')
""" % (spmMatPath, psFileName))
  matlabBatchFile.write("exit\n")
  matlabBatchFile.close()
  
def write_DesignMatrix_Batch(matlabBatchPath, spm8_path, spmJobFilePath, spmMatPath, psFileName='spm_designMatrix'):
  matlabBatchFile = open(matlabBatchPath, 'w')
  matlabBatchFile = write_RunJob_inBatch(matlabBatchFile, spm8_path, spmJobFilePath)
  matlabBatchFile.write(""" 
load('%s')
spm_DesRep('DesMtx',SPM.xX, reshape(cellstr(SPM.xY.P),size(SPM.xY.VY)), SPM.xsDes)
saveas(gcf, '%s', 'ps')
""" % (spmMatPath, psFileName))
  matlabBatchFile.write("exit\n")
  matlabBatchFile.close()
  
def write_RunJob_inBatch(matlabBatchFile, spm8_path, spmJobFilePath):
  matlabBatchFile.write("addpath('" + spm8_path + "');\n")
  matlabBatchFile.write("spm('pet');\n")
  matlabBatchFile.write("jobid = cfg_util('initjob', '%s');\n" % spmJobFilePath)
  matlabBatchFile.write("cfg_util('run', jobid);\n")
  return matlabBatchFile
