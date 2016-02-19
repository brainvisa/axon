# -*- coding: utf-8 -*-
from soma.spm.spm_batch_maker_utils import convertPathListToSPMBatchString
from soma.spm.custom_decorator_pattern import checkIfArgumentTypeIsAllowed


class Subject():
  """
  Subject to be spatially normalized.
  """
  @checkIfArgumentTypeIsAllowed(list, 1)
  def setFlowFieldPathList(self, flow_field_path_list):
    """
    The  flow  fields  store  the deformation information. The same fields can be used
    for  both  forward  or  backward  deformations  (or  even, in principle, half way or
    exaggerated deformations).
    """
    self.flow_field_path_list = flow_field_path_list
    
  @checkIfArgumentTypeIsAllowed(list, 1)
  def setImagePathList(self, image_path_list):
    """
    The  flow  field deformations can be applied to multiple images. At this point, you
    are choosing how many images each flow field should be applied to.
    """
    self.image_path_list = image_path_list
    
  def getStringListForBatch( self ):
    if not None in [self.flow_field_path_list, self.image_path_list]:
      batch_list = []
      batch_list.append("flowfields = {%s};" % convertPathListToSPMBatchString(self.flow_field_path_list))
      batch_list.append("images = {%s};" % convertPathListToSPMBatchString(self.image_path_list))
      return batch_list
    else:
      raise ValueError("flow_field_path_list and image_path_list are required")
      