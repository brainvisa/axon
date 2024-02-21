"""
Several global variables are defined in this module to store **Brainvisa configuration and user options**:

.. py:data:: logFileName

  path of Brainvisa log file where the history of the current session will be saved.


.. py:data:: platform

  linux, windows...

.. py:data:: gui

  false if Brainvisa is in batch mode

.. py:data:: sessionID

.. py:data:: fullVersion
             shortVersion

  Brainvisa version

.. py:data:: userProfile

  if Brainvisa is started with ``-u`` option, the name of the profile stored in this variable is used to create a specific log file for this profile.

.. py:data:: siteOptionFile

  path to a general options file that may be used for all users.

.. py:data:: userOptionFile

  path to user options file.

.. py:data:: logFileName

  path of Brainvisa log file where the history of the current session will be saved.

.. py:data:: runsInfo

  information about the current executions of Brainvisa.

.. py:data:: temporaryDirectory

  directory where temporary files will be written.

.. py:data:: mainPath

  Path of Brainvisa main module.

.. py:data:: sharePath

  Brainvisa share directory

.. py:data:: iconPath

.. py:data:: homeBrainVISADir

  path to Brainvisa home directory (usually *$HOME/.brainvisa*)

.. py:data:: toolboxesDir

  Brainvisa toolboxes directory

.. py:data:: processesPath

  list of paths to Brainvisa processes (outside any toolbox)

.. py:data:: dataPath

  list of DatabaseSettings objects indicating the selected databases.

.. py:data:: typesPath

  list of paths to Brainvisa type files that contain the description of Brainvisa ontology.

.. py:data:: fileSystemOntologiesPath

  list of paths to Brainvisa hierarchy files that contain the rules to organize Brainvisa databases directories.

.. py:data:: debugHierarchyScanning

  stream where debug information about hierarchy rules may be written. Set with ``--debugHierarchy`` option.

.. py:data:: debugParameterLinks

  stream where debug information about parameter links may be written. Set with `--debugLinks` option.

.. py:data:: sharedDatabaseFound

  True if Brainvisa shared database which contain models, templates, referentials, etc, was found.

.. py:data:: mainDocPath

  path to Brainvisa documentation directory

.. py:data:: docPath

  path to Brainvisa documentation directory according to the choosen language.

.. py:data:: brainvisaSysEnv

  :py:class:`soma.env.BrainvisaSystemEnv` - defines system environment variables that have to be passed to external command to restore environment if it have been modified at brainvisa startup

.. py:data:: ignoreValidation

  Do not check vor invalid processes, all are enabled. Set with ``--ignoreValidation``.

.. py:data:: language

  fr or en

.. py:data:: userLevel

  the processes which level is greater than the user level are hidden. Basic = 0, advanced = 1, expert = 2.

.. py:data:: supportEmail
             SMTP_server_name

.. py:data:: textEditor

.. py:data:: HTMLBrowser

.. py:data:: fastStart

  if this mode is enabled, brainvisa starts faster but with less features. Set with ``-f`` or ``-r`` options.

.. py:data:: noToolBox

  if enabled, Brainvisa toolboxes are not loaded. Set with ``--noToolBox``.

.. py:data:: setup

  if enabled, the shared database is updated at startup. Set with ``--setup`` option.

.. py:data:: anatomistExecutable
             anatomistImplementation

.. py:data:: matlabRelease
             matlabExecutable
             matlabOptions
             matlabPath
             matlabStartup

.. py:data:: spmDirectory

.. py:data:: Roptions
             Rexecutable

.. py:data:: profileFileName

  filename where profiling information may be written. Set with ``--profile`` option.

.. py:data:: historyBookDirectory

  path to history_book directory, where processes executions and logs will be saved. Normally it is None so that it is stored in the database of each output data. But in some specific cases (distributed execution of single process) it can be useful to force it.
  May be a list of directories: in that case, history files are duplicated in each of them.
"""

__docformat__ = 'restructuredtext en'

_defaultTranslateFunction = lambda x: x
import six.moves.builtins
if not hasattr(six.moves.builtins, '_t_'):
    six.moves.builtins._t_ = _defaultTranslateFunction

import glob
import sys
import os
import errno
import re
import time
import socket
import tempfile
from soma.wip.application.api import Application
from brainvisa.configuration.api import initializeConfiguration, readConfiguration, DatabaseSettings

