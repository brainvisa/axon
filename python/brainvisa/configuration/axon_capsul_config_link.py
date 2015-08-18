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

import os
from brainvisa.configuration import neuroConfig
from soma.wip.application.api import Application


def axon_to_capsul_config_sync(study_config):
    '''Copies Axon config options to their CAPSUL equivalent.

    Make sure to have initialized axon config before calling it (typically
    by calling brainvisa.axon.processes.initializeProcesses()).

    The StudyConfig of Capsul has to be initialized with BrainVISAConfig,
    FomConfig, FreeSurferConfig modules.
    '''
    ax_conf = Application().configuration

    # soma-workflow
    study_config.use_soma_workflow = True  # always. that's it.

    # FOMs
    if not study_config.shared_fom:
        study_config.shared_fom = 'shared-brainvisa-1.0'
    if not study_config.input_fom:
        study_config.input_fom = 'morphologist-auto-1.0'
    if not study_config.output_fom:
        study_config.output_fom = 'morphologist-auto-1.0'
    if not study_config.volumes_format:
        study_config.volumes_format = 'NIFTI'
    if not study_config.meshes_format:
        study_config.meshes_format = 'GIFTI'
    study_config.use_fom = True

    # Matlab
    if ax_conf.matlab.executable:
        study_config.matlab_exec = ax_conf.matlab.executable
        study_config.use_matlab = True

    # SPM
    use_spm = False
    need_matab = True

    if ax_conf.SPM.spm12_standalone_command:
        study_config.spm_exec = ax_conf.SPM.spm12_standalone_command
        study_config.spm_standalone = True
        use_spm = True
        need_matab = False
    elif ax_conf.SPM.spm8_standalone_command:
        study_config.spm_exec = ax_conf.SPM.spm8_standalone_command
        study_config.spm_standalone = True
        use_spm = True
        need_matab = False
    if ax_conf.SPM.spm12_standalone_path:
        study_config.spm_directory = ax_conf.SPM.spm12_standalone_path
        use_spm = True
    elif ax_conf.SPM.spm8_standalone_path:
        study_config.spm_directory = ax_conf.SPM.spm8_standalone_path
        use_spm = True
    elif ax_conf.SPM.spm12_path:
        study_config.spm_directory = ax_conf.SPM.spm12_path
        use_spm = True
    elif ax_conf.SPM.spm8_path:
        study_config.spm_directory = ax_conf.SPM.spm8_path
        use_spm = True

    if use_spm and (not need_matab or study_config.use_matlab):
        study_config.use_spm = True

    # FSL
    if ax_conf.FSL.fsldir:
        study_config.fsl_config = os.path.join(
            ax_conf.FSL.fsldir, 'etc', 'fslconf', 'fsl.sh')
        study_config.use_fsl = True

    # Freesurfer
    if ax_conf.freesurfer.freesurfer_home_path:
      study_config.freesurfer_config = os.path.join(
          ax_conf.freesurfer.freesurfer_home_path, 'SetUpFreeSurfer.sh')
      study_config.use_freesurfer = True


def capsul_to_axon_config_sync(study_config):
    '''Copies CAPSUL config options to their Axon equivalent.
    Make sure to have initialized axon config before calling it (typically
    by calling brainvisa.axon.processes.initializeProcesses()).
    '''
    ax_conf = Application().configuration
    raise NotImplementedError('To be done later...')

