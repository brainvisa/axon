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

from __future__ import absolute_import
import locale
import os
import sys

from soma.qt_gui.qt_backend.QtCore import QProcess, QTimer, QProcessEnvironment
from brainvisa.configuration import neuroConfig
from soma.qt_gui import qt_backend
if qt_backend.get_qt_backend() == 'PySide':
    use_pyside = True
else:
    use_pyside = False
    from soma.qt_gui.qt_backend.QtCore import PYQT_VERSION
    if PYQT_VERSION < 0x040703:
        # a bug in PyQt QProcess.start() needs a compiled workaround
        from soma import somaqt

# import logging
# LOG_FILENAME = '/tmp/commands.log'
# if os.path.exists( LOG_FILENAME ): os.remove( LOG_FILENAME )
# logging.basicConfig( filename=LOG_FILENAME, level=logging.DEBUG )

#--------------------------------------------------------------------------


def _decode_output(output_bytes):
    """Decode the output of a process to Unicode."""
    return bytes(output_bytes).decode(locale.getpreferredencoding(), 'replace')


class CommandWithQProcess(object):

    class SignalException(Exception):
        pass

    class UserInterruption(Exception):
        pass

    """
  This class is used to make a system call using QProcess
  """

    def __init__(self, *args):
        '''This class is used to call a command line program from any thread
        and launch personalized function whenever the command produce output
        (either standard or error).

        Usage:
          c = CommandWithQProcess( 'executable', 'first argument','second argument' )
          c.start()
          exitStatus = c.wait()

        By default all standard output are redirected to sys.stdout and all error
        output to sys.stderr. It is possible to change this behaviour by setting
        the functions called when an output string is available with
        methods setStdoutAction() and setStderrAction().
        '''
        self.args = [str(i) for i in args]
        self._qprocess = self._createQProcess()
        self._stdoutAction = sys.stdout.write
        self._stderrAction = sys.stderr.write
        self.normalExit = False
        self.exitStatus = None
        self._stopped = False

    def setWorkingDirectory(self, cwd):
        """
        Set the working directory for the process.
        """
        self._qprocess.setWorkingDirectory(cwd)

    def setEnvironment(self, env):
        """
        Set a map of environment variables that have to be change at starting the process.
        @type env: map string -> string
        @param env: map variable -> value
        """
        if env:
            mapenv = os.environ.copy()
            mapenv.update(env)
            pe = QProcessEnvironment()
            #listenv = []
            for var, value in mapenv.items():
                if value is not None:
                    #listenv.append(var + "=" + value)
                    pe.insert(var, value)
            self._qprocess.setProcessEnvironment(pe)

    def start(self):
        '''Starts the command. If it cannot be started, a RuntimeError is raised'''
        # logging.debug( '\n'.join( [ ' '.join( ( repr(i) for i in self.args)
        # ), 'File descriptors: ' + str( len(os.listdir( os.path.join( '/proc',
        # str( os.getpid() ), 'fd' ) ) ) ), open( os.path.join( '/proc', str(
        # os.getpid() ), 'status' ) ).read(), '-' * 70 ] ) )
        self._stopped = False
        self._qprocess.start(self.args[0], self.args[1:])
        if not self._qprocess.waitForStarted(-1):
            err = self._qprocess.error()
            if err == self._qprocess.FailedToStart:
                # logging.error( 'Cannot start command' )
                raise RuntimeError(_t_('Cannot start command %s : %s') %
                                   (str(self), self._qprocess.errorString(), ))
            elif err == self._qprocess.Crashed:
                # logging.error( 'Crash during command start' )
                raise RuntimeError(_t_('Crash during command start %s : %s') %
                                   (str(self), self._qprocess.errorString(), ))
            elif err == self._qprocess.Timedout:
                # logging.error( 'Timeout during command start' )
                raise RuntimeError(_t_('Timeout during command start %s : %s') %
                                   (str(self), self._qprocess.errorString(), ))
            elif err == self._qprocess.WriteError:
                # logging.error( 'Write error during command start' )
                raise RuntimeError(_t_('Write error during command start %s : %s') %
                                   (str(self), self._qprocess.errorString(), ))
            elif err == self._qprocess.ReadError:
                # logging.error( 'Read error during command start' )
                raise RuntimeError(_t_('Read error during command start %s : %s') %
                                   (str(self), self._qprocess.errorString(), ))
            else:
                # logging.error( 'Unknown error during command start' )
                raise RuntimeError(_t_('Unknown error during command start %s : %s') %
                                   (str(self), self._qprocess.errorString(), ))

    def wait(self):
        '''Wait for the command to finish. Upon normal exit, the exit status of
        the command (i.e. its return value) is returned, otherwise a RuntimeError
        is raised.'''
        self._qprocess.waitForFinished(-1)
        # print('wait finished:', self.exitStatus, self.normalExit)
        if not self.normalExit:
            # print('raising exception...')
            if self._stopped:
                raise self.UserInterruption(_t_('System call interrupted'))
            raise self.SignalException(_t_('System call crashed in command: ') + repr(self.args))
        return self.exitStatus

    def error(self):
        return self._qprocess.error()

    def stop(self):
        '''Interrupt a running command. If possible, it tries to terminate the
        command giving it the possibility to do cleanup before exiting. If the
        command is still alive ater 15 seconds, it is killed.'''
        self._stopped = True
        if neuroConfig.platform == 'windows':
            # on Windows, don't even try the soft terminate, it always fails
            self._qprocess.kill()
            return
        self._qprocess.terminate()
        if self._qprocess.state() == self._qprocess.Running:
            # If the command is not finished in 15 seconds, kill it
            # print('still running... violently killing it in 15 seconds')
            QTimer.singleShot(15000, self._qprocess.kill)

    def commandName(self):
        '''Returns the name of the executable of this command'''
        return self.args[0]

    def __str__(self):
        return' '.join(["'" + i + "'" for i in self.args])

    def setStdoutAction(self, callable, *args, **kwargs):
        '''Sets a function called each time a string is available on command's
        standard output. The function is called with the string as a single parameter.'''
        if args or kwargs:
            raise RuntimeError(
                'Command.setStdoutAction() only accept one argument (new in BrainVISA 3.03)')
        self._stdoutAction = callable

    def setStderrAction(self, callable, *args, **kwargs):
        '''Sets a function called each time a string is available on command's
        error output. The function is called with the string as a single parameter.'''
        if args or kwargs:
            raise RuntimeError(
                'Command.setStderrAction() only accept one argument (new in BrainVISA 3.03)')
        self._stderrAction = callable

    def _createQProcess(self):
