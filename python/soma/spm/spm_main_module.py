from soma.spm.spm_launcher import SPM8Standalone, SPM8
from soma.spm.spm_launcher import SPM12Standalone, SPM12
import os
import tempfile


class SPMMainModule():
  
  def start(self, configuration, job_path):
    try:
      self.startFromStandalone(configuration, job_path)
    except:
      print('Starting by standalone failed')
      self.startFromMatlab(configuration, job_path)
  
  def startFromStandalone(self, configuration, job_path):
    spm_standalone = self.getSPMStandaloneInstance(configuration)
    spm_standalone.addBatchList(self.getStringListForBatch())
    spm_standalone.run(job_path)
    del spm_standalone
    self._moveSPMDefaultPathsIfNeeded()
    
  def startFromMatlab(self, configuration, job_path, batch_path=None):
    if batch_path is None:
      tmp_file = tempfile.NamedTemporaryFile(suffix=".m")
      batch_path = tmp_file.name
    else:
      pass
    spm = self.getSPMInstance(configuration)
    spm.addBatchList(self.getStringListForBatch())
    spm.run(job_path, batch_path)
    del spm
    self._moveSPMDefaultPathsIfNeeded()
  
  def _moveSPMDefaultPathsIfNeeded(self):
    """Virtual method, redefined in subclass if necessary"""
    pass
#===============================================================================
# 
#===============================================================================
class SPM8MainModule(SPMMainModule):
  
  def getSPMStandaloneInstance(self, configuration):
    return SPM8Standalone(configuration)
  
  def getSPMInstance(self, configuration):
    return SPM8(configuration)
  
#=============================================================================
# 
#=============================================================================
class SPM12MainModule(SPMMainModule):
  
  def startFromStandalone(self, configuration, job_path):
    spm_12_standalone = SPM12Standalone(configuration)
    spm_12_standalone.setBatchList(self.getStringListForBatch())
    spm_12_standalone.run(job_path)
    del spm_12_standalone
    self._moveSPMDefaultPathsIfNeeded()
    
  def startFromMatlab(self, configuration, job_path, batch_path=None):
    if batch_path is None:
      tmp_file = tempfile.NamedTemporaryFile(suffix=".m")
      batch_path = tmp_file.name
    else:
      pass
    spm_12 = SPM12(configuration)
    spm_12.setBatchList(self.getStringListForBatch())
    spm_12.run(job_path, batch_path)
    del spm_12
    self._moveSPMDefaultPathsIfNeeded()
    
