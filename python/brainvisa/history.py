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

import os, time, shutil
from glob import glob
import weakref
import types
from gzip import open as gzipOpen
import threading

from soma.minf.api import writeMinf
from soma.uuid import Uuid
from soma.translation import translate as _
from soma.undefined import Undefined
from soma.minf.api import readMinf
from soma import safemkdir

from brainvisa.processing import neuroLog
from brainvisa.configuration import neuroConfig
from brainvisa.data import  neuroHierarchy
from brainvisa.processing import neuroException
from brainvisa.data.writediskitem import WriteDiskItem
from brainvisa.data.neuroDiskItems import DiskItem
from brainvisa.processes import defaultContext




minfHistory = 'brainvisa-history_2.0'


_sessionIDs = {}
_sessionsLock = threading.RLock()

def sessionId( database ):
  '''
  Manage an id / database in order to give an id for each bvsession. 
  '''
  global _sessionIDs
  global _sessionsLock
  #_sessionsLock.lock()
  if database is None:
    return neuroConfig.sessionID
  _sessionsLock.acquire()
  try:
    idDb = _sessionIDs.get( database, None )
    if idDb is None:
      idDb = Uuid()
      _sessionIDs[ database ] = idDb
    return idDb
  finally:
  #  _sessionsLock.acquire()
    _sessionsLock.release()




