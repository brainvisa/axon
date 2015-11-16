#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL license version 2 under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the 
# terms of the CeCILL license version 2 as circulated by CEA, CNRS
# and INRIA at the following URL "http://www.cecill.info". 
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or 
# data to be ensured and,  more generally, to use and operate it in the 
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license version 2 and that you accept its terms.
include( 'base' )
#===============================================================================
# Not subject specific
#===============================================================================
#'templates/t1mri/'
t1mri_templates = (
  '{template}_HDW', setType('HDW template'),
  '{template}_HDW_DARTEL_{step}', setType('HDW DARTEL template'),
  '{template}_LDW', setType('LDW template'),
)
insert( 'templates/t1mri/', apply( SetContent, t1mri_templates))

#'analyzes/{analysis}/DARTEL_{template}'
DARTEL_directory = (
  '<template>_HDW_DARTEL_{step}', SetType('HDW DARTEL template created'),
  '{center}',  SetContent( # Center directory
    '{subject}', SetContent( # Subject directory
      '{acquisition}', SetContent(  # Acquisition directory
        '<subject>_HSW_DARTEL_flow_field', SetType('HDW DARTEL flow field'),
      ),
    ),
  ),
)

insert( 'analyzes/{analysis}/DARTEL_{template}', SetType('DARTEL analysis directory'), apply( SetContent, DARTEL_directory))

#===============================================================================
# subject specific
#===============================================================================

#{center}/{subject}/{analysis}/{acquisition}/using_LDW_to_{template}
LDW_directory = (
#using TPM
  #-T1 MRI probability map native space->
  '<subject>_grey_proba', setType('T1 MRI tissue probability map'), SetWeakAttr('tissue_class', 'grey'), # TODO : ajouter Native space ?
  '<subject>_white_proba', setType('T1 MRI tissue probability map'), SetWeakAttr('tissue_class', 'white'),
  '<subject>_csf_proba', setType('T1 MRI tissue probability map'), SetWeakAttr('tissue_class', 'csf'),
  '<subject>_skull_proba', setType('T1 MRI tissue probability map'), SetWeakAttr('tissue_class', 'skull'),
  '<subject>_scalp_proba', setType('T1 MRI tissue probability map'), SetWeakAttr('tissue_class', 'scalp'),
  #<--
  '<subject>_PVE', setType('T1 MRI partial volume estimation'),
  '<subject>_estimate_raw_volumes', setType('Estimate T1 MRI raw volumes'),
  '<subject>_forward_deformation_field', setType('Forward deformation field'),
  '<subject>_inverse_deformation_field', setType('Inverse deformation field'),
  '<subject>_bias_corrected', setType('T1 MRI Bias corrected'), #TODO : check if it's possible
  #-T1 MRI probability map DARTEL imported with rigid transform->
  '<subject>_grey_proba_rigid_registered', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'grey', 
		    'transformation', 'rigid'),
  '<subject>_white_proba_rigid_registered', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'white', 
                    'transformation', 'rigid'),
  '<subject>_csf_proba_rigid_registered', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'csf', 
                    'transformation', 'rigid'),
  '<subject>_skull_proba_rigid_registered', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'skull', 
                    'transformation', 'rigid'),
  '<subject>_scalp_proba_rigid_registered', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'scalp', 
                    'transformation', 'rigid'),
  #<--
  '<subject>_PVE_rigid_registered', 
        setType('T1 MRI Partial Volume Estimation'),
        SetWeakAttr('transformation', 'rigid'),
  #-T1 MRI probability map DARTEL imported with affine transform (VBM toolbox)->
  '<subject>_grey_proba_affine_registered', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'grey', 
		    'transformation', 'affine'),
  '<subject>_white_proba_affine_registered', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'white', 
                    'transformation', 'affine'),
  '<subject>_csf_proba_affine_registered', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'csf', 
                    'transformation', 'affine'),
  '<subject>_skull_proba_affine_registered', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'skull', 
                    'transformation', 'affine'),
  '<subject>_scalp_proba_affine_registered', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'scalp', 
                    'transformation', 'affine'),
  #<--
  '<subject>_PVE_affine_registered', 
        setType('T1 MRI Partial Volume Estimation'),
        SetWeakAttr('transformation', 'affine'),
)
        
