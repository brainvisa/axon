# -*- coding: utf-8 -*-
include('base')
 
insert( '{center}/{subject}/t1mri/{acquisition}/',
  '<subject>_dicoms', SetType( 'Dicoms T1 MRI' ),) # Native space

insert( '{center}/{subject}/t1mri/{acquisition}/',
  '<subject>', SetType( 'Raw T1 MRI' ), SetPriorityOffset( +1 ), SetWeakAttr( 'normalized', 'no' ),) # already existed for morphologist # Native space

insert('{center}/{subject}/t1mri/{acquisition}/',
  '<subject>_Nat_reseted', SetType('reseted Nat T1 MRI'),) # Native space

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}',
  'nobias_<subject>', SetType('T1 MRI Bias Corrected'),) # already existed for morphologist # Native space

# probability map in native space

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_greyProba', SetType('T1 MRI Nat GreyProba'),)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_whiteProba', SetType('T1 MRI Nat WhiteProba'),)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_csfProba', SetType('T1 MRI Nat CSFProba'),)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_skullProba', SetType('T1 MRI Nat SkullProba'),)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_scalpProba', SetType('T1 MRI Nat ScalpProba'),)

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

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_greyProba', SetType('T1 MRI Mni GreyProba'),) 



#############
# transformation #
#############


insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/',
  'invDefField_<subject>', SetType('InvDefField T1 MRI'),)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/',
  'fwdDefField_<subject>', SetType('FwdDefField T1 MRI'),)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/',
  'matFwdDefField_<subject>', SetType('MatFwdDefField T1 MRI'),)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/',
  'matInv_<subject>', SetType('MatInv T1 MRI'),)

insert('{center}/{subject}/t1mri/{acquisition}/{analysis}/',
  'matFwd_<subject>', SetType('MatFwd T1 MRI'),)

