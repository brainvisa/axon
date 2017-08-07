# -*- coding: utf-8 -*-
include('builtin')
include('registration')

#--------------- Templates ------------------------
FileType( 'Template', '3D Volume')
FileType( 'anatomical Template', 'Template')
FileType( 'grey probability map', 'Template')
FileType( 'tissue probability map', 'Template')
FileType( 'PET Template', 'Template')
FileType( 'Dartel Template', 'Template')#False : Dartel template is 4D Volume!! (mickael L)


FileType('TPM template', '4D Volume')
FileType('SPM TPM template', 'TPM template')
FileType('TPM HDW DARTEL template', '4D Volume')
FileType('SPM TPM HDW DARTEL template', 'TPM HDW DARTEL template')

#-------------- Render SPM type ---------------------
FileType( 'SPM Render', 'Matlab SPM file')

#-------------- Canonical SPM types ---------------------
FileType( 'SPM single subject', 'anatomical Template')

#-------------- General SPM types ---------------------

FileType( 'Matlab SPM script', 'Any Type', 'Matlab script'  )
FileType( 'Transform Softmean to MNI', 'Transformation matrix' )
