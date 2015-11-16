 # -*- coding: utf-8 -*-
from soma.spm.virtual_spm.spatial.new_segment import NewSegment as NewSegment_virtual
from soma.spm.spm_main_module import SPM8MainModule

from soma.spm.spm8.spatial.new_segment.channel_container import ChannelContainer
from soma.spm.spm8.spatial.new_segment.tissue_container import TissueContainer

class NewSegment(NewSegment_virtual, SPM8MainModule):
  def __init__(self):
    self.channel_container = ChannelContainer()
    self.tissue_container = TissueContainer()
    self.MRF_parameter = 0
    self.warping_regularisation = 4
    self.affine_regularisation = 'mni'
    self.sampling_distance = 3.0
    self.deformation_fields = [0, 0]
    
    self.forward_deformation_prefix = 'y_'
    self.inverse_deformation_prefix = 'iy_'
    
    self.forward_deformation_path = None
    self.inverse_deformation_path = None
      
