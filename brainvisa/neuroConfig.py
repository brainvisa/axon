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

import __builtin__
_defaultTranslateFunction = lambda x: x
if not __builtin__.__dict__.has_key( '_t_' ):
  __builtin__.__dict__[ '_t_' ] = _defaultTranslateFunction

import gettext, sys, os, pickle, string, traceback, htmllib, formatter, re, time, socket, atexit
import shutil
from distutils.spawn import find_executable
from soma.wip.application.api import Application
from soma.qtgui.api import ApplicationQtGUI
from brainvisa.configuration.api import initializeConfiguration, readConfiguration, setSPM99Compatibility, DatabaseSettings

from soma.html import htmlEscape
from soma.uuid import Uuid
from soma.minf.api import readMinf, writeMinf
from soma.env import BrainvisaSystemEnv

mainPath = os.path.dirname( sys.argv[0] )

sys.argv[0] = os.path.normpath( os.path.abspath( os.path.join( mainPath, '..', 'bin', 'brainvisa' ) ) )

mainPath = os.path.normpath( os.path.abspath( mainPath ) )
if not os.path.isdir( mainPath ):
  raise RuntimeError( 'Cannot find main BrainVISA directory' )

# Change sys.path[0] because Python follow symlinks when it adds
# this directory and we do not want that to be able to make symlinks
# in build tree to source tree and create the *.pyo or *.pyc in build tree.
basePath = os.path.dirname( mainPath )
sys.path[ 0:0 ] = [ mainPath, os.path.join( basePath, 'python' ) ]

# A bit of cleanup
sys.path = [os.path.normpath( os.path.abspath( p ) ) for p in sys.path]

_commandLine = string.join( map( lambda x: '"'+x+'"', sys.argv ) )
def commandLine():
  return _commandLine

# Identify platform, possible return values are :
#   'windows': Windows
#   'linux': Linux
#   'sunos': SunOS (Solaris)
#   'darwin': Darwin (MacOS X)
#   None: unknown
def findPlatform():
  if sys.platform[:3] == "win":
    return 'windows'
  else:
    if sys.platform.find( 'linux' ) != -1:
      return 'linux'
    if sys.platform.find( 'sunos' ) != -1:
      return 'sunos'
    if sys.platform.find( 'darwin' ) != -1:
      return 'darwin'
    if sys.platform.find( 'irix' ) != -1:
      return 'irix'
    return sys.platform
platform = findPlatform()

if platform == 'windows':
  pathSeparator = ';'
else:
  pathSeparator = ':'

def findInPath( file,
                pathlist = os.environ.get( 'PATH' ).split( pathSeparator ) ):
  for i in pathlist:
    p = os.path.normpath( os.path.abspath( i ) )
    if p:
      if os.path.isdir( p ) and os.path.exists( os.path.join( p, file ) ):
        return p

try:
  from brainvisa.config import fullVersion, shortVersion
except ImportError:
  f = os.path.join( mainPath, 'VERSION' )
  if not os.path.exists( f ):
    f = os.path.join( mainPath, '..', 'VERSION' )
  f = open( f )
  fullVersion = f.readline()[:-1]
  f.close()
  shortVersion = '.'.join( fullVersion.split( '.' )[:2] )

def versionNumber():
  global shortVersion
  return float( shortVersion )

def versionString():
  global fullVersion
  return fullVersion

def versionText():
  return 'BrainVISA ' + versionString()

_sharePath = None
def getSharePath():
  global _sharePath
  if _sharePath is not None:
    return _sharePath
  _sharePath = os.environ.get( 'BRAINVISA_SHARE' )
  if not _sharePath:
    _sharePath = os.environ.get( 'SHFJ_SHARED_PATH' )
    if not _sharePath:
      try:
        from soma.config import DEFAULT_BRAINVISA_SHARE
        _sharePath = DEFAULT_BRAINVISA_SHARE
      except ImportError:
        path = os.getenv( 'PATH' ).split( os.pathsep )
        for p in path:
          if p.endswith( '/bin' ) or p.endswith( '\\bin' ):
            p = p[:len(p)-4]
          elif p.endswith( '/bin/commands-links' ) \
            or p.endswith( '\\bin\\commands-links' ):
            p = p[:len(p)-19]
          p = os.path.join( p, 'share' )
          if os.path.isdir( p ):
            _sharePath = p
            break
    if not _sharePath:
      # empty string rather than None to avoid later re-detection
      _sharePath = ''
  return _sharePath

