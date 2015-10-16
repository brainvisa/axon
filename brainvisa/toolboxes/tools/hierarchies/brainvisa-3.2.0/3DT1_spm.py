# -*- coding: utf-8 -*-
include('base')

insert( 
  'analyzes/{analysis}',
  'DARTEL_{template}', SetContent(
    '<template>_DARTEL_{step}', SetType('DARTEL created template'),
    '{center}',  SetContent( # Center directory
      '{subject}', SetContent( # Subject directory
        '{acquisition}', SetContent(  # Acquisition directory
          '<subject>_DARTEL_flow_field', SetType('DARTEL flow field')  ,
          '<subject>_Nat_greyProba_warped', SetType('T1 MRI Nat GreyProba DARTEL warped'),
          '<subject>_Nat_whiteProba_warped', SetType('T1 MRI Nat WhiteProba DARTEL warped')
        ),
      ),
    ),
  ),
  '{center}/{subject}',
  't1mri', SetWeakAttr( 'modality', 't1mri' ),
    SetContent(
      '{acquisition}',
        SetType( 'Acquisition' ),
        SetDefaultAttributeValue( 'acquisition', default_acquisition ), SetNonMandatoryKeyAttribute( 'acquisition' ),
        DeclareAttributes( 'time_point', 'time_duration', 'rescan', 'acquisition_date' ),
        #SetWeakAttr( 'time_point', 'M_0' ),
        SetContent(
          # acquisition

          '<subject>_dicoms', SetType( 'Dicoms T1 MRI' ), # Native space

          '<subject>', SetType( 'Raw T1 MRI' ), SetPriorityOffset( +1 ),
            SetWeakAttr( 'normalized', 'no' ), # already existed for morphologist # Native space

          '<subject>_Nat_reseted', SetType('T1 MRI Nat reseted'), # Nat = Native space # original name was reseted Nat T1 MRI

        'registration', SetContent(), # is not an analysis

        '{analysis}',
          SetType( 'T1 MRI Analysis Directory' ),
          SetDefaultAttributeValue( 'analysis', default_analysis ),
          SetNonMandatoryKeyAttribute( 'analysis' ),
          SetContent(), # SetContent() because it is a directory

        ),
    ),
)


insert('{center}/{subject}/t1mri/{acquisition}/{analysis}',
  'nobias_<subject>', SetType('T1 MRI Bias Corrected'),) # already existed for morphologist # Native space


#PVE
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_pve', SetType('T1 MRI Nat Partial Volume Estimation'), SetPriorityOffset( +1 ))

# probability map in native space
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_greyProba', SetType('T1 MRI Nat GreyProba'), SetPriorityOffset( +1 ))

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_whiteProba', SetType('T1 MRI Nat WhiteProba'), SetPriorityOffset( +1 ))

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_csfProba', SetType('T1 MRI Nat CSFProba'), SetPriorityOffset( +1 ))

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_skullProba', SetType('T1 MRI Nat SkullProba'), SetPriorityOffset( +1 ))

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_scalpProba', SetType('T1 MRI Nat ScalpProba'), SetPriorityOffset( +1 ))



# mask in native space

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_greyMask_{method}', SetType('T1 MRI Nat GreyMask'),) # method is the way to obtain the mask from the probability map (e.g., apply a threshold, compare map...)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_whiteMask_{method}', SetType('T1 MRI Nat WhiteMask'),) # method is the way to obtain the mask from the probability map (e.g., apply a threshold, compare map...)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_CSF_Mask_{method}', SetType('T1 MRI Nat CSFMask'),) # method is the way to obtain the mask from the probability map (e.g., apply a threshold, compare map...)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_skull_Mask_{method}', SetType('T1 MRI Nat SkullMask'),) # method is the way to obtain the mask from the probability map (e.g., apply a threshold, compare map...)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_scalp_Mask_{method}', SetType('T1 MRI Nat ScalpMask'),) # method is the way to obtain the mask from the probability map (e.g., apply a threshold, compare map...)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_brain_Mask_{method}', SetType('T1 MRI Nat BrainMask'),)
#############
# Mni space #
#############
#PVE
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_pve', SetType('T1 MRI Mni Partial Volume Estimation'), SetWeakAttr('normalization', 'low-dimensional'))

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_DARTEL_pve', SetType('T1 MRI Mni Partial Volume Estimation'), SetWeakAttr('normalization', 'high-dimensional'))


insert('{center}/{subject}/t1mri/{acquisition}/',
  '<subject>_Mni', SetType('T1 MRI Mni'),)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}',
  'nobias_Mni_<subject>', SetType('T1 MRI Mni Bias Corrected'), SetWeakAttr('normalization', 'low-dimensional'))

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}',
  'nobias_Mni_DARTEL_<subject>', SetType('T1 MRI Mni Bias Corrected'), SetWeakAttr('normalization', 'high-dimensional'))

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}',
  'nobias_Mni_affine_<subject>', SetType('T1 MRI affine Mni Bias Corrected'),)


