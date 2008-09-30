import sys, os
from traceback      import format_exc

class MultipleExecfile:
  def __init__( self, localDict=None, globalDict=None ):
    if localDict is None:
      localDict = {}
    if globalDict is None:
      # Get the global dictionary of the caller. Using globals() would
      # return the namespace of this module.
      globalDict = sys._getframe(1).f_globals
    self.localDict = localDict
    self.localDict[ 'include' ] = self._include
    self.globalDict = globalDict
    self.includePath = []
    self.fileExtensions = [ '' ]
    self._executedFiles = {}
    self._includeStack = []
    
  def findFile( self, localFileName ):
    result = None
    if self._includeStack:
      path = [ os.path.dirname( self._includeStack[ -1 ] ) ] + self.includePath
    else:
      path = self.includePath + [ '' ]
    for e in self.fileExtensions:
      for p in path:
        if p is None: continue
        f = os.path.join( p, localFileName + e )
        if os.path.exists( f ):
          result = os.path.abspath( os.path.normpath( f ) )
          break
      if result is not None: break
    return result
  
  def execute( self, *args, **kwargs ):
    exc = []
    for f in args:
      file = None
      try:
        file = self.findFile( f )
        if file is None:
          if self._includeStack:
            raise RuntimeError( _t_( 'Include file %s not found (in %s)' ) % ( f, self._includeStack[ -1 ] ) )
          else:
            raise RuntimeError( _t_( 'File %s does not exists' ) % ( f, ) )
  #dbg#      print '!MultipleExecfile!', f, '-->', file
        status = self._executedFiles.get( file )
        if status is None:
  #dbg#        print '!MultipleExecfile! execute', file
          self._executedFiles[ file ] = False
          self._includeStack.append( file )
          self.localDict[ '__name__' ] = file
          execfile( file, self.globalDict, self.localDict )
          self._includeStack.pop()
          if self._includeStack:
            self.localDict[ '__name__' ] = self._includeStack[ -1 ]
          else:
            self.localDict[ '__name__' ] = None
          self._executedFiles[ file ] = True
        elif status == False:
          raise RuntimeError( _t_( 'Circular dependencies in included files. Inclusion order: %s' ) % ( ', '.join( self._includeStack + [ file ] ), ) )
  #dbg#      else:
  #dbg#        print '!MultipleExecfile!', file, 'already executed'
      except Exception, e:
        msg = unicode( 'while executing file ' + f + ' ' )
        if file:
          msg += u'(' + unicode( file ) + u') '
        msg += ': '
        if hasattr( e, 'message' ):
          msg = msg + unicode( e.message )
          e.message = msg
        else:
          msg = msg + format_exc()
        e.args = ( msg, ) + e.args[1:]
        print msg
        if not kwargs.get( 'continue_on_error', False ):
          raise e
        exc.append( e )
    if exc:
      return exc

  def _include( self, *args ):
#dbg#    for f in args:
#dbg#      print '!MultipleExecfile! include', f, 'in', self._includeStack[ -1 ]
#dbg#      self.execute( f )
    self.execute( *args )


  def executedFiles( self ):
    return self._executedFiles.iterkeys()