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

from brainvisa.data.ontology.base import db_entries

# Constants for default attributes values
default_center = "subjects"
default_acquisition = "0"
default_analysis = "0"
default_session = "0"
default_run = "0"
default_graph_version = "3.1"
default_acq_session = '0'

hierarchy = (
    SetWeakAttr('database', '%f'),
    SetContent(
        *(db_entries()),
        'sub-{subject}', SetFileNameStrongAttribute('subject'),
        SetType('Subject'),
        SetContent(
            'ses-{session}',
            SetDefaultAttributeValue('session', default_acq_session),
            SetContent(
                'anat',
                SetContent(
                    'sub-<subject>_ses-<session>_acq-{acquisition}_T1w',
                    SetType('Raw T1 MRI'), SetWeakAttr('modality', 't1mri'),
                    'sub-<subject>_ses-<session>_acq-{acquisition}_T2w',
                    SetType('T2 MRI'), SetWeakAttr('modality', 't2mri'),
                    'sub-<subject>_ses-<session>_run-{run}_T1w',
                    SetType('Raw T1 MRI'), SetWeakAttr('modality', 't1mri'),
                    'sub-<subject>_ses-<session>_run-{run}_T2w',
                    SetType('T2 MRI'), SetWeakAttr('modality', 't2mri'),
                    'sub-<subject>_ses-<session>_run-<run>_*',
                    SetType('Raw T1 MRI'), SetWeakAttr('modality', 't1mri'),
                    'sub-<subject>_ses-<session>_*',
                    SetType('Raw T1 MRI'), SetWeakAttr('modality', 't1mri'),
                    'sub-<subject>_*',
                    SetType('Raw T1 MRI'), SetWeakAttr('modality', 't1mri'),
                ),
                'dwi',
                SetContent(
                    'sub-<subject>_ses-<session>_acq-{acquisition}_dir-{direction}_dwi',
                    SetType('4D Volume'), SetWeakAttr('modality', 'dwimri'),
                ),
                'run-{run}',
                SetContent(
                    'anat',
                    SetContent(
                        'sub-<subject>_ses-<session>_run-<run>_T1w',
                        SetType('Raw T1 MRI'), SetWeakAttr('modality', 't1mri'),
                        'sub-<subject>_ses-<session>_run-<run>_T2w',
                        SetType('T2 MRI'), SetWeakAttr('modality', 't2mri'),
                        'sub-<subject>_ses-<session>_run-<run>_*',
                        SetType('Raw T1 MRI'), SetWeakAttr('modality', 't1mri'),
                        'sub-<subject>_ses-<session>_*',
                        SetType('Raw T1 MRI'), SetWeakAttr('modality', 't1mri'),
                        'sub-<subject>_*',
                        SetType('Raw T1 MRI'), SetWeakAttr('modality', 't1mri'),
                    ),
                    'dwi',
                    SetContent(
                        'sub-<subject>_ses-<session>_{acquisition}_dir-{direction}_dwi',
                        SetType('4D Volume'), SetWeakAttr('modality', 'dwimri'),
                    ),
                ),
            ),
        ),
    ),
)
