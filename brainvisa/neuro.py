#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is the main module of BrainVISA. It is executed by ``brainvisa`` command to start the software.
It loads a lot of other modules and initializes BrainVISA application according to the options given at startup.
"""
import six
__docformat__ = 'restructuredtext en'

# Be careful, it is necessary to initialize
# subprocess with subprocess32 when it is possible because of known
# issues in subprocess module that can lead to lock in subprocess run
import soma.subprocess

import sys
import os
import signal

from soma.qt_gui import qt_backend
qt_backend.set_qt_backend(compatible_qt5=True)
qt_mod = qt_backend.get_qt_backend()

if len(sys.argv) > 1 and sys.platform[:6] == 'darwin' and sys.argv[1][:5] == '-psn_':
    # MacOS calls me with this strange argument, I don't want it.
    del sys.argv[1]

if '-b' in sys.argv[1:]:
    from soma.qt_gui import qt_backend

    qt_backend.set_headless(headless_mode=True, needs_opengl=True)
    from soma.qt_gui.qt_backend import QtWidgets

    qapp = QtWidgets.QApplication([])

from soma.qt_gui.qt_backend import QtCore
from soma.wip.application.api import Application
from soma.signature.api import Choice as SomaChoice
from brainvisa.configuration import neuroConfig
from brainvisa.data import temporary
if neuroConfig.gui:
    from brainvisa.configuration.qtgui import neuroConfigGUI
from brainvisa.processing.neuroException import *
from brainvisa.data.neuroData import *
from brainvisa.processes import *
import brainvisa.processes
from brainvisa.data.neuroHierarchy import *
if neuroConfig.gui:
    from brainvisa.data.qtgui.neuroDataGUI import *
    from brainvisa.processing.qtgui.neuroProcessesGUI import *
from brainvisa.data import neuroHierarchy
if neuroConfig.gui:
    from brainvisa.processing.qtgui.backwardCompatibleQt import *
if neuroConfig.gui:
    from brainvisa.data.qtgui.updateDatabases import warnUserAboutDatabasesToUpdate


def system_exit_handler(number, frame):
    """The callback associated to SIGINT signal (CTRL+C) when there is no Qt Application."""
    sys.exit(1)


def qt_exit_handler(number, frame):
    """The callback associated to SIGINT signal (CTRL+C) when a Qt Application is running."""
    QApplication.instance().exit()

# Ctrl + C is linked to sys.exit() until Qt event loop is entered
signal.signal(signal.SIGINT, system_exit_handler)


class EventFilter(QObject):

    def eventFilter(self, o, e):
        try:
            if getattr(EventFilter, 'pixIcon', None) is None:
                setattr(EventFilter, 'pixIcon', QPixmap(
                    os.path.join(iconPath, 'icon.png')))
            if e.type() == QEvent.Show and o.parent() is None and o.icon() is None:
                o.setIcon(self.pixIcon)
        except:
            pass
        return False


def setQtApplicationStyle(newStyle):
    """
    This function sets the graphical style of the Qt application with the style given in parameter.
    If the parameter is None, the style given in gui_style brainvisa option is applied.
    """
    if not newStyle:
        newStyle = app.configuration.brainvisa.signature[
            'gui_style'].defaultValue
    QApplication.instance().setStyle(newStyle)


def main():
    """
    This function initializes BrainVISA components: log, databases, processes, graphical user interface.
    """
    try:

        from brainvisa import axon
        print('BATCH MODE 2')
        axon.initializeProcesses()
        print('BATCH MODE 3')

        neuroHierarchy.update_soma_workflow_translations()

        nbDatabases = len(neuroHierarchy.databases._databases)
        if neuroConfig.sharedDatabaseFound:
            nbDatabases -= 1
        elif not neuroConfig.fastStart:
            showWarning(
                "BrainVISA Shared database was not found. It is needed for many processes. Check your Brainvisa installation.")
        if not neuroConfig.setup:
            if neuroConfig.gui:
                warnUserAboutDatabasesToUpdate()
                if (nbDatabases == 0 and getattr(neuroConfig, 'databasesWarning', False)):
                    choice = defaultContext().ask(
                        "<p><b>Welcome to BrainVISA !</b></p><p>You have not selected any database yet.</p><p>It is strongly advisable to use a database to process data with BrainVISA. Indeed, some important features are not available when you are using data outside a database. To add a new database, go to <i>databases tab</i> in the <i>preferences window</i> and click on the <i>add button</i>.</p>",  "Open preferences", "Cancel", "Don't show this warning next time")
                    if (choice == 0):
                        neuroConfigGUI.editConfiguration()
                    elif (choice == 2):
                        app = Application()
                        app.configuration.brainvisa.databasesWarning = False
                        app.configuration.save(neuroConfig.userOptionFile)
            else:
                toUpdate = [
                    i for i in neuroHierarchy.databases.iterDatabases() if getattr(i, '_mustBeUpdated', False)]
                if toUpdate:
                    print(_t_('WARNING') + ':', _t_(
                        'Some ontologies (i.e. databases organization) have been modified but are used by currently selected databases. To take this modification into account, it is necessary to update the following databases:'), file=sys.stderr)
                    for i in toUpdate:
                        print(' ', i.name, file=sys.stderr)
                if (nbDatabases == 0 and getattr(neuroConfig, 'databasesWarning', False)):
                    print(_t_('WARNING') + ':', _t_(
                        'You have not selected any database yet. It is strongly advisable to use a database to process data with BrainVISA. Indeed, some important features are not available where you are using data outside a database. To add a new database, go to databases tab in the preferences window and click on the add button.'), file=sys.stderr)
    except:
        raise
        showException()

    if neuroConfig.gui:
        showMainWindow()


if neuroConfig.gui:
    from soma.qt_gui import ipkernel_tools

    ipkernel_tools.before_start_ipkernel()

    neuroConfig.qtApplication = QApplication(
        [sys.argv[0], '-name', versionText()] + sys.argv[1:])
    neuroConfig.qtApplication.setAttribute(Qt.AA_DontShowIconsInMenus, False)

    # Styles list must be read only after QApplication instanciation
    # otherwise it is incomplete (even after instanciation).
    app = Application()
    app.configuration.brainvisa.signature['gui_style'].type = SomaChoice(
        *[('<system default>', None)] + [six.text_type(i) for i in QStyleFactory.keys()])
    app.configuration.brainvisa.signature[
        'gui_style'].defaultValue = six.text_type(
            QApplication.instance().style().objectName())
    app.configuration.brainvisa.onAttributeChange(
        'gui_style', setQtApplicationStyle)
    setQtApplicationStyle(app.configuration.brainvisa.gui_style)

# The following lines are used to put a BrainVISA icon to all
# the top-level windows that do not have one. But it crashes due
# to a PyQt bug. This bug has been reported and fixed in earlier
# versions.

    neuroConfig.qtApplication.setWindowIcon(
        QIcon(os.path.join(iconPath, 'icon.png')))
    QDir.addSearchPath("", os.path.join(neuroConfig.docPath, 'processes'))
else:
    # neuroConfig.qtApplication = QApplication( sys.argv, QApplication.Tty )
    from soma.qt_gui.qt_backend.QtCore import QCoreApplication
    neuroConfig.qtApplication = QCoreApplication(sys.argv)

if neuroConfig.profileFileName:
    import profile
    import pstats
    profile.run('main()', profileFileName)
    p = pstats.Stats(profileFileName)
    p.sort_stats('time').print_stats(10)
    p.sort_stats('time').print_callers(10)
else:
    print('BATCH MODE')
    main()


def startConsoleShell():

    from soma.qt_gui.qt_backend.QtWidgets import QApplication
    try:
        import jupyter_console.app
        ipmodule = 'jupyter_console.app'
    except ImportError:
        import IPython
        ipversion = [int(x) for x in IPython.__version__.split('.')]
        if ipversion >= [1, 0]:
            ipmodule = 'IPython.terminal.ipapp'
        else:
            ipmodule = 'IPython.frontend.terminal.ipapp'

    ipConsole = runIPConsoleKernel()
    import soma.subprocess
    sp = soma.subprocess.Popen([sys.executable, '-c',
                           'from %s import launch_new_instance; launch_new_instance()' % ipmodule,
                           'console', '--existing',
                           '--shell=%d' % ipConsole.shell_port, '--iopub=%d' % ipConsole.iopub_port,
                           '--stdin=%d' % ipConsole.stdin_port, '--hb=%d' % ipConsole.hb_port])
    brainvisa.processes._ipsubprocs.append(sp)


try:
    from soma.application import Application as SomaApplication
except ImportError:
    SomaApplication = None
if SomaApplication is not None:
    soma_app = SomaApplication('brainvisa', versionString())
    soma_app.plugin_modules.append('soma.fom')
    soma_app.initialize()

if neuroConfig.gui:
    neuroConfig.qtApplication.lastWindowClosed .connect(sys.exit)
    # Ctrl + C is now linked to QApplication.instance().exit()
    signal.signal(signal.SIGINT, qt_exit_handler)

    # The GUI can now be used (in particular for showing error messages, see
    # brainvisa.processing.neuroException.showException)
    neuroConfig.guiLoaded = True

    if neuroConfig.shell:
        try:
            import jupyter_console
            print('running jupyter shell...')
            neuroConfig.shell = False
            QTimer.singleShot(0, startConsoleShell)
        except ImportError:
            import IPython
            if [int(x) for x in IPython.__version__.split('.')[:2]] >= [0, 11]:
                # ipython >= 0.11, use client/server mode
                print('running shell...')
                neuroConfig.shell = False
                QTimer.singleShot(0, startConsoleShell)
    if not neuroConfig.shell:
        ipkernel_tools.start_ipkernel_qt_engine()
        # neuroConfig.qtApplication.exec()

ipConsole = None
ipsubprocs = []
if neuroConfig.shell:
    neuroConfig.shell = 0
    try:
        # use jupyter API
        import jupyter_console.app as japp
        app = japp.ZMQTerminalIPythonApp.instance()
        app.initialize([])
        app.start()
    except ImportError:
        try:
            import IPython
            ipversion = [int(x) for x in IPython.__version__.split('.')]
            if ipversion >= [0, 11]:
                if not neuroConfig.gui:  # with gui this is done earlier using qtconsole
                    # ipython >= 0.11
                    if ipversion >= [1, 0]:
                        from IPython.terminal.ipapp import TerminalIPythonApp
                    else:
                        from IPython.frontend.terminal.ipapp import TerminalIPythonApp
                    app = TerminalIPythonApp.instance()
                    app.initialize([])
                    app.start()
            else:
                # Qt console does not exist in ipython <= 0.10
                # and the API was different
                ipshell = IPython.Shell.IPShellQt4(['-q4thread'])
                from soma.qt_gui.qt_backend.QtCore import QTimer
                ipshell.mainloop(sys_exit=1)
                cleanupGui()
        except ImportError:
            print('IPython not found - Shell mode disabled', file=sys.stderr)
            neuroConfig.shell = 0

while len(ipsubprocs) != 0:
    sp = ipsubprocs.pop()
    sp.kill()

neuroHierarchy.databases.currentThreadCleanup()


if __name__ == '__main__':
    ch = []
    if neuroConfig.exitValue == 0:
        temporary.remove_all_temporaries()
        os._exit(0)

    sys.exit(neuroConfig.exitValue)
