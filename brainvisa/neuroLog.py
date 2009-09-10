# -*- coding: iso-8859-1 -*-
# Copyright CEA (2000-2005)
#
#  This software and supporting documentation were developed by
#      CEA/DSV/SHFJ
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

import os, threading, shutil, time, weakref

from soma.minf.api import iterateMinf, createMinfWriter
from brainvisa.data import temporary
import neuroConfig, neuroException
import gzip


#------------------------------------------------------------------------------
class FileLink:
  pass


#------------------------------------------------------------------------------
class TextFileLink( FileLink ):
  def __init__( self, fileName ):
    self.fileName = unicode( fileName )
  
  def expand( self ):
    result = None
    try:
      file = open( self.fileName, 'r' )
      result = file.read()
      file.close()
    except:
      result = neuroException.exceptionHTML()
    return result
  
  def __getinitargs__( self ):
    return ( self.fileName, )



#------------------------------------------------------------------------------
class LogFileLink( FileLink ):
  def __init__( self, fileName ):
    self.fileName = unicode( fileName )
  
  def expand( self ):
    try:
      reader = LogFileReader( self.fileName )
      result = reader.read()
      reader.close()
    except:
      result = [ LogFile.Item( icon='error.png', what='Error', html=neuroException.exceptionHTML() ) ]
    return result
  
  def __getinitargs__( self ):
    return ( self.fileName, )


#------------------------------------------------------------------------------
class LogFile:


  #----------------------------------------------------------------------------
  class SubTextLog( TextFileLink ):
    def __init__( self, fileName, parentLog ):
      self.fileName = fileName
      # Create empty file
      file = open( unicode( self.fileName ), 'w' )
      file.close()
      self._parent = parentLog

    def __del__( self ):
      self.close()

    def close( self ):
      if self.fileName is not None:
        self._parent._subLogClosed( self )
        self.fileName = None

  #----------------------------------------------------------------------------
  class Item:
    icon = 'logItem.png'
    
    def __init__( self, what, when=None, html='', children=[], icon=None ):
      self._what = unicode( what )
      if when is None:
        self._when = time.time()
      else:
        if not isinstance( when, float ):
          raise RuntimeError( _t_( 'Invalid when value' ) )
        self._when = when
      self._html = html
      if isinstance( children, LogFile ):
        self._children = LogFileLink( children.fileName )
      else:
        self._children = children
      self._icon = icon
          
    def what( self ):
      return self._what
      
    def when( self ):
      return self._when
      
    def html( self ):
      if isinstance( self._html, FileLink ):
        return self._html.expand()
      return unicode( self._html )
    
    def children( self ):
      children = self._children
      if isinstance( children, FileLink ):
        children = children.expand()
      else:
        for child in self._children:
          if isinstance(child, LogFile.Item):
            child._expand( {} )
      return children

    def icon( self ):
      return self._icon
      
    def _expand( self, openedFiles ):
      if isinstance( self._html, FileLink ) and \
         self._html.fileName not in openedFiles:
        self._html = self._html.expand()
      children = []
      for child in self.children():
        if isinstance( child, FileLink )and \
         child.fileName not in openedFiles:
          children.append( child.expand() )
        else:
          children.append( child )
      self._children = children
         
    def __getinitkwargs__( self ):
      kwattrs = dict( what=self._what )
      if self._when:
        kwattrs[ 'when' ] = self._when
      if self._html:
        kwattrs[ 'html' ] = self._html
      if self._children:
        kwattrs[ 'children' ] = self._children
      if self._icon:
        kwattrs[ 'icon' ] = self._icon
      return ( (), kwattrs )


  #----------------------------------------------------------------------------
  def __init__( self, fileName, parentLog, lock, file=None ):
    self._writer = None
    self._lock = lock
    self.fileName = fileName
    self._parent = parentLog
    self._opened = weakref.WeakValueDictionary()
    self._closed = set()
    if file is None:
      self._file = open( fileName, 'w' )
    else:
      self._file = file
    self._writer = createMinfWriter( self._file, format='XML', 
                                     reducer='brainvisa-log_2.0' )
    self._writer.flush()
  
  
  def __del__( self ):
    if self._writer is not None:
      self.close()
  
  
  def __getstate__( self ):
    raise RuntimeError( _t_( 'Cannot get state of LogFile' ) )
  
  
  def close( self ):
    if self._lock is None: return
    try:
      self._lock.acquire()
    except TypeError:
      self._lock = None
    try:
      for n,children in self._opened.items():
        children.close()
      if self._writer is not None:
        self._writer.flush()
        self._writer.close()
        self._writer = None
        self._file.close()
        self._file = None
        if self._parent is not None:
          self._parent._subLogClosed( self )
        self.fileName = None
    finally:
      if self._lock is not None:
        self._lock.release()
        self._lock = None
  
  
  def subLog( self, fileName = None ):
    self._lock.acquire()
    try:
      if fileName is None:
        fileName = temporary.manager.new()
      result = LogFile( fileName, self, self._lock )
      self._opened[ unicode( result.fileName ) ] = result
    finally:
      self._lock.release()
    return result

  
  def subTextLog( self, fileName = None ):
    self._lock.acquire()
    try:
      if fileName is None:
        fileName = temporary.manager.new()
      result = self.SubTextLog( fileName, self )
      self._opened[ unicode( result.fileName ) ] = result
    finally:
      self._lock.release()
    return result

  
  def _subLogClosed( self, subLog ):
    if self._lock is None: return
    self._lock.acquire()
    try:
      self._closed.add( subLog.fileName )
      self._opened.pop( unicode( subLog.fileName ), None )
    finally:
      self._lock.release()
   
   
  def append( self, *args, **kwargs ):
    self._lock.acquire()
    try:
      if not kwargs and \
         len( args ) == 1 and isinstance( args[ 0 ], LogFile.Item ):
        result = args[ 0 ]
      else:
        result = LogFile.Item( *args, **kwargs )
      self._writer.write( result )
      self._writer.flush()
    finally:
      self._lock.release()
    return result
  
  
  def expand( self, force=False ):
    if force:
      opened = {}
    else:
      opened = self._opened
    self._lock.acquire()
    try:
      self._writer.flush()
      self._file.close()
      self._file = None
      reader = LogFileReader( self.fileName )
      tmp = temporary.manager.new()
      writer = newLogFile( tmp )
      logItem = reader.readItem()
      while logItem is not None:
        logItem._expand( opened )
        writer.append( logItem )
        logItem = reader.readItem()
      reader.close()
      self._closed.clear()
      shutil.copyfile( tmp, self.fileName )
      self._file = open( self.fileName, 'a+' )
      self._writer.changeFile( self._file )
    finally:
      self._lock.release()
  
  
  def flush( self ):
    if self._writer is not None:
      self._writer.flush()
  




