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
import stat, os, cStringIO, types
from brainvisa import shelltools
from UserDict import UserDict



#-------------------------------------------------------------------------------
class VirtualDirectory:
  '''A VirtualDirectory is a place where file- or directory-like data are stored
  (local file system, ftp server, data base, etc.). A VirtualDirectory have a
  name. That name is used whith a VirtualDirectoriesManager to build URL-like identifiers.'''
  


  #-------------------------------------------------------------------------------
  class Item( UserDict ):
    '''A VirtualDirectory.Item is either a binary block of data or directory
    like structure containing VirtualDirectory.Items.'''

    def __init__( self, virtualDirectory = None ):
      self.virtualDirectory = virtualDirectory

    def size( self ):
      '''Return the size of the binary data (in bytes) or None if the size is
      unknown. The size of a VirtualDirectory.Item with children may be None
      or the sum of the size of all children (and sub-children) that do not
      have child.'''
      return None

    def reader( self ):
      '''Return a opened file compatible object that can be used to read binary
      data. If the self.hasChildren() returns True, this method throws an
      exception.'''

      return cStringIO.StringIO( '' )

    def hasChildren( self ):
      '''Returns True if the object has one or more children.'''

      return False

    def children( self ):
      '''Returns a generator (or a sequence) of VirtualDirectory.Item objects.'''
      return ()


    def fullName( self ):
      '''Return an identifier wich is unique in the VirtualDirectory where 
      the data comes from. This identifier can be stored and used later with
      the VirtualDirectory's get() method in order to get a
      VirtualDirectory.Item for the same data. May return None if the
      identifier cannot be build. A typical value for this identifier is the
      full path of a file relative to the virtual directory.'''
      return None

    def name( self ):
      '''Return the short name of the data. If not empty, this value can be
      used to create a file or directory name for the data. Therefore, it does
      not contain directory separator nor characters forbidden for file names.
      A typical value for name() is the file name without its parent path.'''
      return ''


    def globalName( self ):
      '''Return an identifier wich is unique in the VirtualDirectoryManager where the 
      VirtualDirectory containing the data is registered. This identifier can be stored
      and used later with the virtual directory manager's get() method in order to get a 
      VirtualDirectory.Item for the same data. May return an empty string if the identifier
      cannot be build.'''

      if self.virtualDirectory is not None and self.virtualDirectory.manager is not None:
        virtualDirectory = self.virtualDirectory.name()
        if virtualDirectory:
          me = self.fullName()
          if me is not None:
            return self.virtualDirectory.manager.join( virtualDirectory, me )
      return None


    def parent( self ):
      '''Return the virtualDirectory.Item corresponding to this item's parent
      directory. May return None if either the parent cannot be easily found
      (e.g. in a non hierarchical storage implementation).'''
      if self.virtualDirectory is not None:
        return self.virtualDirectory.get( self.parentFullName() )
      return None


    def parentFullName( self ):
      '''Equivalent to parent().fullName() but may be faster. May return None.'''
      return None



    def __str__( self ):
      result = self.globalName()
      if result is None:
        result = self.fullName()
        if result is None:
          result = self.name()
      return result


  def __init__( self, manager = None ):
    self.manager = manager
  
  
  def get( identifier ):
    '''Return a VirtualDirectory.Item corresponding to a string identifier.'''
    return None


  def set( identifier, binHandle,
           bufferSize,
           startCallBack,
           progressCallback,
           endCallback ):
    '''Copy the content of a VirtualDirectory.Item coming from any VirtualDirectory into this
    VirtualDirectory with the given identifer.'''
    raise RuntimeError( 'virtual directory is read only' )



  def name( self ):
    '''Return the virtual directory name. May return an empty string if the virtual directory has
    no name. This name is used when several virtual directories are registered in a 
    VirtualDirectoryManager.'''
    return ''


  def __str__( self ):
    return self.name()


#-------------------------------------------------------------------------------
class VirtualDirectoriesManager:
  def __init__( self ):
    self.__virtualDirectories = {}

  def split( self, identifier ):
    index = identifier.find( ':' )
    if index >= 0:
      return ( identifier[ :index ], identifier[ index+1: ] )
    else:
      return ( identifier, '' )
  
  def join( self, virtualDirectoryId, binId ):
    return virtualDirectoryId + ':' + binId
    
  def getVirtualDirectory( self, virtualDirectoryId ):
    return self.__virtualDirectories.get( virtualDirectoryId )

  def registerVirtualDirectory( self, virtualDirectory ):
    key = virtualDirectory.name()
    if self.__virtualDirectories.has_key( key ):
      raise RuntimeError( 'virtual directory "%s" already registered' % ( key, ) )
    if virtualDirectory.manager is not None:
      raise RuntimeError( 'virtual directory "%s" already registered in another VirtualDirectoriesManager' % ( key, ) )
    virtualDirectory.manager = self      
    self.__virtualDirectories[ key ] = virtualDirectory

  def get( self, identifier ):
    virtualDirectoryId, binId  = self.split( identifier )
    virtualDirectory = self.getVirtualDirectory( virtualDirectoryId )
    if virtualDirectory is not None:
      return virtualDirectory.get( binId )
    return None

  def set( self, identifier, binHandle,
           bufferSize = 32768,
           startCallback = None,
           progressCallback = None,
           endCallback = None ):
    virtualDirectoryId, binId  = self.split( identifier )
    virtualDirectory = self.getVirtualDirectory( virtualDirectoryId )
    if virtualDirectory is not None:
      virtualDirectory.set( binId, binHandle,
        bufferSize = bufferSize,
        startCallback = startCallback,
        progressCallback = progressCallback,
        endCallback = endCallback )
    else:
      raise RuntimeError( 'No virtual directory named "%s"' %( virtualDirectory, ) )


