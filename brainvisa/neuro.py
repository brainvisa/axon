#!/usr/bin/env python

# Copyright CEA and IFR 49 (2000-2005)
#
#  This software and supporting documentation were developed by
#      CEA/DSV/SHFJ and IFR 49
#      4 place du General Leclerc
#      91401 Orsay cedex
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

import sys, os, signal, atexit, time
  
if len( sys.argv ) > 1 and sys.platform[:6] == 'darwin' and sys.argv[1][:5] == '-psn_':
  # MacOS calls me with this strange argument, I don't want it.
  del sys.argv[1]

try:
  sys.setdefaultencoding( 'iso-8859-1' )
except AttributeError:
  pass
import site

USE_QT4=False
if USE_QT4:
  import PyQt4

from soma.wip.application.api import Application
from soma.signature.api import Choice as SomaChoice
import neuroConfig
import Server
from brainvisa.data import temporary
from qtgui.neuroConfigGUI import *
import neuroLog
from neuroException import *
from neuroData import *
from neuroProcesses import *
from neuroHierarchy import *
from qtgui.neuroDataGUI import *
from qtgui.neuroProcessesGUI import *
import neuroHierarchy
from neuroHierarchyGUI import *
from backwardCompatibleQt import *
from minfExtensions import initializeMinfExtensions
from brainvisa.data.qtgui.updateDatabases import warnUserAboutDatabasesToUpdate

def system_exit_handler( number, frame ):
  sys.exit()

def qt_exit_handler( number, frame ):
  qApp.exit()

# Ctrl + C is linked to sys.exit() until Qt event loop is entered
signal.signal( signal.SIGINT, system_exit_handler )


class EventFilter( QObject ):
  def eventFilter( self, o, e ):
    try:
      if getattr( EventFilter, 'pixIcon', None ) is None:
        setattr( EventFilter, 'pixIcon', QPixmap( os.path.join( iconPath, 'icon.png' ) ) )
      if e.type() == QEvent.Show and o.parent() is None and o.icon() is None:
        o.setIcon( self.pixIcon )
    except:
      pass
    return False
  
  
def setQtApplicationStyle( newStyle ):
  if not newStyle:
    newStyle = app.configuration.brainvisa.signature[ 'gui_style' ].defaultValue
  qApp.setStyle( newStyle )


def main():
  if neuroConfig.server:
    # make the program into a daemon
    Server.daemonize()
    
#  sys.excepthook = exceptionHook

  # InitializationoptionFile
  try:
    temporary.initializeTemporaryFiles( 
      defaultTemporaryDirectory = neuroConfig.temporaryDirectory )
    atexit.register( temporary.manager.__del__ )
    
    neuroLog.initializeLog()
    atexit.register( neuroLog.closeMainLog )
    initializeData()

    if neuroConfig.validationEnabled:
      # Looking for main validation directory
      try:
        v = os.path.dirname( sys.argv[0] )
        v = v[ v.rfind( '-' )+1: ]
        p4 = os.environ.get( 'P4', '' )
        # Looking for validation directory
        for d in ( 'validation-' + v, 'validation-main', ):
          d = os.path.join( p4, d, 'brainvisa' )
          if os.path.isdir( d ): break
        else:
          raise RuntimeError( 'Cannot find validation directory' )
        neuroConfig.processesPath.append( os.path.join( d, 'processes' ) )
      except:
        d = None
        neuroConfig.validationEnabled = False
        showException( afterError=': validation mode disabled' )

    if neuroConfig.newDatabases:
      initializeDatabases()
    else:
      initializeHierarchy()
    initializeProcesses()
    initializeDataGUI()
    if not neuroConfig.newDatabases:
      initializeHierarchyGUI()
    initializeProcessesGUI()
    atexit.register( neuroConfig.clearObjects )

    # Logging BrainVISA environment
    neuroConfig.brainvisaSessionLogItem = neuroLog.log( 'starting BrainVISA', 
      html=neuroConfig.environmentHTML(), icon='brainvisa_small.png' )

    # write information about brainvisa log file
    defaultContext().write("The log file for this session is "+str(neuroConfig.logFileName))
    # check for expired run informatiib supporton : ask user what to do
    neuroConfig.runsInfo.check(defaultContext())

    #neuroConfig.runsInfo.check(defaultContext())

    if neuroConfig.validationEnabled:
      neuroLog.log( 'Validation mode', html='Validation mode enabled. Databases are going to be modified.', icon='warning.png' )

    readTypes()
    if neuroConfig.newDatabases:
      openDatabases()
    else:
      readHierarchies( neuroConfig.clearCacheRequest )
    readProcesses( neuroConfig.processesPath )
    warnUserAboutDatabasesToUpdate()
  except:
    raise
    showException()

  if neuroConfig.validationEnabled:
    defaultContext().warning( 'Validation mode enabled. Databases are going to be modified.' )
    try:
      if d:
        neuroConfig.validationDirectory = d
        execfile( os.path.join( d, 'initBrainVISAValidation.py' ) )
    except:
      showException()
  
  if neuroConfig.gui:
    showMainWindow()
  
  localsStartup = {}
  for f in neuroConfig.startup:
    try:
      if isinstance( f, basestring ):
        exec f in globals(), localsStartup
      else:
        f()
    except:
      showException()
  del localsStartup
  
  if neuroConfig.server:
    Server.startServer()