class HistoryBook( object ):
  '''
  An L{HistoryBook} contains some L{HistoricalEvent}.
  '''
  
  _allBooks = weakref.WeakValueDictionary()
  
  def __new__( cls, directory = None, database = None, dirBvsession = None, compression=False ):
    book = HistoryBook._allBooks.get( directory )
    if book is None:
      book = object.__new__( cls )
      HistoryBook._allBooks[ directory ] = book
    return book
  
  
  def __init__( self, directory = None, database = None, dirBvsession = None, compression=False ):
    if hasattr( self, '_HistoryBook__dir' ):
      # self has already been created but __init__ is always
      # called after __new__
      return
    if dirBvsession is None:
      dirBvsession = os.path.join( directory, 'bvsession' )
    self.uuid = Uuid()
    self.__compression = compression
    if not os.path.isdir( directory ):
      safemkdir.makedirs( directory )
    self.__dir = directory
    self.__database = database
    if not os.path.isdir( dirBvsession ):
      safemkdir.makedirs( dirBvsession ) 
    self.__dirBvsession = dirBvsession


  def storeEvent( self, event, compression=None , storeBvproc = False):
    if isinstance( event, ProcessExecutionEvent ):
      # Store an event corresponding to current BrainVISA session
      # if it is not already done.
      bvsessionEvent = self.findEvent( event.content[ 'bvsession' ], None )
      if bvsessionEvent is None:
        bvsessionEvent = BrainVISASessionEvent()
        if self.__database is not None:
          bvsessionEvent.setCurrentBrainVISASession( sessionId( self.__database.name ) )
        else: # no database
          bvsessionEvent.setCurrentBrainVISASession( sessionId( None ) )
        self.storeEvent( bvsessionEvent )
    if compression is None:
      compression = self.__compression

    if event.eventType == "bvsession":
      eventFileName = os.path.join( self.__dirBvsession, str( event.uuid ) + '.' + event.eventType )
      #eventFileName = os.path.join( self.__dirBvsession, str( sessionId( self.__database.name ) ) + '.' + event.eventType )
    elif event.eventType == "bvproc":
      timeNameDirectory = time.strftime( '%Y-%m-%d',time.localtime() )  
      eventDirectory = os.path.join( self.__dir, timeNameDirectory )
      if not os.path.exists( eventDirectory ): 
        safemkdir.mkdir( eventDirectory )
      eventFileName = os.path.join( eventDirectory, str( event.uuid ) + '.' + event.eventType )
      
    event.save( eventFileName, compression, storeBvproc ) 


  def findEvent( self, uuid, default=Undefined ):
    try:
      fileName = self._findEventFileName( uuid )
    except ValueError:
      if default is Undefined: raise
      return default
    return readMinf( fileName )[ 0 ]
    
  
  def _findEventFileName( self, uuid ):
    eventFilePattern = os.path.join( self.__dir,  str( uuid ) + '.*' )
    l = glob( eventFilePattern )
    if l:
      return l[0]
    raise ValueError( _( 'History book %(book)s does not contain event %(uuid)s' ) %
                        { 'book': unicode( self ), 'uuid': str(uuid) } )
  
  
  def removeEvent( self, uuid ):
    os.remove( self._findEventFileName( uuid ) )


  @staticmethod
  def getHistoryBookDirectories(item ):
    if item is None:
      return ( None, None, None )
    historyBook = None
    if hasattr( neuroConfig, 'historyBookDirectory' ): #used for distributed executions
      
      historyBook = neuroConfig.historyBookDirectory
      db = None
      dirBvsession = None
    if not historyBook:
      database = item.getHierarchy( '_database' )
      if database:
        db = neuroHierarchy.databases.database( database )
        if db is not None and db.activate_history:
          historyBook = os.path.join( database, 'history_book' )
        #ini the bvSession Directory
        di = WriteDiskItem( 'Bvsession', 'Directory' )
        dirBvsession = str(di.findValue({ '_database' : database }))
        sessionId( database )
    if type( historyBook ) in types.StringTypes:
      historyBook = [ historyBook ]
    return ( historyBook, db, dirBvsession )

  @staticmethod
  def storeProcessStart( executionContext, process ):
    historyBooksContext = {}
    for parameterized, attribute, type in process.getAllParameters():
      if isinstance( type, WriteDiskItem ):
        item = getattr( parameterized, attribute )
        historyBooks, db, dirBvsession = HistoryBook.getHistoryBookDirectories( item )
        if historyBooks:
          for historyBook in historyBooks:
            #event = None
            if not os.path.exists( historyBook ):
              safemkdir.mkdir( historyBook )
            historyBook = HistoryBook( historyBook, db, dirBvsession, compression=True )
            dHistoryBook = {}
            historyBooksContext.setdefault( historyBook, dHistoryBook )[ item.fullPath() ] = ( item, item.modificationHash() )

    event = None
    if historyBooksContext:
      for book in historyBooksContext.iterkeys():
        event = executionContext.createProcessExecutionEvent()
        if book.__database is not None:
          event.setBvsession(sessionId( book.__database.name ) )
        else: # no database
          event.setBvsession(sessionId( None ) )
        dirBook = historyBooksContext.get(book).copy()
        dirBook [ "processExcutionEvent"] = event
        historyBooksContext [ book ] = dirBook 
        book.storeEvent( event )
        event._logItem = executionContext._lastStartProcessLogItem

    return event, historyBooksContext


  @staticmethod
  def storeProcessFinished( executionContext, process, event, historyBooksContext ):
    for book, items in historyBooksContext.iteritems():
      historyBooksContext[book].get('processExcutionEvent').setLog( historyBooksContext[book].get('processExcutionEvent')._logItem )
      changedItems = []
      g = items.itervalues()
      for i in g :
        if not isinstance(i, ProcessExecutionEvent) : 
          val = [j for j in i]
          if val[1] != val[0].modificationHash() :
            changedItems.append(val[0])
      historyBooksContext[book].get('processExcutionEvent').content[ 'modified_data' ] = [unicode(item) for item in changedItems]
      book.storeEvent( historyBooksContext[book].get('processExcutionEvent'), storeBvproc = True )
      #update the the lastHistoricalEvent of each diskitems
      for item in changedItems:
        try:
          item.setMinf( 'lastHistoricalEvent', historyBooksContext[book].get('processExcutionEvent').uuid )
        except:
          neuroException.showException()