from soma.html import htmlEscape
from soma.uuid import Uuid
from soma.minf.api import readMinf, writeMinf
from soma.env import BrainvisaSystemEnv
import brainvisa
import six
import io

from brainvisa.config import fullVersion, shortVersion

exitValue = 0

mainPath = None
casa_build = os.environ.get('CASA_BUILD')
if casa_build:
    for i in [os.path.join(casa_build, 'python', 'brainvisa'), 
              os.path.join(casa_build, 'lib', 'python*', 'site-packages', 'brainvisa')]:
        g = glob.glob(i)
        if g:
            if os.path.exists(os.path.join(g[0], 'toolboxes')):
                mainPath = g[0]
                break
if not mainPath:
    mainPath = os.path.normpath(
        os.path.join(os.path.dirname(brainvisa.__file__), "..", "..", "brainvisa"))

    sys.argv[0] = os.path.normpath(
        os.path.abspath(os.path.join(mainPath, '..', 'bin', 'brainvisa')))

    mainPath = os.path.normpath(os.path.abspath(mainPath))
if not os.path.isdir(mainPath):
    raise RuntimeError('Cannot find main BrainVISA directory')

basePath = os.path.dirname(mainPath)

_commandLine = " ".join(['"' + x + '"' for x in sys.argv])


def commandLine():
    return _commandLine


def findPlatform():
    """Identify system platform, possible return values are :

  * 'windows': Windows
  * 'linux': Linux
  * 'sunos': SunOS (Solaris)
  * 'darwin': Darwin (MacOS X)
  * 'irix': Irix
  * None: unknown
    """
    if sys.platform[:3] == "win":
        return 'windows'
    else:
        if sys.platform.find('linux') != -1:
            return 'linux'
        if sys.platform.find('sunos') != -1:
            return 'sunos'
        if sys.platform.find('darwin') != -1:
            return 'darwin'
        if sys.platform.find('irix') != -1:
            return 'irix'
        return sys.platform
platform = findPlatform()

if platform == 'windows':
    pathSeparator = ';'
else:
    pathSeparator = ':'


def findInPath(file,
               pathlist=os.environ.get('PATH').split(pathSeparator),
               is_dir=False):
    """Returns the directory containing file"""
    for i in pathlist:
        p = os.path.normpath(os.path.abspath(i))
        if p:
            if os.path.isdir(p) and os.path.exists(os.path.join(p, file)):
                if (is_dir and os.path.isdir(os.path.join(p, file))) \
                        or (not is_dir and not os.path.isdir(os.path.join(p, file))):
                    return p


def executableWithPath(file,
                       pathlist=os.environ.get('PATH').split(pathSeparator)):
    if os.path.isabs(file) and os.path.exists(file):
        return file
    path = findInPath(file, pathlist)
    return os.path.join(path, file)


def versionNumber():
    """Returns Brainvisa short version X.Y as a float number"""
    global shortVersion
    return float(shortVersion)


def versionString():
    """Returns Brainvisa full version 'X.Y.Z'"""
    global fullVersion
    return fullVersion


def versionText():
    """Returns the text 'BrainVISA X.Y.Z'"""
    return 'BrainVISA ' + versionString()

_sharePath = None


def getSharePath():
    """Returns BrainVISA share directory path."""
    global _sharePath
    if _sharePath is not None:
        return _sharePath
    try:
        from soma.config import BRAINVISA_SHARE
        _sharePath = BRAINVISA_SHARE
    except ImportError:
        path = os.getenv('PATH').split(os.pathsep)
        for p in path:
            if p.endswith('/bin') or p.endswith('\\bin'):
                p = p[:len(p) - 4]
            elif p.endswith( '/bin/commands-links' ) \
                    or p.endswith('\\bin\\commands-links'):
                p = p[:len(p) - 19]
            p = os.path.join(p, 'share')
            if os.path.isdir(p):
                _sharePath = p
                break
    if not _sharePath or \
        (not os.path.isdir(os.path.join(_sharePath,
                                        'axon-' + shortVersion))
         and not os.path.isdir(os.path.join(_sharePath,
                                            'brainvisa-' + shortVersion))):
        # empty string rather than None to avoid later re-detection
        _sharePath = None
        for projectName in ('axon', 'brainvisa'):
            sharePath = os.path.normpath(os.path.join(os.environ.get('CASA_BUILD', ''), 'share',
                                                      projectName + '-' + shortVersion))
            if os.path.isdir(sharePath):
                _sharePath = os.path.normpath(os.path.join(os.environ.get('CASA_BUILD', ''),
                                                           'share'))
                break
            sharePath = os.path.normpath(os.path.join(mainPath, '..', '..', '..', '..', 'share',
                                                      projectName + '-' + shortVersion))
            if os.path.isdir(sharePath):
                _sharePath = os.path.normpath(os.path.join(mainPath, '..', '..', '..', '..',
                                                           'share'))
                break
    return _sharePath


