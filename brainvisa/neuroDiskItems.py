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

import types, string, re, sys, os, stat, threading, cPickle, operator, time, traceback
from weakref import ref, WeakValueDictionary
from UserList import UserList
from threading import RLock

from soma.html import htmlEscape
from soma.undefined import Undefined
from soma.uuid import Uuid
from soma.path import split_path
from soma.minf.api import readMinf, MinfError
from soma.wip.application.api import Application

import neuroConfig
from neuroException import *
from brainvisa.data import temporary
from brainvisa.data.patterns import DictPattern
from brainvisa import shelltools
from brainvisa.multipleExecfile import MultipleExecfile

#----------------------------------------------------------------------------
def sameContent( a, b ):
  result = 0
  if type( a ) is type( b ):
    if type( a ) in ( types.ListType, types.TupleType ):
      result = 1
      i = 0
      for x in a:
        if not sameContent( x, b[i] ):
          result = 0
          break
        i += 1
    elif hasattr( a, 'sameContent' ):
      result = a.sameContent( b )
    else:
      result = a == b
  return result


#----------------------------------------------------------------------------
def modificationHashOrEmpty( f ):
  try:
    s = os.lstat( f )
    return ( s.st_mode, s.st_uid, s.st_gid, s.st_size, s.st_mtime, s.st_ctime )
  except OSError:
    return ()


