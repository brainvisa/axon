#!/usr/bin/env python
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
"""
This is the main module of BrainVISA. It is executed by ``brainvisa`` command to start the software.
It loads a lot of other modules and initializes BrainVISA application according to the options given at startup. 
"""
__docformat__ = 'restructuredtext en'

import sys, os, signal, atexit, time

# Force QString API version in order to be compatible with recent version
# of enthought.traits.ui (3.6 for instance)
import sip
PYQT_API_VERSION = 2
qt_api = [ "QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl",
"QVariant" ]
for qt_class in qt_api:
    sip.setapi( qt_class, PYQT_API_VERSION )
del qt_api, qt_class

if len( sys.argv ) > 1 and sys.platform[:6] == 'darwin' and sys.argv[1][:5] == '-psn_':
  # MacOS calls me with this strange argument, I don't want it.
  del sys.argv[1]

try:
  from soma.config import MAJOR_QT_VERSION
  USE_QT4 = MAJOR_QT_VERSION == 4
except ImportError:
  # in non-cmake version, soma.config does not exist.
  # Then we are forced to use the gui to check Qt
  import soma.qtgui.api as qg
  if qg.QtGUI == getattr(qg, "Qt4GUI", None):
    USE_QT4 = True
  else:
    USE_QT4 = False
  del qg
if USE_QT4:
  import PyQt4

from soma.wip.application.api import Application
from soma.signature.api import Choice as SomaChoice
from brainvisa.configuration import neuroConfig
from brainvisa.toolboxes import readToolboxes, allToolboxes
from brainvisa.data import temporary
from brainvisa.configuration.qtgui import neuroConfigGUI
from brainvisa.processing import neuroLog
from brainvisa.processing.neuroException import *
from brainvisa.data.neuroData import *
from brainvisa.processes import *
import brainvisa.processes
from brainvisa.data.neuroHierarchy import *
from brainvisa.data.qtgui.neuroDataGUI import *
from brainvisa.processing.qtgui.neuroProcessesGUI import *
from brainvisa.data import neuroHierarchy
from brainvisa.processing.qtgui.backwardCompatibleQt import *
from brainvisa.data.minfExtensions import initializeMinfExtensions
from brainvisa.data.qtgui.updateDatabases import warnUserAboutDatabasesToUpdate

def system_exit_handler( number, frame ):
  """The callback associated to SIGINT signal (CTRL+C) when there is no Qt Application."""
  sys.exit( 1 )

def qt_exit_handler( number, frame ):
  """The callback associated to SIGINT signal (CTRL+C) when a Qt Application is running."""
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
  """
  This function sets the graphical style of the Qt application with the style given in parameter. 
  If the parameter is None, the style given in gui_style brainvisa option is applied.
  """
  if not newStyle:
    newStyle = app.configuration.brainvisa.signature[ 'gui_style' ].defaultValue
  qApp.setStyle( newStyle )


def main():
  """
  This function initializes BrainVISA components: log, databases, processes, graphical user interface. 
  """
  import brainvisa.processing.qtgui
  p = os.path.join( os.path.dirname( brainvisa.processing.qtgui.__file__ ),
    'protection_against_qt3' )
  if os.path.exists( p ):
    sys.path.insert( 0, p )
  #  sys.excepthook = exceptionHook
  # InitializationoptionFile
  try:

    from brainvisa import axon
    axon.initializeProcesses()

    neuroHierarchy.update_soma_workflow_translations()

    nbDatabases=len(neuroHierarchy.databases._databases)
    if neuroConfig.sharedDatabaseFound:
      nbDatabases-=1
    elif  not neuroConfig.fastStart:
      showWarning("BrainVISA Shared database was not found. It is needed for many processes. Check your Brainvisa installation.")
    if not neuroConfig.setup:
      if neuroConfig.gui:
        warnUserAboutDatabasesToUpdate()
        if ( nbDatabases == 0 and getattr( neuroConfig, 'databasesWarning', False ) ):
          choice=defaultContext().ask("<p><b>Welcome to BrainVISA !</b></p><p>You have not selected any database yet.</p><p>It is strongly advisable to use a database to process data with BrainVISA. Indeed, some important features are not available when you are using data outside a database. To add a new database, go to <i>databases tab</i> in the <i>preferences window</i> and click on the <i>add button</i>.</p>",  "Open preferences", "Cancel", "Don't show this warning next time")
          if (choice == 0):
            neuroConfigGUI.editConfiguration()
          elif (choice == 2):
            app = Application()
            app.configuration.brainvisa.databasesWarning = False
            app.configuration.save( neuroConfig.userOptionFile)
      else:
        toUpdate = [i for i in neuroHierarchy.databases.iterDatabases() if getattr( i, '_mustBeUpdated', False )]
        if toUpdate:
          print >> sys.stderr, _t_( 'WARNING' )+':', _t_( 'Some ontologies (i.e. databases organization) have been modified but are used by currently selected databases. To take this modification into account, it is necessary to update the following databases:' )
          for i in toUpdate:
            print >> sys.stderr, ' ', i.name
        if ( nbDatabases == 0 and getattr( neuroConfig, 'databasesWarning', False ) ):
          print >> sys.stderr, _t_( 'WARNING' )+':', _t_( 'You have not selected any database yet. It is strongly advisable to use a database to process data with BrainVISA. Indeed, some important features are not available where you are using data outside a database. To add a new database, go to databases tab in the preferences window and click on the add button.' )
  except:
    raise
    showException()

  # this is obsolete and doesn't do anything any longer
  #if neuroConfig.validationEnabled:
    #neuroLog.log( 'Validation mode', html='Validation mode enabled. Databases are going to be modified.', icon='warning.png' )
    #defaultContext().warning( 'Validation mode enabled. Databases are going to be modified.' )
    #try:
      #if d:
        #neuroConfig.validationDirectory = d
        #execfile( os.path.join( d, 'initBrainVISAValidation.py' ) )
    #except:
      #showException()

  if neuroConfig.gui:
    showMainWindow()