HDW_directory= (
  '<subject>_jacobian_warped', 
        setType('Jacobian determinant'),
)
#{center}/{subject}/{analysis}/{acquisition}/using_LDW_to_{template} ==> warping_method : low-dimensional
#{center}/{subject}/{analysis}/{acquisition}/using_HDW_to_{template} ==> warping_method : high-dimensional
def createHierarchyTreeDependingOnNormalization(warping_method):
  return (
#Warped on template, LDW(ex: TPM)/or/HDW(ex : DARTEL) depending on warping_method (low-dimensional/or/high-dimensional)
  #-T1 MRI probability map warped on LDW/or/HDW template with non-linear only modulation->
  '<subject>_grey_proba_warped_with_non_linear_modulation', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'grey', 
                    'modulation', 'non-linear only',
                    'warping_method', warping_method),
  '<subject>_white_proba_warped_with_non_linear_modulation', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'white', 
                    'modulation', 'non-linear only',
                    'warping_method', warping_method),
  '<subject>_csf_proba_warped_with_non_linear_modulation', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'csf', 
                    'modulation', 'non-linear only',
                    'warping_method', warping_method),
  '<subject>_skull_proba_warped_with_non_linear_modulation', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'skull', 
                    'modulation', 'non-linear only',
                    'warping_method', warping_method),
  '<subject>_scalp_proba_warped_with_non_linear_modulation', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'scalp', 
                    'modulation', 'non-linear only',
                    'warping_method', warping_method),
  #<--
  #-T1 MRI probability map warped on TPM/or/DARTEL template with affine and non-linear modulation->
  '<subject>_grey_proba_warped_with_affine_and_non_linear_modulation', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'grey', 
                    'modulation', 'affine and non-linear',
                    'warping_method', warping_method),
  '<subject>_white_proba_warped_with_affine_and_non_linear_modulation', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'white', 
                    'modulation', 'affine and non-linear',
                    'warping_method', warping_method),
  '<subject>_csf_proba_warped_with_affine_and_non_linear_modulation', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'csf', 
                    'modulation', 'affine and non-linear',
                    'warping_method', warping_method),
  '<subject>_skull_proba_warped_with_affine_and_non_linear_modulation', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'skull', 
                    'modulation', 'affine and non-linear',
                    'warping_method', warping_method),
  '<subject>_scalp_proba_warped_with_affine_and_non_linear_modulation', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'scalp',  
                    'modulation', 'affine and non-linear',
                    'warping_method', warping_method),
  #<--
  #-T1 MRI probability map warped on TPM/or/DARTEL without modulation->
  '<subject>_grey_proba_warped_without_modulation', #TODO : check if without_modulation is useless
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'grey', 
                    'warping_method', warping_method),
  '<subject>_white_proba_warped_without_modulation', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'white', 
                    'warping_method', warping_method),
  '<subject>_csf_proba_warped_without_modulation', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'csf', 
                    'warping_method', warping_method),
  '<subject>_skull_proba_warped_without_modulation', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'skull', 
                    'warping_method', warping_method),
  '<subject>_scalp_proba_warped_without_modulation', 
	setType('T1 MRI tissue probability map'), 
	SetWeakAttr('tissue_class', 'scalp', 
                    'warping_method', warping_method),
  #<--
  '<subject>_PVE_warped_without_modulation', 
        setType('T1 MRI Partial Volume Estimation'),
        SetWeakAttr('warping_method', warping_method),
  )
#{center}/{subject}/{analysis}/{acquisition}
analysis_directory = (
  'using_LDW_to_{template}', apply( SetContent, LDW_directory +
                                                createHierarchyTreeDependingOnNormalization(warping_method='low-dimensional')),
  'using_HDW_to_{template}', apply( SetContent, HDW_directory +
                                                createHierarchyTreeDependingOnNormalization(warping_method='high-dimensional'),
)
#{center}/{subject}/{analysis}
acquisition_directory = (
  '{acquisition}', apply( SetContent, analysis_directory),
)
insert( '{center}/{subject}/{analysis}', apply( SetContent, acquisition_directory))


