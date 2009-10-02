# -*- coding: utf-8 -*-
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

import neuroConfig 
import threading, sys, time, os
from backwardCompatibleQt import QProcess, qApp, QTimer, SIGNAL, QStringList

#--------------------------------------------------------------------------
class CommandWithQProcess( object ):
  """
  This class is used to make a system call using QProcess
  """
  def __init__( self, *args ):
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
    from qtgui.neuroProcessesGUI import mainThreadActions
    self._mainThreadCalls = mainThreadActions()
    self._semaphore = threading.Semaphore( 0 )
    self.args = [str(i) for i in args]
    self._qprocess = self._mainThreadCalls.call( self._createQProcess )
    self._stdoutAction = sys.stdout.write
    self._stderrAction = sys.stderr.write
    self.env=None

  def setEnvironment(self, env):
    """
    Set a map of environment variables that have to be change at starting the process.
    @type env: map string -> string
    @param env: map variable -> value
    """
    self.env=os.environ.copy()
    self.env.update(env)

  def start( self ):
    '''Starts the command. If it cannot be started, a RuntimeError is raised'''
    if not self._mainThreadCalls.call( self._startProcess ):
      raise RuntimeError( _t_( 'Cannot start command %s' ) % ( str( self ), ) )


  def wait( self ):
    '''Wait for the command to finish. Upon normal exit, the exit status of
    the command (i.e. its return value) is returned, otherwise a RuntimeError
    is raised.'''
    if self._mainThreadCalls.isInMainThread():
      # process a local Qt events loop
      while self._qprocess.isRunning():
        qApp.processEvents()
        time.sleep( 0.05 )
    else:
      # in a different thread, block on a semaphore until it is finished
      self._semaphore.acquire()
    #if not self.normalExit:
      #raise RuntimeError( _t_( 'System call exited abnormally' ) )
    return self.exitStatus


  def stop( self ):
    '''Interrupt a running command. If possible, it tries to terminate the
    command giving it the possibility to do cleanup before exiting. If the
    command is still alive ater 15 seconds, it is killed.'''
    self._mainThreadCalls.push( self._stop )

  def _stop( self ):
    if neuroConfig.platform == 'windows':
      # on Windows, don't even try the soft terminate, it always fails
      self._qprocess.kill()
      return
    self._qprocess.tryTerminate()
    if self._qprocess.isRunning():
      # If the command is not finished in 15 seconds, kill it
      # print 'still running... violently killing it in 15 seconds'
      QTimer.singleShot( 15000, self._qprocess.kill )


  def commandName( self ):
    '''Returns the name of the executable of this command'''
    return self.args[ 0 ]


  def __str__( self ):
    return' '.join( ["'" + i + "'" for i in self.args ] )


  def setStdoutAction( self, callable, *args, **kwargs ):
    '''Sets a function called each time a string is available on command's
    standart output. The function is called with the string as a single parameter.'''
    if args or kwargs:
      raise RuntimeError( 'Command.setStdoutAction() only accept one argument (new in BrainVISA 3.03)' )
    self._stdoutAction = callable


  def setStderrAction( self, callable, *args, **kwargs ):
    '''Sets a function called each time a string is available on command's
    error output. The function is called with the string as a single parameter.'''
    if args or kwargs:
      raise RuntimeError( 'Command.setStderrAction() only accept one argument (new in BrainVISA 3.03)' )
    self._stderrAction = callable


  def _createQProcess( self ):
#    print threading.currentThread(), '_createQProcess()', self.args
    qprocess = QProcess()
    for arg in self.args:
      qprocess.addArgument( arg )

    qprocess.setCommunication( QProcess.Stdout | QProcess.Stderr )

    qprocess.connect( qprocess,
                      SIGNAL( 'processExited()' ),
                      self._processExited )
    qprocess.connect( qprocess,
                      SIGNAL( 'launchFinished()' ),
                      self._processLaunched )
    qprocess.connect( qprocess, SIGNAL( 'readyReadStdout()' ),
                      self._readStdout )
    qprocess.connect( qprocess, SIGNAL( 'readyReadStderr()' ),
                      self._readStderr )
    return qprocess


  def _startProcess( self ):
#    print threading.currentThread(), '_startProcess()', self
    env=None
    if self.env:
      env=QStringList()
      for var, value in self.env.items():
        if value is not None:
          env.append(var+"="+value)
    return self._qprocess.launch( '', env )


  def _processExited( self ):
    #print threading.currentThread(), '_processExited()', self
    self.normalExit = self._qprocess.normalExit()
    self.exitStatus = self._qprocess.exitStatus()
    self._semaphore.release()


  def _processLaunched( self ):
    pass


  def _filterOutputString( buffer ):
    # filter '\r', '\b' and similar
    result = ''
    for c in buffer:
      if c == '\b':
        if len( result ) > 0:
          result = result[:-1]
      elif c == '\r':
        result = ''
      elif c in ( '\a', '\m', '\x0b' ): # might appear on Mac/Windows
        pass
      else:
        result += c
    return result
  _filterOutputString = staticmethod( _filterOutputString )

  def _readStdout( self ):
    while self._qprocess.canReadLineStdout():
      line = self._filterOutputString( unicode( self._qprocess.readLineStdout() ) )
      self._stdoutAction( line + '\n' )


  def _readStderr( self ):
    while self._qprocess.canReadLineStderr():
      line = self._filterOutputString( unicode( self._qprocess.readLineStderr() ) )
      self._stderrAction( line + '\n' )
