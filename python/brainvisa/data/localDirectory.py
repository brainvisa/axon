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

import os, stat

from brainvisa.data import virtualDirectory

#-------------------------------------------------------------------------------
class LocalDirectory( virtualDirectory.VirtualDirectory ):

  class Item( virtualDirectory.VirtualDirectory.Item ):
    def __init__( self, s, fileName ):
      virtualDirectory.VirtualDirectory.Item.__init__( self, s )
      self.__fileName = os.path.normpath( fileName )
      
    def size( self ):
      try:
        fileStat = os.stat( self.__fileName )
        if stat.S_ISDIR( fileStat[ST_MODE] ):
          return None
        else:
          return fileStat[ stat.ST_SIZE ]
      except:
        return None
          
    def reader( self ):
      return open( self.__fileName, 'rb' )

    def hasChildren( self ):
      fileStat = os.stat( self.__fileName )
      if stat.S_ISDIR( fileStat[stat.ST_MODE] ):
        return True
      else:
        return False

    def children( self ):
      result = []
      for file in os.listdir( self.__fileName ):
        result.append( LocalDirectory.Item( self.virtualDirectory, os.path.join( self.__fileName, file ) ) )
        return result

    def name( self ):    
      return os.path.basename( self.__fileName )
    
    def fullName( self ):
      if self.virtualDirectory:
        return self.virtualDirectory._LocalDirectory__binIdFromPath( self.__fileName )
      return self.__fileName
        
    def parentFullName( self ):
      p = os.path.dirname( self.__fileName )
      if self.virtualDirectory:
        return self.virtualDirectory._LocalDirectory__binIdFromPath( p )
      return p

  def __init__( self, name, baseDirectory='/' ):
    virtualDirectory.VirtualDirectory.__init__( self )
    self.__name = name
    self.__baseDirectory = baseDirectory

  def __pathFromBinId( self, binId ):
    if binId:
      if binId[ 0 ] in ( os.sep, os.altsep ):
        return os.path.join( self.__baseDirectory, binId[ 1: ] )
      return os.path.join( self.__baseDirectory, binId )
    else:
      return self.__baseDirectory

  def __binIdFromPath( self, path ):
    if self.__baseDirectory in ( os.sep, os.altsep ):
      return path[ 1: ]
    else:
      return path[ len( self.__baseDirectory ) + 1: ]
      
    
  def get( self, binId ):
    return self.Item( self, self.__pathFromBinId( binId ) )
  
  def set( self, binId, virtualDirectoryItem,
           bufferSize = 32768,
           startCallback = None,
           progressCallback = None,
           endCallback = None ):
 
    if virtualDirectoryItem.hasChildren():
      directory = self.__pathFromBinId( binId )
      if os.path.exists( directory ): shelltools.rm( directory )
      try:
        os.mkdir( directory )
      except OSError, e:
        if not e.errno == os.errno.EEXIST:
          # filter out 'File exists' exception, if the same dir has been created
          # concurrently by another instance of BrainVisa or another thread
          raise
      for child in virtualDirectoryItem.children():
        name = virtualDirectoryItem.name()
        if not name:
          raise RuntimeError( _t_( 'Cannot create path for unnamed data' ) )
        self.set( os.path.join( directory, name ), virtualDirectoryItem,
          bufferSize = bufferSize,
          startCallback = startCallback,
          progressCallback = progressCallback,
          endCallback = endCallback )
    else:
      reader = virtualDirectoryItem.reader()
      if startCallback is not None:
        startCallback( str( virtualDirectoryItem ) )
      totalRead = 0
      byteRead = bufferSize
      writer = open( self.__pathFromBinId( binId ), 'wb' )
      while byteRead == bufferSize:
        data = reader.read( bufferSize )
        writer.write( data )
        byteRead = len( data )
        totalRead += byteRead
        if progressCallback is not None:
          progressCallback( byteRead, totalRead )
      if endCallback is not None:
        endCallback( totalRead )

  def name( self ):
    return self.__name

