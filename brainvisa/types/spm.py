# -*- coding: utf-8 -*-
include('builtin')
include('registration')

#--- Templates ----------------------------------
FileType('anatomical Template', 'Template')
FileType('PET Template', 'Template')
FileType('grey probability map', 'Template')

#FileType('Tissue Probability Map Template', 'Template') # never used and same as the one above
FileType('TPM template', '4D Template')
#FileType('SPM TPM template', 'TPM template') # with the attribute '_ontology'='spm', no need for this type

FileType('Dartel template', '4D Template')
FileType('Geodesic shooting template', '4D Template')
FileType('TPM HDW DARTEL template', 'Dartel Template')
#FileType('SPM TPM HDW DARTEL template', 'TPM HDW DARTEL template') # with the attribute '_ontology'='spm', no need for this type

#--- Templates CAT ------------------------------
FileType('CAT Dartel template', 'Dartel template')
FileType('CAT shooting template', 'Geodesic shooting template')

#--- Render SPM type ----------------------------
FileType('SPM Render', 'Matlab SPM file')

#--- Canonical SPM types ------------------------
FileType('SPM single subject', 'anatomical Template')

#--- General SPM types --------------------------
FileType('Transform Softmean to MNI', 'Transformation matrix')
