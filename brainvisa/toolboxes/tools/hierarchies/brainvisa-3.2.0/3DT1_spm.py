# -*- coding: utf-8 -*-
include('base')

insert( '{center}/{subject}',
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

# probability map in native space

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_greyProba', SetType('T1 MRI Nat GreyProba'), SetWeakAttr('dartel_imported', 'no'))
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_dartel_greyProba', SetType('T1 MRI Nat GreyProba'), SetWeakAttr('dartel_imported', 'yes'))

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_whiteProba', SetType('T1 MRI Nat WhiteProba'), SetWeakAttr('dartel_imported', 'no'))
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_dartel_whiteProba', SetType('T1 MRI Nat WhiteProba'), SetWeakAttr('dartel_imported', 'yes'))

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_csfProba', SetType('T1 MRI Nat CSFProba'), SetWeakAttr('dartel_imported', 'no'))
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_dartel_csfProba', SetType('T1 MRI Nat CSFProba'), SetWeakAttr('dartel_imported', 'yes'))

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_skullProba', SetType('T1 MRI Nat SkullProba'), SetWeakAttr('dartel_imported', 'no'))
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_dartel_skullProba', SetType('T1 MRI Nat SkullProba'), SetWeakAttr('dartel_imported', 'yes'))

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_scalpProba', SetType('T1 MRI Nat ScalpProba'), SetWeakAttr('dartel_imported', 'no'))
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_dartel_scalpProba', SetType('T1 MRI Nat ScalpProba'), SetWeakAttr('dartel_imported', 'yes'))



# mask in native space

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_greyMask_{method}', SetType('T1 MRI Nat GreyMask'),) # methode is the way to obtain the mask from the probability map. e.g. : apply a threshold, compare map...

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_whiteMask_{method}', SetType('T1 MRI Nat WhiteMask'),) # methode is the way to obtain the mask from the probability map. e.g. : apply a threshold, compare map...

#############
# Mni space #
#############

insert('{center}/{subject}/t1mri/{acquisition}/',
  '<subject>_Mni', SetType('T1 MRI Mni'),)

# probability map in mni space

# WARNING please inform nuclear imaging team (morphologist team, and maybe others...) before changing this hierarchies

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_greyProba', SetType('T1 MRI Mni GreyProba'), SetWeakAttr('modulated', 'no')) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_whiteProba', SetType('T1 MRI Mni WhiteProba'), SetWeakAttr('modulated', 'no')) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_csfProba', SetType('T1 MRI Mni CSFProba'), SetWeakAttr('modulated', 'no')) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_skullProba', SetType('T1 MRI Mni SkullProba'), SetWeakAttr('modulated', 'no')) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_scalpProba', SetType('T1 MRI Mni ScalpProba'), SetWeakAttr('modulated', 'no')) 

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_modulated_greyProba', SetType('T1 MRI Mni GreyProba'), SetWeakAttr('modulated', 'yes')) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_modulated_whiteProba', SetType('T1 MRI Mni WhiteProba'), SetWeakAttr('modulated', 'yes')) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_modulated_csfProba', SetType('T1 MRI Mni CSFProba'), SetWeakAttr('modulated', 'yes')) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_modulated_skullProba', SetType('T1 MRI Mni SkullProba'), SetWeakAttr('modulated', 'yes')) 
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_modulated_scalpProba', SetType('T1 MRI Mni ScalpProba'), SetWeakAttr('modulated', 'yes')) 

#############
# PetSpc space #
#############

# probability map in native space

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
# mask in native space
insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_PetSpc_greyMask_{method}', SetType('T1 MRI PetSpc GreyMask'),) # methode is the way to obtain the mask from the probability map. e.g. : apply a threshold, compare map...

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
  'mat_<subject>_Mni_TO_Nat', SetType('Mat T1 MRI from Mni to Native'),)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/',
  'mat_<subject>_Nat_TO_Mni', SetType('Mat T1 MRI from Native to Mni'),)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/',
  'jac_wrp1<subject>_JacobianDeterminant', SetType('JacobianDeterminant'),)
