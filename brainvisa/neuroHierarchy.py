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

import neuroConfig

if neuroConfig.newDatabases:
  import os
  
  from brainvisa.data.sqlFSODatabase import SQLDatabase, SQLDatabases
  from brainvisa.data.readdiskitem import ReadDiskItem
  from brainvisa.data.writediskitem import WriteDiskItem
  from neuroException import showException, showWarning
  import neuroConfig
  
  global databaseVersion
  databaseVersion="1.1" 
  # mapping between databases versions and axon versions : database version -> first axon version where this database version is used
  databaseVersions={ "1.0" : "3.1.0", "1.1" : "3.2.0"}
  
  def initializeDatabases():
    global databases
    databases = SQLDatabases()
  
  def openDatabases():
    from neuroProcesses import defaultContext
    global databases
      
    newDatabases=[] 
    for dbSettings in neuroConfig.dataPath:
      try:
        if getattr(dbSettings, "builtin", False) and databases.hasDatabase(dbSettings.directory): # builtin databases are not re created
          newDatabases.append(databases.database(dbSettings.directory))
        else:
          databases.remove( dbSettings.directory )
          remoteAccessURI = os.path.join( dbSettings.directory, 'remoteAccessURI' )
          print '!!', repr( remoteAccessURI )
          if os.path.exists( remoteAccessURI ):
            print '!remote!'
            import Pyro.core
            from soma.pyro import ThreadSafeProxy
            print '!2!'
            uri = Pyro.core.PyroURI( open( remoteAccessURI ).read() )
            print '!3!'
            print 'Database', dbSettings.directory, 'is remotely accessed from', str( uri )
            base = ThreadSafeProxy( uri.getAttrProxy() )
            newDatabases.append( base )
          else:
            print '!local!'
            otherSqliteFiles=[]
            if dbSettings.expert_settings.sqliteFileName != ":memory:":
              if dbSettings.expert_settings.sqliteFileName:
                path, ext = os.path.splitext(dbSettings.expert_settings.sqliteFileName)
              else:
                path=os.path.join( dbSettings.directory, 'database' )
                ext='.sqlite'
      
              sqlite=path+"-"+databaseVersion+ext
              # other versions of sqlite file
              other=path+ext
              if os.path.exists(other):
                otherSqliteFiles.append(other)
              for version in databaseVersions.keys():
                if version != databaseVersion:
                  other=path+"-"+version+ext
                  if os.path.exists(other):
                    otherSqliteFiles.append(path+"-"+version+ext)
            else:
              sqlite=dbSettings.expert_settings.sqliteFileName
  
            base = SQLDatabase( sqlite, dbSettings.directory, fso=dbSettings.expert_settings.ontology, context=defaultContext(), otherSqliteFiles=otherSqliteFiles )
  
            newDatabases.append( base )
              
            # Usually users do not have to modify a builtin database. Therefore no warning is shown for these databases.
            if (not os.access(dbSettings.directory, os.W_OK) or ( os.path.exists(sqlite) and not os.access(sqlite, os.W_OK)) ):
              showWarning(_t_("The database "+base.name+" is read only, you will not be able to add new items in this database."))
            if base.fso.name == "brainvisa-3.0":
              showWarning(_t_("The database "+base.name+" uses brainvisa-3.0 ontology which is deprecated. You should convert this database to the new ontology using the process Data management -> Convert Old database."))
      except:
        showException()    
    # update SQLDatabases object
    databases.removeDatabases()
    for db in newDatabases:
      databases.add(db)

    
  def hierarchies():
    return databases._databases.values()
    