def initializeOntologyPaths():
    """
    Initializes the global variables :py:data:`typesPath` and :py:data:`fileSystemOntologiesPath`.
    This function is used when toolboxes are reloaded.
    """
    global typesPath
    global fileSystemOntologiesPath
    global mainPath
    typesPath = [os.path.join(mainPath, 'types')]
    fileSystemOntologiesPath = [os.path.join(mainPath, 'hierarchies')]

initializeOntologyPaths()
processesPath = [os.path.join(mainPath, 'processes')]

sharePath = getSharePath()
iconPath = os.path.join(sharePath, 'icons')
uiPath = os.path.join(sharePath, 'ui')
toolboxesDir = os.path.join(mainPath, 'toolboxes')

# environment variable holding path for dynamic libraries


def libraryPathEnvironmentVariable():
    if platform == 'windows':
        return 'PATH'
    elif platform == 'darwin':
        return 'DYLD_LIBRARY_PATH'
    return 'LD_LIBRARY_PATH'

# Define system environment variables that have to be passed to external
# command to restore environment if it have been modified at brainvisa
# startup
brainvisaSysEnv = BrainvisaSystemEnv()
# try to determine if we are in a build tree with system libraries - in that
# case, brainvisaSysEnv should not be altered when calling external commands
if not sys.executable.startswith(basePath):
    # python is not in the BV tree, or it is a system-wide installation
    brainvisaSysEnv.variables = {}

userLevel = 0
sessionID = Uuid()

temporaryDirectory = tempfile.gettempdir()


def getDocPath(path, project=''):
    """Returns the path of the documentation directory of the given project."""
    # Language and documentation
    global sharePath
    result = os.path.join(sharePath, 'doc', project)
    if not os.path.exists(result):
        result = os.path.normpath(
            os.path.join(path, '..', 'share', 'doc', project))
        if not os.path.exists(result):
            result = os.path.normpath(os.path.join(path, '..', 'doc'))

    return result

docPath = mainDocPath = getDocPath(
    mainPath, 'axon-' + str(versionNumber()))

_languages = []
if os.path.exists(docPath):
    for l in os.listdir(docPath):
        if len(l) == 2 and os.path.isdir(os.path.join(mainDocPath, l)):
            _languages.append(l)
else:
    print(
        'WARNING: You should check your BrainVISA installation because the following directory does not exist:',
          repr(docPath), file=sys.stderr)
for i in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
    language = os.environ.get(i, '')[: 2]
    if language in _languages:
        break
if language not in _languages:
    language = 'en'
# variable to ensure the format used for numbers
os.environ["LC_NUMERIC"] = "C"

# debug console defaults
shell = 0

# GUI defaults
gui = True
guiLoaded = False
qtApplication = None

# Create $HOME/.brainvisa directory
homedir = os.getenv('HOME')
if not homedir:
    homedir = ''
    if sys.platform[:3] == 'win':
        homedir = os.getenv('USERPROFILE')
        if not homedir:
            homedir = os.getenv('HOMEPATH')
            if not homedir:
                homedir = '\\'
            drive = os.getenv('HOMEDRIVE')
            if not drive:
                drive = os.getenv('SystemDrive')
                if not drive:
                    drive = os.getenv('SystemRoot')
                    if not drive:
                        drive = os.getenv('windir')
                    if drive and len(drive) >= 2:
                        drive = drive[:2]
                    else:
                        drive = ''
            homedir = drive + homedir

# Try to get BrainVISA user dir from environment variable
homeBrainVISADir = os.getenv('BRAINVISA_USER_DIR')