#------------------------------------------------------------------------------
def newLogFile( fileName, file=None ):
  return LogFile( fileName, None, threading.RLock(), file=file )


#------------------------------------------------------------------------------
class LogFileReader:
  def __init__( self, source ):
    self._iterator = iterateMinf( source )
  
  
  def close( self ):
    self._iterator = None
  
  
  def readItem( self ):
    try:
      return self._iterator.next()
    except StopIteration:
      return None
  
  
  def read( self ):
    return list( self._iterator )


#------------------------------------------------------------------------------
def expandedCopy( source, destFileName, destFile=None ):
  reader = LogFileReader( source )
  writer = newLogFile( destFileName, file=destFile )
  item = reader.readItem()
  while item is not None:
    writer.append( item.what(), when=item.when(), html=item.html(),
                   children=item.children(), icon=item.icon() )
    item = reader.readItem()
  reader.close()
  writer.flush()
  writer.close()


#------------------------------------------------------------------------------
def expandedReader( source ):
  reader = LogFileReader( source )
  item = reader.readItem()
  while item is not None:
    item._expand( {} )
    yield item
    item = reader.readItem()
  reader.close()
  
  
#------------------------------------------------------------------------------
def initializeLog():
  neuroConfig.mainLog = None
  try:
    if neuroConfig.logFileName:
      if os.path.exists( neuroConfig.logFileName ):
        shutil.copyfile( neuroConfig.logFileName, 
                         neuroConfig.logFileName + '~' )
      neuroConfig.mainLog = newLogFile( neuroConfig.logFileName )
  except Exception, e:
    import traceback
    traceback.print_exc()
    neuroConfig.mainLog = None


#------------------------------------------------------------------------------
def closeMainLog():
  if neuroConfig.mainLog is not None:
    tmpFileName = temporary.manager.new()
    logFileName = neuroConfig.mainLog.fileName
    neuroConfig.mainLog.close()
    
#TODO: compressing the log file corrupt its content
    dest = gzip.GzipFile( tmpFileName, 'wb', 9 )
#    dest = open( tmpFileName, 'wb' )
    expandedCopy( logFileName, tmpFileName, dest )
    dest = None
    shutil.copyfile( tmpFileName, logFileName )
    neuroConfig.mainLog = None


#------------------------------------------------------------------------------
def log( *args, **kwargs ):
  if neuroConfig.mainLog is not None:
    neuroConfig.mainLog.append( *args, **kwargs )
