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

import distutils, os
from brainvisa.validation import ValidationError
import neuroProcesses, neuroLog
from brainvisa import matlab

_valid = None
_validchecked = None


def detect_matlab_version( matexe, log=None ):
  if matlab.matlabRelease:
    mver =  matlab.matlabRelease
    if log is not None:
      log[0] += _t_( 'matlab release is forced in config' ) + '<br>'
  else:
    if log is not None:
      log[0] += _t_( 'opening matlab to guess release version' ) + '<br>'
    tmp = neuroProcesses.defaultContext().temporary( 'File' )
    cmd = "fid = fopen( '" + tmp.fullPath() + "', 'w' ); fprintf( fid, version('-release'), '%s' ); fclose( fid ); exit"
    try:
      try:
        # Valid only since Python 2.4
        import subprocess
        out, err = subprocess.Popen( ( matexe, '-nodesktop', '-nosplash', '-r', cmd ), 
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE ).communicate()
      except ImportError:
        # Work with earlier Python version but generates the following error at exit:
        # Exception exceptions.TypeError: TypeError("'NoneType' object is not callable",) in <bound method Popen3.__del__ of <popen2.Popen3 instance at 0xb7303c2c>> ignored
        stdin, stdout, stderr = os.popen3( matexe + ' "-nodesktop" "-nosplash" "-r" "' + cmd + '"' )
        stdin.close()
        err = stderr.read()
        out = stdout.read()
        stdout.close()
        stderr.close()
        del stdout, stderr, stdin
      if log is not None:
        log[0] += _t_( 'matlab seems to work. How lucky you are.' ) + '<br>'
        if err:
          log[0] += '<b>' + _t_( 'matlab error output' ) + '</b>: ' + err \
                    + '<br>'
      if log is not None and not os.path.exists( tmp.fullPath() ):
        log[0] += _t_( "matlab didn't write the verison file it should" ) \
                  + '<br>'
        return None
      f = open( tmp.fullPath() )
      mver = f.readline()
      f.close()
    except Exception, e:
      import traceback
      traceback.print_exc()
      if log is not None:
        log[0] += _t_( 'Matlab could not start' ) + ':' + str(e) + '<br>'
      return None
    matlab.matlabRelease = mver
  mver = mver.split( '.' )[0]
  if matlab.matlabRelease.startswith( '20' ) and len( mver ) >= 5:
    # new style: '2006a'
    return '7' # for now it's only matlab 7
  else:
    mver = int( mver )
    if mver < 12:
      return '5'
    elif mver < 14:
      return '6'
    else:
      return '7'

def validation():
  global _validchecked
  global _valid
  if _validchecked is not None:
    if _valid is None:
      return
    else:
      raise ValidationError( _valid )
  _validchecked = 1
  logmsg = '<b>' + _t_( 'Matlab executable' ) + '</b>: ' + matlab.matlabExecutable \
           + '<br>'
  matexe = distutils.spawn.find_executable( matlab.matlabExecutable )
  logmsg += '<b>' + _t_( 'Matlab executable full path' ) + '</b>: ' \
            + str( matexe ) + '<br>'
  if not matexe:
    logmsg += _t_( 'Matlab executbale not found' ) + '<br>'
    _valid = _t_( 'Matlab executable not found' )
    neuroProcesses.defaultContext().log( \
          _t_( 'Matlab configuration' ), html=logmsg, icon='matlab' )
    raise ValidationError( _valid )
  x = [ logmsg ]
  matver = detect_matlab_version( matexe, x )
  logmsg = x[0]
  logmsg += '<b>' + _t_( 'Matlab version' ) + '</b>: ' + str( matver ) + '<br>'
  try:
    if matver is not None:
      try:
        v = matver.split( '.' )[0]
        logmsg += '<b>' + _t_( 'pymat module' ) + '</b>: pymat' + v + '<br>'
        pymatmoduleimport = 'import pymat' + v + ' as pymat'
        exec( pymatmoduleimport, globals(), globals() )
        _valid = None
        matlab.Matlab._pymatmoduleimport = pymatmoduleimport
        logmsg += _t_( 'pymat module loaded.' ) + '<br>'
        neuroProcesses.defaultContext().log( \
          _t_( 'Matlab configuration' ), html=logmsg, icon='matlab.png' )
        return
      except:
        logmsg += _t_( 'importation failed.' ) + '<br>'
    logmsg += _t_( 'loading default pymat module' ) + '<br>'
    import pymat
  except:
    logmsg += _t_( 'Matlab unavailable' ) + '<br>'
    _valid = _t_( 'Matlab unavailable' )
    neuroProcesses.defaultContext().log( \
          _t_( 'Matlab configuration' ), html=logmsg, icon='matlab.png' )
    raise ValidationError( _valid )
  neuroProcesses.defaultContext().log( \
          _t_( 'Matlab configuration' ), html=logmsg, icon='matlab.png' )
  _valid = None


