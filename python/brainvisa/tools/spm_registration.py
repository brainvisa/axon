
#------------------------------------------------------------------------------

def ititializeCoregisterParameters_withSPM8DefaultValuesforPET(process):
  process.others = []
  process.cost_fun = """'mi'"""
  process.sep = """[4 2]"""
  process.tol = """[0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001]"""
  process.fwhm = """[7 7]"""
  process.interp = """1"""
  process.wrap = """[0 0 0]"""
  process.mask = """0"""
  
def writeCoregisteredMatFile(context, sourcePath, refPath, spmJobFile
, othersPath, cost_fun, sep, tol, fwhm, interp, wrap, mask, prefix="""'spmCoregister_'"""):

  mat_file = open(spmJobFile, 'w')
  refFilesInScript = """{'""" + refPath + """,1'}"""
  sourceFilesInScript = """{'""" + sourcePath + """,1'}"""
  if(othersPath is None or len(othersPath) == 0):
    othersToWrite = """{''}"""
  else:
    othersToWrite="""{"""
    for otherPath in othersPath:
      othersToWrite+="\n\t'"+otherPath+",1'"
    othersToWrite+="""}"""
      
  
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

def initializeNormalizeParameters_usingSPM8DefaultValuesForPET(process):
  process.wtsrc = """''"""
  process.weight = """''"""
  process.smosrc = """8"""
  process.smoref = """0"""
  process.regtype = """'mni'"""
  
  process.cutoff = """25"""
  process.nits = """16"""
  process.reg = """1"""
  process.preserve = """0"""
  process.bb = """[-90 -126 -72  
                                                                        90 90 108]"""
  process.vox = """[2 2 2]"""# bouding box and voxel size value used for PET modality
  process.interp = """1"""
  process.wrap = """[0 0 0]"""
  
def writeNormalizeMatFile(context, configuration, src, imgToWrite, spmJobFile, tmp
        , wtsrc, weight, smosrc, smoref, regtype, cutoff, nits, reg, preserve, bb, vox, interp, wrap, prefix):
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
      , wtsrc
      , imgToWrite, tmp
      , weight, smosrc, smoref, regtype, cutoff, nits, reg
       ))
  
  if preserve is not None:
    mat_file.write(
      """matlabbatch{1}.spm.spatial.normalise.estwrite.roptions.preserve = %s;
""" % (preserve))
    
  if bb is not None:
    mat_file.write(
      """matlabbatch{1}.spm.spatial.normalise.estwrite.roptions.bb = %s;
"""%(bb) )
    
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