if not homeBrainVISADir:
    # Uses default BrainVISA home directory
    homeBrainVISADir = os.path.join(homedir, '.brainvisa')

if not os.path.exists(homeBrainVISADir):
    if os.path.lexists(homeBrainVISADir):
        # .brainvisa is a broken symbolic link, likely from
        # /casa/home/.brainvisa to the host home directory; make the target
        # directory
        path_to_make = os.readlink(homeBrainVISADir)
    else:
        path_to_make = homeBrainVISADir
    try:
        os.mkdir(path_to_make)
    except OSError as e:
        if e.errno == errno.EEXIST:
            # filter out 'File exists' exception, if the same dir has been
            # created concurrently by another instance of BrainVisa or another
            # thread
            pass
        else:
            raise

# Other defaults
anatomistExecutable = 'anatomist'
anatomistImplementation = 'threaded'

remoteBrainvisaExecutable = ''

HTMLBrowser = ''
useHTMLBrowser = 0

matlabExecutable = 'matlab'
matlabRelease = None
matlabOptions = '-nosplash -nodisplay'
matlabPath = []
tmp = [os.path.join(homeBrainVISADir, 'matlab'),
       os.path.join(mainPath, 'matlab')]
while tmp:
    p = tmp.pop()
    if os.path.isdir(p):
        matlabPath.append(p)
        for x in os.listdir(p):
            tmp.append(os.path.join(p, x))
spmDirectory = ''

textEditor = ''

matlabStartup = []
dataPath = []
logFileName = None
cleanLog = False
profileFileName = ''
mainLog = None
brainvisaSessionLog = None
brainvisaSessionLogItem = None
startup = []
flatHierarchy = os.path.join(mainPath, 'shfjFlatHierarchy.py')
debugHierarchyScanning = None
debugParametersLinks = None
historyBookDirectory = None

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


app = Application('brainvisa', versionString())
app.directories.user = homeBrainVISADir
app.directories.application = sharePath


def openDebugFile(fileName):
    '''Opens a file to put debug messages in. If '-' is given, sys.stdout is
    returned. If '~' is given, sys.stderr is returned. If this function is
    used several times with the same fileName, the same file object is retured.
    '''
    result = _openedDebugFiles.get(fileName)
    if result is None:
        result = open(fileName, 'a')
        _openedDebugFiles[fileName] = result
    return result

#------------------------------------------------------------------------------


def chooseDatabaseVersionSyncOption(context):
    """
    Asks user to choose a database synchronization mode (Automatic or manual) when a database is used with different versions of Brainvisa.
    The choice is saved in brainvisa options file.

    :param context: The context enables to adapt the interaction with the user according to Brainvisa mode of execution (graphical, batch)

    :returns: the user choice: *auto* for automatic mode, *man* for manual mode.
    """
    global databaseVersionSync, userOptionFile
    choice = context.ask(
        "<p><b>Database synchronization between different versions of BrainVISA<b></p><p>Some of your databases have been used with different versions of BrainVISA. They may need to be updated when you switch from one BrainVISA version to another.</p> Please choose the way you want to manage the database synchronization throught BrainVISA versions : <ul><li>Automatic (recommended) : BrainVISA will automatically update your database if you switch from one BrainVISA version to another. </li><li>Manual : Database update is not automatic when switch from one BrainVISA version to another but if you modify a database in one version, you will have to update it with the other version for BrainVISA to take into account the modifications.</li></ul><p>You can change this option later in BrainVISA preferences.</p>", "Automatic (recommended)", "Manual")
    if (choice == 0):
        databaseVersionSync = "auto"
    else:
        databaseVersionSync = "man"
    app = Application()
    app.configuration.brainvisa.databaseVersionSync = databaseVersionSync
    app.configuration.save(userOptionFile)
    return databaseVersionSync


def stdinLoop():
    """
    Reads Brainvisa commands on stdin and executes them.
    """
    e = []
    for l in sys.stdin:
        if l.startswith('# brainvisa run commands'):
            exec(''.join(e))
            e = []
        else:
            e.append(l)
    if e:
        exec(''.join(e))


# Parse command Line
# To use -- <Other options> do not use sys.argv but args (returned by getopt)