#----------------------------------------------------------------------------
class DiskItem:
  """
  This class represents data stored in one or several files on a filesystem.
  It can have additional information stored in attributes and may be indexed in a Brainvisa database.
  """
  
  _minfLock=RLock()
  
  def __init__( self, name, parent ):
    self.name = name
    if name and name[ -5: ] != '.minf': 
      self._files = [ name ]
    else: self._files = []
    self.parent = parent
    if self.parent is None:
      self._topParentRef = ref( self )
    else:
      self._topParentRef = self.parent._topParentRef
    self._localAttributes = {}
    self._globalAttributes = {}
    self._minfAttributes = {}
    self._otherAttributes = {}
    self.type = None
    self.format = None
    self._setLocal( 'name_serie', [] )
    self._isTemporary = 0
    self._uuid = None
    self._write = False
    self._identified = False
    self._lock = RLock()
  
  
  def __getstate__( self ):
    state =  {
      'name': self.name,
      '_files': self._files,
      'parent': self.parent,
      '_localAttributes': self._localAttributes,
      '_globalAttributes': self._globalAttributes,
      '_minfAttributes': self._minfAttributes,
      '_otherAttributes': self._otherAttributes,
      '_uuid': self._uuid,
      '_write': self._write,
      '_identified': self._identified,
    }
    if self.type:
      state[ 'type' ] = self.type.id
    else:
      state[ 'type' ] = None
    if self.format:
      state[ 'format' ] = self.format.id
    else:
      state[ 'format' ] = None
    priority = getattr( self, '_priority', None )
    if priority is not None:
      state[ '_priority' ] = priority
    return state


  def __setstate__( self, state ):
    self.name = state[ 'name' ]
    self._files = state[ '_files' ]
    self.parent = state[ 'parent' ]
    if self.parent is None:
      self._topParentRef = ref( self )
    t = state[ 'type' ]
    if t: self.type = getDiskItemType( t )
    else: self.type = None
    t = state[ 'format' ]
    if t: self.format = getFormat( t )
    else: self.format = None
    self._localAttributes = state[ '_localAttributes' ]
    self._globalAttributes = state[ '_globalAttributes' ]
    self._minfAttributes = state[ '_minfAttributes' ]
    self._otherAttributes = state[ '_otherAttributes' ]
    self._isTemporary = 0
    priority = state.get( '_priority' )
    if priority is not None:
      self._priority = priority
    self._changeUuid( state.get( '_uuid' ) )
    self._write = state[ '_write' ]
    self._identified = state[ '_identified' ]
    if not hasattr( self, '_lock' ):
      self._lock = RLock()
  
  
  def __eq__( self, other ):
    if isinstance( other, basestring ):
      return other in self.fullPaths()
    return self is other or ( isinstance( other, DiskItem ) and self.fullPath() == other.fullPath() )


  def __ne__( self, other ):
    if isinstance( other, basestring ):
      return other not in self.fullPaths()
    return self is not other and ((not isinstance( other, DiskItem )) or self.fullPath() != other.fullPath() )
  
  
  def clone( self ):
    result = self.__class__( self.name, self.parent )
    result.__setstate__( self.__getstate__() )
    # Copy attributes so that they can be modified without
    # changing cloned item attributes
    self.copyAttributes( result )
    return result
  
  
  def _topParent( self ):
    try:
      return self._topParentRef()
    except AttributeError:
      pass
    if self.parent:
      p = self.parent
      while p.parent is not None:
        p = p.parent
      self._topParentRef = p._topParentRef
    else:
      self._topParentRef = ref( self )
    return self._topParentRef()
  
  
  def attributes( self ):
    result = {}
    self._mergeAttributes( result )
    return result


  def globalAttributes( self ):
    result = {}
    self._mergeGlobalAttributes( result )
    return result
  
  
  def localAttributes( self ):
    result = {}
    self._mergeLocalAttributes( result )
    return result


  def copyAttributes( self, other ):
    self._localAttributes = other._localAttributes.copy()
    self._globalAttributes = other._globalAttributes.copy()
    self._minfAttributes = other._minfAttributes.copy()
    self._otherAttributes = other._otherAttributes.copy()
  
  
  def _mergeAttributes( self, result ):
    result.update( self._globalAttributes )
    if self.parent:
      self.parent._mergeAttributes( result )
    result.update( self._localAttributes )
    result.update( self._otherAttributes )
    result.update( self._minfAttributes )


  def _mergeGlobalAttributes( self, result ):
    result.update( self._globalAttributes )
    if self.parent:
      self.parent._mergeGlobalAttributes( result )


  def _mergeLocalAttributes( self, result ):
    if self.parent:
      self.parent._mergeLocalAttributes( result )
    result.update( self._localAttributes )
    result.update( self._otherAttributes )
    result.update( self._minfAttributes )


  def _mergeHierarchyAttributes( self, result ):
    if self.parent:
      self.parent._mergeHierarchyAttributes( result )
    result.update( self._localAttributes )
    result.update( self._globalAttributes )


  def _mergeNonHierarchyAttributes( self, result ):
    if self.parent:

      self.parent._mergeNonHierarchyAttributes( result )
    result.update( self._otherAttributes )
    result.update( self._minfAttributes )


  def fileName( self, index=0 ):
    name_serie = self.get( 'name_serie' )
    if name_serie:
      return self.fileNameSerie( index / len( self._files ) , 
                                 index % len( self._files ) )
    if self._files: return self._files[index]
    else: return self.name


  def fileNames( self ):
    name_serie = self.get( 'name_serie' )
    if name_serie:
      result = []
      for number in name_serie:
        result += map( lambda x, number=number: expand_name_serie( x, number ),
                       self._files )
      return result
    if self._files: return self._files
    else: return [ self.name ]
  
  
  def fileNameSerie( self, serie, index=0 ):
    name_serie = self.get( 'name_serie' )
    if name_serie:
      return expand_name_serie( self._files[ index ],
                                name_serie[ serie ] )
    raise RuntimeError( HTMLMessage(_t_( '<em>%s</em> is not a file series' )) )
  
  
  def fileNamesSerie( self, serie ):
    name_serie = self.get( 'name_serie' )
    if name_serie:
      return map( lambda x, number=name_serie[serie]: expand_name_serie( x, number ),
                   self._files )
    raise RuntimeError( HTMLMessage(_t_( '<em>%s</em> is not a file series' )) )
  
  
  def fullName( self ):
    if self.parent is None:
      return self.name
    else:
      return os.path.join( self.parent.fullName(), self.name )

  def relativePath(self, index=0):
    """
    Gets the file path of this diskitem, relatively to the path of its root diskitem. 
    """
    database=self.get("database")
    if database is None:
      database=self.get("_database")
    path=self.fullPath(index)
    if database and path.startswith( database ):
      path=path[ len(database) +1: ]
    return path
    
  def fullPath( self, index=0 ):
    if self.parent is None:
      return self.fileName(index)
    else:
      return os.path.join( self.parent.fullPath(), self.fileName(index) )


  def fullPaths( self ):
    if self.parent is None:
      return self.fileNames()
    else:
      return map( lambda x, p=self.parent.fullPath(): os.path.join( p, x ),
                  self.fileNames() )

  def existingFiles(self):
    """
    Returns all files reprensented by this diskitem and that really exist.
    """
    files=[ f for f in self.fullPaths() if os.path.exists(f)]
    minfFile= self.minfFileName()
    if minfFile != self.fullPath() and os.path.exists(minfFile):
      files.append(minfFile)
    return files

  def fullPathSerie( self, serie, index=0 ):
    if self.parent is None:
      return self.fileNameSerie( serie, index )
    else:
      return os.path.join( self.parent.fullPath(), self.fileNameSerie( serie, index ) )


  def fullPathsSerie( self, serie ):
    if self.parent is None:
      return self.fileNamesSerie( serie )
    else:
      return map( lambda x, p=self.parent.fullPath(): os.path.join( p, x ),
                  self.fileNamesSerie( serie ) )


  def firstFullPathsOfEachSeries( self ):
    return map( lambda i, self=self: self.fullPathSerie( i ),
                range( len( self.get( 'name_serie' ) ) ) )


  def _getGlobal( self, attrName, default = None ):
    r = self._globalAttributes.get( attrName )
    if r is None:
      if self.parent: return self.parent._getGlobal( attrName, default )
      else: return default
    return r


  def _getLocal( self, attrName, default = None ):
    r = self._localAttributes.get( attrName )
    if r is None:
      if self.parent: return self.parent._getLocal( attrName, default )
      else: return default
    return r


  def _getOther( self, attrName, default = None ):
    r = self._otherAttributes.get( attrName )
    if r is None:
      if self.parent: return self.parent._getOther( attrName, default )
      else: return default
    return r
  
  
  def get( self, attrName, default = None ):
    r = self._globalAttributes.get( attrName )
    if r is None: r = self._minfAttributes.get( attrName )
    if r is None: r = self._otherAttributes.get( attrName )
    if r is None: r = self._localAttributes.get( attrName )
    if r is None:
      info = aimsFileInfo( self.fullPath() )
      for k, v in info.iteritems():
        self._otherAttributes.setdefault( k, v )
      r = info.get( attrName )
    if r is None:
      if self.parent: return self.parent.get( attrName, default )
      else: return default
    return r


  def __getitem__( self, attrName ):
    r = self.get( attrName )
    if r is None: raise KeyError( attrName )
    return r


  def getInTree( self, attrPath, default = None, separator = '.' ):
    item = self
    stack = attrPath.split( separator )
    while stack and item is not None:
      item = item.get( stack.pop(0) )
    if item is None or stack:
      return default
    return item
  
  
  def getHierarchy( self, attrName, default = None ):
    r = self._globalAttributes.get( attrName )
    if r is None: r = self._localAttributes.get( attrName )
    if r is None:
      if self.parent: return self.parent.getHierarchy( attrName, default )
      else: return default
    return r


  def getNonHierarchy( self, attrName, default = None ):
    r = self._minfAttributes.get( attrName )
    if r is None: r = self._otherAttributes.get( attrName )
    if r is None:
      if self.parent: return self.parent.getNonHierarchy( attrName, default )
      else: return default
    return r
  
  
  def nonHierarchyAttributes( self ):
    result = {}
    self._mergeNonHierarchyAttributes( result )
    return result
  
  
  def hierarchyAttributes( self ):
    result = {}
    self._mergeHierarchyAttributes( result )
    return result
  
  
  def has_key( self, attrName ):
    r = self._minfAttributes.has_key( attrName )
    if r: return r
    r = self._otherAttributes.has_key( attrName )
    if r: return r
    r = self._localAttributes.has_key( attrName )
    if r: return r
    r = self._globalAttributes.has_key( attrName )
    if r: return r
    if self.parent: return self.parent.has_key( attrName )
    return 0
  
  
  def _setGlobal( self, attrName, value ):
    if self.parent and self.parent._getGlobal( attrName ) is not None:
      raise AttributeError( HTMLMessage(_t_('a global attribute <em>%s</em> already exists in item <em><code>%s</code></em>') % ( str(attrName), str(self) )) )
    self._globalAttributes[ attrName ] = value
  
  
  def _updateGlobal( self, dict ):
    for attrName, value in dict.items():
      self._setGlobal( attrName, value )
  
  
  def _setLocal( self, attrName, value ):
    if self._getGlobal( attrName ) is not None:
      raise AttributeError( HTMLMessage(_t_('a global attribute <em>%s</em> already exists in item <em><code>%s</code></em>') % ( str(attrName), str(self) )) )
    self._localAttributes[ attrName ] = value
  
  
  def _updateLocal( self, dict ):
    for attrName, value in dict.items():
      self._setLocal( attrName, value )
  
  
  def _setOther( self, attrName, value ):
    if self._getGlobal( attrName ) is not None:
      raise AttributeError( HTMLMessage(_t_('a global attribute <em>%s</em> already exists in item <em><code>%s</code></em>') % ( str(attrName), str(self) )) )
    minfValue = self._minfAttributes.get( attrName, Undefined )
    if minfValue is Undefined:
      self._otherAttributes[ attrName ] = value
    elif minfValue != value:
      raise AttributeError( HTMLMessage(_t_('a MINF attribute <em>%s</em> already exists in item <em><code>%s</code></em>') % ( str(attrName), str(self) )) )

  
  def _updateOther( self, dict ):
    for attrName, value in dict.items():
      self._setOther( attrName, value )


  def setMinf( self, attrName, value, saveMinf = True ):
    self._otherAttributes.pop( attrName, None )
    self._minfAttributes[ attrName ] = value
    if saveMinf:
      minf = self._readMinf()
      if minf is None: minf = {}
      minf[ attrName ] = value
      self._writeMinf( minf )
  
  
  def minf( self ):
    return self._minfAttributes
  
  
  def updateMinf( self, dict, saveMinf = True ):
    for attrName, value in dict.items():
      self._otherAttributes.pop( attrName, None )
      self._minfAttributes[ attrName ] = value
    if saveMinf:
      minf = self._readMinf()
      if minf is None: minf = {}
      minf.update( dict )
      self._writeMinf( minf )
  
  
  def isReadable( self ):
    result = 1
    for p in self.fullPaths():
      if not os.access( p, os.F_OK + os.R_OK ):
        result = 0
        break
    return result


  def isWriteable( self ):
    result = 1
    for p in self.fullPaths():
      if not os.access( p, os.F_OK + os.R_OK + os.W_OK ):
        result = 0
        break
    return result


  def __repr__( self ):
    return repr( self.fullPath() )


  def childs( self ):
    return None
  
  
  def __str__( self ):
    return self.fullPath()


  def setFormatAndTypeAttributes( self, writeOnly=0 ):
    # Set format attributes
    if self.format is not None:
      self.format.setAttributes( self, writeOnly=writeOnly )
    # Set type attributes
    if self.type is not None:
      self.type.setAttributes( self, writeOnly=writeOnly )
    if not writeOnly:
      # Set local file attributes
      self.readAndUpdateMinf()
    return self


  def priority( self ):
    if getattr( self, '_priority', None ) is not None:
      return self._priority
    if self.parent is not None:
      return self.parent.priority()
    return getattr( self, '_defaultPriority', 0 )

  
  def setPriority( self, newPriority, priorityOffset=0 ):
    self._priority = newPriority
    if priorityOffset:
      self._priority = self.priority() + priorityOffset
  
  
  def minfFileName( self ):
    if self.format is not None and ( isinstance( self.format, MinfFormat ) or self.format.name == 'Minf' ):
      return self.fullPath()
    else:
      return self.fullPath() + '.minf'
  
  
  def saveMinf( self, overrideMinfContent = None ):
    minfContent = {}
    if self._uuid is not None:
      minfContent[ 'uuid' ] = str( self._uuid )
    if overrideMinfContent is None:
      minfContent.update( self._minfAttributes )
    else:
      minfContent.update( overrideMinfContent )
    if self._isTemporary: temporary.manager.registerPath( self.minfFileName() )
    self._writeMinf( minfContent )
  
  
  def removeMinf( self, attrName, saveMinf = True ):
    del self._minfAttributes[ attrName ]
    if saveMinf:
      minf = self._readMinf()
      if minf is not None:
        if minf.pop( attrName, Undefined ) is not Undefined:
          self._writeMinf( minf )
  
  
  def clearMinf( self, saveMinf = True  ):
    self._minfAttributes.clear()
    if saveMinf:
      minf = self.minfFileName()
      if os.path.exists( minf ):
        os.remove( minf )
  
  
  def _readMinf( self ):
    attrFile = self.minfFileName()
    if os.path.exists( attrFile ):
      try:
        f = open( attrFile )
        minfContent = readMinf( f )[ 0 ]
        # Ignor huge DICOM information produced by NMR 
        # and stored in 'dicom' key.
        if minfContent: minfContent.pop( 'dicom', None )
        f.close()
        return minfContent
      except:
        showException( beforeError = \
                       _t_('in file <em>%s</em><br>') % attrFile )
    return None
  
  
  def _writeMinf( self, minfContent ):
    minf = self.minfFileName()
    if minfContent:
      file = open( minf, 'w' )
      print >> file, 'attributes = ' + repr( minfContent )
      file.close()
    else:
      if os.path.exists( minf ):
        os.remove( minf )
  
  
  def readAndUpdateMinf( self ):
    self._lock.acquire()
    try:
      attrs = self._readMinf()
      if attrs is not None:
        if attrs.has_key( 'uuid' ):
          self._changeUuid( Uuid( attrs[ 'uuid' ] ) )
          del attrs[ 'uuid' ]
        self.updateMinf( attrs, saveMinf=False )
    finally:
      self._lock.release()
  
  
  def createParentDirectory( self ):
    p = os.path.dirname( self.fullPath() )
    if not os.path.exists( p ):
      try:
        os.makedirs( p )
      except OSError, e:
        if not e.errno == os.errno.EEXIST:
          # filter out 'File exists' exception, if the same dir has been created
          # concurrently by another instance of BrainVisa or another thread
          raise


  def isTemporary( self ):
    return self._isTemporary


  def distance( self, other ):
    '''Returns a value that represents a sort of distance between two DiskItems.
       The distance is not a number but distances can be sorted.'''
    # Count the number of common hierarchy attributes
    hierarchyCommon = \
      reduce( 
        operator.add, 
        map( 
          lambda nv, other=other: other.getHierarchy( nv[ 0 ] ) == nv[ 1 ], 
          self.hierarchyAttributes().items() ),
        self.type is other.type )
    # Count the number of common non hierarchy attributes
    nonHierarchyCommon = \
      reduce( 
        operator.add, 
        map( 
          lambda nv, other=other: other.getNonHierarchy( nv[ 0 ] ) == nv[ 1 ], 
          self.nonHierarchyAttributes().items() ),
        self.type is other.type )
    return ( -hierarchyCommon, self.priority() - other.priority(), -nonHierarchyCommon, )


  def _changeUuid( self, newUuid ):
    self._uuid = newUuid
    if newUuid is not None:
      _uuid_to_DiskItem[ newUuid ] = self
  

  def setUuid( self, uuid, saveMinf=True ):
    self._changeUuid( Uuid( uuid ) )
    if saveMinf:
      attrs = self._readMinf()
      if not attrs:
        attrs = {}
      if attrs.get( 'uuid' ) != self._uuid:
        attrs[ 'uuid' ] = self._uuid
        try:
          self._writeMinf( attrs )
        except Exception, e:
          raise MinfError( _t_( 'uuid cannot be saved in minf file' ) + ': ' + unicode( e ) )
  
  
  def uuid( self, saveMinf=True ):
    if self._uuid is None:
      self._minfLock.acquire()
      try:
        attrs = self._readMinf()
        if attrs and attrs.has_key( 'uuid' ):
          self._changeUuid( Uuid( attrs[ 'uuid' ] ) )
        else:
          self.setUuid( Uuid(), saveMinf=saveMinf )
      finally:
        self._minfLock.release()
    return self._uuid
  
  
  def findFormat(self, amongFormats=None):
    """
    Find the format of this diskItem : the format whose pattern matches this diskitem's filename.
    Does nothing if this item has already a format. 
    Doesn't take into account format whose pattern matches any filename (*). 
    Stops when a matching format is found : 
      - item name is modified (prefix and suffix linked to the format are deleted)
      - item list of files is modified accoding to format patterns
      - the format is applied to the item
      - setFormatAndTypesAttributes method is applied
    """
    if not self.format:
      if not amongFormats:
        amongFormats=getAllFormats()
      for format in amongFormats:
        # don't choose a FormatSeries, we can't know if it is a serie only with the filename, FormatSeries has the same pattern as its base format.
        if not isinstance(format, FormatSeries) and "*" not in format.getPatterns().patterns: # pass formats that match any pattern, it can't be used to find the format only with filename. To be used only contextually in hierarchy rules.
          m = format.match( self )
          if m:
            self.name = format.formatedName( self, m )
            self._files = format.unmatch( self, m )
            format.setFormat( self )
            self.setFormatAndTypeAttributes()
            break;

  def modificationHash( self ):
    """
    Return a value that can be used to assess modification of this 
    DiskItem. Two calls to modificationHash will return the same value if and 
    only if all files in the DiskItem have not changed. Note that the contents 
    of the files are not read, the modification hash rely only on os.stat.
    """
    files = self.fullPaths() + [ self.minfFileName() ]
    return tuple( [(f,) + tuple(modificationHashOrEmpty( f )) for f in files] )
  
  
  def eraseFiles( self ):
    for fp in self.fullPaths():
      if os.path.exists( fp ):
        shelltools.rm( fp )
    fp = self.minfFileName()
    if os.path.exists( fp ):
      shelltools.rm( fp )
  
  
