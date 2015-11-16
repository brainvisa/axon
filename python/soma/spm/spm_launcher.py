# -*- coding: utf-8 -*-
from distutils.spawn import find_executable
import os

from soma.spm.custom_decorator_pattern import checkIfArgumentTypeIsAllowed
from soma.spm.spm_batch_maker_utils import addBatchKeyWordInEachItem
from soma.spm.custom_decorator_pattern import singleton


class SPMLauncher():
  def __init__(self, BV_configuration):
    self.BV_configuration = BV_configuration
    self.current_batch_index = 0
    self.full_batch_list = []

  @checkIfArgumentTypeIsAllowed(list, 1)
  def addBatchList(self, batch_list):
    self.current_batch_index += 1
    matlab_batch_key_word = 'matlabbatch{' + str(self.current_batch_index) + '}'
    self.full_batch_list.extend(addBatchKeyWordInEachItem(matlab_batch_key_word, batch_list))
    
  @checkIfArgumentTypeIsAllowed(list, 1)
  def setBatchList(self, batch_list):
    self.current_batch_index = 1
    matlab_batch_key_word = 'matlabbatch{' + str(self.current_batch_index) + '}'
    self.full_batch_list = addBatchKeyWordInEachItem(matlab_batch_key_word, batch_list)
    
  @checkIfArgumentTypeIsAllowed(list, 1)
  def addSPMCommand(self, spm_commands_list):
    self.full_batch_list.extend(spm_commands_list)
    
  def _writeJob(self, job_path):
    if not os.path.exists(os.path.dirname(job_path)):
      os.makedirs(os.path.dirname(job_path))
    else:
      pass#folder already exists
    matlab_job_file = open(job_path, 'w+')
    for batch_row in self.full_batch_list:
      matlab_job_file.write(batch_row + '\n')
    matlab_job_file.close()  
    
  #TODO : find an other way to re-initialize or destroy singleton function
  def _reset(self):
    self.__init__(self.BV_configuration)
    
#===========================================================================
# 
#===========================================================================
class SPM(SPMLauncher):
  def __init__(self, BV_configuration):
    SPMLauncher.__init__(self, BV_configuration)
    self.matlab_executable_path = self._checkMatlabAvailability(BV_configuration)
    self.matlab_options = self._checkMatlabOptions(BV_configuration)
    self.matlab_commands_before_list = []
    self.matlab_commands_after_list = []
    self.spm_path = None
    
  def _checkMatlabOptions(self, BV_configuration):
    if BV_configuration.matlab.options is not None:
      return BV_configuration.matlab.options
    else:
      return ''
    
  def _checkMatlabAvailability(self, BV_configuration):
    if BV_configuration.matlab.executable is not None:
      matlab_executable_path = find_executable(BV_configuration.matlab.executable)
      if matlab_executable_path:
        return matlab_executable_path
      else:
        raise RuntimeError('Matlab executable not found')
    else:
      raise ValueError('Matlab not configured')
    
  @checkIfArgumentTypeIsAllowed(list, 1)
  def addMatlabCommandBefore(self, matlab_commands_list):
    self.matlab_commands_before_list.extend(matlab_commands_list)
    
  @checkIfArgumentTypeIsAllowed(list, 1)
  def addMatlabCommandAfter(self, matlab_commands_list):
    self.matlab_commands_after_list.extend(matlab_commands_list)    
    
  def setNewMatlabOptions(self, matlab_options):
    self.matlab_options = matlab_options
    
  def run(self, job_path, batch_path, use_matlab_options=True):
    self._writeJob(job_path)
    self._writeBatch(job_path, batch_path)
    self._runMatlabBatch(batch_path, use_matlab_options)
    self._reset()
    
  def _writeBatch(self, job_path, batch_path):
    if not os.path.exists(os.path.dirname(batch_path)):
      os.makedirs(os.path.dirname(batch_path))
    else:
      pass#folder already exists
    if self.spm_path is not None:
      matlab_batch_file = open(batch_path, 'w+')
      for matlab_command in self.matlab_commands_before_list:
        matlab_batch_file.write(matlab_command + "\n")
      matlab_batch_file.write("try\n")
      matlab_batch_file.write("  addpath('" + self.spm_path + "');\n")
      matlab_batch_file.write("  spm('pet');\n")
      matlab_batch_file.write("  jobid = cfg_util('initjob', '%s');\n" % job_path)#initialise job
      matlab_batch_file.write("  cfg_util('run', jobid);\n")
      matlab_batch_file.write("catch\n")
      matlab_batch_file.write("  disp('error running SPM');\n")
      matlab_batch_file.write("  exit(1);\n")
      matlab_batch_file.write("end\n")
      for matlab_command in self.matlab_commands_after_list:
        matlab_batch_file.write(matlab_command + "\n")
      matlab_batch_file.write("exit\n")
      matlab_batch_file.close()
    else:
      raise ValueError('Spm path not found')#This raise is normally useless!!
    
  def _runMatlabBatch(self, batch_path, use_matlab_options):
    cwd = os.getcwd()
    batch_directory = os.path.dirname(batch_path)
    os.chdir(batch_directory)
    if not use_matlab_options:
      matlab_run_options = ''
    else:
      matlab_run_options = self.matlab_options
      
    matlab_commmand = [self.matlab_executable_path, matlab_run_options, "-r \"run('%s');\"" %batch_path]
    print('Running matlab command:', matlab_commmand)
    try:
      result = os.system(' '.join(matlab_commmand))
    except:
      pass#This method have to continue to call at least self._reset()
    finally:
      os.chdir(cwd)
      #os.remove(batch_path)

