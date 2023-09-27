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
import os.path as osp
import distutils.spawn
import glob
from soma.controller import undefined
from soma.wip.application.api import Application


class AxonCapsulConfSynchronizer(object):

    def __init__(self, capsul):
        self.capsul = capsul
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
        ax_conf.SPM.onAttributeChange('spm12_standalone_mcr_path',
                                      self._set_spm_mcr_capsul)
        ax_conf.SPM.onAttributeChange('spm8_standalone_mcr_path',
                                      self._set_spm_mcr_capsul)
        # FSL
        ax_conf.FSL.onAttributeChange('fsldir',
                                      self._set_fsl_directory_capsul)
        # Freesurfer
        ax_conf.FSL.onAttributeChange('freesurfer_home_path',

                                      self._set_fs_home_path_capsul)
        # TODO
        ## Soma-Workflow
        #ax_conf.soma_workflow.onAttributeChange(
            #'somaworkflow_keep_failed_workflows',
            #self._set_swf_keep_failed_wf_capsul)
        #ax_conf.soma_workflow.onAttributeChange(
            #'somaworkflow_keep_succeeded_workflows',
            #self._set_swf_keep_succeeded_wf_capsul)

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
        ax_conf.SPM.removeOnAttributeChange(
            'spm12_standalone_mcr_path', self._set_spm_mcr_capsul)
        ax_conf.SPM.removeOnAttributeChange(
            'spm8_standalone_mcr_path', self._set_spm_mcr_capsul)
        # FSL
        ax_conf.FSL.removeOnAttributeChange(
            'fsldir', self._set_fsl_directory_capsul)
        # Freesurfer
        ax_conf.FSL.removeOnAttributeChange(
            'freesurfer_home_path', self._set_fs_home_path_capsul)
        # TODO
        ## Soma-Workflow
        #ax_conf.soma_workflow.removeOnAttributeChange(
            #'somaworkflow_keep_failed_workflows',
            #self._set_swf_keep_failed_wf_capsul)
        #ax_conf.soma_workflow.removeOnAttributeChange(
            #'somaworkflow_keep_succeeded_workflows',
            #self._set_swf_keep_succeeded_wf_capsul)

    def sync_axon_to_capsul(self):
        '''Copies Axon config options to their CAPSUL equivalent.

        Make sure to have initialized axon config before calling it (typically
        by calling brainvisa.axon.processes.initializeProcesses()).

        The StudyConfig of Capsul has to be initialized with BrainVISAConfig,
        FomConfig, FreeSurferConfig modules.
        '''
        def get_shared_path():
            try:
                from soma import aims
                return aims.carto.Paths.resourceSearchPath()[-1]
            except Exception:
                return '!{dataset.shared.path}'

        capsul = self.capsul
        ax_conf = Application().configuration

        bconf = capsul.config.builtin
        # FOMs
        if bconf.dataset is undefined:
            bconf.dataset = {
                'input': {'metadata_schema': 'brainvisa',
                          'path': ''},
                'output': {'metadata_schema': 'brainvisa',
                           'path': ''},
                'shared': {'metadata_schema': 'brainvisa_shared',
                           'path': get_shared_path()}
            }

        if bconf.dataset.field('shared') is None:
            bconf.dataset.shared = {}
        if not bconf.dataset.shared.metadata_schema:
            bconf.dataset.shared.metadata_schema = 'brainvisa_shared'
        if not bconf.dataset.input.metadata_schema:
            bconf.dataset.input.metadata_schema = 'brainvisa'
        if not bconf.dataset.output.metadata_schema:
            bconf.dataset.output.metadata_schema = 'brainvisa'
        # TODO
        #if not study_config.volumes_format:
            #study_config.volumes_format = 'NIFTI'
        #if not study_config.meshes_format:
            #study_config.meshes_format = 'GIFTI'

        # Matlab
        if ax_conf.matlab.executable:
            # capsul only accepts complete file names
            if ax_conf.matlab.executable \
                    == osp.basename(ax_conf.matlab.executable):
                matlab = \
                    distutils.spawn.find_executable(ax_conf.matlab.executable)
                if matlab:
                    if 'matlab' not in bconf.config_modules:
                        bconf.config_modules.append('matlab')
                    bconf.matlab.matlab = {'executable': matlab}
            else:
                bconf.matlab.matlab = {'executable': ax_conf.matlab.executable}

        # SPM
        if ax_conf.SPM.spm12_standalone_command:
            bconf.spm.spm12_stadalone = {
                'directory': ax_conf.SPM.spm12_standalone_path,
                'standalone': True,
                'version': '12'}
            bconf.matlab.matlab_mcr = {
                'mcr_directory': ax_conf.SPM.spm12_standalone_mcr_path}
        elif ax_conf.SPM.spm8_standalone_command:
            bconf.spm.spm8_stadalone = {
                'directory': ax_conf.SPM.spm8_standalone_path,
                'standalone': True,
                'version': '8'}
            bconf.matlab.matlab_mcr = {
                'mcr_directory': ax_conf.SPM.spm8_standalone_mcr_path}

        # FSL
        if ax_conf.FSL.fsldir:
            bconf.add_module('fsl')
            bconf.fsl.fsl = {
                'setup_script': osp.join(
                    ax_conf.FSL.fsldir, 'etc', 'fslconf', 'fsl.sh'),
                'directory': ax_conf.FSL.fsldir,
                'prefix': ax_conf.FSL.fsl_commands_prefix
            }

        # Freesurfer
        try:
            if ax_conf.freesurfer.freesurfer_home_path:
                bconf.add_module('freesurfer')
                bconf.freesurfer.freesurfer = {
                    'setup_script': osp.join(
                        ax_conf.freesurfer.freesurfer_home_path,
                        'SetUpFreeSurfer.sh'),
                    'subjects_dir': ax_conf.freesurfer.freesurfer_home_path
                }
        except AttributeError:
            # FS toolbox is probably not installed.
            bconf.freesurfer = {}

        # TODO
        ## Soma-Workflow
        #study_config.somaworkflow_keep_failed_workflows \
            #= ax_conf.soma_workflow.somaworkflow_keep_failed_workflows
        #study_config.somaworkflow_keep_succeeded_workflows \
            #= ax_conf.soma_workflow.somaworkflow_keep_succeeded_workflows

    def sync_capsul_to_axon(self):
        '''Copies CAPSUL config options to their Axon equivalent.
        Make sure to have initialized axon config before calling it (typically
        by calling brainvisa.axon.processes.initializeProcesses()).
        '''
        ax_conf = Application().configuration
        capsul = self.capsul
        bconf = capsul.config.builtin

        # matlab
        try:
            if len(bconf.matlab) != 0:
                if bconf.matlab.field('matlab') is None:
                    ax_conf.matlab.executable = ''
                else:
                    ax_conf.matlab.executable = bconf.matlab.matlab.executable
        except Exception as e:
            print('Exception while setting matlab config:', e)

        # SPM
        try:
            if len(bconf.spm) != 0:
                for keyf in bconf.spm.user_fields():
                    key = keyf.name
                    sc = getattr(bconf.spm, key)
                    ver = sc.version
                    if sc.standalone:
                        if bconf.matlab.field('matlab_mcr') is not None:
                            setattr(ax_conf.SPM,
                                    'spm%s_standalone_parh' % ver,
                                    sc.directory)
                            setattr(ax_conf.SPM,
                                    'spm%s_standalone_command' % ver,
                                    osp.join(sc, 'run_spm%s.sh' % ver))
                            setattr(ax_conf.SPM,
                                    'spm%s_standalone_mcr_path' % ver,
                                    bconf.matlab.matlab_mcr.mcr_directory)
                        if not bconf.matlab.matlab_mcr.mcr_directory:
                            mcr = glob.glob(os.path.join(
                                sc.directory, 'mcr', 'v*'))
                            if len(mcr) == 1:
                                setattr(ax_conf.SPM,
                                        'spm%s_standalone_mcr_path' % ver,
                                        mcr[0])
                    else:
                        setattr(ax_conf.SPM, 'spm%s_standalone_path' % ver, '')
                        setattr(ax_conf.SPM, 'spm%s_standalone_command' % ver,
                                '')
                        setattr(ax_conf.SPM, 'spm%s_standalone_mcr_path' % ver,
                                '')
        except Exception as e:
            print('Exception:', e)

        # FSL
        try:
            if len(bconf.fsl) != 0:
                ax_conf.FSL.fsldir = bconf.fsl.fsl.directoty
                ax_conf.FSL.fsl_commands_prefix = bconf.fsl.fsl.prefix
            else:
                ax_conf.FSL.fsldir = None
                ax_conf.FSL.fsl_commands_prefix = ''
        except Exception as e:
            print('Exception:', e)

        # Freesurfer
        try:
            if len(bconf.freesurfer) != 0:
                ax_conf.freesurfer.freesurfer_home_path \
                    = osp.dirname(bconf.freesurfer.freesurfer.setup_script)
            else:
                ax_conf.freesurfer.freesurfer_home_path = None
        except Exception as e:
            print('Exception:', e)

        # TODO
        ## Soma-Workflow
        #ax_conf.soma_workflow.somaworkflow_keep_failed_workflows \
            #= study_config.somaworkflow_keep_failed_workflows
        #ax_conf.soma_workflow.somaworkflow_keep_succeeded_workflows \
            #= study_config.somaworkflow_keep_succeeded_workflows

    def _set_matlab_executable_capsul(self, value):
        capsul = self.capsul
        notdone = True
        bconf = capsul.config.builtin
        if value:
            # capsul only accepts complete file names
            if value == os.path.basename(value):
                matlab = distutils.spawn.find_executable(value)
                if matlab:
                    bconf.matlab.matlab.executable = matlab
                    notdone = False
            else:
                bconf.matlab.matlab.executable = value
                notdone = False
        if notdone and bconf.matlab.field('matlab') is not None:
            bconf.matlab.remove_field('matlab')

    def _set_spm_standalone_command_capsul(self, unused_value):
        capsul = self.capsul
        bconf = capsul.config.builtin
        ax_conf = Application().configuration
        variables = (('spm12_standalone_command', '12'),
                     ('spm8_standalone_command', '8'))
        ver = None
        value = None
        for var, ver in variables:
            value = getattr(ax_conf.SPM, var)
            if value:
                break
        k = 'spm%s_standalone'
        if value:
            if bconf.spm.field(k) is None:
                setattr(bconf.spm, k, {})
            sc = getattr(bconf.spm, k)
            setattr(sc, 'directory', osp.dirname(value))
            setattr(sc, 'version', ver)
        else:
            if bconf.spm.field(k) is not None:
                sc = getattr(bconf.spm, k)
                sc.directory = ''

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

    def _set_spm_mcr_capsul(self, unused_value):
        capsul = self.capsul
        bconf = capsul.config.builtin
        ax_conf = Application().configuration
        variables = (('spm12_standalone_mcr_path', '12'),
                     ('spm8_standalone_mcr_path', '8'))
        ver = None
        value = None
        for var, ver in variables:
            value = getattr(ax_conf.SPM, var)
            if value:
                break
        if value:
            bconf.matlab.matlab_mcr = {'mcr_directory': value}

    def _set_fsl_directory_capsul(self, value):
        capsul = self.capsul
        bconf = capsul.config.builtin
        if value:
            if bconf.fsl.field('fsl') is None:
                bconf.fsl.fsl = {}
            bconf.fsl.fsl.setup_script = os.path.join(
                value, 'etc', 'fslconf', 'fsl.sh')
            bconf.fsl.fsl.directory = value
        else:
            if bconf.fsl.field('fsl') is not None:
                bconf.fsl.remove_field('fsl')

    def _set_fs_home_path_capsul(self, value):
        capsul = self.capsul
        bconf = capsul.config.builtin
        if value:
            if bconf.freesurfer.field('freesurfer') is None:
                bconf.freesurfer.freesurfer = {}
            bconf.freesurfer.freesurfer.setup_script \
                = os.path.join(value, 'SetUpFreeSurfer.sh')

