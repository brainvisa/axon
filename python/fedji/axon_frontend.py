# -*- coding: utf-8 -*-
from brainvisa.data.sqlFSODatabase import Database
from fedji.api import fedji_connect

from brainvisa.data.fileSystemOntology import FileSystemOntology
from soma.undefined import Undefined

import os
#from soma.database.entity import EntityDefinition
#import types
#import sys

#import time
#from itertools import izip, chain
#from StringIO import StringIO
#import cPickle

from soma.minf.api import readMinf
#from soma.html import htmlEscape
#from soma.sorted_dictionary import SortedDictionary

#from soma.translation import translate as _
#from soma.path import split_path, relative_path
#from soma.somatime import timeDifferenceToString
#from soma.uuid import Uuid
#from soma.notification import Notifier
#from soma.databases.api import sqlite3, ThreadSafeSQLiteConnection

from brainvisa.data.fileSystemOntology import FileSystemOntology, SetContent
#from brainvisa.processes import diskItemTypes, getDiskItemType
import brainvisa.processes
#from brainvisa.configuration import neuroConfig
#from brainvisa.processing.neuroException import showWarning
#from brainvisa.data.neuroDiskItems import DiskItem, getFormat, getFormats, Format, FormatSeries, File, Directory, getAllFormats, MinfFormat
#from brainvisa.processing.neuroException import HTMLMessage
#from brainvisa.data.patterns import DictPattern
#from brainvisa.data.sql import mangleSQL, unmangleSQL
#from brainvisa.data.fileformats import FileFormats
#from brainvisa.data.directory_iterator import DirectoryIterator, VirtualDirectoryIterator

