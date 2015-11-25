# -*- coding: utf-8 -*-
#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL license version 2 under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the
# terms of the CeCILL license version 2 as circulated by CEA, CNRS
# and INRIA at the following URL "http://www.cecill.info".
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license version 2 and that you accept its terms.


# The FSL database allows to use FSL shared data, especially the normalization
# templates.
# The database root is the $FSLDIR/data directory.

templates_contents = (
    'T1', SetType('anatomical Template'),
    SetWeakAttr('normalized', 'yes', 'skull_stripped', 'no', 'Size',
        '2 mm','referential', '19bfee8e-51b1-4d9e-8721-990b9f88b12f',
        'databasename', 'spm'),
    'PET', SetType('PET Template'),
    SetWeakAttr('normalized', 'yes', 'databasename', 'spm'),
)

hierarchy = (
    SetWeakAttr('database', '%f', 'databasename', 'spm'),
    SetPriorityOffset(-10),
    SetContent(
        'tpm', SetContent(
            'grey', SetType('grey probability map')),
        # TMP in SPM12
        'TPM', SetType('tissue probability map'),
        'toolbox', SetContent(
            'Seg', SetContent(
                # TPM in SPM8
                '{template}', SetType('SPM TPM template'),
            'vbm8', SetContent(
                # SPM8
                'Template_{step}_IXI550_{template}', SetType('SPM TPM HDW DARTEL template'),
                SetWeakAttr('normalized', 'yes', 'databasename', 'spm')),
            # this OldNorm is the location of templates in SPM12
            'OldNorm', SetContent(*templates_contents),
            'DARTEL', SetContent(
                # in SPM12, but not exactly the same as in SPM8, this one
                # looks more similar to Template_6_IXI550_MNI152 in SPM8
                'icbm152', SetType('Dartel Template'),
                SetWeakAttr('normalized', 'yes', 'databasename', 'spm')),
        ),# toolbox
        'rend', SetContent(
            'render_{spm_render}', SetType('SPM Render')),
        'canonical', SetContent(
            'single_subj_T1', SetType('SPM single subject')),
        # this templates dir is for SPM8 and SPM5
        'templates', SetContent(*templates_contents),
    )
)

