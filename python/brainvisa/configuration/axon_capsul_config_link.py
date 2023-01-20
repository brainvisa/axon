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

from __future__ import print_function

from __future__ import absolute_import
import os
import distutils.spawn
import glob
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
        # Soma-Workflow
        ax_conf.soma_workflow.onAttributeChange(
            'somaworkflow_keep_failed_workflows',
            self._set_swf_keep_failed_wf_capsul)
        ax_conf.soma_workflow.onAttributeChange(
            'somaworkflow_keep_succeeded_workflows',
            self._set_swf_keep_succeeded_wf_capsul)

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
        # Soma-Workflow
        ax_conf.soma_workflow.removeOnAttributeChange(
            'somaworkflow_keep_failed_workflows',
            self._set_swf_keep_failed_wf_capsul)
        ax_conf.soma_workflow.removeOnAttributeChange(
            'somaworkflow_keep_succeeded_workflows',
            self._set_swf_keep_succeeded_wf_capsul)

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
            try:
                study_config.use_matlab = True
            except EnvironmentError:
                pass  # will be False finally.

        # SPM
        use_spm = False
        need_matab = True

        if ax_conf.SPM.spm12_standalone_command:
            study_config.spm_exec = ax_conf.SPM.spm12_standalone_command
            study_config.spm_version = '12'
            use_spm = True
            need_matab = False
        elif ax_conf.SPM.spm8_standalone_command:
            study_config.spm_exec = ax_conf.SPM.spm8_standalone_command
            study_config.spm_version = '8'
            use_spm = True
            need_matab = False
        if ax_conf.SPM.spm12_standalone_path:
            mcr = glob.glob(os.path.join(ax_conf.SPM.spm12_standalone_path,
                                         'mcr', 'v*'))
            if len(mcr) == 1 and os.path.exists(mcr[0]):
                study_config.spm_directory = ax_conf.SPM.spm12_standalone_path
            else:
                mcr = glob.glob(os.path.join(ax_conf.SPM.spm12_standalone_path,
                                             '../..', 'mcr', 'v*'))
                if len(mcr) == 1 and os.path.exists(mcr[0]):
                    study_config.spm_directory \
                        = os.path.dirname(os.path.dirname(
                            ax_conf.SPM.spm12_standalone_path))
            study_config.spm_version = '12'
            use_spm = True
        elif ax_conf.SPM.spm8_standalone_path:
            study_config.spm_directory = ax_conf.SPM.spm8_standalone_path
            study_config.spm_version = '8'
            use_spm = True
        elif ax_conf.SPM.spm12_path:
            study_config.spm_directory = ax_conf.SPM.spm12_path
            study_config.spm_version = '12'
            use_spm = True
        elif ax_conf.SPM.spm8_path:
            study_config.spm_directory = ax_conf.SPM.spm8_path
            study_config.spm_version = '8'
            use_spm = True

        if not need_matab:
            study_config.spm_standalone = True

        if use_spm and (not need_matab or study_config.use_matlab):
            study_config.use_spm = True

        # FSL
        if ax_conf.FSL.fsldir:
            study_config.fsl_config = os.path.join(
                ax_conf.FSL.fsldir, 'etc', 'fslconf', 'fsl.sh')
            study_config.use_fsl = True

        # Freesurfer
        try:
            if ax_conf.freesurfer.freesurfer_home_path:
                study_config.freesurfer_config = os.path.join(
                    ax_conf.freesurfer.freesurfer_home_path,
                    'SetUpFreeSurfer.sh')
                study_config.use_freesurfer = True
        except AttributeError:
            # FS toolbox is probably not installed.
            study_config.use_freesurfer = False

        # Soma-Workflow
        study_config.somaworkflow_keep_failed_workflows \
            = ax_conf.soma_workflow.somaworkflow_keep_failed_workflows
        study_config.somaworkflow_keep_succeeded_workflows \
            = ax_conf.soma_workflow.somaworkflow_keep_succeeded_workflows

    def sync_capsul_to_axon(self):
        '''Copies CAPSUL config options to their Axon equivalent.
        Make sure to have initialized axon config before calling it (typically
        by calling brainvisa.axon.processes.initializeProcesses()).
        '''
        ax_conf = Application().configuration
        study_config = self.study_config

        # matlab
        try:
            if study_config.use_matlab is not Undefined:
                if study_config.matlab_exec is Undefined:
                    ax_conf.matlab.executable = ''
                else:
                    ax_conf.matlab.executable = study_config.matlab_exec
        except Exception as e:
            print('Exception while setting matlab config:', e)

        # SPM
        try:
            if study_config.use_spm:
                if getattr(study_config, 'spm_version', '12') == '12':
                    if study_config.spm_standalone:
                        if study_config.spm_exec is not Undefined:
                            ax_conf.SPM.spm12_standalone_command \
                                = study_config.spm_exec
                        if study_config.spm_directory is not Undefined:
                            ax_conf.SPM.spm12_standalone_path \
                                = study_config.spm_directory
                            mcr = glob.glob(os.path.join(
                                study_config.spm_directory, 'mcr', 'v*'))
                            if len(mcr) == 1:
                                ax_conf.SPM.spm12_standalone_mcr_path = mcr[0]
                    else:
                        ax_conf.SPM.spm12_standalone_path = ''
                        ax_conf.SPM.spm12_standalone_command = ''
                        ax_conf.SPM.spm12_standalone_mcr_path = ''
                    ax_conf.SPM.spm8_standalone_path = ''
                    ax_conf.SPM.spm8_standalone_command = ''
                    ax_conf.SPM.spm8_standalone_mcr_path = ''
                else:
                    if study_config.spm_standalone:
                        if study_config.spm_exec is not Undefined:
                            ax_conf.SPM.spm8_standalone_command \
                                = study_config.spm_exec
                        if study_config.spm_directory is not Undefined:
                            ax_conf.SPM.spm8_standalone_path \
                                = study_config.spm_directory
                            mcr = glob.glob(os.path.join(
                                study_config.spm_directory, 'mcr', 'v*'))
                            if mcr:
                                ax_conf.SPM.spm8_standalone_mcr_path = mcr[0]
                    else:
                        ax_conf.SPM.spm8_standalone_path = ''
                        ax_conf.SPM.spm8_standalone_command = ''
                        ax_conf.SPM.spm8_standalone_mcr_path = ''
                    ax_conf.SPM.spm12_standalone_path = ''
                    ax_conf.SPM.spm12_standalone_command = ''
                    ax_conf.SPM.spm12_standalone_mcr_path = ''
            #else:
                #ax_conf.SPM.spm12_standalone_path = ''
                #ax_conf.SPM.spm12_standalone_command = ''
                #ax_conf.SPM.spm12_standalone_mcr_path = ''
                #ax_conf.SPM.spm8_standalone_path = ''
                #ax_conf.SPM.spm8_standalone_command = ''
                #ax_conf.SPM.spm8_standalone_mcr_path = ''
        except Exception as e:
            print('Exception:', e)

        # FSL
        try:
            if study_config.use_fsl:
                ax_conf.FSL.fsldir = os.path.dirname(os.path.dirname(
                    os.path.dirname(study_config.fsl_config)))
            else:
                ax_conf.FSL.fsldir = None
        except Exception as e:
            print('Exception:', e)

        # Freesurfer
        try:
            if study_config.use_freesurfer:
                ax_conf.freesurfer.freesurfer_home_path \
                    = os.path.dirname(study_config.freesurfer_config)
            else:
                ax_conf.freesurfer.freesurfer_home_path = None
        except Exception as e:
            print('Exception:', e)

        # Soma-Workflow
        ax_conf.soma_workflow.somaworkflow_keep_failed_workflows \
            = study_config.somaworkflow_keep_failed_workflows
        ax_conf.soma_workflow.somaworkflow_keep_succeeded_workflows \
            = study_config.somaworkflow_keep_succeeded_workflows

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
        variables = (('spm12_standalone_command', '12'),
                     ('spm8_standalone_command', '8'))
        ver = None
        value = None
        for var, ver in variables:
            value = getattr(ax_conf.SPM, var)
            if value:
                break
        if value:
            study_config.spm_exec = value
            study_config.spm_standalone = True
            study_config.spm_version = ver
        else:
            study_config.spm_standalone = False
            study_config.spm_exec = ''
            study_config.spm_version = None
        if study_config.spm_standalone \
                or (study_config.use_matlab and study_config.spm_directory):
            study_config.use_spm = True
        else:
            study_config.use_spm = False

    def _set_spm_directory_capsul(self, unused_value):
        study_config = self.study_config
        ax_conf = Application().configuration
        variables = (('spm12_standalone_path', '12'), ('spm12_path', '12'),
                     ('spm8_standalone_path', '8'), ('spm8_path', '8'))
        ver = None
        value = None
        for var, ver in variables:
            value = getattr(ax_conf.SPM, var)
            if value:
                break
        study_config.spm_directory = value
        study_config.spm_version = ver

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

    def _set_swf_keep_failed_wf_capsul(self, value):
        study_config = self.study_config
        study_config.somaworkflow_keep_failed_workflows = value

    def _set_swf_keep_succeeded_wf_capsul(self, value):
        study_config = self.study_config
        study_config.somaworkflow_keep_succeeded_workflows = value
