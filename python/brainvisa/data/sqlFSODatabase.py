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
"""
This module contains classes defining Brainvisa **databases**.

The main classes are :py:class:`SQLDatabases` and :py:class:`SQLDatabase`.

"""
from __future__ import print_function
import sys
import os
import re

import time
from itertools import chain
from six.moves import StringIO
from six.moves import cPickle

from soma.minf.api import readMinf, writeMinf
from soma.html import htmlEscape
from soma.sorted_dictionary import SortedDictionary
from soma.undefined import Undefined
from soma.translation import translate as _
from soma.path import split_path, relative_path, parse_query_string,\
                      remove_query_string, split_query_string
from soma.somatime import timeDifferenceToString
from soma.uuid import Uuid
from soma.sqlite_tools import sqlite3, ThreadSafeSQLiteConnection

from brainvisa.data.fileSystemOntology import FileSystemOntology, SetContent
import brainvisa.processes
from brainvisa.configuration import neuroConfig
from brainvisa.data import neuroDiskItems
from brainvisa.processing.neuroException import showWarning, HTMLMessage, showException
from brainvisa.data.neuroDiskItems import DiskItem, getFormat, getFormats, Format, FormatSeries, File, Directory, getAllFormats, MinfFormat, getDiskItemType
from brainvisa.data.patterns import DictPattern
from brainvisa.data.sql import mangleSQL, unmangleSQL
from brainvisa.data.fileformats import FileFormats
from brainvisa.data.directory_iterator import DirectoryIterator, VirtualDirectoryIterator
from brainvisa.data import temporary
import six
from six.moves import reduce

if sys.version_info[0] >= 3:
    izip = zip

    def values(thing):
        return list(thing.values())
    xrange = range
    basestring = str
    unicode = str
else:
    from itertools import izip

    def values(thing):
        return thing.values()

out = sys.stdout

databaseVersion = '2.3'
# mapping between databases versions and axon versions : database version
# -> first axon version where this database version is used
databaseVersions = {'1.0': '3.1.0',
                    '1.1': '3.2.0',
                    '2.0': '4.0.0',
                    '2.1': '4.2.0',
                    '2.2': '4.5.0',
                    '2.3': '4.6.0'}

#------------------------------------------------------------------------------


class CombineGet(object):

    def __init__(self, *args):
        self.__objects = args

    def get(self, key, default=None):
        for o in self.__objects:
            v = o.get(key, Undefined)
            if v is not Undefined:
                return v
        return default

    def __getitem__(self, key):
        for o in self.__objects:
            v = o.get(key, Undefined)
            if v is not Undefined:
                return v
        raise KeyError(key)

    def copy(self):
        result = self.__objects[0].copy()
        for d in self.__objects[1:]:
            for k, v in six.iteritems(d):
                result.setdefault(k, v)
        return result

#------------------------------------------------------------------------------


def _indicesForTuplesWithMissingValues(n):
    if n > 0:
        for i in xrange(n):
            yield (i, )
            for t in _indicesForTuplesWithMissingValues(n - i - 1):
                yield (i, ) + tuple(j + i + 1 for j in t)

#------------------------------------------------------------------------------


def tupleWithMissingValues(t, tpl, missingValue):
    result = list()
    for i in xrange(len(tpl)):
        if (i in t):
            result += tuple((missingValue, ))
        else:
            result += tuple((tpl[i],))

    return tuple(result)

#------------------------------------------------------------------------------


def tuplesWithMissingValues(tpl, missingValue):
    yield tpl
    for t in _indicesForTuplesWithMissingValues(len(tpl)):
        yield tupleWithMissingValues(t, tpl, missingValue)

#------------------------------------------------------------------------------
_all_formats = None


def getAllFileFormats():
    global _all_formats

    if _all_formats is None:
                # Build list of all formats used in BrainVISA
        _all_formats = FileFormats('All formats')
        formatsAlreadyDefined = set(('Directory',
                                    'Graph',
                                     'Graph and data',
                                     'mdata file'))
        _all_formats.newFormat('Graph and data', ('arg', 'd|data'))
        _all_formats.newAlias('Graph', 'Graph and data')
        for format in (i for i in getAllFormats() if not i.name.startswith(
            'Series of '
        )):

            if isinstance(format, FormatSeries) or format.name == 'mdata file':
                continue

            if format.name not in formatsAlreadyDefined:
                patterns = []
                for p in format.patterns.patterns:
                    p = p.pattern
                    dotIndex = p.find('.')
                    if dotIndex < 0:
                        break
                    patterns.append(p[dotIndex + 1:])
                try:
                    _all_formats.newFormat(format.name,
                                           patterns,
                                           isinstance(format, MinfFormat))
                    formatsAlreadyDefined.add(format.name)
                except Exception as e:
                    showException()

    return _all_formats

#------------------------------------------------------------------------------


def changeFormat(diskItem,
                 newFormat):

    result = None
    # print('!changeDiskItemFormat!', diskItem, newFormat, type( newFormat ))
    allFormats = getAllFileFormats()

    newFormat = allFormats.getFormat(newFormat.name, None)
    if newFormat is not None:
        # print('!changeDiskItemFormat!  ', newFormat, 'found.')
        format, ext, noExt = allFormats._findMatchingFormat(
            diskItem.fullPath(withQueryString=False)
        )
        if format is not None:
            # print('!changeDiskItemFormat!  ', format, 'matching.')
            result = diskItem.clone()
            result.format = getFormat(str(format.name))
            result._files = [os.path.normpath(noExt + '.' + ext)
                             for ext in newFormat.extensions()]

    return result


#------------------------------------------------------------------------------
def getFileFormatExtensions(formatName):
    format = getAllFileFormats().getFormat(formatName)
    if format is not None:
        return format.extensions()
    else:
        return None


#------------------------------------------------------------------------------
class DatabaseError(Exception):
    pass


#------------------------------------------------------------------------------
class NotInDatabaseError(DatabaseError):
    pass


#------------------------------------------------------------------------------
class Database(object):

    """
    Base class for Brainvisa databases.
    """

    _all_formats = None

    @property
    def formats(self):
        if Database._all_formats is None:
            Database._all_formats = getAllFileFormats()
        return Database._all_formats

    @staticmethod
    def getAttributeValues(attributeName, selection, required, default=Undefined):
        r = required.get(attributeName, Undefined)
        s = selection.get(attributeName, Undefined)
        t = selection.get(attributeName, default)
        if t is Undefined:
            if r is Undefined:
                return []
            if r is None or isinstance(r, basestring):
                return [r]
            return r
        if t is None or isinstance(t, basestring):
            t = [t]
        elif t is Undefined:
            t = []
        if s is None or isinstance(s, basestring):
            s = [s]
        elif s is Undefined:
            s = []
        # if no selection is specified, we must try both None and default value
        # otherwise we are making this attribute mandatory
        if len(s) == 0:
            s = s + [None] + t
        if r is Undefined:
            return s
        if r is None or isinstance(r, basestring):
            r = set([r])
        else:
            r = set(r)
        i = r.intersection(s)
        if i:
            return list(i)
        return list(r)

    def insertDiskItem(self, item, **kwargs):
        self.insertDiskItems((item, ), **kwargs)

    def removeDiskItem(self, item, **kwargs):
        self.removeDiskItems((item, ), **kwargs)

    def findOrCreateDiskItems(self, selection={}, **required):
        fullPaths = set()
        for item in self.findDiskItems(selection, **required):
            fullPaths.add(item.fullPath())
            yield item
        for item in self.createDiskItems(selection, **required):
            if item.fullPath() not in fullPaths:
                yield item

    def findDiskItem(self, *args, **kwargs):
        item = None
        for i in self.findDiskItems(*args, **kwargs):
            if item is None:
                item = i
            else:
                # At least two values found ==> return None
                return None
        return item

    def findOrCreateDiskItem(self, *args, **kwargs):
        item = None
        for i in self.findOrCreateDiskItems(*args, **kwargs):
            if item is None:
                item = i
            else:
                # At least two values found ==> return None
                return None
        return item

    def currentThreadCleanup(self):
        pass

    def createDiskItemFromFormatExtension(self, fileName, defaultValue=Undefined):
        fileName, queryString = split_query_string(fileName)
        format, ext, noExt = self.formats._findMatchingFormat(fileName)
        if format is not None:
            extensions = format.extensions()
            if len(extensions) == 1:
                if ext:
                    files = [noExt + '.' + ext]
                else:
                    files = [noExt]
            else:
                files = [noExt + '.' + ext for ext in extensions]
            diskItem = File(noExt, None)
            diskItem.format = getFormat(str(format.name))
            diskItem.type = None
            diskItem._files = files
            diskItem._queryStringAttributes = parse_query_string(queryString) \
                                              if queryString else {}
            return diskItem
        if defaultValue is Undefined:
            raise DatabaseError(
                _('No format is matching filename "%s"') % fileName)
        return None

    def findTransformationPaths(self, source_referential,
                                destination_referential, maxLength=None,
                                bidirectional=False):
        '''Return a generator object that iterate over all the transformation
        paths going from source_referential to destination_referential.
        A transformation path is a list of ( transformation uuid, destination
        referentia uuid). The pathsare returned in increasing length order.
        If maxlength is set to a non null positive value, it limits the size of
        the paths returned. Source and destination referentials must be given as
        string uuid.'''
        if isinstance(source_referential, Uuid):
            source_referential = str(source_referential)
        if isinstance(destination_referential, Uuid):
            destination_referential = str(destination_referential)

        # print('!findTransformationPaths!', source_referential,
        # destination_referential, maxLength, bidirectional)
        paths = self.findReferentialNeighbours(
            source_referential, bidirectional=bidirectional,
          flat_output=True)
        paths = [([[t[0], t[1 if t[1] != source_referential else 2]]],
                  set([t[1 if t[1] != source_referential else 2]]))
                 for t in paths]
        length = 1
        while paths:
            if maxLength and length > maxLength:
                break
            longerPaths = []
            for path, referentials in paths:
                # Get the last referential of the path
                lastReferential = path[-1][1]
                # Check if the path reach the destination referential
                # print('!findTransformationPaths 2!', path)
                if lastReferential == destination_referential:
                    # print('!findTransformationPaths! -->', path)
                    yield path
                    continue
                if lastReferential == source_referential:
                    continue

                # Get all the transformations objects starting from the last referential
                # of the path
                newPaths = self.findReferentialNeighbours(
                    lastReferential, bidirectional=bidirectional,
                  flat_output=True)

                for p in newPaths:
                    index = 1 if p[1] != lastReferential else 2
                    if p[index] not in referentials:
                        newReferentials = set(referentials)
                        newReferentials.add(p[index])
                        longerPaths.append(
                            (path + [[p[0], p[index]]], newReferentials))
            paths = longerPaths
            length += 1
        # print('!findTransformationPaths! finished')

    def findTransformationPathsFast(self, source_referential,
                                    destination_referential, maxLength=4,
                                    stopAtFirstPath=False):

        if isinstance(source_referential, Uuid):
            source_referential = str(source_referential)
        if isinstance(destination_referential, Uuid):
            destination_referential = str(destination_referential)

        # print('!findTransformationPathsFast!', source_referential, destination_referential, maxLength)
        # cursor = self._getDatabaseCursor()

        refs2explore = set([source_referential])
        allRefs = refs2explore
        # transfos = {source_referential:[[(None, None, None),],]}
        transfos = {source_referential: [[], ]}
            # transfos contains for each referential in refs2explore a list of
            # triplet (transform, from, to)
        length = 0
        refs2explore2 = set()
        # if '7c5de998-bce1-04b7-1b71-9f31ee946620' == source_referential or destination_referential == '7c5de998-bce1-04b7-1b71-9f31ee946620':
            # import pdb; pdb.set_trace()
        while destination_referential not in refs2explore and length <= maxLength and len(refs2explore) > 0:
            for r in refs2explore:  # Parcourons les referentiels source disponibles
                (refs, paths) = self.findReferentialNeighbours(r)
                 #On obtient tous les référentiels cible et les chemins vers ceux-ci
                # print("EXPAND REFS -> ",refs)
                refs2explore2.update(
                    refs)  # On ajoute ces référentiels dans ceux à explorer plus tard
                for r2 in refs:  # Pour les referentiels trouvés, on ajoute un chemin
                    if r2 not in transfos:  # Si on n'a pas encore ce referentiel, on initialise ses chemins de transfos
                        transfos[r2] = []
                    for tr in transfos[r]:  # On est partis du referentiel r pour trouver r2 -> on cherche les transfos qui menaient à r
                        for tr2 in paths[r2]:  # S'il y a plusieurs transfos disponibles de r vers r2
                            if len(tr) > 0 and tr[-1] == tr2:  # Do not add paths like transf12,transf12 (transf12 + transf12 in reverse goes back to the previous referential)
                                pass
                            else:
                                transfos[r2].append(
                                    tr + [tr2, ])  # On ajoute à r2 les chemins vers r+les chemins r->r2

            refs2explore = refs2explore2 - \
                allRefs  # Do not explore already explored ones (removes circular transforms)
            allRefs.update(refs)
            # print("--- all Refs ->", allRefs)
            # print("------transfos ->",transfos)
            if stopAtFirstPath == True and destination_referential in refs2explore:  # Found it !
                # print("FOUND :",transfos[destination_referential])
                return iter(transfos[destination_referential])  # iter -> because calling function expects a generator

            length += 1
        if destination_referential in refs2explore:  # Found it !
            # print("FOUND :",transfos[destination_referential])
            return iter(transfos[destination_referential])
        else:
            # print("NOT FOUND")
            return iter([])

                # for p in newPaths:
                    # if p[ 1 ] not in referentials:
                        # newReferentials = set( referentials )
                        # newReferentials.add( p[ 1 ] )
                        # longerPaths.append( ( path + [ p ], newReferentials ) )
            # paths = longerPaths
            # length += 1
        # print('!findTransformationPaths! finished')

    def findReferentialNeighbours(self, ref, bidirectional=True,
                                  flat_output=False):
        raise NotImplementedError(
            'findReferentialNeighbours has to be redefined in children classes of Database')