#----------------------------------------------------------------------------
class File( DiskItem ):
  def __init__( self, name, parent ):
    DiskItem.__init__( self, name, parent )



#----------------------------------------------------------------------------
class Directory( DiskItem ):
  def __init__( self, name, parent ):
    DiskItem.__init__( self, name, parent )
    self._childs = []
    self.lastModified = 0
    self.scanner = None
    if self.parent is None:
      self._automatic_update = True
      self._check_directory_time_only = False
  
  def __getstate__( self ):
    state = DiskItem.__getstate__( self )
    state[ '_childs' ] = self._childs
    state[ 'lastModified' ] = self.lastModified
    state[ 'scanner' ] = self.scanner
    return state
  
  
  def __setstate__( self, state ):
    DiskItem.__setstate__( self, state )
    self._childs = state[ '_childs' ]
    self.lastModified = state[ 'lastModified' ]
    self.scanner = state[ 'scanner' ]
    if self.parent is None:
      self._automatic_update = True
      self._check_directory_time_only = False
  
  
  def childs( self ):
    self._lock.acquire()
    try:
      if self.scanner is None: return []
      if not self._topParent()._automatic_update:
        return self._childs
      fullName = self.fullPath()
      if not os.path.isdir( fullName ):
        return []
      
      currentTime = int( time.time() )
      listdir = None
      if not self._topParent()._check_directory_time_only:
        modificationTime = 0
        #print 'directory', fullName, 'NOT smart'
        #sys.stdout.flush()
        listdir = []
        for n in os.listdir( fullName ):
          try:
            modificationTime = max( modificationTime, 
                        os.stat( os.path.join( fullName, n ) )[ stat.ST_MTIME ] )
            listdir.append( n )
          except:
            pass
      else:
        modificationTime = os.stat( fullName )[ stat.ST_MTIME ]
  
      debug = neuroConfig.debugHierarchyScanning
      if modificationTime >= self.lastModified:
        if debug:
          print >> debug, '----------------------------------------------'
          print >> debug, fullName, 'modified'
          print >> debug, '----------------------------------------------'
          print >> debug, 'modification time:', time.ctime( modificationTime )
          print >> debug, 'last modification:', time.ctime( self.lastModified )
          debug.flush()
        # Rescan directory
        childs = []
        if listdir is None: listdir = os.listdir( fullName )
        for n in listdir:
          if os.path.isdir( os.path.join( fullName, n ) ):
            childs.append( Directory( n, self ) )
          else:
            childs.append( File( n, self ) )
        if debug:
          print >> debug, 'children count:', len( childs )
        # Identify files
        if self.scanner:
          if self._childs:
            oldChilds={}
            for i in self._childs:
              oldChilds[ ( i.fileName(), i.type, i.format ) ] = i
            self._childs = self.scanner.scan( childs )
            for i in self._childs:
              old = oldChilds.get( ( i.fileName(), i.type, i.format )  )
              if isinstance( old, Directory ):
                i.lastModified = old.lastModified            
                i._childs = old._childs
          else :
            self._childs = self.scanner.scan( childs )
        else:
          self._childs = childs
        self.lastModified = currentTime
      result = self._childs
    finally:
      self._lock.release()
    return result






