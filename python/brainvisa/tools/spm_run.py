# -*- coding: utf-8 -*-

from brainvisa.validation import ValidationError
import distutils.spawn
import os
import sys

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
    # print "Matlab executable is not found"
    raise ValidationError('Matlab is not found')
  if(not configuration.SPM.spm8_path):
    # print "SPM8 path is not found"
    raise ValidationError('SPM is not found')
  return True

#------------------------------------------------------------------------------
# try spm8Standalone, but if not working, use spm8 Matlab. Read note on top of this file
def run(context, configuration, jobPath, cmd=None, useMatlabFirst=False, isMatlabMandatory = False):
  '''Run a SPM job using SPM8 standalone or SMP8 Matlab version, trying them
  alternatively, with a specifiable priority
  '''

  firstException = None
  spmRunResult = None
  isSpmRunFailed=False

  if useMatlabFirst or isMatlabMandatory:
    spmRunResult, firstException = tryToRunSpm8(context, configuration, jobPath, cmd)
    isSpmRunFailed = spmRunResult != 0 or firstException != None
    
  if ((isSpmRunFailed or not useMatlabFirst) and not isMatlabMandatory):
    spmRunResult, e = tryToRunSpm8Standalone(context, configuration, jobPath)
    if not firstException:
      firstException = e    
    isSpmRunFailed = spmRunResult != 0 or firstException != None
     
    if (isSpmRunFailed and not useMatlabFirst):
      spmRunResult, e = tryToRunSpm8(context, configuration, jobPath, cmd)
      if not firstException:
        firstException = e
    
  if firstException is not None:
    raise firstException
  
  return spmRunResult

def tryToRunSpm8(context, configuration, jobPath, cmd):
  hasexception = None
  result = None
  try:
    result = runSpm8(context, configuration, jobPath, cmd)
    print 'spm_run.run, matlab version result:', result
  except Exception as e:
    print 'Exception in sun_spm.runSpm8:', e 
    hasexception = e       
  return result, hasexception

def tryToRunSpm8Standalone(context, configuration, jobPath):
  hasexception = None
  result = None
  try:
    result = runSpm8Standalone(context, configuration, jobPath)
    print 'spm_run.run, standalone version result:', result
  except Exception as e:
    print 'Exception in run_spm.runSpm8Standalone:', e
    hasexception = e       
  return result, hasexception

def runSpm8Standalone(context, configuration, matfilePath):

  if configuration.SPM.spm8_standalone_command is None or \
      len(configuration.SPM.spm8_standalone_command) == 0:
    raise SpmConfigError('SPM8 standalone is not configured')

  context.write(_t_('Using SPM8 standalone version (compiled, Matlab not needed)'))
  mexe = configuration.SPM.spm8_standalone_command
  pd = os.getcwd()
  os.chdir(os.path.dirname(matfilePath))
  cmd = [mexe, configuration.SPM.spm8_standalone_mcr_path, 'run', matfilePath] # it's possible to use 'script' instead of 'run'
  context.write('running SPM command:', cmd)
  try:
    result = context.system(*cmd)
  finally:
    os.chdir(pd)
  return result


def runSpm8(context, configuration, jobPath, spmCmd=None):

  if configuration.SPM.spm8_path is None or configuration.SPM.spm8_path == '':
    raise SpmConfigError('SPM8/Matlab is not configured')

  matlabBatchPath = str(jobPath).replace('_job', '')
  if matlabBatchPath == str(jobPath):
    matlabBatchPath = str(jobPath).replace('.m', '_batch.m')
  matlabBatchFile = open(matlabBatchPath, 'w')

  context.write("matlabBatchPath", matlabBatchPath)

  matlabBatchFile.write("try\n")
  matlabBatchFile.write("  addpath('" + configuration.SPM.spm8_path + "');\n")
  matlabBatchFile.write("  spm('pet');\n")
  matlabBatchFile.write("  jobid = cfg_util('initjob', '%s');\n" % jobPath)
  matlabBatchFile.write("  cfg_util('run', jobid);\n")
  if(spmCmd is not None):
    matlabBatchFile.write('  ' + spmCmd + "\n")
  matlabBatchFile.write("catch\n")
  matlabBatchFile.write("  disp('error running SPM');\n")
  matlabBatchFile.write("  exit(1);\n")
  matlabBatchFile.write("end\n")
  matlabBatchFile.write("exit\n")
  matlabBatchFile.close()

  try:
    result = runMatblatBatch(context, configuration, matlabBatchPath)
  finally:
    os.unlink(matlabBatchPath)
  return result


def runMatblatBatch(context, configuration, matlabBatchPath,
    removeCmdOption=None):
  cwd = os.getcwd()
  curDir = matlabBatchPath[:matlabBatchPath.rindex('/')]
  os.chdir(curDir)
  # execution batch file
  # momoTODO check if mexe is None when no matlab then raise error or exception
  mexe = distutils.spawn.find_executable(configuration.matlab.executable)
  matlabCmd = os.path.basename(matlabBatchPath)[:os.path.basename(matlabBatchPath).rindex('.')] # remove extension
  matlabOptions = configuration.matlab.options
  if(removeCmdOption is not None):
    matlabOptions = matlabOptions.replace(removeCmdOption, '')
  cmd = [mexe] + matlabOptions.split() + ['-r', matlabCmd]
  context.write('Running matlab command:', cmd)
  try:
    result = context.system(*cmd)
  finally:
    os.chdir(cwd)
  return result
