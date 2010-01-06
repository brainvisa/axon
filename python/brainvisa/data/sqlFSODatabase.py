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
import sys
import os, re

import time
from itertools import izip, chain
from StringIO import StringIO

from soma.minf.api import readMinf, writeMinf
from soma.html import htmlEscape
from soma.sorted_dictionary import SortedDictionary
from soma.undefined import Undefined
from soma.translation import translate as _
from soma.path import split_path, relative_path
from soma.time import timeDifferenceToString
from soma.uuid import Uuid
from soma.notification import Notifier
from soma.databases.api import sqlite3, ThreadSafeSQLiteConnection

from fileSystemOntology import FileSystemOntology, SetContent
from neuroProcesses import diskItemTypes, getDiskItemType
import neuroProcesses, neuroConfig
from neuroException import showWarning
from neuroDiskItems import getFormat, getFormats, Format, FormatSeries, File, Directory, getAllFormats
from neuroException import HTMLMessage
from brainvisa.data.patterns import DictPattern
from brainvisa.data.sql import mangleSQL, unmangleSQL
from brainvisa.data.fileformats import FileFormats
from brainvisa.data.directory_iterator import DirectoryIterator, VirtualDirectoryIterator

out = sys.stdout

#------------------------------------------------------------------------------
class CombineGet( object ):
  def __init__( self, *args ):
    self.__objects = args
  
  def get( self, key, default=None ):
    for o in self.__objects:
      v = o.get( key, Undefined )
      if v is not Undefined:
        return v
    return default


  def __getitem__( self, key ):
    for o in self.__objects:
      v = o.get( key, Undefined )
      if v is not Undefined:
        return v
    raise KeyError( key )

  def copy( self ):
    result = self.__objects[ 0 ].copy()
    for d in self.__objects[ 1: ]:
      for k, v in d.iteritems():
        result.setdefault( k, v )
    return result

#------------------------------------------------------------------------------
def _indicesForTuplesWithMissingValues( n ):
  if n > 0:
    for i in xrange( n ):
      yield ( i, )
      for t in _indicesForTuplesWithMissingValues( n-i-1 ):
        yield ( i, ) + tuple(j+i+1 for j in t)

#------------------------------------------------------------------------------
def tupleWithMissingValues( t, tpl, missingValue ) :
  result = list()
  for i in xrange(len(tpl)) :
    if (i in t ) :
      result += tuple((missingValue, ))
    else :
      result += tuple((tpl[i],))
  
  return tuple(result)

#------------------------------------------------------------------------------
def tuplesWithMissingValues( tpl, missingValue ):
  yield tpl
  for t in _indicesForTuplesWithMissingValues( len( tpl ) ):
    yield tupleWithMissingValues( t, tpl, missingValue )
    
#------------------------------------------------------------------------------
class Database( object ):
  class Error( Exception ):
    pass
  
  class NotInDatabaseError( Error ):
    pass
  
  
  @staticmethod
  def getAttributeValues( attributeName, selection, required, default=Undefined ):
    r = required.get( attributeName, Undefined )
    s = selection.get( attributeName, default )
    if s is Undefined:
      if r is Undefined:
        return []
      if r is None or isinstance( r, basestring ):
        return [ r ]
      return r
    if s is None or isinstance( s, basestring ):
      s = [ s ]
    if r is Undefined:
      return s
    if r is None or isinstance( r, basestring ):
      r = set( [ r ] )
    else:
      r = set( r )
    i = r.intersection( s )
    if i: return list( i )
    return list( r )

  def __init__(self):
    # a notifier that notifies database update
    self.onUpdateNotifier=Notifier()
  
  def insertDiskItem( self, item, **kwargs ):
    self.insertDiskItems( ( item, ), **kwargs )
  

  def removeDiskItem( self, item, **kwargs ):
    self.removeDiskItems( ( item, ), **kwargs )
  

  def findOrCreateDiskItems( self, selection={}, **required ):
    fullPaths = set()
    for item in self.findDiskItems( selection, **required ):
      fullPaths.add( item.fullPath() )
      yield item
    for item in self.createDiskItems( selection, **required ):
      if item.fullPath() not in fullPaths:
        yield item
  
  
  def findDiskItem( self, *args, **kwargs ):
    item = None
    for i in self.findDiskItems( *args, **kwargs ):
      if item is None:
        item = i
      else:
        # At least two values found ==> return None
        return None
    return item


  def findOrCreateDiskItem( self, *args, **kwargs ):
    item = None
    for i in self.findOrCreateDiskItems( *args, **kwargs ):
      if item is None:
        item = i
      else:
        # At least two values found ==> return None
        return None
    return item


  def currentThreadCleanup( self ):
    pass



#------------------------------------------------------------------------------
#dbg# import weakref
class SQLDatabase( Database ):
  class CursorProxy( object ):
#dbg#     _allProxy = weakref.WeakKeyDictionary()
    _proxyId = 0
    _executeCount = 0
    
    def __init__( self, cursor ):
      self.__cursor = cursor
      self._id = self._proxyId
      SQLDatabase.CursorProxy._proxyId += 1
#dbg#       self._debugMessage( 'create' )
#dbg#       self._allProxy[ self ] = None
    
    def execute( self, *args, **kwargs ):
      #SQLDatabase.CursorProxy._executeCount += 1
      self._debugMessage( 'execute:' + str( SQLDatabase.CursorProxy._executeCount ) + ' ' + args[0] )
      return self.__cursor.execute( *args, **kwargs )
    
    def executemany( self, *args, **kwargs ):
      #SQLDatabase.CursorProxy._executeCount += 1
      self._debugMessage( 'executemany:' + str( SQLDatabase.CursorProxy._executeCount ) + ' ' + args[0] )
      return self.__cursor.executemany( *args, **kwargs )
    
    def close( self ):
