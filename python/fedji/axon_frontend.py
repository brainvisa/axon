# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
import os
import os.path as osp
from stat import S_ISDIR
import shutil
from itertools import chain

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
                                           getAllFormats,
                                           getAllDiskItemTypes,
                                           File,
                                           Directory)
import six


class AxonFedjiDatabase(Database):

    def __init__(self, directory, fedji_url=None, fom_name=None):
        super(AxonFedjiDatabase, self).__init__()
        # Connect to FEDJI on database "axon" and collection "disk_items"
        if fedji_url is None:
            fedji_url = 'sqlite://' + osp.join(directory, 'fedji')
        self.fedji_url = fedji_url
        self._fedji_collection = None

        self.name = directory
        self.directory = osp.normpath(directory)
        if not osp.exists(self.directory):
            raise ValueError(
                HTMLMessage(_t_('<em>%s</em> is not a valid directory') % str(self.directory)))
        minf = osp.join(self.directory, 'database_settings.minf')
        if fom_name is None:
            if osp.exists(minf):
                fom_name = readMinf(minf)[0].get(
                    'ontology', 'brainvisa-3.2.0')
            else:
                fom_name = 'brainvisa-3.2.0'
        fomm = FileOrganizationModelManager()
        self.fom = fomm.load_foms(fom_name)
        self._pta = None
        self._atp = None
        self._typeKeysAttributes = {}

    @property
    def fedji_collection(self):
        if self._fedji_collection is None:
            self._fedji_collection = fedji_connect(
                self.fedji_url).axon.disk_items
            if '_files' not in self.fedji_collection.fields:
                self.fedji_collection.new_field('_files', list)
                self.fedji_collection.create_index('_files')
        return self._fedji_collection

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
            self._atp = AttributesToPaths(self.fom)
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

    def insertDiskItems(self, diskItems, update=False):
        for d in diskItems:
            if d.type is None:
                raise ValueError(
                    'Cannot insert an item without type in a database: %s' % (six.text_type(d), ))

            d._globalAttributes["_database"] = self.name

            if update:
                raise NotImplementedError(
                    'DiskItem update is not yet implemented')
            else:
                documents = d.globalAttributes()
                documents.pop('uuid', None)
                documents['_id'] = str(d.uuid())
                documents['_type'] = [d.type.name] + [
                    i.name for i in d.type.parents()]
                documents['_format'] = d.format.name
                documents['_files'] = d._files
                print('!fedji insert!', documents)
                self.fedji_collection.insert(documents)

    def removeDiskItems(self, diskItems, eraseFiles=False):
        for d in diskItems:
            uuid = str(d.uuid(saveMinf=False))
            self.fedji_collection.remove({'_id': uuid})
            if eraseFiles:
                for path in diskItems.fullPaths():
                    shutil.rmtree(path)

    def _createDiskitemFromDocument(self, doc):
        diskitem = DiskItem("Document " + doc['_id'], None)
        diskitem.type = getDiskItemType(doc.pop('_type')[0])
        diskitem.format = getFormat(doc.pop('_format'))
        diskitem._globalAttributes["_database"] = self.name
        diskitem._globalAttributes['_ontology'] = self.fom.fom_names[0]
        diskitem._changeUuid(doc.pop('_id'))
        diskitem._files = doc.pop('_files')
        diskitem._updateGlobal(doc)
        return diskitem

    def getDiskItemFromUuid(self, uuid, defaultValue=Undefined):
        documents = list(self.fedji_collection.find({'_id': uuid}))
        if documents:
            return self._createDiskitemFromDocument(documents[0])
        elif defaultValue is Undefined:
            raise ValueError('Database "%(database)s" contains no DiskItem with uuid %(uuid)s' %
                             {'database': self.name,  'uuid': str(uuid)})
        return defaultValue

    def getDiskItemFromFileName(self, fileName, defaultValue=Undefined):
        if fileName.startswith(self.directory):
            documents = list(self.fedji_collection.find({'_files': fileName}))
            if documents:
                return self._createDiskitemFromDocument(documents[0])
        if defaultValue is Undefined:
            raise ValueError('Database "%(database)s" does not reference file "%(filename)s"' %
                             {'database': self.name,  'filename': fileName})
        return defaultValue

    def _createDiskItemFromPathAttributes(self, path, attributes):
        diskItem = self.createDiskItemFromFormatExtension(path, None)
        if diskItem:
            format = attributes.pop('fom_format', None)
            type = attributes.pop('fom_parameter', None)
            attributes.pop('fom_process', None)
            attributes.pop('fom_name', None)
            if format is not None and format is not diskItem.format:
                newItem = self.changeDiskItemFormat(diskItem, format)
                if newItem is not None:
                    diskItem = newItem
            if type:
                diskItem.type = getDiskItemType(type)
            diskItem._updateGlobal(attributes)
        return diskItem

    def createDiskItemFromFileName(self, fileName, defaultValue=Undefined):
        print('!createDiskItemFromFileName!', fileName)
        diskItem = None
        if fileName.startswith(self.directory):
            print('!createDiskItemFromFileName! 2')
            relative_path = fileName[len(self.directory) + 1:]
            for path, st, attributes in self.path_to_attributes.parse_path(relative_path):
                if attributes:
                    diskItem = self._createDiskItemFromPathAttributes(
                        fileName, attributes)
                    break
            else:
                # diskItem = self._createDiskItemFromPathAttributes(fileName,
                # {})
                diskItem = File(fileName, None)
                diskItem.type = None
                diskItem.format = None
                diskItem.files = [fileName]
                print('!createDiskItemFromFileName! 3', diskItem)
        if diskItem is not None:
            print('!createDiskItemFromFileName! -->', diskItem)
            return diskItem
        elif defaultValue is Undefined:
            raise ValueError('Database "%(database)s" cannot create DiskItem for %(filename)s"' %
                             {'database': self.name,  'filename': fileName})
        return defaultValue

    def changeDiskItemFormat(self, diskItem, newFormat):
        newFormat = self.formats.getFormat(newFormat)
        if newFormat is not None:
            noExt = diskItem.fullName()
            result = diskItem.clone()
            result.format = getFormat(newFormat.name)
            result._files = [osp.normpath(noExt + '.' + i if i else noExt)
                             for i in newFormat.extensions()]
            return result
        return None

    def scanDatabaseDirectories(self, directoriesToScan, includeUnknowns=True, recursion=False):
        print('!scanDatabaseDirectories!', directoriesToScan)
        if not includeUnknowns:
            raise NotImplementedError(
                'On FEDJI databases, scanDatabaseDirectories cannot be called with includeUnknowns=False')
        if recursion:
            raise NotImplementedError(
                'On FEDJI databases, scanDatabaseDirectories cannot be called with recursion=True')
        for directory in directoriesToScan:
            content = set()
            minf = set()
            for i in os.listdir(directory):
                fp = osp.join(directory, i)
                if fp.endswith('.minf'):
                    minf.add(fp)
                else:
                    content.add(fp)
            unknown = {}
            while content:
                path = content.pop()
                try:
                    item = self.getDiskItemFromFileName(path)
                    print('!scanDatabaseDirectories! 1', item)
                except ValueError:
                    item = self.createDiskItemFromFileName(path)
                    item._globalAttributes["_database"] = self.name
                    item._globalAttributes[
                        '_ontology'] = self.fom.fom_names[0]
                    print('!scanDatabaseDirectories! 2', item)
                if item.type:
                    for path in item.fullPaths():
                        content.discard(path)
                        unknown.pop(path, None)
                    minf.discard(item.minfFileName())
                    print(
                        '!scanDatabaseDirectories! 3 -->', item, item.type, item.format)
                    yield item
                else:
                    unknown[path] = item
                if not content and minf:
                    content = minf
                    minf = set()
            for path, item in six.iteritems(unknown):
                if S_ISDIR(os.stat(path).st_mode):
                    item.type = getDiskItemType('Directory')
                print('!scanDatabaseDirectories! 4 -->',
                      item, item.type, item.format)
                yield item

    def clear(self, context=None):
        db = self.fedji_collection.fedji_sqlite_db
        self._fedji_collection = None
        db.drop()

    def update(self, directoriesToScan=None, depth=0, context=None):
        if directoriesToScan is None:
            directoriesToScan = [self.directory]
        stack = [(d, 0) for d in directoriesToScan]
        while stack:
            directory, dir_depth = stack.pop(0)
            if depth and dir_depth > depth:
                continue
            content = set()
            minf = set()
            for i in os.listdir(directory):
                fp = osp.join(directory, i)
                if S_ISDIR(os.stat(fp).st_mode):
                    stack.append((fp, dir_depth + 1))
                if fp.endswith('.minf'):
                    minf.add(fp)
                else:
                    content.add(fp)

            while content:
                path = content.pop()
                try:
                    item = self.getDiskItemFromFileName(path)
                    print('!update! ignore already stored', item)
                except ValueError:
                    item = self.createDiskItemFromFileName(path)
                    if item.type:
                        item._globalAttributes["_database"] = self.name
                        item._globalAttributes[
                            '_ontology'] = self.fom.fom_names[0]
                        # if item.type is None and S_ISDIR(os.stat(path).st_mode):
                            # item.type = getDiskItemType('Directory')
                        self.insertDiskItems((item,))
                        print('!update! store', item)
                if item:
                    for path in item.fullPaths():
                        content.discard(path)
                    minf.discard(item.minfFileName())

                if not content and minf:
                    content = minf
                    minf = set()

    @staticmethod
    def _get_query(selection, required):
        query = {}
        for k, v in chain(six.iteritems(selection),
                          six.iteritems(required)):
            if k == '_uuid':
                k = '_id'
            if isinstance(v, six.string_types):
                query[k] = v
            elif not v:
                continue
            elif isinstance(v, list):
                query[k] = {'$in': v}
            else:
                query[k] = {'$in': list(v)}
        return query

    def findAttributes(self, attributes, selection={}, _debug=None, exactType=False, **required):
        # print('!findAttributes! 1', attributes, selection, required,
        # exactType)
        query = self._get_query(selection, required)
        # print('!findAttributes! 2 query=', query)

        try:
            type_index = attributes.index('_type')
        except ValueError:
            type_index = -1

        fields = list(attributes)
        try:
            i = attributes.index('_uuid')
            fields[i] = '_id'
        except Exception:
            pass

        for document in self.fedji_collection.find(query, fields=fields):
            values = [document.get(f) for f in fields]
            if type_index >= 0 and values[type_index]:
                values[type_index] = values[type_index][0]
            # print('!findAttributes! 3 -->', values)
            yield values

    def findDiskItems(self, selection={}, _debug=None, exactType=False, **required):
        # print('!findDiskItems! 1', selection, required, exactType)
        query = self._get_query(selection, required)
        # print('!findDiskItems! 2 query=', query)
        for document in self.fedji_collection.find(query):
            item = self._createDiskitemFromDocument(document)
            # print('!findDiskItems! -->', item)
            yield item

    def createDiskItems(self, selection={}, _debug=None, exactType=False, **required):
        if _debug:
            print('!createDiskItems! 1', selection, exactType, required,
                  file=_debug)
        query = {}
        for k, v in chain(six.iteritems(selection),
                          six.iteritems(required)):
            if k == '_format':
                k = 'fom_format'
            if k == '_type':
                k = 'fom_parameter'
            if isinstance(v, six.string_types):
                query[k] = v
            elif not v:
                continue
            elif isinstance(v, list):
                query[k] = v
            else:
                query[k] = list(v)
        # print('!createDiskItems! query=', query)
        if _debug:
            class debug(object):

                @staticmethod
                def debug(*args):
                    print(' '.join(str(i) for i in args), file=_debug)
        else:
            debug = None
        for path, attributes in self.attributes_to_paths.find_paths(query, debug=debug):
            # print('!createDiskItems! 3', path, attributes)
            item = self._createDiskItemFromPathAttributes(path, attributes)
            # print('!createDiskItems! 4 -->', item)
            if item:
                if _debug:
                    print('-->', item, file=_debug)
                yield item

    def getTypesKeysAttributes(self, type):
        result = self._typeKeysAttributes.get(type)
        if result is None:
            result = list(
                self.attributes_to_paths.find_discriminant_attributes(fom_parameter=type))
            self._typeKeysAttributes[type] = result
        return result

    def getAttributesEdition(self, *types):
        editable = set()
        attribute_values = {}
        for t in self.getTypeChildren(*types):
            attributes = self.attributes_to_paths.find_discriminant_attributes(
                fom_parameter=t)
            for attribute in attributes:
                definition = self.fom.attribute_definitions.get(attribute, {})
                values = set(definition.get('values', ()))
                values.update(str(i.popitem()[1])
                              for i in self.fedji_collection.find({}, fields=[attribute]) if i)
                attribute_values[attribute] = values
                if definition.get('fom_open_value', False):
                    editable.add(attribute)
        return editable, attribute_values, ()

    def getTypeChildren(self, *types):
        if getattr(self, '_childrenByTypeName', None) is None:
            self._childrenByTypeName = {}
            for type in getAllDiskItemTypes():
                self._childrenByTypeName.setdefault('Any', set()).add(type)
                self._childrenByTypeName.setdefault(type.name, set())
                parent = type.parent
                while parent is not None:
                    self._childrenByTypeName.setdefault(
                        type.parent.name, set()).add(type.name)
                    parent = parent.parent
        result = set(types)
        for type in types:
            try:
                result.update(self._childrenByTypeName[type])
            except KeyError:
                pass
                # import pprint
                # pprint.pprint(self._childrenByTypeName)
        return result

    def getTypesFormats(self, *types):
        if getattr(self, '_formatsByTypeName', None) is None:
            self._formatsByTypeName = {}
            for type in getAllDiskItemTypes():
                # TODO: There should be a method in AttributesToPaths to avoid
                # direct access to _db.
                self._formatsByTypeName[type.name] = list(self.attributes_to_paths._db.execute(
                    'SELECT DISTINCT _fom_format FROM rules WHERE _fom_parameter="%s"' % type.name))
        result = set()
        for type in types:
            result.update(self._formatsByTypeName[type])
        return result

    def findTransformationPaths(self, source_referential, destination_referential, maxLength, bidirectional):
        # TODO
        if False:
            yield None
