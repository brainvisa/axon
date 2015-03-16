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

#-------------- General SPM types ---------------------

FileType( 'Matlab SPM script', 'Any Type', 'Matlab script'  )
