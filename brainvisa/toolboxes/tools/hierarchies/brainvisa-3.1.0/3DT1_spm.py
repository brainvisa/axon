# -*- coding: utf-8 -*-
include('base')

insert('{protocol}/{subject}',
    't1mri', SetWeakAttr( 'modality', 't1mri' ),
      SetContent(
        '{acquisition}',
          SetDefaultAttributeValue('acquisition', default_acquisition),
          SetNonMandatoryKeyAttribute('acquisition'),
          SetContent(
            '<subject>', SetType('Raw T1 MRI'), SetPriorityOffset( +1 ),
              SetWeakAttr('normalized', 'no'), # already existed for morphologist

            '<subject>_dicoms', SetType('Dicoms T1 MRI'), # Native space
            '<subject>_Nat_reseted', SetType('T1 MRI Nat reseted'), # Nat = Native space # original name was reseted Nat T1 MRI

            'registration', SetContent(),

            '{analysis}',
              SetType('T1 MRI Analysis Directory'),
              SetDefaultAttributeValue('analysis', default_analysis),
              SetNonMandatoryKeyAttribute('analysis'),
              SetContent(),

        ),
    ),
)


insert('{protocol}/{subject}/t1mri/{acquisition}/{analysis}',
  'nobias_<subject>', SetType('T1 MRI Bias Corrected'),) # already existed for morphologist # Native space

# mask in native space

insert('{protocol}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_greyMask_{method}', SetType('T1 MRI Nat GreyMask'),) # methode is the way to obtain the mask from the probability map. e.g. : apply a threshold, compare map...

insert('{protocol}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Nat_whiteMask_{method}', SetType('T1 MRI Nat WhiteMask'),) # methode is the way to obtain the mask from the probability map. e.g. : apply a threshold, compare map...

#############
# Mni space #
#############

insert('{protocol}/{subject}/t1mri/{acquisition}/',
  '<subject>_Mni', SetType('T1 MRI Mni'),)

# probability map in mni space
insert('{protocol}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_greyProba', SetType('T1 MRI Mni GreyProba'), SetWeakAttr('modulated', 'no')) 
insert('{protocol}/{subject}/t1mri/{acquisition}/{analysis}/segmentation',
  '<subject>_Mni_modulated_greyProba', SetType('T1 MRI Mni GreyProba'), SetWeakAttr('modulated', 'yes')) 

###################
# transformations #
###################

insert('{protocol}/{subject}/t1mri/{acquisition}/{analysis}/',
  'y_defField_<subject>_Nat_TO_Mni', SetType('DefField T1 MRI from Native to Mni'),)

insert('{protocol}/{subject}/t1mri/{acquisition}/{analysis}/',
  'mat_<subject>_Mni_TO_Nat', SetType('Mat T1 MRI from Mni to Native'),)

insert('{protocol}/{subject}/t1mri/{acquisition}/{analysis}/',
  'mat_<subject>_Nat_TO_Mni', SetType('Mat T1 MRI from Native to Mni'),)