userProfile = None
openMainWindow = 1
showHelp = 0
fastStart = False
global setup
setup = False
noToolBox = False
ignoreValidation = False


def convertCommandLineParameter(i):
    if len(i) > 0 and (i[0] in '[({' or i in ('None', 'True', 'False')):
        try:
            res = eval(i)
        except Exception:
            res = i
    else:
        res = i
    return res

try:
    i = sys.argv.index('-r')
except ValueError:
    i = -1
if i >= 0:
    gui = 0
    fastStart = True
    # noToolBox = True
    logFileName = ''
    startup.append('defaultContext().runProcess' + repr(
        tuple((convertCommandLineParameter(i) for i in sys.argv[i + 1:]))))
else:
    import getopt
    # Ignore Qt -style attribute
    try:
        i = sys.argv.index('-style')
        argv = sys.argv[1:i] + sys.argv[i + 2:]
    except ValueError:
        argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv, "bfe:c:s:u:h",
                                   ["updateDocumentation", "noMainWindow",
                                    "logFile=", "cleanLog", "profile=", "shell",
                                    "debugHierarchy=", "debugLinks=",
                                    "help", "setup", "noToolBox",
                                    "ignoreValidation"])
    except getopt.GetoptError as msg:
        # print help information and exit:
        sys.stderr.write(
            "error in options: %s\nUse -h or --help for help\n" % msg)
        sys.exit(1)
    for o, a in opts:
        if o in ("-b", ):
            gui = 0
        elif o in ("-e", ):
            if a == '-':
                startup.append('neuroConfig.stdinLoop()')
            else:
                startup.append("with open({0!r}, 'rb') as f:\n"
                               "    code = compile(f.read(), {0!r}, 'exec')\n"
                               "six.exec_(code)\n"
                               .format(a))
        elif o in ("-c", ):
            startup.append(a)
        elif o in ("-s", ):
            m = re.match(r'(.*)\((.*[^)])\)?', a)
            if m:
                startup.append(
                    'brainvisa.processing.qt4gui.neuroProcessesGUI.showProcess("' + m.group(1) + '",' + m.group(2) + ')')
            else:
                startup.append(
                    'brainvisa.processing.qt4gui.neuroProcessesGUI.showProcess("' + a + '")')
        elif o in ("-u", ):
            userProfile = a
        elif o in ("-f", ):
            fastStart = True
        elif o in ("--updateDocumentation", ):
            startup.append('generateHTMLProcessesDocumentation()')
        elif o in ("--noMainWindow", ):
            openMainWindow = 0
        elif o in ("--logFile", ):
            logFileName = a
        elif o in ("--cleanLog",):
            cleanLog = True
        elif o in ("--profile", ):
            profileFileName = a
        elif o in ("--shell", ):
            shell = 1
        elif o in ("--debugHierarchy", ):
            debugHierarchyScanning = openDebugFile(a)
        elif o in ("--debugLinks", ):
            debugParametersLinks = openDebugFile(a)
        elif o in ("-h", "--help"):
            showHelp = 1
        elif o in ("--setup"):
            setup = True
        elif o in ("--noToolBox"):
            noToolBox = True
        elif o in ("--ignoreValidation"):
            ignoreValidation = True