#dbg#       self._debugMessage( 'close' )
      self.__cursor.close()
      del self.__cursor
      
    def _debugMessage( self, message ):
      print >> sys.stderr, '!cursor!', self._id, ':', message


  def __init__( self, sqlDatabaseFile, directory, fso=None, context=None, otherSqliteFiles=[] ):
    super(SQLDatabase, self).__init__()
    self._connection = None
    self.name = os.path.normpath( directory )
    if sqlDatabaseFile not in ( '', ':memory:' ):
      self.sqlDatabaseFile = os.path.normpath( os.path.abspath( sqlDatabaseFile ) )
    else:
      self.sqlDatabaseFile = sqlDatabaseFile
    self.directory = os.path.normpath( directory )
    if not os.path.exists( self.directory ):
        raise ValueError( HTMLMessage(_t_('<em>%s</em> is not a valid directory') % str( self.directory )) )
    minf = os.path.join( self.directory, 'database_settings.minf' )
    if fso is None:
      if os.path.exists(minf):
        fso = readMinf( minf )[ 0 ].get( 'ontology', 'brainvisa-3.0' )
      else:
        fso='brainvisa-3.0'
    self.fso = FileSystemOntology.get( fso )
    self.otherSqliteFiles=otherSqliteFiles
    
    # Build list of all formats used in BrainVISA
    self.formats = FileFormats( self.fso.name )
    formatsAlreadyDefined = set( ( 'Directory', 'Graph', 'Graph and data' ,'mdata file' ) )
    self.formats.newFormat( 'Graph and data', ( 'arg', 'd|data' ) )
    self.formats.newAlias( 'Graph', 'Graph and data' )
    for format in (i for i in getAllFormats() if not i.name.startswith( 'Series of ' )):
      if isinstance( format, FormatSeries ) or format.name == 'mdata file': continue
      if format.name not in formatsAlreadyDefined:
        patterns = []
        for p in format.patterns.patterns:
          p = p.pattern
          dotIndex = p.find( '.' )
          if dotIndex < 0:
            break
          patterns.append( p[ dotIndex + 1 : ] )
        self.formats.newFormat( format.name, patterns )
        formatsAlreadyDefined.add( format.name )
    
    
    self.keysByType = {}
    self._tableAttributesByTypeName = {}
    self._nonMandatoryKeyAttributesByType = {}
    self.ruleSelectionByType = {}
    self._attributesEditionByType = {}
    self._formatsByTypeName = {}
    for type, rules in self.fso.typeToPatterns.iteritems():
      keys = []
      ruleSelectionByAttributeValue = []
      defaultAttributesValues = {}
      rulesDictionary = SortedDictionary()
      rulesByLOPA = {}
      editableAttributes = set()
      selectedValueAttributes = {}
      nonMandatoryKeyAttributes = set()
      for rule in rules:
        nonMandatoryKeyAttributes.update( rule.nonMandatoryKeyAttributes )
        for n, v in rule.defaultAttributesValues.iteritems():
          vv = defaultAttributesValues.get( n, Undefined )
          if vv is Undefined:
            defaultAttributesValues[ n ] = v
          else:
            if v != vv:
              raise Database.Error( _( 'Two different values (%(v1)s and %(v2)s) found for default attribute "%(key)s" of type "%(type)s"' ) %
                                { 'v1': repr( v ), 'v2': repr( vv ), 'key': n, 'type': type.name } )
          defaultAttributesValues[ n ] = v
        rulesByLOPA.setdefault( tuple( rule.pattern.namedRegex() ), [] ).append( rule )
        if rule.formats:
          for format in rule.formats:
            typeFormats = self._formatsByTypeName.setdefault( type.name, [] )
            formatName = self.formats.getFormat( format.name, format ).name
            if formatName not in typeFormats:
              typeFormats.append( formatName )
      for lopa, lopaRules in rulesByLOPA.iteritems():
        for n in lopa:
          editableAttributes.add( n )
        if len( lopaRules ) > 1:
          key = list( lopa )
          localAttributesValues = {}
          for rule in lopaRules:
            for n, v in rule.localAttributes:
              ev = localAttributesValues.get( n )
              if ev is None:
                localAttributesValues[ n ] = v
              elif ev != v:
                if n not in key:
                  key.append( n )
                if n not in ruleSelectionByAttributeValue:
                  ruleSelectionByAttributeValue.append( n )
        else:
          key = lopa
        for a in key:
          if a not in keys:
            keys.append( a )
      
      ruleSelectionByMissingKeyAttributes = []
      for rule in rules:
        for n in keys:
          if n not in ruleSelectionByAttributeValue and n not in rule.pattern.namedRegex() and n not in ruleSelectionByMissingKeyAttributes:
            ruleSelectionByMissingKeyAttributes.append( n )
      for rule in rules:
        localAttributes = dict( rule.localAttributes )
        for n, v in localAttributes.iteritems():
          selectedValueAttributes.setdefault( n, set() ).add( v )
        ruleWithMissingValues = tuplesWithMissingValues(tuple((localAttributes.get(n, '') for n in ruleSelectionByAttributeValue)), '')
        ruleSelection = tuple(((not(n in rule.pattern.namedRegex())) for n in ruleSelectionByMissingKeyAttributes))
        ruleKeys = set((t, ruleSelection) for t in ruleWithMissingValues)
        #if rulesDictionary.has_key( ruleKey ):
          #raise ValueError( 'Two rules with the same selecion key' )
        for ruleKey in ruleKeys:
          rulesDictionary.setdefault( ruleKey, [] ).append( rule )
      # Sort rules by priorityOffset
      for rules in rulesDictionary.itervalues():
        if len( rules ) > 1:
          rules.sort( lambda x, y: cmp( y.priorityOffset, x.priorityOffset ) )
      self.keysByType[ type ] = keys
      self._tableAttributesByTypeName[ type.name ] = list( keys )
      for a in selectedValueAttributes:
        if a not in self._tableAttributesByTypeName[ type.name ]:
          self._tableAttributesByTypeName[ type.name ].append( a )
      self._nonMandatoryKeyAttributesByType[ type.name ] = nonMandatoryKeyAttributes
      self.ruleSelectionByType[ type.name ] = ( ruleSelectionByAttributeValue, ruleSelectionByMissingKeyAttributes, rulesDictionary, defaultAttributesValues )
      self._attributesEditionByType[ type.name ] = ( editableAttributes, selectedValueAttributes )
      
    
    self.typesWithTable = set()
    self._childrenByTypeName = {}
    for type in diskItemTypes.itervalues():
      self._childrenByTypeName.setdefault( type.name, set() ).add( type.name )
      p = type.parent
      while p is not None:
        self._childrenByTypeName.setdefault( p.name, set() ).add( type.name )
        p = p.parent
      if self.keysByType.get( type ) is not None:
        self.typesWithTable.add( type )
    self.typesParentOfATypeWithTable = set()
    for type in self.typesWithTable:
      parent = type.parent
      while parent:
        if parent not in self.typesWithTable:
          self.typesParentOfATypeWithTable.add( parent )
        parent = parent.parent
    self.typesWithTable = set((t.name for t in self.typesWithTable))
    self.keysByType = dict( ((t.name,v) for t,v in self.keysByType.iteritems()))
    
    # init of _tableFieldsAndInsertByTypeName
    self._tableFieldsAndInsertByTypeName = {}
    for type in self.typesWithTable:
      tableName = type
      tableFields = [ '_uuid', '_format', '_name' ] + [mangleSQL(i) for i in self._tableAttributesByTypeName[ type ]]
      tableAttributes = [ '_uuid', '_format', '_name' ] + [i for i in self._tableAttributesByTypeName[ type ]]
      sql = 'INSERT INTO ' + '"' + tableName + '" (' + ', '.join( (i for i in tableFields) ) + ') VALUES (' + ', '.join( ('?' for i in tableFields) ) + ')'
      self._tableFieldsAndInsertByTypeName[ type ] = ( tableName, tableFields, tableAttributes, sql )

    # Determine if the database needs update
    if os.path.exists( self.sqlDatabaseFile ):
      if self.fso.lastModification > os.stat(self.sqlDatabaseFile).st_mtime:
        self._mustBeUpdated = True
        neuroProcesses.defaultContext().write("Database ",  self.name, " must be updated because the database file is too old." )
        #showWarning( _( 'ontology "%(ontology)s" had been modified, database "%(database)s" should be updated. Use the process : Data Management =&gt; Update databases.' ) % { 'ontology': self.fso.name, 'database': self.name } )
      else: # database seem to be up to date but let's check if all the types tables exist
        if not self.checkTables():
          self._mustBeUpdated=True
          neuroProcesses.defaultContext().write( "Database ",  self.name, " must be updated because some types tables are missing." )
    else :
      if (self.sqlDatabaseFile != ":memory:") and (len(os.listdir(self.directory)) > 1): # there is at least database_settings.minf
        self._mustBeUpdated = True
        neuroProcesses.defaultContext().write( "Database ",  self.name, " must be updated because there is no database file." )
      else: # if database directory is empty , it is a new database or it is in memory -> automatically update
        if self.createTables():
          self.update( context=context)
    # do not update automatically enven if the database sqlite file doesn't exists, ask the user.
    #if self.createTables():
      #self.update( context=context)
    if self.otherSqliteFiles: # if there are other sqlite files, the database might have been modified by other version of brainvisa
      # update or not depends on the value of databaseVersionSync option
      if ((neuroConfig.databaseVersionSync is None) and (not neuroConfig.setup)):
        neuroConfig.chooseDatabaseVersionSyncOption(context)
      if neuroConfig.databaseVersionSync == 'auto':
        self._mustBeUpdated = True
        neuroProcesses.defaultContext().write( "Database ",  self.name, " must be updated because it has been used with other versions of Brainvisa." )
  
  
  def update( self, directoriesToScan=None, recursion=True, context=None ):
    if context is not None:
      context.write( self.name + ': parse directories and insert items' )
    t0 = time.time()
    self.insertDiskItems( ( i for i in self.scanDatabaseDirectories( directoriesToScan=directoriesToScan, recursion=recursion ) if i.type is not None ), update=True )
    duration = time.time() - t0
    cursor = self._getDatabaseCursor()
    try:
      fileCount = cursor.execute( 'select COUNT(*) from _filenames_' ).fetchone()[0]
      diskItemCount = cursor.execute( 'select COUNT(*) from _diskitems_' ).fetchone()[0]
    finally:
      self._closeDatabaseCursor( cursor )
    if context is not None:
      context.write( self.name + ':', fileCount, 'files are stored as', diskItemCount, 'DiskItems in', timeDifferenceToString( duration ) )
    # notifies the update to potential listeners
    self.onUpdateNotifier.notify()
  
  
  def clear( self, context=None ):
    if ((neuroConfig.databaseVersionSync=='auto') and self.otherSqliteFiles):
      for f in self.otherSqliteFiles:
        if os.path.exists(f):
          os.remove(f)
        if os.path.exists(f+".minf"):
          os.remove(f+".minf")
      if context is not None:
        context.write("Delete other versions of database cache files : "+unicode(self.otherSqliteFiles))
      self.otherSqliteFiles=[]
    cursor = self._getDatabaseCursor()
    try:
      tables = cursor.execute( 'SELECT name FROM sqlite_master WHERE type="table"' ).fetchall()
      for table in tables:
        cursor.execute( 'DROP TABLE "' + table[0] + '"' )
      cursor.execute( 'VACUUM' )
    finally:
      self._closeDatabaseCursor( cursor )
    self._connection.closeSqliteConnections()
    self.currentThreadCleanup()
    self._connection=None
    self.createTables( context=context )
  
  
  def fsoToHTML( self, fileName ):
    out = open( fileName, 'w' )
    print >> out, '<html>\n<body>\n<center><h1>' + self.fso.name + '</h1></center>'
    for type in sorted( self.keysByType ):
      print >> out, '<h3 id="' + htmlEscape( type ) + '">' + htmlEscape( type ) + '</h3><blockquote>'
      parentType = getDiskItemType( type ).parent
      if parentType is not None:
        print >> out, '<b>Parent types:<blockquote>'
        while parentType is not None:
          t = htmlEscape( parentType.name )
          print >> out, '<a href="#' + t + '">' + htmlEscape( t ) + '</a></p>'
          parentType = parentType.parent
        print >> out, '</blockquote>'
      key = self.keysByType[ type ]
      print >> out, '<b>Key: </b><font color="blue">' + htmlEscape( unicode( key ) ) + '</font><p>'
      nonMandatory = self._nonMandatoryKeyAttributesByType[ type ]
      if nonMandatory:
        print >> out, '<blockquote><b>Non mandatory key attributes: </b>' + htmlEscape( tuple( nonMandatory ) ) + '<p>'
      ruleSelectionByAttributeValue, ruleSelectionByMissingKeyAttributes, rulesDictionary, defaultAttributesValues = self.ruleSelectionByType[ type ]
      if defaultAttributesValues:
        print >> out, '<b>Default attributes values:</b><blockquote>'
        for n, v in defaultAttributesValues.iteritems():
          print >> out, n + ' = ' + htmlEscape( repr(v) ) + '<br/>'
        print >> out, '</blockquote>'
      if ruleSelectionByAttributeValue or ruleSelectionByMissingKeyAttributes:
        print >> out, '<b>Rules selection key: </b><font color=darkgreen>' + htmlEscape( unicode( ruleSelectionByAttributeValue ) ) + '</font> <font color=blue>' + htmlEscape( unicode( ruleSelectionByMissingKeyAttributes ) ) + '</font><p>'
      for ruleKey, rules in rulesDictionary.iteritems():
        #print >> out,'<font color=darkgreen>' + htmlEscape( unicode( ruleKey[0] ) ) + '</font> <font color=blue>' + htmlEscape( unicode( ruleKey[1] ) ) + '</font><blockquote>'
        if len( rules ) > 1:
          print >> out, '<hr>'
        for rule in rules:
          print >> out, htmlEscape( unicode( rule.pattern.pattern ) ) + '<br/>'
          print >> out, '<blockquote>'
          print >> out, '<b>Formats: </b>' + htmlEscape( repr(rule.formats) ) + '<br/>'
          print >> out, 'Rule selection key: <font color=darkgreen>' + htmlEscape( unicode( ruleKey[0] ) ) + '</font> <font color=blue>' + htmlEscape( unicode( ruleKey[1] ) ) + '</font><br/>'
          print >> out, 'Priority offset: ' + str(rule.priorityOffset) + '<br/>'
          if rule.localAttributes:
            for n in key:
              if n in rule.pattern.namedRegex() or n in ruleSelectionByAttributeValue: continue
              f = '<font color=blue>'
              nf = '</font>'
              print >> out, f + n + " = ''" + nf + '<br/>'
            for n, v in rule.localAttributes:
              if n in rule.pattern.namedRegex(): continue
              if n in ruleSelectionByAttributeValue:
                f = '<font color=darkgreen>'
                nf = '</font>'
              else:
                f = nf = ''
              print >> out, f + n + ' = ' + htmlEscape( repr(v) ) + nf + '<br/>'
          print >> out, '</blockquote>'
        if len( rules ) > 1:
          print >> out, '<hr>'
        #print >> out, '</blockquote>'
      print >> out, '</blockquote></blockquote>'
    print >> out, '</body>\n<//html>\n'
    out.close()
  
  
  def _getDatabaseCursor( self ):
    databaseFile=self.sqlDatabaseFile
    if not (os.path.exists(self.sqlDatabaseFile)):
      databaseFile=':memory:'
    if self._connection is None:
      self._connection = ThreadSafeSQLiteConnection( databaseFile )
    #cursor = self.CursorProxy( self._connection._getConnection().cursor() )
    cursor = self._connection._getConnection().cursor()
    return cursor
  
  
  def _closeDatabaseCursor( self, cursor, rollback=False ):
    if self._connection is not None:
      cursor.close()
      connection = self._connection._getConnection()
      if rollback:
        connection.rollback()
      else:
        connection.commit()
  
  
  def currentThreadCleanup( self ):
    if self._connection is not None:
      self._connection.currentThreadCleanup()
  
  
  def createTables( self, context=None ):
    # if the database file is created by sqlite, the write permission is given only for the current user, not for the group, so the database cannot be shared
    if not os.path.exists( self.sqlDatabaseFile ) and self.sqlDatabaseFile not in ( '', ':memory:' ):
      f=open(self.sqlDatabaseFile, "w")
      f.close()
    cursor = self._getDatabaseCursor()
    try:
      self._tableFieldsAndInsertByTypeName = {}
      create = True
      try:
        cursor.execute( 'CREATE TABLE _DISKITEMS_ (_uuid CHAR(36) PRIMARY KEY, _diskItem TEXT)' )
      except sqlite3.OperationalError:
        create = False
      if create:
        if context is not None:
          context.write( 'Generating database tables for', self.name )
        cursor.execute( 'CREATE TABLE _FILENAMES_ (filename VARCHAR PRIMARY KEY, _uuid CHAR(36))' )
        cursor.execute( 'CREATE INDEX _IDX_FILENAMES_ ON _FILENAMES_ (filename, _uuid)' )
      for type in self.typesWithTable:
        #tableName = mangleSQL(type.name)
        tableName = type
        tableFields = [ '_uuid', '_format', '_name' ] + [mangleSQL(i) for i in self._tableAttributesByTypeName[ type ]]
        tableAttributes = [ '_uuid', '_format', '_name' ] + [i for i in self._tableAttributesByTypeName[ type ]]
        if create:
          sql = 'CREATE TABLE ' + '"' + tableName + '" (_uuid CHAR(36) PRIMARY KEY, ' + ', '.join( (i + ' VARCHAR' for i in tableFields[1:]) ) + ')'
          #print '!createTables!', sql
          cursor.execute( sql )
          # create index
          keys = self.keysByType[ type ]
          if keys:
            sql = 'CREATE INDEX "IDX_' + tableName + '" ON "' + tableName + '" ( ' + ', '.join([mangleSQL(i) for i in keys]) + ')'
            cursor.execute( sql )
        sql = 'INSERT INTO ' + '"' + tableName + '" (' + ', '.join( (i for i in tableFields) ) + ') VALUES (' + ', '.join( ('?' for i in tableFields) ) + ')'
        self._tableFieldsAndInsertByTypeName[ type ] = ( tableName, tableFields, tableAttributes, sql )
    except:
      self._closeDatabaseCursor( cursor, rollback=True )
      raise
    else:
      self._closeDatabaseCursor( cursor )
    # Save, in the database directory, an HTML file corresponding to database ontology
    if create and os.path.exists( self.sqlDatabaseFile ):
      html = os.path.join( os.path.dirname( self.sqlDatabaseFile ), 'database_fso.html' )
      self.fsoToHTML( html )
    return create

  def checkTables(self):
    """
    Checks if all types currently defined in the database ontology have a matching table in the sqlite database.
    It may be not the case when the database have been update with a version of brainvisa that has not all the toolboxes. It should then be updated.
    """
    cursor = self._getDatabaseCursor()
    tablesExist=False
    try:
      try:
        res=cursor.execute( "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name" )
        tables=set([t[0] for t in res.fetchall()]) # fetchall returns a list of tuples
        tablesExist=self.typesWithTable.issubset(tables) # there are also tables for diskitems and filenames which does match a specific type.
      except sqlite3.OperationalError, e:
        neuroProcesses.defaultContext().warning(e.message)
    finally:
      self._closeDatabaseCursor( cursor )
    return tablesExist

  def insertDiskItems( self, diskItems, update=False ):
    cursor = self._getDatabaseCursor()
    try:
      for diskItem in diskItems:
        #print '!insertDiskItems!', diskItem
        if diskItem.type is None:
          raise Database.Error( _('Cannot insert an item wthout type in a database: %s') % ( unicode( diskItem ), ) )
        try:
          uuid = str( diskItem.uuid() )
        except RuntimeError:
          uuid = str( diskItem.uuid( saveMinf=False ) )
        if diskItem._write:
          diskItem.readAndUpdateMinf()
          diskItem._write = False
        
        if diskItem.format :
          format = self.formats.getFormat( diskItem.format.name,diskItem.format).name
        else :
          format = None
        
        state =  {
          'isDirectory': isinstance( diskItem, Directory ),
          'type': diskItem.type.name,
          'format': format,
          'name': relative_path(diskItem.name, self.directory),
          '_files': [ relative_path(f, self.directory) for f in diskItem._files ],
          '_localAttributes': diskItem._localAttributes,
          '_globalAttributes': diskItem._globalAttributes,
          '_minfAttributes': diskItem._minfAttributes,
          '_otherAttributes': diskItem._otherAttributes,
          '_uuid': diskItem._uuid,
          '_priority': getattr( diskItem, '_priority', 0 ),
        }
        f = StringIO()
        writeMinf( f, ( state, ) )
        minf = f.getvalue()
        # decode the minf string to pass a unicode string  to the sqlite database
        minf = minf.decode("utf-8")
        try:
          cursor.execute( 'INSERT INTO _DISKITEMS_ (_uuid, _diskItem) VALUES (? ,?)', ( uuid, minf ) )
          delete = False
        except sqlite3.IntegrityError, e:
          # an item with the same uuid is already in the database
          uuid = cursor.execute( 'SELECT _uuid FROM _FILENAMES_ WHERE filename=?', ( relative_path(diskItem.fullPath(), self.directory), ) ).fetchone()
          if uuid:
            uuid = uuid[ 0 ]
            # diskItem file name is in the database
            if update:
              if uuid == str( diskItem._uuid ):
                delete = True
                cursor.execute( 'UPDATE _DISKITEMS_ SET _diskItem=? WHERE _uuid=?', ( minf, uuid ) )
              else:
                raise Database.Error( 'Cannot insert "%s" because its uuid is in conflict with the uuid of another file in the database' % diskItem.fullPath() )
            else:
              raise Database.Error( 'Cannot insert "%s" because it is already in the database' % diskItem.fullPath() )
          else:
            # diskItem file name is not in the database ==> DiskItem's uuid is changed
            # commit changes
            self._closeDatabaseCursor( cursor )
            cursor = self._getDatabaseCursor()
            print >> sys.stderr, _( 'Warning: changed uuid of "%(newDiskItem)s" because another file has the same uuid: %(uuid)s' ) % {
                'newDiskItem': repr( diskItem ),
                'uuid': str( uuid ),
              }
            delete = False
            diskItem.setUuid( Uuid() )
            uuid = str( diskItem._uuid )
            state[ '_uuid' ] = diskItem._uuid
            f = StringIO()
            writeMinf( f, ( state, ) )
            minf = f.getvalue()
            cursor.execute( 'INSERT INTO _DISKITEMS_ (_uuid, _diskItem) VALUES (? ,?)', ( uuid, minf ) )
        if delete:
          cursor.execute( 'DELETE FROM _FILENAMES_ WHERE _uuid=?', ( uuid, ) )
        try:
          cursor.executemany( 'INSERT INTO _FILENAMES_ (filename, _uuid) VALUES (? ,?)', (( relative_path(i, self.directory), uuid ) for i in diskItem.fullPaths()) )
        except sqlite3.IntegrityError, e:
          raise Database.Error( unicode(e)+': file names = ' + repr(diskItem.fullPaths()) )
        
        values = [ uuid, format, os.path.basename( diskItem.fullPath() ) ]					
        if diskItem.type.name in self._tableFieldsAndInsertByTypeName:
          tableName, tableFields, tableAttributes, sql = self._tableFieldsAndInsertByTypeName[ diskItem.type.name ]
          for i in tableAttributes[3:]:
            v = diskItem.get( i )
            if v is None:
              values.append( None )
            elif isinstance( v, basestring ):
              values.append( v )
            else:
              values.append( unicode( v ) )
          #print '!insertDiskItems!', sql, values, [ type(i) for i in values ]
          if delete:
            cursor.execute( 'DELETE FROM "' + tableName + '" WHERE _uuid=?', ( uuid, ) )
          cursor.execute( sql, values )
    except sqlite3.OperationalError, e:
      self._closeDatabaseCursor( cursor, rollback=True )
      raise Database.Error( "Cannot insert items in database "+self.name+". You should update this database." )
    except:
      self._closeDatabaseCursor( cursor, rollback=True )
      raise
    else:
      self._closeDatabaseCursor( cursor )
  
  
  def removeDiskItems( self, diskItems, eraseFiles=False ):
    cursor = self._getDatabaseCursor()
    try:
      for diskItem in diskItems:
        uuid = str( diskItem.uuid( saveMinf=False ) )
        cursor.execute( 'DELETE FROM _DISKITEMS_ WHERE _uuid=?', ( uuid, ) )
        cursor.execute( 'DELETE FROM _FILENAMES_ WHERE _uuid=?', ( uuid, ) )
        tableName, tableFields, tableAttributes, sql = self._tableFieldsAndInsertByTypeName[ diskItem.type.name ]
        cursor.execute( 'DELETE FROM "' + tableName + '" WHERE _uuid=?', ( uuid, ) )
        if eraseFiles:
          diskItem.eraseFiles()
    except sqlite3.OperationalError, e:
      self._closeDatabaseCursor( cursor, rollback=True )
      raise Database.Error( "Cannot remove items from database "+self.name+". You should update this database." )
    except:
      self._closeDatabaseCursor( cursor, rollback=True )
      raise
    else:
      self._closeDatabaseCursor( cursor )
  
  def _diskItemFromMinf(self, minf ):
    if type(minf) is unicode:
      # have to pass a str to readMinf and not a unicode because, xml parser will use encoding information written in the xml tag to decode the string. In brainvisa, all minf are encoded in utf-8
      minf=minf.encode("utf-8")
    f = StringIO( minf )
    state = readMinf( f )[ 0 ]
    if state[ 'isDirectory' ]:
      diskItem = Directory( os.path.join( self.directory, state[ 'name' ]), None )
    else:
      diskItem = File( os.path.join( self.directory, state[ 'name' ]), None )
    diskItem.type = getDiskItemType( str( state[ 'type' ] ) )
    f = state[ 'format' ]
    if f:
      diskItem.format = getFormat( str( f ) )
    #self.name = state[ 'name' ]
    diskItem._files = [ os.path.join( self.directory, f) for f in state[ '_files' ] ]
    diskItem._localAttributes = state[ '_localAttributes' ]
    diskItem._globalAttributes = state[ '_globalAttributes' ]
    diskItem._minfAttributes = state[ '_minfAttributes' ]
    diskItem._otherAttributes = state[ '_otherAttributes' ]
    diskItem._changeUuid( state.get( '_uuid' ) )
    diskItem._priority = state[ '_priority' ]
    return diskItem
  
  
  def getDiskItemFromUuid( self, uuid, defaultValue=Undefined ):
    cursor = self._getDatabaseCursor()
    minf=None
    try:
      sql = "SELECT _diskItem from _DISKITEMS_ WHERE _uuid='" + str( uuid ) + "'"
      minf = cursor.execute( sql ).fetchone()
    except sqlite3.OperationalError, e:
      neuroProcesses.defaultContext().warning( "Cannot question database "+self.name+". You should update this database." )
    finally:
      self._closeDatabaseCursor( cursor )
    if minf is not None:
      return self._diskItemFromMinf( minf[ 0 ] )
    if defaultValue is Undefined:
      raise Database.Error( _( 'Database "%(database)s" contains no DiskItem with uuid %(uuid)s' ) % { 'database': self.name,  'uuid': str(uuid) } )
    return defaultValue
  
  
  def getDiskItemFromFileName( self, fileName, defaultValue=Undefined ):
    if fileName.startswith(self.directory):
      cursor = self._getDatabaseCursor()
      minf=None
      try:
        sql = "SELECT _diskItem FROM _FILENAMES_ F, _DISKITEMS_ D WHERE F._uuid=D._uuid AND F.filename='" + unicode( relative_path(fileName, self.directory) ) + "'"
        minf = cursor.execute( sql ).fetchone()
      except sqlite3.OperationalError, e:
        neuroProcesses.defaultContext().warning( "Cannot question database "+self.name+". You should update this database." )
      finally:
        self._closeDatabaseCursor( cursor )
      if minf is not None:
        return self._diskItemFromMinf( minf[ 0 ] )
    if defaultValue is Undefined:
      raise Database.Error( _( 'Database "%(database)s" does not reference file "%(filename)s"' ) % { 'database': self.name,  'filename': fileName } )
    return defaultValue


  def createDiskItemFromFileName( self, fileName, defaultValue=Undefined ):
    diskItem = self.createDiskItemFromFormatExtension( fileName, None )
    if diskItem is not None:
      d=self.directory
      if fileName.startswith( d ):
        splitted = split_path( fileName[ len(d)+1: ] )
        content = reduce( lambda x,y: [(y,x)], reversed(splitted[:-1]), [ (os.path.basename(f), None) for f in diskItem._files ] )
        vdi = VirtualDirectoryIterator( fileName[ :len(d) ], content )
        lastItem = None
        for item in self.scanDatabaseDirectories( vdi ):
          lastItem = item
        if lastItem is not None and fileName in lastItem.fullPaths():
          return lastItem
    if defaultValue is Undefined:
      raise Database.Error( _( 'Database "%(database)s" cannot reference file "%(filename)s"' ) % { 'database': self.name,  'filename': fileName } )
    return defaultValue

  def createDiskItemFromFormatExtension( self, fileName, defaultValue=Undefined ):
    format, ext, noExt = self.formats._findMatchingFormat( fileName )
    if format is not None:
      extensions = format.extensions()
      if len( extensions ) == 1:
        files = [ noExt + '.' + ext ]
      else:
        files = [ noExt + '.' + ext for ext in extensions ]
      diskItem = File( noExt, None )
      diskItem.format = getFormat( str(format.name) )
      diskItem.type = None
      diskItem._files = files
      return diskItem
    if defaultValue is Undefined:
      raise Database.Error( _( 'Database "%(database)s" has no format to recognise "%(filename)s"' ) % { 'database': self.name,  'filename': fileName } )
    return None
    
  def changeDiskItemFormat( self, diskItem, newFormat ):
    #print '!changeDiskItemFormat!', self.name, diskItem, newFormat, type( newFormat )
    result = None
    newFormat = self.formats.getFormat( newFormat, None )
    if newFormat is not None:
      #print '!changeDiskItemFormat!  ', newFormat, 'found.'
      format, ext, noExt = self.formats._findMatchingFormat( diskItem.fullPath() )
      if format is not None:
        #print '!changeDiskItemFormat!  ', format, 'matching.'
        result = diskItem.clone()
        result.format = getFormat( str(format.name) )
        result._files = [ noExt + '.' + ext for ext in newFormat.extensions() ]
    return result
  
  
  def scanDatabaseDirectories( self, directoriesIterator=None, includeUnknowns=False, directoriesToScan=None, recursion=True, debugHTML=None ):
    if debugHTML:
      print >> debugHTML, '<html><body><h1>Scan log for database <tt>' + self.name + '</tt></h1>\n<h2>Directory</h2><blockquote>'
      print >> debugHTML, '<br>\n'.join( self.directory ), '</blockquote>'
    scanner = [i for i in self.fso.content if isinstance(i,SetContent)][0].scanner
    if directoriesIterator is None:
      stack = [ ( DirectoryIterator(self.directory), scanner, { }, 0 ) ]
    else:
      stack = [ ( directoriesIterator, scanner, {  }, 0 ) ]
    while stack:
      itDirectory, scanner, attributes, priorityOffset = stack.pop( 0 )
      f = itDirectory.fullPath()
      if directoriesToScan is not None:
        ignore = True
        allowYield = False
        if recursion:
          for d in directoriesToScan:
            i = min( len(d), len(f) )
            if d[:i] == f[:i]:
              allowYield = len( f ) >= len( d )
              ignore = False
              break
        else:
          for d in directoriesToScan:
            i = min( len(d), len(f) )
            if d[:i] == f[:i]:
              allowYield = allowYield or f == d
              ignore = not allowYield and not len( f ) <= len( d )
              if allowYield and not ignore: break
        #print '!scanDatabaseDirectories! directory "' + f + '": ignore =', ignore, ', allowYield =', allowYield
        if ignore:
          continue
      else:
        allowYield = True
      if debugHTML:
        print >> debugHTML, '<h2>' + itDirectory.fullPath() + '</h2>\nparents attributes: ' + repr( attributes )
      directoryRules = []
      nonDirectoryRules = []
      for rule in getattr( scanner, 'rules', () ):
        if rule.scanner is not None:
          directoryRules.append( rule )
        else:
          nonDirectoryRules.append( rule )
      if debugHTML:
        print >> debugHTML, '<h3>Rules</h3><blockquote>'
        for rule in directoryRules:
          print >> debugHTML, '<font color=darkblue>' + htmlEscape( rule.pattern.pattern ) + ':</font>', rule.type, '<br>'
        for rule in nonDirectoryRules:
          print >> debugHTML, '<font color=darkgreen>' + htmlEscape( rule.pattern.pattern ) + ':</font>', rule.type, '<br>'
        print >> debugHTML, '</blockquote>'
      # Identify formats
      try:
        knownFormat, unknownFormat = self.formats.identify( itDirectory )
      except OSError, e:
        print >> sys.stderr, e
        knownFormat = unknownFormat = []
      
      if includeUnknowns and allowYield:
        for it in unknownFormat:
          diskItem = File( it.fileName(), None )
          diskItem._files = [ it.fullPath() ]
          diskItem._globalAttributes[ '_database' ] = self.name
          diskItem._identified = False
          yield diskItem
      if debugHTML:
        if unknownFormat:
          print >> debugHTML, '<h3>Unknown format</h3><blockquote>'
          for f in unknownFormat:
            print >> debugHTML, '<font color=red>' + repr( f.fullPath() ) + '</font><br>'
          print >> debugHTML, '</blockquote>'
        print >> debugHTML, '<h3>Items identification</h3><blockquote>'
      
      unknownType = []
      knownType = []
      nameSeriesGroupedItems = {}
      for nameWithoutExtension, files, minf, format, it in knownFormat:
        if format == 'Directory':
          # Find directories corresponding to a rule with a SetContent
          f = it.fileName()
          for rule in directoryRules:
            match = DictPattern.match( rule.pattern, f, attributes )
            if match is not None:
              a = attributes.copy()
              a.update( match )
              a.update( rule.localAttributes )
              stack.append( ( it, rule.scanner, a, priorityOffset + rule.priorityOffset ) )
              if allowYield and ( rule.type is not None or includeUnknowns ):
                diskItem = Directory( nameWithoutExtension, None )
                diskItem.type = rule.type
                diskItem.format = getFormat( 'Directory' )
                diskItem._files = files
                diskItem._globalAttributes[ '_database' ] = self.name
                diskItem._globalAttributes[ '_ontology' ] = self.fso.name
                diskItem._globalAttributes.update( a )
                diskItem._priority = priorityOffset + rule.priorityOffset
                diskItem._identified = True
                diskItem.readAndUpdateMinf()
                yield diskItem
                if debugHTML:
                  print >> debugHTML, '<font color=darkblue><b>', diskItem, ':</b>', diskItem.type, '</font> (' + htmlEscape( rule.pattern.pattern ) + ':' + str( rule.type ) + ')<br>'
              #if debugHTML:
                #print >> debugHTML, '<font color=darkorange><b>' + f + ':</b> ' + repr( match ) + '</font><br>'
              break
          else:
            #for rule in directoryRules:
              #print '  -->', rule.pattern
            if includeUnknowns:
              stack.append( ( it, None, attributes, priorityOffset ) )
              if allowYield:
                diskItem = Directory( nameWithoutExtension, None )
                diskItem._files = files
                diskItem._globalAttributes[ '_database' ] = self.name
                diskItem._identified = False
                yield diskItem
        else:
          diskItem = File( nameWithoutExtension, None )
          diskItem.format = getFormat( str( format ) )
          diskItem._files = [ os.path.join( itDirectory.fullPath(), i ) for i in files ]
          diskItem._globalAttributes[ '_database' ] = self.name
          for rule in nonDirectoryRules:
            if rule.formats and format not in rule.formatNamesInSet:
              if format != 'Graph and data' or 'Graph' not in rule.formatNamesInSet:
                continue
            match = DictPattern.match( rule.pattern, os.path.basename( nameWithoutExtension ), attributes )
            if match is not None:
              diskItem.type = rule.type
              name_serie = match.pop( 'name_serie', None )
              if name_serie is not None:
                key = ( diskItem.type, format, rule.pattern.pattern, tuple( match.itervalues() ) )
                groupDiskItem = nameSeriesGroupedItems.get( key )
                if groupDiskItem is None:
                  diskItem._globalAttributes[ '_ontology' ] = self.fso.name
                  diskItem._globalAttributes.update( attributes )
                  diskItem._globalAttributes.update( match )
                  diskItem._globalAttributes.update( rule.localAttributes )
                  diskItem._priority = priorityOffset + rule.priorityOffset
                  diskItem._identified = True
                  groupDiskItem = diskItem
                  match[ 'name_serie' ] = '#'
                  groupDiskItem.format = getFormat( str( 'Series of ' + format ) )
                  n = DictPattern.unmatch( rule.pattern, match, attributes )
                  groupDiskItem._files = [ os.path.join( itDirectory.fullPath(), n + '.' + i ) for i in self.formats.getFormat( format ).extensions() ]
                  groupDiskItem._setLocal( 'name_serie', set( ( name_serie, ) ) )
                  nameSeriesGroupedItems[ key ] = groupDiskItem
                else:
                  groupDiskItem._getLocal( 'name_serie' ).add( name_serie )
              elif allowYield:
                diskItem._globalAttributes[ '_ontology' ] = self.fso.name
                diskItem._globalAttributes.update( attributes )
                diskItem._globalAttributes.update( match )
                diskItem._globalAttributes.update( rule.localAttributes )
                diskItem._priority = priorityOffset + rule.priorityOffset
                diskItem.readAndUpdateMinf()
                diskItem._identified = True
                if debugHTML:
                  print >> debugHTML, '<font color=darkgreen><b>', diskItem, ':</b>', diskItem.type, '</font> (' + htmlEscape( rule.pattern.pattern ) + ':' + str( rule.type ) + ')<br>'
                yield diskItem
              break
          else:
            if allowYield and includeUnknowns:
              diskItem.readAndUpdateMinf()
              diskItem._identified = False
              yield diskItem
            unknownType.append( diskItem )
      if allowYield:
        for diskItem in nameSeriesGroupedItems.itervalues():
          diskItem._setLocal( 'name_serie', sorted( diskItem._getLocal( 'name_serie' ) ) )
          diskItem.readAndUpdateMinf()
          yield diskItem
      if debugHTML:
        for diskItem in nameSeriesGroupedItems.itervalues():
          print >> debugHTML, '<font color=darkgreen><b>', diskItem, ':</b> ', diskItem.type, repr( diskItem._getLocal( 'name_serie' ) ) + '</font><br>'
          #for f in diskItem.fullPaths()[ 1: ]:
            #print >> debugHTML, '&nbsp;' * 8 + f + '<br>'
          #print >> debugHTML, '</font>'
        for diskItem in unknownType:
          print >> debugHTML, '<font color=red>', diskItem.fullPath(), '(' + diskItem.format.name + ')</font><br>'
        
      if debugHTML:
        print >> debugHTML, '</blockquote>'
    
    if debugHTML:
      print >> debugHTML, '</body></html>'

  def findAttributes( self, attributes, selection={}, _debug=None, **required ):
    types = set( chain( *( self._childrenByTypeName.get( t, ()) for t in self.getAttributeValues( '_type', selection, required ) ) ) )
    if _debug is not None:
      print >> _debug, '!findAttributes!', repr(self.name), attributes, tuple( types ), selection, required
    for t in types:
      try:
        tableName, tableFields, tableAttributes, sql = self._tableFieldsAndInsertByTypeName[ t ]
      except KeyError:
        if _debug is not None:
          print >> _debug, '!findAttributes!  No table for type', t, 'in', repr(self.name)
        continue
      tableAttributes = [ '_diskItem' ] + tableAttributes
      tableFields = [ '_diskItem', 'T._uuid' ] + tableFields[1:]
      nonMandatoryKeyAttributes = self._nonMandatoryKeyAttributesByType[ t ]
      #if _debug is not None:
        #print >> _debug, '!findAttributes!  tableFields(', repr( t ), ') =', repr( tableFields )
      select = []
      tupleIndices = []
      for a in attributes:
        if a == '_type':
          tupleIndices.append( 1 )
          continue
        try:
          i = tableAttributes.index( a )
          select.append( tableFields[ i ] )
          tupleIndices.append( len( select ) + 1 )
        except ValueError:
          tupleIndices.append( 0 )
          continue
      typeOnly = False
      if not select:
        if [i for i in tupleIndices if i != 0]:
          select = [ 'COUNT(*)' ]
          typeOnly = True
        else:
          if _debug is not None:
            print >> _debug, '!findAttributes!  No attribute selected for type', t, 'in', repr(self.name), 'possible values are:', tableAttributes
          continue
      where = {}
      for f, a in izip( tableFields, tableAttributes ):
        if a in required or a not in nonMandatoryKeyAttributes:
          v = self.getAttributeValues( a, selection, required )
          #if _debug is not None:
            #print >> _debug, '!findAttributes!  getAttributeValues(', repr( a ), ', ... ) =', repr( v )
          if v:
            where[ f ] = v
      sql = 'SELECT DISTINCT ' + ', '.join( select ) + " FROM '" + tableName + "' T, _DISKITEMS_ D WHERE T._uuid=D._uuid"
      if where:
        sqlWhereClauses = []
        for f, v in where.iteritems():
          if v is None:
            sqlWhereClauses.append( f + '=NULL' )
          elif isinstance( v, basestring ):
            sqlWhereClauses.append( f + "='" + v + "'" )
          else:
            #sqlWhereClauses.append( f + ' IN (' + ','.join( (('NULL' if i is None else "'" + i +"'") for i in v) ) + ')' )
            whereParts = list()
            for i in v :
              if i is None :
                whereParts += ('NULL', )
              else :
                whereParts += ("'" + i +"'", )
            sqlWhereClauses.append( f + ' IN (' + ','.join( whereParts ) + ')' )
        sql += ' AND ' + ' AND '.join( sqlWhereClauses )
      if _debug is not None:
        print >> _debug, '!findAttributes! ->', sql
      cursor = self._getDatabaseCursor()
      sqlResult=[]
      try:
        try:
          sqlResult = cursor.execute( sql ).fetchall()
        except sqlite3.OperationalError, e:
          neuroProcesses.defaultContext().warning(e.message)
      finally:
        self._closeDatabaseCursor( cursor )
      for tpl in sqlResult:
        if typeOnly:
          if tpl[0] > 0:
            yield tuple( (( None, t )[i] for i in tupleIndices) )

        else:
          tpl = ( None, t ) + tpl
          yield tuple( (tpl[i] for i in tupleIndices) )
  
  def findDiskItems( self, selection={}, _debug=None, **required ):
    for t in self.findAttributes( ( '_diskItem', ), selection, _debug=_debug, **required ):
        yield self._diskItemFromMinf( t[0] )
  
  
  def createDiskItems( self, selection={}, _debug=None, **required ):
    types = set( chain( *( self._childrenByTypeName[ t ] for t in self.getAttributeValues( '_type', selection, required ) ) ) )
    if _debug is not None:
      print >> _debug, '!createDiskItems!', tuple( types ), selection, required
    for type in types:
      r = self.ruleSelectionByType.get( type )
      if r is None:
        if _debug is not None:
          print >> _debug, '!createDiskItems! no rule selection found for type', type
        continue
      possibleFormats = self.getAttributeValues( '_format', selection, required )
      if _debug is not None:
        print >> _debug, '!createDiskItems! possibleFormats = ', possibleFormats
      ruleSelectionByAttributeValue, ruleSelectionByMissingKeyAttributes, rulesDictionary, defaultAttributesValues = r
      #key = ( tuple( ( selection.get( i, required.get( i, '' ) ) for i in ruleSelectionByAttributeValue ) ),
              #tuple( ( (False if selection.get( i, required.get( i ) ) else True) for i in ruleSelectionByMissingKeyAttributes ) ) )
      keys = []
      stack = [ [
                [ self.getAttributeValues( i, selection, required, defaultAttributesValues.get( i, Undefined ) ) for i in ruleSelectionByAttributeValue ],
                [ self.getAttributeValues( i, selection, required, defaultAttributesValues.get( i, Undefined ) ) for i in ruleSelectionByMissingKeyAttributes ]
              ] ]
      if _debug is not None:
        print >> _debug, '!createDiskItems! stack = ', stack
      while stack:
        k1, k2 = stack.pop( 0 )
        for i in xrange( len(k1) ):
          if isinstance( k1[i], ( set, list, tuple ) ):
            if k1[i]:
              stack += [ [ k1[ :i] + [j] + k1[i+1:], k2 ] for j in k1[i] ]
            else:
              stack += [ [ k1[ :i] + [''] + k1[i+1:], k2 ] ]
            k1 = None
            break
        if k1 is not None:
          for i in xrange( len(k2) ):
            if isinstance( k2[i], ( set, list, tuple ) ) and k2[i]:
              stack += [ [ k1, k2[ :i] + [j] + k2[i+1:] ] for j in k2[i] ]
              k2 = None
              break
          if k2 is not None:
            keys.append( ( tuple(k1), tuple((not(i)) for i in k2) ) )
      if _debug is not None:
        print >> _debug, '!createDiskItems! keys for rules selection = ', keys
      for key in keys:
        rules = rulesDictionary.get( key )
        if rules is not None:
          if _debug is not None:
            print >> _debug, '!createDiskItems! rules = ', [r.pattern.pattern for r in rules]
          for rule in rules:
            if rule._formatsNameSet:
              formats = rule._formatsNameSet.intersection( possibleFormats )
            else:
              formats = possibleFormats
            if not formats:
              if _debug is not None:
                print >> _debug, '!createDiskItems! no possible format for type', type, 'and rule', rule.pattern.pattern
              continue
            cg = CombineGet( required, selection, defaultAttributesValues )
            names = rule.pattern.multipleUnmatch( cg )
            if names:
              for name, unmatchAttributes in names:
                databaseDirectory = self.getAttributeValues( '_databaseDirectory', selection, required )
                if databaseDirectory:
                  databaseDirectory = databaseDirectory[ 0 ]
                else:
                  databaseDirectory = self.directory
                for format in (getFormat( f ) for f in formats): # search format in all format including Series of ...
                  if format.name == 'Directory':
                    files = [ os.path.join( databaseDirectory, name ) ]
                  elif isinstance( format, FormatSeries ): # a Series of ... has in _files the pattern of each data with # instead of the number
                    cg2 = CombineGet( {'name_serie' : "#"}, required, selection, defaultAttributesValues ) 
                    name2 = rule.pattern.unmatch( cg2, cg2 )
                    format2=self.formats.getFormat(format.baseFormat.name) # get the base file format
                    files = [ os.path.join( databaseDirectory, name2 + '.' + e ) for e in format2.extensions() ]
                  else:
                    format=self.formats.getFormat(format.name) # get corresponding file format
                    files = [ os.path.join( databaseDirectory, name + '.' + e ) for e in format.extensions() ]
                  diskItem = File( os.path.join( databaseDirectory, name ), None )
                  diskItem._files = files
                  diskItem.type = getDiskItemType( type )
                  diskItem.format = getFormat( str(format.name) )
                  #diskItem.uuid( saveMinf=False )
                  diskItem._globalAttributes[ '_database' ] = self.name
                  diskItem._globalAttributes[ '_ontology' ] = self.fso.name
                  diskItem._write = True
                  
                  c = CombineGet( unmatchAttributes, required, selection, defaultAttributesValues )
                  for n in self.keysByType[ type ]:
                    if n=="name_serie": # name_serie is a local attribute
                      diskItem._setLocal(n, c.get(n, ""))
                    else:
                      diskItem._globalAttributes[ n ] = c.get( n, '' )
                  for n, v in rule.localAttributes:
                    diskItem._globalAttributes[ n ] = v
                  diskItem._priority = rule.priorityOffset
                  yield diskItem
            elif _debug is not None:
              print >> _debug, '!createDiskItems! rule', rule.pattern.pattern, 'not "unmatched"'
        else:
          if _debug is not None:
            print >> _debug, '!createDiskItems! no rule found for type', type,' and key =', key
  
  
  def getAttributesEdition( self, *types ):
    editable = set()
    values = {}
    for t1 in types:
      for t2 in self._childrenByTypeName[ t1 ]:
        e = self._attributesEditionByType.get( t2 )
        if e is not None:
          editable.update( e[0] )
          for a, v in e[1].iteritems():
            values.setdefault( a, set() ).update( v )
    return editable, values
  
  
  def getTypeChildren( self, *types ):
    return set( chain( *( self._childrenByTypeName[ t ] for t in  types ) ) )
  
  
  def getTypesKeysAttributes( self, *types ):
    result = []
    for t1 in types:
      for t2 in self._childrenByTypeName[ t1 ]:
        for a in self.keysByType.get( t2, () ):
          if a not in result: result.append( a )
    return result
    
  
  def getTypesFormats( self, *types ):
    result = set()
    for t1 in types:
      for t2 in self._childrenByTypeName[ t1 ]:
        f = self._formatsByTypeName.get( t2 )
        if f:
          result.update( f )
    return result
    
    
  def newFormat( self, name, patterns ):
    if getFormat( name, None ) is None:
      bvPatterns = []
      for p in patterns:
        i = p.find( '|' )
        if i < 0:
          bvPatterns.append( '*.' + p )
        else:
          bvPatterns.append( p[ :i+1 ] + '*.' + p[ i+1: ] )
      Format( name, bvPatterns )
      self.formats.newFormat( name, patterns )

  
