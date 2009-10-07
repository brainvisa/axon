# Copyright IFR 49 (1995-2009)
#
#  This software and supporting documentation were developed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL-B license under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the 
# terms of the CeCILL-B license as circulated by CEA, CNRS
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
# knowledge of the CeCILL-B license and that you accept its terms.

'''Threading compiliant Interface between Matlab and Python. This module uses PyMat
(see http://claymore.engineer.gvsu.edu/~steriana/Python for more information).
The module always defines the variable "valid". If pymat module cannot be
imported, "valid" is set to 0 and the matlab module does not contain anything
else. Otherwise, "valid" is set to 1 and usefull classes and functions are
defined.'''

import os, string
from brainvisa.threadCalls import *
 
class MatlabError( RuntimeError ):
  '''Exception raised when matlab command evaluation fails'''
  pass


  
class Matlab:
  _pymatmoduleimport = 'import pymat'

  '''This class is a wrapper between Python and PyQt. It is necessary if you
  whish to use PyQt in a multi-threaded environment. It creates a thread that
  initialise a Matlab engine via PyMat. All calls to PyMat functions are
  executed in that thread (otherwise the call may fail). But calls to this 
  class public methods (not begining with an underscore) can be done from
  any thread.    
  '''
  
  def importpymat():
    exec( Matlab._pymatmoduleimport, globals(), globals() )

  importpymat = staticmethod( importpymat )

  def __init__( self, *args, **kwargs ):
    Matlab.importpymat()
    '''Create the matlab thread and initialise engine. Arguments are passed
    to PyMat open'''
    queue = Queue.Queue( 32 )
    self._matlabThread = CallerThread( queue, name='MatlabThread' )
    self._matlabThread.setDaemon( 1 )
    self._matlabThread.start()
    self._callMatlabThread = SingleThreadCalls( self._matlabThread, queue )
    self._callMatlabThread.push( self._initPyMat, *args, **kwargs )

  def _initPyMat( self, startCommand=None ):
    Matlab.importpymat()
    if startCommand is None:
      self._handle = pymat.open()
    else:
      self._handle = pymat.open( startCommand )

  def __del__( self ):
    self._callMatlabThread.call( self._closePyMat )
    self._callMatlabThread.stop()
    self._callMatlabThread = None
    self._matlabThread = None

  def _closePyMat( self ):
    Matlab.importpymat()
    pymat.close( self._handle )
    self._handle = None

  def eval( self, *args, **kwargs ):
    '''Evaluate matlab expressions passed in parameters. The optional keyword
    argument "workspace" can be used to change Matlab's workspace. If it is 
    not None, expressions are evaluated within the Matlab funcion 
    "evalin(workspace,expression)". By default "workspace" is set to 'base'.'''
      
    workspace = kwargs.get( 'workspace' )
    expression = string.join( args, ',' )
    if workspace:
      error = self._callMatlabThread.call( self._evalin, expression, workspace=workspace )
    else:
      error = self._callMatlabThread.call( self._eval, expression )
    if error:
      raise MatlabError( error )

  def _evalin( self, expression, workspace='base' ):
    Matlab.importpymat()
    pymat.put( self._handle, 'bvError_',
               'Syntax error in matlab expression' )
    command = "bvError_='',try,evalin('" + workspace + "','" + expression + "'),catch,bvError_=lasterr,end"
    pymat.eval( self._handle, command )
    return pymat.get( self._handle, 'bvError_' )

  def _eval( self, expression ):
    Matlab.importpymat()
    pymat.put( self._handle, 'bvError_',
               'Syntax error in matlab expression' )
    command = "bvError_='',try," + expression + ",catch,bvError_=lasterr,end"
    pymat.eval( self._handle, command )
    return pymat.get( self._handle, 'bvError_' )

  def get( self, *args, **kwargs ):
    '''Get a matrix from Matlab engine by calling pymat.get() in the matlab
    thread.'''
    return self._callMatlabThread.call( self._get, *args, **kwargs )

  def _get( self, *args, **kwargs ):
    Matlab.importpymat()
    return pymat.get( self._handle, *args, **kwargs )

  def put( self, *args, **kwargs ):
    '''Put a matrix on Matlab engine by calling pymat.put() in the matlab
    thread.'''
    return self._callMatlabThread.call( self._put, *args, **kwargs )

  def _put( self, *args, **kwargs ):
    Matlab.importpymat()
    return pymat.put( self._handle, *args, **kwargs )



'''Command used to start matlab engine'''
matlabRelease = None
matlabExecutable = 'matlab'
matlabOptions = '-nosplash -nojvm'
'''Paths added to Matlab environment'''
matlabPath = []
'''Matlab expressions evaluated on engine startup'''
matlabStartup = []

_matlabInstance = None
_matlabLock = threading.Lock()

def matlab():
  '''Return a unique instance of Matlab engine.'''
  global _matlabInstance, _matlabLock
  _matlabLock.acquire()
  try:
    if _matlabInstance is None:
      _matlabInstance = Matlab( '"' + matlabExecutable + '" ' + matlabOptions )
      mp = os.environ.get( 'MATLABPATH', [] )
      if mp:
        mp = string.split( mp, ':' )
      for path in matlabPath + mp:
        _matlabInstance.eval( "addpath('" + path + "','-end')", workspace=None )
      for cmd in matlabStartup:
        _matlabInstance.eval( cmd )
  finally:
    _matlabLock.release()
  return _matlabInstance

def closeMatlab():
  '''Close a unique instance of Matlab engine. The engine will actually be
  destroyed when garbage collected. Therefore if it is references somewhere,
  it will not be destroyed immediatly. After closeMatlab(), a call to matlab()
  creates a new engine.'''
  global _matlabInstance, _matlabLock
  _matlabLock.acquire()
  try:
    _matlabInstance = None
  finally:
    _matlabLock.release()

