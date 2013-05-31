# -*- coding: utf-8 -*-
include( 'builtin' )

FileType('Dicoms T1 MRI', 'T1 MRI')
FileType('reseted Nat T1 MRI', 'T1 MRI')
FileType('T1 MRI Bias Corrected', 'T1 MRI')
FileType('T1 MRI Mni', 'T1 MRI')

#################
# segmentations #
#################

# Tissue Probability Map : in native and mni space

FileType('T1 MRI Tissue Probability Map', '4D Volume')

FileType('T1 MRI Native Space Tissue Probability Map', 'T1 MRI Tissue Probability Map')
FileType('T1 MRI Nat GreyProba', 'T1 MRI Native Space Tissue Probability Map')
FileType('T1 MRI Nat WhiteProba', 'T1 MRI Native Space Tissue Probability Map')
FileType('T1 MRI Nat CSFProba', 'T1 MRI Native Space Tissue Probability Map')
FileType('T1 MRI Nat SkullProba', 'T1 MRI Native Space Tissue Probability Map')
FileType('T1 MRI Nat ScalpProba', 'T1 MRI Native Space Tissue Probability Map')

FileType('T1 MRI Mni Space Tissue Probability Map', 'T1 MRI Tissue Probability Map')
FileType('T1 MRI Mni GreyProba', 'T1 MRI Mni Space Tissue Probability Map')
FileType('T1 MRI Mni WhiteProba', 'T1 MRI Mni Space Tissue Probability Map')
FileType('T1 MRI Mni CSFProba', 'T1 MRI Mni Space Tissue Probability Map')
FileType('T1 MRI Mni SkullProba', 'T1 MRI Mni Space Tissue Probability Map')
FileType('T1 MRI Mni ScalpProba', 'T1 MRI Mni Space Tissue Probability Map')

# Tissue Mask : in native and mni space

FileType('T1 MRI Tissue Mask', '4D Volume')

FileType('T1 MRI Native Space Tissue Mask', 'T1 MRI Tissue Mask')
FileType('T1 MRI Nat GreyMask', 'T1 MRI Native Space Tissue Mask')
FileType('T1 MRI Nat WhiteMask', 'T1 MRI Native Space Tissue Mask')
FileType('T1 MRI Nat CSFMask', 'T1 MRI Native Space Tissue Mask')
FileType('T1 MRI Nat SKullMask', 'T1 MRI Native Space Tissue Mask')
FileType('T1 MRI Nat ScalpMask', 'T1 MRI Native Space Tissue Mask')

FileType('T1 MRI Mni Space Tissue Mask', 'T1 MRI Tissue Mask')
FileType('T1 MRI Mni GreyMask', 'T1 MRI Mni Space Tissue Mask')
FileType('T1 MRI Mni WhiteMask', 'T1 MRI Mni Space Tissue Mask')
FileType('T1 MRI Mni CSFMask', 'T1 MRI Mni Space Tissue Mask')
FileType('T1 MRI Mni SKullMask', 'T1 MRI Mni Space Tissue Mask')
FileType('T1 MRI Mni ScalpMask', 'T1 MRI Mni Space Tissue Mask')

###################
# transformations #
###################

FileType('Deformation Field of T1 MRI', '4D Volume')
FileType('DefField T1 MRI from Mni to Native', 'Deformation Field of T1 MRI')
FileType('DefField T1 MRI from Native to Mni', 'Deformation Field of T1 MRI')

FileType('MatlabFile of Deformation Field of T1 MRI', 'Matlab SPM file')
FileType('MatDefField T1 MRI from Native to Mni', 'MatlabFile of Deformation Field of T1 MRI')

FileType('MatlabFile of Transformation of T1 MRI', 'Matlab SPM file')
FileType('Mat T1 MRI from Mni to Native', 'MatlabFile of Transformation of T1 MRI')
FileType('Mat T1 MRI from Native to Mni', 'MatlabFile of Transformation of T1 MRI')

##################
#                #
##################