# Print(help)
if showHelp == 1:
    print('''
Usage: brainvisa [ <BrainVISA options> ] [ -- <other options> ]

<BrainVISA options> are interpreted by BrainVISA, <other options> are
passed to BrainVISA scripts (technically, they are kept in sys.argv).

BrainVISA options:
  -b                      Run in batch mode: no graphical interface started by BrainVISA.
  -e <file>               Execute <file> which must be a valid Python script.
  -c <command>            Execute <command> which must be a valid Python command.
  --shell                 Run BrainVISA in a IPython shell, if IPython is
                          available (see http://ipython.scipy.org).
  -s <process_id>         Open a process window. Equivalent to -c 'brainvisa.processing.qt4gui.neuroProcessesGUI.showProcess("<process_id>")'.

  -u <profile>            Select a user profile.
  --logFile <file>        Change the log file name (default=$HOME/.brainvisa/brainvisa.log).
  --updateDocumentation   Generate processes and types HTML documentation pages.
  --setup                 Update the shared database at startup.

  --noMainWindow          Do not open Brainvisa main window.
  --noToolBox             Do not load any process nor toolbox.
  --cleanLog              Clean home brainvisa directory by removing session information (current_runs.minf) and all log files (brainvisa*.log)
  --ignoreValidation      Do not check vor invalid processes, all are enabled.
                          (generally not useful)
  -f                      Run in faststart mode: databases are not loaded, processes are loaded from a cache
                          (this mode is used when processes are run in parallel  via Soma-workflow).
  --debugHierarchy <file> Write ontology rules debug information in <file>.
  --debugLinks <file>     Write parameter links debug information in <file>.
  -r <process specs>      Run a process in batch mode, and quit after execution.
                          The process specs can be either a .bvproc filename,
                          or a process name followed by its paremeters.
                          Parameters names cannot be specified in arguments,
                          so they must be provided in the correct order:
                          brainvisa -r process.bvproc
                          brainvisa -r threshold ~/data/irm.ima /tmp/th.nii "greater than" 80
                          This used to be the standard way to run batches, but
                          now it is recommended to use
                          "python -m brainvisa.axon.runprocess",
                          which is lighter, instead, and more flexible on
                          parameters (parameters names are allowed).

  -h  or --help           Show help message in batch mode and exit.

Notes:
  Multiple -e and -c commands are executed in the order they are given after
  all initialization steps are done (options parsing, databases and processes
  parsing, etc.).
''')
    sys.exit()

if setup:
    startup.append(
        'from brainvisa.data.neuroHierarchy import databases\nfrom brainvisa.processes import defaultContext\ndb = list( databases.iterDatabases() )[0]\ndb.clear(context=defaultContext())\ndb.update(context=defaultContext())')

#


