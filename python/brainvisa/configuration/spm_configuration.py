__docformat__ = "epytext en"

import os

from soma.configuration import ConfigurationGroup
from soma.signature.api import Signature, FileName

#------------------------------------------------------------------------------


class SPMConfiguration(ConfigurationGroup):
    label = 'SPM'
    icon = 'matlab.png'
    signature = Signature(
        'spm12_path', FileName(directoryOnly=True, readOnly=True), dict(
            defaultValue='', doc='location of SPM 12 installation directory'),
      'spm12_standalone_command', FileName(directoryOnly=False, readOnly=True), dict(
          defaultValue='', doc='location of SPM 12 standalone (compiled) run script'),
      'spm12_standalone_mcr_path', FileName(directoryOnly=True, readOnly=True), dict(
          defaultValue='', doc='location of SPM 12 standalone MCR directory (generally ./spm12-standalone/mcr/v713'),
      'spm12_standalone_path', FileName(directoryOnly=True, readOnly=True), dict(
          defaultValue='', doc='location of SPM 12 standalone directory where the templates directory can be found.(Maybe ./spm12-standalone/spm12_mcr/spm12)'),
      'spm8_path', FileName(directoryOnly=True, readOnly=True), dict(
          defaultValue='', doc='location of SPM 8 installation directory'),
      'spm8_standalone_command', FileName(directoryOnly=False, readOnly=True), dict(
          defaultValue='', doc='location of SPM 8 standalone (compiled) run script'),
      'spm8_standalone_mcr_path', FileName(directoryOnly=True, readOnly=True), dict(
          defaultValue='', doc='location of SPM 8 standalone MCR directory (generally &lt;spm8&gt;/standalone/mcr/v713'),
      'spm8_standalone_path', FileName(directoryOnly=True, readOnly=True), dict(
          defaultValue='', doc='location of SPM 8 standalone directory where the templates directory can be found.'),
      'spm8_wfu_pickatlas_path', FileName(directoryOnly=True, readOnly=True), dict(
          defaultValue='', doc='location of SPM8 WFU PickAtlas directory where the atlases can be found.'),
      'spm5_path', FileName(directoryOnly=True, readOnly=True), dict(
          defaultValue='', doc='location of SPM 5 installation directory'),
    )

    def __init__(self, *args, **kwargs):
        super(SPMConfiguration, self).__init__(*args, **kwargs)
        conda_prefix = os.environ.get('CONDA_PREFIX')
        if conda_prefix:
            spm12_path = os.path.join(conda_prefix, 'spm12')
            if os.path.exists(spm12_path) and not self.spm12_path and not self.spm12_standalone_path:
                self.spm12_standalone_path = spm12_path
                self.spm12_standalone_command = os.path.join(spm12_path, 'run_spm12.sh')
                self.spm12_standalone_mcr_path = os.path.join(conda_prefix, 'MATLAB', 'MATLAB_Runtime', 'v97')