#----------------------------------------------------------------------------
def getId( name ):
  return  name.lower()

 

#----------------------------------------------------------------------------
class BackwardCompatiblePattern( DictPattern ):
  _msgBadPattern = '<em><code>%s</code></em> is not a valid pattern'

  def __init__( self, pattern ):
    i = pattern.find( '|' )
    if i >= 0:
      fileType = pattern[ :i ]
      # Check file type
      if fileType == 'fd':
        self.fileType = None
      elif fileType == 'f':
        self.fileType = File
      elif fileType == 'd':
        self.fileType = Directory
      else:
        raise ValueError( HTMLMessage(_t_(self._msgBadPattern) % pattern) )     
      p = pattern[ i+1: ]
    else:
      self.fileType = None
      p = pattern
    DictPattern.__init__( self, p )
    self.pattern = pattern
    
  def match( self, diskItem ):
    # Check File / Directory / both
    if self.fileType is not None:
      if diskItem.__class__ is not DiskItem and \
         not isinstance( diskItem, self.fileType ):
        return None

    result = DictPattern.match( self, os.path.basename( diskItem.name ), diskItem )
    return result      

  def unmatch( self, diskItem, matchResult, force=False ):
    if matchResult is None: return None
    if force:
      matchResult.setdefault( 'filename_variable', '' )
      matchResult.setdefault( 'name_serie', [] )
    return DictPattern.unmatch( self, matchResult, diskItem )
    

