# -*- coding: utf-8 -*-
from soma.spm.spm_batch_maker_utils import addBatchKeyWordInEachItem, convertPathListToSPMBatchString, moveFileAndCreateFoldersIfNeeded
from soma.spm.custom_decorator_pattern import checkIfArgumentTypeIsAllowed, checkIfArgumentTypeIsStrOrUnicode
from soma.spm.virtual_spm.spatial.realign.estimation_options import EstimationOptions
from soma.spm.virtual_spm.spatial.realign.reslice_options import ResliceOptions
class Realign():


class EstimateAndReslice(Realign):
  """
  This  routine  realigns  a  time-series  of images acquired from the same subject using a least squares approach and a 6
  parameter  (rigid  body) spatial transformation.  The first image in the list specified by the user is used as a reference to
  which  all subsequent scans are realigned. The reference scan does not have to be the first chronologically and it may be
  wise to chose a "representative scan" in this role.
  The  aim  is primarily to remove movement artefact in fMRI and PET time-series (or more generally longitudinal studies) .
  The  headers  are  modified for each of the input images, such that. they reflect the relative orientations of the data. The
  details  of  the  transformation  are  displayed  in  the  results  window  as  plots  of  translation  and  rotation.  A set of
  realignment parameters are saved for each session, named rp_*.txt. After realignment, the images are resliced such that
  they  match  the  first  image selected voxel-for-voxel. The resliced images are named the same as the originals, except
  that they are prefixed by 'r'.
  """
  
  @checkIfArgumentTypeIsAllowed(list, 1)
  def addSessionPathList(self, session_path_list):
    self.session_path_list.append(session_path_list)
    
  @checkIfArgumentTypeIsAllowed(EstimationOptions, 1)
  def replaceEstimationOptions(self, estimation_options):
    del self.estimate_options
    self.self.estimate_options = self.estimate_options
    
  @checkIfArgumentTypeIsAllowed(ResliceOptions, 1)
  def replaceResliceOptions(self, reslice_options):
    del self.reslice_options
    self.self.reslice_options = self.reslice_options
    
  def getStringListForBatch(self):
    if self.session_path_list:
      batch_list = []
      data_string_converted = '{\n'
      for path_list in self.session_path_list:
	data_string_converted += convertPathListToSPMBatchString(path_list)
      data_string_converted += '}'
      batch_list.append("spm.spatial.realign.estwrite.data = '%s';" % data_string_converted)
      batch_list.extend(addBatchKeyWordInEachItem("spm.spatial.realign.estwrite", self.estimate_options.getStringListForBatch()))
      batch_list.extend(addBatchKeyWordInEachItem("spm.spatial.realign.estwrite", self.reslice_options.getStringListForBatch()))
      return batch_list
    else:
      raise ValueError("At least one session is required")
    
