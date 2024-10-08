# -*- coding: utf-8 -*-
include('base')

insert('{protocol}/{subject}',
       't1mri', SetWeakAttr('modality', 't1mri'),
       SetContent(
       '{acquisition}',
       SetDefaultAttributeValue('acquisition', default_acquisition),
       SetNonMandatoryKeyAttribute('acquisition'),
       SetContent(
       '<subject>', SetType('Raw T1 MRI'), SetPriorityOffset(+1),
       SetWeakAttr('normalized', 'no'),

       'registration', SetContent(),

       '{analysis}',
       SetType('T1 MRI Analysis Directory'),
       SetDefaultAttributeValue('analysis', default_analysis),
       SetNonMandatoryKeyAttribute('analysis'),
       SetContent(),

       ),
       ),
       )