#----------------------------------------------------------------------------
class BackwardCompatiblePatterns:
  _typeMsg = '<em><code>%s</code></em> is not a valid pattern list'
   
  def __init__( self, patterns ):
    # Build Pattern list in self.patterns
    if type( patterns ) is types.StringType:
      self.patterns = [ BackwardCompatiblePattern( patterns ) ]
    elif type( patterns ) in ( types.TupleType, types.ListType ):
      self.patterns = []
      for i in patterns:
        if isinstance( i, BackwardCompatiblePattern ):
          self.patterns.append( i )
        else:
          self.patterns.append( BackwardCompatiblePattern( i ) )
    else:
      raise TypeError( HTMLMessage(_t_(self._typeMsg) % str( patterns )) )
            
  def match( self, diskItem, returnPosition=0 ):
    pos = 0
    for i in self.patterns:
      m = i.match( diskItem )
      if m:
        if returnPosition: return ( m, pos )
        return m
      pos += 1
    return None

  def unmatch( self, diskItem, matchResult, force = 0 ):
    return [ p.unmatch( diskItem, matchResult, force )
             for p in self.patterns ]

  def fileOrDirectory( self ):
    if self.patterns:
      result = self.patterns[0].fileType
      for p in self.patterns[ 1: ]:
        if p.fileType is not result: return None
      return result
    return None

  def __cmp__( self, other ):
    return self.patterns != other.patterns


#----------------------------------------------------------------------------
formats = {}
formatLists = {}


#----------------------------------------------------------------------------
class Format:
  _msgError = 'error in <em>%s</em> format'
  
  def __init__( self, formatName, patterns, attributes=None, exclusive=None, 
                ignoreExclusive=0 ):
    if type( formatName ) is not types.StringType:
      raise ValueError( HTMLMessage(_t_('<em><code>%s</code></em> is not a valid format name') % formatName) )

    tb=traceback.extract_stack(None, 2)
    self.fileName=tb[0][0]
    self.name = formatName
    self.id = getId( self.name )
    # Check patterns
    if isinstance( patterns, BackwardCompatiblePatterns ):
      self.patterns = patterns
    else:
      self.patterns = BackwardCompatiblePatterns( patterns )
    # Register self in formats
    f = formats.get( self.id )
    if f:
      if self.patterns != f.patterns:
        raise ValueError( HTMLMessage(_t_('format <em>%s</em> already exists whith a different pattern') % self.name) )
    else:
      formats[ self.id ] = self
    self._formatAttributes = attributes
    self._exclusive = exclusive
    self._ignoreExclusive = ignoreExclusive
    
  def __getstate__( self ):
    raise cPickle.PicklingError
  
  def match( self, item, returnPosition=0, ignoreExclusive=0 ):
    name = item.name
    if name[ -5: ] == '.minf':
      item.name = name[ : -5 ]
      result = self.patterns.match( item, returnPosition )
      item.name = name
    else:
      result = self.patterns.match( item, returnPosition )
    if self._exclusive and not ignoreExclusive:
      for f in getAllFormats():
        if f is not self and not f._ignoreExclusive and f.match( item, returnPosition, ignoreExclusive=1 ):
          return None
    return result

  def unmatch( self, diskItem, matchResult, force = 0 ):
    d, f = os.path.split( diskItem.name )
    if d:
      oldName = diskItem.name
      diskItem.name = f
      result = map( lambda x, d=d: os.path.join( d, x ), self.patterns.unmatch( diskItem, matchResult, force=force ) )
      diskItem.name = oldName
    else:
      result =  self.patterns.unmatch( diskItem, matchResult, force=force )
    return result

  def formatedName( self, item, matchResult ):
    star = matchResult.get( 'filename_variable' )
    if star:
      if item.parent is None:
        d = os.path.dirname( item.name )
        if d:
          return os.path.join( d, star )
      return star
    return item.name
  
  def setFormat( self, item, ruleMatchingInfo = None ):
    item.format = self
  
  def group( self, groupedItem, matchedItem, position=0 ):
    if isinstance( matchedItem, Directory ) and not isinstance( groupedItem, Directory ):
      # If a directory is grouped, the final DiskItem is a Directory
      tmp = groupedItem
      groupedItem = matchedItem
      matchedItem = tmp
      groupedItem.__dict__.update( matchedItem.__dict__ )
    if matchedItem.fileName()[ -5: ] == '.minf':
      return groupedItem
    groupedItem._files[ position:position ] = matchedItem._files
    return groupedItem
  
  def fileOrDirectory( self ):
    return self.patterns.fileOrDirectory()
  
  def __str__( self ):
    return self.name
  
  def __repr__( self ):
    return  repr( self.name )

  def setAttributes( self, item, writeOnly=0 ):
    attrs = self._formatAttributes
    if attrs is not None:
      if type( attrs ) is types.DictType:
        item._updateOther( attrs )
      elif callable( attrs ):
        item._updateOther( attrs( item, writeOnly=writeOnly ) )
      else:
        raise ValueError( HTMLMessage(_t_('Invalid attributes: <em>%s</em>') % htmlEscape( str(attrs) )) )

  def postProcessing( self, item ):
    pass

  def getPatterns( self ):
    return self.patterns


