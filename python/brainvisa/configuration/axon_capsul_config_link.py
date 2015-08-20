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
import distutils.spawn
from traits.api import Undefined
from brainvisa.configuration import neuroConfig
from soma.wip.application.api import Application


class AxonCapsulConfSynchronizer(object):

    def __init__(self, study_config):
        self.study_config = study_config
        self.install_axon_to_capsul_config_sync()


    def __del__(self):
        self.uninstall_axon_to_capsul_config_sync()


    def install_axon_to_capsul_config_sync(self):
        '''Notifies Axon config options changes and sync them into CAPSUL
        equivalent.

        The StudyConfig of Capsul has to be initialized with BrainVISAConfig,
        FomConfig, FreeSurferConfig modules.
        '''
        ax_conf = Application().configuration

        # Matlab
        ax_conf.matlab.onAttributeChange('executable',
                                         self._set_matlab_executable_capsul)
        # SPM
        ax_conf.SPM.onAttributeChange('spm12_standalone_command',
                                      self._set_spm_standalone_command_capsul)
        ax_conf.SPM.onAttributeChange('spm8_standalone_command',
                                      self._set_spm_standalone_command_capsul)
        ax_conf.SPM.onAttributeChange('spm12_standalone_path',
                                      self._set_spm_directory_capsul)
        ax_conf.SPM.onAttributeChange('spm12_path',
                                      self._set_spm_directory_capsul)
        ax_conf.SPM.onAttributeChange('spm8_standalone_path',
                                      self._set_spm_directory_capsul)
        ax_conf.SPM.onAttributeChange('spm8_path',
                                      self._set_spm_directory_capsul)
        # FSL
        ax_conf.FSL.onAttributeChange('fsldir',
                                      self._set_fsl_directory_capsul)
        # Freesurfer
        ax_conf.FSL.onAttributeChange('freesurfer_home_path',
                                      self._set_fs_home_path_capsul)

    def uninstall_axon_to_capsul_config_sync(self):
        ax_conf = Application().configuration

        # Matlab
        ax_conf.matlab.removeOnAttributeChange(
            'executable', self._set_matlab_executable_capsul)
        # SPM
        ax_conf.SPM.removeOnAttributeChange(
            'spm12_standalone_command',
            self._set_spm_standalone_command_capsul)
        ax_conf.SPM.removeOnAttributeChange(
            'spm8_standalone_command', self._set_spm_standalone_command_capsul)
        ax_conf.SPM.removeOnAttributeChange(
            'spm12_standalone_path', self._set_spm_directory_capsul)
        ax_conf.SPM.removeOnAttributeChange(
            'spm12_path', self._set_spm_directory_capsul)
        ax_conf.SPM.removeOnAttributeChange(
            'spm8_standalone_path', self._set_spm_directory_capsul)
        ax_conf.SPM.removeOnAttributeChange(
            'spm8_path', self._set_spm_directory_capsul)
        # FSL
        ax_conf.FSL.removeOnAttributeChange(
            'fsldir', self._set_fsl_directory_capsul)
        # Freesurfer
        ax_conf.FSL.removeOnAttributeChange(
            'freesurfer_home_path', self._set_fs_home_path_capsul)


    def sync_axon_to_capsul(self):
        '''Copies Axon config options to their CAPSUL equivalent.

        Make sure to have initialized axon config before calling it (typically
        by calling brainvisa.axon.processes.initializeProcesses()).

        The StudyConfig of Capsul has to be initialized with BrainVISAConfig,
        FomConfig, FreeSurferConfig modules.
        '''
        study_config = self.study_config
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
            # capsul only accepts complete file names
            if ax_conf.matlab.executable \
                    == os.path.basename(ax_conf.matlab.executable):
                matlab = \
                    distutils.spawn.find_executable(ax_conf.matlab.executable)
                if matlab:
                    study_config.matlab_exec = matlab
            else:
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


    def sync_capsul_to_axon(self):
        '''Copies CAPSUL config options to their Axon equivalent.
        Make sure to have initialized axon config before calling it (typically
        by calling brainvisa.axon.processes.initializeProcesses()).
        '''
        #ax_conf = Application().configuration
        raise NotImplementedError('To be done later...')


    def _set_matlab_executable_capsul(self, value):
        study_config = self.study_config
        notdone = True
        if value:
            # capsul only accepts complete file names
            if value == os.path.basename(value):
                matlab = distutils.spawn.find_executable(value)
                if matlab:
                    study_config.matlab_exec = matlab
                    study_config.use_matlab = True
                    notdone = False
            else:
                study_config.matlab_exec = value
                study_config.use_matlab = True
                notdone = False
        if notdone:
            study_config.use_matlab = False

    def _set_spm_standalone_command_capsul(self, unused_value):
        study_config = self.study_config
        ax_conf = Application().configuration
        variables = ('spm12_standalone_command', 'spm8_standalone_command')
        for var in variables:
            value = getattr(ax_conf.SPM, var)
            if value:
                break
        if value:
            study_config.spm_exec = value
            study_config.spm_standalone = True
        else:
            study_config.spm_standalone = False
            study_config.spm_exec = ''
        if study_config.spm_standalone \
                or (study_config.use_matlab and study_config.spm_directory):
            study_config.use_spm = True
        else:
            study_config.use_spm = False

    def _set_spm_directory_capsul(self, unused_value):
        study_config = self.study_config
        ax_conf = Application().configuration
        variables = ('spm12_standalone_path', 'spm12_path',
                     'spm8_standalone_path', 'spm8_path')
        for var in variables:
            value = getattr(ax_conf.SPM, var)
            if value:
                break
        study_config.spm_directory = value

    def _set_fsl_directory_capsul(self, value):
        study_config = self.study_config
        if value:
            study_config.fsl_config = os.path.join(
                value, 'etc', 'fslconf', 'fsl.sh')
            study_config.use_fsl = True
        else:
            study_config.fsl_config = Undefined
            study_config.use_fsl = False

    def _set_fs_home_path_capsul(self, value):
        study_config = self.study_config
        if value:
            study_config.freesurfer_config = os.path.join(
                value, 'SetUpFreeSurfer.sh')
            study_config.use_freesurfer = True
        else:
            study_config.freesurfer_config = Undefined
            study_config.use_freesurfer = False

