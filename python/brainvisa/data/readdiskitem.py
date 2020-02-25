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
This module defines the class :py:class:`ReadDiskItem` which is a subclass :py:class:`brainvisa.data.neuroData.Parameter`.
It is used to define an input data file as a parameter in a :py:class:`brainvisa.processes.Process` :py:class:`brainvisa.data.neuroData.Signature`.
"""
from __future__ import print_function
from __future__ import absolute_import
import os
import operator
# from soma.debug import print_stack
from soma.path import split_query_string
from soma.undefined import Undefined
from brainvisa.data.neuroData import Parameter
from brainvisa.processes import getDiskItemType
import brainvisa.processes
from brainvisa.data.neuroDiskItems import getFormat, getFormats, DiskItem, isSameDiskItemType, File, Directory
from brainvisa.processing.neuroException import HTMLMessage
import six
import sys
from functools import reduce

if sys.version_info[0] >= 3:

    def to_list(thing):
        return list(thing)
else:
    def to_list(thing):
        return thing

#----------------------------------------------------------------------------
def diskItemFilter(database, diskItem, required, explainRejection=False):
    if diskItem.type is not None:
        types = database.getTypeChildren(
            *database.getAttributeValues('_type', {}, required))
        if types and diskItem.type.name not in types:
            if explainRejection:
                return 'DiskItem type ' + repr(diskItem.type.name) + ' is not in ' + repr(tuple(types))
            return False
    formats = database.getAttributeValues('_format', {}, required)
    if formats and diskItem.format is not None:
        if diskItem.format.name not in formats:
            if explainRejection:
                if diskItem.format is None:
                    value = None
                else:
                    value = diskItem.format.name
                return 'DiskItem format ' + repr(value) + ' is not in ' + repr(tuple(formats))
            return False
    for key in required:
        if key in ('_type', '_format', '_declared_attributes_location'):
            continue
        values = database.getAttributeValues(key, {}, required)
        itemValue = diskItem.get(key, '')
        if (key == 'name_serie'):
            if itemValue != values:
                if explainRejection:
                    return 'DiskItem attribute ' + repr(key) + ' = ' + repr(itemValue) + ' != ' + repr(values)
                return False
        else:
            if itemValue not in values:
                if explainRejection:
                    return 'DiskItem attribute ' + repr(key) + ' = ' + repr(itemValue) + ' is not in ' + repr(tuple(values))
                return False
    return True


#----------------------------------------------------------------------------


class ReadDiskItem(Parameter):

    """
    The expected value for this parameter must be a readable :py:class:`brainvisa.data.neuroDiskItems.DiskItem`.
    This parameter type uses BrainVISA data organization to select possible files.

    :Syntax:

    ::

      ReadDiskItem( file_type_name, formats [, required_attributes, enableConversion=1, ignoreAttributes=0 ])
      formats <- format_name
      formats <- [ format_name, ... ]
      required_attributes <- { name : value, ...}

    file_type_name enables to select files of a specific type, that is to say DiskItem objects whose type is either file_name_type or a derived type. The formats list gives the exhaustive list of accepted formats for this parameter. But if there are some converters ( see the section called “Role”) from other formats to one of the accepted formats, they will be accepted too because BrainVISA can automatically convert the parameter (if enableConversion value is 1, which is the default). Warning : the type and formats given in parameters of ReadDiskItem constructor must have been defined in BrainVISA types and hierarchies files. required_attributes enables to add some conditions on the parameter value : it will have to match the given attributes value.

    This method of files selection ease file selection by showing the user only files that matches type and format required for this parameter. It also enables BrainVISA to automatically fill some parameters values. The ReadDiskItem class has methods to search matching diskitems in BrainVISA databases :

      * :py:meth:`ReadDiskItem.findItems(\<database directory diskitem\> <ReadDiskItem.findItems>`, <attributes>) : this method returns a list of diskitems that exist in that database and match type, format and required attributes of the parameter. It is possible to specify additional attributes in the method parameters. Found items will have the selected value for these attributes if they have the attribute, but these attributes are not mandatory. That's the difference with the required attributes set in the constructor.
      * :py:meth:`ReadDiskItem.findValues(\<value\>) <ReadDiskItem.findValues>` : this method searches diskitems matching the value in parameter. This value can be a diskitem, a filename, a dictionary of attributes.
      * :py:meth:`ReadDiskItem.findValue(\<value\>) <ReadDiskItem.findValue>` : this method returns the best among possible value, that is to say with the more common attributes, highest priority. If there is an ambiguity, it returns None.

    **Examples**

    >>> ReadDiskItem( 'Volume 3D', [ 'GIS Image', 'VIDA image' ] )
    >>> ReadDiskItem( 'Cortical folds graph', 'Graph', requiredAttributes = { 'labelled' : 'No', 'side' : 'left'} )


    In the first example, the parameter will accept only a file whose type is 3D Volume and format is either GIS image or VIDA image, or a format that can be converted to GIS or VIDA image. These types and formats must have been defined first. In the second example, the parameter value type must be "Cortical folds graph", its format must be "Graph". The required attributes add some conditions : the graph isn't labelled and represents the left hemisphere.
    """

    def __init__(self, diskItemType, formats, requiredAttributes={},
                enableConversion=True, ignoreAttributes=False, _debug=None, 
                exactType=False, section=None, enableMultiResolution=False ):
        Parameter.__init__(self, section)
        self._debug = _debug
        self.type = getDiskItemType(diskItemType)
        formatsList = to_list(getFormats(formats))
        if len(formatsList) != 0:
            self.formats = (formatsList[0], ) + tuple(sorted(formatsList))
        else:
            self.formats = ()
        self.enableConversion = enableConversion
        self.exactType = exactType
        self.enableMultiResolution = enableMultiResolution
        self._formatsWithConversion = None
        self.requiredAttributes = requiredAttributes
        self._write = False
        # self._modified = 0
        self.ignoreAttributes = ignoreAttributes
        self._selectedAttributes = {}
        self.valueLinkedNotifier.add(self.valueLinked)

    _formatsAndConversionCache = {}

    def _getDatabase(self):
        '''Returns the database this disk item belongs to
        '''
        # WARNING: don't import earlier to prevent a circular inclusion!
        from brainvisa.data import neuroHierarchy
        return neuroHierarchy.databases
    database = property(_getDatabase)

    # Allow direct affectation to requiredAttributes for backward compatibility
    def _getRequiredAttributes(self):
        #_debug = self._debug
        # if _debug is not None:
            # print('!_getRequiredAttributes!', self, self.type, self.formats,
            # self.enableConversion, file=_debug)
        if self._requiredAttributes['_format'] is None:
            cache = self._formatsAndConversionCache.get(
                (self.type.name, self.formats))
            # if _debug is not None:
        # print('!_getRequiredAttributes! 1', cache, file=_debug)
            if cache is None:
                formats = set(self.database.formats.getFormat(
                    f.name, f).name for f in self.formats)
                # if _debug is not None:
                 # print('!_getRequiredAttributes! 2', formats, file=_debug)
                formatsWithConversion = set()
                any = getDiskItemType('Any type')
                for f in getFormats(self.formats):
                    convs = brainvisa.processes.getConvertersTo(
                        (any, f), checkUpdate=False)
                    convs.update(brainvisa.processes.getConvertersTo(
                        (self.type, f), keepType=0, checkUpdate=False))
                    # if _debug is not None:
                      # print('!_getRequiredAttributes! 3', self.type,
                      # object.__repr__( self.type ), f, object.__repr__( f ),
                      # convs, file=_debug)
                    for type_format, converter in six.iteritems(convs):
                        typ, format = type_format
                        formatName = self.database.formats.getFormat(
                            format.name, format).name
                        # if _debug is not None:
                          # print('!_getRequiredAttributes! 4', formatName,
                          # file=_debug)
                        if formatName not in formats:
                            formatsWithConversion.add(formatName)
                cache = (formats, formatsWithConversion)
                self._formatsAndConversionCache[
                    (self.type.name, self.formats)] = cache
            formats, self._formatsWithConversion = cache
            # if _debug is not None:
                # print('!_getRequiredAttributes! 5', formats,
                # self._formatsWithConversion, file=_debug)
            if self.enableConversion:
                self._requiredAttributes['_format'] = self._formatsWithConversion.union(
                    formats)
            else:
                self._requiredAttributes['_format'] = formats
        self._requiredAttributes['_type'] = self.type.name
        # if _debug is not None:
            # print('!_getRequiredAttributes! 6', self._requiredAttributes[
            # '_format' ], file=_debug)
        return self._requiredAttributes

    def _setRequiredAttributes(self, value):
        self._requiredAttributes = value.copy()
        self._requiredAttributes['_type'] = self.type.name
        self._requiredAttributes['_format'] = None
    requiredAttributes = property(
        _getRequiredAttributes, _setRequiredAttributes)

    def valueLinked(self, parameterized, name, value):
        """This method is a callback called when the valueLinkedNotifier is activated.
        This notifier is shared between this parameter and the initial parameter in the static signature of the process.
        So when this function is called self is the initial parameter in the static signature.
        That why self is not used in this function.
        """
        if isinstance(value, DiskItem):
            parameterized.signature[
                name]._selectedAttributes = value.hierarchyAttributes()
        elif isinstance(value, dict):
            parameterized.signature[name]._selectedAttributes = value
        else:
            parameterized.signature[name]._selectedAttributes = {}

    def checkValue(self, name, value):
        Parameter.checkValue(self, name, value)
        if ((value is not None) and (self.mandatory == True)):
            if not value.isReadable():
                raise RuntimeError(
                    HTMLMessage(_t_('the parameter <em>%s</em> is not readable or does not exist : %s') % (six.text_type(name), six.text_type(value))))

    def get_formats_order(self, database_dir):
          if database_dir in (None, ''):
              return self.formats
          from brainvisa.configuration import neuroConfig
          dbs = [d for d in neuroConfig.dataPath
                 if d.directory == database_dir]
          if len(dbs) != 1:
              return self.formats
          dbs = dbs[0]
          forder = getattr(dbs.expert_settings, 'preferred_formats_order',
                           None)
          if forder is None:
              return self.formats
          fdict = {}
          for f in self.formats:  # TODO: could use a cache for this dict
              fdict[f.name] = f
          hprio = [fdict[f] for f in forder if f in fdict]
          lprio = [f for f in self.formats if f not in hprio]
          return hprio + lprio

    def findValue(self, selection, requiredAttributes=None,
                  preferExisting=False, ignore_db_formats_sorting=False,
                  _debug=Undefined):
        '''Find the best matching value for the ReadDiskItem, according to the given selection criterions.

        The "best matching" criterion is the maximum number of common attributes with the selection, with required attributes satisfied.

        In case of WriteDiskItem, if preferExisting, also search for value already in database.

        If there is an ambiguity (no matches, or several equivalent matches), *None* is returned.

        Parameters
        ----------
        selection: diskitem, or dictionary, or str (filename)
        requiredAttributes: dictionary (optional)
        preferExisting: boolean
        ignore_db_formats_sorting: boolean
            by default, in Axon >= 4.6.2, formats are sorted according to
            database-specific formats orders, thus overriding process-specified
            formats orders. This flag allows to disable this behavior.
        _debug: file-like object (optional)

        Returns
        -------
        matching_value: :py:class:`DiskItem <brainvisa.data.neuroDiskItems.DiskItem>` instance, or *None*
        '''
        if _debug is Undefined:
            _debug = self._debug
        if selection is None:
            return None
        if requiredAttributes is None:
            requiredAttributes = self.requiredAttributes
        else:
            r = self.requiredAttributes.copy()
            r.update(requiredAttributes)
            requiredAttributes = r
        if _debug is not None:
            print('\n' + '-' * 70, file=_debug)
            print(self.__class__.__name__ +
                  '(\'' + str(self.type) + '\').findValue', file=_debug)
            if isinstance(selection, DiskItem):
                print('  value type = DiskItem', file=_debug)
                print('  fullPath = ', repr(selection), file=_debug)
                print('  type = ', repr(selection.type), file=_debug)
                print('  format = ', repr(selection.format), file=_debug)
                print('  attributes:', file=_debug)
                for n, v in selection.attributes().items():
                    print('   ', n, '=', repr(v), file=_debug)
            else:
                print('  value type =', type(selection), file=_debug)
                print('  value = ', selection, file=_debug)
            print('  required attributes:', file=_debug)
            for n, v in six.iteritems(requiredAttributes):
                print('   ', n, '=', repr(v), file=_debug)
            # print('- ' * 35, file=_debug)
            # print_stack( file=_debug )
            # print('- ' * 35, file=_debug)

        result = None
        fullSelection = None
        write = False
        if isinstance(selection, DiskItem):
            if selection.getHierarchy('_database') is None:
                # If DiskItem is not in a database, required attributes are
                # ignored (except _format)
                rr = {}
                if '_format' in requiredAttributes:
                    rr['_format'] = requiredAttributes['_format']
                requiredAttributes = rr

            if (selection.type is None or (selection.type is self.type) or
               (not self.exactType and (isSameDiskItemType( selection.type, self.type ) or isSameDiskItemType( self.type, selection.type )))) \
               and self.diskItemFilter(selection, requiredAttributes):
                result = selection

            else:
                if _debug is not None:
                    print('  DiskItem rejected because:', self.diskItemFilter(
                        selection, requiredAttributes, explainRejection=True), file=_debug)
                if selection._write:
                    if _debug is not None:
                        print(
                            '  DiskItem has the _write attribute set to True',
                              file=_debug)
                    write = True
                fullSelection = selection.globalAttributes()
                if selection.type is None:
                    fullSelection['_type'] = None
                else:
                    fullSelection['_type'] = selection.type.name

                if selection.format is None:
                    fullSelection['_format'] = None
                else:
                    fullSelection['_format'] = selection.format.name

        elif isinstance(selection, six.string_types):
            if selection.startswith('{'):
                # String value is a dictionary
                return self.findValue(eval(selection), requiredAttributes=requiredAttributes, _debug=_debug)
            fullSelection = None
            if selection == '':
                return None  # avoid using cwd
            selection, query_string = split_query_string(selection)
            fileName = os.path.normpath(os.path.abspath(selection))
            for database in self.database.iterDatabases():
                if fileName.startswith(database.directory + os.sep):
                    break
            else:
                database = self.database
            result = database.getDiskItemFromFileName(
                fileName + query_string, None)
            if result is None:
                if _debug is not None:
                    print('  DiskItem not found in databases', file=_debug)
                directory = getFormat('Directory') in self.formats
                result = database.createDiskItemFromFileName(
                    fileName + query_string, None, directory=directory)
                if result is None:
                    if _debug is not None:
                        print(
                            '  DiskItem not created in databases from file name',
                              file=_debug)
                    # WARNING FIXME QUESTION ??
                    # Denis 2018/08/07
                    # createDiskItemFromFileName() 3 lines earlier already
                    # calls createDiskItemFromFormatExtension(), so if we
                    # are here, createDiskItemFromFormatExtension can just not
                    # work, right ?
                    result = database.createDiskItemFromFormatExtension(
                        fileName + query_string, None)
                    if result is None:
                        if _debug is not None:
                            print(
                                '  DiskItem not created in databases from format extension', 
                                file=_debug)
                        if os.path.exists( fileName ):
                            from brainvisa.tools.aimsGlobals import aimsFileInfo
                            file_type = aimsFileInfo(fileName).get('file_type')
                            if _debug is not None:
                                print(
                                    '  aimsFileInfo returned file_type =', repr(
                                        file_type),
                                      file=_debug)
                            if file_type == 'DICOM':
                                if _debug is not None:
                                    print(
                                        '  creating DICOM DiskItem', file=_debug)
                                result = File(fileName + query_string, None)
                                result.format = getFormat('DICOM image')
                                result.type = None
                                result._files = [fileName]
                                result.readAndUpdateMinf()
                    else:
                        result.readAndUpdateMinf()
                else:
                    result.readAndUpdateMinf()
                    if _debug is not None:
                        print('  DiskItem created in databases', file=_debug)
                if result is None:
                    if _debug is not None:
                        print(
                            '  no format found for file name extension', file=_debug)
                    directoryFormat = getFormat('Directory')
                    if directoryFormat in self.formats:
                        # In this case, item is a directory
                        if _debug is not None:
                            print(
                                '  no extension ==> create Directory item', file=_debug)
                        result = Directory(fileName + query_string, None)
                        result.format = directoryFormat
                        result._files = [fileName]
                        result._identified = False
                        result.type = self.type
                        result.readAndUpdateMinf()
                elif _debug is not None:
                    print(
                        '  found matching format:', result.format, file=_debug)
            elif _debug is not None:
                print('  DiskItem found in databases', file=_debug)
            if result is not None:
                if result.type is None:
                    # Set the result type if this is not already done
                    result.type = self.type
                if result.getHierarchy('_database') is None:
                    # If DiskItem is not in a database, required attributes are
                    # ignored
                    requiredAttributes = {
                        '_format': requiredAttributes.get('_format')}
                    # if the diskitem format does not match the required
                    # format, and if required format contains Series of
                    # diskitem.format, try to change the format of the diskItem
                    # to a format series.
                    if not self.diskItemFilter(result, requiredAttributes):
                        if ("Series of " + result.format.name in requiredAttributes.get("_format")):
                            database.changeDiskItemFormatToSeries(result)
                if not self.diskItemFilter(result, requiredAttributes):
                    if _debug is not None:
                        print('  DiskItem rejected because:', self.diskItemFilter(
                            result, requiredAttributes, explainRejection=True), file=_debug)
                    result = None
            if result is None and self._parameterized is not None \
                and self._name is not None \
                    and not self._parameterized().isDefault(self._name):
                try:
                    result = database.createDiskItemFromFormatExtension(
                        selection + query_string)
                    if result is not None:
                        result.type = self.type
                except Exception:
                    pass
        elif isinstance(selection, dict):
            if '_declared_attributes_location' in list(selection.keys()):
                # keep it could cause problems because it should not be
                # compared between disk items
                del selection['_declared_attributes_location']
            else:
                pass
            fullSelection = dict(selection)

        if result is None and fullSelection is not None:
            values = []
            if preferExisting and (write or self._write):
                fullAttributes = fullSelection.copy()
                fullAttributes.update(requiredAttributes)
                values = list(self._findValues(fullSelection, fullAttributes,
                                               write=False,
                                               _debug=_debug))
            if not values:
                values = list(self._findValues(fullSelection, requiredAttributes,
                                               write=(write or self._write),
                                               _debug=_debug))

            if values:
                if len(values) == 1:
                    result = values[0]
                else:
                    # Find the item with the "smallest" "distance" from item
                    values = sorted((self.diskItemDistance(i, selection), i)
                                    for i in values)
                    if _debug is not None:
                        print(
                            '  findValue priority sorted items:', file=_debug)
                        for l in values:
                            print('   ', l, file=_debug)
                    if values[0][0] != values[1][0]:
                        result = values[0][1]
                    else:
                        refOrder, refDiskItem = values[0]
                        refHierarchy = refDiskItem.hierarchyAttributes()
                        # WARNING: this _declared_attributes_location attribute causes
                        # problems since it should not be compared between disk
                        # items
                        try:
                            del refHierarchy['_declared_attributes_location']
                        except KeyError:
                            pass
                        differentOnFormatOnly = [refDiskItem]
                        for checkOrder, checkDiskItem in values[1:]:
                            if checkOrder != refOrder:
                                break
                            checkHierarchy = checkDiskItem.hierarchyAttributes(
                            )
                            # WARNING: this _declared_attributes_location attribute causes
                            # problems since it should not be compared between
                            # disk items
                            try:
                                del checkHierarchy[
                                    '_declared_attributes_location']
                            except KeyError:
                                pass
                            if ((refHierarchy == checkHierarchy) and (refDiskItem.format.name != checkDiskItem.format.name)):
                                differentOnFormatOnly.append(checkDiskItem)
                            else:
                                differentOnFormatOnly = []
                                break
                        if differentOnFormatOnly:
                            formatsToTest = self.get_formats_order(
                                differentOnFormatOnly[0].getHierarchy(
                                    '_database'))
                            for preferredFormat in formatsToTest:
                                l = [
                                    i for i in differentOnFormatOnly if i.format is preferredFormat]
                                if l:
                                    result = l[0]
                                    break
                            if _debug is not None:
                                print(
                                    '  top priority values differ only by formats:',
                                      file=_debug)
                                for i in differentOnFormatOnly:
                                    print('   ', i.format, file=_debug)
                                if result:
                                    print(
                                        '  chosen format:', result.format, file=_debug)
                        elif _debug is not None:
                            print(
                                '  top priority values differ on ontology attributes ==> no selection on format', file=_debug)
                            print(
                                'ref   element:', refDiskItem.fullPath(), refHierarchy, file=_debug)
                            print(
                                'check element:', checkDiskItem.fullPath(), checkHierarchy, file=_debug)

        # this block of code was originally in WriteDiskItem.findValue().
        # We do not remember what it was exactly meant for, and did not do
        # correctly its job. We don't completely remove it because it might solve
        # a very specific situation, but we also fix it: check requiredAttributes,
        # and select preferred format instead of the first one.
        # (Denis 2015/10/09)
        if result is None and write and isinstance( selection, DiskItem ) and \
            (selection.type is None or selection.type is self.type
             or (not self.exactType
                 and isSameDiskItemType(selection.type, self.type))):
            format = requiredAttributes.get('_format') or self.formats[0]
            if _debug is not None:
                print(
                    '  No unique best selection found. But compatible input DiskItem. Checking format.', file=_debug)
                print('    Format:', format, file=_debug)
            if format in self.formats and format != selection.format:
                # check requiredAttributes
                sel_attr = selection.hierarchyAttributes()
                ok = True
                for attrib, value in six.iteritems(requiredAttributes):
                    if not attrib.startswith('_') and \
                            (attrib not in sel_attr or sel_attr[attrib] != value):
                        ok = False
                        break
                if _debug:
                    print('    checking RequiredAttributes:', ok, file=_debug)
                if ok:
                    result = self.database.changeDiskItemFormat(
                        selection, format.name)
                    if _debug is not None:
                        print(
                            '  selection is compatible with a different format, select: %s'
                          % format, file=_debug)

        if _debug is not None:
            print('-> findValue return', result, file=_debug)
            if result is not None:
                print('-> type:', result.type, file=_debug)
                print('-> format:', result.format, file=_debug)
                print('-> attributes:', file=_debug)
                for n, v in result.attributes().items():
                    print('->  ', n, '=', v, file=_debug)
            print('-' * 70 + '\n', file=_debug)
            _debug.flush()
        return result

    def diskItemDistance(self, diskItem, other):
        '''Returns a value that represents a sort of distance between two
           DiskItems.
            The distance is not a number but distances can be sorted.'''
        # Count the number of common hierarchy attributes
        if isinstance(other, DiskItem):
            if other.type is not None:
                other_type = other.type.name
            else:
                other_type = None
            other_priority = other.priority()
        else:
            other_type = other.get('_type')
            other_priority = 0
        if diskItem.type is not None:
            diskItem_type = diskItem.type.name
        else:
            diskItem_type = None
        if isinstance(other, DiskItem):
            getHierarchy = other.getHierarchy
            getNonHierarchy = other.getNonHierarchy
        else:
            getHierarchy = other.get
            getNonHierarchy = other.get
        filtered_out_attribs = set(
            ['_ontology', '_declared_attributes_location'])
        hierarchyCommon = reduce(
            operator.add,
          ((getHierarchy(n) == v)
           for n, v in six.iteritems(diskItem.hierarchyAttributes())
           if n not in filtered_out_attribs),
          (int(diskItem_type == other_type)))
        # Count the number of common non hierarchy attributes
        nonHierarchyCommon = reduce(
            operator.add,
          ((getNonHierarchy(n) == v)
           for n, v in six.iteritems(diskItem.nonHierarchyAttributes())),
          (int(diskItem_type == other_type)))
        if getattr(other, '_write', False) and diskItem.isReadable():
            readable = -1
        else:
            readable = 0
        return (-hierarchyCommon, other_priority - diskItem.priority(), -nonHierarchyCommon, readable)

    def findValues(self, selection, requiredAttributes={}, write=False,
                   _debug=Undefined):
        '''Find all DiskItems matching the selection criterions

        Parameters
        ----------
        selection: :py:class:`DiskItem <brainvisa.data.neuroDiskItems.DiskItem>` or dictionary
        requiredAttributes: dictionary (optional)
        write: bool (optional)
            if write is True, look for write diskitems
        _debug: file-like object (optional)
        '''
        return self._findValues(selection, requiredAttributes, write, _debug)

    def _findValues(self, selection, requiredAttributes, write, _debug=Undefined):
        if _debug is Undefined:
            _debug = self._debug
        if requiredAttributes is None:
            requiredAttributes = self.requiredAttributes
        keySelection = {}
        if selection:
            # in selection attributes, choose only key attributes because the
            # request must not be too restrictive to avoid failure. The results
            # will be sorted by distance to the selection later.
            keyAttributes = self.database.getTypesKeysAttributes(
                self.type.name)
            keySelection = dict((i, selection[i]) for i in keyAttributes
                                if i in selection)
        # type is required in database selection
        if '_type' not in keySelection:
            keySelection['_type'] = self.type.name
        readValues = (i for i in self.database.findDiskItems(
            keySelection, _debug=_debug, exactType=self.exactType,
            write=self._write, **requiredAttributes)
            if self.diskItemFilter(i, requiredAttributes))
        if write:
            # use selection attributes to create a new diskitem
            fullPaths = set()
            for item in readValues:
                fullPaths.add(item.fullPath())
                yield item
            requiredAttributes = dict(requiredAttributes)  # copy
            if '_type' not in requiredAttributes:
                # if selection is a diskitem with a different type as self
                requiredAttributes['_type'] = self.type.name
            if '_format' not in requiredAttributes:
                requiredAttributes['_format'] = self.formats
            # Do not allow formats that require a conversion in DiskItem
            # creation
            if self._formatsWithConversion:
                oldFormats = requiredAttributes.get('_format')
                if oldFormats is not None:
                    requiredAttributes['_format'] = [
                        i for i in oldFormats if i not in self._formatsWithConversion]
            for item in self.database.createDiskItems(selection, _debug=_debug, exactType=self.exactType, **requiredAttributes):
                if self.diskItemFilter(item, requiredAttributes):
                    if item.fullPath() not in fullPaths:
                        yield item
                elif _debug is not None:
                    print(' ', item, 'rejected because:', self.diskItemFilter(
                        item, requiredAttributes, explainRejection=True), file=_debug)
            if self._formatsWithConversion:
                requiredAttributes['_format'] = oldFormats
        else:
            for i in readValues:
                yield i

    def diskItemFilter(self, *args, **kwargs):
        return diskItemFilter(self.database, *args, **kwargs)
        # if diskItem.type is not None:
            # types = self.database.getTypeChildren( *self.database.getAttributeValues( '_type', {}, required ) )
            # if types and diskItem.type.name not in types:
                # if explainRejection:
                    # return 'DiskItem type ' + repr(diskItem.type.name) + ' is not in ' + repr( tuple(types) )
                # return False
        # formats = self.database.getAttributeValues( '_format', {}, required )
        # if formats and not(diskItem.format is None) :
            # if diskItem.format.name not in formats:
                # if explainRejection:
                    # if diskItem.format is None :
                        # value = None
                    # else :
                        # value = diskItem.format.name
                    # return 'DiskItem format ' + repr(value) + ' is not in ' + repr( tuple(formats) )
                # return False
        # for key in required:
            # if key in ( '_type', '_format' ): continue
            # values = self.database.getAttributeValues( key, {}, required )
            # itemValue = diskItem.get( key, Undefined )
            # if itemValue is Undefined or itemValue not in values:
                # if explainRejection:
                    # if itemValue is Undefined:
                        # return 'DiskItem do not have the required ' + repr( key ) + ' attribute'
                    # else:
                        # return 'DiskItem attribute ' + repr(key) + ' = ' + repr( itemValue ) + ' is not in ' + repr( tuple(values) )
                # return False
        # return True

    def typeInfo(self, translator=None):
        if translator:
            translate = translator.translate
        else:
            translate = _t_
        formats = ''
        for f in self.formats:
            if formats:
                formats += ', '
            formats += translate(f.name)
        return ((translate('Type'), translate(self.type.name)),
                (translate('Access'), translate('input')),
                (translate('Formats'), formats))

    def toolTipText(self, parameterName, documentation):
        result = '<center>' + parameterName
        if not self.mandatory:
            result += ' (' + _t_('optional') + ')'
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

    def editor(self, parent, name, context):
        # WARNING: don't import at the beginning of the module,
        # it would cause a circular inclusion
        from brainvisa.data.qtgui.readdiskitemGUI import DiskItemEditor
        return DiskItemEditor(self, parent, name, context=context,
                              write=self._write,
                              process=getattr(context, 'parameterized', None))

    def listEditor(self, parent, name, context):
        # WARNING: don't import at the beginning of the module,
        # it would cause a circular inclusion
        from brainvisa.data.qtgui.readdiskitemGUI import DiskItemListEditor
        return DiskItemListEditor(self, parent, name, context=context,
                                  write=self._write,
                                  process=getattr(context, 'parameterized', None))
