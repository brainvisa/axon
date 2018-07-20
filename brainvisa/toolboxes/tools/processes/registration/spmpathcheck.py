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
from brainvisa.processes import *
from soma.wip.application.api import Application
from brainvisa.configuration import neuroConfig
from brainvisa.data import neuroHierarchy
from distutils.spawn import find_executable

import os
import platform


name = 'SPM path check'
userLevel = 2

signature = Signature(
)


def initialization(self):
    pass


def inlineGUI(self, values, pview, parent, externalRunButton=False):
    from soma.qt_gui.qt_backend import QtGui
    from brainvisa.processing.qtgui import neuroProcessesGUI
    vb = QtGui.QWidget()
    lay = QtGui.QVBoxLayout(vb)
    lay.addWidget(neuroProcessesGUI.ProcessView.defaultInlineGUI(pview, vb,
                                                                 externalRunButton, None))
    lay.addWidget(QtGui.QLabel(
                  _t_('The SPM paths have not been setup in the configuration.\nCurrently, processes using SPM might not work,\nand the SPM database (normalization templates...) cannot be used.\nThis process can try to detect it and set it in the configuration.\nYou should re-open any process depending on SPM afterwards.'),
                  vb))
    return vb


def checkSPMCommand(context, cmd):
    configuration = Application().configuration
    spm_path = None
    mexe = distutils.spawn.find_executable(
        configuration.matlab.executable)
    if mexe == None:
        context.write('The Matlab executable was not found.')
        return
    matlab_script_diskitem = context.temporary('Matlab Script')
    spm_path_saving_text_file_diskitem = context.temporary('Text File')
    matlab_script_path = matlab_script_diskitem.fullPath()
    matlab_script = '''try
  a = which( \'''' + cmd + '''\' );
  if ~isempty( a )
    try
      ''' + cmd + ''';
    catch me
    end
  end
  spm_path = which( 'spm' );
  f = fopen( ''' + "'" + spm_path_saving_text_file_diskitem.fullPath() + "'" + ''', 'w' );
  fprintf( f, '%s\\n', spm_path );
catch me
end
exit;
'''
    open(matlab_script_path, 'w').write(matlab_script)
    cmd = [ mexe ] + configuration.matlab.options.split(' ') \
        + ['-r', os.path.basename(matlab_script_diskitem.fullName())]
    context.write('Attempt to run the matlab command: ' + repr(cmd))
    # print('running matlab command: ', cmd)
    try:
        context.system(*cmd, cwd=os.path.dirname(matlab_script_path))
    except Exception as e:
        return None
    spm_path = open(
        spm_path_saving_text_file_diskitem.fullPath()).read().strip()
    spm_directory = os.path.dirname(spm_path)
    return spm_directory


def execution(self, context):
    configuration = Application().configuration

    old_spm_configuration = configuration.SPM
    if platform.system() == 'Linux':
        detectPathsForLinuxPlatform(context, configuration)
    elif platform.system() == 'Windows':
        context.warning(
            'The SPM paths auto detect is not yet configured for Windows platform')
    else:
        context.error('Platform used is unvalid for this process')
        return 0

    if configuration.SPM.spm8_standalone_command:
        context.write('\nSetting up SPM templates database')

        # remove previous spm databases if any
        for old_spm_path in [old_spm_configuration.spm5_path,
                             old_spm_configuration.spm8_standalone_path,
                             old_spm_configuration.spm8_path]:
            if old_spm_path:
                if neuroHierarchy.databases.hasDatabase(old_spm_path):
                    neuroHierarchy.databases.remove(old_spm_path)
                    for settings in neuroConfig.dataPath:
                        if settings.directory == old_spm_path:
                            neuroConfig.dataPath.remove(settings)

        dbs = neuroConfig.DatabaseSettings(
            configuration.SPM.spm8_standalone_command)
        dbs.expert_settings.ontology = 'spm'
        dbs.expert_settings.sqliteFileName = ':temporary:'
        dbs.expert_settings.uuid = 'a91fd1bf-48cf-4759-896e-afea136c0549'
        dbs.builtin = True
        neuroConfig.dataPath.insert(1, dbs)
        db = neuroHierarchy.SQLDatabase(dbs.expert_settings.sqliteFileName,
                                        configuration.SPM.spm8_standalone_command,
                                        'spm',
                                        settings=dbs)
        neuroHierarchy.databases.add(db)
        db.clear()
        db.update(context=defaultContext())
        neuroHierarchy.update_soma_workflow_translations()