class HistoricalEvent( object ):
  """
  
  """
  def __init__( self, uuid = None):
    if uuid is None: uuid = Uuid()
    self.uuid = uuid

  def save( self, eventFileName, compression=False, storeBvproc = False):
    close = True
    writeMinFile = False
    bvProcDiskItem = None 
    
    if type( eventFileName ) in ( str, unicode ):
      if compression:
        eventFile = gzipOpen( eventFileName, mode='w' )
      else:
        eventFile = open( eventFileName, mode='w' )
    else:
      eventFile = eventFileName
      close = False

    writeMinf( eventFile, ( self, ), reducer=minfHistory )
    
    if self.eventType == 'bvproc': 
      if storeBvproc:
        #move the bvproc if the time is new
        timeNameDirectory = time.strftime( '%Y-%m-%d',time.localtime() )  
        s = os.stat( eventFileName )
        fileDate = time.strftime( '%Y-%m-%d', time.localtime(s.st_mtime) )
        if fileDate != timeNameDirectory: 
          eventDirectory = os.path.join( self.__dir, timeNameDirectory )
          if not os.path.exists( eventDirectory ): 
            safemkdir.mkdir( eventDirectory )
            newFile =  os.path.join( eventDirectory, os.path.basename( eventFileName ) )
            shutil.move( eventFileName, newFile )
            bvProcDiskItem = WriteDiskItem( 'Process execution event', 'Process execution event' ).findValue( eventFileName )
      else :
        bvProcDiskItem = WriteDiskItem( 'Process execution event', 'Process execution event' ).findValue( eventFileName )
    elif self.eventType == 'bvsession':
      bvProcDiskItem = WriteDiskItem( 'BrainVISA session event', 'BrainVISA session event' ).findValue( eventFileName )
    
    if bvProcDiskItem is not None:
        minf = {}
        minf ['uuid'] = self.uuid
        bvProcDiskItem.saveMinf( minf )
        database = bvProcDiskItem.getHierarchy( '_database' )
        if database:
          db = neuroHierarchy.databases.database( database )
          db.insertDiskItem( bvProcDiskItem, update=True )
#    else :
#      defaultContext().warning("No diskitem found for BrainVISA session event or Process execution event")
    
    if close:
      eventFile.close()



class ProcessExecutionEvent( HistoricalEvent ):
  """
  This object enables to store the state of a :py:class:`Process` instance in a dictionary format.
  """
  eventType = 'bvproc'
    
  
  def __init__( self, uuid=None, content={} ):
    HistoricalEvent.__init__( self, uuid )
    self.content = {}
    self.content.update( content )
  
  def __getinitargs__( self ):
    return ( self.uuid, self.content )
  
  def setBvsession( self, uuid):
    self.content[ 'bvsession' ] = uuid 

  
  def setProcess( self, process ):
    process.saveStateInDictionary( self.content )
  
  
  def setWindow( self, processView ):
    self.content[ 'window' ] = {
        'position': [ processView.x(), processView.y() ],
        'size': [ processView.width(), processView.height() ],
        #'state': processView.windowState(),
      }


  def setLog( self, log ):
    if log:
      if isinstance( log, neuroLog.LogFile.Item ):
        log._expand({})
        self.content[ 'log' ] = [ log ]
      else:
        self.content[ 'log' ] = list( neuroLog.expandedReader( log.fileName ) )


  def __str__( self ):
    if self.content.get('id', None):
      return 'bvproc<' + str(self.uuid) + ',' + self.content['id'] + '>'
    else:
      return str(self.content)


class BrainVISASessionEvent( HistoricalEvent ):
  eventType = 'bvsession'
  
#  def __init__( self, uuid=None, content={}, database):
  def __init__( self, uuid=None, content={}):
    HistoricalEvent.__init__( self, uuid )
    self.content = content.copy()
  
  
  def __getinitargs__( self ):
    return ( self.uuid, self.content )
  
  
  def setCurrentBrainVISASession( self, uuidDb ):
    self.content[ 'version' ] = neuroConfig.versionString()
    if uuidDb is not None:
      self.uuid = uuidDb
    else:
      self.uuid = neuroConfig.sessionID
    if neuroConfig.brainvisaSessionLogItem:
      neuroConfig.brainvisaSessionLogItem._expand({})
      self.content[ 'log' ] = [ neuroConfig.brainvisaSessionLogItem ]
  
  
  def __str__( self ):
    return 'bvsession<' + str(self.uuid) + '>'