# probability map in mni space
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_rigid_greyProba_dartel_imported', SetType('T1 MRI Mni GreyProba Dartel imported'), SetWeakAttr('transformation', 'rigid'))
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_affine_greyProba_dartel_imported', SetType('T1 MRI Mni GreyProba Dartel imported'), SetWeakAttr('transformation', 'affine'))

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_rigid_whiteProba_dartel_imported', SetType('T1 MRI Mni WhiteProba Dartel imported'), SetWeakAttr('transformation', 'rigid'))
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_affine_whiteProba_dartel_imported', SetType('T1 MRI Mni WhiteProba Dartel imported'), SetWeakAttr('transformation', 'affine'))

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_rigid_csfProba_dartel_imported', SetType('T1 MRI Mni CSFProba Dartel imported'), SetWeakAttr('transformation', 'rigid'))
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_affine_csfProba_dartel_imported', SetType('T1 MRI Mni CSFProba Dartel imported'), SetWeakAttr('transformation', 'affine'))

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_rigid_skullProba_dartel_imported', SetType('T1 MRI Mni SkullProba Dartel imported'), SetWeakAttr('transformation', 'rigid'))

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_rigid_scalpProba_dartel_imported', SetType('T1 MRI Mni ScalpProba Dartel imported'), SetWeakAttr('transformation', 'rigid'))

#PVE
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_rigid_pve_dartel_imported', SetType('T1 MRI Mni Partial Volume Estimation Dartel imported'), SetWeakAttr('transformation', 'rigid'))
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_affine_pve_dartel_imported', SetType('T1 MRI Mni Partial Volume Estimation Dartel imported'), SetWeakAttr('transformation', 'affine'))

# WARNING please inform nuclear imaging team (morphologist team, and maybe others...) before changing this hierarchies
#unmodulated
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_greyProba', SetType('T1 MRI Mni GreyProba'), SetWeakAttr('modulated', 'no', 'normalization', 'low-dimensional'), SetPriorityOffset( +1 )) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_whiteProba', SetType('T1 MRI Mni WhiteProba'), SetWeakAttr('modulated', 'no', 'normalization', 'low-dimensional'), SetPriorityOffset( +1 )) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_csfProba', SetType('T1 MRI Mni CSFProba'), SetWeakAttr('modulated', 'no', 'normalization', 'low-dimensional'), SetPriorityOffset( +1 )) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_skullProba', SetType('T1 MRI Mni SkullProba'), SetWeakAttr('modulated', 'no', 'normalization', 'low-dimensional'), SetPriorityOffset( +1 )) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_scalpProba', SetType('T1 MRI Mni ScalpProba'), SetWeakAttr('modulated', 'no', 'normalization', 'low-dimensional'), SetPriorityOffset( +1 )) 
#modulated affine and non-linear
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_modulated_greyProba', SetType('T1 MRI Mni GreyProba'), SetWeakAttr('modulated', 'yes', 'modulation', 'affine and non-linear', 'normalization', 'low-dimensional')) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_modulated_whiteProba', SetType('T1 MRI Mni WhiteProba'), SetWeakAttr('modulated', 'yes', 'modulation', 'affine and non-linear', 'normalization', 'low-dimensional')) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_modulated_csfProba', SetType('T1 MRI Mni CSFProba'), SetWeakAttr('modulated', 'yes', 'modulation', 'affine and non-linear', 'normalization', 'low-dimensional')) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_modulated_skullProba', SetType('T1 MRI Mni SkullProba'), SetWeakAttr('modulated', 'yes', 'modulation', 'affine and non-linear', 'normalization', 'low-dimensional')) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_modulated_scalpProba', SetType('T1 MRI Mni ScalpProba'), SetWeakAttr('modulated', 'yes', 'modulation', 'affine and non-linear', 'normalization', 'low-dimensional')) 

