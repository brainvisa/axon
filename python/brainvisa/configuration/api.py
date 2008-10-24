# -*- coding: iso-8859-1 -*-

#  This software and supporting documentation were developed by
#  NeuroSpin and IFR 49
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


'''
@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

import sys, os, time
from soma.wip.application.api import Application
from brainvisa.configuration.brainvisa_configuration import BrainVISAConfiguration
from brainvisa.configuration.databases_configuration import DatabasesConfiguration, DatabaseSettings
from brainvisa.configuration.anatomist_configuration import AnatomistConfiguration
from brainvisa.configuration.r_configuration import RConfiguration
from brainvisa.configuration.matlab_configuration import MatlabConfiguration
from brainvisa.configuration.distributed_configuration import DistributedBrainVISAConfiguration
from brainvisa.configuration.nmrserver_configuration import NmrServerConfiguration
from soma.wip.configuration import Configuration
from soma.translation import translate as _
from brainvisa import shelltools


#------------------------------------------------------------------------------
def initializeConfiguration():
  configuration = Application().configuration
  configuration.add( 'brainvisa', BrainVISAConfiguration() )
  configuration.add( 'databases',  DatabasesConfiguration() )
  configuration.add( 'anatomist',  AnatomistConfiguration() )
  configuration.add( 'R',  RConfiguration() )
  configuration.add( 'matlab', MatlabConfiguration() )
  configuration.add( 'distributed_execution',
    DistributedBrainVISAConfiguration() )
  configuration.add( 'nmrserver', NmrServerConfiguration() )


#------------------------------------------------------------------------------
def readConfiguration( mainPath, userProfile, homeBrainVISADir ):
  configuration = Application().configuration
  saveUserOptions = False
  siteOptionFile = os.path.join( mainPath, 'options.minf' )
  siteStartupFile = os.path.join( mainPath, 'startup.py' )
  if os.path.exists( siteOptionFile ):
    configuration.load( siteOptionFile )
  else:
    oldSiteOptionFile = siteOptionFile[ :-4 ] + 'py'
    if os.path.exists( oldSiteOptionFile ):
      convertConfiguration30To31( oldSiteOptionFile, siteOptionFile,
        siteStartupFile )
  if os.path.exists( siteOptionFile ):
    configuration.load( siteOptionFile )

  if userProfile is None:
    userOptionFile = os.path.join( homeBrainVISADir, 'options.minf' )
    userStartupFile = os.path.join( os.path.dirname( userOptionFile ),
          'startup.py' )
    if not os.path.exists( userOptionFile ):
      oldUserOptionFile = userOptionFile[ :-4 ] + 'py'
      if os.path.exists( oldUserOptionFile ):
        convertConfiguration30To31( oldUserOptionFile, userOptionFile,
          userStartupFile )
  else:
    userOptionFile = os.path.join( homeBrainVISADir, 'options-' \
      + userProfile + '.minf' )
    userStartupFile = os.path.join( homeBrainVISADir, 'startup-' \
      + userProfile + '.py' )
    if not os.path.exists( userOptionFile ):
      oldUserOptionFile = userOptionFile[ :-4 ] + 'py'
      if os.path.exists( oldUserOptionFile ):
        userStartupFile = os.path.join( homeBrainVISADir, 'startup-' \
          + userProfile + '.minf' )
        convertConfiguration30To31( oldUserOptionFile, userOptionFile,
          userStartupFile )
    if not os.path.exists( userOptionFile ):
      commonUserOptionFile = os.path.join( homeBrainVISADir, 'options.minf' )
      commonUserStartupFile = os.path.join( homeBrainVISADir, 'startup.py' )
      if not os.path.exists( commonUserOptionFile ):
        oldUserOptionFile = commonUserOptionFile[ :-4 ] + 'py'
        if os.path.exists( oldUserOptionFile ):
          convertConfiguration30To31( oldUserOptionFile, commonUserOptionFile,
            commonUserStartupFile )
      if os.path.exists( commonUserOptionFile ):
        shelltools.cp( commonUserOptionFile, userOptionFile )
      if os.path.exists( commonUserStartupFile ):
        shelltools.cp( commonUserStartupFile, userStartupFile )
  
  if os.path.exists( userOptionFile ):
    configuration.load( userOptionFile )
  
  equiv31_30 = {
    'R.executable': 'Rexecutable',
    'R.options': 'Roptions',
    'anatomist.executable': 'anatomistExecutable',
    'brainvisa.htmlBrowser': 'HTMLBrowser',
    'brainvisa.language': 'language',
    'brainvisa.processesPath': 'processesPath',
    'brainvisa.removeTemporary': 'removeTemporary',
    'brainvisa.support.smtpServer': 'SMTP_server_name',
    'brainvisa.support.supportEmail': 'supportEmail',
    'brainvisa.support.userEmail': 'userEmail',
    'brainvisa.temporaryDirectory': 'temporaryDirectory',
    'brainvisa.textEditor': 'textEditor',
    'brainvisa.userLevel': 'userLevel',
    'matlab.executable': 'matlabExecutable',
    'matlab.options': 'matlabOptions',
    'matlab.path': 'matlabPath',
    'matlab.startup': 'matlabStartup',
    'matlab.version': 'matlabRelease'
  }
  
  yield ( 'siteOptionFile', siteOptionFile )
  yield ( 'userOptionFile', userOptionFile )
  yield ( 'siteStartupFile', siteStartupFile )
  yield ( 'userStartupFile', userStartupFile )
  for newKey, oldKey in equiv31_30.iteritems():
    value = configuration
    for attr in newKey.split( '.' ):
      value = getattr( value, attr )
    if value:
      yield ( oldKey, value )
  setSPM99Compatibility( configuration.brainvisa.SPM )
  newDataPath = []
  for fso in configuration.databases.fso:
    if fso.selected:
      newDataPath.append( DatabaseSettings( fso.directory ) )
  yield ( 'dataPath', newDataPath )


#------------------------------------------------------------------------------
def convertConfiguration30To31( sourceFileName, destFileName,
  startupfileName ):
  class Options3_0:
    equiv30_31 = {
      'showSplashScreen': None,
      'userLevel': 'brainvisa.userLevel',
      'language': 'brainvisa.language',
      'processesPath': 'brainvisa.processesPath',
      'fileSystemOntologiesPath': None,
      'startup': None,
      'temporaryDirectory': 'brainvisa.temporaryDirectory',
      'anatomistExecutable': 'anatomist.executable',
      'matlabRelease': 'matlab.version',
      'matlabExecutable': 'matlab.executable',
      'matlabOptions': 'matlab.options',
      'matlabPath': 'matlab.path',
      'matlabStartup': 'matlab.startup',
      'Rexecutable': 'R.executable',
      'Roptions': 'R.options',
      'spmDirectory': None,
      'textEditor': 'brainvisa.textEditor',
      'useHTMLBrowser': None,
      'HTMLBrowser': 'brainvisa.htmlBrowser',
      'removeTemporary': 'brainvisa.removeTemporary',
      'multiconvExecutable': None,
      'dataHandlerExecutable': None,
      'userEmail': 'brainvisa.support.userEmail',
      'supportEmail': 'brainvisa.support.supportEmail',
      'SMTP_server_name': 'brainvisa.support.smtpServer',
    }
    
    def __init__( self, configuration ):
      self.configuration = configuration
    
    def set( self, name, value ):
      dest = self.equiv30_31.get( name )
      if dest is not None:
        dest = dest.split( '.' )
        obj = self.configuration
        for attr in dest[:-1]:
          obj = getattr( obj, attr )
        setattr( obj, dest[ -1 ], obj.signature[ dest[-1] ].type.convertAttribute( obj, dest[ -1 ], value ) )
    
    
    def addDatabaseDirectory( self, directory, hierarchy=None, selected=True ):
      self.configuration.databases.fso.append( DatabasesConfiguration.FileSystemOntology( directory, selected ) ) #DatabasesConfiguration.FileSystemOntology( directory, hierarchy, selected ) )
    
    
    def append( self, name, value ):
      dest = self.equiv30_31.get( name )
      if dest is not None:
        dest = dest.split( '.' )
        obj = self.configuration
        for attr in dest[:-1]:
          obj = getattr( obj, attr )
        getattr( obj, dest[ -1 ] ).append( value )

  def convertStartupCode30to31( fileName, outFileName ):
    if os.path.exists( outFileName ):
      return # already done or manually converted
    beforeOptions = ''
    afterOptions = ''
    if os.path.exists( fileName ):
      file = open( fileName )
      location = 0
      for line in file.xreadlines():
        if location == 0:
          if line == '#------------- DO NOT CHANGE ANYTHING BELOW (INCLUDING THIS LINE) -------------\n':
            location = 1
          else:
            beforeOptions += line
        elif location == 1:
          if line == '#------------- DO NOT CHANGE ANYTHING ABOVE (INCLUDING THIS LINE) -------------\n':
            location = 2
        else:
          afterOptions += line
      file.close()
    if beforeOptions or afterOptions:
      file = open( outFileName, 'w' )
      file.write( '#------------- BrainVISA startup code file -------------'
        '\n' )
      file.write( '#--- automatically converted from 3.0 (options.py) to '
        '3.1\n' )
      file.write( '#--- conversion date: ' + time.asctime() + '\n\n' )
      if beforeOptions:
        file.write( '#--- code used to be done before the automatic part of '
          'options.py\n' )
        file.write( beforeOptions )
      if afterOptions:
        file.write( '\n#--- code done after standard options\n' )
        file.write( afterOptions )


  configuration = Configuration()
  configuration.add( 'brainvisa', BrainVISAConfiguration() )
  configuration.add( 'databases',  DatabasesConfiguration() )
  configuration.add( 'anatomist',  AnatomistConfiguration() )
  configuration.add( 'R',  RConfiguration() )
  configuration.add( 'matlab', MatlabConfiguration() )
  
  from neuroConfig import versionNumber
  d = { 'options': Options3_0( configuration ), 'versionNumber': versionNumber }
  try:
    execfile( sourceFileName, d, d )
  except:
    import traceback
    print >> sys.stderr, _( 'Cannot execute "%s":' % sourceFileName )
    traceback.print_exc()
    return
  try:
    configuration.save( destFileName )
  except:
    print >> sys.stderr, _( 'Cannot convert "%(old)s" to "%(new)s"' % {
                          'old': sourceFileName, 'new': destFileName } )
    #raise
  convertStartupCode30to31( sourceFileName, startupfileName )


#------------------------------------------------------------------------------
def setSPM99Compatibility( values ):
  import neuroConfig
  aimsrc = os.path.join( neuroConfig.homedir, '.aimsrc' )
  if values.SPM99_compatibility or ( not values.radiological_orientation ) or os.path.exists( aimsrc ):
    aimsrc = open( aimsrc, 'w' )
    print >> aimsrc, "attributes = {\n  '__syntax__' : 'aims_settings',"
    if values.SPM99_compatibility:
      print >> aimsrc, "  'spm_input_spm2_normalization' : 0,\n" \
                       "  'spm_output_spm2_normalization' : 0,\n" \
                       "  'spm_output_4d_volumes' : 0,\n" \
                       "  'nifti_output_4d_volumes' : 0,"
    else:
      print >> aimsrc, "  'spm_input_spm2_normalization' : 1,\n" \
                      "  'spm_output_spm2_normalization' : 1,\n" \
                      "  'spm_output_4d_volumes' : 1,\n" \
                      "  'nifti_output_4d_volumes' : 1,"
    if values.radiological_orientation:
      print >> aimsrc, "  'spm_input_radio_convention' : 1,\n" \
                       "  'spm_output_radio_convention' : 1,"
    else:
      print >> aimsrc, "  'spm_input_radio_convention' : 0,\n" \
                       "  'spm_output_radio_convention' : 0,"
    print >> aimsrc, "}"
    aimsrc.close()
