import os


class DirectoryIterator( object ):
  def __init__( self, fileOrDirectory ):
    self.__fileOrDirectory = fileOrDirectory
    self.__isDir = os.path.isdir( fileOrDirectory )
  
  
  def fullPath( self ):
    return self.__fileOrDirectory
  
  
  def fileName( self ):
    return os.path.basename( self.__fileOrDirectory )
  
  
  def isDir( self ):
    return self.__isDir
  
  
  def listDir( self ):
    return (DirectoryIterator(f) for f in (os.path.join( self.__fileOrDirectory, i ) for i in os.listdir( self.__fileOrDirectory ) ) )


class VirtualDirectoryIterator( object ):
  def __init__( self, baseDirectory, content ):
    self.__baseDirectory = baseDirectory
    self.__content = content
  
  
  def fullPath( self ):
    return self.__baseDirectory
  
  
  def fileName( self ):
    return os.path.basename( self.__baseDirectory )
  
  
  def isDir( self ):
    return self.__content is not None
  
  
  def listDir( self ):
    return (VirtualDirectoryIterator(f, content) for f,content in ((os.path.join( self.__baseDirectory, name ),c) for name, c in self.__content ) )
  
  