#Using only in VBM8 process -->
#modulated non-linear only
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_non_linear_modulated_greyProba', SetType('T1 MRI Mni GreyProba'), SetWeakAttr('modulated', 'yes', 'modulation', 'non-linear only', 'normalization', 'low-dimensional')) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_non_linear_modulated_whiteProba', SetType('T1 MRI Mni WhiteProba'), SetWeakAttr('modulated', 'yes', 'modulation', 'non-linear only', 'normalization', 'low-dimensional')) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_non_linear_modulated_csfProba', SetType('T1 MRI Mni CSFProba'), SetWeakAttr('modulated', 'yes', 'modulation', 'non-linear only', 'normalization', 'low-dimensional')) 
#DARTEL unmodulated
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_DARTEL_greyProba', SetType('T1 MRI Mni GreyProba'), SetWeakAttr('modulated', 'no', 'normalization', 'high-dimensional'), SetPriorityOffset( +1 )) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_DARTEL_whiteProba', SetType('T1 MRI Mni WhiteProba'), SetWeakAttr('modulated', 'no', 'normalization', 'high-dimensional'), SetPriorityOffset( +1 )) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_DARTEL_csfProba', SetType('T1 MRI Mni CSFProba'), SetWeakAttr('modulated', 'no', 'normalization', 'high-dimensional'), SetPriorityOffset( +1 )) 
#DARTEL modulated affine and non-linear
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_DARTEL_modulated_greyProba', SetType('T1 MRI Mni GreyProba'), SetWeakAttr('modulated', 'yes', 'modulation', 'affine and non-linear', 'normalization', 'high-dimensional')) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_DARTEL_modulated_whiteProba', SetType('T1 MRI Mni WhiteProba'), SetWeakAttr('modulated', 'yes', 'modulation', 'affine and non-linear', 'normalization', 'high-dimensional')) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_DARTEL_modulated_csfProba', SetType('T1 MRI Mni CSFProba'), SetWeakAttr('modulated', 'yes', 'modulation', 'affine and non-linear', 'normalization', 'high-dimensional')) 
#DARTEL modulated non-linear only
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_DARTEL_non_linear_modulated_greyProba', SetType('T1 MRI Mni GreyProba'), SetWeakAttr('modulated', 'yes', 'modulation', 'non-linear only', 'normalization', 'high-dimensional')) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_DARTEL_non_linear_modulated_whiteProba', SetType('T1 MRI Mni WhiteProba'), SetWeakAttr('modulated', 'yes', 'modulation', 'non-linear only', 'normalization', 'high-dimensional')) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_DARTEL_non_linear_modulated_csfProba', SetType('T1 MRI Mni CSFProba'), SetWeakAttr('modulated', 'yes', 'modulation', 'non-linear only', 'normalization', 'high-dimensional')) 
#<--
# mask in MNI space

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_greyMask_{method}', SetType('T1 MRI Mni GreyMask'),) 
  
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_whiteMask_{method}', SetType('T1 MRI Mni WhiteMask'),)
  
#############
# PetSpc space #
#############

# probability map in pet space

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_PetSpc_greyProba', SetType('T1 MRI PetSpc GreyProba'),)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_PetSpc_whiteProba', SetType('T1 MRI PetSpc WhiteProba'),)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_PetSpc_csfProba', SetType('T1 MRI PetSpc CSFProba'),)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_PetSpc_skullProba', SetType('T1 MRI PetSpc SkullProba'),)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_PetSpc_scalpProba', SetType('T1 MRI PetSpc ScalpProba'),)
# mask in pet space
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_PetSpc_greyMask_{method}', SetType('T1 MRI PetSpc GreyMask'),) 

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_PetSpc_whiteMask_{method}', SetType('T1 MRI PetSpc WhiteMask'),)


###################
# transformations #
###################

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/',
  'iy_defField_<subject>_Mni_TO_Nat', SetType('DefField T1 MRI from Mni to Native'),) # need a spm prefix : iy to be used by SPM

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/',
  'y_defField_<subject>_Nat_TO_Mni', SetType('DefField T1 MRI from Native to Mni'),)# need a spm prefix : y to be used by SPM
  
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/',
  'iy_defField_<subject>_Mni_TO_PetSpc', SetType('DefField T1 MRI from Mni to PetSpc'),) # need a spm prefix : iy to be used by SPM

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/',
  'y_defField_<subject>_PetSpc_TO_Mni', SetType('DefField T1 MRI from PetSpc to Mni'),)# need a spm prefix : y to be used by SPM  

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/',
  'matDefField_<subject>_Nat_TO_Mni', SetType('MatDefField T1 MRI from Native to Mni'),)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/',
  'mat_<subject>_Mni_TO_Nat', SetType('OLD Mat T1 MRI from Mni to Native'),)
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/',
  'mat_<subject>_Mni_TO_Nat_sn', SetType('Mat T1 MRI from Mni to Native'),)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/',
  'mat_<subject>_Nat_TO_Mni', SetType('OLD Mat T1 MRI from Native to Mni'),)# old type without suffix _sn
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/',
  'mat_<subject>_Nat_TO_Mni_sn', SetType('Mat T1 MRI from Native to Mni'),) # le process "deformation" de spm8 ne filtre que les .mat qui ont le suffixe _sn

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/',
  'jac_wrp1<subject>_JacobianDeterminant', SetType('JacobianDeterminant'),)
###################
# Txt #
###################
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/',
  '<subject>_brain_matter_volumes', SetType('Brain Matter Volumes'),)