def detectPathsForLinuxPlatform(context, configuration):
    context.write('Looking for spm12 standalone...')
    try:
        spm12_directory_path, spm12_stand_alone_run_path, spm12_stand_alone_MCR_path = findStandAlonePaths(
            '12')
        configuration.SPM.spm12_standalone_path = spm12_directory_path
        configuration.SPM.spm12_standalone_mcr_path = spm12_stand_alone_MCR_path
        configuration.SPM.spm12_standalone_command = spm12_stand_alone_run_path
    except:
        context.warning('spm12 standalone paths not found')

    context.write('Looking for spm12 by Matlab...')
    try:
        spm_12_path = checkSPMCommand(context, 'spm12')
        configuration.SPM.spm12_path = spm_12_path
    except:
        context.warning('spm12 path not found, maybe Matlab is not available')

    context.write('Looking for spm8 standalone...')
    try:
        spm8_directory_path, spm8_stand_alone_run_path, spm8_stand_alone_MCR_path = findStandAlonePaths(
            '8')
        configuration.SPM.spm8_standalone_path = spm8_directory_path
        configuration.SPM.spm8_standalone_mcr_path = spm8_stand_alone_MCR_path
        configuration.SPM.spm8_standalone_command = spm8_stand_alone_run_path
    except:
        context.warning('spm8 standalone paths not found')

    context.write('Looking for spm8 by Matlab...')
    try:
        spm_8_path = checkSPMCommand(context, 'spm8')
        configuration.SPM.spm8_path = spm_8_path
    except:
        context.warning('spm8 path not found, maybe Matlab is not available')

    context.write('Try to find spm8 wfu pickatlas...')
    if configuration.SPM.spm8_path:
        wfu_pickatlas_path = os.path.join(
            configuration.SPM.spm8_path, 'toolbox/wfu_pickatlas')
        if os.path.exists(wfu_pickatlas_path):
            configuration.SPM.spm8_wfu_pickatlas_path = wfu_pickatlas_path
        else:
            context.warning('spm8 wfu pickatlas, not found')

    context.write('Looking for spm5 by Matlab...')
    try:
        spm_5_path = checkSPMCommand(context, 'spm5')
        configuration.SPM.spm5_path = spm_5_path
    except:
        context.warning('spm5 path not found, maybe Matlab is not available')


def findStandAlonePaths(spm_version):
    if spm_version == '8':
        executable_name = 'spm8'
    elif spm_version == '12':
        executable_name = 'spm12'
    else:
        raise ValueError('Unvalid SPM version')

    # output = check_output('compgen -c | grep "spm"', shell=True, executable='/bin/bash')
    # command_contains_spm_list =  output.splitlines()

    output = soma.subprocess.Popen('compgen -c | grep "spm"', shell=True,
                              stdout=soma.subprocess.PIPE, executable='/bin/bash').communicate()[0]
    command_contains_spm_list = output.split('\n')
    possible_right_command_list = []
    for command_contains_spm in command_contains_spm_list:
        if spm_version in command_contains_spm:
            possible_right_command_list.append(command_contains_spm)

    for possible_right_command in possible_right_command_list:
        executable_path = find_executable(possible_right_command)
        stand_alone_run_path, stand_alone_MCR_path = extractPathFromExecutable(
            executable_path)
        if not None in [stand_alone_run_path, stand_alone_MCR_path]:
            if 'run_' + executable_name + '.sh' in stand_alone_run_path and\
                    'mcr/v713' in stand_alone_MCR_path:
                standalone_directory = os.path.dirname(stand_alone_run_path)
                return standalone_directory, stand_alone_run_path, stand_alone_MCR_path
            else:
                pass  # This command is not the command searches
        else:
            pass  # possible_right_command is not the command searches

    raise Exception('SPM standalone paths not found for SPM' + spm_version)


def extractPathFromExecutable(executable_path):
    shutil.copy(executable_path, '/tmp/SPMPathCheck')
    os.system('sed -i "s/exec /echo /g" /tmp/SPMPathCheck')
    output = soma.subprocess.Popen(
        'sh /tmp/SPMPathCheck', shell=True, stdout=soma.subprocess.PIPE).communicate()[0]
    output_line_list = output.splitlines()
    if len(output_line_list) == 1:
        output_splitted = output.splitlines()[0].split()
        if len(output_splitted) == 2:
            return output_splitted
        else:
            # this command is not the command searches
            return None, None
    else:
        raise Exception(
            'More than 1 line exec found for ' + str(executable_path))