#------------------------------------------------------------------------------
# dbg# import weakref
class SQLDatabase(Database):

    """
    A Brainvisa database with files stored in a hierarchically organized directory and a SQL database indexing the files according to Brainvisa ontology.

    The SQL database is implemented using SQLite.
    """
    class CursorProxy(object):
# dbg#     _allProxy = weakref.WeakKeyDictionary()
        _proxyId = 0
        _executeCount = 0

        def __init__(self, cursor):
            self.__cursor = cursor
            self._id = self._proxyId
            SQLDatabase.CursorProxy._proxyId += 1
# dbg#       self._debugMessage( 'create' )
# dbg#       self._allProxy[ self ] = None

        def execute(self, *args, **kwargs):
            # SQLDatabase.CursorProxy._executeCount += 1
            self._debugMessage(
                'execute:' + str(SQLDatabase.CursorProxy._executeCount) + ' ' + args[0])
            return self.__cursor.execute(*args, **kwargs)

        def executemany(self, *args, **kwargs):
            # SQLDatabase.CursorProxy._executeCount += 1
            self._debugMessage('executemany:' + str(
                SQLDatabase.CursorProxy._executeCount) + ' ' + args[0])
            return self.__cursor.executemany(*args, **kwargs)

        def close(self):
# dbg#       self._debugMessage( 'close' )
            self.__cursor.close()
            del self.__cursor

        def _debugMessage(self, message):
            print('!cursor!', self._id, ':', message, file=sys.stderr)

    def __init__(self, sqlDatabaseFile, directory, fso=None, context=None, otherSqliteFiles=[], settings=None):
        # print('!==================================!')
        # print('!SQLDatabase, initialization started!')
        # print('!==================================!')
        # print('!sqlDatabaseFile:', sqlDatabaseFile, '!')
        # print('!directory:', directory, '!')
        # print('!otherSqliteFiles:', otherSqliteFiles, '!')
        # print('!==================================!')

        super(SQLDatabase, self).__init__()
        self._connection = None
        self.name = os.path.normpath(directory)
        if not sqlDatabaseFile or sqlDatabaseFile == ':temporary:':
            self.sqlDatabaseDirectory = temporary.manager.new()
            os.mkdir(self.sqlDatabaseDirectory)
            self.sqlDatabaseFile = os.path.join(
                self.sqlDatabaseDirectory, 'database.sqlite')
        elif sqlDatabaseFile != ':memory:':
            self.sqlDatabaseFile = os.path.normpath(
                os.path.abspath(sqlDatabaseFile))
        else:
            self.sqlDatabaseFile = sqlDatabaseFile
        self.directory = os.path.normpath(directory)
        if not os.path.exists(self.directory):
            raise ValueError(
                HTMLMessage(_t_('<em>%s</em> is not a valid directory') % str(self.directory)))
        minf = os.path.join(self.directory, 'database_settings.minf')
        if fso is None:
            if os.path.exists(minf):
                fso = readMinf(minf)[0].get('ontology', 'brainvisa-3.2.0')
            else:
                fso = 'brainvisa-3.2.0'
        self.fso = FileSystemOntology.get(fso)
        self.otherSqliteFiles = otherSqliteFiles
        self._mustBeUpdated = False
        if settings is not None:
            self.builtin = settings.builtin
            self.read_only = settings.read_only or settings.builtin
            self.uuid = settings.expert_settings.uuid
            self.activate_history = settings.expert_settings.activate_history
        else:
            self.builtin = False
            self.read_only = False
            self.uuid = None
            self.activate_history = False
        if not self.read_only and not os.access(self.directory,
                                                os.R_OK + os.W_OK + os.X_OK):
            self.read_only = True

        self.keysByType = {}
        self._tableAttributesByTypeName = {}
        self._nonMandatoryKeyAttributesByType = {}
        self.ruleSelectionByType = {}
        self._attributesEditionByType = {}
        self._formatsByTypeName = {}
        self._declared_attributes = self.fso._declared_attributes
        for type, rules in six.iteritems(self.fso.typeToPatterns):
            keys = []
            ruleSelectionByAttributeValue = []
            defaultAttributesValues = {}
            rulesDictionary = SortedDictionary()
            rulesByLOPA = {}
            editableAttributes = set()
            declaredAttributes = set(
                chain(*(r.declared_attributes for r in rules)))
            selectedValueAttributes = {}
            nonMandatoryKeyAttributes = set()
            for rule in rules:
                nonMandatoryKeyAttributes.update(
                    rule.nonMandatoryKeyAttributes)
                for n, v in six.iteritems(rule.defaultAttributesValues):
                    vv = defaultAttributesValues.get(n, Undefined)
                    if vv is Undefined:
                        defaultAttributesValues[n] = v
                    else:
                        if v != vv:
                            raise DatabaseError(_('Two different values (%(v1)s and %(v2)s) found for default attribute "%(key)s" of type "%(type)s"') %
                                                {'v1': repr(v), 'v2': repr(vv), 'key': n, 'type': type.name})
                    defaultAttributesValues[n] = v
                rulesByLOPA.setdefault(
                    tuple(rule.pattern.namedRegex()), []).append(rule)
                if rule.formats:
                    for format in rule.formats:
                        typeFormats = self._formatsByTypeName.setdefault(
                            type.name, [])
                        try:
                            formatName = self.formats.getFormat(
                                format.name, format).name
                        except Exception as e:
                            print('!!ERROR!! SQLDatabase: getFormat failed:',
                                  format.name)
                            print(
                                'Database', directory, 'will not be complete and fully working !')
                            continue
                        if formatName not in typeFormats:
                            typeFormats.append(formatName)
                for a in rule.declared_attributes:
                    if a not in keys:
                        keys.append(a)
                        nonMandatoryKeyAttributes.add(a)
            for lopa, lopaRules in six.iteritems(rulesByLOPA):
                for n in lopa:
                    editableAttributes.add(n)
                if len(lopaRules) > 1:
                    key = list(lopa)
                    localAttributesValues = {}
                    for rule in lopaRules:
                        for n, v in rule.localAttributes:
                            ev = localAttributesValues.get(n)
                            if ev is None:
                                localAttributesValues[n] = v
                            elif ev != v:
                                if n not in key:
                                    key.append(n)
                                if n not in ruleSelectionByAttributeValue:
                                    ruleSelectionByAttributeValue.append(n)
                else:
                    key = lopa
                for a in key:
                    if a not in keys:
                        keys.append(a)

            ruleSelectionByMissingKeyAttributes = []
            for rule in rules:
                for n in keys:
                    if n not in ruleSelectionByAttributeValue \
                        and n not in rule.pattern.namedRegex() \
                      and n not in ruleSelectionByMissingKeyAttributes \
                      and n not in nonMandatoryKeyAttributes:
                        ruleSelectionByMissingKeyAttributes.append(n)
            for rule in rules:
                localAttributes = dict(rule.localAttributes)
                for n, v in six.iteritems(localAttributes):
                    selectedValueAttributes.setdefault(n, set()).add(v)
                ruleWithMissingValues = tuplesWithMissingValues(
                    tuple((localAttributes.get(n, '') for n in ruleSelectionByAttributeValue)), '')
                ruleSelection = tuple(((not(n in rule.pattern.namedRegex()))
                                      for n in ruleSelectionByMissingKeyAttributes))
                ruleKeys = set((t, ruleSelection)
                               for t in ruleWithMissingValues)
                # if ruleKey in rulesDictionary:
                    # raise ValueError( 'Two rules with the same selecion key'
                    # )
                for ruleKey in ruleKeys:
                    rulesDictionary.setdefault(ruleKey, []).append(rule)
            # Sort rules by priorityOffset
            for rules in six.itervalues(rulesDictionary):
                if len(rules) > 1:
                    rules.sort(key=lambda x: x.priorityOffset)
            self.keysByType[type] = keys
            self._tableAttributesByTypeName[type.name] = list(keys)
            for a in selectedValueAttributes:
                if a not in self._tableAttributesByTypeName[type.name]:
                    self._tableAttributesByTypeName[type.name].append(a)
            self._nonMandatoryKeyAttributesByType[
                type.name] = nonMandatoryKeyAttributes
            self.ruleSelectionByType[type.name] = (
                ruleSelectionByAttributeValue, ruleSelectionByMissingKeyAttributes, rulesDictionary, defaultAttributesValues)
            self._attributesEditionByType[type.name] = (
                editableAttributes, selectedValueAttributes, declaredAttributes)

        # print('!SQLDatabase, rule! selection by type :')
        # print(self.ruleSelectionByType)

        self.typesWithTable = set()
        self._childrenByTypeName = {}
        for type in six.itervalues(neuroDiskItems.diskItemTypes):
            self._childrenByTypeName.setdefault(
                type.name, set()).add(type.name)
            p = type.parent
            while p is not None:
                self._childrenByTypeName.setdefault(
                    p.name, set()).add(type.name)
                p = p.parent
            if self.keysByType.get(type) is not None:
                self.typesWithTable.add(type)
        self.typesParentOfATypeWithTable = set()
        for type in self.typesWithTable:
            parent = type.parent
            while parent:
                if parent not in self.typesWithTable:
                    self.typesParentOfATypeWithTable.add(parent)
                parent = parent.parent
        self.typesWithTable = set((t.name for t in self.typesWithTable))
        self.keysByType = dict(((t.name, v)
                                for t, v in six.iteritems(self.keysByType)))

        # init of _tableFieldsAndInsertByTypeName
        self._tableFieldsAndInsertByTypeName = {}
        for type in self.typesWithTable:
            tableName = type
            tableFields = ['_uuid', '_format', '_name'] + [
                mangleSQL(i) for i in self._tableAttributesByTypeName[type]]
            tableAttributes = ['_uuid', '_format', '_name'] + [
                i for i in self._tableAttributesByTypeName[type]]
            sql = 'INSERT INTO ' + '"' + tableName + \
                '" (' + ', '.join((i for i in tableFields) ) + \
                ') VALUES (' + ', '.join(('?' for i in tableFields)) + ')'
            self._tableFieldsAndInsertByTypeName[type] = (
                tableName, tableFields, tableAttributes, sql)

        # Determine if the database needs update
        if os.path.exists(self.sqlDatabaseFile):
            if self.fso.lastModification > os.stat(self.sqlDatabaseFile).st_mtime:
                self._mustBeUpdated = True
                brainvisa.processes.defaultContext().write(
                    "Database ",  self.name, " must be updated because the database file is too old.")
                # showWarning( _( 'ontology "%(ontology)s" had been modified,
                # database "%(database)s" should be updated. Use the process :
                # Data Management =&gt; Update databases.' ) % { 'ontology':
                # self.fso.name, 'database': self.name } )
            else:  # database seem to be up to date but let's check if all the types tables exist
                if not self.checkTables():
                    self._mustBeUpdated = True
                    brainvisa.processes.defaultContext().write(
                        "Database ",  self.name, " must be updated because some types tables are missing.")
        else:
            if (sqlDatabaseFile != ":memory:") and (sqlDatabaseFile != ":temporary:") and (len(os.listdir(self.directory)) > 1):  # there is at least database_settings.minf
                self._mustBeUpdated = True
                brainvisa.processes.defaultContext().write(
                    "Database ",  self.name, " must be updated because there is no database file.")
            else:  # if database directory is empty , it is a new database or it is in memory or in temp dir -> automatically update
                if self.createTables():
                    self.update(context=context)
        if self.otherSqliteFiles:  # if there are other sqlite files, the database might have been modified by other version of brainvisa
            # update or not depends on the value of databaseVersionSync option
            if ((neuroConfig.databaseVersionSync is None) and (not neuroConfig.setup)):
                neuroConfig.chooseDatabaseVersionSyncOption(context)
            if neuroConfig.databaseVersionSync == 'auto':
                self._mustBeUpdated = True
                brainvisa.processes.defaultContext().write(
                    "Database ",  self.name, " must be updated because it has been used with other versions of Brainvisa.")

        # print('!==================================!')
        # print('!SQLDatabase initialization ended!')
        # print('!==================================!')

    def _scanDatabaseByChunks(
            self, directoriesToScan, recursion=True, context=None, chunkSize=1000):

        diskitems = []
        n = 0
        for i in self.scanDatabaseDirectories(
            directoriesToScan=directoriesToScan, recursion=recursion,
                context=context):
            if i.type is not None:
                if i.isReadable():
                    diskitems.append(i)
                    n += 1
                    if n >= chunkSize:
                        yield diskitems
                        diskitems = []
                        n = 0
                else:
                    if context is not None:
                        context.warning(
                            "The data ", i.fullPath(), "is not readable.")
        if n != 0:
            yield diskitems

    def updateHistoryFiles(self, directoriesToScan=None, recursion=True, context=None, scanAllBvproc=False):
        """
        Method to update a database based on reading bvproc and the date of the last incremental date in order to avoid the whole scan
        of files. Faster than updateAll method.
        """
        # INI
        infiles = []
        simulation = False
        # if simulation: removeold = False
        directory = os.path.join(self.name, "history_book")
        params = neuroConfig.DatabaseSettings(self.name)
        lastIncrementalUpdates = params.expert_settings.lastIncrementalUpdates
        lastIncrementalUpdate = lastIncrementalUpdates.get(databaseVersion)
        if lastIncrementalUpdate is None:
            lastIncrementalUpdate = params.expert_settings.lastIncrementalUpdate
        if not lastIncrementalUpdate:
            t = 0.
        else:
            t = time.mktime(time.strptime(lastIncrementalUpdate,
                                          '%Y-%m-%d-%H:%M'))
        t0 = time.time()

        # INI of the list of bvproc files
        for f in os.listdir(directory):
            if os.path.isdir(os.path.join(directory, f)):
                for readFile in os.listdir(os.path.join(directory, f)):
                    if readFile.endswith('.bvproc') or readFile.endswith('.bvsession'):
                        ff = os.path.join(directory, f, readFile)
                        if not scanAllBvproc:
                            s = os.stat(ff)
                            if s.st_mtime >= t:
                                infiles.append(ff)
                        else:
                            infiles.append(ff)

        toadd = set()  # diskItems to insert
        deadhistories = set()  # diskItems which doesn't exist anymore
        livehistories = set()  # already inserted diskItems
        scanned = 0

        if len(infiles) > 0:
            for bvprocfile in infiles:
                addit = False
                # scan bvproc
                if bvprocfile.endswith('.bvproc'):
                    # print("Name of bvproc", bvprocfile)
                    try:
                        p = readMinf(bvprocfile)[
                            0]  # ProcessExecutionEvent object
                    except:
                        context.warning(
                            'process history file %s cannot be read.' % bvprocfile)
                        continue
                    if not hasattr(p, 'content'):
                        context.warning(
                            'process history file %s is actually not an history file' % bvprocfile)
                        continue
                    idf = os.path.basename(bvprocfile)
                    idf = idf[: idf.rfind('.')]
                    halive = False
                    listModifiedFiles = p.content.get('modified_data', [])
                    listModifiedFiles.append(
                        bvprocfile)  # add the bvprocfile name in order to update it too
                    for par in listModifiedFiles:
                        # addit = False
                        try:
                            item = self.getDiskItemFromFileName(
                                par)  # already exists in DB: no need to add it
                            item.readAndUpdateMinf()
                                                   # it may have been
                                                   # modified/rewritten.
                        except:
                            try:
                                item = self.createDiskItemFromFileName(par)
                                addit = True
                            except:
                                context.write(
                                    'Warning: file', par, 'cannot be inserted in any database.')
                                continue
                        scanned += 1
                        if item is not None and (isinstance(item, DiskItem)) and item.isReadable() and item.get("_database", None) and (not hasattr(item, '_isTemporary') or not item._isTemporary):
                            if addit:
                                toadd.add(item)
                            lasth = item.get('lastHistoricalEvent', None)
                            if lasth is not None and lasth == idf:
                                halive = True
                    if not halive:
                        deadhistories.add(bvprocfile)
                    else:
                        livehistories.add(bvprocfile)

                # scan bvsession
                elif bvprocfile.endswith('.bvsession'):
                    try:
                        item = self.getDiskItemFromFileName(
                            bvprocfile)  # already exists in DB: no need to add it
                    except:
                        try:
                            item = self.createDiskItemFromFileName(bvprocfile)
                            addit = True
                        except:
                            context.write(
                                'Warning: file', bvprocfile, 'cannot be inserted in any database.')
                            continue
                    if item is not None and (isinstance(item, DiskItem)) and item.isReadable() and item.get("_database", None) and (not hasattr(item, '_isTemporary') or not item._isTemporary):
                        if addit:
                            toadd.add(item)

        else:
            context.write(
                "None history file to update, please check the organisation of history files. Use the BvProc sorting process into the Data Management toolbox.")

        context.write('parsing done. Scanned %d files/items.' % scanned)
        context.write('living history files:', len(livehistories))
        context.write('list history files:', livehistories)
        context.write('dead history files:', len(deadhistories))
        context.write('list of dead history files:', deadhistories)

        # dead files are not removed for the moment, because a bvproc could
        # referenced other files.
        context.write('removing dead histories...')
        for item in deadhistories:
            diskItem = self.getDiskItemFromFileName(item, None)
            if diskItem:  # remove like a diskitem
                self.removeDiskItem(diskItem, eraseFiles=True)
            else:  # remove like files, not created into database
                os.unlink(item)
                temporaryPath = item + ".minf"
                if os.path.isfile(temporaryPath):
                    os.unlink(temporaryPath)
        context.write('done.')

        context.write('adding %d disk items...' % len(toadd))
        context.write('adding ', toadd)
        if simulation:
            context.write('Nothing changed: we are in simulation mode.')
        else:
            for item in toadd:
                try:
                    self.insertDiskItem(item, update=True)
                except NotInDatabaseError:
                    pass

        # update the date of last_incremental_update
        if not scanAllBvproc and len(infiles) > 0:
            dateLastIncrementalUpdate = time.strftime(
                '%Y-%m-%d-%H:%M', time.localtime())
            params = neuroConfig.DatabaseSettings(self.name)
            params.expert_settings.lastIncrementalUpdates[databaseVersion] \
                = dateLastIncrementalUpdate
            try:
                writeMinf(
                    os.path.join(params.directory, 'database_settings.minf'), (params.expert_settings, ))
            except IOError:
                pass

        duration = time.time() - t0
        context.write("All is done: ", timeDifferenceToString(duration))

    def update(self, directoriesToScan=None, recursion=True, context=None):
        if directoriesToScan:
            directoriesToScan = [d for d in directoriesToScan
                                 if os.path.normpath(d).startswith(os.path.normpath(self.directory))]
            if not directoriesToScan:
                return
        if context is not None:
            context.write(self.name + ': parse directories and insert items')
        t0 = time.time()
        for diskitems in self._scanDatabaseByChunks(
            directoriesToScan=directoriesToScan, recursion=recursion,
                context=context, chunkSize=1000):
            self.insertDiskItems(
                diskitems, update=True, insertParentDirs=False)
        duration = time.time() - t0
        cursor = self._getDatabaseCursor()
        try:
            fileCount = cursor.execute(
                'select COUNT(*) from _filenames_').fetchone()[0]
            diskItemCount = cursor.execute(
                'select COUNT(*) from _diskitems_').fetchone()[0]
        finally:
            self._closeDatabaseCursor(cursor)
        if context is not None:
            context.write(self.name + ':', fileCount, 'files are stored as',
                          diskItemCount, 'DiskItems in', timeDifferenceToString(duration))
        self._mustBeUpdated = False

    def clear(self, context=None):
        if ((neuroConfig.databaseVersionSync == 'auto') and self.otherSqliteFiles):
            for f in self.otherSqliteFiles:
                if os.path.exists(f):
                    os.remove(f)
                if os.path.exists(f + ".minf"):
                    os.remove(f + ".minf")
            if context is not None:
                context.write(
                    "Delete other versions of database cache files : " + unicode(self.otherSqliteFiles))
            self.otherSqliteFiles = []
        cursor = self._getDatabaseCursor()
        try:
            tables = cursor.execute(
                'SELECT name FROM sqlite_master WHERE type="table"').fetchall()
            for table in tables:
                cursor.execute('DROP TABLE "' + table[0] + '"')
            cursor.execute('VACUUM')
        except Exception:
            context.warning(
                "The database file must be corrupted, deleting it.")
            if os.path.exists(self.sqlDatabaseFile):
                os.remove(self.sqlDatabaseFile)
        finally:
            self._closeDatabaseCursor(cursor)
        self._connection.closeSqliteConnections()
        self.currentThreadCleanup()
        self._connection = None
        self.createTables(context=context)

    def fsoToHTML(self, fileName):
        out = open(fileName, 'w')
        print(
            '<html>\n<body>\n<center><h1>' + self.fso.name + '</h1></center>',
              file=out)
        for type in sorted(self.keysByType):
            print(
                '<h3 id="' +
                    htmlEscape(type) + '">' + htmlEscape(
                        type) + '</h3><blockquote>',
                  file=out)
            parentType = getDiskItemType(type).parent
            if parentType is not None:
                print('<b>Parent types:<blockquote>', file=out)
                while parentType is not None:
                    t = htmlEscape(parentType.name)
                    print(
                        '<a href="#' + t + '">' + htmlEscape(t) + '</a></p>',
                          file=out)
                    parentType = parentType.parent
                print('</blockquote>', file=out)
            key = self.keysByType[type]
            print('<b>Key: </b><font color="blue">' +
                  htmlEscape(unicode(key)) + '</font><p>', file=out)
            nonMandatory = self._nonMandatoryKeyAttributesByType[type]
            if nonMandatory:
                print('<blockquote><b>Non mandatory key attributes: </b>' +
                      htmlEscape(tuple(nonMandatory)) + '<p>', file=out)
            ruleSelectionByAttributeValue, ruleSelectionByMissingKeyAttributes, rulesDictionary, defaultAttributesValues = self.ruleSelectionByType[
                type]
            if defaultAttributesValues:
                print(
                    '<b>Default attributes values:</b><blockquote>', file=out)
                for n, v in six.iteritems(defaultAttributesValues):
                    print(n + ' = ' + htmlEscape(repr(v)) + '<br/>', file=out)
                print('</blockquote>', file=out)
            if ruleSelectionByAttributeValue or ruleSelectionByMissingKeyAttributes:
                print('<b>Rules selection key: </b><font color=darkgreen>' + htmlEscape(unicode(ruleSelectionByAttributeValue))
                      + '</font> <font color=blue>' + htmlEscape(unicode(ruleSelectionByMissingKeyAttributes)) + '</font><p>', file=out)
            for ruleKey, rules in six.iteritems(rulesDictionary):
                # print('<font color=darkgreen>' + htmlEscape( unicode(
                # ruleKey[0] ) ) + '</font> <font color=blue>' + htmlEscape(
                # unicode( ruleKey[1] ) ) + '</font><blockquote>', file=out)
                if len(rules) > 1:
                    print('<hr>', file=out)
                for rule in rules:
                    print(
                        htmlEscape(unicode(rule.pattern.pattern)) + '<br/>',
                          file=out)
                    print('<blockquote>', file=out)
                    print('<b>Formats: </b>' + htmlEscape(
                        repr(rule.formats)) + '<br/>', file=out)
                    print('Rule selection key: <font color=darkgreen>' + htmlEscape(
                        unicode(ruleKey[0])) + '</font> <font color=blue>' + htmlEscape(unicode(ruleKey[1])) + '</font><br/>', file=out)
                    print(
                        'Priority offset: ' +
                            str(rule.priorityOffset) + '<br/>',
                          file=out)
                    if rule.localAttributes:
                        for n in key:
                            if n in rule.pattern.namedRegex() or n in ruleSelectionByAttributeValue:
                                continue
                            f = '<font color=blue>'
                            nf = '</font>'
                            print(f + n + " = ''" + nf + '<br/>', file=out)
                        for n, v in rule.localAttributes:
                            if n in rule.pattern.namedRegex():
                                continue
                            if n in ruleSelectionByAttributeValue:
                                f = '<font color=darkgreen>'
                                nf = '</font>'
                            else:
                                f = nf = ''
                            print(
                                f + n + ' = ' +
                                    htmlEscape(repr(v)) + nf + '<br/>',
                                  file=out)
                    print('</blockquote>', file=out)
                if len(rules) > 1:
                    print('<hr>', file=out)
                # print('</blockquote>', file=out)
            print('</blockquote></blockquote>', file=out)
        print('</body>\n<//html>\n', file=out)
        out.close()

    def _getDatabaseCursor(self):
        databaseFile = self.sqlDatabaseFile
        if not (os.path.exists(self.sqlDatabaseFile)):
            databaseFile = ':memory:'
        if self._connection is None:
            self._connection = ThreadSafeSQLiteConnection(
                databaseFile, 20, isolation_level="EXCLUSIVE")
        # cursor = self.CursorProxy( self._connection._getConnection().cursor()
        # )
        cursor = self._connection._getConnection().cursor()
        cursor.execute('PRAGMA synchronous =  0')
        return cursor

    def _closeDatabaseCursor(self, cursor, rollback=False):
        if self._connection is not None:
            cursor.close()
            connection = self._connection._getConnection()
            if rollback:
                connection.rollback()
            else:
                connection.commit()

    def currentThreadCleanup(self):
        if self._connection is not None:
            self._connection.currentThreadCleanup()

    def createTables(self, context=None):
        # if the database file is created by sqlite, the write permission is
        # given only for the current user, not for the group, so the database
        # cannot be shared
        if not os.path.exists(self.sqlDatabaseFile) and self.sqlDatabaseFile not in ('', ':memory:'):
            f = open(self.sqlDatabaseFile, "w")
            f.close()
        cursor = self._getDatabaseCursor()
        try:
            self._tableFieldsAndInsertByTypeName = {}
            create = True
            try:
                cursor.execute(
                    'CREATE TABLE _DISKITEMS_ (_uuid CHAR(36) PRIMARY KEY, _diskItem TEXT)')
            except sqlite3.OperationalError:
                create = False
            if create:
                if context is not None:
                    context.write('Generating database tables for', self.name)
                cursor.execute(
                    'CREATE TABLE _FILENAMES_ (filename VARCHAR PRIMARY KEY, _uuid CHAR(36))')
                cursor.execute(
                    'CREATE INDEX _IDX_FILENAMES_ ON _FILENAMES_ (_uuid)')
                cursor.execute(
                    'CREATE TABLE _TRANSFORMATIONS_ (_uuid CHAR(36) PRIMARY KEY, _from CHAR(36), _to CHAR(36))')
                cursor.execute(
                    'CREATE INDEX _IDX_TRANSFORMATIONS_1_ ON _TRANSFORMATIONS_ (_from )')
                cursor.execute(
                    'CREATE INDEX _IDX_TRANSFORMATIONS_2_ ON _TRANSFORMATIONS_ ( _to )')
            for type in self.typesWithTable:
                # tableName = mangleSQL(type.name)
                tableName = type
                tableFields = ['_uuid', '_format', '_name'] + [
                    mangleSQL(i) for i in self._tableAttributesByTypeName[type]]
                tableAttributes = ['_uuid', '_format', '_name'] + [
                    i for i in self._tableAttributesByTypeName[type]]
                if create:
                    sql = 'CREATE TABLE ' + '"' + tableName + \
                        '" (_uuid CHAR(36) PRIMARY KEY, ' + ', '.join(
                            (i + ' VARCHAR' for i in tableFields[1:])) + ')'
                    # print('!createTables!', sql)
                    cursor.execute(sql)
                    # create index
                    keys = self.keysByType[type]
                    if keys:
                        sql = 'CREATE INDEX "IDX_' + tableName + '" ON "' + tableName + \
                            '" ( ' + ', '.join(
                                [mangleSQL(i) for i in keys]) + ')'
                        cursor.execute(sql)
                sql = 'INSERT INTO ' + '"' + tableName + \
                    '" (' + ', '.join((i for i in tableFields) ) + \
                    ') VALUES (' + ', '.join(
                            ('?' for i in tableFields)) + ')'
                self._tableFieldsAndInsertByTypeName[type] = (
                    tableName, tableFields, tableAttributes, sql)
        except:
            self._closeDatabaseCursor(cursor, rollback=True)
            raise
        else:
            self._closeDatabaseCursor(cursor)
        # Save, in the database directory, an HTML file corresponding to
        # database ontology
        if create and os.path.exists(self.sqlDatabaseFile):
            html = os.path.join(
                os.path.dirname(self.sqlDatabaseFile), 'database_fso.html')
            self.fsoToHTML(html)
        return create

    def checkTables(self):
        """
        Checks if all types currently defined in the database ontology have a matching table in the sqlite database.
        It may be not the case when the database has been updated with a version of brainvisa that has not all the toolboxes. It should then be updated.
        """
        cursor = self._getDatabaseCursor()
        tablesExist = False
        try:
            try:
                res = cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = set([t[0] for t in res.fetchall()])
                             # fetchall returns a list of tuples
                tablesExist = self.typesWithTable.issubset(
                    tables)  # there are also tables for diskitems and filenames which does match a specific type.
            except sqlite3.OperationalError as e:
                brainvisa.processes.defaultContext().warning(e.message)
        finally:
            self._closeDatabaseCursor(cursor)
        return tablesExist

    def _diskItemsWithParents(self, diskItems):
        diSet = set(diskItems)
        cursor = None
        for diskItem in diskItems:
            dirname = os.path.dirname(diskItem.fullPath())
            reldirname = relative_path(dirname, self.directory)
            # add parents until one is already in the set or already in the
            # database
            lastItem = diskItem
            while reldirname:
                dirItem = self.createDiskItemFromFileName(
                    os.path.join(self.directory, reldirname), None)
                if dirItem:
                    # set/fix parent item
                    lastItem.parent = dirItem
                    lastItem = dirItem
                    if dirItem in diSet:
                        break
                    # check if it is already in the database
                    if cursor is None:
                        cursor = self._getDatabaseCursor()
                    uuid = cursor.execute(
                        'SELECT _uuid FROM _FILENAMES_ WHERE filename=?',
                      (reldirname, )).fetchone()
                    if uuid:
                        break
                    diSet.add(dirItem)
                reldirname = os.path.dirname(reldirname)
        return diSet

    def insertDiskItems(self, diskItems, update=False, insertParentDirs=True):
        cursor = self._getDatabaseCursor()
        diSet = diskItems
        if insertParentDirs:
            diSet = self._diskItemsWithParents(diskItems)
        try:
            # print("sqlFSODatabase : insertDiskItems ", diSet)
            for diskItem in diSet:
                if diskItem.type is None:
                    raise DatabaseError(
                        _('Cannot insert an item wthout type in a database: %s') % (unicode(diskItem), ))
                try:
                    uuid = str(diskItem.uuid())
                except RuntimeError:
                    uuid = str(diskItem.uuid(saveMinf=False))
                if diskItem._write:
                    diskItem.readAndUpdateMinf()
                    diskItem._write = False

                if diskItem.format:
                    format = self.formats.getFormat(
                        diskItem.format.name, diskItem.format).name
                else:
                    format = None

                diskItem._globalAttributes.pop("_database", None)
                state = {
                    'isDirectory': isinstance(diskItem, Directory),
                  'type': diskItem.type.name,
                  'format': format,
                  'name': relative_path(diskItem.name, self.directory),
                  '_files': [relative_path(f, self.directory) for f in diskItem._files],
                  '_localAttributes': diskItem._localAttributes,
                  '_globalAttributes': diskItem._globalAttributes,
                  '_minfAttributes': diskItem._minfAttributes,
                  '_otherAttributes': diskItem._otherAttributes,
                  '_queryStringAttributes': diskItem._queryStringAttributes,
                  '_uuid': diskItem._uuid,
                  '_priority': getattr(diskItem, '_priority', 0),
                }
                minf = cPickle.dumps(state)
                diskItem._globalAttributes["_database"] = self.name
                if diskItem.type.isA('Transformation'):
                    destination_referential = diskItem.getNonHierarchy(
                        'destination_referential')
                    if destination_referential:
                        destination_referential = str(destination_referential)
                    source_referential = diskItem.getNonHierarchy(
                        'source_referential')
                    if source_referential:
                        source_referential = str(source_referential)
                else:
                    destination_referential = None
                    source_referential = None
                try:
                    # print("!!!!!!insert into diskitem : insert", uuid, minf)
                    cursor.execute(
                        'INSERT INTO _DISKITEMS_ (_uuid, _diskItem) VALUES (? ,?)', (uuid, minf))
                    if source_referential and destination_referential:
                        # print('!insert transformation!', uuid,
                        # source_referential, destination_referential )
                        cursor.execute('INSERT INTO _TRANSFORMATIONS_ (_uuid, _from, _to) VALUES (? ,?, ?)', (
                            str(uuid), source_referential, destination_referential))
                    delete = False
                except sqlite3.IntegrityError as e:
                    # an item with the same uuid is already in the database
                    uuid = cursor.execute('SELECT _uuid FROM _FILENAMES_ WHERE filename=?', (
                        relative_path(diskItem.fullPath(), self.directory), )).fetchone()
                    if uuid:
                        uuid = uuid[0]
                        # diskItem file name is in the database
                        if update:
                            if uuid == str(diskItem._uuid):
                                delete = True
                                cursor.execute(
                                    'UPDATE _DISKITEMS_ SET _diskItem=? WHERE _uuid=?', (minf, uuid))
                                if source_referential and destination_referential:
                                    # print('!update transformation!', repr(
                                    # uuid ), repr( source_referential ), repr(
                                    # destination_referential  ))
                                    cursor.execute('UPDATE _TRANSFORMATIONS_ SET _from=?, _to=? WHERE _uuid=?', (
                                        source_referential, destination_referential, str(uuid)))
                            else:
                                raise DatabaseError(
                                    'Cannot insert "%s" because its uuid is in conflict with the uuid of another file in the database' % diskItem.fullPath())
                        else:
                            raise DatabaseError(
                                'Cannot insert "%s" because it is already in the database' % diskItem.fullPath())
                    else:
                        # diskItem file name is not in the database ==> DiskItem's uuid is changed
                        # commit changes
                        self._closeDatabaseCursor(cursor)
                        cursor = self._getDatabaseCursor()
                        print(_('Warning: changed uuid of "%(newDiskItem)s" because another file has the same uuid: %(uuid)s') % {
                            'newDiskItem': repr(diskItem),
                            'uuid': str(diskItem._uuid),
                        }, file=sys.stderr)
                        delete = False
                        diskItem.setUuid(Uuid())
                        uuid = str(diskItem._uuid)
                        state['_uuid'] = diskItem._uuid
                        # f = StringIO()
                        # writeMinf( f, ( state, ) )
                        # minf = f.getvalue()
                        minf = cPickle.dumps(state)
                        cursor.execute(
                            'INSERT INTO _DISKITEMS_ (_uuid, _diskItem) VALUES (? ,?)', (uuid, minf))
                        if source_referential and destination_referential:
                            # print('!insert transformation!', uuid,
                            # source_referential, destination_referential )
                            cursor.execute('INSERT INTO _TRANSFORMATIONS_ (_uuid, _from, _to) VALUES (? ,?, ?)', (
                                str(uuid), source_referential, destination_referential))
                if delete:
                    cursor.execute(
                        'DELETE FROM _FILENAMES_ WHERE _uuid=?', (uuid, ))
                try:
                    cursor.executemany('INSERT INTO _FILENAMES_ (filename, _uuid) VALUES (? ,?)', (
                        (relative_path(i, self.directory), uuid) for i in diskItem.fullPaths()))
                except sqlite3.IntegrityError as e:
                    raise DatabaseError(
                        unicode(e) + ': file names = ' + repr(diskItem.fullPaths()))

                values = [uuid,
                          format, os.path.basename(diskItem.fullPath())]
                if diskItem.type.name in self._tableFieldsAndInsertByTypeName:
                    tableName, tableFields, tableAttributes, sql = self._tableFieldsAndInsertByTypeName[
                        diskItem.type.name]
                    for i in tableAttributes[3:]:
                        v = diskItem.getHierarchy(i)
                        if v is None:
                            values.append(None)
                        elif isinstance(v, basestring):
                            values.append(v)
                        else:
                            values.append(unicode(v))
                    # print('!!', sql, values, [ type(i) for i in values ])
                    if delete:
                        cursor.execute(
                            'DELETE FROM "' + tableName + '" WHERE _uuid=?', (uuid, ))
                    cursor.execute(sql, values)

        except sqlite3.OperationalError as e:
            self._closeDatabaseCursor(cursor, rollback=True)
            raise DatabaseError("Cannot insert items in database " + self.name + ": " +
                                e.message + ". Item:" + diskItem.fullPath() + ". You should update this database.")
        except:
            self._closeDatabaseCursor(cursor, rollback=True)
            raise
        else:
            self._closeDatabaseCursor(cursor)

    def removeDiskItems(self, diskItems, eraseFiles=False):
        cursor = self._getDatabaseCursor()
        try:
            for diskItem in diskItems:
                uuid = str(diskItem.uuid(saveMinf=False))
                cursor.execute(
                    'DELETE FROM _DISKITEMS_ WHERE _uuid=?', (uuid, ))
                cursor.execute(
                    'DELETE FROM _FILENAMES_ WHERE _uuid=?', (uuid, ))
                tableName, tableFields, tableAttributes, sql = self._tableFieldsAndInsertByTypeName[
                    diskItem.type.name]
                cursor.execute(
                    'DELETE FROM "' + tableName + '" WHERE _uuid=?', (uuid, ))
                if diskItem.type.isA('Transformation'):
                    cursor.execute(
                        'DELETE FROM _TRANSFORMATIONS_ WHERE _uuid=?',
                      (uuid, ))
                if eraseFiles:
                    diskItem.eraseFiles()
        except sqlite3.OperationalError as e:
            self._closeDatabaseCursor(cursor, rollback=True)
            raise DatabaseError(
                "Cannot remove items from database " + self.name + ". You should update this database.")
        except:
            self._closeDatabaseCursor(cursor, rollback=True)
            raise
        else:
            self._closeDatabaseCursor(cursor)

    def _diskItemFromMinf(self, minf):
        # if type(minf) is unicode:
            # have to pass a str to readMinf and not a unicode because, xml parser will use encoding information written in the xml tag to decode the string. In brainvisa, all minf are encoded in utf-8
            # minf=minf.encode("utf-8")
        # f = StringIO( minf )
        # state = readMinf( f )[ 0 ]
        if sys.version_info[0] >= 3:
            try:
                state = cPickle.loads(minf)
            except:
                # pickes from python2 may look like this.
                state = cPickle.loads(six.b(minf), encoding='latin1')
        else:
            state = cPickle.loads(str(minf))
        if state['isDirectory']:
            diskItem = Directory(
                os.path.join(self.directory, state['name']), None)
        else:
            diskItem = File(
                os.path.join(self.directory, state['name']), None)
        diskItem.type = getDiskItemType(str(state['type']))
        f = state['format']
        if f:
            diskItem.format = getFormat(str(f))
        # self.name = state[ 'name' ]
        diskItem._files = [os.path.join(self.directory, f)
                           for f in state['_files']]
        diskItem._localAttributes = state['_localAttributes']
        diskItem._globalAttributes = state['_globalAttributes']
        diskItem._globalAttributes["_database"] = self.name
        diskItem._minfAttributes = state['_minfAttributes']
        diskItem._otherAttributes = state['_otherAttributes']
        diskItem._queryStringAttributes = state.get('_queryStringAttributes', {})
        diskItem._changeUuid(state.get('_uuid'))
        diskItem._priority = state['_priority']
        return diskItem

    def getDiskItemFromUuid(self, uuid, defaultValue=Undefined):
        cursor = self._getDatabaseCursor()
        minf = None
        try:
            sql = "SELECT _diskItem from _DISKITEMS_ WHERE _uuid='" + \
                str(uuid) + "'"
            minf = cursor.execute(sql).fetchone()
        except sqlite3.OperationalError as e:
            brainvisa.processes.defaultContext().warning(
                "Cannot question database " + self.name + ". You should update this database.")
        finally:
            self._closeDatabaseCursor(cursor)
        if minf is not None:
            return self._diskItemFromMinf(minf[0])
        if defaultValue is Undefined:
            raise DatabaseError(_('Database "%(database)s" contains no DiskItem with uuid %(uuid)s') %
                                {'database': self.name,  'uuid': str(uuid)})
        return defaultValue

    def getDiskItemFromFileName(self, fileName, defaultValue=Undefined):
        if fileName.startswith(self.directory):
            cursor = self._getDatabaseCursor()
            minf = None
            try:
                sql = "SELECT _diskItem FROM _FILENAMES_ F, _DISKITEMS_ D WHERE F._uuid=D._uuid AND F.filename='" + \
                    unicode(relative_path(fileName, self.directory)) + "'"
                minf = cursor.execute(sql).fetchone()
            except sqlite3.OperationalError as e:
                brainvisa.processes.defaultContext().warning(
                    "Cannot question database " + self.name + ". You should update this database.")
            finally:
                self._closeDatabaseCursor(cursor)
            if minf is not None:
                return self._diskItemFromMinf(minf[0])
        if defaultValue is Undefined:
            raise DatabaseError(_('Database "%(database)s" does not reference file "%(filename)s"') %
                                {'database': self.name,  'filename': fileName})
        return defaultValue

    def createDiskItemFromFileName(self, fileName, defaultValue=Undefined):
        fileName, queryString = split_query_string(fileName)
        diskItem = self.createDiskItemFromFormatExtension(fileName + queryString, 
                                                          None)
        if diskItem is not None:
            d = self.directory
            if fileName.startswith(d):
                splitted = split_path(fileName[len(d) + 1:])
                if os.path.isdir(fileName):
                    lastContent = []
                else:
                    lastContent = None
                content = reduce(lambda x, y: [(y, x)], reversed(splitted[:-1]), [
                                 (os.path.basename(f), lastContent) for f in diskItem._files])
                vdi = VirtualDirectoryIterator(fileName[:len(d)], content)
                lastItem = None
                for item in self.scanDatabaseDirectories(vdi):
                    lastItem = item
                if lastItem is not None and fileName in lastItem.fullPaths(withQueryString=False):
                    lastItem._queryStringAttributes = parse_query_string(
                        queryString)
                    return lastItem
        if defaultValue is Undefined:
            raise DatabaseError(_('Database "%(database)s" cannot reference file "%(filename)s"') %
                                {'database': self.name,  'filename': fileName})
        return defaultValue

    def changeDiskItemFormat(self, diskItem, newFormat):
        return changeFormat(diskItem,
                            newFormat)

    def scanDatabaseDirectories(self, directoriesIterator=None, includeUnknowns=False, directoriesToScan=None, recursion=True, debugHTML=None, context=None):
        if debugHTML:
            print('<html><body><h1>Scan log for database <tt>' + self.name +
                  '</tt></h1>\n<h2>Directory</h2><blockquote>', file=debugHTML)
            print(self.directory, '</blockquote>', file=debugHTML)
        scanner = [
            i for i in self.fso.content if isinstance(i, SetContent)][0].scanner
        # print('## scanDatabaseDirectories', directoriesIterator, directoriesToScan, self.directory)
        # get specific attributes from parent directories
        attributes = {}
        # if directoriesToScan and len( directoriesToScan ) == 1:
            # self._getParentAttributes( directoriesToScan[0], attributes )
        if directoriesIterator is None:
            stack = [
                (DirectoryIterator(self.directory), scanner, attributes, 0)]
        else:
            stack = [(directoriesIterator, scanner, attributes, 0)]

        while stack:
            itDirectory, scanner, attributes, priorityOffset = stack.pop(0)

            f = itDirectory.fullPath()
            if directoriesToScan is not None:
                ignore = True
                allowYield = False
                if recursion:
                    for d in directoriesToScan:
                        i = min(len(d), len(f))
                        if d[:i] == f[:i]:
                            allowYield = len(f) >= len(d)
                            ignore = False
                            break
                else:
                    for d in directoriesToScan:
                        i = min(len(d), len(f))
                        if d[:i] == f[:i]:
                            allowYield = allowYield or f == d
                            ignore = not allowYield and not len(f) <= len(d)
                            if allowYield and not ignore:
                                break
                # print('!scanDatabaseDirectories! directory "' + f + '":
                # ignore =', ignore, ', allowYield =', allowYield)
                if ignore:
                    continue
            else:
                allowYield = True
            if debugHTML:
                print('<h2>' + itDirectory.fullPath() +
                      '</h2>\nparents attributes: ' + repr(attributes), file=debugHTML)
            directoryRules = []
            nonDirectoryRules = []
            for rule in getattr(scanner, 'rules', ()):
                if rule.scanner is not None:
                    directoryRules.append(rule)
                else:
                    nonDirectoryRules.append(rule)
            if debugHTML:
                print('<h3>Rules</h3><blockquote>', file=debugHTML)
                for rule in directoryRules:
                    print('<font color=darkblue>' + htmlEscape(
                        rule.pattern.pattern) + ':</font>', rule.type, '<br>', file=debugHTML)
                for rule in nonDirectoryRules:
                    print('<font color=darkgreen>' + htmlEscape(
                        rule.pattern.pattern) + ':</font>', rule.type, '<br>', file=debugHTML)
                print('</blockquote>', file=debugHTML)
            # Identify formats
            try:
                knownFormat, unknownFormat = self.formats.identify(
                    itDirectory, context=context)
            except OSError as e:
                print(e, file=sys.stderr)
                knownFormat = unknownFormat = []

            if includeUnknowns and allowYield:
                for it in unknownFormat:
                    diskItem = File(it.fileName(), None)
                    diskItem._files = [os.path.normpath(it.fullPath())]
                    diskItem._globalAttributes['_database'] = self.name
                    diskItem._identified = False
                    yield diskItem
            if debugHTML:
                if unknownFormat:
                    print(
                        '<h3>Unknown format</h3><blockquote>', file=debugHTML)
                    for f in unknownFormat:
                        print(
                            '<font color=red>' +
                                repr(f.fullPath()) + '</font><br>',
                              file=debugHTML)
                    print('</blockquote>', file=debugHTML)
                print(
                    '<h3>Items identification</h3><blockquote>', file=debugHTML)

            unknownType = []
            knownType = []
            nameSeriesGroupedItems = {}
            for nameWithoutExtension, files, minf, format, it in knownFormat:
                if format == 'Directory':
                    # Find directories corresponding to a rule with a
                    # SetContent
                    f = it.fileName()

                    for rule in directoryRules:
                        match = DictPattern.match(rule.pattern, f, attributes)
                        if match is not None:
                            a = attributes.copy()
                            a.update(match)
                            a.update(rule.localAttributes)
                            if rule.type is not None or includeUnknowns:
                                # insert declared_attributes read from minf and
                                # fso_attributes.json file
                                if rule.declared_attributes:
                                    for att in rule.declared_attributes:
                                        a.setdefault('_declared_attributes_location', {})[att] = \
                                            os.path.join(
                                            nameWithoutExtension, 'fso_attributes.json')
                                        val = diskItem.get(att)
                                        if val is not None:
                                            a[att] = val
                                if allowYield:
                                    diskItem = Directory(
                                        nameWithoutExtension, None)
                                    diskItem.type = rule.type
                                    diskItem.format = getFormat('Directory')
                                    diskItem._files = [
                                        os.path.normpath(f) for f in files]
                                    diskItem._globalAttributes[
                                        '_database'] = self.name
                                    diskItem._globalAttributes[
                                        '_ontology'] = self.fso.name
                                    diskItem._globalAttributes.update(a)
                                    diskItem._priority = priorityOffset + \
                                        rule.priorityOffset
                                    diskItem._identified = True
                                    diskItem.readAndUpdateMinf()
                                    yield diskItem
                                    if debugHTML:
                                        print(
                                            '<font color=darkblue><b>', diskItem, ':</b>', diskItem.type, '</font> (' + htmlEscape(
                                                rule.pattern.pattern) + ':' + str(rule.type) + ')<br>',
                                              file=debugHTML)
                            stack.append(
                                (it, rule.scanner, a, priorityOffset + rule.priorityOffset))
                            break
                    else:
                        # for rule in directoryRules:
                            # print('  -->', rule.pattern)
                        if includeUnknowns:
                            stack.append(
                                (it, None, attributes, priorityOffset))
                            if allowYield:
                                diskItem = Directory(
                                    nameWithoutExtension, None)
                                diskItem._files = [
                                    os.path.normpath(f) for f in files]
                                diskItem._globalAttributes[
                                    '_database'] = self.name
                                diskItem._identified = False
                                yield diskItem
                else:
                    diskItem = File(nameWithoutExtension, None)
                    diskItem.format = getFormat(str(format))
                    diskItem._files = [
                        os.path.normpath(os.path.join(itDirectory.fullPath(), i)) for i in files]
                    diskItem._globalAttributes['_database'] = self.name
                    for rule in nonDirectoryRules:
                        if rule.formats and format not in rule.formatNamesInSet:
                            if format != 'Graph and data' or 'Graph' not in rule.formatNamesInSet:
                                continue
                        match = DictPattern.match(
                            rule.pattern, os.path.basename(nameWithoutExtension), attributes)
                        if match is not None:
                            diskItem.type = rule.type
                            name_serie = match.pop('name_serie', None)
                            if name_serie is not None:
                                key = (diskItem.type,
                                       format, rule.pattern.pattern, tuple(six.itervalues(match)))
                                groupDiskItem = nameSeriesGroupedItems.get(
                                    key)
                                if groupDiskItem is None:
                                    diskItem._globalAttributes[
                                        '_ontology'] = self.fso.name
                                    diskItem._globalAttributes.update(match)
                                    diskItem._globalAttributes.update(
                                        attributes)
                                    diskItem._globalAttributes.update(
                                        rule.localAttributes)
                                    diskItem._priority = priorityOffset + \
                                        rule.priorityOffset
                                    diskItem._identified = True
                                    groupDiskItem = diskItem
                                    match['name_serie'] = '#'
                                    groupDiskItem.format = getFormat(
                                        str('Series of ' + format))
                                    n = DictPattern.unmatch(
                                        rule.pattern, match, attributes)
                                    groupDiskItem._files = [os.path.normpath(os.path.join(itDirectory.fullPath(), n + '.' + i)) for i in self.formats.getFormat(
                                        format).extensions()]
                                    groupDiskItem._setLocal(
                                        'name_serie', set((name_serie, )))
                                    nameSeriesGroupedItems[
                                        key] = groupDiskItem
                                else:
                                    groupDiskItem._getLocal(
                                        'name_serie').add(name_serie)
                            elif allowYield:
                                diskItem._globalAttributes[
                                    '_ontology'] = self.fso.name
                                diskItem._globalAttributes.update(match)
                                diskItem._globalAttributes.update(attributes)
                                diskItem._globalAttributes.update(
                                    rule.localAttributes)
                                diskItem._priority = priorityOffset + \
                                    rule.priorityOffset
                                diskItem.readAndUpdateMinf()
                                diskItem.readAndUpdateDeclaredAttributes()
                                diskItem._identified = True
                                if debugHTML:
                                    print(
                                        '<font color=darkgreen><b>', diskItem, ':</b>', diskItem.type, '</font> (' + htmlEscape(
                                            rule.pattern.pattern) + ':' + str(rule.type) + ')<br>',
                                          file=debugHTML)
                                yield diskItem
                            break
                    else:
                        if allowYield and includeUnknowns:
                            diskItem.readAndUpdateMinf()
                            diskItem.readAndUpdateDeclaredAttributes()
                            diskItem._identified = False
                            yield diskItem
                        unknownType.append(diskItem)
            if allowYield:
                for diskItem in six.itervalues(nameSeriesGroupedItems):
                    diskItem._setLocal(
                        'name_serie', sorted(diskItem._getLocal('name_serie')))
                    diskItem.readAndUpdateMinf()
                    diskItem.readAndUpdateDeclaredAttributes()
                    yield diskItem
            if debugHTML:
                for diskItem in six.itervalues(nameSeriesGroupedItems):
                    print(
                        '<font color=darkgreen><b>', diskItem, ':</b> ', diskItem.type, repr(
                            diskItem._getLocal(
                                'name_serie')) + '</font><br>',
                          file=debugHTML)
                    # for f in diskItem.fullPaths()[ 1: ]:
                        # print('&nbsp;' * 8 + f + '<br>', file=debugHTML)
                    # print('</font>', file=debugHTML)
                for diskItem in unknownType:
                    print(
                        '<font color=red>', diskItem.fullPath(
                        ), '(' + diskItem.format.name + ')</font><br>',
                          file=debugHTML)

            if debugHTML:
                print('</blockquote>', file=debugHTML)

        if debugHTML:
            print('</body></html>', file=debugHTML)

    def findAttributes(self, attributes, selection={}, _debug=None, exactType=False, **required):
        if exactType:
            types = set(
                self.getAttributeValues('_type', selection, required))
        else:
            types = set(chain(*(self._childrenByTypeName.get(t, ())
                        for t in self.getAttributeValues('_type', selection, required))))
        diskitem_searched = "_diskItem" in attributes
        if _debug is not None:
            print(
                '!findAttributes!', repr(self.name), attributes, tuple(types),
                  selection, required, file=_debug)
        for t in types:
            try:
                tableName, tableFields, tableAttributes, sql = self._tableFieldsAndInsertByTypeName[
                    t]
            except KeyError:
                if _debug is not None:
                    print('!findAttributes!  No table for type', t, 'in',
                          repr(self.name), file=_debug)
                continue
            if diskitem_searched:
                tableAttributes = ['_diskItem'] + tableAttributes
                tableFields = ['_diskItem', 'T._uuid'] + tableFields[1:]
            nonMandatoryKeyAttributes = self._nonMandatoryKeyAttributesByType[
                t]
            # if _debug is not None:
                # print('!findAttributes!  tableFields(', repr( t ), ') =',
                # repr( tableFields ), file=_debug)
            select = []
            tupleIndices = []
            for a in attributes:
                if a == '_type':
                    tupleIndices.append(1)
                    continue
                try:
                    i = tableAttributes.index(a)
                    select.append(tableFields[i])
                    tupleIndices.append(len(select) + 1)
                except ValueError:
                    tupleIndices.append(0)
                    continue
            typeOnly = False
            if not select:
                if [i for i in tupleIndices if i != 0]:
                    select = ['COUNT(*)']
                    typeOnly = True
                else:
                    if _debug is not None:
                        print(
                            '!findAttributes!  No attribute selected for type', t, 'in',
                              repr(
                                  self.name), 'possible values are:', tableAttributes,
                              file=_debug)
                    continue
            where = {}
            for f, a in izip(tableFields, tableAttributes):
                if a in required or a not in nonMandatoryKeyAttributes:
                    v = self.getAttributeValues(a, selection, required)
                    # if _debug is not None:
                        # print('!findAttributes!  getAttributeValues(', repr(
                        # a ), ', ... ) =', repr( v ), file=_debug)
                    if v:
                        where[f] = v
            sql = 'SELECT DISTINCT ' + \
                ', '.join(select) + " FROM '" + tableName + "' "
            if diskitem_searched:
                sql += " T, _DISKITEMS_ D WHERE T._uuid=D._uuid "
            if where:
                sqlWhereClauses = []
                for f, v in six.iteritems(where):
                    if v is None:
                        sqlWhereClauses.append(f + '=NULL')
                    elif isinstance(v, basestring):
                        sqlWhereClauses.append(f + "='" + v + "'")
                    else:
                        # sqlWhereClauses.append( f + ' IN (' + ','.join(
                        # (('NULL' if i is None else "'" + i +"'") for i in v)
                        # ) + ')' )
                        whereParts = list()
                        for i in v:
                            if i is None:
                                whereParts += ('NULL', )
                            else:
                                whereParts += ("'" + i + "'", )
                        sqlWhereClauses.append(
                            f + ' IN (' + ','.join(whereParts) + ')')
                if diskitem_searched:
                    sql += ' AND ' + ' AND '.join(sqlWhereClauses)
                else:
                    sql += ' WHERE ' + ' AND '.join(sqlWhereClauses)
            if _debug is not None:
                print('!findAttributes! ->', sql, file=_debug)
            cursor = self._getDatabaseCursor()
            sqlResult = []
            try:
                try:
                    sqlResult = cursor.execute(sql).fetchall()
                except sqlite3.OperationalError as e:
                    brainvisa.processes.defaultContext().warning(
                        "Cannot question database ", self.name, " : ", e.message, ". You should update this database.")
            finally:
                self._closeDatabaseCursor(cursor)
            for tpl in sqlResult:
                if typeOnly:
                    if tpl[0] > 0:
                        yield tuple(((None, t)[i] for i in tupleIndices))

                else:
                    tpl = (None, t) + tpl
                    yield tuple((tpl[i] for i in tupleIndices))

    def findDiskItems(self, selection={}, _debug=None, exactType=False, **required):
        for t in self.findAttributes(('_diskItem', ), selection, _debug=_debug, exactType=exactType, **required):
            yield self._diskItemFromMinf(t[0])

    def createDiskItems(self, selection={}, _debug=None, exactType=False, **required):
        if exactType:
            types = set(
                self.getAttributeValues('_type', selection, required))
        else:
            tval = [x for x in self.getAttributeValues('_type', selection,
                                                       required) if x is not None]
            types = set(
                chain(*(self._childrenByTypeName[t] for t in tval)))
        if _debug is not None:
            print('!createDiskItems! database:', self.directory, file=_debug)
            print(_debug, '!createDiskItems! types:',
                  tuple(types), file=_debug)
            print(
                _debug, '!createDiskItems! selection:', selection, file=_debug)
            print(_debug, '!createDiskItems! required:', required, file=_debug)
        for type in types:
            r = self.ruleSelectionByType.get(type)
            if r is None:
                if _debug is not None:
                    print(
                        '!createDiskItems! no rule selection found for type', type,
                          file=_debug)
                continue
            possibleFormats = self.getAttributeValues(
                '_format', selection, required)
            if _debug is not None:
                print('!createDiskItems! possibleFormats = ', possibleFormats,
                      file=_debug)
            ruleSelectionByAttributeValue, ruleSelectionByMissingKeyAttributes, rulesDictionary, defaultAttributesValues = r
            if _debug is not None:
                print('!createDiskItems! ruleSelectionByAttributeValue:',
                      ruleSelectionByAttributeValue, file=_debug)
                print('!createDiskItems! ruleSelectionByMissingKeyAttributes:',
                      ruleSelectionByMissingKeyAttributes, file=_debug)
                print('!createDiskItems! rulesDictionary:',
                      rulesDictionary, file=_debug)
                print('!createDiskItems! defaultAttributesValues:',
                      defaultAttributesValues, file=_debug)
            # key = ( tuple( ( selection.get( i, required.get( i, '' ) ) for i in ruleSelectionByAttributeValue ) ),
                            # tuple( ( (False if selection.get( i,
                            # required.get( i ) ) else True) for i in
                            # ruleSelectionByMissingKeyAttributes ) ) )
            keys = []
            stack = [[
                [self.getAttributeValues(i, selection, required, defaultAttributesValues.get(i, Undefined))
                    for i in ruleSelectionByAttributeValue],
                      [self.getAttributeValues(i, selection, required, defaultAttributesValues.get(i, Undefined))
                       for i in ruleSelectionByMissingKeyAttributes]
            ]]
            if _debug is not None:
                print('!createDiskItems! stack = ', stack, file=_debug)
            while stack:
                k1, k2 = stack.pop(0)
                for i in xrange(len(k1)):
                    if isinstance(k1[i], (set, list, tuple)):
                        if k1[i]:
                            stack += [[k1[:i] + [j] + k1[i + 1:], k2]
                                      for j in k1[i]]
                        else:
                            stack += [[k1[:i] + [''] + k1[i + 1:], k2]]
                        k1 = None
                        break
                if k1 is not None:
                    for i in xrange(len(k2)):
                        if isinstance(k2[i], (set, list, tuple)) and k2[i]:
                            stack += [[k1, k2[:i] + [j] + k2[i + 1:]]
                                      for j in k2[i]]
                            k2 = None
                            break
                    if k2 is not None:
                        keys.append((tuple(k1), tuple((not(i)) for i in k2)))
            if _debug is not None:
                print('!createDiskItems! keys for rules selection = ', keys,
                      file=_debug)
            for key in keys:
                rules = rulesDictionary.get(key)
                if rules is not None:
                    if _debug is not None:
                        print('!createDiskItems! rules = ',
                              [r.pattern.pattern for r in rules], file=_debug)
                    for rule in rules:
                        if rule._formatsNameSet:
                            formats = rule._formatsNameSet.intersection(
                                possibleFormats)
                        else:
                            formats = possibleFormats
                        if not formats:
                            if _debug is not None:
                                print(
                                    '!createDiskItems! no possible format for type', type,
                                      'and rule', rule.pattern.pattern, file=_debug)
                            continue
                        cg = CombineGet(
                            required, selection, defaultAttributesValues)
                        names = rule.pattern.multipleUnmatch(cg)
                        if names:
                            for name, unmatchAttributes in names:
                                databaseDirectory = self.getAttributeValues(
                                    '_databaseDirectory', selection, required)
                                if databaseDirectory:
                                    databaseDirectory = databaseDirectory[0]
                                else:
                                    databaseDirectory = self.directory
                                for format in (getFormat(f) for f in formats):  # search format in all format including Series of ...
                                    if format.name == 'Directory':
                                        files = [
                                            os.path.normpath(os.path.join(databaseDirectory, name))]
                                    elif isinstance(format, FormatSeries):  # a Series of ... has in _files the pattern of each data with # instead of the number
                                        cg2 = CombineGet(
                                            {'name_serie': "#"}, unmatchAttributes, required, selection, defaultAttributesValues)
                                        name2 = rule.pattern.unmatch(cg2, cg2)
                                        format2 = self.formats.getFormat(
                                            format.baseFormat.name)  # get the base file format
                                        files = [os.path.normpath(os.path.join(databaseDirectory, name2 + '.' + e))
                                                 for e in format2.extensions()]
                                    else:
                                        format = self.formats.getFormat(
                                            format.name)  # get corresponding file format
                                        files = [os.path.normpath(os.path.join(databaseDirectory, name + '.' + e))
                                                 for e in format.extensions()]
                                    diskItem = File(
                                        os.path.join(databaseDirectory, name), None)
                                    diskItem._files = files
                                    diskItem.type = getDiskItemType(type)
                                    diskItem.format = getFormat(str(
                                        format.name))
                                    # diskItem.uuid( saveMinf=False )
                                    diskItem._globalAttributes[
                                        '_database'] = self.name
                                    diskItem._globalAttributes[
                                        '_ontology'] = self.fso.name
                                    diskItem._write = True
                                    diskItem._globalAttributes['_declared_attributes_location'] = dict(
                                        (att, os.path.normpath(os.path.join(diskItem.fullPath(), path))) for att, path in six.iteritems(rule._declared_attributes_location))
                                    c = CombineGet(
                                        unmatchAttributes, required, selection, defaultAttributesValues)
                                    for n in self.keysByType[type]:
                                        if n == "name_serie":  # name_serie is a local attribute
                                            diskItem._setLocal(n, c.get(n, ""))
                                        else:
                                            value = c.get(n)  # c.get( n, '' )
                                            # don't set values on empty attributes -- this is
                                            # expected for optional declared_attributes, but is it
                                            # OK for standard ones ?
                                            if value:
                                                diskItem._globalAttributes[
                                                    n] = value
                                    for n, v in rule.localAttributes:
                                        diskItem._globalAttributes[n] = v
                                    diskItem._priority = rule.priorityOffset
                                    diskItem.readAndUpdateDeclaredAttributes()
                                    yield diskItem
                        elif _debug is not None:
                            print(
                                '!createDiskItems! rule', rule.pattern.pattern,
                                  'not "unmatched"', file=_debug)
                else:
                    if _debug is not None:
                        print('!createDiskItems! no rule found for type', type,
                              'and key =', key, file=_debug)

    def getAttributesEdition(self, *types):
        editable = set()
        values = {}
        declared = set()
        for t1 in types:
            for t2 in self._childrenByTypeName[t1]:
                e = self._attributesEditionByType.get(t2)
                if e is not None:
                    editable.update(e[0])
                    declared.update(e[2])
                    for a, v in six.iteritems(e[1]):
                        values.setdefault(a, set()).update(v)
        return editable, values, declared

    def getTypeChildren(self, *types):
        return set(chain(*(self._childrenByTypeName[t] for t in types)))

    def getTypesKeysAttributes(self, *types):
        result = []
        for t1 in types:
            for t2 in self._childrenByTypeName[t1]:
                for a in self.keysByType.get(t2, ()):
                    if a not in result:
                        result.append(a)
        return result

    def getTypesFormats(self, *types):
        result = set()
        for t1 in types:
            for t2 in self._childrenByTypeName[t1]:
                f = self._formatsByTypeName.get(t2)
                if f:
                    result.update(f)
        return result

    def newFormat(self, name, patterns):
        if getFormat(name, None) is None:
            bvPatterns = []
            for p in patterns:
                i = p.find('|')
                if i < 0:
                    bvPatterns.append('*.' + p)
                else:
                    bvPatterns.append(p[:i + 1] + '*.' + p[i + 1:])
            Format(name, bvPatterns)
            self.formats.newFormat(name, patterns)

    def findReferentialNeighbours(self, source_referential, cursor=None,
                                  bidirectional=True, flat_output=False):
        """From one referential, find all referentials directly linked by transforms
        and return a tuple (referentials, paths), where paths is a dictionary which contains a list
        of transforms that leads to each referential (key of the dictionary)
        from the source_referential (a transform is a triplet (uuid_transform, uuid_from, uuid_to))

        If flat_output is True, the output is a list of tuples
        (transform, source, dest).
        """
        if cursor is None:
            cursor = self._getDatabaseCursor()
        try:
            if bidirectional:
                paths = cursor.execute(
                    'SELECT DISTINCT _uuid, _from, _to FROM _TRANSFORMATIONS_ WHERE _TRANSFORMATIONS_._from = ? OR _TRANSFORMATIONS_._to = ?',
                  (source_referential, source_referential)).fetchall()
            else:
                paths = cursor.execute(
                    'SELECT DISTINCT _uuid, _from, _to FROM _TRANSFORMATIONS_ WHERE _TRANSFORMATIONS_._from = ?',
                  (source_referential,)).fetchall()
        except Exception as e:
            print('SQL error in database:', self.sqlDatabaseFile)
            print(e)
            paths = []
        if flat_output:
            return paths
        refs = list(set([p[1] for p in paths] + [p[2] for p in paths])
                    - set([source_referential, ]))
        trsfs = dict(
            [(r, [p for p in paths if p[1] == r or p[2] == r]) for r in refs])
        return (refs, trsfs)

    def findTransformationWith(self, uuid):
        '''Return a generator object that iterate over all transformations in database using uuid
        parameter for _to or _from fields'''

        cursor = self._getDatabaseCursor()
        pathsWith = []
        try:
            sql = "SELECT _uuid, _from, _to from _TRANSFORMATIONS_ WHERE _to='" + \
                str(uuid) + "' OR " + "_from='" + str(uuid) + "'"
            # sql = "SELECT _uuid, _from, _to from _TRANSFORMATIONS_ "
            # print(sql)
            pathsWith = cursor.execute(sql).fetchall()
        except sqlite3.OperationalError as e:
            brainvisa.processes.defaultContext().warning(
                "Cannot question database " + self.name + ". You should update this database.")
        finally:
            self._closeDatabaseCursor(cursor)
        if pathsWith == []:
            return None
        else:
            return pathsWith


