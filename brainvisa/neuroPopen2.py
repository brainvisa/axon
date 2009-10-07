
#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCIL license version 2 under
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
# knowledge of the CeCILL version 2 license and that you accept its terms.
import sys, os

if sys.platform[:3] != "win":
    from popen2 import *
    import popen2
    pipeimpl = popen2
    pipestreams = ( 0, 1, 2 )
else:
    try:
        import win32pipe
        pipeimpl = win32pipe
        pipestreams = ( 1, 0, 2 )
        import win32process, win32file, win32security
        import time
    except:
        from popen2 import *
        import popen2
        pipeimpl = popen2
        pipestreams = ( 0, 1, 2 )

def popen2( *args, **kwargs ):
    res = pipeimpl.popen2( *args, **kwargs )
    return ( res[ pipestreams[0] ], res[ pipestreams[1] ] )

def popen3( *args, **kwargs ):
    res = pipeimpl.popen3( *args, **kwargs )
    return ( res[ pipestreams[0] ], res[ pipestreams[1] ],
             res[ pipestreams[2] ] )

def popen4( *args, **kwargs ):
    res = pipeimpl.popen4( *args, **kwargs )
    return ( res[ pipestreams[0] ], res[ pipestreams[1] ] )


class Popen3:
  def __init__( self, cmd, capturestderr=0, bufsize=0 ):
    attr = win32security.SECURITY_ATTRIBUTES()
    attr.bInheritHandle = True
    self.stdin = win32pipe.CreatePipe( attr, bufsize )
    print self.stdin
    sys.stdout.flush()
    self.stdout = win32pipe.CreatePipe( attr, bufsize )
    self.tochild = os.fdopen( win32file._open_osfhandle( self.stdin[1], os.O_APPEND ) )
    self.fromchild = os.fdopen( win32file._open_osfhandle( self.stdout[0], os.O_RDONLY ) )
    if capturestderr:
      self.stderr = win32pipe.CreatePipe( attr, bufsize )
      self.childerr = os.fdopen( win32file._open_osfhandle( self.stderr[0], os.O_RDONLY ) )
    else:
      self.childerr = None
    startup = win32process.STARTUPINFO()
    startup.hStdInput = self.stdin[0]
    startup.hStdOutput = self.stdout[1]
    startup.dwFlags |= win32process.STARTF_USESTDHANDLES #| win32process.STARTF_USESHOWWINDOW
    #startup.wShowWindow = 0
    if capturestderr:
      startup.hStdError = self.stderr[1]
    self.pid = win32process.CreateProcess( None, cmd, attr, attr, True, 
      0, #win32process.NORMAL_PRIORITY_CLASS | win32process.CREATE_NO_WINDOW | \
      #win32process.CREATE_NEW_CONSOLE, 
      None, None, startup )
    print 'pid:', self.pid
    sys.stdout.flush()

  def __del__( self ):
    win32file.CloseHandle( self.pid[0] )
    win32file.CloseHandle( self.pid[1] )
    win32file.CloseHandle( self.stdin[0] )
    win32file.CloseHandle( self.stdin[1] )
    win32file.CloseHandle( self.stdout[0] )
    win32file.CloseHandle( self.stdin[1] )
    if getattr( self, 'stderr' ):
      win32file.CloseHandle( self.stderr[0] )
      win32file.CloseHandle( self.stderr[0] )

  def poll( self ):
    ret = win32process.GetExitCodeProcess( self.pid[0] )
    if ret == 259: # STILL_ACTIVE
      return -1
    return ret

  def wait( self ):
    x = self.poll()
    while x:
      time.sleep( 0.02 )
      x = self.poll()
    return x


if sys.platform[:3] != 'win':
  Popen3 = pipeimpl.Popen3 