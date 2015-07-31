# -*- coding: utf-8 -*-
include( 'builtin' )

#--------------- Templates ------------------------
FileType( 'Template', '3D Volume')
FileType( 'anatomical Template', 'Template')
FileType( 'grey probability map', 'Template')
FileType( 'tissue probability map', 'Template')
FileType( 'PET Template', 'Template')
FileType( 'Dartel Template', 'Template')

#-------------- Render SPM type ---------------------
FileType( 'SPM Render', 'Matlab SPM file')

#-------------- Canonical SPM types ---------------------
FileType( 'SPM single subject', '3D Volume')

#-------------- General SPM types ---------------------

FileType( 'Matlab SPM script', 'Any Type', 'Matlab script'  )
FileType( 'Transform Softmean to MNI', 'Transformation matrix' )