else:
  import types, string, re, sys, os, threading, cPickle, threading, operator, time, traceback
  from neuroData import *
  import neuroConfig
  from neuroDiskItems import *
  import neuroLog
  from neuroException import *
  from brainvisa.data import temporary
  from brainvisa import shelltools
  from fileSystemOntology import *
  
  
  #----------------------------------------------------------------------------
  # The following global variables are set in neuroHierarchyGUI.py
  progressBarFactory = None
  eventsCallback = None
  
  #----------------------------------------------------------------------------
  class AttributesFilter:
    class _impossibleValue: pass
    
    def __init__( self, attributes ):
      self.attributes = attributes
    
    def match( self, diskItem ):
      for ( key, value ) in self.attributes.items():
        itemValue = diskItem.get( key, self._impossibleValue )
        if itemValue is not self._impossibleValue:
          if callable( value ):
            if not value( key, itemValue, diskItem ):
              return False
          else:
            if value != itemValue:
              return False
      return True
      
    def matchStrict( self, diskItem ):
      for key, value in self.attributes.items():
        itemValue = diskItem.get( key, self._impossibleValue )
        if itemValue is not self._impossibleValue:
          if callable( value ):
            if not value( key, itemValue, diskItem ):
              return False
          else:
            if value != itemValue:
              return False
        else:
          return False
      return True
  
  
  
  
  
  
  #----------------------------------------------------------------------------
  class ReadDiskItem( Parameter ):
    def __init__( self, diskItemType, formats, requiredAttributes={},
                  enableConversion=1, ignoreAttributes=0 ):
      Parameter.__init__( self )
      self.type = getDiskItemType( diskItemType )
      self.formats = getFormats( formats )
      self.enableConversion = enableConversion
      self.requiredAttributes = requiredAttributes.copy()
      self._modified = 0
      self.ignoreAttributes = ignoreAttributes;
      
    def typeInfo( self, translator = None ):
      if translator: translate = translator.translate
      else: translate = _
      formats = ''
      for f in self.formats:
        if formats: formats += ', '
        formats += translate( f.name )
      return  ( ( translate( 'Type' ), translate( self.type.name ) ),
                ( translate( 'Access' ), translate( 'input' ) ), 
                ( translate( 'Formats' ), formats ) )
        
    
    def checkValue( self, name, value ):
      Parameter.checkValue( self, name, value )
      if value is not None:
        if not value.isReadable():
          raise RuntimeError( HTMLMessage(_t_( '<em>%s</em> is not readable' ) % unicode( value )) )
  
        if getattr( value, '_write', False ):
          readValue = self.findValue( value.fullPath() )
          if readValue is not None:
            value.__setstate__( readValue.__getstate__() )
            value._write = False
  
    
    
    def findItems( self, directory, attributes, 
                  maxItems = -1, 
                  maxDepth = -1, 
                  requiredAttributes = {},
                  convertibleTypes = None,
                  attributesValues = None,
                  fileNameAttributes = None,
                  volume_dimension = None,
                  fileName = None,
                  eventsCallback = None,
                  progressBar = None ):
  #debug#    print '  !ReadDiskItem.findItems! 1', directory, attributes, maxItems, maxDepth
      if self.enableConversion and convertibleTypes is None:
        convertible = {}
        for format in self.formats:
          convertible.update( getConvertersTo( ( self.type, format ) ) )
        convertible = convertible.keys()
        convertibleTypes = {}
        for t,format in convertible:
          convertibleTypes[ t ] = t
        convertibleTypes = convertibleTypes.keys()
        del convertible
      else:
        convertibleTypes = []
      result = []
      attributesFilter = attributes.copy()
      attributesFilter = AttributesFilter( attributesFilter )
      requiredAttributesFilter = AttributesFilter( requiredAttributes )
      if directory.scanner and \
        attributesFilter.match( directory._globalAttributes ) and \
        requiredAttributesFilter.match( directory._globalAttributes ):
        ok = 0
        for t in directory.scanner.possibleTypes.keys():
          for pt in [ self.type ] + convertibleTypes:
            if isSameDiskItemType( t, pt ):
              ok = 1
              break
            if ok: break
        if ok:
          childs = directory.childs()
          for item in childs:
  #debug#          print '!ReadDiskItem.findItems! 2', item, item._globalAttributes
            if attributesFilter.match( item._globalAttributes ) and \
              requiredAttributesFilter.match( item ):
  #debug#            print '!ReadDiskItem.findItems! 2.1'
              ok = 0
              if isSameDiskItemType( item.type, self.type ) and \
                item.format in self.formats:
  #debug#              print '!ReadDiskItem.findItems! 2.2'
                ok = 1
              elif self.enableConversion:
  #debug#              print '!ReadDiskItem.findItems! 2.3'
                for format in self.formats:
                  if getConverter( (item.type,item.format), (self.type, format) ):
  #debug#                  print '!ReadDiskItem.findItems! 2.4'
                    ok = 1
                    break
              if ok and requiredAttributesFilter.matchStrict( item ):
  #debug#              print '!ReadDiskItem.findItems! 3'
                result.append( item )
                if attributesValues is not None:
                  for attrName, attrValue in item.hierarchyAttributes().items():
                    values = attributesValues.get( attrName, [] )
                    if attrValue not in values:
                      values.append( attrValue )
                    attributesValues[ attrName ] = values
                if maxItems > 0 and len( result ) >= maxItems: break
            if maxDepth and isinstance( item, Directory ):
              result += ReadDiskItem.findItems( self, item, attributes,  \
                                        maxItems-len(result), maxDepth-1, \
                                        requiredAttributes = requiredAttributes,
                                        convertibleTypes=convertibleTypes,
                                        attributesValues = attributesValues,
                                        fileNameAttributes = fileNameAttributes,
                                        volume_dimension = volume_dimension,
                                        fileName = fileName,
                                        eventsCallback = eventsCallback )
              if maxItems > 0 and len( result ) >= maxItems: break
            if progressBar is not None:
              progressBar.step()
            if eventsCallback is not None:
              eventsCallback()
      return result
  
    def findValue( self, value, force=0, requiredAttributes=None ):
      if requiredAttributes is None:
        requiredAttributes = self.requiredAttributes
      debug = neuroConfig.debugParametersLinks
      if debug:
        print >> debug, '\n' + '-' * 70
        print >> debug, self.__class__.__name__ + '(\'' + str( self.type ) + '\').findValue'
        if isinstance( value, DiskItem ):
          print >> debug, '  value type = DiskItem'
          print >> debug, '  fullPath = ', value
          print >> debug, '  attributes:'
          for n, v in value.attributes().items():
            print >> debug, '   ', n, '=', v
        else:
          print >> debug, '  value type =', type( value )
          print >> debug, '  value = ', value
        print >> debug, '  required attributes:'
        for n, v in requiredAttributes.items():
          print >> debug, '   ', n, '=', v
      if type( value ) is types.DictType:
        stupidItem = DiskItem( 'void', None )
        stupidItem._updateLocal( value )
        return self.findValue( stupidItem, force=1,
                              requiredAttributes=requiredAttributes )
      result = None
      values = self.findValues( value, force, requiredAttributes )
      if not values and isinstance( value, DiskItem ) \
        and not isinstance( self, WriteDiskItem ) and not value.isReadable():
        wd = WriteDiskItem( self.type, self.formats, 
                            requiredAttributes = self.requiredAttributes,
                            exactType=False,
                            ignoreAttributes=self.ignoreAttributes )
        values = wd.findValues( value, force, requiredAttributes )
      if values:
        if len( values ) == 1:
          result = values[ 0 ]
        else:
          # Find the item with the "smallest" "distance" from item
          values = map( lambda item, value=value: ( value.distance( item ), item ),
                        values )
          values.sort()
          if debug:
            print >> debug, '  findValue priority sorted items:'
            for l in values:
              print >> debug, '   ', l
          if values[ 0 ][ 0 ] != values[ 1 ] [ 0 ]:
            result = values[ 0 ][ 1 ]
      if debug:
        print >> debug, '-> findValue return', result
        if result is not None:
          print >> debug, '-> type:', result.type
          print >> debug, '-> format:', result.format
          print >> debug, '-> attributes:'
          for n, v in result.attributes().items():
            print >> debug, '->  ', n, '=', v
        print >> debug, '-' * 70 + '\n'
        debug.flush()
      return result
      
      
    def findValues( self, value, force=0, requiredAttributes={}, debug=False ):
      global flatHierarchyContent
      if debug:
        print '\n-------------------------------\n!findValues!', self.__class__.__name__, self.type, value, requiredAttributes
      if value is None:
        if debug:
          print '!findValues! 1'
        return []
      if len( self.requiredAttributes ) > 0:
        # merge self.requiredAttributes and requiredAttributes
        if len( requiredAttributes ) == 0:
          requiredAttributes = self.requiredAttributes
        else:
          ra = self.requiredAttributes
          for k,v in requiredAttributes.items():
            ra[k] = v
          requiredAttributes = ra
      if isinstance(value, types.StringTypes): #type( value ) is types.StringType:
        if debug:
          print '!findValues! 2'
        if not value: return []
        item = None
        # Search item in hierarchies
        value = os.path.abspath( os.path.normpath( value ) )
        ( void, last ) = os.path.split( value )
        completions = self.findFromPathInHierarchies( value )
        if debug: print '!findValues! 2.1', completions
        for i in completions:
          if last == i.name or last in i.fileNames():
            ok = 0
            if isSameDiskItemType( i.type, self.type ) and i.format in self.formats:
              ok = 1
            elif self.enableConversion:
              for format in self.formats:
                if getConverter( (i.type, i.format), (self.type, format) ):
                  ok = 1
                  break
            if ok:
              item = i
              break
        if not item:
          if debug:
            print '!findValues! 2.2'
          # Try to identify item according to parameter format
          i=DiskItem(value, None)
          i.findFormat(self.formats)
          if i.format:
            item=i
            item.type=self.type
            if not self.ignoreAttributes: item.setFormatAndTypeAttributes()
        if not item:
          if debug:
            print '!findValues! 2.3'
          if self.enableConversion:
            convertible = {}
            for format in self.formats:
              convertible.update( getConvertersTo( ( self.type, format ), keepType=0 ) )
            for t, format in convertible.keys():
              if format.fileOrDirectory() is Directory:
                i = Directory( value, None )
              else:
                i = File( value, None )
              m = format.match( i )
              if m:
                item = i
                item.name = format.formatedName( item, m )
                format.setFormat( item )
                item.type = self.type
                if not self.ignoreAttributes: item.setFormatAndTypeAttributes()
                if debug:
                  print '!findValues! 2.4', format.name
                break;
        if not item:
          raise Exception( HTMLMessage(_t_( '<em>%s</em> is not a valid file for type <em>%s</em> and format list <em>%s</em>' ) \
            % ( value, _t_( self.type.name ), str( map( lambda x: _t_( x.name ), self.formats ) ) )) )
        return [ item ]
      elif isinstance( value, DiskItem ):
        if debug:
          print '!findValues! 3', value.type, requiredAttributes, value.attributes()
        if ( value.type is None or isSameDiskItemType( value.type, self.type ) ) \
          and value.format in self.formats:
          if debug:
            print '!findValues! 3.1', value
          if AttributesFilter( requiredAttributes ).match( value ):
            if debug:
              print '!findValues! 3.1.1', value
            # If a ReadDiskItem receive a WriteDiskItem, it must find it
            # in hierarchy first in order to have all the attributes if it
            # exists
            if ( not isinstance( self, WriteDiskItem ) ) and \
              getattr( value, '_write', False ) and value.isReadable():
              if debug:
                print '!findValues! 3.1.2'
              readValue = self.findValue( value.fullPath(), requiredAttributes=requiredAttributes )
              if readValue is not None:
                if debug:
                  print '!findValues! 3.1.3'
                return [ readValue ]
            return [ value ]
        
        # Check if value is outside hierarchy
        if value.get( 'outside_hierarchy' ):
          if debug:
            print '!findValues! 3.2'
          flatHierarchiesList, flatHierarchiesDict = _flatHierarchies
          path = value.fullPath()
          h = flatHierarchiesDict.get( path )
          if h is None:
            # Create a new flat hierarchy
            if len( flatHierarchiesList ) >= 10:
              # Remove oldest flat hierarchy
              del flatHierarchiesDict[ flatHierarchiesList[ 0 ] ]
              del flatHierarchiesList[ 0 ]
            h = Directory( os.path.dirname( path ), None )
            h._cacheName = None
            h._defaultPriority = 0
            h._setLocal( 'filename', os.path.basename( value.name ) )
            h.scanner = flatHierarchyContent[0].scanner
            if debug:
              print '!findValues! 3.2.1', h, map( lambda x: ( x.fullPath(), x.type ), h.childs() )
              print '   scanner = ', h.scanner
            flatHierarchiesList.append( path )
            flatHierarchiesDict[ path ] = h
          allHierarchies = [ h ]
          force = 1
        else:
          allHierarchies = hierarchies()
            
            
                    
        # Check if value can be looked for in hierarchy
        attrs = value.attributes().copy()
        if force or value.parent is not None or len( attrs ) > 2:
          result = []
          if debug:
            print '!findValues! 3.3', attrs
          global progressBarFactory, eventsCallback
          if progressBarFactory is not None:
            progressCounts = []
            i = 0
            for count in [len(h.childs()) for h in allHierarchies]:
              i += count
              progressCounts.append( i )
            if progressCounts: progressBar = progressBarFactory( progressCounts[ -1 ] )
            hierarchyProgress = 0
          else:
            progressBar = None
          for h in allHierarchies:
            if eventsCallback is not None:
              eventsCallback()
            result += self.findItems( h, attrs,
                          requiredAttributes = requiredAttributes,
                          volume_dimension = value.get( 'volume_dimension' ),
                          eventsCallback = eventsCallback )
            if progressBar is not None:
              progressBar.setProgress( progressCounts[ hierarchyProgress ] )
              hierarchyProgress += 1
          if debug:
            print '!findValues! 3.4', result
          if result: return result
                
        if self.enableConversion:
          for format in self.formats:
            if getConverter( ( value.type, value.format ), ( self.type, format ) ):
              if debug:
                print '!findValues! 3.5', value
              return [ value ]
  
        return []
      elif type( value ) is types.DictType:
        if debug:
          print '!findValues! 4'
        stupidItem = DiskItem( 'void', None )
        stupidItem.type = self.type
        stupidItem._updateOther( value )
        return self.findValues( stupidItem, force=1, requiredAttributes=requiredAttributes, debug=debug )
      else:
        raise TypeError( HTMLMessage(_t_('Cannot find a <em><code>ReadDiskItem</code></em> value from a <em><code>%s</code></em>') % type(value).__name__) )
  
  
    # This method should be in a global Hierarchies class ... one day.
    def findFromPathInHierarchies( self, text, debug=False ):
      if debug: print '!findFromPathInHierarchies! 1', text
      if not text: return []
      
      # Find the hierarchy DiskItem corresponding to text
      ( notLast, last ) = os.path.split( text )
      current = notLast
      completions = []
      for i in hierarchies():
        completions.append( ( os.path.normpath( i.fullPath() ), i ) )
      item = None
      old = ''
      notFound = 1
      pathList = []
      while old != current:
        if debug: print '!findFromPathInHierarchies! 1.1', completions, current
        for i in completions:
          if debug: print '!findFromPathInHierarchies! 1.2', repr(i[0]), repr(current)
          if i[0] == current:
            notFound = 0
            break
        if not notFound: break
        old = current
        ( current, tail ) = os.path.split( current )
        if tail: pathList.insert( 0, tail )
        
      if notFound:
        if debug: print '!findFromPathInHierarchies! 2'
        return []
      
      # Go down in the hierarchy tree to find text's parent DiskItem
      notFound = False
      item = i[1]
      if debug: print '!findFromPathInHierarchies! 3', item, pathList
      while pathList:
        p = pathList.pop( 0 )
        if isinstance( item, Directory ):
          childFound = False
          for i in item.childs():
            if i.fileName() == p:
              childFound =True
              break
          if not childFound:
            notFound = True
            break
        item = i
  
      if notFound:
        if debug: print '!findFromPathInHierarchies! 3.1', item, [ p ] + pathList
        item = self._createFromPathInHierarchy( item, [ p ] + pathList )
  
      if debug: print '!findFromPathInHierarchies! 4', item
      if not isinstance( item, Directory ): 
        return []
      parent = item
  
      # Look for result in parent's childs
      rAttributes = parent.globalAttributes().copy()
      rAttributes.update( self.requiredAttributes )
      if debug: print '!findFromPathInHierarchies! 5', rAttributes, self.findItems( parent, rAttributes, maxDepth = 0, fileName=last )
      return self.findItems( parent, rAttributes, maxDepth = 0, fileName=last )
  
    def _createFromPathInHierarchy( self, databaseItem, pathList ):
      return None
    
    def toolTipText( self, parameterName, documentation ):
      result = '<center>' + parameterName
      if not self.mandatory: result += ' (' + _t_( 'optional' ) + ')'
      result += '</center><hr><b>' + _t_( 'Type' ) + \
                ':</b> ' + self.type.name + '<br><b>' + _t_( 'Formats' ) + \
                ':</b><blockquote>'
      br = 0
      for f in self.formats:
        if br:
          result += '<br>'
        else:
          br = 1
        result += f.name + ': ' + str(f.getPatterns().patterns[0].pattern)
      result += '</blockquote><b>' + _t_( 'Description' ) + '</b>:<br>' + \
                documentation
      return result
  
  
  #----------------------------------------------------------------------------
  class WriteDiskItem( ReadDiskItem ):
    def __init__( self, diskItemType, formats, requiredAttributes={},
                  exactType=0, ignoreAttributes = 0 ):
      Parameter.__init__( self )
      self.type = getDiskItemType( diskItemType )
      self.formats = getFormats( formats )
      self.enableConversion = 0
      self.requiredAttributes = requiredAttributes.copy()
      self.exactType = exactType
      self._modified = 0
      self.ignoreAttributes = ignoreAttributes;
          
    def typeInfo( self, translator = None ):
      if translator: translate = translator.translate
      else: translate = _
      formats = ''
      for f in self.formats:
        if formats: formats += ', '
        formats += translate( f.name )
      return  ( ( translate( 'Type' ), translate( self.type.name ) ), 
                ( translate( 'Access' ), translate( 'output' ) ), 
                ( translate( 'Formats' ), formats ) )
  
    def checkValue( self, name, value ):
      Parameter.checkValue( self, name, value )
  
    def _createFromPathInHierarchy( self, parentItem, pathList ):
  #    print '!_createFromPathInHierarchy!', parentItem, pathList
      result = None
      if not pathList:
        result = parentItem
      else:
        if parentItem.scanner:
          item = parentItem.scanner.scan( [ Directory( pathList.pop( 0 ), parentItem ) ] )[ 0 ]
          result = self._createFromPathInHierarchy( item, pathList )
  #    print '!_createFromPathInHierarchy! return', result
      return result
  
  
    def findItems( self, directory, attributes, 
                  maxItems = -1,
                  maxDepth = -1,
                  requiredAttributes = {},
                  attributesValues = None,
                  fileNameAttributes = None,
                  volume_dimension = None,
                  fileName = None,
                  debug=False,
                  eventsCallback = None,
                  progressBar = None ):
      if debug: print '!WriteDiskItem.findItems!', directory, attributes, requiredAttributes, maxItems, maxDepth
      result = {}
      if directory.scanner:
        # Find existing items
        if os.path.exists( directory.fullPath() ):
          for tmp in ReadDiskItem.findItems( self, directory, attributes, 
                                        maxItems, 0,
                                        requiredAttributes = requiredAttributes,
                                        attributesValues = attributesValues,
                                        fileNameAttributes = fileNameAttributes,
                                        volume_dimension = volume_dimension,
                                        fileName = fileName,
                                        eventsCallback = eventsCallback,
                                        progressBar = progressBar ):
            result[ tmp.fullPath() ] = tmp
          if maxItems > 0 and len( result ) >= maxItems: return result.values()
  
  
        if debug: print '!WriteDiskItem.findItems 1!'
        attributes = attributes.copy()
        attributes.update( requiredAttributes )
        attributesFilter = AttributesFilter( attributes )
        requiredAttributesFilter = AttributesFilter( requiredAttributes )
        if not attributesFilter.match( directory._globalAttributes ) or \
          not requiredAttributesFilter.match( directory._globalAttributes ):
          if debug: print '!WriteDiskItem.findItems 2!'
          return []
        ok = 0
        if debug:
          print '!WriteDiskItem.findItems 2.1!', directory.scanner.possibleTypes.keys()
        for t in directory.scanner.possibleTypes.keys():
          if t is self.type or ( not self.exactType and 
                                isSameDiskItemType( t, self.type ) ):
            ok = 1
            break
        if not ok: 
          if debug: print '!WriteDiskItem.findItems 2.2!'
          return []
        if debug: print '!WriteDiskItem.findItems 3!'
        if attributesValues is not None:
          for attrName, attrValue in directory.hierarchyAttributes().items():
            values = attributesValues.get( attrName, [] )
            if attrValue not in values:
              values.append( attrValue )
            attributesValues[ attrName ] = values
        virtualChilds = []
        for rule in directory.scanner.rules:
          if debug: print '!WriteDiskItem.findItems 3.0! check rule', rule.pattern, rule.type
          # Add editable attributes even if no item of the appropriate type
          # exists
          if ( self.type is rule.type or ( not self.exactType and 
                                  isSameDiskItemType( rule.type, self.type ) )) \
                or (rule.scanner and rule.scanner.possibleTypes.get( self.type, 
                                                                    0 ) ):
            if attributesValues is not None:
              for (attr,value) in rule.globalAttributes + rule.localAttributes:
                if isinstance( value, AttrValueFunction ):
                  attributesValues.setdefault( attr, [] )
                  if debug:
                    print '!WriteDiskItem.findItems! 3.1', attr, '=', attributesValues[ attr ]
            if fileNameAttributes is not None:
              if debug:
                print '!WriteDiskItem.findItems! 3.2 editable', \
                      rule.pattern, rule.type
              for a in rule.pattern.namedRegex():
                fileNameAttributes[ a ] = 1
                  
          # Check if the rule correspond to a directory which
          # can contain the appropriate type
          if rule.scanner:
            # Check that the rule has a fixed name
            name=None
            if rule.itemName:
              if not isinstance( rule.itemName, AttrValueFunction ):
                name = rule.itemName
            else:
              if debug: print '!WriteDiskItem.findItems 3.3!', rule.pattern, rule.type
              d = { rule.fileNameAttribute: attributes.get( rule.fileNameAttribute, '' ) }
              defaultAttributesValues = getattr( rule, 'defaultAttributesValues', {} )
              defaultAttributesToSet = {}
              if defaultAttributesValues:
                for k, v in  defaultAttributesValues.iteritems():
                  if not attributes.has_key( k ):
                    d[ k ] = v
                    defaultAttributesToSet[ k ] = v
              name = rule.pattern.unmatch( attributes, d )
            if name:
              if debug: print '!WriteDiskItem.findItems 3.4!'
              ok = 0
              for t in rule.scanner.possibleTypes.keys():
                if t is self.type or ( not self.exactType and 
                                      isSameDiskItemType( t, self.type ) ):
                  ok = 1
                  break
              if ok:
                if debug: print '!WriteDiskItem.findItems 3.5!'
                # Build virtual directory
                item = Directory( name, directory )
                item._write = True
                fnv = attributes.get( rule.fileNameAttribute )
                if fnv:
                  item._setLocal( rule.fileNameAttribute, fnv )
                if not os.path.exists( item.fullPath() ):
                  # Set attributes
                  for (attr,value) in rule.globalAttributes:
                    if isinstance( value, AttrValueFunction ):
                      value = value.getValue( item, ( '', '' ) )
                    if not value:
                      value = rule.defaultAttributesValues.get( attr )
                    item._setGlobal(  attr, value )
                  for (attr,value) in rule.localAttributes:
                    if isinstance( value, AttrValueFunction ):
                      value = value.getValue( item, ( '', '' ) )
                    if not value:
                      value = rule.defaultAttributesValues.get( attr )
                    item._setLocal( attr, value )
                  for key in rule.pattern.namedRegex():
                    if not item.has_key( key ):
                      value = attributes.get( key, defaultAttributesValues.get( key ) )
                      if key:
                        item._setLocal( key, value )
                  if not self.ignoreAttributes:
                    item.setFormatAndTypeAttributes( writeOnly = 1 )
                  item.scanner = rule.scanner
                  item.setPriority( rule.priority, priorityOffset=rule.priorityOffset )
                  virtualChilds.append( item )
  
          if rule.type is self.type or ( not self.exactType and 
                                isSameDiskItemType( rule.type, self.type ) ):
            if debug: print '!WriteDiskItem.findItems 4!', rule.pattern, rule.type
            formats = []
            for f in rule.formats:
              if f in self.formats:
                formats.append( f )
            if debug: print '!WriteDiskItem.findItems 4.1!', formats
            for format in formats:
              if rule.pattern.fileType is Directory:
                item = Directory( 'new', directory )
              else:
                item = File( 'new', directory )
              item._write = True
              name=None
              filename_variable = requiredAttributes.get( rule.fileNameAttribute )
              if filename_variable is None:
                filename_variable = attributes.get( rule.fileNameAttribute, '' )
              name_serie = requiredAttributes.get( 'name_serie' )
              if name_serie is None:
                name_serie = attributes.get( 
                  'name_serie', [] )
              if not name_serie and isinstance( format, FormatSeries ):
                # Try to build name_serie according to time dimension
                # of volume_dimension
                try:
                  if debug: print '!WriteDiskItem.findItems 4.2!', name_serie
                  if volume_dimension:
                    name_serie = map( str, range( volume_dimension[ 3 ] ) )
                  else:
                    name_serie = []
                except:
                  name_serie = []
                  showException()
              if debug:
                print '!WriteDiskItem.findItems 5!', rule.fileNameAttribute, \
                      "'" + filename_variable + "'", name_serie
              if name_serie and filename_variable:
                matchDict = { 'filename_variable': filename_variable, 'name_serie':'#' }
                name = rule.pattern.unmatch( item, matchDict, 0 )
                if debug: print '!WriteDiskItem.findItems 5.1!', name
              if not name:
                if filename_variable:
                  name_serie = []
                  matchDict = { 'filename_variable': filename_variable }
                  name = rule.pattern.unmatch( item, matchDict, 0 )
                  if debug: print '!WriteDiskItem.findItems 5.2!', name
                elif name_serie:
                  filename_variable = ''
                  matchDict = { 'name_serie': '#' }
                  name = rule.pattern.unmatch( item, matchDict, 0 )
                  if debug: print '!WriteDiskItem.findItems 5.3!', name
              if not name:
                name_serie = []
                filename_variable = ''
                matchDict = {}
                name = rule.pattern.unmatch( attributes, item )
                if name:
                  for key in rule.pattern.attributes():
                    if not item.has_key( key ):
                      item._setGlobal( key, attributes.get( key, item.get( key ) ) )
                    
                if debug: print '!WriteDiskItem.findItems 5.4! unmatch(',  attributes, ',', item, ') =', name
              if rule.fileNameAttribute:
                if rule.fileNameAttributeIsWeak:
                  item._setLocal( rule.fileNameAttribute, matchDict.get(rule.fileNameAttribute) )
                else:
                  item._setGlobal( rule.fileNameAttribute, matchDict.get(rule.fileNameAttribute) )
              item._setLocal( 'name_serie', name_serie )
              if name:
                item.name = name
                item.format = format
                matchDict[ 'filename_variable' ] = item.name
                item._files = format.unmatch( item, matchDict, 1 )
                rule.type.setType( item, matchDict, 0 )
                fnv = attributes.get( rule.fileNameAttribute, None )
                if fnv:
                  item._setLocal( rule.fileNameAttribute, fnv )
                # Check if item alredy exists in readable values
                if not result.has_key( item.fullPath() ):
                  if rule.itemName:
                    if isinstance( rule.itemName, AttrValueFunction ):
                      item.name = rule.itemName.getValue( item, matchDict )
                    else:
                      item.name = rule.itemName
                  # Set attributes
                  for (attr,value) in rule.globalAttributes:
                    if isinstance( value, AttrValueFunction ):
                      item._setGlobal( attr, value.getValue( item, matchDict ) )
                    else:
                      item._setGlobal(  attr, value )
                  for (attr,value) in rule.localAttributes:
                    if isinstance( value, AttrValueFunction ):
                      item._setLocal( attr, value.getValue( item, matchDict ) )
                    else:
                      item._setLocal( attr, value )
                  item.format.postProcessing( item )
                  if debug: print '!WriteDiskItem.findItems 6!', item
  
                  # Set priority
                  item.setPriority( rule.priority,
                                    priorityOffset=rule.priorityOffset )
  
                  # Expand name with name_serie
                  if name_serie:
                    item.name = expand_name_serie( item.name, name_serie[ 0 ] )
                    item._setLocal( 'name_serie', name_serie )
  
                  # Add fileNameAttribute value to attributesValues
                  if attributesValues is not None:
                    if not self.ignoreAttributes: item.setFormatAndTypeAttributes( writeOnly = 1 )
                    values = attributesValues.get( rule.fileNameAttribute, [] )
                    attrValue = item.get( rule.fileNameAttribute )
                    if attrValue not in values:
                      values.append( attrValue )
                    attributesValues[ rule.fileNameAttribute ] = values
                  # Filter attributes
                  if debug: print '!WriteDiskItem.findItems 7!', item, attributesFilter.attributes, item.attributes()
                  if attributesFilter.match( item.globalAttributes() ) and \
                    requiredAttributesFilter.matchStrict( item ):
                    if debug: print '!WriteDiskItem.findItems 8!', item
                    result[ item.fullPath() ] = item
                    if attributesValues is not None:
                      for attrName, attrValue in item.attributes().items():
                        values = attributesValues.get( attrName, [] )
                        if attrValue not in values:
                          values.append( attrValue )
                        attributesValues[ attrName ] = values
                    if maxItems > 0 and len( result ) >= maxItems: break
          if maxItems > 0 and len( result ) >= maxItems: break
        ignoreProgressSteps = len( virtualChilds )
        if os.path.exists( directory.fullPath() ):
          virtualChilds += directory.childs()
        for item in virtualChilds:
          if maxDepth and isinstance( item, Directory ):
            for tmp in self.findItems( item, attributes, 
                                      maxItems-len(result), maxDepth-1,
                                      requiredAttributes = requiredAttributes,
                                      attributesValues = attributesValues,
                                      fileNameAttributes = fileNameAttributes,
                                      volume_dimension = volume_dimension,
                                      fileName = fileName,
                                      debug = debug,
                                      eventsCallback=eventsCallback ):
              result[ tmp.fullPath() ] = tmp
            if maxItems > 0 and len( result ) >= maxItems: break
          if progressBar is not None:
            if ignoreProgressSteps:
              ignoreProgressSteps -= 1
            else:
              progressBar.step()
      if debug: print '!WriteDiskItem.findItems! result = ', result
      return result.values()
  
  
  
  #----------------------------------------------------------------------------
  class ReadHierarchyDirectory( ReadDiskItem ):
    def __init__( self, hdType, **kwargs ):
      ReadDiskItem.__init__( self, hdType, directoryFormat, **kwargs )
  
  
  #----------------------------------------------------------------------------
  class WriteHierarchyDirectory( OpenChoice ):
    def __init__( self, hdType, **kwargs ):
      OpenChoice.__init__( self, ('',None), )
      self._writeDiskItem = WriteDiskItem( hdType, directoryFormat, **kwargs )
      self._linkedDirectory = None
      self.linkParameterWithNonDefaultValue = 1
      
    def findValue( self, value, debug = 0 ):
      if not value: return None
      if debug:
        print '!WriteHierarchyDirectory.findValue! 1', value, isinstance( value, DiskItem )
      try:
        result = Choice.findValue( self, value )
      except KeyError:
        if self._linkedDirectory is None or isinstance( value, DiskItem ):
          result = self._writeDiskItem.findValue( value )
        else:
          result = self._writeDiskItem.findValue( os.path.join( \
            self._linkedDirectory, str( value ) ) )
      if debug:
        print '!WriteHierarchyDirectory.findValue! 2', result, isinstance( result, DiskItem )
        if result is not None:
          for name, value in result.attributes().items():
            print ' ', name, '=', value
      return result
    
    def valueLinked( self, name, value, debug=0 ):
      if debug:
        print '!WriteHierarchyDirectory.valueLinked! 1', name, value, type( value )
      if isinstance( value, DiskItem ):
        attributes = value.attributes().copy()
  
        values = self._writeDiskItem.findValues( attributes )
        if len( values ) > 1:
          # Find the item with the "smallest" "distance" from item
          values = map( lambda item, value=value: ( value.distance( item ), item ),
                        values )
          values.sort()
          if debug:
            print '!WriteHierarchyDirectory.valueLinked! 2 priorities'
            for l in values:
              print ' ', l
          firstKey = values[ 0 ][ 0 ]
          items = []
          for i in values:
            if i[ 0 ] != firstKey: break
            items.append( i[ 1 ] )
        else:
          items = values
    
        if debug:
          print '!WriteHierarchyDirectory.valueLinked! 3', items
  
        self._linkedDirectory = None
        choices = []
        for item in items:
          d, n = os.path.split( item.fullPath() )
          if self._linkedDirectory is None:
            self._linkedDirectory = d
          else:
            if d != self._linkedDirectory:
              self._linkedDirectory = None
              choices = []
              break
          if n != '*':
            choices.append( ( n, item ) )
        if debug:
          print '!WriteHierarchyDirectory.valueLinked! 4 choices', choices
        self.setChoices( *choices )
  
      
      
  
  #----------------------------------------------------------------------------
  def hierarchies():
    return _hierarchies
  
  
  #----------------------------------------------------------------------------
  def readHierarchy( directory, clearCache=False, defaultPriority = None ):
    debug = neuroConfig.debugHierarchyScanning
    if not os.path.isdir( directory ):
      raise ValueError( HTMLMessage(_t_('<em>%s</em> is not a valid directory') % str( directory )) )
    ontology = 'brainvisa-3.0'
    
    minf = os.path.join( directory, 'database_settings.minf' )
    if os.path.exists( minf ):
      settings = readMinf( minf )[ 0 ]
      ontology = settings.get( 'ontology', ontology )
    
    fso = FileSystemOntology.get( ontology )
    cacheName = os.path.join( directory, fso.cacheName )
    cacheTime = 0
    readCache = False
    logContent = '<h1>' + directory + '</h1><em>File system ontology: </em>' + fso.name + '<p><em>database file name: </em>' + cacheName + '<p>'
    if debug:
      print >> debug, '=' * 80
      print >> debug, 'read database', directory
      print >> debug, '=' * 80
      print >> debug, '   FSO name:', fso.name
      print >> debug, '   FSO source:', fso.source
      print >> debug, '   cache name:', cacheName
    
    #print '!readHierarchy! guiLoaded =', neuroConfig.guiLoaded
    #showException( exceptionInfo=( 'more info', 'error message', None ) )
    
    if os.path.exists( cacheName ):
      if clearCache:
        try:
          # Erase cache file content
          logContent += '<em>cache cleared</em>'
          f = open( cacheName, 'wb' )
          f.close()
          if debug: print >> debug, 'cache cleared'
        except:
          showException( beforeError=_t_('cannot clear cache file <em>%s</em>') % cacheName )
      else:
        cacheTime = os.stat( cacheName ).st_mtime
      pTime = os.stat( directory ).st_mtime
      hTime = fso.lastModification
      if hTime <= cacheTime:
        readCache = 1
      logContent += '<em>database directory time: </em>' + str(pTime) + ' (' + time.ctime(pTime) + ')' + '<p>'
      logContent += '<em>FSO time: </em>' + str(hTime) + ' (' + time.ctime(hTime) + ')' + '<p>'
      logContent += '<em>cache time: </em>' + str(cacheTime) + ' (' + time.ctime(cacheTime) + ')' + '<p>'
      if debug:
        print >> debug, '   database directory time:', time.ctime(pTime)
        print >> debug, '   FSO time:', time.ctime(hTime)
        print >> debug, '   cache time:', time.ctime(cacheTime)
    if readCache:
      if debug: print >> debug, '-> reading cache'
      f = open( cacheName, 'rb' )
      try:
        try:
          h = cPickle.load( f )
          h._cacheName = cacheName
          h._defaultPriority = defaultPriority
          _hierarchies.append( h )
        except EOFError:
          readCache = 0
          # If cache file exists but is empty, it is not an error.
          if f.tell() != 0:
            raise
          if debug: print >> debug, '-> cache file is empty'
          logContent += '<font color="orange">Database file is empty</font><p>'
        except:
          if debug: print >> debug, '-> error in database file'
          readCache = 0
          showException( beforeError=_t_('While reading database file "%s"') % (cacheName,) )
      finally:
        f.close()
    else:
      if debug: print >> debug, '-> cache ignored'  
    logContent += '<em>read cache: </em>' + ('no','yes')[readCache] + '<p>'
    neuroLog.log( 'Read hierarchy', html=logContent, icon='icon_log.png' )
    if not readCache:
      h = Directory( directory, None )
      h._cacheName = cacheName
      h._defaultPriority = defaultPriority
      _hierarchies.append( h )
      h._localAttributes[ 'ontology' ] = fso.name
      content = fso.content
      if type( content ) is not types.TupleType: content = ( content, )
      apply( SetContent, ( os.path.basename( h.name ), ) \
            + content ).scanner.scan( [ h ] )
    
  
  #----------------------------------------------------------------------------
  def readHierarchies( clearCache = False ):
    # Read flat hierarchy
    global flatHierarchyContent
    try:
      fso = FileSystemOntology.get( neuroConfig.flatHierarchy )
      flatHierarchyContent = fso.content
      if type( flatHierarchyContent ) is not types.TupleType:
        flatHierarchyContent = ( flatHierarchyContent, )
    except:
      showException()
    
    # Read other hierarchies
    global _hierarchies, _flatHierarchies
    _hierarchies = []
    _flatHierarchies = ( [], {} )
    beforeError=''
    defaultPriority = len( neuroConfig.dataPath )
    for dbSettings in neuroConfig.dataPath:
      defaultPriority -= 1
      try:
        if not isinstance( dbSettings.directory, basestring ):
          raise ValueError( HTMLMessage(_t_('Bad value in dataPath: "%s"') % unicode(p)))
        readHierarchy( dbSettings.directory, clearCache=clearCache, \
                        defaultPriority = defaultPriority )
      except:
        showException( beforeError=beforeError )
  
      
  
  #-------------------------------------------------------------------------------
  def ontologies():
    default = 'brainvisa-3.0'
    return [ default ] + [i for i in os.listdir( os.path.join( neuroConfig.mainPath, 'hierarchies' ) ) if i != default]
    
  
  
  #-------------------------------------------------------------------------------
  def _fullScan( l ):
    for item in l:
      c = item.childs()
      if c: _fullScan( c )
  
  
  #-------------------------------------------------------------------------------
  def cacheUpdate( hierarchyList=None ):
    if hierarchyList is None:
      hierarchyList = hierarchies()
    _fullScan( hierarchyList )  
    for h in hierarchyList:
      f = None
      try:
        f = open( h._cacheName, 'wb' )
        if f:
          try:
            cPickle.dump( h, f, 1 )
          finally:
            f.close()
            
      except: showException( beforeError=_t_('in cache file "%s"') % h._cacheName )
  
  
  #----------------------------------------------------------------------------
  def hierarchyAttributesValues( hierarchyList=None ):
    result = {}
    if hierarchyList is None:
      hierarchyList = hierarchies()
    for h in hierarchyList:
      h.scanner.attributesValues( result )
    return result
  
  
  #----------------------------------------------------------------------------
  def initializeHierarchy():
    # Here, I have got a problem. neuroProcesses.py needs neuroHierarchy.py
    # but neuroHierarchy.py needs some functions of neuroProcesses.py. The
    # only solution I sought of is the following two lines.
    global getConverter, getConvertersTo
    from neuroProcesses import getConverter, getConvertersTo
  