processesPath = [ os.path.join( mainPath, 'processes' ) ]
typesPath = [ os.path.join( mainPath, 'types' ) ]
for projectName in ( 'axon', 'brainvisa' ):
  sharePath = os.path.join( getSharePath(), projectName + '-' + shortVersion )
  if os.path.isdir( sharePath ):
    break
  # Sources organization
  sharePath = os.path.normpath( os.path.join( mainPath, '..', 'share', projectName + '-' + shortVersion ) )
  if os.path.isdir( sharePath ):
    break
    
iconPath = os.path.join( sharePath, 'icons' )
toolboxesDir = os.path.join( mainPath, 'toolboxes' )

# environment variable holding path for dynamic libraries
def libraryPathEnvironmentVariable():
  if platform == 'windows':
    return 'PATH'
  elif platform == 'darwin':
    return 'DYLD_LIBRARY_PATH'
  return 'LD_LIBRARY_PATH'

# Define system environment variables that have to be passed to external command to restore environment if it have been modified at brainvisa startup
global brainvisaSysEnv
brainvisaSysEnv=BrainvisaSystemEnv()

from brainvisa import shelltools
from soma.minf.api import readMinf

userLevel = 0
sessionID = Uuid()
if platform == "windows":
  temporaryDirectory = os.getenv( 'TEMP' )
  if not temporaryDirectory:
    temporaryDirectory = os.getenv( 'TMP' )
    if not temporaryDirectory:
      temporaryDirectory = 'C:\\WINDOWS\\TEMP'
else:
  temporaryDirectory = '/tmp'

def getDocPath( path, project = '' ) :
  # Language and documentation
  result = os.path.join( getSharePath(), 'doc', project )
  if not os.path.exists( result ):
    result = os.path.normpath( os.path.join( path, '..', 'share', 'doc', project ) )
    if not os.path.exists( result ):
      result = os.path.normpath( os.path.join( path, '..', 'doc' ) )
  
  return result

docPath = mainDocPath = getDocPath( mainPath, projectName + '-' + str( versionNumber() ) )

_languages = []
for l in os.listdir( docPath ):
  if len( l ) == 2 and os.path.isdir( os.path.join( mainDocPath, l ) ):
    _languages.append( l )
for i in ( 'LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG' ):
  language = os.environ.get( i, '' )[ : 2 ]
  if language in _languages: break
if language not in _languages:
  language = 'en'


# debug console defaults
shell = 0

# GUI defaults
gui = True
guiLoaded = False

# server defaults
server = 0

# Create $HOME/.brainvisa directory
homedir = os.getenv( 'HOME' )
if not homedir:
  homedir = ''
  if sys.platform[:3] == 'win':
    homedir = os.getenv( 'USERPROFILE' )
    if not homedir:
      homedir = os.getenv( 'HOMEPATH' )
      if not homedir:
        homedir = '\\'
      drive = os.getenv( 'HOMEDRIVE' )
      if not drive:
        drive = os.getenv( 'SystemDrive' )
        if not drive:
          drive = os.getenv( 'SystemRoot' )
          if not drive:
            drive = os.getenv( 'windir' )
          if drive and len( drive ) >= 2:
            drive = drive[ :2 ]
          else:
            drive = ''
      homedir = drive + homedir
homeBrainVISADir = os.path.join( homedir, '.brainvisa' )
if not os.path.exists( homeBrainVISADir ):
  os.mkdir( homeBrainVISADir )
  
# Other defaults
anatomistExecutable = 'anatomist'
if platform == 'windows':
  # Fix issue in socket communication on windows platform (libc++ seems to not be thread safe)
  anatomistImplementation = 'threaded'
else :
  anatomistImplementation = 'socket'
remoteBrainvisaExecutable = ''