initializeMinfExtensions()

if neuroConfig.gui:
  # QApplication.setColorSpec( QApplication.ManyColor )
  neuroConfig.qtApplication = QApplication(
    [ sys.argv[0], '-name', versionText() ] + sys.argv[1:] )

  # Styles list must be read only after QApplication instanciation
  # otherwise it is incomplete (even after instanciation).
  app = Application()
  app.configuration.brainvisa.signature[ 'gui_style' ].type = SomaChoice( *[ ('<system default>', None ) ] + [unicode(i) for i in QStyleFactory.keys()] )
  if USE_QT4:
    app.configuration.brainvisa.signature[ 'gui_style' ].defaultValue = unicode( qApp.style().objectName() )
  else: 
    app.configuration.brainvisa.signature[ 'gui_style' ].defaultValue = unicode( qApp.style().name() )
  app.configuration.brainvisa.onAttributeChange( 'gui_style', setQtApplicationStyle )
  setQtApplicationStyle( app.configuration.brainvisa.gui_style )

# The following lines are used to put a BrainVISA icon to all
# the top-level windows that do not have one. But it crashes due
# to a PyQt bug. This bug has been reported and fixed in earlier
# versions.
  global _globalEventFilter
  _globalEventFilter = EventFilter()
  qApp.installEventFilter( _globalEventFilter )
  if USE_QT4:
    QDir.addSearchPath("", os.path.join( neuroConfig.docPath, 'processes' ))
  else:
    QMimeSourceFactory.defaultFactory().addFilePath( \
    os.path.join( neuroConfig.docPath, 'processes' ) )
  neuroConfig.guiLoaded = True
else:
  neuroConfig.qtApplication = QApplication( sys.argv, QApplication.Tty )

if neuroConfig.profileFileName:
  import profile, pstats
  profile.run( 'main()', profileFileName )
  p=pstats.Stats( profileFileName )
  p.sort_stats( 'time' ).print_stats(10)
  p.sort_stats( 'time' ).print_callers(10)
else:
  main()

if neuroConfig.gui:
  neuroConfig.qtApplication.connect( neuroConfig.qtApplication,\
                                     SIGNAL( 'lastWindowClosed ()' ),\
                                     sys.exit )
  # Ctrl + C is now linked to qApp.exit()
  signal.signal( signal.SIGINT, qt_exit_handler )
  if not neuroConfig.shell:
    if USE_QT4:
      neuroConfig.qtApplication.exec_()
    else:
      neuroConfig.qtApplication.exec_loop()

if neuroConfig.shell:
  try:
    import IPython
    if USE_QT4:
      ipshell = IPython.Shell.IPShellQt4( [ '-q4thread' ] )
    else:
      ipshell = IPython.Shell.IPShellQt( [ '-qthread' ] )
    ipshell.mainloop()
  except ImportError:
    print >> sys.stderr, 'IPython not found - Shell mode disabled'
    neuroConfig.shell = 0




if neuroConfig.newDatabases:
  neuroHierarchy.databases.currentThreadCleanup()
