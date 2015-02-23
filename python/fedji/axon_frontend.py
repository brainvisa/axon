# -*- coding: utf-8 -*-
import os
import os.path as osp
from stat import S_ISDIR
import shutil

from soma.uuid import Uuid
from soma.undefined import Undefined
from soma.fom import (FileOrganizationModelManager,
                      DirectoryAsDict,
                      PathToAttributes,
                      AttributesToPaths)
from soma.minf.api import readMinf
from fedji.api import fedji_connect
from brainvisa.data.sqlFSODatabase import Database
from brainvisa.data.neuroHierarchy import databases
from brainvisa.processes import getDiskItemType
from brainvisa.data.neuroDiskItems import (DiskItem, 
                                           getFormat,
                                           getFormats,
                                           Format,
                                           getAllFormats)

class AxonFedjiDatabase(Database):
    def __init__( self, directory, fedji_url=None, fom_name=None):
        super(AxonFedjiDatabase, self).__init__()
        # Connect to FEDJI on database "axon" and collection "disk_items"
        if fedji_url is None:
            fedji_url = 'sqlite:' + osp.join(directory, 'fedji')
        self.fedji_collection = fedji_connect(fedji_url).axon.disk_items
        if 'files' not in self.fedji_collection.fields:
            self.fedji_collection.new_field('files', list)
            self.fedji_collection.create_index('files')
        
        self.name = directory
        self.directory = osp.normpath( directory )
        if not osp.exists( self.directory ):
            raise ValueError( HTMLMessage(_t_('<em>%s</em> is not a valid directory') % str( self.directory )) )
        minf = osp.join(self.directory, 'database_settings.minf')
        if fom_name is None:
            if osp.exists(minf):
                fom_name = readMinf(minf)[ 0 ].get('ontology', 'brainvisa-3.1')
            else:
                fom_name = 'brainvisa-3.2'
        fomm = FileOrganizationModelManager()
        self.fom = fomm.load_foms(fom_name)
        self._pta = None
        self._atp = None
    
    def close(self):
        self.fedji_collection = None
        self.fom = None
        self._pta = None
        self._atp = None
    
    @property
    def path_to_attributes(self):
        if self._pta is None:
            self._pta = PathToAttributes(self.fom)
        return self._pta
    
    @property
    def attributes_to_paths(self):
        if self._atp is None:
            self._atp = AttributesToPath(self.fom)
        return self._atp
    
    def add_to_axon(self):
        try:
            old_db = databases.database(self.directory)
        except KeyError:
            pass
        else:
            databases.remove(old_db.name)
            old_db.close()
        databases.add(self)
        return self

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
                raise ValueError( 'Cannot insert an item without type in a database: %s' % ( unicode( d ), ) )

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
                for path in diskItems.fullPaths():
                    shutil.rmtree(path)

    def _createDiskitemFromDocument(self, doc):
        diskitem = DiskItem("Document " + doc['_id'], None)
        diskitem.type = getDiskItemType(doc.pop('type')[0])
        diskitem.format = getFormat(doc.pop('format'))
        diskitem._globalAttributes["_database"] = self.name
        diskItem._globalAttributes[ '_ontology' ] = self.fom.fom_names[0]
        diskitem._changeUuid( doc.pop('_id') )
        diskitem._files = doc.pop['files']
        diskitem._updateGlobal(doc)
        return diskitem
    
    def getDiskItemFromUuid( self, uuid, defaultValue=Undefined ):
        documents = list(self.fedji_collection.find({'_id':uuid}))
        if documents:
            return self._createDiskitemFromDocument(documents[0])
        elif defaultValue is Undefined:
            raise ValueError('Database "%(database)s" contains no DiskItem with uuid %(uuid)s' % { 'database': self.name,  'uuid': str(uuid) } )
        return defaultValue
  
    def getDiskItemFromFileName( self, fileName, defaultValue=Undefined ):
        if fileName.startswith(self.directory):
            documents = list(self.fedji_collection.find({'files':fileName}))
            if documents:
                return self._createDiskitemFromDocument(documents[0])
        if defaultValue is Undefined:
            raise ValueError('Database "%(database)s" does not reference file "%(filename)s"' % { 'database': self.name,  'filename': fileName } )
        return defaultValue
    
    
    def createDiskItemFromFileName( self, fileName, defaultValue=Undefined ):
        if fileName.startswith(self.directory):
            diskItem = self.createDiskItemFromFormatExtension( fileName, None )
            if diskItem is not None:
                relative_path = diskItem.fullPath()[len(self.directory)+1:]
                dad = DirectoryAsDict.paths_to_dict(relative_path)
                import sys
                class log:
                    @staticmethod
                    def debug(msg):
                        print msg
                        sys.stdout.flush()
                log.debug('createDiskItemFromFileName ' + fileName)
                for path, st, attributes in self.path_to_attributes.parse_directory(dad, log=log):
                    if osp.join(*path) == relative_path:
                        if attributes:
                            format = attributes.pop('fom_format', None)
                            type = attributes.pop('fom_parameter',None)
                            attributes.pop('fom_process',None)
                            attributes.pop('fom_name',None)
                            if format is not None:
                                newItem = self.changeDiskItemFormat(diskItem, format)
                            if newItem is not None:
                                diskItem = newItem
                            diskItem.type = getDiskItemType(type)
                            diskItem._updateGlobal(attributes)
                        log.debug('==> ' + fileName)
                        sys.stderr.flush()
                sys.stderr.flush()
                return diskItem
            elif defaultValue is Undefined:
                raise ValueError( 'Database "%(database)s" cannot create DiskItem for %(filename)s"' % { 'database': self.name,  'filename': fileName } )
        if defaultValue is Undefined:
            raise ValueError( 'Database "%(database)s" cannot reference file "%(filename)s"' % { 'database': self.name,  'filename': fileName } )
        return defaultValue
      
    def changeDiskItemFormat( self, diskItem, newFormat ):
        newFormat = self.formats.getFormat(newFormat)
        if newFormat is not None:
            noExt = diskItem.fullName()
            result = diskItem.clone()
            result.format = getFormat(newFormat.name)
            result._files = [ osp.normpath( noExt + '.' + i if i else noExt ) for i in newFormat.extensions() ]
            return result
        return None
    
    
    def scanDatabaseDirectories( self, directoriesToScan, includeUnknowns=True, recursion=False ):
        if not includeUnknowns:
            raise NotImplementedError('On FEDJI databases, scanDatabaseDirectories cannot be called with includeUnknowns=False')
        if recursion:
            raise NotImplementedError('On FEDJI databases, scanDatabaseDirectories cannot be called with recursion=True')
        for directory in directoriesToScan:
            content = set(osp.join(directory,i) for i in os.listdir(directory))
            while content:
                path = content.pop()
                try:
                    item = self.getDiskItemFromFileName(path)
                except ValueError:
                    item = self.createDiskItemFromFileName(path)
                    item._globalAttributes["_database"] = self.name
                    item._globalAttributes[ '_ontology' ] = self.fom.fom_names[0]
                    if item.type is None and S_ISDIR(os.stat(path).st_mode):
                        item.type = getDiskItemType('Directory')
                for path in item.fullPaths():
                    content.discard(path)
                content.discard(item.minfFileName())
                yield item
    
    def findAttributes( self, attributes, selection={}, _debug=None, exactType=False, **required ):
        query = selection.copy()
        query.update(required)
        for attribute in attributes:
            yield [i[attribute] for i in self.fedji_collection.find(query,fields=[attribute])]
    
    
    def findDiskItems( self, selection={}, _debug=None, exactType=False, **required ):
        query = selection.copy()
        query.update(required)
        for document in self.fedji_collection.find(query):
            yield self._createDiskitemFromDocument(documents)
    
    
    def createDiskItems( self, selection={}, _debug=None, exactType=False, **required ):
        NotImplementedError('createDiskItems not implemented for FEDJI databases')
    
    def getAttributesEdition( self, *types ):
      editable = set()
      values = {}
      # TODO
      #for t1 in types:
        #for t2 in self._childrenByTypeName[ t1 ]:
          #e = self._attributesEditionByType.get( t2 )
          #if e is not None:
            #editable.update( e[0] )
            #for a, v in e[1].iteritems():
              #values.setdefault( a, set() ).update( v )
      return editable, values
    
    
    def getTypeChildren( self, *types ):
        return self.fso.getTypeChildren(types)
        
    
    def getTypesFormats( self, *types ):
        return self.fso.getTypesFormats(types)
      