HTMLBrowser = ''
useHTMLBrowser = 0

matlabExecutable = 'matlab'
matlabRelease = None
matlabOptions = '-nosplash -nojvm'
matlabPath = []
tmp = [ os.path.join( homeBrainVISADir, 'matlab' ),
        os.path.join( mainPath, 'matlab' ) ]
while tmp:
  p = tmp.pop()
  if os.path.isdir( p ):
    matlabPath.append( p )
    for x in os.listdir( p ):
      tmp.append( os.path.join( p, x ) )
spmDirectory=''

textEditor = ''
if platform == 'windows':
  texteditors = ( 'notepad', 'write' )
else:
  texteditors = ( 'nedit', 'kedit', 'kwrite', 'xemacs', 'emacs', 'textedit' )
for m in texteditors:
  if find_executable( m ):
    textEditor = m
    break
del m
del texteditors
matlabStartup = []
fileSystemOntologiesPath = [ os.path.join( mainPath, 'hierarchies' ) ]
dataPath= []
clearCacheRequest = False
cacheUpdateRequest = False
logFileName = None
cleanLog=False
profileFileName = ''
mainLog = None
brainvisaSessionLogItem = None
startup=[]
flatHierarchy = os.path.join( mainPath, 'shfjFlatHierarchy.py' )
debugHierarchyScanning = None
debugParametersLinks = None
validationEnabled = False

userEmail = ''
supportEmail = 'support@brainvisa.info'
SMTP_server_name = 'localhost'
if platform == 'windows':
  Rexecutable = 'Rterm.exe'
  Roptions = '--no-restore --no-save --args'
else:
  Rexecutable = 'R'
  Roptions = '--vanilla --slave --args'


_openedDebugFiles = {
  '-': sys.stdout,
  '~': sys.stderr,
}


app = Application( 'brainvisa', versionString() )
app.directories.user = homeBrainVISADir
app.directories.application = sharePath


def openDebugFile( fileName ):
  '''Opens a file to put debug messages in. If '-' is given, sys.stdout is
  returned. If '~' is given, sys.stderr is returned. If this function is
  used several times with the same fileName, the same file object is retured.
  '''
  result = _openedDebugFiles.get( fileName )
  if result is None:
    result = open( fileName, 'w' )
    _openedDebugFiles[ fileName ] = result
  return result

#------------------------------------------------------------------------------
def chooseDatabaseVersionSyncOption(context):
  global databaseVersionSync, userOptionFile
  choice=context.ask("<p><b>Database synchronization between different versions of BrainVISA<b></p><p>Some of your databases have been used with different versions of BrainVISA. They may need to be updated when you switch from one BrainVISA version to another.</p> Please choose the way you want to manage the database synchronization throught BrainVISA versions : <ul><li>Automatic (recommended) : BrainVISA will automatically update your database if you switch from one BrainVISA version to another. </li><li>Manual : Database update is not automatic when switch from one BrainVISA version to another but if you modify a database in one version, you will have to update it with the other version for BrainVISA to take into account the modifications.</li></ul><p>You can change this option later in BrainVISA preferences.</p>", "Automatic (recommended)", "Manual")
  if (choice == 0):
    databaseVersionSync = "auto"
  else:
    databaseVersionSync = "man"
  app = Application()
  app.configuration.brainvisa.databaseVersionSync = databaseVersionSync
  app.configuration.save( userOptionFile)
  return databaseVersionSync
  
