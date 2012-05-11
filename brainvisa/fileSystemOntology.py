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
This module contains classes defining Brainvisa **ontology rules** to manage a database directory. 

In Brainvisa ontology, adding to the types and formats definition, it is possible to define rules associating a data type and a path in a location and filename in a database directory. The classes in this module enable to define such rules. 

These rules describe the organization of data in the database filesystem. 
Thanks to this description, the name and place of a file allows to guess its type and some information about it, 
as for example the protocol, subject or acquisition associated to this data. 
It also makes it possible to write data in the database using the same rules, 
so the information can be retrieved when the data is reloaded later.

These ontology files that we called *hierarchy* files in Brainvisa are located in ``brainvisa/hierarchies`` directory and in the hierarchies directory of each toolbox. BrainVISA can use several hierarchies whose files are grouped in a directory named as the hierarchy.

The main class in this module is :py:class:`FileSystemOntology`. 
It represents a Brainvisa **hierarchy**, a set of rules that associate data types and data organization on the filesystem.

A rule is represented by the class :py:class:`ScannerRule`. 
Several classes inheriting from :py:class:`ScannerRuleBuilder` are used to associate ontology attributes to a rule.

:Inheritance diagram:

.. inheritance-diagram:: fileSystemOntology

:Classes:


"""
import types, sys, os, time
import neuroConfig
from brainvisa.processing.neuroException import *
from brainvisa import shelltools
from soma.sorted_dictionary import SortedDictionary
import neuroDiskItems
from brainvisa.multipleExecfile import MultipleExecfile

#----------------------------------------------------------------------------
class AttrValueFunction( object ):
  _msgBadValue = '<em>%s</em> is not a valid attribute value'

  def __init__( self, function_string, dependencies ):
    self.function_string = function_string
    self.function = eval( function_string )
    self.dependencies = dependencies
  
  def __getstate__( self ):
    return ( self.function_string, self.dependencies )
  
  def __setstate__( self, state ):
    self.function_string, self.dependencies = state
    self.function = eval( self.function_string )
  
  def getValue( self, diskItem, matchResult ):
    star = matchResult.get( 'filename_variable' )
    number = matchResult.get( 'name_serie' )
    return self.function( diskItem, star, number )

  percent = {
    'f': 'i.fileName()',
    'F': 'i.fullName()',
    'd': 'i.parent.fileName()',
    'D': 'i.parent.fullPath()',
    '*': 's',
    '#': 'n'
  }


#----------------------------------------------------------------------------
_attrValueFunctions = {}
def getAttrValue( value ):
  global _attrValueFunctions
  function = _attrValueFunctions.get( value )
  if function is not None: return function
  dependencies = []
  functionBegin = 'lambda i,s,n: '
  i = 0
  s = ''
  while i < len( value ):
    c = value[i]
    if c == '%':
      i += 1
      if i >= len( value ): raise ValueError( HTMLMessage(_t_(AttrValueFunction._msgBadValue) % value) )
      c = value[ i ]
      if c == '%':
        s += c
      else:
        if function: function += '+'
        else: function = functionBegin
        if s:
          function += "'"+s+"'+"
          s=''
        if c == '<':
          i += 1
          j = value.find( '>', i )
          if j == -1: raise ValueError( HTMLMessage(_t_(AttrValueFunction._msgBadValue) % value) )
          attributeName = value[i:j]
          function += 'i.get(\'' + attributeName + '\',"")'
          if attributeName not in dependencies:
            dependencies.append( attributeName )
          i=j
        else:
          percent = AttrValueFunction.percent.get( c )
          if percent:
            function += percent
          else: raise ValueError( HTMLMessage(_t_(AttrValueFunction._msgBadValue) % value) )
    elif c == "'":
      s += '\\\''
    else:
      s += c
    i += 1
  if function and s: function += "+'"+s+"'"
  if function:
    function = AttrValueFunction( function, dependencies )
    _attrValueFunctions[ value ] = function
    return function
  return value


#----------------------------------------------------------------------------
class ScannerRule( object ):
  """
  This class represents a hierarchy rule. It associates a filename pattern and ontology attributes. 
  
  :Attributes:
  
  .. py:attribute:: pattern
  
    The filename pattern for this rule. It is an instance of :py:class:`neuroDiskItems.BackwardCompatiblePattern`.
    
  .. py:attribute:: globalAttributes
  
    List of global attributes names and values (tuples). Global attributes are added with a :py:class:`SetAttr` builder.
  
  .. py:attribute:: localAttributes
  
    List of local attributes names and values (tuples). Local attributes are added with a :py:class:`SetWeakAttr` builder.
    
  .. py:attribute:: defaultAttributesValues
  
    Dictionary associating attribute names and default values. It can be added with a :py:class:`SetDefaultAttributeValue` builder.
  
  .. py:attribute:: type
  
    Data type associated to this rule. Instance of :py:class:`neuroDiskItems.DiskItemType`. 
    It can be added with a :py:class:`SetType` builder.
  
  .. py:attribute:: formats
  
    List of file formats associated to this rule, each format is an instance of :py:class:`neuroDiskItems.Format`.
    It can be added with a :py:class:`SetFormats` builder.
    
  .. py:attribute:: scanner
  
    When the rule pattern matches a directory, it can contain other elements. 
    In this case, this attribute is a :py:class:`DirectoryScanner` and it contains other rules describing the content of the directory.
    
  .. py:attribute:: itemName
  
    A name associated to this rule. It can be added with a :py:class:`SetName` builder.
    
  .. py:attribute:: priority
  
    This attribute can be added with a :py:class:`SetPriority` builder.
    
  .. py:attribute:: priorityOffset
    
    This attribute can be added with a :py:class:`SetPriorityOffset` builder.
    
  .. py:attribute:: fileNameAttribute
  
    This attribute can be added with a :py:class:`SetFileNameAttribute` or a :py:class:`SetFileNameStrongAttribute` builder.
    
  .. py:attribute:: fileNameAttributeIsWeak
  
    This attribute can be added with a :py:class:`SetFileNameAttribute` or a :py:class:`SetFileNameStrongAttribute` builder.
    
  .. py:attribute:: fileNameAttributeDefault
  
    Default value for the filename attribute.
    
  .. py:attribute:: nonMandatoryKeyAttributes
  
    This attribute can be added with a :py:class:`SetNonMandatoryKeyAttribute` builder.
    
  """
  def __init__( self, pattern ):
    self.pattern = pattern
    self.type = None
    self.formats = None
    self.globalAttributes = []
    self.localAttributes = []
    self.defaultAttributesValues = {}
    self.scanner = None
    self.itemName = None
    self.priority = None
    self.priorityOffset = 0
    self.nonMandatoryKeyAttributes = set()
    for fileNameAttribute in pattern.namedRegex():
      if fileNameAttribute != 'name_serie': break 
    else:
      fileNameAttribute = 'filename_variable'
    self.fileNameAttribute = fileNameAttribute
    self.fileNameAttributeIsWeak = 1
    
  def __getstate__( self ):
    state = {}
    for n in ( 'pattern', 'globalAttributes', 'localAttributes',
               'defaultAttributesValues','scanner',
               'itemName', 'priority', 'priorityOffset', 
               'fileNameAttribute', 'fileNameAttributeIsWeak',
               'nonMandatoryKeyAttributes' ):
      state[ n ] = getattr( self, n )
    if self.type is not None:
      state[ 'type' ] = self.type.id
    else:
      state[ 'type' ] = None
    if self.formats is not None:
      state[ 'formats' ] = [x.id for x in self.formats]
    else:
      state[ 'formats' ] = None
    return state

  def __setstate__( self, state ):
    for n in ( 'pattern', 'globalAttributes', 'localAttributes', 'scanner',
               'defaultAttributesValues', 'itemName', 'priority',
               'priorityOffset', 'fileNameAttribute', 'fileNameAttributeIsWeak',
               'nonMandatoryKeyAttributes' ):
      setattr( self, n, state[ n ] )
    t = state[ 'type' ]
    if t:
      self.type = neuroDiskItems.getDiskItemType( t )
    else:
      self.type = None
    t = state[ 'formats' ]
    if t:
      self.formats = [neuroDiskItems.getFormat(i) for i in t]
    else:
      self.formats = None


  def _getFormats( self ):
    return self.__formats
  
  
  def _setFormats( self, formats ):
    if formats is None:
      self.__formats = None
      self._formatsNameSet = set()
    else:
      self.__formats = formats
      # Ugly trick that will last until 'Graph' format is completely replaced by 'Graph and data'
      formatsName=[]
      for f in formats:
        if f.name!='Graph':
          formatsName.append(f.name)
        else:
          formatsName.append('Graph and data')
      self._formatsNameSet = set( formatsName )
  
  
  formats = property( _getFormats, _setFormats )

#----------------------------------------------------------------------------
class ScannerRuleBuilder( object ):
  """
  Base class for rule builders. 
  
  It defines a virtual method :py:meth:`build`. All derived class override this method.
  """
  def build( self, scannerRule ):
    """
    :param scannerRule: related :py:class:`ScannerRule`.
    """
    pass  


#----------------------------------------------------------------------------
class SetType( ScannerRuleBuilder ):
  """
  This builder set the :py:attr:`ScannerRule.type` attribute of the current rule.
  """
  def __init__( self, diskItemType ):
    """
    :param string diskItemType: data type.
    """
    self.type = neuroDiskItems.getDiskItemType( diskItemType )

  def build( self, scannerRule ):
    """
    Sets its data type to the given scannerRule. 
    
    If the type has associated formats, the :py:attr:`ScannerRule.formats` is also updated.
    """
    scannerRule.type = self.type
    # Set default formats
    if self.type.formats:
      if scannerRule.formats is None:
        if 'name_serie' in scannerRule.pattern.namedRegex():
          scannerRule.formats = map( neuroDiskItems.changeToFormatSeries,
                                     self.type.formats )
        else:
          scannerRule.formats = self.type.formats
        scannerRule.formatNamesInSet = set( (f.name for f in self.type.formats) )

  def __str__( self ):
    return "SetType('"+self.type.name+"')"


#----------------------------------------------------------------------------
class SetName( ScannerRuleBuilder ):
  """
  This builder set the :py:attr:`ScannerRule.itemName` attribute of the current rule.
  """
  def __init__( self, name ):
    """
    :param string name: a name that will be associated to any diskitem that match the rule.
    """
    self.name = getAttrValue( name )

  def build( self, scannerRule ):
    scannerRule.itemName = self.name
  

#----------------------------------------------------------------------------
class SetAttr( ScannerRuleBuilder ):
  """
  This builder set the :py:attr:`ScannerRule.globalAttributes` attribute of the current rule.
  """
  def __init__( self, *params ):
    """
    :param params: list of attribute name followed by its value.
    """
    self.attributes = []
    i = 0
    while i+1 < len( params ):
      ( attr, value ) = ( params[ i ], params[ i+1 ] )
      # Check attribute name
      if type( attr )  is not types.StringType:
        raise TypeError( HTMLMessage(_t_('<em><code>%s</code></em> is not a valid attribute name') % str( attr )) )
      # Check attribute value
      if type( value ) is types.StringType:
        value = getAttrValue( value )
      self.attributes.append( ( attr, value ) )
      i += 2
    if i != len( params ):
      raise ValueError( HTMLMessage(_t_('missing value for attribute <em>%s</em>') % str( params[ -1 ] )) )

  def build( self, scannerRule ):
    scannerRule.globalAttributes += self.attributes


#----------------------------------------------------------------------------
class SetWeakAttr( SetAttr ):
  """
  This builder set the :py:attr:`ScannerRule.localAttributes` attribute of the current rule.
  """

  def build( self, scannerRule ):
    scannerRule.localAttributes += self.attributes
  


#----------------------------------------------------------------------------
class SetDefaultAttributeValue( ScannerRuleBuilder ):
  """
  This builder adds a new attribute value in the :py:attr:`ScannerRule.defaultAttributesValues` map of the current rule.
  """
  def __init__( self, attribute, value ):
    """
    :param string attribute: name of the attribute
    :param string value: default value of the attribute.
    """
    self.attribute = attribute
    self.value = value
  
  def build( self, scannerRule ):
    scannerRule.defaultAttributesValues[ self.attribute ] = self.value



#----------------------------------------------------------------------------
class SetNonMandatoryKeyAttribute( ScannerRuleBuilder ):
  """
  This builder adds new attributes names in the :py:attr:`ScannerRule.nonMandatoryKeyAttributes` list of the current rule.
  """
  def __init__( self, *attributes ):
    """
    :param attributes: list of attributes names that are not mandatory key attributes. 
    """
    self.attributes = attributes
  
  def build( self, scannerRule ):
    scannerRule.nonMandatoryKeyAttributes.update( self.attributes )


#----------------------------------------------------------------------------
class SetContent( ScannerRuleBuilder ):
  """
  This builder assumes that the current rule pattern is matches a directory. 
  As a directory can contain other files, a new :py:class:`DirectoryScanner` is created 
  and set as the :py:attr:`ScannerRule.scanner` attribute of the current rule.
  This directory scanner contains the rules defined to describe the content of this directory.
  """
  def __init__( self, *params ):
    """
    :param params: list of rules describing the content of a directory: 
      several filename patterns followed by associated rule builders.
    """
    scannerRules = []
    i = 0
    while i < len( params ):
      filterValue = params[ i ]
      rule = ScannerRule( neuroDiskItems.BackwardCompatiblePattern( filterValue ) )
      i += 1
      while i < len( params ):
        builder = params[ i ]
        if isinstance( builder, ScannerRuleBuilder ):
          builder.build( rule )
        else:
          i -= 1
          break
        i += 1
      scannerRules.append( rule )
      i += 1
    self.scanner = DirectoryScanner( scannerRules )
    
  def build( self, scannerRule ):
    # Only directories can have a content
    scannerRule.pattern.fileType = neuroDiskItems.Directory
    scannerRule.scanner = self.scanner


#----------------------------------------------------------------------------
class SetPriority( ScannerRuleBuilder ):
  """
  This builder set the :py:attr:`ScannerRule.priority` attribute of the current rule.
  """
  def __init__( self, priority ):
    self.priority = priority
  
  def build( self, scannerRule ):
    scannerRule.priority = self.priority


#----------------------------------------------------------------------------
class SetPriorityOffset( ScannerRuleBuilder ):
  """
  This builder set the :py:attr:`ScannerRule.priorityOffset` attribute of the current rule.
  """
  def __init__( self, priorityOffset ):
    self.priorityOffset = priorityOffset
  
  def build( self, scannerRule ):
    scannerRule.priorityOffset = self.priorityOffset

  
#----------------------------------------------------------------------------
class SetFormats( ScannerRuleBuilder ):
  """
  This builder set the :py:attr:`ScannerRule.formats` attribute of the current rule.
  """
  def __init__( self, formats ):
    """
    :param formats: list of formats names that will be associated to the current pattern.
    """
    self.formats = neuroDiskItems.getFormats( formats )
  
  def build( self, scannerRule ):
    if scannerRule.pattern.number:
      scannerRule.formats = map( neuroDiskItems.changeToFormatSeries, 
                                 self.formats )
    else:
      scannerRule.formats = self.formats
    scannerRule.formatNamesInSet = set( (f.name for f in scannerRule.formats) )

  
#----------------------------------------------------------------------------
class SetFileNameAttribute( ScannerRuleBuilder ):
  """
  This builder set the :py:attr:`ScannerRule.fileNameAttribute` and :py:attr:`ScannerRule.fileNameAttributeDefault` attributes of the current rule.
  The :py:attr:`ScannerRule.fileNameAttributeIsWeak` attribute is set to 1.
  """
  def __init__( self, attribute, defaultValue=None ):
    """
    :param string attribute: name of the attribute
    :param string defaultValue: a default value for this attribute.
    """
    self.attribute = str( attribute )
    self.default = defaultValue
  
  def build( self, scannerRule ):
    scannerRule.fileNameAttribute = self.attribute
    scannerRule.fileNameAttributeIsWeak = 1
    scannerRule.fileNameAttributeDefault = self.default

#----------------------------------------------------------------------------
class SetFileNameStrongAttribute( ScannerRuleBuilder ):
  """
  This builder set the :py:attr:`ScannerRule.fileNameAttribute` and :py:attr:`ScannerRule.fileNameAttributeDefault` attributes of the current rule.
  The :py:attr:`ScannerRule.fileNameAttributeIsWeak` attribute is set to 0.
  """
  def __init__( self, attribute, defaultValue=None ):
    """
    :param string attribute: name of the attribute
    :param string defaultValue: a default value for this attribute.
    """
    self.attribute = str( attribute )
    self.default = defaultValue
  
  def build( self, scannerRule ):
    scannerRule.fileNameAttribute = self.attribute
    scannerRule.fileNameAttributeIsWeak = 0
    scannerRule.fileNameAttributeDefault = self.default


#----------------------------------------------------------------------------
class DirectoryScanner( object ):
  """
  This object contains a list of :py:class:`ScannerRule` describing the content of a directory.
  
  :Attributes:
  
  .. py:attribute:: rules
  
    The list of :py:class:`ScannerRule` describing the content of the directory.
    
  .. py:attribute:: possibleTypes
  
    Dictionary containing the data types associated to its rules as keys. Values are always 1. 
  
  :Methods:
  
  """
  def __init__( self, scannerRules ):
    self.rules = scannerRules
    # Set possible types
    self.possibleTypes = {}
    for rule in self.rules:
      t = rule.type
      while t:
        self.possibleTypes[ t ] = 1
        t = t.parent
      if rule.scanner:
        self.possibleTypes.update( rule.scanner.possibleTypes )

  def __getstate__( self ):
    return {
      'rules': self.rules,
      'possibleTypes': map( lambda x: x.id, self.possibleTypes.keys() )
    }
    
  def __setstate__( self, state ):
    self.rules = state[ 'rules' ]
    self.possibleTypes = {}
    for t in state[ 'possibleTypes' ]:
      self.possibleTypes[ neuroDiskItems.getDiskItemType( t ) ] = 1
  
  def scan( self, directory ):
    """
    Scans a directory and returns the list of diskitem that it contain. 
    The diskitems that match ontology rules get corresponding ontology attributes.
    """
    debug = neuroConfig.debugHierarchyScanning
    groups={}
    formatGroups={}
    unknownGroups={}
    known = []
    unknown = []
    for item in directory:
      if item.name[-5: ] == '.minf':
        if debug:
          print >> debug, '-> Skiping', item
        continue
      if debug:
        print >> debug, '-> Examining', item
        print >> debug, '   time:', time.ctime()
        print >> debug, '   attributes:'
        for n, v in item.attributes().items():
          print >> debug, '    ', n, '=', repr( v )
      checkedFormats = {}
      identified= 0
      for rule in self.rules:
        # Check item format and rule matching
        matchDict = None
        if rule.formats is None:
          # No format list check only pattern
          position = 0
          if debug: print >> debug, '   rule (without formats list)', rule.pattern.pattern
          matchDict = rule.pattern.match( item )
          if matchDict is not None:
            if debug: print >> debug, '   -> matched'
            known.append( item )
        else:
          # Only formats in self.formats are allowed for this rule
          for format in rule.formats:
            # Check if format as already been checked
            matchFormat = checkedFormats.get( format, 1 )
            if matchFormat == 1:
              # Check if file/directory name match format
              matchFormat = format.match( item, returnPosition=1 )
              checkedFormats[ format ] = matchFormat
            if matchFormat:
              position = matchFormat[ 1 ]
              matchFormat = matchFormat[ 0 ]
              # Remove format prefix and sufix
              oldName = item.name
              item.name = format.formatedName( item, matchFormat )
              
              # Only one item is created for each ( item.name, item.format ) couple.
              # Items are grouped with format.group() method
              formatId = ( format, item.name )
              groupedItem = formatGroups.get( formatId )
              if groupedItem is not None:
                if debug: print >> debug, '   -> grouped with ', groupedItem, 'at position', position
                item = format.group( groupedItem, item, position = position )
                formatGroups[ formatId ] = item
                groupId = ( item.name, item.type, item.format )
                groups[ groupId ] = item
                # item is merged into groupedItem (wich is identified). Therefore further
                # identification for item is useless.
                identified = 1
                break

              # Check if file/directory name without format prefix and sufix
              # match the current rule pattern
              if debug: print >> debug, '   rule', rule.pattern.pattern
              matchDict = rule.pattern.match( item )
              if matchDict is not None:
                if debug: print >> debug, '   -> matched'
                format.setFormat( item, ( rule, matchDict ) )
                # Set the definite name of the item
                if rule.itemName:
                  if isinstance( rule.itemName, AttrValueFunction ):
                    item.name = rule.itemName.getValue( item, matchDict )
                  else:
                    item.name = rule.itemName
                if debug: print >> debug, '     item name set to', repr( item.name )
                # Only one item is created for each ( item.name, item.type, item.format ) triplet.
                # Items are grouped with format.group() method
                groupId = ( item.name, rule.type, item.format )
                groupedItem = groups.get( groupId )
                if groupedItem is not None:
                  if debug: print >> debug, '   -> grouped with ', groupedItem, 'at position', position
                  item = format.group( groupedItem, item, position = position, matchRule=matchDict )
                  groups[ groupId ] = item
                  # item is merged into groupedItem (wich is identified). Therefore further
                  # identification for item is useless.
                  identified = 1
                else:
                  formatGroups[ formatId ] = item
                  # A new ( item.name, item.type, item.format ) triplet is created
                  groups[ groupId ] = item
                # No more format checked
                break
              else:
                # The rule pattern is not matched for that format, the item name is restored
                item.name = oldName
          if not identified and item.format is None:
           # No format in self.formats allow self.pattern to match, the rule is rejected
            continue

        # If all has been done for this item, go to the next item              
        if identified: break

        # Check if the current rule matched
        if matchDict is not None:
        
          # Set item type (and possibly some attributes)
          if rule.type:
            rule.type.setType( item, matchDict, position )
        
          # Set attributes
          star = matchDict.get( rule.fileNameAttribute, '' )
          if debug:
            if rule.fileNameAttributeIsWeak:
              debug.write( '   Setting local attribute: ' )
            else:
              debug.write( '   Setting global attribute: ' )
            print >> debug, rule.fileNameAttribute, '=', repr( star )
          if rule.fileNameAttributeIsWeak:
            item._setLocal( rule.fileNameAttribute, star )
          else:
            item._setGlobal( rule.fileNameAttribute, star )
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

          # Set scanner
          item.scanner = rule.scanner

          # Set priority
          item.setPriority( rule.priority, priorityOffset=rule.priorityOffset )

          if debug:
            print >> debug, '   identified as', item.name, 'by rule', rule.pattern
            if rule.scanner is None:
              print >> debug, '     rule has no scanner'
            else:
              print >> debug, '     rule scanner:', ', '.join( [i.pattern.pattern for i in rule.scanner.rules] )
                              
          # A matching rule has been found, do not inspect other rules
          identified = 1
          break
      # After for rule in ... 
      # if item is not identified, try to find its format accoding to filename and group files that are part of item format
      if not identified:
        if debug: print >> debug, '     -> Not identified:', item
        item.findFormat()
        if item.format:
          formatId = ( item.format, item.name )
          if not unknownGroups.get(formatId, None):
            # register a group for this format
            unknownGroups[formatId]=item
            unknown.append( item )
      
    # Correct items if necessary
    known += groups.values()
    for item in known:
      if item.format: item.format.postProcessing( item )
      item._identified = True
    return [ i.setFormatAndTypeAttributes() for i in known + unknown ]
 
  def attributesDependencies( self, parentAttributes, result ):
    allRulesAttributes = []
    for rule in self.rules:
      currentAttributes = map( lambda x: x[0], rule.globalAttributes + rule.localAttributes )
      if rule.fileNameAttribute != 'filename_variable':
        currentAttributes.append( rule.fileNameAttribute )
      allRulesAttributes = currentAttributes
      for attribute in currentAttributes:
        if attribute in ( 'name_serie', ):
          continue
        dependencies = result.get( attribute, [] )
        for parent in parentAttributes:
          if parent not in dependencies + [ attribute ]:
            dependencies.append( parent )
          for grandParent in result.get( parent, [] ):
            if grandParent not in dependencies + [ attribute ]:
              dependencies.append( grandParent )
        if dependencies: result[ attribute ] = dependencies
    for rule in self.rules:
      if rule.scanner is not None:
        rule.scanner.attributesDependencies( currentAttributes, result )

  def attributesValues( self, result ):
    for rule in self.rules:
      for name, value in  [(rule.fileNameAttribute,getAttrValue( '%*' ))] + rule.globalAttributes + rule.localAttributes:
        if name == 'filename_variable': continue
        values = result.get( name, [] )
        if value not in values:
          values.append( value )
        result[ name ] = values
      if rule.scanner is not None:
        rule.scanner.attributesValues( result )


#----------------------------------------------------------------------------
class FileSystemOntology( object ):
  """
  This class represents a Brainvisa hierarchy, that is to say a set of rules associating data types and filenames.
  
  The right way to use this class is to use the :py:meth:`get` method 
  to get an instance of this class for a specific hierarchy in order to create only one instance for each hierarchy.
  
  :Attributes:
  
  .. py:attribute:: name
  
    The name of the hierarchy. It is the name of the directory containing the hierachy files, under the *hierarchies* directory.
    
  .. py:attribute:: source
  
    List of source paths for this hierarchy. Indeed, the hierarchy files can be in several directories: in the main Brainvisa directory and in each toolbox directory.
    
  .. py:attribute:: content
  
    Content of the hierarchy as it is described in the hierarchy files.
    
  .. py:attribute:: typeToPatterns
  
    Map associating each data type (:py:class:`neuroDiskItems.FileType`) with a list of rules (:py:class:`ScannerRule`).
    
  .. py:attribute:: lastModification
    
    Date of last modification of the hierarchy files. This enables to detect ontology changes and to offer the user to update his databases.
  
  :Methods:
  
  """
  __instances = {}
  
  def __init__( self, source, directories ):
    # FileSystemOntology constructor is private. Use :py:meth:`get` instead.
    self.cacheName = None
    #if os.path.isdir( source ):
      ## Source is a directory => new (version 3.1 and later) multiple files
      ## definition of FSO
      #reader = self.__Reader()
      #reader.read( self, source )
    if os.path.isfile( source ):
      # Source is a file => old (prior to version 3.1) single file FSO (that was
      # called hierarchy)
      oldFSOContent = {}
      beforeError = _t_('in file system ontology <em>%s</em>') % str( p )
      execfile( source, globals(), oldFSOContent )
      self.content = oldFSOContent.get( 'hierarchy' )
      self.cacheName = oldFSOContent.get( 'cache' )
      self.lastModification = os.stat( source ).st_mtime
    # hierarchy is in several directories
    elif len(directories)>0 and os.path.isdir(directories[0]):
      reader = self.__Reader()
      reader.read( self, directories )
    else:
      raise RuntimeError( HTMLMessage(_t_( '<em>%s</em> is not a valid file system ontology' ) % ( str( source ),)) )
    self.source = directories #source
    dir, name = os.path.split( source )
    if dir == "": #in neuroConfig.fileSystemOntologiesPath:
      self.name = name
    else:
      self.name = source
    if self.cacheName is None:
      self.cacheName = self.name + '.fsd'

    # For each data type, build all the possible patterns in extenso
    self.typeToPatterns = SortedDictionary()
    stack = [ (r,) for r in [i for i in self.content if isinstance( i, SetContent)][0].scanner.rules ]
    while stack:
      rules = stack.pop( 0 )
      rule = rules[ -1 ]
      if rule.type is not None:
        ruleInExtenso = ScannerRule( neuroDiskItems.DictPattern( '/'.join( (r.pattern.pattern for r in rules) ) ) )
        ruleInExtenso.type = rule.type
        ruleInExtenso.formats = rule.formats
        ruleInExtenso.priority = rule.priority
        for r in rules:
          ruleInExtenso.globalAttributes += r.globalAttributes
          ruleInExtenso.defaultAttributesValues.update( r.defaultAttributesValues )
          ruleInExtenso.globalAttributes += r.globalAttributes
          d = None
          for i in r.localAttributes:
            for j in ruleInExtenso.localAttributes:
              if i[0] == j[0]:
                d = j
                break
          if d:
            ruleInExtenso.localAttributes.remove( d )
          ruleInExtenso.localAttributes += r.localAttributes
          ruleInExtenso.priorityOffset += r.priorityOffset
          ruleInExtenso.nonMandatoryKeyAttributes.update( r.nonMandatoryKeyAttributes )
        ruleInExtenso.itemName = rule.itemName
        self.typeToPatterns.setdefault( rule.type, [] ).append( ruleInExtenso )
      if rule.scanner:
        stack = [rules+(r,) for r in rule.scanner.rules] + stack

  def getOntologiesNames():
    """
    Lists all the ontologies names found in fileSystemOntologiesPath. 
    """
    ontologies=set()
    for fsoPath in neuroConfig.fileSystemOntologiesPath:
      _, dirnames, _ = os.walk(fsoPath).next()
      for ontology in dirnames:
        ontologies.add(ontology)
    return ontologies
  getOntologiesNames = staticmethod( getOntologiesNames )   
    
  def get( source ):
    '''
    Satic factory for creation of FileSystemOntology instances. The source can be:
    
    * The name of one of the FSO directories located in one of the "hierarchies" directories
      of neuroConfig.fileSystemOntologiesPath (for example 'brainvisa-3.1.0' is the main FSO).
    * The name of any FSO directory.
    * The name of an old-style (prior to version 3.1) hierarchy file.
    '''
    # Get the source file
    if source is None:
      source = 'brainvisa-3.0'
    # Keep backward compatibility with old <mainPath>/*Hierarchy.py files
    source = os.path.normpath( source )
    if source == os.path.normpath( os.path.join( neuroConfig.mainPath, 'shfjHierarchy.py' ) ):
      source = 'brainvisa-3.0'
    elif source == os.path.normpath( os.path.join( neuroConfig.mainPath, 'sharedHierarchy.py' ) ):
      source = 'shared' 
    elif source == os.path.normpath( os.path.join( neuroConfig.mainPath, 'shfjFlatHierarchy.py' ) ):
      source = 'flat' 

    # as hierarchy can be located in several directories, the fileSystemOntology will be created with a list of directories
    directories=[]
    if not os.path.isabs( source ) or os.path.exists( source ):
      source = os.path.basename( source ) # remove path if any
      for fsoPath in neuroConfig.fileSystemOntologiesPath:
        s = os.path.normpath( os.path.join( fsoPath, source ) )
        if os.path.exists( s ):
          #source = s
          #break
          directories.append(s)
    if len(directories) == 0:
      directories.append(source)
      
    # Check if the FSO instance have already been created
    result = FileSystemOntology.__instances.get( source )
    if result is None:
        result = FileSystemOntology( source, directories ) # source
        FileSystemOntology.__instances[ source ] = result
    return result
  get = staticmethod( get )

  def clear():
    FileSystemOntology.__instances={}
  clear=staticmethod( clear )
  #--------------------------------------------------------------------------
  class __Reader( MultipleExecfile ):
    """
    A reader for hierarchy files.
    
    It enables to use the functions *insert*, *insertFirst* and *insertLast* in these files.
    These functions are associated to the methods :py:meth:`insert`, :py:meth:`insertFirst` and :py:meth:`insertLast` of this class.
    """
    def __init__( self ):
      MultipleExecfile.__init__( self )
      self.fileExtensions.append( '.py' )
      self.localDict[ 'insert' ] = self.insert
      self.localDict[ 'insertFirst' ] = self.insertFirst
      self.localDict[ 'insertLast' ] = self.insertLast

    def read( self, fso, directories):
      """
      Reads the hiearchy files of an ontology.
      Set the value of *hierarchy* variable that should be defined in the hierarchy files as the content of the fso.
      
      :param fso: :py:class:`FileSystemOntoloy`
      :param directories: paths to the hierarchy files of this ontology.
      """
      self.includePath.update(directories)
      files=[]
      for directory in directories:
        files.extend(shelltools.filesFromShPatterns( os.path.join( directory, '*.py' ) ))
      files.sort()
      exc=self.execute( continue_on_error=True, *files )
      if exc:
        for e in exc:
          try:
            raise e
          except:
            showException(beforeError="Error while reading ontology "+ directory +": ")

      try:
        fso.content = self.localDict[ 'hierarchy' ]
      except Exception, e:
        msg = 'in filesystem ontology "' + directory + '": ' + e.message \
          + ', files=' + str( files )
        e.message = msg
        e.args = ( msg, ) + e.args[1:]
        raise
      fso.lastModification = max( neuroDiskItems.typesLastModification, max( (os.stat(f).st_mtime for f in files) ) )

    def insert( self, path, *content ):
      """
      Inserts rules in a :py:class:`DirectoryScanner` whose pattern matches *path*.
      """
      self._insert( False, False, path, *content )
    
    def insertLast( self, path, *content ):
      """
      Appends rules in a :py:class:`DirectoryScanner` whose pattern matches *path*.
      """
      self._insert( False, True, path, *content )

    def insertFirst( self, path, *content ):
      """
      Inserts rules in a :py:class:`DirectoryScanner` whose pattern matches *path* at the beginning of the list of rules.
      """
      self._insert( True, False, path, *content )

    def _insert( self, first, last, path, *content ):
#dbg#      print '!_insert! in', path, first, '(', self.localDict[ '__name__' ], ')'
      contentScanner = SetContent( *content ).scanner
      for ruleBuilder in self.localDict[ 'hierarchy' ]:
        if isinstance( ruleBuilder, SetContent ):
          scanner = ruleBuilder.scanner
          break
      parentScanners = [ scanner ]
      if path:
        if path[ -1 ] == '/': path = path[ :-1 ]
        currentPattern = [] #'!'
        for pattern in path.split( '/' ):
          currentPattern.append( pattern ) # '!'
          found= None
          for rule in scanner.rules:
            if rule.pattern.pattern == pattern:
              found = rule.scanner
              break
          if found is None:
            if pattern.find( '*' ) == -1:
#dbg#              print '!_insert!   creating', '/'.join( currentPattern )
              # Create a rule for that directory
              found = SetContent( pattern, SetContent() ).scanner
#dbg#              print '!_insert!     adding rules:', ', '.join( [r.pattern.pattern for r in found.rules] )
              scanner.rules += found.rules
              found = found.rules[0].scanner
            else:
              raise RuntimeError( HTMLMessage(_t_( 'invalid hierarchy path: <em>%s</em>' ) % (path,)) )
          scanner = found
          parentScanners.append( scanner )

      # Concatenate rules (updating hierarchy towards the leaves)
      stack = [ (scanner, contentScanner.rules ) ]
      while stack:
        scanner, rules = stack.pop()
        posCount = 0
        for rule in rules:
          found = False
          if rule.scanner is not None:
            for scannerRule in scanner.rules:
              if scannerRule.pattern.pattern == rule.pattern.pattern:
                found = True
                if scannerRule.scanner is None:
                  raise RuntimeError( _t_( 'Invalid redefinition of rule %(rule)s in file %(file)s' ) % { 'rule': rule.pattern.pattern, 'file': self.localDict[ '__name__' ] } )
                stack.append( ( scannerRule.scanner, rule.scanner.rules ) )
                scannerRule.scanner.possibleTypes.update( rule.scanner.possibleTypes )
                break
          if not found:
#dbg#            print '!_insert!   add', rule.pattern.pattern, first
            if not hasattr( scanner, '_lastpos' ):
              scanner._lastpos = len( scanner.rules )
            if first:
              scanner.rules.insert( posCount, rule )
              posCount += 1
              scanner._lastpos += 1
            elif last:
              scanner.rules.append( rule )
            else:
              scanner.rules.insert( scanner._lastpos, rule )
              scanner._lastpos += 1

      # Update parent possible types (updating hierarchy towards the root)
      for s in parentScanners:
        s.possibleTypes.update( contentScanner.possibleTypes )

  #def printOntology( self, file=sys.stdout ):
    #print >> file, '\n\n#' + '=' * 79        
    #print >> file, '#  Ontology:', self.name
    #print >> file, '#' + '=' * 79
    #allKeys = set()
    #tab = '  '
    #anyType = neuroDiskItems.getDiskItemType( 'Any type' )
    #for type, rules in self.typeToPatterns.iteritems():
      #print >> file
      #print >> file, '#' + '-' * 79
      #print >> file, 'newType( ' + repr(type.name) + ','
      #keys = []
      #for rule in rules:
        #ruleAttributes = set( rule.pattern.namedRegex() )
        #ruleAttributes.update( rule.pattern.attributes() )
        #for keyAttributes in keys:
          #if ruleAttributes.issubset( keyAttributes ):
            #break
          #elif keyAttributes and ruleAttributes.issuperset( keyAttributes ):
            #keys.remove( keyAttributes )
            #keys.append( ruleAttributes )
            #break
        #else:
          #keys.append( ruleAttributes )
        #allKeys.update( [tuple(i) for i in keys] )
      #for attributes in keys:
        #print >> file, tab + repr( tuple( attributes ) ) + ','
      #if type.parent is not None and type.parent is not anyType:
        #print >> file, tab + 'parent=' + repr(type.parent.name) + ','
      #print >> file, '),'
    #print >> file
    #print >> file, '# all FSO keys:'
    #for attributes in allKeys:
      #print >> file, '#' + tab + ', '.join([repr(i) for i in attributes])
  
  
  def printOntology( self, file=sys.stdout ):
    """
    Writes ontology information.
    """
    allKeys = set()
    tab = '  '
    anyType = neuroDiskItems.getDiskItemType( 'Any type' )
    ontology = { anyType.name: [ (), None ] }
    for type, rules in self.typeToPatterns.iteritems():
      keys = []
      for rule in rules:
        ruleAttributes = set( rule.pattern.namedRegex() )
        ruleAttributes.update( rule.pattern.attributes() )
        localAttributesValues = {}
        for n, v in rule.localAttributes:
          ev = localAttributesValues.get( n )
          if ev is None:
            localAttributesValues[ n ] = v
          elif ev != v:
            ruleAttributes.add( n )
        for keyAttributes in keys:
          if ruleAttributes.issubset( keyAttributes ):
            break
          elif keyAttributes and ruleAttributes.issuperset( keyAttributes ):
            keys.remove( keyAttributes )
            keys.append( ruleAttributes )
            break
        else:
          keys.append( ruleAttributes )
        allKeys.update( [tuple(i) for i in keys] )
      if type.parent:
        ontology[ type.name ] = [ keys, type.parent.name ]
      else:
        ontology[ type.name ] = [ keys, None ]
    for type in neuroDiskItems.diskItemTypes.itervalues():
      if not ontology.has_key( type.name ):
        if type.parent:
          ontology[ type.name ] = [ (), type.parent.name ]
        else:
          ontology[ type.name ] = [ (), None ]
        
    def keepAttribute( ontology, type, attribute ):
      try:
        parent = ontology[ type ][ 1 ]
      except KeyError:
        ontology
      if parent:
        if attribute in ontology[ parent ][ 0 ]:
          return False
        return keepAttribute( ontology, parent, attribute )
      return True
    for k, v in ontology.iteritems():
      v[ 0 ] = [i for i in v[0] if keepAttribute(ontology, k, i)]
    
    print >> file, '\n\n#' + '=' * 79        
    print >> file, '#  Ontology:', self.name
    print >> file, '#' + '=' * 79
    for typeName, ( attributes, parent ) in ontology.iteritems():
      print >> file
      print >> file, '#' + '-' * 79
      print >> file, 'newType( ' + repr(typeName) + ','
      for a in attributes:
        print >> file, tab + repr( tuple( a ) ) + ','
      if parent is not None:
        print >> file, tab + 'parent=' + repr(parent) + ','
      print >> file, '),'
    print >> file
    print >> file, '# all FSO keys:'
    for attributes in allKeys:
      print >> file, '#' + tab + ', '.join([repr(i) for i in attributes])

  def printFSO( self, file=sys.stdout ):
    print >> file, '\n\n#' + '=' * 79        
    print >> file, '#  File System Ontology:', self.name
    print >> file, '#' + '=' * 79
    tab = '  '
    for type, rules in self.typeToPatterns.iteritems():
      print >> file
      print >> file, '#' + '-' * 79
      print >> file, 'newRules(', repr(type.name), ','
      for rule in rules:
        file.write( tab + repr( rule.pattern.pattern ) + "," )
        if rule.priority or rule.priorityOffset or \
           rule.localAttributes or rule.formats is not type.formats:
          print >> file, ' {'
          if rule.formats is not type.formats:
            print >> file, tab * 2 + "'formats':", repr(rule.formats) + ','
          if rule.priority:
            print >> file, tab * 2 + "'priority':", repr( rule.priority ) + ','
          if rule.priorityOffset:
            print >> file, tab * 2 + "'priorityOffset':", repr( rule.priorityOffset ) + ','
          if rule.localAttributes:
            attributes = tuple(rule.pattern.namedRegex())
            print >> file, tab * 2 + "'attributes': {"
            for n, v in rule.localAttributes:
              if n in attributes: continue
              print >> file, tab * 3 + repr( n ) + ':', repr( v ) + ','
            print >> file, tab * 2 + '},'
          print >> file, tab + '},'
        else:
          print >> file
      print >> file, '),'
    print >> file
  
  
  def printFormats( self, file=sys.stdout ):
    """
    Prints information about formats.
    """
    for format in neuroDiskItems.formats.itervalues():
      output = 'newFormat( ' + repr( format.name ) + ', ( '
      for pattern in format.getPatterns().patterns:
        output +=  "'"
        if pattern.fileType is neuroDiskItems.Directory:
          output +=  'd|'
        dotIndex = pattern.pattern.find( '.' )
        if dotIndex != -1:
          output +=  pattern.pattern[ dotIndex+1 : ]
        else:
          output = '# ' + output +  '???'
        output +=  "', "
      output +=  ') )'
      print >> file, output
    print >> file
    
    for formatList in neuroDiskItems.formatLists.itervalues():
      print >> file, 'newFormatList( ' + repr( formatList.name ) + ', ' + repr( tuple( (f.name for f in formatList) ) ) + ' )'