#----------------------------------------------------------------------------
class MinfFormat( Format ):
  pass
    
#----------------------------------------------------------------------------
class FormatSeries( Format ):
  def __init__( self, baseFormat, formatName=None, attributes=None ):
    baseFormat = getFormat( baseFormat )
    if isinstance( baseFormat, FormatSeries ):
      raise ValueError( HTMLMessage(_t_('Impossible to build a format series of <em>%s</em> which is already a format series' ) % ( baseFormat.name )) )
    if formatName is None:
      formatName = 'Series of ' + baseFormat.name
    if type( formatName ) is not types.StringType:
      raise ValueError( HTMLMessage(_t_('<em><code>%s</code></em> is not a valid format name') % formatName) )
    if attributes is None:
      attributes = baseFormat._formatAttributes
    
    tb=traceback.extract_stack(None, 2)
    self.fileName=tb[0][0]
    self.name = formatName
    self.id = getId( self.name )
    self.baseFormat = baseFormat
    registerFormat( self )
    self._formatAttributes = attributes
    self._ignoreExclusive = baseFormat._ignoreExclusive

  def match( self, *args, **kwargs ):
    return self.baseFormat.match( *args, **kwargs )

  def unmatch( self, *args, **kwargs ):
    return self.baseFormat.unmatch( *args, **kwargs )

  def formatedName( self, item, matchResult ):
    return self.baseFormat.formatedName( item, matchResult )
    
  def setFormat( self, item, ruleMatchingInfo=None ):
    item.format = self
    if ruleMatchingInfo is not None:
      rule, matchRule = ruleMatchingInfo
      ns = matchRule.get( 'name_serie' )
      matchRule[ 'name_serie' ] = '#'
      item.name = rule.pattern.unmatch( item, matchRule )
      matchRule[ 'name_serie' ] = ns
      item._files = self.unmatch( item, { 'filename_variable': item.name, } )
      if ns:
        item._getLocal( 'name_serie' ).append( ns )
      #if not isinstance( ns, basestring ):
        #ns.append( matchRule.get( 'name_serie' ) )

  def group( self, groupedItem, matchedItem, position=0, matchRule=None ):
    if isinstance( matchedItem, Directory ) and not isinstance( groupedItem, Directory ):
      # If a directory is grouped, the final DiskItem is a Directory
      tmp = groupedItem
      groupedItem = matchedItem
      matchedItem = tmp
      groupedItem.__dict__.update( matchedItem.__dict__ )
    if matchedItem.fileName()[ -5: ] == '.minf':
      return groupedItem
    if matchRule:
      ns = groupedItem._getLocal( 'name_serie' )
      if not isinstance( ns, basestring ):
        ns.append( matchRule.get( 'name_serie' ) )
    return groupedItem
    
  def fileOrDirectory( self ):
    return self.baseFormat.fileOrDirectory()

  def postProcessing( self, item ):
    name_serie = item.get( 'name_serie' )
    if len( name_serie ) > 1:
      # Sort name_serie by numeric order
      numbers = [ (long(i), i) for i in name_serie ]
      numbers.sort()
      name_serie = [ i[ 1 ] for i in numbers ]
      # Remove identical entries
      i = 1
      while i < len( name_serie ):
        if name_serie[ i ] == name_serie[ i-1 ]:
          del name_serie[ i ]
        else:
          i += 1
      item._setLocal( 'name_serie', name_serie )

  def getPatterns( self ):
    return self.baseFormat.patterns
  

#----------------------------------------------------------------------------
def changeToFormatSeries( format ):
  if isinstance( format, FormatSeries ):
    return format
  global formats
  result = formats.get( getId( 'Series of ' + format.name ), None )
  if not result:
    result = FormatSeries( format )
  return result


#----------------------------------------------------------------------------
def registerFormat( format ):
  global formats
  f = formats.get( format.id )
  if f:
    raise ValueError( HTMLMessage(_t_('format <em>%s</em> already exists') % format.name) )
  else:
    formats[ format.id ] = format


#----------------------------------------------------------------------------
def getFormat( item, default=Undefined ):
  if isinstance( item, Format ): return item
  elif isinstance( item, basestring ):
    if item == 'Graph': item = 'Graph and data'
    result = formats.get( getId( item ) )
    if result: return result
    if item.startswith( 'Series of ' ):
      result = changeToFormatSeries( getFormat( item[ 10: ] ) )
      if result: return result
  if default is Undefined:
    raise ValueError( HTMLMessage(_t_('<em><code>%s</code></em> is not a valid format') % str( item )) )
  return default


#----------------------------------------------------------------------------
class NamedFormatList( UserList ):
  def __init__( self, name, data ):
      self.name = name
      self.data = list(data)
      tb=traceback.extract_stack(None, 2)
      self.fileName=tb[0][0]

  
  def __str__( self ):
      return self.name

  def __repr__( self ):
      return repr( self.name )

  def __getstate__( self ):
    return ( self.name, self.data )
  
  def __setstate__( self, state ):
    self.name, self.data = state

  def __add__(self, other):
    if isinstance(other, UserList):
      return self.data + other.data
    elif isinstance(other, type(self.data)):
        return self.data + other
    else:
        return self.data + list(other)

  def __radd__( self, other ):
    if isinstance(other, UserList):
      return other.data + self.data
    elif isinstance(other, type(self.data)):
      return other + self.data
    else:
      return list(other) + self.data
      
  def __mul__(self, n):
      return self.data*n
  __rmul__ = __mul__