#------------------------------------------------------------------------------
def editConfiguration():
  import neuroProcesses, neuroHierarchy
  from brainvisa.data.qtgui.updateDatabases import warnUserAboutDatabasesToUpdate
  global userLevel, dataPath, newDatabases, HTMLBrowser, textEditor, language, docPath
  configuration = Application().configuration
  appGUI = ApplicationQtGUI()
  if appGUI.edit( configuration, live=False ):
    configuration.save( userOptionFile )
    setSPM99Compatibility( configuration.brainvisa.SPM )
  newDataPath = [ x for x in dataPath if hasattr( x, 'builtin' ) and x.builtin ]
  for fso in configuration.databases.fso:
    if fso.selected and fso.directory and os.path.exists(fso.directory):
      newDataPath.append( DatabaseSettings( fso.directory ) )
  if dataPath != newDataPath:
    dataPath = newDataPath
    if newDatabases:
      neuroHierarchy.openDatabases()
    else:
      neuroHierarchy.readHierarchies()
    warnUserAboutDatabasesToUpdate()
  if userLevel != configuration.brainvisa.userLevel:
    userLevel = configuration.brainvisa.userLevel
    neuroProcesses.updateProcesses()
  HTMLBrowser=configuration.brainvisa.htmlBrowser
  if configuration.brainvisa.textEditor:
    textEditor=configuration.brainvisa.textEditor
  if language != configuration.brainvisa.language \
    and configuration.brainvisa.language is not None:
    language=configuration.brainvisa.language
    print 'mainDocPath:', mainDocPath
    print 'language:', language
    docPath=os.path.join(mainDocPath, language)
    os.environ[ 'LANGUAGE' ] = language
    neuroProcesses.updateProcesses()


# Parse command Line
# To use -- <Other options> do not use sys.argv but args (returned by getopt)
import getopt
try:
  opts, args = getopt.getopt( sys.argv[1:], "dbfe:c:s:u:h",
                              [ "updateCache", "clearCache",
                                "updateDocumentation", "noMainWindow",
                                "logFile=", "cleanLog", "profile=", "shell", "validation",
                                "debugHierarchy=", "debugLinks=", "oldDatabases", 
                                "help", "setup" ] )
except getopt.GetoptError, msg:
  # print help information and exit:
  sys.stderr.write( "error in options: %s\nUse -h or --help for help\n" % msg )
  sys.exit( 1 )
  showHelp = 1
userProfile = None
openMainWindow = 1
showHelp = 0
newDatabases = True
fastStart = False
global setup
setup=False
for o, a in opts:
  if o in ( "-b", ):
    gui = 0
  elif o in ("-d", ):
    gui = 0
    server = 1
  elif o in ( "-e", ):
    startup.append( "execfile('" + a + "')" )
  elif o in ( "-c", ):
    startup.append( a )
  elif o in ( "-s", ):
    m = re.match( r'(.*)\((.*[^)])\)?', a )
    if m:
      startup.append( 'showProcess("' + m.group(1) + '",' + m.group(2) + ')' )
    else:
      startup.append( 'showProcess("' + a + '")' )
  elif o in ( "-u", ):
    userProfile = a
  elif o in ( "-f", ):
    fastStart = True
  elif o in ( "--updateCache", ):
    cacheUpdateRequest = True
  elif o in ( "--clearCache", ):
    clearCacheRequest = True
  elif o in ( "--updateDocumentation", ):
    startup.append( 'generateHTMLProcessesDocumentation()' )
  elif o in ( "--noMainWindow", ):
    openMainWindow = 0
  elif o in ( "--logFile", ):
    logFileName = a
  elif o in ("--cleanLog",):
    cleanLog=True
  elif o in ( "--profile", ):
    profileFileName = a
  elif o in ( "--shell", ):
    shell = 1
  elif o in ( "--debugHierarchy", ):
    debugHierarchyScanning = openDebugFile( a )
  elif o in ( "--debugLinks", ):
    debugParametersLinks = openDebugFile( a )
  elif o in ( "--validation", ):
    validationEnabled = True
  elif o in ( "--oldDatabases", ):
    newDatabases = False
  elif o in ( "-h", "--help" ):
    showHelp = 1
  elif o in ( "--setup" ):
    setup = True

