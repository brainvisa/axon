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

from brainvisa.processes import *
from soma.wip.application.api import Application
from brainvisa.configuration import neuroConfig
from brainvisa.data import neuroHierarchy

import platform


name = 'SPM path check'
userLevel = 2

signature = Signature(
)


def initialization( self ):
  pass

def inlineGUI( self, values, pview, parent, externalRunButton=False ):
  from PyQt4 import QtGui
  from brainvisa.processing.qtgui import neuroProcessesGUI
  vb = QtGui.QWidget()
  lay = QtGui.QVBoxLayout( vb )
  lay.addWidget( neuroProcessesGUI.ProcessView.defaultInlineGUI( pview, vb,
    externalRunButton, None ) )
  lay.addWidget( QtGui.QLabel( \
    _t_( 'The SPM paths have not been setup in the configuration.\nCurrently, processes using SPM might not work,\nand the SPM database (normalization templates...) cannot be used.\nThis process can try to detect it and set it in the configuration.\nYou should re-open any process depending on SPM afterwards.' ),
    vb ) )
  return vb

def checkSPMCommand( context, cmd ):
  configuration = Application().configuration
  spm_path = None
  mexe = distutils.spawn.find_executable( \
    configuration.matlab.executable )
  if mexe == None:
    context.write('The Matlab executable was not found.')
    return
  matlab_script_diskitem = context.temporary( 'Matlab Script' )
  spm_path_saving_text_file_diskitem = context.temporary( 'Text File' )
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
  open( matlab_script_path, 'w' ).write( matlab_script )
  pd = os.getcwd()
  os.chdir( os.path.dirname( matlab_script_path ) )
  cmd = [ mexe ] + configuration.matlab.options.split(' ') \
    + [ '-r', os.path.basename( matlab_script_diskitem.fullName() ) ]
  context.write('Attempt to run the matlab command: ' + repr(cmd))
  #print 'running matlab command: ', cmd
  try:
    context.system( *cmd )
  except Exception, e:
    return None
  os.chdir( pd )
  spm_path = open( spm_path_saving_text_file_diskitem.fullPath() ).read().strip()
  spm_directory = os.path.dirname( spm_path )
  return spm_directory


def execution( self, context ):
  configuration = Application().configuration

  old_spm_configuration = configuration.SPM
  if platform.system() == 'Linux':
    detectPathsForLinuxPlatform(context, configuration)
  elif platform.system() == 'Windows':
    context.warning('The SPM paths auto detect is not yet configured for Windows platform')
  else:
    context.error('Platform used is unvalid for this process')
    return 0

  if configuration.SPM.spm8_standalone_command:
    context.write( '\nSetting up SPM templates database' )

    # remove previous spm databases if any
    for old_spm_path in [old_spm_configuration.spm5_path,
                         old_spm_configuration.spm8_standalone_path,
                         old_spm_configuration.spm8_path]:
      if old_spm_path:
        if neuroHierarchy.databases.hasDatabase( old_spm_path ):
          neuroHierarchy.databases.remove( old_spm_path )
          for settings in neuroConfig.dataPath:
            if settings.directory == old_spm_path:
              neuroConfig.dataPath.remove(settings)


    dbs = neuroConfig.DatabaseSettings( configuration.SPM.spm8_standalone_command )
    dbs.expert_settings.ontology = 'spm'
    dbs.expert_settings.sqliteFileName = ':temporary:'
    dbs.expert_settings.uuid = 'a91fd1bf-48cf-4759-896e-afea136c0549'
    dbs.builtin = True
    neuroConfig.dataPath.insert( 1, dbs )
    db = neuroHierarchy.SQLDatabase( dbs.expert_settings.sqliteFileName,
                                    configuration.SPM.spm8_standalone_command,
                                    'spm',
                                    settings=dbs )
    neuroHierarchy.databases.add( db )
    db.clear()
    db.update( context=defaultContext() )
    neuroHierarchy.update_soma_workflow_translations()


from distutils.spawn import find_executable
import re
import subprocess


