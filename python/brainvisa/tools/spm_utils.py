# -*- coding: utf-8 -*-

import calendar
import datetime as dt
import locale
import os
import shutil
import re

def moveSpmOutFiles(inDir, outPath, spmPrefixes=['w'], outDir=None, ext='.nii'):
  if not isinstance( spmPrefixes, list):
    raise TypeError('a list is required for spmPrefixes')
  else:
    for i in range(0, len(spmPrefixes)):
      if(spmPrefixes[i].startswith("""'""")):
        spmPrefixes[i] = spmPrefixes[i][1:-1]
    for root, _dirs, filenames in os.walk(inDir):
      for f in filenames:
        goodPrefix = False;
        for spmPrefix in spmPrefixes:
          if(f.startswith(spmPrefix)):
            goodPrefix = True;
            break
        goodExtension = f.endswith(ext) or f.endswith('.txt')
        if (goodPrefix and goodExtension):
          if(outPath is not None):
            movePath(root + '/' + f, outPath)
            return True
          else:
            movePath(root + '/' + f, outDir + '/' + f)   
            return True
  return False
       
    
def movePathToDiskItem(srcPath, dstDI):
  if(dstDI is not None):
    return movePath(srcPath, dstDI.fullPath())

def movePath(srcPath, dstPath):
  if (os.path.exists(srcPath)):
    if(os.path.exists(dstPath)): 
      os.remove(dstPath) # do not use directly os.rename (but remove before) because : on windows, rename with dstPath already exists causes exception
    shutil.move(srcPath, dstPath) # shutil.move is better than os.rename, because os.rename failed if src and dst are not on the same filesystem
  if (os.path.exists(srcPath)):
    os.remove(srcPath)

def merge_mat_files(mergedMatFile, *matFiles):
    """
    Create a .m file from a set of .m files
    
    :param string mergedMatFile
        The .m file containing the merge result
        
    :param set *matFiles
        The .m files to merge
        
    :returns:
        True if the merge succeeds and False otherwise
    """
    mergedMatFileFo = open(mergedMatFile, 'w')
    moduleNum = 1
    for f in matFiles:
        currentNum = None
        previousNum = None
        for l in open(f, 'r'):
            if not l.strip():
                continue
            try:
                currentNum = re.match(r"matlabbatch\{([0-9]*)\}(.*)",l).group(1)
            except:
                pass            
            if previousNum and currentNum != previousNum:
                moduleNum += 1
            previousNum = currentNum
            try:
                mergedMatFileFo.write(re.sub(r"matlabbatch{([0-9]*)}", "matlabbatch{" + str(moduleNum) + "}", l))
            except:
                return False
        moduleNum += 1
    mergedMatFileFo.close()
    
    return True

def spm_today():  
  now = dt.datetime.now()
  
  currentLocale = locale.getlocale(locale.LC_TIME)  
  #locale.setlocale(locale.LC_TIME, ("en","us"))# mika : doesn't works for me
  locale.setlocale(locale.LC_TIME, ('en_US', 'UTF8'))
  month_name = calendar.month_name[now.month]
  locale.setlocale(locale.LC_TIME, currentLocale)
  
  month = month_name[:3]
  mth = month[0].upper() + month[1:]
  mth = mth.replace('é', 'e')
  mth = mth.replace('û', 'u')
  spm_today = str(now.day)
  if (now.day < 10):
    spm_today = '0' + str(now.day)
  d = str(now.year) + mth + spm_today
  return d

def removeNan(filePath):
  fileMinfPath=filePath+ '.minf'
  if(os.path.exists(fileMinfPath)):
    os.remove(fileMinfPath)
  AimsRemoveNaNCmd='AimsRemoveNaN' + ' -i "' + str(filePath) + '" -o "' + str(filePath) + '.noNan.nii"'
  os.system(AimsRemoveNaNCmd)
  os.remove(filePath)
  os.rename(filePath + '.noNan.nii', filePath)
  os.rename(filePath + '.noNan.nii.minf', filePath + '.minf')
  
  
#------------------------------------------------------------------------------

def writeSmoothMatFile(context, data, matfileDI, mat_file
                              , fwhm="""[8 8 8]"""
                              , dtype="""0"""
                              , im="""0""" 
                              , prefix="""'spmSmooth_'"""                                           
                            ):
  mat_file.write("""
matlabbatch{1}.spm.spatial.smooth.data = {'%s,1'};
matlabbatch{1}.spm.spatial.smooth.fwhm = %s;
matlabbatch{1}.spm.spatial.smooth.dtype = %s;
matlabbatch{1}.spm.spatial.smooth.im = %s;
matlabbatch{1}.spm.spatial.smooth.prefix = %s;
""" % (data
        , fwhm, dtype, im, prefix)
                 )
  mat_file.close()
  return mat_file.name