#    print(threading.currentThread(), '_createQProcess()', self.args)
        if use_pyside or PYQT_VERSION >= 0x040703:
            qprocess = QProcess()
        else:
            qprocess = somaqt.makeQProcess()
        qprocess.finished.connect(self._processExited)
        qprocess.readyReadStandardOutput.connect(self._readStdout)
        qprocess.readyReadStandardError.connect(self._readStderr)
        return qprocess

    def _processExited(self, exitCode, exitStatus):
        self.normalExit = (exitStatus == QProcess.NormalExit)
        self.exitStatus = exitCode

    @staticmethod
    def _filterOutputString(buffer):
        # filter '\r', '\b' and similar
        # FIXME: use a more efficient filtering method!!! (e.g. re.sub)
        result = u''
        for c in buffer:
            if c == u'\b':
                if len(result) > 0:
                    result = result[:-1]
            elif (c == u'\r') and (neuroConfig.platform != 'windows'):
                # On windows \r means a carriage return and is followed by a \n
                result = ''
            elif c in (u'\a', u'\u000b'):  # might appear on Mac/Windows
                pass
            else:
                result += c
        return result

    def _readStdout(self):
        line = self._filterOutputString(
            _decode_output(self._qprocess.readAllStandardOutput()))
        self._stdoutAction(line + u'\n')

    def _readStderr(self):
        line = self._filterOutputString(
            _decode_output(self._qprocess.readAllStandardError()))
        self._stderrAction(line + u'\n')