# Print help
if showHelp == 1:
  print '''
Usage: brainvisa [ <BrainVISA options> ] [ -- <other options> ]

<BrainVISA options> are interpreted by BrainVISA, <other options> are
passed to BrainVISA scripts (technically, they are kept in sys.argv).

BrainVISA options:
  -d                      Run as a processes server, in daemon mode.
  -b                      Run in batch mode: no graphical interface started by BrainVISA.
  -f                      EXPERIMENTAL: Try to speed-up BrainVISA startup by caching processes reading.
  -e <file>               Execute <file> which must be a valid Python script.
  -c <command>            Execute <command> which must be a valid Python command.
  -s <process_id>         Open a process window. Equivalent to -c 'showProcess("<process_id>")'.
  -u <profile>            Select a user profile.
  --oldDatabases          Use old obsolete implementation of database system.
  --updateDocumentation   Generate HTML documentation pages.
  --noMainWindow          Do not open the process selection window.
  --logFile <file>        Change log file name (default=$HOME/.brainvisa/brainvisa.log)
  --cleanLog              Clean home brainvisa directory by removing session information (current_runs.minf) and all log files (brainvisa*.log)
  --shell                 Run BrainVISA in a IPython shell, if IPython is
                          available (see http://ipython.scipy.org).
  -h  or --help           Show help message in batch mode and exit.

Notes:
  Multiple -e and -c commands are executed in the order they are given after
  all initialization steps are done (options parsing, databases and processes
  parsing, etc.).
'''
  sys.exit()

if newDatabases:
  if clearCacheRequest:
    print >> sys.stderr, 'WARNING: --clearCache is obsolete\n'
  if cacheUpdateRequest:
    print >> sys.stderr, 'WARNING: --updateCache is obsolete\n'
  if setup:
    startup.append( 'from neuroHierarchy import databases\nfrom neuroProcesses import defaultContext\ndb = list( databases.iterDatabases() )[0]\ndb.clear(context=defaultContext())\ndb.update(context=defaultContext())' )
elif cacheUpdateRequest:
  startup.append( 'cacheUpdate()' )

# get information about possibly existing runs of Brainvisa and add information about current
class RunsInfo:
  def __init__(self):
    global logFileName
    global cleanLog
    self.file=os.path.join(homeBrainVISADir, "current_runs.minf")
    if cleanLog:
      try:
        if os.path.exists(self.file):
          os.remove(self.file)
        for f in os.listdir(homeBrainVISADir):
          if f.startswith("brainvisa") and (f.endswith(".log") or f.endswith(".log~")):
            os.remove(os.path.join(homeBrainVISADir, f) )
      except Exception, e:
        print "Fail cleaning log files:"
        print e
    self.currentRun=1
    self.timeout=604800 # 7 days in seconds
    self.runs={}
    self.count=0
    self.expiredRuns={}
    try:
      if os.path.exists( self.file ):
        self.runs, self.count = readMinf(self.file)
      currentTime = time.time() 
      
      # register information for current run
      infos={ 'host' : socket.gethostname(), 'pid' : os.getpid(), 'time' : currentTime }
      self.count+=1
      i=1
      while ((i<=self.count+1) and (self.runs.has_key(i))):
        i+=1
      self.currentRun=i
      if logFileName is None:
        if self.currentRun > 1:
          logFileName=os.path.join( homeBrainVISADir, 'brainvisa'+ str(self.currentRun) +'.log' )
        else : 
          logFileName=os.path.join( homeBrainVISADir, 'brainvisa.log' )
      else:
        self.currentRun=logFileName
      infos["logFileName"]=logFileName
      self.runs[self.currentRun]=infos
      self.write()
      atexit.register(self.delete)
    except Exception, e:
      print "Fail to get or set current runs information:"
      print e
      if os.path.exists( self.file ):
        os.remove(self.file)
      
  def delete(self):
    #print "delete run info "
    if os.path.exists( self.file ):
      try:
        self.runs, self.count = readMinf(self.file)
        self.runs.pop(self.currentRun, None)
        self.count=len(self.runs)
        self.write()
      except:
        pass

  def check(self, context):
    if os.path.exists(self.file):
      try:
        self.runs, self.count=readMinf(self.file)
      except Exception, e:
        print >> sys.stderr, 'Cannot read "' + self.file + '":'
        print >> sys.stderr, e
        return
      currentTime = time.time() 
      # check for expired runs
      for n, run in self.runs.items():
        if currentTime-run["time"]>self.timeout:
          self.expiredRuns[n]=run
      if self.expiredRuns:
        choice=0
        if gui: # ask user if brainvisa is not  started in batch mode
          message="The following Brainvisa sessions have expired. Maybe they terminated abnormally : \n"
          for n, run in self.expiredRuns.items():
            logfile=run.get("logFileName", os.path.join( homeBrainVISADir, 'brainvisa'+ str(n) +'.log' ))
            run["logFileName"]=logfile
            message+="\t- Brainvisa process "+str(run["pid"])+" on machine "+str(run["host"])+" started at "+time.ctime(run["time"])+" - log file : "+logfile+"\n"
          message+="\nAre these processes still running?\nIf no, sessions information and associated log file will be deleted.\nif yes, the timeout will be increased."
          currentTime=time.time()
          choice=context.ask(message, "No", "Yes")
        if  choice == 1: # the processes are still running
          for n in self.expiredRuns.keys():
            self.runs[n]["time"]=currentTime
        else:
           for n in self.expiredRuns.keys():
             logfile=self.expiredRuns[n].get("logFileName", None)
             if logfile is not None and os.path.exists(logfile):
              try:
                os.remove(logfile)
                if os.path.exists(logfile+"~"):
                  os.remove(logfile+"~")
              except Exception, e:
                print e
                print "Fail removing log file." 
             del self.runs[n]
           self.count=len(self.runs)
        self.write()

  def write(self):
    writeMinf(self.file, (self.runs, self.count,) )

