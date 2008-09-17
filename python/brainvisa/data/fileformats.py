import os
from soma.translation import translate as _
from soma.undefined import Undefined

class Format( object ):
  def __init__( self, name, extensions ):
    self.name = unicode( name )
    self._extensionsAndIsDir = []
    for e in extensions:
      isDirectory = False
      if e.startswith( 'd|' ):
        isDirectory = True
        e = e[ 2: ]
      elif e.startswith( 'f|' ):
        e = e[ 2: ]
      self._extensionsAndIsDir.append( ( e, isDirectory ) )
    
  def extensions( self ):
    return [i[0] for i in self._extensionsAndIsDir]
  

    
class FileFormats( object ):
  def __init__( self, name ):
    self.name = name
    self._formatsByExtension = {}
    self._formatsByName = { 'Directory': Format( 'Directory', ( 'd|', ) ) }
    self._formatLists = {}
    self._alias = {}

  
  def newFormat( self, name, extensions ):
    f = self._formatsByName.get( name )
    if f is not None:
      raise KeyError( _( 'Format "%s" already defined' ) % ( name,) )
    f = Format( name, extensions )
    self._formatsByName[ name ] = f
    for oe, d in f._extensionsAndIsDir:
      le = oe.lower()
      ue = oe.upper()
      for e in set ( ( oe, le, ue, ue[0] + le[1:] ) ):
        of = self._formatsByExtension.get( e )
        if of is not None:
          raise KeyError( _( 'Cannot define format "%(f2)s" because file extension "*.%(e)s" is already used by format "%(f1)s"' ) % { 'e': e, 'f1': of.name, 'f2': f.name } )
        self._formatsByExtension[ e ] = f
  
  
  def newAlias( self, alias, format ):
    f = self._formatsByName.get( alias )
    if f is not None:
      raise KeyError( _( 'Format "%s" already defined' ) % ( alias,) )
    a = self._alias.get( alias )
    if a is not None:
      raise KeyError( _( 'Format alias "%s" already defined' ) % ( alias,) )
    self._alias[ alias ] = self.getFormat( format )
  
  
  def getFormat( self, format, default=Undefined ):
    if isinstance( format, Format ):
      return format
    f = self._formatsByName.get( format )
    if f is None:
      f = self._alias.get( format )
    if f is None:
      if default is Undefined:
        raise KeyError( _( 'Unknown format "%s"' ) % ( format, ) )
      return default
    return f
  
  
  def update( self, fileFormat ):
    self._formatsByExtension.update( fileFormat._formatsByExtension )
    self._formatsByName.update( fileFormat._formatsByName )
    self._formatLists.update( fileFormat._formatLists )
    self._alias.update( fileFormat._alias )
    
  
  def _findMatchingFormat( self, f ):
    format = None
    noExt = ext = None
    dotIndex = f.find( '.' )
    if dotIndex > -1:
      ext = f[ dotIndex + 1 : ]
      noExt = f[ : dotIndex ]
      while True:
        format = self._formatsByExtension.get( ext )
        if format is not None:
          break
        dotIndex = ext.find( '.' )
        if dotIndex == -1:
          break
        noExt = noExt + '.' + ext[ : dotIndex ]
        ext = ext[ dotIndex + 1 : ]
    return ( format, ext, noExt )
  
  
  def newFormatList( self, name, formats ):
    if self._formatLists.has_key( name ):
      raise KeyError( _( 'Format list "%s" already defined' ) % ( name,) )
    self._formatLists[ name ] = tuple( (self._formatsByName[ f ] for f in formats) )
  
  
  def read( self, fileName ):
    context = { 'newFormat': self.newFormat, 'newFormatList': self.newFormatList }
    execfile( fileName, context, context )


  def identify( self, directoryIterator ):
    unknown = []
    known = []
    minfs = {}
    stack = dict( (i.fullPath(),i) for i in directoryIterator.listDir() )
    while stack:
      f,it = stack.popitem()
      #print '!identify! "' +  f + '"'
      format, ext, noExt = self._findMatchingFormat( f )
      if format is None:
        if it.isDir():
          format, ext, noExt = self.getFormat( 'Directory' ), '', f
        else:
          if not f.endswith( '.minf' ):
            #print '!identify! --> unknown'
            unknown.append( it )
          continue
      elif format.name == 'Minf':
        minfs[ f ] = ( noExt, [ f ], f, format.name, it )
        continue

      if len( format._extensionsAndIsDir ) == 1:
        #print '!identify!  format with only one file'
        files = [ f ]
      else:
        files = []
        for fext, isdir in format._extensionsAndIsDir:
          other = noExt + '.' + fext
          stack.pop( other, None )
          files.append( other )
      fext = format._extensionsAndIsDir[0][0]
      if fext:
        minf = noExt + '.' + fext + '.minf'
      else:
        minf = noExt + '.minf'
      if minfs.pop( minf, None ) is None and stack.pop( minf, None ) is None:
        minf = None
      #if minf is None:
        #print '!identify!  no minf file found: "' + minf + '"'
      #else:
        #print '!identify!  minf file "' + minf + '"'
      #print '!identify! -->', noExt, files, minf, format.name
      known.append( ( noExt, files, minf, format.name, it ) )
    # add remaining .minfs
    known += minfs.values()
    return known, unknown