class RunsInfo(object):

    """
    This class gets information about possibly existing runs of Brainvisa and adds information about the current one.

    :var string file: information about current runs is stored in *<Brainvisa home dir>/current_runs.minf*
    :var integer currentRun: index of the current execution of Brainvisa (from 1)
    :var float timeout: timeout before asking the user if the execution of Brainvisa is still alive. When Brainvisa fails, the file current_runs.minf may not be cleaned.
    :var dictionary runs: information about current executions of Brainvisa. The information is loaded from the minf file and information about the current execution is added. It is a dictionary *{index -> {host, pid, time, logFileName} }*
    :var integer count: number of executions of Brainvisa
    :var dictonary expiredRuns: dictionary containing the runs for which the timeout is reached. The user will be asked if these runs are still alive. If not, the corresponding log files will be deleted and the *current_runs.minf* file will be cleaned.
    """

    def __init__(self, dontrecordruns=False):
        global logFileName
        global cleanLog
        self.dontrecordruns = dontrecordruns
        if dontrecordruns:
            fd, self.file = tempfile.mkstemp(suffix='.minf',
                                             prefix='bv_current_runs', dir=temporaryDirectory, text=True)
            os.close(fd)
            os.unlink(self.file)
        else:
            self.file = os.path.join(homeBrainVISADir, "current_runs.minf")
        if cleanLog:
            try:
                if os.path.exists(self.file):
                    os.remove(self.file)
                for f in os.listdir(homeBrainVISADir):
                    if f.startswith("brainvisa") and (f.endswith(".log") or f.endswith(".log~")):
                        os.remove(os.path.join(homeBrainVISADir, f))
            except Exception as e:
                print("Fail cleaning log files:")
                print(e)
        self.currentRun = 1
        self.timeout = 604800  # 7 days in seconds
        self.runs = {}
        self.count = 0
        self.expiredRuns = {}
        try:
            if os.path.exists(self.file):
                self.runs, self.count = readMinf(self.file)
            currentTime = time.time()

            # register information for current run
            infos = {
                'host': socket.gethostname(), 'pid': os.getpid(), 'time': currentTime}
            self.count += 1
            i = 1
            while ((i <= self.count + 1) and i in self.runs):
                i += 1
            self.currentRun = i
            if logFileName is None:
                if dontrecordruns:
                    fd, logFileName = tempfile.mkstemp(
                        suffix='.log', prefix='brainvisa',
                      dir=temporaryDirectory, text=True)
                    os.close(fd)
                    os.unlink(logFileName)
                elif self.currentRun > 1:
                    logFileName = os.path.join(
                        homeBrainVISADir, 'brainvisa' + str(self.currentRun) + '.log')
                else:
                    logFileName = os.path.join(
                        homeBrainVISADir, 'brainvisa.log')
            else:
                self.currentRun = logFileName
            infos["logFileName"] = logFileName
            self.runs[self.currentRun] = infos
            self.write()
        except Exception as e:
            print("Fail to get or set current runs information:")
            print(e)
            if os.path.exists(self.file):
                os.remove(self.file)

    def delete(self):
        """
        Removes current run information from the current_runs.minf file.
        """
        if os.path.exists(self.file):
            try:
                if self.dontrecordruns:
                    os.unlink(self.file)
                else:
                    self.runs, self.count = readMinf(self.file)
                    self.runs.pop(self.currentRun, None)
                    self.count = len(self.runs)
                    self.write()
            except Exception:
                pass

    def check(self, context):
        """
        Checks if there are expired runs and asks the user what to do.
        """
        if self.dontrecordruns:
            return  # don't check in this mode
        if os.path.exists(self.file):
            try:
                self.runs, self.count = readMinf(self.file)
            except Exception as e:
                print('Cannot read "' + self.file + '":', file=sys.stderr)
                print(e, file=sys.stderr)
                return
            currentTime = time.time()
            # check for expired runs
            for n, run in self.runs.items():
                if currentTime - run["time"] > self.timeout:
                    self.expiredRuns[n] = run
            if self.expiredRuns:
                choice = 0
                if gui:  # ask user if brainvisa is not  started in batch mode
                    message = "The following Brainvisa sessions have expired. Maybe they terminated abnormally : \n"
                    for n, run in self.expiredRuns.items():
                        logfile = run.get("logFileName", os.path.join(
                            homeBrainVISADir, 'brainvisa' + str(n) + '.log'))
                        run["logFileName"] = logfile
                        message += "\t- Brainvisa process " + str(run["pid"]) + " on machine " + str(
                            run["host"]) + " started at " + time.ctime(run["time"]) + " - log file : " + logfile + "\n"
                    message += "\nAre these processes still running?\nIf no, sessions information and associated log file will be deleted.\nif yes, the timeout will be increased."
                    currentTime = time.time()
                    choice = context.ask(message, "No", "Yes")
                if choice == 1:  # the processes are still running
                    for n in self.expiredRuns.keys():
                        self.runs[n]["time"] = currentTime
                else:
                    for n in self.expiredRuns.keys():
                        logfile = self.expiredRuns[n].get("logFileName", None)
                        if logfile is not None and os.path.exists(logfile):
                            try:
                                os.remove(logfile)
                                if os.path.exists(logfile + "~"):
                                    os.remove(logfile + "~")
                            except Exception as e:
                                print(e)
                                print("Fail removing log file.")
                        del self.runs[n]
                    self.count = len(self.runs)
                self.write()

    def write(self):
        writeMinf(self.file, (self.runs, self.count,))

# Set log file name
if logFileName is None:
    if userProfile:
        logFileName = os.path.join(
            homeBrainVISADir, 'brainvisa-' + userProfile + '.log')

runsInfo = None

initializeConfiguration()

# add brainvisa shared database to the list of available databases
sharedDatabaseFound = False
try:
    import brainvisa_share.config
    bvShareDirectory = brainvisa_share.config.share
except Exception:
    bvShareDirectory = 'brainvisa-share-' + shortVersion
for p in (os.path.join(sharePath, bvShareDirectory),):
    if os.path.isdir(p):
        dataPath.insert(0, DatabaseSettings(p, read_only=True))
        dataPath[0].builtin = True  # mark as a builtin, non-removable database
        sharedDatabaseFound = True
        break


class Translator(object):

    def __init__(self, lang=language):
        self.language = lang
        self.translations = self.getTranslations()

    def translate(self, msg):
        return self.translations.get(msg, msg)

    def getTranslations(self):
        translations = dict()

        for filePath in self.getTranslationFiles():
            file = io.open(filePath, 'r', encoding='utf-8')
            translations.update(readMinf(file)[0])
            file.close()

        return translations

    def getTranslationFiles(self):
        baseDocPath = getDocPath(mainPath)

        for directory in os.listdir(baseDocPath):
            file = os.path.join(
                baseDocPath, directory, self.language, 'translation.minf')

            if os.path.exists(file):
                yield file