# Set log file name
if logFileName is None:
  if userProfile:
    logFileName = os.path.join( homeBrainVISADir, 'brainvisa-' + userProfile+'.log' )

runsInfo=RunsInfo()

from brainvisa.toolboxes import readToolboxes, allToolboxes
from neuroException import showException

initializeConfiguration()

readToolboxes( toolboxesDir, homeBrainVISADir )

for toolbox in allToolboxes():
  if os.path.exists( toolbox.initializationFile ):
    try:
      execfile( toolbox.initializationFile )
    except:
      showException()
  if os.path.isdir( toolbox.fsoDir ):
    fileSystemOntologiesPath.append( toolbox.fsoDir )
  if os.path.isdir( toolbox.typesDir ):
    typesPath.append( toolbox.typesDir )

# add brainvisa shared database to the list of available databases
sharedDatabaseFound=False
for p in ( os.path.join( getSharePath(), 'brainvisa-share-' + shortVersion ),
           os.path.join( getSharePath(), 'shfj-' + shortVersion ),
           os.path.join( getSharePath(), 'shfj' ) ):
  if os.path.isdir( p ):
    dataPath.insert( 0, DatabaseSettings( p ) )
    dataPath[0].builtin = True # mark as a builtin, non-removable database
    sharedDatabaseFound=True
    break
  
for attr, value in readConfiguration( mainPath, userProfile, homeBrainVISADir ):
  if isinstance( value, list ):
    globals()[ attr ] += value
  else:
    globals()[ attr ] = value


# executes brainvisa startup.py if it exists. there's no use to execute user startup.py here because .brainvisa is a toolbox and its startup.py will be executed with the toolboxes' ones.
if os.path.exists(siteStartupFile):
  startup.append( "execfile(" + repr(siteStartupFile) + ",globals(),{})" )
# Search for hierarchy and types paths in toolboxes
for toolbox in allToolboxes():
  # executes startup.py of each toolbox if it exists
  if os.path.exists( toolbox.startupFile ):
    startup.append( "execfile(" + repr(toolbox.startupFile) + ",globals(),{})" )


# Clean pathes
for p in ( typesPath, dataPath, processesPath, fileSystemOntologiesPath, matlabPath ):
  i = 0
  l = []
  while i < len( p ):
    if p[ i ] in l:
      del p[ i ]
    else:
      l.append( p[ i ] )
      i += 1

# Translations

os.environ[ 'LANGUAGE' ] = language
docPath = os.path.join( docPath, language )
def getDocFile(filename):
  """
  Search doc file in doc path and if not found, in english documentation path.
  """
  global docPath, mainDocPath
  path=os.path.join(docPath, filename)
  if not os.path.exists(path):
    path=os.path.join(mainDocPath, "en", filename)
  return path