#===========================================================================
#===============================================================================
# # SPM8 (Matlab needed)
#===============================================================================
#===========================================================================
@singleton
class SPM8(SPM):
  def __init__(self, BV_configuration):
    SPM.__init__(self, BV_configuration)
    self._checkSPM8Availability(BV_configuration)
      
  def _checkSPM8Availability(self, BV_configuration):
    self.spm_path = checkIfItemIsConfiguratedAndExists(BV_configuration.SPM.spm8_path, 'spm8_path')
    
#===========================================================================
# SPM12 (Matlab needed)
#===========================================================================
@singleton
class SPM12(SPM):
  def __init__(self, BV_configuration):
    SPM.__init__(self, BV_configuration)
    self._checkSPM12Availability(BV_configuration)
      
  def _checkSPM12Availability(self, BV_configuration):
    self.spm_path = checkIfItemIsConfiguratedAndExists(BV_configuration.SPM.spm12_path, 'spm12_path')

#===========================================================================
# 
#===========================================================================
class SPMStandalone(SPMLauncher):
  def __init__(self, BV_configuration):
    SPMLauncher.__init__(self, BV_configuration)
    self.standalone_command = None
    self.standalone_mcr_path = None
    self.standalone_path = None

  def run(self, job_path, initcfg=True):
    self.full_batch_list.insert(0, "spm('defaults', 'PET');")
    if initcfg:
      self.full_batch_list.insert(0, "spm_jobman('initcfg');")
    self._writeJob(job_path)
    self._runStandaloneBatch(job_path)
    self._reset()
  
  def _runStandaloneBatch(self, job_path):
    cwd = os.getcwd()
    job_directory = os.path.dirname(job_path)
    os.chdir(job_directory)
    standalone_command = [self.standalone_command, self.standalone_mcr_path, 'run', job_path]
    print('running SPM standalone command:', standalone_command)
    try:
      result = os.system(' '.join(standalone_command))
    except:
      pass#This method have to continue to call at least self._reset()
    finally:
      os.chdir(cwd)
    
#===============================================================================
# SPM8 Standalone
#===============================================================================
@singleton
class SPM8Standalone(SPMStandalone):
  def __init__(self, BV_configuration):
    SPMStandalone.__init__(self, BV_configuration)
    self._checkSPM8StandaloneAvailability(BV_configuration)
    
  def _checkSPM8StandaloneAvailability(self, BV_configuration):
    self.standalone_command = checkIfItemIsConfiguratedAndExists(BV_configuration.SPM.spm8_standalone_command, 'spm8_standalone_command')
    self.standalone_mcr_path = checkIfItemIsConfiguratedAndExists(BV_configuration.SPM.spm8_standalone_mcr_path, 'spm8_standalone_mcr_path')
    self.standalone_path = checkIfItemIsConfiguratedAndExists(BV_configuration.SPM.spm8_standalone_path, 'spm8_standalone_path')
    

#===============================================================================
# SPM12 Standalone
#===============================================================================
@singleton
class SPM12Standalone(SPMStandalone):
  def __init__(self, BV_configuration):
    SPMStandalone.__init__(self, BV_configuration)
    self._checkSPM12StandaloneAvailability(BV_configuration)
    
  def _checkSPM12StandaloneAvailability(self, BV_configuration):
    self.standalone_command = checkIfItemIsConfiguratedAndExists(BV_configuration.SPM.spm12_standalone_command, 'spm12_standalone_command')
    self.standalone_mcr_path = checkIfItemIsConfiguratedAndExists(BV_configuration.SPM.spm12_standalone_mcr_path, 'spm12_standalone_mcr_path')
    self.standalone_path = checkIfItemIsConfiguratedAndExists(BV_configuration.SPM.spm12_standalone_path, 'spm12_standalone_path')
    
        
#===========================================================================
#===========================================================================
# # 
#===========================================================================
#===========================================================================
def checkIfItemIsConfiguratedAndExists(configuration_item, configuration_name):
  if configuration_item is not None:
    if os.path.exists(configuration_item):
      return configuration_item
    else:
      raise ValueError(configuration_name + ' does not exist')
  else:
    raise ValueError(configuration_name + ' not configured')