if neuroConfig.gui:
  # QApplication.setColorSpec( QApplication.ManyColor )
  neuroConfig.qtApplication = QApplication(
    [ sys.argv[0], '-name', versionText() ] + sys.argv[1:] )
  neuroConfig.qtApplication.setAttribute(Qt.AA_DontShowIconsInMenus, False)

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
  
  if USE_QT4:
    neuroConfig.qtApplication.setWindowIcon( QIcon( os.path.join( iconPath, 'icon.png' )) )
    QDir.addSearchPath("", os.path.join( neuroConfig.docPath, 'processes' ))
  else:
    global _globalEventFilter
    _globalEventFilter = EventFilter()
    qApp.installEventFilter( _globalEventFilter )
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


def startConsoleShell():
  from PyQt4.QtGui import qApp
  import IPython
  ipConsole = runIPConsoleKernel()
  import subprocess
  sp = subprocess.Popen( [ sys.executable, '-c',
    'from IPython.frontend.terminal.ipapp import launch_new_instance; ' \
    'launch_new_instance()', 'console', '--existing',
    '--shell=%d' % ipConsole.shell_port, '--iopub=%d' % ipConsole.iopub_port,
    '--stdin=%d' % ipConsole.stdin_port, '--hb=%d' % ipConsole.hb_port ] )
  brainvisa.processes._ipsubprocs.append( sp )


from soma.application import Application as SomaApplication
soma_app = SomaApplication( 'brainvisa', versionString() )
soma_app.plugin_modules.append( 'soma.fom' )
soma_app.initialize()

if neuroConfig.gui:
  neuroConfig.qtApplication.connect( neuroConfig.qtApplication,\
                                     SIGNAL( 'lastWindowClosed ()' ),\
                                     sys.exit )
  # Ctrl + C is now linked to qApp.exit()
  signal.signal( signal.SIGINT, qt_exit_handler )
  if neuroConfig.shell:
    import IPython
    if [ int(x) for x in IPython.__version__.split('.')[:2] ] >= [ 0, 11 ]:
      # ipython >= 0.11, use client/server mode
      print 'running shell...'
      neuroConfig.shell = False
      QTimer.singleShot( 0, startConsoleShell )
  if not neuroConfig.shell:
    if USE_QT4:
      neuroConfig.qtApplication.exec_()
    else:
      neuroConfig.qtApplication.exec_loop()

if neuroConfig.databaseServer:
  # Start a Pyro server to serve databases
  from brainvisa.remote.database import DatabaseServer
  server = DatabaseServer()
  server.initialize()
  for database in neuroHierarchy.databases.iterDatabases():
    server.addDatabase( database )
  server.serve()

ipConsole = None
ipsubprocs = []
if neuroConfig.shell:
  try:
    neuroConfig.shell = 0
    import IPython
    if [ int(x) for x in IPython.__version__.split('.')[:2] ] >= [ 0, 11 ]:
      if not neuroConfig.gui: # with gui this is done earlier using qtconsole
        # ipython >= 0.11
        from IPython.frontend.terminal.ipapp import TerminalIPythonApp
        app = TerminalIPythonApp.instance()
        app.initialize( [] )
        app.start()
    else:
      # Qt console does not exist in ipython <= 0.10
      # and the API was different
      if USE_QT4:
        ipshell = IPython.Shell.IPShellQt4( [ '-q4thread' ] )
        from PyQt4.QtCore import QTimer
      else:
        ipshell = IPython.Shell.IPShellQt( [ '-qthread' ] )
        from qt import QTimer
      ipshell.mainloop( sys_exit=1 )
      cleanupGui()
  except ImportError:
    print >> sys.stderr, 'IPython not found - Shell mode disabled'
    neuroConfig.shell = 0

while len( ipsubprocs ) != 0:
  sp = ipsubprocs.pop()
  sp.kill()


neuroHierarchy.databases.currentThreadCleanup()

if __name__ == '__main__' :
  sys.exit( neuroConfig.exitValue )
