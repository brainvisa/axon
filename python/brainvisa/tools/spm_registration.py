from brainvisa.tools.spm_run import getSpm8Path 

#------------------------------------------------------------------------------
    
def writeCoregisteredMatFile(context, sourcePath, refPath, matfileDI, mat_file
, others="""{''}""", cost_fun="""'nmi'""", sep="""[4 2]""", tol="""[0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001]"""
, fwhm="""[7 7]""", interp="""1""", wrap="""[0 0 0]""", mask="""0""", prefix="""'spmCoregister_'"""):

  refFilesInScript = """{'""" + refPath + """,1'}"""
  sourceFilesInScript = """{'""" + sourcePath + """,1'}"""
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
""" % (refFilesInScript, sourceFilesInScript, others, cost_fun, sep, tol, fwhm, interp, wrap, mask, prefix))
  mat_file.close()
  return mat_file.name

#------------------------------------------------------------------------------

def writeNormalizeMatFile(context, configuration, src, imgToWrite, matfileDI, mat_file
        , tmp=None, wtsrc="""''"""
        , weight="""''""", smosrc="""8""", smoref="""0""", regtype="""'mni'""", cutoff="""25""", nits="""16""", reg="""1"""
        , preserve="""0""", bb="""[-90 -126 -72  
                                      90 90 108]""", vox="""[2 2 2]""", interp="""1""", wrap="""[0 0 0]""", prefix="""'spmNormalized_'""" 
        ):
  spm8Path = getSpm8Path(configuration)
  if(tmp == None):
    tmp = str(spm8Path) + """/templates/SPECT.nii"""
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
matlabbatch{1}.spm.spatial.normalise.estwrite.roptions.preserve = %s;
matlabbatch{1}.spm.spatial.normalise.estwrite.roptions.bb = %s;
matlabbatch{1}.spm.spatial.normalise.estwrite.roptions.vox = %s;
matlabbatch{1}.spm.spatial.normalise.estwrite.roptions.interp = %s;
matlabbatch{1}.spm.spatial.normalise.estwrite.roptions.wrap = %s;
matlabbatch{1}.spm.spatial.normalise.estwrite.roptions.prefix = %s;
""" % (src
      , wtsrc
      , imgToWrite, tmp
      , weight, smosrc, smoref, regtype, cutoff, nits, reg
      , preserve, bb, vox, interp, wrap, prefix 
       ))
  mat_file.close()
  return mat_file.name 