def initGlobalVariables():
    global mainPath, userProfile, homeBrainVISADir
    for attr, value in readConfiguration(mainPath, userProfile, homeBrainVISADir):
        if isinstance(value, list):
            globals()[attr] += value
        else:
            globals()[attr] = value

    # Clean pathes
    global typesPath, dataPath, processesPath, fileSystemOntologiesPath, matlabPath
    for p in (typesPath, dataPath, processesPath, fileSystemOntologiesPath, matlabPath):
        i = 0
        l = []
        while i < len(p):
            if p[i] in l:
                del p[i]
            else:
                l.append(p[i])
                i += 1

    # Translations
    global docPath, language, _defaultTranslateFunction
    os.environ['LANGUAGE'] = language
    docPath = os.path.join(docPath, language)
    if _t_ is _defaultTranslateFunction:
        
        try:
            six.moves.builtins.__dict__['_t_'] = Translator(language).translate
        except Exception as msg:
            six.moves.builtins.__dict__['_t_'] = lambda x: x
            sys.stderr.write(str(msg) + '\n')


def get_database_settings(name, selected=True, read_only=False):
    global dataPath
    for dbs in dataPath:
        if dbs.directory == name:
            return dbs
    # not found, create a new one
    return DatabaseSettings(name, selected=selected, read_only=read_only)


def getDocFile(filename):
    """
    Search doc file in doc path and if not found, in english documentation path.
    """
    global docPath, mainDocPath
    path = os.path.join(docPath, filename)
    if not os.path.exists(path):
        path = os.path.join(mainDocPath, "en", filename)
    return path


# Pathes for binaries and libraries
# (shouldn't we just test platform != 'windows' ?) (Denis)
# if platform != 'windows':
    # if 'PATH' in os.environ:
        # os.environ[ 'PATH' ] = os.path.join( mainPath, 'bin', platform ) + ':' + os.path.join( mainPath, 'bin' ) + ':' + \
                             # os.environ[ 'PATH' ]
    # else:
        # os.environ[ 'PATH' ] = os.path.join( mainPath, 'bin', platform ) + ':' + os.path.join( mainPath, 'bin' )
    # libpathenv = libraryPathEnvironmentVariable()
    # if libpathenv in os.environ:
        # os.environ[ libpathenv ] = \
            # os.path.join( mainPath, 'lib', platform ) + ':' + \
            # os.environ[ libpathenv ]
    # else:
        # os.environ[ libpathenv ] = os.path.join( mainPath, 'lib', platform )


# Setup GUI

_allObjects = {}


def registerObject(object):
    global _allObjects
    _allObjects[object] = object


def unregisterObject(object):
    global _allObjects
    try:
        del _allObjects[object]
        return True
    except Exception:
        return False


def clearObjects():
    global _allObjects
    _allObjects = {}


def environmentHTML():
    """
    Returns an HTML page displaying Brainvisa configuration:

    * Brainvisa version
    * Python Version
    * Command line used to start Brainvisa
    * Environment variables
    * Brainvisa options (global variables of this module)

    This page is displayed in Brainvisa log in starting Brainvisa item.
    """
    from brainvisa.toolboxes import allToolboxes
    content = '<html><body><h1>' + htmlEscape( versionText() ) + '''</h1>
<h2>''' + _t_( 'Python version' ) + '</h2>' + htmlEscape( sys.version ) + '''
<h2>''' + _t_( 'Command line' ) + '''</h2>
<tt>''' + htmlEscape( commandLine() ) + '''</tt>
<h2>''' + _t_( 'Toolboxes' ) + '</h2>\n' + \
        '\n'.join((i.name + '<br>' for i in allToolboxes()))
    content += '<h2>' + _t_('Environment variables') + '</h2>'
    for n, v in os.environ.items():
        content += '<tt><em>' + n + '</em> = ' + htmlEscape(v) + '</tt><p>'
    content += '<h2>' + _t_('BrainVISA options') + '</h2>'
    g = globals()
    for n in ('platform', 'gui', 'sessionID', 'userProfile', 'siteOptionFile',
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
              'textEditor'):
        content += '<code><em>' + n + '</em> = ' + \
            htmlEscape(str(g[n])) + '</code><p>'
    content += '</body></html>'
    return content