#----------------------------------------------------------------------------
def createFormatList( listName, formats=[] ):
  global formatLists
  key = getId( listName )
  if formatLists.has_key( key ):
    raise KeyError( listName )
  result = NamedFormatList( listName, getFormats( formats ) )
  formatLists[ key ] = result
  return result


#----------------------------------------------------------------------------
def getFormats( formats ):
  if formats is None: return None
  global formatLists
  if type( formats ) in types.StringTypes:
    key = getId( formats )
    result = formatLists.get( key )
    if result is None:
      result = [ getFormat( formats ) ]
  elif isinstance( formats, NamedFormatList ):
    return formats
  elif isinstance( formats, Format ):
    result = [formats]
  else:
    if [i for i in formats if not isinstance( i, Format )]:
      result = [getFormat(i) for i in formats]
    else:
      result = formats
  return result


#----------------------------------------------------------------------------
def getAllFormats():
  global formats
  return formats.values()

directoryFormat = Format( 'Directory', 'd|*', ignoreExclusive=1 )
fileFormat = Format( 'File', 'f|*', ignoreExclusive=1 )




#----------------------------------------------------------------------------
diskItemTypes = {}


#----------------------------------------------------------------------------
class DiskItemType:
  def __init__( self, typeName, parent = None, attributes=None ):
    # Check name
    if type( typeName ) is not types.StringType:
      raise ValueError( _t_('a type name must be a string') )
    
    tb=traceback.extract_stack(None, 3)
    self.fileName=tb[0][0]
    self.name = typeName
    self.id = getId( typeName )
    if parent is None: self.parent = None
    else: self.parent = getDiskItemType( parent )
    other = diskItemTypes.get( self.id )
    if other:
      if not sameContent( self, other ):
        raise ValueError( HTMLMessage(_t_( 'invalid redefinition for type <em>%s</em>') % self.name) )
    else:
      diskItemTypes[ self.id ] = self
    if attributes is None:
      if self.parent is not None:
        self._typeAttributes = self.parent._typeAttributes
      else:
        self._typeAttributes = None
    else:
      self._typeAttributes = attributes
  
  def __getstate__( self ):
    raise cPickle.PicklingError

  def setType( self, item, matchResult, formatPosition ):
    item.type = self

  def isA( self, diskItemType ):
    diskItemType = getDiskItemType( diskItemType )
    if diskItemType is self: return 1
    if self.parent is None: return 0
    return self.parent.isA( diskItemType )

  def parents( self ):
    if self.parent: return [ self.parent ] + self.parent.parents()
    return []

  def __str__( self ):
    return self.name

  def __repr__( self ):
    return '<' + str( self ) + '>'

  def setAttributes( self, item, writeOnly=0 ):
    attrs = self._typeAttributes
    if attrs is not None:
      if type( attrs ) is types.DictType:
        item.updateMinf( attrs )
      elif callable( attrs ):
        item.updateMinf( attrs( item, writeOnly=writeOnly ) )
      else:
        raise ValueError( HTMLMessage(_t_('Invalid attributes: <em>%s</em>') % htmlEscape( str(attrs) )) )


#----------------------------------------------------------------------------
def getDiskItemType( item ):
  if isinstance( item, DiskItemType ): return item
  elif type( item ) is types.StringType or type( item ) is types.UnicodeType:
    result = diskItemTypes.get( getId( item ) )
    if result: return result
  raise ValueError( HTMLMessage(_t_('<em><code>%s</code></em> is not a valid file or directory type') % str( item )) )


#----------------------------------------------------------------------------
def getAllDiskItemTypes():
  return diskItemTypes.values()


#----------------------------------------------------------------------------
def isSameDiskItemType( base, ref ):
  if base: return base.isA( ref )
  else: return ref is None



#----------------------------------------------------------------------------
class FileType( DiskItemType ):
  def __init__( self, typeName, parent = None, formats = None, minfAttributes = None ):
    # Check formats
    if formats:
      self.formats = getFormats( formats )
    elif parent:
      parent = getDiskItemType( parent )
      self.formats = parent.formats
    else:
      self.formats = None
    # Register type
    DiskItemType.__init__( self, typeName, parent, minfAttributes )

  def sameContent( self, other ):
    return isinstance( other, FileType ) and \
           self.__class__ is  other.__class__ and \
           sameContent( self.formats, other.formats ) and \
           sameContent( self.parent, other.parent )

#----------------------------------------------------------------------------
def expand_name_serie( text, number ):
  l = text.split( '#' )
  if len( l ) == 2:
    return l[0] + number + l[1]
  return text
 









#----------------------------------------------------------------------------
class TemporaryDirectory( Directory ):
  def __init__( self, name, parent ):
    self._isTemporary = 1
    if parent:
      fullPath = os.path.join( parent.fullPath(), name )
    else:
      fullPath = name
    if not os.path.isdir( fullPath ):
      try:
        os.mkdir( fullPath, 0770 )
      except OSError, e:
        if not e.errno == os.errno.EEXIST:
          # filter out 'File exists' exception, if the same dir has been created
          # concurrently by another instance of BrainVisa or another thread
          raise
    Directory.__init__( self, name, parent )


#----------------------------------------------------------------------------
class TemporaryDiskItem( File ):
  def __init__( self, name, parent ):
    File.__init__( self, name, parent )
    self._isTemporary = 1
    
  def __del__( self ):
    if Application().configuration.brainvisa.removeTemporary:
      toDelete = self.fullPaths()
      toDelete.append( toDelete[ 0 ] + '.minf' )
      #print 'deleting temp DI:', toDelete
      for f in toDelete:
        n = 0
        while 1:
          try:
            temporary.manager.removePath( f )
            break
          except:
            if n < 100:
              n += 1
              time.sleep( 0.01 )
              #print 'can\' delete', f, 'yet. waiting'
              #sys.stdout.flush()
            else:
              #print 'exception while removing', f
              showException( beforeError=_t_('temorary file <em>%s</em> not '
                                             'deleted<br>') % f, gui=0 )
              # giving up, let it for later
              temporary.manager.registerPath( f )
              print 'continuing after failed rm'
              sys.stdout.flush()
              break

  def clear( self ):
    for f in self.fullPaths():
      try:
        temporary.manager.removePath( f )
        temporary.manager.registerPath( f )
      except:
        showException( beforeError=_t_('temorary file <em>%s</em> not deleted<br>') % f,
          gui=0 )