class AxonFedjiDatabase(Database):
    def __init__( self, fedji_url, database_name, directory, fso=None, context=None ):
        super(AxonFedjiDatabase, self).__init__()
	# Connect to FEDJI on database "axon" and collection "disk_items"
        self.fedji_collection = fedji_connect(fedji_url).axon.disk_items
        # => self.fedji_collection = fedji_connect(fedji_url).__getattr__('axon').__getattr__('disk_items')
        self.name = database_name
        self.directory = os.path.normpath( directory )
        if not os.path.exists( self.directory ):
            raise ValueError( HTMLMessage(_t_('<em>%s</em> is not a valid directory') % str( self.directory )) )
        minf = os.path.join(self.directory, 'database_settings.minf')
        if fso is None:
            if os.path.exists(minf):
                fso = readMinf(minf)[ 0 ].get('ontology', 'brainvisa-3.2.0')
            else:
                fso='brainvisa-3.2.0'
        self.fso = FileSystemOntology.get(fso)
        
    def checkTables(self):
        """
        Checks if all types currently defined in the database ontology 
        have a matching table in the sqlite database. It may be not the
        case when the database have been update with a version of 
        brainvisa that has not all the toolboxes. It should then be updated.
        """
        pass 
  
    def insertDiskItems( self, diskItems, update=False ):
        for d in diskItems:
            if d.type is None:
                raise DatabaseError( _('Cannot insert an item without type in a database: %s') % ( unicode( d ), ) )

            d._globalAttributes["_database"] = self.name

            if update:
                raise NotImplementedError('DiskItem update is not yet implemented')
            else:
                documents = d.globalAttributes()
                documents['type'] = [d.type.name] + [i.name for i in d.type.parents()]
                documents['format'] = d.format.name
                documents['_id'] = documents.pop('uuid')
                documents['files'] = d._files
                self.fedji_collection.insert(documents)
  
    def removeDiskItems( self, diskItems, eraseFiles=False ):
        for d in diskItems:
            uuid = str(d.uuid(saveMinf=False))
            self.fedji_collection.remove({'_id': uuid})
            if eraseFiles:
                # TODO: erase files from disk
                for path in diskItems.fullPaths():
                    shutils.rmtree(path)

    def _createDiskitemFromDocument(self, doc):
        diskitem = DiskItem("Document " + doc['_id'], None)
        diskitem.type = getDiskItemType(doc.pop('type')[0])
        diskitem.format = getFormat(doc.pop('format'))
        diskitem._globalAttributes["_database"] = self.name
        diskitem._changeUuid( doc.pop('_id') )
        diskitem._files = doc.pop['files']
        diskitem._updateGlobal(doc)
        return diskitem
    
    def getDiskItemFromUuid( self, uuid, defaultValue=Undefined ):
        documents = list(self.fedji_collection.find({'_id':uuid}))
        if documents:
            return self._createDiskitemFromDocument(documents[0])
        elif defaultValue is Undefined:
            raise DatabaseError( _( 'Database "%(database)s" contains no DiskItem with uuid %(uuid)s' ) % { 'database': self.name,  'uuid': str(uuid) } )
        return defaultValue
  

   # TODO ...
  
    def getDiskItemFromFileName( self, fileName, defaultValue=Undefined ):
      if fileName.startswith(self.directory):
        entity=None
        try:
          res = self._cursor.execute("Any X WHERE X has_file F, F name %s" % fileName )
          entity = res.get_entity(0, 0)
        except :
          brainvisa.processes.defaultContext().warning( "Cannot question database "+self.name+". You should update this database." )
        if entity is not None:
          return self._diskItemFromEntity( entity )
      if defaultValue is Undefined:
        raise DatabaseError( _( 'Database "%(database)s" does not reference file "%(filename)s"' ) % { 'database': self.name,  'filename': fileName } )
      return defaultValue
    
    
    # Should be a copy-paste from brainvisa.data.SQLDatabase.createDiskItemFromFileName
    def createDiskItemFromFileName( self, fileName, defaultValue=Undefined ):
      diskItem = self.createDiskItemFromFormatExtension( fileName, None )
      if diskItem is not None:
        d=self.directory
        if fileName.startswith( d ):
          splitted = split_path( fileName[ len(d)+1: ] )
          if os.path.isdir(fileName):
            lastContent=[]
          else:
            lastContent=None
          content = reduce( lambda x,y: [(y,x)], reversed(splitted[:-1]), [ (os.path.basename(f), lastContent) for f in diskItem._files ] )
          vdi = VirtualDirectoryIterator( fileName[ :len(d) ], content )
          lastItem = None
          for item in self.scanDatabaseDirectories( vdi ):
            lastItem = item
          if lastItem is not None and fileName in lastItem.fullPaths():
            return lastItem
      if defaultValue is Undefined:
        raise DatabaseError( _( 'Database "%(database)s" cannot reference file "%(filename)s"' ) % { 'database': self.name,  'filename': fileName } )
      return defaultValue
      
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
          result._files = [ os.path.normpath( noExt + '.' + ext ) for ext in newFormat.extensions() ]
      return result
    
    
    # Should be a copy-paste from brainvisa.data.SQLDatabase.scanDatabaseDirectories
    def scanDatabaseDirectories( self, directoriesIterator=None, includeUnknowns=False, directoriesToScan=None, recursion=True, debugHTML=None ):
      
      if debugHTML:
        print >> debugHTML, '<html><body><h1>Scan log for database <tt>' + self.name + '</tt></h1>\n<h2>Directory</h2><blockquote>'
        print >> debugHTML, self.directory, '</blockquote>'
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
            diskItem._files = [ os.path.normpath( it.fullPath() ) ]
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
                  diskItem._files = [ os.path.normpath( f ) for f in files ]
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
                  diskItem._files = [ os.path.normpath( f ) for f in files ]
                  diskItem._globalAttributes[ '_database' ] = self.name
                  diskItem._identified = False
                  yield diskItem
          else:
            diskItem = File( nameWithoutExtension, None )
            diskItem.format = getFormat( str( format ) )
            diskItem._files = [ os.path.normpath( os.path.join( itDirectory.fullPath(), i ) ) for i in files ]
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
                    groupDiskItem._files = [ os.path.normpath( os.path.join( itDirectory.fullPath(), n + '.' + i ) ) for i in self.formats.getFormat( format ).extensions() ]
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
    
    def findAttributes( self, attributes, selection={}, _debug=None, exactType=False, **required ):
      # query = required.copy()
      # query.update(selection)
      #  for attribute in attributes:
      #     yield list(self.fedji_collection.find(query,fields=[attribute]))
    
      try:
        db_index=attributes.index("_database")
      except ValueError:
        db_index=-1
      nb_attr=len(attributes)
      req="Any "+",".join(["A"+str(i) for i in xrange(nb_attr) if i != db_index])
      req+=" WHERE "
      req+=",".join(["X "+EntityDefinition.valid_attribute_name(attributes[i])+" A"+str(i) for i in xrange(nb_attr) if i != db_index])
      for a, v in required.iteritems():
        if isinstance(v, basestring):
          if a == '_type':
            req+=", X is_instance_of "+EntityDefinition.valid_entity_type_name(v)
          else:
            req+=", X "+EntityDefinition.valid_attribute_name(a)+" '"+v+"'"
        else:
          if a == '_type':
            req+=", X is_instance_of in ("+",".join([EntityDefinition.valid_entity_type_name(value) for  value in v])+")"
          else:
            req+=", X "+EntityDefinition.valid_attribute_name(a)+" in ("+",".join(["'"+value+"'" for  value in v])+")"
          
      try:
        res=self._cursor.execute(req)
        #print "=> ", res
        for r in res.rows:
          if db_index != -1:
            r.insert(db_index, self.name)
          yield tuple([v for v in r])
    
      except Exception, e:
        brainvisa.processes.defaultContext().warning(e.message)    
    
    def findDiskItems( self, selection={}, _debug=None, exactType=False, **required ):
      #print "*findDiskItems"
      req="Any X WHERE "
      for a, v in required.iteritems():
        if isinstance(v, basestring):
          req+="X "+EntityDefinition.valid_attribute_name(a)+" '"+v+"', "
        else:
          req+="X "+EntityDefinition.valid_attribute_name(a)+" in ("+",".join(["'"+value+"'" for  value in v])+"), "
          
      req=req[:-2]
      try:
        res=self._cursor.execute(req)
        for e in res.entities():
          yield self._diskItemFromEntity(e)
      except Exception, e:
        brainvisa.processes.defaultContext().warning(e.message)    
    
    
    # Should be a copy-paste from brainvisa.data.SQLDatabase.createDiskItems
    def createDiskItems( self, selection={}, _debug=None, exactType=False, **required ):
      if exactType:
        types = set( self.getAttributeValues( '_type', selection, required ) )
      else:
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
                      files = [ os.path.normpath( os.path.join( databaseDirectory, name ) ) ]
                    elif isinstance( format, FormatSeries ): # a Series of ... has in _files the pattern of each data with # instead of the number
                      cg2 = CombineGet( {'name_serie' : "#"}, unmatchAttributes, required, selection, defaultAttributesValues ) 
                      name2 = rule.pattern.unmatch( cg2, cg2 )
                      format2=self.formats.getFormat(format.baseFormat.name) # get the base file format
                      files = [ os.path.normpath( os.path.join( databaseDirectory, name2 + '.' + e ) ) for e in format2.extensions() ]
                    else:
                      format=self.formats.getFormat(format.name) # get corresponding file format
                      files = [ os.path.normpath( os.path.join( databaseDirectory, name + '.' + e ) ) for e in format.extensions() ]
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


