
#------------------------------------------------------------------------------


def writeConversionMatFile(context, sourcePath, spmJobFile, name, dtype):

    mat_file = open(spmJobFile, 'w')
    mat_file.write("""matlabbatch{1}.spm.util.cat.vols = {'%s,1'};
matlabbatch{1}.spm.util.cat.name = '%s';
matlabbatch{1}.spm.util.cat.dtype = %s;
""" % (sourcePath, name, dtype))
    mat_file.close()
    return mat_file.name
