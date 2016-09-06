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
import os
import sys
from soma.translation import translate as _
from soma.undefined import Undefined

if sys.version_info[0] >= 3:
    unicode = str


class Format( object ):
  def __init__( self, name, extensions, isMinf=False ):
    self.name = unicode( name )
    self.isMinf = isMinf
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

  
  def newFormat( self, name, extensions, isMinf=False ):
    f = self._formatsByName.get( name )
    if f is not None:
      raise KeyError( _( 'Format "%s" already defined' ) % ( name,) )
    f = Format( name, extensions, isMinf )
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
    path, filename = os.path.split( f )
    dotIndex = filename.find( '.' )
    if dotIndex > -1:
      dotIndex = len( path ) + dotIndex + 1
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
    elif os.path.isdir(f):
      format=self._formatsByName["Directory"]
      ext=None
      noExt=f
    return ( format, ext, noExt )


  def newFormatList( self, name, formats ):
    if self._formatLists.has_key( name ):
      raise KeyError( _( 'Format list "%s" already defined' ) % ( name,) )
    self._formatLists[ name ] = tuple( (self._formatsByName[ f ] for f in formats) )
  
  
  def read( self, fileName ):
    context = { 'newFormat': self.newFormat, 'newFormatList': self.newFormatList }
    execfile( fileName, context, context )


  def identify( self, directoryIterator, context=None ):
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