class Translator:
  def __init__( self, lang=language ) :
    self.language = lang
    self.translations = self.getTranslations( )

  def translate( self, msg ) :
    return self.translations.get( msg, msg )

  def getTranslations( self ) :
    translations = dict()
    
    for filePath in self.getTranslationFiles( ) :
      file = open( filePath, 'r' )
      translations.update( readMinf( file )[ 0 ] )
      file.close()
      
    return translations
    
  def getTranslationFiles( self ) :
    baseDocPath = getDocPath( mainPath )
    
    for directory in os.listdir( baseDocPath ) :
      file = os.path.join( baseDocPath, directory, self.language, 'translation.minf' )
      
      if os.path.exists( file ):
        yield file

if _t_ is _defaultTranslateFunction:
  try:
    __builtin__.__dict__['_t_'] = Translator().translate
  except Exception, msg:
    __builtin__.__dict__['_t_'] = lambda x: x
    sys.stderr.write( str(msg) + '\n' )


# Pathes for binaries and libraries
# (shouldn't we just test platform != 'windows' ?) (Denis)
#if platform != 'windows':
  #if os.environ.has_key( 'PATH' ):
    #os.environ[ 'PATH' ] = os.path.join( mainPath, 'bin', platform ) + ':' + os.path.join( mainPath, 'bin' ) + ':' + \
                           #os.environ[ 'PATH' ]
  #else:
    #os.environ[ 'PATH' ] = os.path.join( mainPath, 'bin', platform ) + ':' + os.path.join( mainPath, 'bin' )
  #libpathenv = libraryPathEnvironmentVariable()
  #if os.environ.has_key( libpathenv ):
    #os.environ[ libpathenv ] = \
      #os.path.join( mainPath, 'lib', platform ) + ':' + \
      #os.environ[ libpathenv ]
  #else:
    #os.environ[ libpathenv ] = os.path.join( mainPath, 'lib', platform )



# Set matlab options
from brainvisa import matlab
matlab.matlabRelease = matlabRelease
matlab.matlabExecutable = matlabExecutable
matlab.matlabOptions = matlabOptions
matlab.matlabPath = matlabPath
matlab.matlabStartup = matlabStartup



# Setup GUI

_allObjects = {}

def registerObject( object ):
  global _allObjects
  _allObjects[ object ] = object

def unregisterObject( object ):
  global _allObjects
  try:
    del _allObjects[ object ]
    return True
  except:
    return False

def clearObjects():
  global _allObjects
  _allObjects = {}

def environmentHTML():
  content = '<html><body><h1>' + htmlEscape( versionText() ) + '''</h1>
<h2>''' + _t_( 'Python version' ) + '</h2>'+ htmlEscape( sys.version ) + '''
<h2>''' + _t_( 'Command line' ) + '''</h2>
<tt>''' + htmlEscape( commandLine() ) + '''</tt>
<h2>''' + _t_( 'Environment variables' ) + '</h2>'
  for n,v in os.environ.items():
    content += '<tt><em>'+ n + '</em> = ' + htmlEscape( v ) + '</tt><p>'
  content += '<h2>' + _t_( 'BrainVISA options' ) + '</h2>'
  g = globals()
  for n in ( 'platform', 'gui', 'sessionID', 'userProfile', 'siteOptionFile',
             'userOptionFile', 
             'logFileName', 'temporaryDirectory', 'mainPath', 'iconPath', 
             'typesPath', 'dataPath', 'processesPath', 'fileSystemOntologiesPath', 
             'mainDocPath', 'docPath',
             'anatomistExecutable', 'matlabRelease', 'matlabExecutable',
             'matlabOptions', 'matlabPath', 
             #'matlabLibraryDirectory',
             'matlabStartup', 'spmDirectory',
             'logFileName', 'language', 'userLevel',
             'startup', 'supportEmail', 'SMTP_server_name', 'flatHierarchy',
             'textEditor' ):
    content += '<code><em>'+ n + '</em> = ' + htmlEscape( str( g[ n ] ) ) + '</code><p>'
  content += '</body></html>'
  return content