def detectPathsForLinuxPlatform(context, configuration):
  context.write('Looking for spm12 standalone...')
  try:
    spm12_directory_path, spm12_stand_alone_run_path, spm12_stand_alone_MCR_path = findStandAlonePaths('spm12')
    configuration.SPM.spm12_standalone_path = spm12_directory_path
    configuration.SPM.spm12_standalone_mcr_path = spm12_stand_alone_MCR_path
    configuration.SPM.spm12_standalone_command = spm12_stand_alone_run_path
  except:
    context.warning('spm12 standalone paths not found')

  context.write('Looking for spm12 by Matlab...')
  try:
    spm_12_path = checkSPMCommand( context, 'spm12' )
    configuration.SPM.spm12_path = spm_12_path
  except:
    context.warning('spm12 path not found, maybe Matlab is not available')


  context.write('Looking for spm8 standalone...')
  try:
    spm8_directory_path, spm8_stand_alone_run_path, spm8_stand_alone_MCR_path = findStandAlonePaths('spm8')
    configuration.SPM.spm8_standalone_path = spm8_directory_path
    configuration.SPM.spm8_standalone_mcr_path = spm8_stand_alone_MCR_path
    configuration.SPM.spm8_standalone_command = spm8_stand_alone_run_path
  except:
    context.warning('spm8 standalone paths not found')

  context.write('Looking for spm8 by Matlab...')
  try:
    spm_8_path = checkSPMCommand( context, 'spm8' )
    configuration.SPM.spm8_path = spm_8_path
  except:
    context.warning('spm8 path not found, maybe Matlab is not available')

  context.write('Try to find spm8 wfu pickatlas...')
  if configuration.SPM.spm8_path:
    wfu_pickatlas_path = os.path.join(configuration.SPM.spm8_path, 'toolbox/wfu_pickatlas')
    if os.path.exists(wfu_pickatlas_path):
      configuration.SPM.spm8_wfu_pickatlas_path = wfu_pickatlas_path
    else:
      context.warning('spm8 wfu pickatlas, not found')


  context.write('Looking for spm5 by Matlab...')
  try:
    spm_5_path = checkSPMCommand( context, 'spm5' )
    configuration.SPM.spm5_path = spm_5_path
  except:
    context.warning('spm5 path not found, maybe Matlab is not available')

def findStandAlonePaths(executable_name):
  executable_path = find_executable(executable_name)
  executable_file = open(executable_path, 'r')
  text_in_executable = executable_file.read()
  executable_file.close()

  main_directory_path = extractMainDirectoryPath(text_in_executable, executable_name)
  stand_alone_run_path = findStandAloneRunPath(main_directory_path, executable_name)
  stand_alone_MCR_path = findStandAloneMCRPath(main_directory_path)

  return main_directory_path, stand_alone_run_path, stand_alone_MCR_path


def extractMainDirectoryPath(text_in_executable, executable_name):
  #find the source directory
  #This method can be optimize... its aims is to find the main directory in executable script as :
  #SPM8_STANDALONE_HOME=/i2bm/local/spm8-standalone ==> neurospin
  #export SPM8=/coconut/applis/src/spm8 ==> LIB
  match_object = re.search('/[/A-z0-9_\-]*/' + executable_name + '[A-z0-9_\-]*', text_in_executable)
  if match_object:
    sentence = match_object.group(0)
  else:
    raise Exception('Unvalid regular expression pattern')
  if os.path.isdir(sentence):
    return sentence
  else:
    return os.path.dirname(sentence)

def findStandAloneRunPath(main_directory_path, executable_name):
  #find file looks like : run_spm12.sh"
  executable_file_name = 'run_' + executable_name + '.sh'
  find_line = subprocess.Popen('find ' + main_directory_path + '/ -name ' + executable_file_name, stdout=subprocess.PIPE, shell=True).communicate()[0]
  return find_line.replace('\n', '')

def findStandAloneMCRPath(main_directory_path):
  #find the line looks like : "$/mcr/v713"
  find_line = subprocess.Popen('find ' + main_directory_path + '/ -name "v713" -type d', stdout=subprocess.PIPE, shell=True).communicate()[0]
  return find_line.replace('\n', '')