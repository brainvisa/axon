
import distutils.spawn
import os
import sys
from brainvisa.validation import ValidationError

def getSpm8Path(configuration):  
  if(configuration.SPM.spm8_path is not None and configuration.SPM.spm8_path != ''):
    return configuration.SPM.spm8_path
  elif(configuration.SPM.spm8_standalone_path is not None and configuration.SPM.spm8_standalone_path != ''):
    return configuration.SPM.spm8_standalone_path
  else:
    return None
  
#------------------------------------------------------------------------------
# spm8_standalone : 
#* does not generate spm_2012Oct03.ps file for result job 
#* can NOT execute spm_write_filtered command
#* has not VBM toolboxe
#-> so first, try spm8, but if not in configuration, use spm8Standalone
#------------------------------------------------------------------------------

def validation(configuration):
  try:
    return validationSpm8(configuration)
  except Exception, Spm8_error:
    try :
      validationSpm8Standalone(configuration)
    except Exception, Spm8Standalone_error:
      raise Spm8_error    
      raise Spm8Standalone_error

def validationSpm8Standalone(configuration):
  if((not configuration.SPM.spm8_standalone_command \
        or not (configuration.SPM.spm8_standalone_mcr_path or (sys.platform == "win32")))) \
      and not distutils.spawn.find_executable(\
        configuration.matlab.executable):
      raise ValidationError('SPM or matlab is not found')
  return True

def validationSpm8(configuration):
  if(not distutils.spawn.find_executable(configuration.matlab.executable)):
    print "Matlab executable is not found"
    raise ValidationError('Matlab is not found')
  if(not configuration.SPM.spm8_path):
    print "SPM8 path is not found"
    raise ValidationError('SPM is not found')
  return True

#------------------------------------------------------------------------------
# first, try spm8, but if not in configuration, use spm8Standalone. Read note on top of this file
def run(context, configuration, jobPath, cmd=None):  
  if(configuration.SPM.spm8_path is not None and configuration.SPM.spm8_path != ''):
    return runSpm8(context, configuration, jobPath, cmd)
  elif(configuration.SPM.spm8_standalone_command is not None and len(configuration.SPM.spm8_standalone_command) > 0):
    return runSpm8Standalone(context, configuration, jobPath, cmd)
  else:
    context.error('need SPM8 : see Brainvisa preferences and fill spm8 paths please.')

def runSpm8Standalone(context, configuration, matfilePath, matlabCommande=None):
  context.write(_t_('Using SPM8 standalone version (compiled, Matlab not needed)'))
  mexe = configuration.SPM.spm8_standalone_command
  pd = os.getcwd()
  os.chdir(os.path.dirname(matfilePath))
  cmd = [mexe, configuration.SPM.spm8_standalone_mcr_path, 'run', matfilePath] # it's possible to use 'script' instead of 'run'
  context.write('running SPM command:', cmd)
  context.system(*cmd)
  os.chdir(pd)  

def runSpm8(context, configuration, jobPath, spmCmd=None):
  matlabBatchPath = str(jobPath).replace('_job', '')  
  matlabBatchFile = open(matlabBatchPath, 'w')
  
  context.write("matlabBatchPath", matlabBatchPath)
  curDir = matlabBatchPath[:matlabBatchPath.rindex('/')]
  os.chdir(curDir)
  
  matlabBatchFile.write("addpath('" + configuration.SPM.spm8_path + "');\n")
  matlabBatchFile.write("spm('pet');\n")
  matlabBatchFile.write("jobid = cfg_util('initjob', '%s');\n" % jobPath)
  matlabBatchFile.write("cfg_util('run', jobid);\n")
  if(spmCmd is not None):
    matlabBatchFile.write(spmCmd + "\n")    
  matlabBatchFile.write("exit\n")
  matlabBatchFile.close()

  runMatblatBatch(context, configuration, matlabBatchPath) 
  
def runMatblatBatch(context, configuration, matlabBatchPath):
  curDir = matlabBatchPath[:matlabBatchPath.rindex('/')]
  os.chdir(curDir)
  # execution batch file
  mexe = distutils.spawn.find_executable(configuration.matlab.executable)
  matlabCmd = os.path.basename(matlabBatchPath)[:os.path.basename(matlabBatchPath).rindex('.')] # remove extension
  cmd = [mexe] + configuration.matlab.options.split() + ['-r', matlabCmd]
  context.write('Running matlab command:', cmd)
  context.system(*cmd)
 
#------------------------------------------------------------------------------

def moveSpmOutFiles(inDir, outPath, spmPrefixes, outDir=None, ext='.nii'):
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
        else:
          movePath(root + '/' + f, outDir + '/' + f)          
    
def movePathToDiskItem(srcPath, dstDI):
  if(dstDI is not None):
    return movePath(srcPath, dstDI.fullPath())

def movePath(srcPath, dstPath):
  if (os.path.exists(srcPath)):
    if(os.path.exists(dstPath)):      
      os.remove(dstPath) # do not use directly os.rename (but remove before) because : on windows, rename with dstPath already exists causes exception
    os.rename(srcPath, dstPath)
  if (os.path.exists(srcPath)):
    os.remove(srcPath)

#------------------------------------------------------------------------------
