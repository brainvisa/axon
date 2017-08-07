# -*- coding: utf-8 -*-
include( 'builtin' )

FileType('Dicoms T1 MRI', 'Any Type') # does not work with T1 MRI or 4D volume instead of Any Type
FileType('T1 MRI Nat reseted', 'T1 MRI') # original name was reseted Nat T1 MRI
FileType('T1 MRI Bias Corrected', 'T1 MRI')
FileType('T1 MRI Mni', 'T1 MRI')
FileType('T1 MRI Mni Bias Corrected', 'T1 MRI')
FileType('T1 MRI affine Mni Bias Corrected', 'T1 MRI')

FileType('T1 MRI Analysis Directory', 'Directory')

#################
# segmentations #
#################
#PVE image
FileType('OLD T1 MRI Partial Volume Estimation', '4D Volume')
FileType('T1 MRI Nat Partial Volume Estimation', 'OLD T1 MRI Partial Volume Estimation')
FileType('T1 MRI Mni Partial Volume Estimation', 'OLD T1 MRI Partial Volume Estimation')
FileType('T1 MRI Mni Partial Volume Estimation Dartel imported', 'OLD T1 MRI Partial Volume Estimation')

# Tissue Probability Map : in native, mni space and pet space

FileType('OLD T1 MRI Tissue Probability Map', '4D Volume')

FileType('T1 MRI Native Space Tissue Probability Map', 'OLD T1 MRI Tissue Probability Map')
FileType('T1 MRI Nat GreyProba', 'T1 MRI Native Space Tissue Probability Map')
FileType('T1 MRI Nat WhiteProba', 'T1 MRI Native Space Tissue Probability Map')
FileType('T1 MRI Nat CSFProba', 'T1 MRI Native Space Tissue Probability Map')
FileType('T1 MRI Nat SkullProba', 'T1 MRI Native Space Tissue Probability Map')
FileType('T1 MRI Nat ScalpProba', 'T1 MRI Native Space Tissue Probability Map')

FileType('T1 MRI Mni Space Tissue Probability Map', 'OLD T1 MRI Tissue Probability Map')
FileType('T1 MRI Mni GreyProba', 'T1 MRI Mni Space Tissue Probability Map')
FileType('T1 MRI Mni WhiteProba', 'T1 MRI Mni Space Tissue Probability Map')
FileType('T1 MRI Mni CSFProba', 'T1 MRI Mni Space Tissue Probability Map')
FileType('T1 MRI Mni SkullProba', 'T1 MRI Mni Space Tissue Probability Map')
FileType('T1 MRI Mni ScalpProba', 'T1 MRI Mni Space Tissue Probability Map')

FileType('T1 MRI Mni Space Dartel imported Tissue Probability Map', 'OLD T1 MRI Tissue Probability Map')
FileType('T1 MRI Mni GreyProba Dartel imported', 'T1 MRI Mni Space Dartel imported Tissue Probability Map')
FileType('T1 MRI Mni WhiteProba Dartel imported', 'T1 MRI Mni Space Dartel imported Tissue Probability Map')
FileType('T1 MRI Mni CSFProba Dartel imported', 'T1 MRI Mni Space Dartel imported Tissue Probability Map')
FileType('T1 MRI Mni SkullProba Dartel imported', 'T1 MRI Mni Space Dartel imported Tissue Probability Map')
FileType('T1 MRI Mni ScalpProba Dartel imported', 'T1 MRI Mni Space Dartel imported Tissue Probability Map')

FileType('T1 MRI PetSpc Space Tissue Probability Map', 'OLD T1 MRI Tissue Probability Map')
FileType('T1 MRI PetSpc GreyProba', 'T1 MRI PetSpc Space Tissue Probability Map')
FileType('T1 MRI PetSpc WhiteProba', 'T1 MRI PetSpc Space Tissue Probability Map')
FileType('T1 MRI PetSpc CSFProba', 'T1 MRI PetSpc Space Tissue Probability Map')
FileType('T1 MRI PetSpc SkullProba', 'T1 MRI PetSpc Space Tissue Probability Map')
FileType('T1 MRI PetSpc ScalpProba', 'T1 MRI PetSpc Space Tissue Probability Map')
# Tissue Mask : in native, mni space and pet space

FileType('T1 MRI Tissue Mask', '4D Volume')

FileType('T1 MRI Native Space Tissue Mask', 'T1 MRI Tissue Mask')
FileType('T1 MRI Nat GreyMask', 'T1 MRI Native Space Tissue Mask')
FileType('T1 MRI Nat WhiteMask', 'T1 MRI Native Space Tissue Mask')
FileType('T1 MRI Nat CSFMask', 'T1 MRI Native Space Tissue Mask')
FileType('T1 MRI Nat SkullMask', 'T1 MRI Native Space Tissue Mask')
FileType('T1 MRI Nat ScalpMask', 'T1 MRI Native Space Tissue Mask')
FileType('T1 MRI Nat BrainMask', 'T1 MRI Native Space Tissue Mask')

FileType('T1 MRI Mni Space Tissue Mask', 'T1 MRI Tissue Mask')
FileType('T1 MRI Mni GreyMask', 'T1 MRI Mni Space Tissue Mask')
FileType('T1 MRI Mni WhiteMask', 'T1 MRI Mni Space Tissue Mask')
FileType('T1 MRI Mni CSFMask', 'T1 MRI Mni Space Tissue Mask')
FileType('T1 MRI Mni SKullMask', 'T1 MRI Mni Space Tissue Mask')
FileType('T1 MRI Mni ScalpMask', 'T1 MRI Mni Space Tissue Mask')

FileType('T1 MRI PetSpc Space Tissue Mask', 'T1 MRI Tissue Mask')
FileType('T1 MRI PetSpc GreyMask', 'T1 MRI PetSpc Space Tissue Mask')
FileType('T1 MRI PetSpc WhiteMask', 'T1 MRI PetSpc Space Tissue Mask')

###################
# transformations #
###################

FileType('Deformation Field of T1 MRI', '4D Volume')
FileType('DefField T1 MRI from Mni to Native', 'Deformation Field of T1 MRI')
FileType('DefField T1 MRI from Native to Mni', 'Deformation Field of T1 MRI')

FileType('DefField T1 MRI from Mni to PetSpc', 'Deformation Field of T1 MRI')
FileType('DefField T1 MRI from PetSpc to Mni', 'Deformation Field of T1 MRI')

FileType('MatlabFile of Deformation Field of T1 MRI', 'Matlab SPM file')
FileType('MatDefField T1 MRI from Native to Mni', 'MatlabFile of Deformation Field of T1 MRI')

FileType('MatlabFile of Transformation of T1 MRI', 'Matlab SPM file')
FileType('Mat T1 MRI from Mni to Native', 'MatlabFile of Transformation of T1 MRI')
FileType('OLD Mat T1 MRI from Mni to Native', 'MatlabFile of Transformation of T1 MRI')
FileType('Mat T1 MRI from Native to Mni', 'MatlabFile of Transformation of T1 MRI')
FileType('OLD Mat T1 MRI from Native to Mni', 'MatlabFile of Transformation of T1 MRI')

FileType('JacobianDeterminant', '4D Volume')

#DARTEL
FileType('T1 MRI Nat GreyProba DARTEL warped', '4D Volume')
FileType('T1 MRI Nat WhiteProba DARTEL warped', '4D Volume')
FileType('DARTEL created template', '4D Volume')
FileType('DARTEL flow field', '4D Volume')
FileType('DARTEL analysis directory', 'Directory')

##################
#                #
##################
FileType('Brain Matter Volumes', 'Text file')