#------------------------------------------------------------------------------
class SQLDatabases( Database ):
  def __init__( self, databases=[] ):
    super(SQLDatabases, self).__init__()
    self._databases = SortedDictionary()
    self.formats = FileFormats( '<TODO>' )
    for database in databases:
      self.add( database )
  
  
  def iterDatabases( self ):
    return self._databases.itervalues()
  
  
  def database( self, name ):
    return self._databases[ name ]
  
  def hasDatabase(self, name):
    return self._databases.has_key(name)
  
  def add( self, database ):
    self._databases[ database.name ] = database
    self.formats.update( database.formats )
    # SQLDatabases notifier notifies when one of its database notifies an update
    database.onUpdateNotifier.add(self.onUpdateNotifier.notify)
  
  def remove( self, name ):
    if self._databases.has_key(name):
      del self._databases[name]
    
  def removeDatabases( self ):
    self._databases = SortedDictionary()
    self.formats = FileFormats( '<TODO>' )
  
  
  def clear( self ):
    for d in self.iterDatabases():
      d.clear()
  
  
  def update( self, directoriesToScan=None, recursion=True, context=None ):
    self.onUpdateNotifier.delayNotification()
    for d in self.iterDatabases():
      d.update( directoriesToScan=directoriesToScan, recursion=recursion, context=context )
    self.onUpdateNotifier.restartNotification()
  
  
  def _iterateDatabases( self, selection, required={} ):
    databases = self.getAttributeValues( '_database', selection, required )
    if not databases:
      for d in self._databases.itervalues():
        yield d
    for n in databases:
      try:
        yield self._databases[os.path.normpath(n)]
      except KeyError:
        pass
  
  
  def insertDiskItems( self, diskItems, update=False ):
    for diskItem in diskItems:
      baseName = diskItem.get( '_database' )
      if baseName is None:
        if len( self._databases ) == 1:
          database = self._databases.values()[0]
        else:
          raise Database.NotInDatabaseError( _( 'Cannot find out in which database "%s" should be inserted' ) % ( diskItem.fullPath(), ) )
      else:
        database = self._databases[ baseName ]
      database.insertDiskItems( (diskItem,), update=update )
  
  
  def removeDiskItems( self, diskItems, eraseFiles=False ):
    for diskItem in diskItems:
      baseName = diskItem.get( '_database' )
      if baseName is None:
        if len( self._databases ) == 1:
          database = self._databases.values()[0]
        else:
          raise Database.NotInDatabaseError( _( 'Cannot find out from which database "%s" should be removed' ) % ( diskItem.fullPath(), ) )
      else:
        database = self._databases[ baseName ]
      database.removeDiskItems( (diskItem,), eraseFiles=eraseFiles )
  
  
  def getDiskItemFromUuid( self, uuid, defaultValue=Undefined ):
    for database in self._databases.itervalues():
      item = database.getDiskItemFromUuid( uuid, None )
      if item is not None:
        return item
    if defaultValue is Undefined:
      raise Database.Error( _( 'No database contain a DiskItem with uuid %(uuid)s' ) % { 'uuid': str(uuid) } )
    return defaultValue
  
  
  def getDiskItemFromFileName( self, fileName, defaultValue=Undefined ):
    for database in self._databases.itervalues():
      item = database.getDiskItemFromFileName( fileName, None )
      if item is not None:
        return item
    if defaultValue is Undefined:
      raise Database.Error( _( 'No database reference file "%(filename)s"' ) % { 'filename': fileName } )
    return defaultValue
  
  
  def findAttributes( self, attributes, selection={}, _debug=None, **required ):
    index = 0
    for a in attributes:
      if a == '_database':
        break
      index += 1
    else:
      index = -1
    for database in self._iterateDatabases( selection, required ):
      for tpl in database.findAttributes( attributes, selection, _debug=_debug, **required ):
        if index >= 0:
          yield tpl[:index] + ( database.name, ) + tpl[index+1:]
        else:
          yield tpl
  
  
  def findDiskItems( self, selection={}, _debug=None, **required ):
    for database in self._iterateDatabases( {}, required ):
      for item in database.findDiskItems( selection, _debug=_debug, **required ):
        yield item
  
  
  def createDiskItems( self, selection={}, _debug=None, **required ):
    for database in self._iterateDatabases( {}, required ):
      for item in database.createDiskItems( selection, _debug=_debug, **required ):
        yield item
  
  
  def createDiskItemFromFileName( self, fileName, defaultValue=Undefined ):
    for database in self._iterateDatabases( {}, {} ):
      item = database.createDiskItemFromFileName( fileName, None )
      if item is not None:
        return item
    if defaultValue is Undefined:
      raise Database.Error( _( 'No database can reference file "%(filename)s"' ) % { 'filename': fileName } )
    return defaultValue
  
  
  
  def createDiskItemFromFormatExtension( self, fileName, defaultValue=Undefined ):
    for database in self._iterateDatabases( {}, {} ):
      item = database.createDiskItemFromFormatExtension( fileName, None )
      if item is not None:
        return item
    if defaultValue is Undefined:
      raise Database.Error( _( 'No database has a format to recognise "%(filename)s"' ) % { 'filename': fileName } )
    return defaultValue
  
  
  def changeDiskItemFormat( self, diskItem, newFormat ):
    for database in self._iterateDatabases( {}, {} ):
      item = database.changeDiskItemFormat( diskItem, newFormat )
      if item is not None:
        return item
    return None
  
  def changeDiskItemFormatToSeries( self, diskItem ):
    """
    Changes the format of the diskItem to Series of diskItem.format
    The number is extracted from the name to begin the name_serie list attribute. Other files with the same name but another number are searched in the parent directory to find the other numbers of the serie.
    """
    formatSeries=getFormat("Series of "+diskItem.format.name)
    if formatSeries is not None:
      parentDir=os.path.dirname(diskItem.fileName())
      filename=os.path.basename(diskItem.fileName())
      # get the number at the end of the filename : it is considered as the name_serie
      regexp=re.compile("(.+?)(\d+)\.(.+)")
      match=regexp.match(filename)
      if match:
        diskItem.format=formatSeries
        name=match.group(1)
        num=match.group(2)
        ext=match.group(3)
        name_serie=[]
        diskItem._setLocal("name_serie", name_serie)
        diskItem._files=[f.replace(num, "#") for f in diskItem._files]
        # search the other numbers of the serie
        regexp=re.compile("^"+name+"(\d+)\."+ext+"$")
        for file in sorted(os.listdir(parentDir)):
          match=regexp.match(file)
          if match:
            name_serie.append(match.group(1))
    return diskItem
  
  def getAttributesEdition( self, *types ):
    editable = set()
    values = { '_database': tuple( (i.name for i in self._databases.itervalues()) ) }
    for database in self._databases.itervalues():
      e, d = database.getAttributesEdition( *types )
      editable.update( e )
      for a, v  in d.iteritems():
        values.setdefault( a, set() ).update( v )
    return editable, values
  
  def getTypeChildren( self, *types ):
    if self._databases:
      return set( chain( *(d.getTypeChildren( *types ) for d in self._databases.itervalues() ) ) )
    return ()
  
  
  def getTypesKeysAttributes( self, *types ):
    if self._databases:
      # Combine attributes from databases but try to keep the order (not using only a set)
      # because this order is used to build combos on graphical interface
      result = []
      set_result = set()
      for d in self._databases.itervalues():
        for a in d.getTypesKeysAttributes( *types ):
          if a not in set_result:
            result.append( a )
            set_result.add( a )
      return result
    return []
    
  
  def getTypesFormats( self, *types ):
    if self._databases:
      return set( chain( *(d.getTypesFormats( *types ) for d in self._databases.itervalues() ) ) )
    return ()

  def currentThreadCleanup( self ):
    for database in self._iterateDatabases( {}, {} ):
      database.currentThreadCleanup()
  
  
  def newFormat( self, name, patterns ):
    for database in self._iterateDatabases( {}, {} ):
      database.newFormat( name, patterns )