#----------------------------------------------------------------------------
globalTmpDir = None


#----------------------------------------------------------------------------
def getTemporary( format, diskItemType = None, parent = None, name = None ):
  global globalTmpDir

  format = getFormat( format )
  if diskItemType is not None: diskItemType = getDiskItemType( diskItemType )
  if parent is None:
    if globalTmpDir is None:
      globalTmpDir = TemporaryDirectory( neuroConfig.temporaryDirectory, None )
    parent = globalTmpDir

  if name is None:
    name = temporary.manager.newFileName( directory=parent.fullPath() )
  if format.fileOrDirectory() is Directory:
    item = TemporaryDirectory( name, parent )
  else:
    item = TemporaryDiskItem( name, parent )
  item._files = format.unmatch( item, { 'filename_variable': name, 'name_serie': None }, 1 )
  item.format = format
  item.type = diskItemType
  toDelete = item.fullPaths()
  toDelete.append( toDelete[ 0 ] + '.minf' )
  for f in toDelete:
    temporary.manager.registerPath( f )
  return item


#----------------------------------------------------------------------------
_uuid_to_DiskItem = WeakValueDictionary()

#----------------------------------------------------------------------------
def getDataFromUuid( uuid ):
  if not isinstance( uuid, Uuid ):
    uuid = Uuid( uuid )
  return _uuid_to_DiskItem.get( uuid )

#----------------------------------------------------------------------------
class HierarchyDirectoryType( FileType ):
  def __init__( self, typeName, **kwargs ):
    FileType.__init__( self, typeName, None, directoryFormat, **kwargs )
  
#----------------------------------------------------------------------------
typesLastModification = 0
# mef is global to handle multiple call to readTypes since allready read
# file types are stored in it to prevent multiple loads which cause troubles.
class TypesMEF( MultipleExecfile ):
  def __init__( self ):
    super( TypesMEF, self ).__init__()
    self.localDict[ 'Format' ] = self.create_format
    self.localDict[ 'createFormatList' ] = self.create_format_list
    self.localDict[ 'FileType' ] = self.create_type
  
  
  def create_format( self, *args, **kwargs ):
    format = Format( *args, **kwargs )
    toolbox, module = self.currentToolbox()
    format.toolbox = toolbox
    format.module = module
    return format
  
  
  def create_format_list( self, *args, **kwargs ):
    format_list = createFormatList( *args, **kwargs )
    toolbox, module = self.currentToolbox()
    format_list.toolbox = toolbox
    format_list.module = module
    return format_list
  
  def create_type( self, *args, **kwargs ):
    type = FileType( *args, **kwargs )
    toolbox, module = self.currentToolbox()
    type.toolbox = toolbox
    type.module = module
    return type
  
  
  def currentToolbox( self ):
    file = self.localDict[ '__name__' ]
    toolbox = None
    module = None
    if file.startswith( neuroConfig.mainPath ):
      l = split_path( file[ len( neuroConfig.mainPath ) + 1: ] )
      if l and l[0] == 'toolboxes':
        if len( l ) >= 4:
          toolbox = l[ 1 ]
          module = '.'.join( l[ 2:] )
          if module.endswith( '.py' ):
            module = module[ :-3 ]
      elif l and l[0] == 'types':
        toolbox = 'axon'
        module = '.'.join( l )
        if module.endswith( '.py' ):
          module = module[ :-3 ]
    else:
      module = file
    return ( toolbox, module )
  
  

mef = TypesMEF()
mef.fileExtensions.append( '.py' )
def readTypes():
  global typesLastModification
  global mef
  mef.includePath.update(neuroConfig.typesPath)
  try:
    files = shelltools.filesFromShPatterns( *[os.path.join( path, '*.py' ) for path in neuroConfig.typesPath] )
    files.sort()
    mef.execute( continue_on_error=True, *files )
    typesLastModification = max( (os.stat(f).st_mtime for f in mef.executedFiles()) )
  except:
    showException()

#----------------------------------------------------------------------------
try:
  from soma import aims
  
  # Fix libxml2 multithreaded application issue by initializing parser from the main thread
  aims.xmlInitParser()
  
  _finder = aims.Finder()
  # don't resolve symlinks if file browser to be consistent with
  # all DiskItem namings
  try:
    aims.setQtResolveSymlinks( False )
  except:
    pass
except:
  _finder = None


#----------------------------------------------------------------------------
def aimsFileInfo( fileName ):
  from neuroProcesses import defaultContext
  from neuroProcessesGUI import mainThreadActions
  global _finder
  result = {}
  if fileName.endswith( '.ima.gz' ) or fileName.endswith( '.dim.gz' ) or fileName.endswith( '.ima.Z' ) or fileName.endswith( '.dim.Z' ):
    context = defaultContext()
    tmp = context.temporary( 'GIS image' )
    context.runProcess( 'uncompressGIS', fileName, tmp, False )
    fileName = tmp.fullPath()
  try:
    try:
      import numpy
      nan = numpy.nan
    except ImportError:
      nan = None
    if _finder is not None:
      finder = aims.Finder()
      if type( fileName ) is unicode:
        # convert to str
        import codecs
        fileName = codecs.getencoder( 'utf8' )( fileName )[0]
      # Finder is not thread-safe (yet)
      if mainThreadActions().call( finder.check, fileName ):
        result = eval( str(finder.header() ), locals())
    else:
      if neuroConfig.platform == 'windows':
        f=os.popen( 'AimsFileInfo -i "' + fileName + '"', 'r' )
      else:
        f=os.popen( 'AimsFileInfo -i "' + fileName + '" 2> /dev/null', 'r' )
      s = f.readline()
      while s and s != 'attributes = {\n': s = f.readline()
      s = s[13:-1] + f.read()
      result = eval( s , locals())
      f.close()
  except:
    pass
  return result