#------------------------------------------------------------------------------
class NoGeneratorSQLDatabase(SQLDatabase):

    '''
    It is not possible to use a SQLDatabase through Pyro because generators
    cannot be pickled. This class replace all methods creating generators (i.e.
    using yield) by methods returning lists.
    '''

    def __init__(self, sqlDatabaseInstance):
        self._sqlDatabaseInstance = sqlDatabaseInstance

    def __getattr__(self, name):
        return getattr(self._sqlDatabaseInstance, name)

    def scanDatabaseDirectories(self, *args, **kwargs):
        return list(self._sqlDatabaseInstance.scanDatabaseDirectories(*args, **kwargs))

    def findAttributes(self, *args, **kwargs):
        return list(self._sqlDatabaseInstance.findAttributes(*args, **kwargs))

    def findDiskItems(self, *args, **kwargs):
        return list(self._sqlDatabaseInstance.findDiskItems(*args, **kwargs))

    def createDiskItems(self, *args, **kwargs):
        return list(self._sqlDatabaseInstance.createDiskItems(*args, **kwargs))


#------------------------------------------------------------------------------
class SQLDatabases(Database):

    """
    This object stores several :py:class:`SQLDatabase` objects.
    """

    def __init__(self, databases=[]):
        super(SQLDatabases, self).__init__()
        self._databases = SortedDictionary()
        for database in databases:
            self.add(database)

    def iterDatabases(self):
        return six.itervalues(self._databases)

    def database(self, name):
        return self._databases[name]

    def hasDatabase(self, name):
        return name in self._databases

    def add(self, database):
        self._databases[database.name] = database

    def remove(self, name):
        if name in self._databases:
            del self._databases[name]

    def removeDatabases(self):
        self._databases = SortedDictionary()

    def clear(self):
        for d in self.iterDatabases():
            d.clear()

    def update(self, directoriesToScan=None, recursion=True, context=None):
        for d in self.iterDatabases():
            d.update(directoriesToScan=directoriesToScan,
                     recursion=recursion, context=context)

    def _iterateDatabases(self, selection, required={}):
        databases = self.getAttributeValues('_database', selection, required)
        if not databases:
            for d in six.itervalues(self._databases):
                yield d
        for n in databases:
            try:
                yield self._databases[os.path.normpath(n)]
            except KeyError:
                pass

    def insertDiskItems(self, diskItems, update=False, insertParentDirs=True):
        for diskItem in diskItems:
            baseName = diskItem.getHierarchy('_database')
            if baseName is None:
                database = None
                if len(self._databases) == 1:
                    database = values(self._databases)[0]
                    if not diskItem.fullPath().startswith(values(self._databases)[0].name):
                        database = None
                if database is None:
                    raise NotInDatabaseError(
                        _('Cannot find out in which database "%s" should be inserted') % (diskItem.fullPath(), ))
            else:
                database = self._databases[baseName]
            database.insertDiskItems((diskItem,), update=update,
                                     insertParentDirs=insertParentDirs)

    def removeDiskItems(self, diskItems, eraseFiles=False):
        for diskItem in diskItems:
            baseName = diskItem.getHierarchy('_database')
            if baseName is None:
                if len(self._databases) == 1:
                    database = values(self._databases)[0]
                else:
                    raise NotInDatabaseError(
                        _('Cannot find out from which database "%s" should be removed') % (diskItem.fullPath(), ))
            else:
                database = self._databases[baseName]
            database.removeDiskItems((diskItem,), eraseFiles=eraseFiles)

    def getDiskItemFromUuid(self, uuid, defaultValue=Undefined):
        for database in six.itervalues(self._databases):
            item = database.getDiskItemFromUuid(uuid, None)
            if item is not None:
                return item
        if defaultValue is Undefined:
            raise DatabaseError(
                _('No database contain a DiskItem with uuid %(uuid)s') % {'uuid': str(uuid)})
        return defaultValue

    def findTransformationWith(self, uuid):
        item = []
        for database in six.itervalues(self._databases):
            val = database.findTransformationWith(uuid)
            if val != None:
                item.append(database.findTransformationWith(uuid))
        if len(item) == 0:
            return None
        else:
            return item

    def getDiskItemFromFileName(self, fileName, defaultValue=Undefined):
        for database in six.itervalues(self._databases):
            item = database.getDiskItemFromFileName(fileName, None)
            if item is not None:
                return item
        if defaultValue is Undefined:
            raise DatabaseError(
                _('No database reference file "%(filename)s"') % {'filename': fileName})
        return defaultValue

    def findAttributes(self, attributes, selection={},  _debug=None, exactType=False, **required):
        index = 0
        for a in attributes:
            if a == '_database':
                break
            index += 1
        else:
            index = -1
        for database in self._iterateDatabases(selection, required):
            for tpl in database.findAttributes(attributes, selection, _debug=_debug, exactType=exactType, **required):
                if index >= 0:
                    yield tuple(chain(tpl[:index], (database.name, ), tpl[index + 1:]))
                else:
                    yield tpl

    def findDiskItems(self, selection={}, _debug=None, exactType=False,
                      write=False, **required):
        for database in self._iterateDatabases({}, required):
            if not write or (not database.read_only and not database.builtin):
                for item in database.findDiskItems(selection, _debug=_debug,
                                                   exactType=exactType, **required):
                    yield item

    def createDiskItems(self, selection={}, _debug=None, exactType=False, **required):
        for database in self._iterateDatabases({}, required):
            if not database.read_only and not database.builtin:
                for item in database.createDiskItems(selection, _debug=_debug, exactType=exactType, **required):
                    yield item

    def createDiskItemFromFileName(self, fileName, defaultValue=Undefined):
        for database in self._iterateDatabases({}, {}):
            item = database.createDiskItemFromFileName(fileName, None)
            if item is not None:
                return item
        if defaultValue is Undefined:
            raise DatabaseError(
                _('No database can reference file "%(filename)s"') % {'filename': fileName})
        return defaultValue

    def changeDiskItemFormat(self, diskItem, newFormat):
        for database in self._iterateDatabases({}, {}):
            item = database.changeDiskItemFormat(diskItem, newFormat)
            if item is not None:
                return item
        return None

    def changeDiskItemFormatToSeries(self, diskItem):
        """
        Changes the format of the diskItem to Series of diskItem.format
        The number is extracted from the name to begin the name_serie list attribute. Other files with the same name but another number are searched in the parent directory to find the other numbers of the serie.
        """
        formatSeries = getFormat("Series of " + diskItem.format.name)
        if formatSeries is not None:
            parentDir = os.path.dirname(diskItem.fileName())
            filename = os.path.basename(diskItem.fileName())
            # get the number at the end of the filename : it is considered as
            # the name_serie
            regexp = re.compile("(.+?)(\d+)\.(.+)")
            match = regexp.match(filename)
            if match:
                name = match.group(1)
                ext = match.group(3)
                diskItem.format = formatSeries
                name_serie = []
                diskItem._setLocal("name_serie", name_serie)
                files = diskItem._files
                diskItem._files = []
                for f in files:
                    match = regexp.match(f)
                    if match:
                        namef = match.group(1)
                        numf = match.group(2)
                        extf = match.group(3)
                        diskItem._files.append(
                            os.path.join(os.path.dirname(f), namef + "#." + extf))
                # search the other numbers of the serie
                regexp = re.compile("^" + name + "(\d+)\." + ext + "$")
                for file in sorted(os.listdir(parentDir)):
                    match = regexp.match(file)
                    if match:
                        name_serie.append(match.group(1))
        return diskItem

    def getAttributesEdition(self, *types):
        editable = set()
        values = {
            '_database': tuple((i.name for i in six.itervalues(self._databases)))}
        declared = set()
        for database in six.itervalues(self._databases):
            e, d, dcl = database.getAttributesEdition(*types)
            editable.update(e)
            declared.update(dcl)
            for a, v in six.iteritems(d):
                values.setdefault(a, set()).update(v)
        return editable, values, declared

    def getTypeChildren(self, *types):
        if self._databases:
            return set(chain(*(d.getTypeChildren(*types) for d in six.itervalues(self._databases))))
        return ()

    def getTypesKeysAttributes(self, *types):
        if self._databases:
            # Combine attributes from databases but try to keep the order (not using only a set)
            # because this order is used to build combos on graphical interface
            result = []
            set_result = set()
            for d in six.itervalues(self._databases):
                for a in d.getTypesKeysAttributes(*types):
                    if a not in set_result:
                        result.append(a)
                        set_result.add(a)
            return result
        return []

    def getTypesFormats(self, *types):
        if self._databases:
            return set(chain(*(d.getTypesFormats(*types) for d in six.itervalues(self._databases))))
        return ()

    def currentThreadCleanup(self):
        for database in self._iterateDatabases({}, {}):
            database.currentThreadCleanup()

    def newFormat(self, name, patterns):
        for database in self._iterateDatabases({}, {}):
            database.newFormat(name, patterns)

    def findReferentialNeighbours(self, ref, bidirectional=True,
                                  flat_output=False):
        allrefs = []
        alltrsfs = {}
        allneigh = []
        for database in self._iterateDatabases({}, {}):
            neighbours = database.findReferentialNeighbours(
                ref, bidirectional=bidirectional, flat_output=flat_output)
            if flat_output:
                allneigh += neighbours
            else:
                (refs, transfs) = neighbours
                allrefs.extend(refs)
                for r, p in six.iteritems(transfs):
                    alltrsfs.setdefault(r, []).extend(p)
        if flat_output:
            return allneigh
        else:
            return (allrefs, alltrsfs)
