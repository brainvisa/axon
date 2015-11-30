# HOW TO USE
#===============================================================================
#  Segment

from soma.spm.spm8.spatial.new_segment import NewSegment
from soma.spm.spm8.spatial.new_segment.channel import Channel
from soma.spm.spm8.spatial.new_segment.tissue import Tissue
from soma.spm.spm_launcher import SPM8, SPM8Standalone

new_segment = NewSegment()
#===============================================================================
#The fastest way to use is using SPM defaults :
new_segment.setSPMDefaultSetting('/tmp/t1mri.nii', '/tmp/TPM_template.nii')
new_segment.setSPMDefaultChannel('/tmp/t1mri.nii')
new_segment.setSPMDefautTissues('/tmp/TPM_template.nii')
#===============================================================================
#But each parameters can be modified
first_channel = Channel()
first_channel.setVolumePath('/tmp/t1mri.nii')
#the other parameters are already set with SPM default but to modify it, follow this example:
first_channel.setBiasRegularisationToExtremelyLight()
first_channel.setBiasFWHMTo60cutoff()
first_channel.saveBiasFieldAndBiasCorrected()
#By default spm prefix used, but setting custom outputs is possible
first_channel.setBiasCorrectedPath('/tmp/t1mri_bias_corrected.nii')
first_channel.setBiasFieldPath('/tmp/t1mri_bias_field.nii')

new_segment.appendChannel(first_channel)

first_tissue = Tissue()
first_tissue.setTissueProbilityMapPath('/tmp/TPM_template.nii')
first_tissue.setTissueProbilityDimension(1)
first_tissue.setGaussianNumber(2)
first_tissue.setNativeTissueNativeSpace()
first_tissue.unsetWarpedTissue()
new_segment.appendTissue(first_tissue)

second_tissue = Tissue()
second_tissue.setTissueProbilityMapPath('/tmp/TPM_template.nii')
second_tissue.setTissueProbilityDimension(2)
second_tissue.setGaussianNumber(2)
second_tissue.setNativeTissueNativeSpace()
second_tissue.unsetWarpedTissue()
new_segment.appendTissue(second_tissue)

third_tissue = Tissue()
third_tissue.setTissueProbilityMapPath('/tmp/TPM_template.nii')
third_tissue.setTissueProbilityDimension(3)
third_tissue.setGaussianNumber(2)
third_tissue.setNativeTissueNativeSpace()
third_tissue.unsetWarpedTissue()
new_segment.appendTissue(third_tissue)

fourth_tissue = Tissue()
fourth_tissue.setTissueProbilityMapPath('/tmp/TPM_template.nii')
fourth_tissue.setTissueProbilityDimension(4)
fourth_tissue.setGaussianNumber(3)
fourth_tissue.setNativeTissueNativeSpace()
fourth_tissue.unsetWarpedTissue()
new_segment.appendTissue(fourth_tissue)

fifth_tissue = Tissue()
fifth_tissue.setTissueProbilityMapPath('/tmp/TPM_template.nii')
fifth_tissue.setTissueProbilityDimension(5)
fifth_tissue.setGaussianNumber(4)
fifth_tissue.setNativeTissueNativeSpace()
fifth_tissue.unsetWarpedTissue()
new_segment.appendTissue(fifth_tissue)

sixth_tissue = Tissue()
sixth_tissue.setTissueProbilityMapPath('/tmp/TPM_template.nii')
sixth_tissue.setTissueProbilityDimension(6)
sixth_tissue.setGaussianNumber(2)
sixth_tissue.unsetNativeTissue()
sixth_tissue.unsetWarpedTissue()
new_segment.appendTissue(sixth_tissue)


new_segment.setMRFParameter(0)
new_segment.setWarpingRegularisation(4)
new_segment.setAffineRegularisationToEuropeanBrains()
new_segment.setSamplingDistance(3)
new_segment.saveDeformationFieldInverseAndForward()
new_segment.setDeformationFieldInverseOutputPath('/tmp/inverse_field.nii')
new_segment.setDeformationFieldForwardOutputPath('/tmp/forward_field.nii')

new_segment.start(configuration, '/tmp/batch_new_segment_8.m')#configuration is BV object (containing SPM & Matlab paths)