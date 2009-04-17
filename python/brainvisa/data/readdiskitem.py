import os, operator
#from soma.debug import print_stack
from soma.undefined import Undefined
from neuroData import Parameter
from neuroProcesses import getDiskItemType
import neuroProcesses
from neuroDiskItems import getFormat, getFormats, DiskItem, isSameDiskItemType
import neuroHierarchy
from neuroException import HTMLMessage
from brainvisa.data.qtgui.readdiskitemGUI import DiskItemEditor, DiskItemListEditor
from brainvisa.data.qtgui.diskItemBrowser import diskItemFilter

#----------------------------------------------------------------------------
class ReadDiskItem( Parameter ):
  def __init__( self, diskItemType, formats, requiredAttributes={},
                enableConversion=True, ignoreAttributes=False, _debug=None ):
    Parameter.__init__( self )
    self._debug = _debug
    self._formatsWithConverter = None
    self.type = getDiskItemType( diskItemType )
    self.formats = getFormats( formats )
    self.enableConversion = enableConversion
    self.requiredAttributes = requiredAttributes
    self._write = False
    #self._modified = 0
    self.ignoreAttributes = ignoreAttributes;
  
  
  def _getDatabase( self ):
    return neuroHierarchy.databases
  database = property( _getDatabase )
  
  
  # Allow direct affectation to requiredAttributes for backward compatibility
  def _getRequiredAttributes( self ):
    if self._formatsWithConverter is None:
      self._formatsWithConverter = {}
      self.requiredAttributes = self.requiredAttributes
    return self._requiredAttributes
    
  def _setRequiredAttributes( self, value ):
    self._requiredAttributes = value.copy()
    self._requiredAttributes[ '_type' ] = self.type.name
    formats = set( self.database.formats.getFormat( f.name, f ).name for f in self.formats )
    #if self._debug is not None:
      #print >> self._debug, '!_setRequiredAttributes!', self, self.type, 'formats', [f for f in self.formats]
    if self.enableConversion and self._formatsWithConverter is not None:
      self._formatsWithConverter = {}
      #if self._debug is not None:
        #print >> self._debug, '!_setRequiredAttributes!', self, self.type, 'conversion enabled'
      any = getDiskItemType( 'Any type' )
      for f in self.formats:
        #if self._debug is not None:
          #print >> self._debug, '!_setRequiredAttributes!', self, self.type, 'Examining converters to', f, '(' + repr( type(f) ) + ')', len( neuroProcesses._converters )
        for type_format, converter in neuroProcesses.getConvertersTo( ( any, f ) ).iteritems():
          typ, format = type_format
          formatName = self.database.formats.getFormat( format.name, format ).name
          #if self._debug is not None:
            #print >> self._debug, '!_setRequiredAttributes!', self, self.type, '  <--', formatName
          if formatName not in formats:
            self._formatsWithConverter[ formatName ] = converter
      formats.update( self._formatsWithConverter.iterkeys() )
    #elif self._debug is not None:
      #print >> self._debug, '!_setRequiredAttributes!', self, self.type, 'conversion disabled'
    self._requiredAttributes[ '_format' ] = formats
    #if self._debug is not None:
      #if self._formatsWithConverter:
        #print >> self._debug, '!_setRequiredAttributes!', self, self.type, '_formatsWithConverter', self._formatsWithConverter
      #print >> self._debug, '!_setRequiredAttributes!', self, self.type, '_requiredAttributes', self._requiredAttributes
  requiredAttributes = property( _getRequiredAttributes, _setRequiredAttributes )
  
  
  #def _getFormats( self ):
    #return self._formats
  #def _setFormats( self, formats ):
    #self._formats = getFormats( formats )
  #format = property( _getFormats, _setFormats )
  
  
  def checkValue( self, name, value ):
    Parameter.checkValue( self, name, value )
    if value is not None:
      if not value.isReadable():
        raise RuntimeError( HTMLMessage(_t_( '<em>%s</em> is not readable or does not exists' ) % unicode( value )) )


  def findValue( self, selection, requiredAttributes=None, _debug=Undefined ):
    if _debug is Undefined:
      _debug = self._debug
    if selection is None: return None
    if requiredAttributes is None:
      requiredAttributes = self.requiredAttributes
    else:
      r = self.requiredAttributes.copy()
      r.update( requiredAttributes )
      requiredAttributes = r
    if _debug is not None:
       print >> _debug, '\n' + '-' * 70
       print >> _debug, self.__class__.__name__ + '(\'' + str( self.type ) + '\').findValue'
       if isinstance( selection, DiskItem ):
         print >> _debug, '  value type = DiskItem'
         print >> _debug, '  fullPath = ', repr( selection )
         print >> _debug, '  type = ', repr( selection.type )
         print >> _debug, '  format = ', repr( selection.format )
         print >> _debug, '  attributes:'
         for n, v in selection.attributes().items():
           print >> _debug, '   ', n, '=', repr( v )
       else:
         print >> _debug, '  value type =', type( selection )
         print >> _debug, '  value = ', selection
       print >> _debug, '  required attributes:'
       for n, v in requiredAttributes.iteritems():
         print >> _debug, '   ', n, '=', repr( v )
       #print >> _debug, '- ' * 35
       #print_stack( file=_debug )
       #print >> _debug, '- ' * 35
    
    result = None
    fullSelection = None
    write = False
    if isinstance( selection, DiskItem ):
      if selection.getHierarchy( '_database' ) is None:
        # If DiskItem is not in a database, required attributes are ignored (except _format)
        rr = {}
        if requiredAttributes.has_key( '_format' ):
          rr[ '_format' ] = requiredAttributes[ '_format' ]
        requiredAttributes = rr
        
      if ( selection.type is None or isSameDiskItemType( selection.type, self.type ) or isSameDiskItemType( self.type, selection.type )) \
        and self.diskItemFilter( selection, requiredAttributes ):
          result = selection
          
      else:
        if _debug is not None:
          print >> _debug, '  DiskItem rejected because:', self.diskItemFilter( selection, requiredAttributes, explainRejection=True )
        if selection._write:
          if _debug is not None:
            print >> _debug, '  DiskItem has the _write attribute set to True'
          write = True
        fullSelection = selection.globalAttributes()
        if selection.type is None :
          fullSelection[ '_type' ] = None
        else :
          fullSelection[ '_type' ] = selection.type.name
          
        if selection.format is None :
          fullSelection[ '_format' ] = None
        else :
          fullSelection[ '_format' ] = selection.format.name
          
    elif isinstance( selection, basestring ):
      fullselection = None
      fileName = os.path.normpath( os.path.abspath( selection ) )
      result = self.database.getDiskItemFromFileName( fileName, None )
      if result is None:
        if _debug is not None:
          print >> _debug, '  DiskItem not found in databases'
        result = self.database.createDiskItemFromFileName( fileName, None )
        if result is None:
          if _debug is not None:
            print >> _debug, '  DiskItem not created in databases'
          result = self.database.createDiskItemFromFormatExtension( fileName, None )
          if result is not None:
            result.readAndUpdateMinf()
        else:
          result.readAndUpdateMinf()
          if _debug is not None:
            print >> _debug, '  DiskItem created in databases'
        if result is None:
          if _debug is not None:
            print >> _debug, '  no format found for file name extension'
          directoryFormat = getFormat( 'Directory' )
          if directoryFormat in self.formats:
            # In this case, item is a directory
            if _debug is not None:
              print >> _debug, '  no extension ==> create Directory item'
            result = Directory( fileName, None )
            result.format = directoryFormat
            result._files = [ fileName ]
            result._identified = False
            result.type = self.type
            result.readAndUpdateMinf()
        elif _debug is not None:
          print >> _debug, '  found matching format:', result.format
      elif _debug is not None:
        print >> _debug, '  DiskItem found in databases'
      if result is not None:
        if result.type is None :
          # Set the result type if this is not already done
          result.type=self.type
        if result.getHierarchy( '_database' ) is None:
          # If DiskItem is not in a database, required attributes are ignored
          requiredAttributes = { '_format': requiredAttributes.get( '_format' ) }
          # if the diskitem format does not match the required format, and if required format contains Series of diskitem.format, try to change the format of the diskItem to a format series.
          if not self.diskItemFilter( result, requiredAttributes ):
            if ("Series of "+result.format.name in requiredAttributes.get("_format") ):
              self.database.changeDiskItemFormatToSeries(result)
        if not self.diskItemFilter( result, requiredAttributes ):
          if _debug is not None:
            print >> _debug, '  DiskItem rejected because:', self.diskItemFilter( result, requiredAttributes, explainRejection=True )
          result = None
    elif isinstance( selection, dict ):
      fullSelection = dict( selection )
      
    if result is None and fullSelection is not None:
      values = list( self._findValues( fullSelection, requiredAttributes, write=(write or self._write) , _debug=_debug ) )

      if values:
        if len( values ) == 1:
          result = values[ 0 ]
        else:
          # Find the item with the "smallest" "distance" from item
          values = sorted( (self.diskItemDistance( i, selection ), i ) for i in values )
          if _debug is not None:
            print >> _debug, '  findValue priority sorted items:'
            for l in values:
              print >> _debug, '   ', l
          if values[ 0 ][ 0 ] != values[ 1 ] [ 0 ]:
            result = values[ 0 ][ 1 ]
          else:
            refOrder, refDiskItem = values[ 0 ]
            refHierarchy = refDiskItem.hierarchyAttributes()
            differentOnFormatOnly = [ refDiskItem ]
            for checkOrder, checkDiskItem in values[1:]:
              if checkOrder != refOrder:
                break
              if refHierarchy == checkDiskItem.hierarchyAttributes():
                differentOnFormatOnly.append( checkDiskItem )
              else:
                differentOnFormatOnly = []
                break
            if differentOnFormatOnly:
              for preferedFormat in self.formats:
                l = [i for i in differentOnFormatOnly if i.format is preferedFormat]
                if l:
                  result = l[0]
                  break
              if _debug is not None:
                print >> _debug, '  top priority values differ only by formats:'
                for i in differentOnFormatOnly:
                  print >> _debug, '   ', i.format
                if result:
                  print >> _debug, '  choosen format:', result.format
            elif _debug is not None:
                print >> _debug, '  top priority values differ on ontology attributes ==> no selection on format'
            
    if _debug is not None:
      print >> _debug, '-> findValue return', result
      if result is not None:
        print >> _debug, '-> type:', result.type
        print >> _debug, '-> format:', result.format
        print >> _debug, '-> attributes:'
        for n, v in result.attributes().items():
          print >> _debug, '->  ', n, '=', v
      print >> _debug, '-' * 70 + '\n'
      _debug.flush()
    return result
  
  def diskItemDistance( self, diskItem, other ):
    '''Returns a value that represents a sort of distance between two DiskItems.
        The distance is not a number but distances can be sorted.'''
    # Count the number of common hierarchy attributes
    if isinstance( other, DiskItem ):
      if other.type is not None:
        other_type = other.type.name
      else:
        other_type = None
      other_priority = other.priority()
    else:
      other_type = other.get( '_type' )
      other_priority = 0
    if diskItem.type is not None:
      diskItem_type = diskItem.type.name
    else:
      diskItem_type = None
    if isinstance( other, DiskItem ):
      getHierarchy = other.getHierarchy
      getNonHierarchy = other.getNonHierarchy
    else:
      getHierarchy = other.get
      getNonHierarchy = other.get
    hierarchyCommon = reduce( operator.add, 
        ( (getHierarchy( n ) == v) for n, v in diskItem.hierarchyAttributes().iteritems() ),
        ( int(diskItem_type==other_type) ) )
    # Count the number of common non hierarchy attributes
    nonHierarchyCommon = reduce( operator.add, 
        ( (getNonHierarchy( n ) == v) for n, v in diskItem.nonHierarchyAttributes().iteritems() ),
        (int(diskItem_type == other_type) ) )
    if getattr( other, '_write', False ) and diskItem.isReadable():
      readable = -1
    else:
      readable = 0
    return ( -hierarchyCommon, other_priority - diskItem.priority(), -nonHierarchyCommon, readable  )
  
  
  def _findValues( self, selection, requiredAttributes, write, _debug=Undefined ):
    if _debug is Undefined:
      _debug = self._debug
    if requiredAttributes is None:
      requiredAttributes = self.requiredAttributes
    keySelection={}
    if selection:
      # in selection attributes, choose only key attributes because the request must not be too restrictive to avoid failure. The results will be sorted by distance to the selection later.
      keyAttributes=self.database.getTypesKeysAttributes(self.type.name)
      keySelection=dict( (i,selection[i] ) for i in keyAttributes if i in selection )
    readValues = ( i for i in self.database.findDiskItems( keySelection, _debug=_debug, **requiredAttributes ) if self.diskItemFilter( i, requiredAttributes ) )
    if write:
      # use selection attributes to create a new diskitem
      fullPaths = set()
      for item in readValues:
        fullPaths.add( item.fullPath() )
        yield item
      if self._formatsWithConverter:
        # Do not allow formats that require a conversion in DiskItem creation
        oldFormats = requiredAttributes.get( '_format' )
        requiredAttributes[ '_format' ] = oldFormats.difference( self._formatsWithConverter.iterkeys() )
      for item in self.database.createDiskItems( selection, _debug=_debug, **requiredAttributes ):
        if self.diskItemFilter( item, requiredAttributes ):
          if item.fullPath() not in fullPaths:
            yield item
        elif _debug is not None:
          print >> _debug, ' ', item, 'rejected because:', self.diskItemFilter( item, requiredAttributes, explainRejection=True )
      if self._formatsWithConverter:
        requiredAttributes[ '_format' ] = oldFormats
    else:
      for i in readValues:
        yield i
  
  
  def diskItemFilter( self, *args, **kwargs ):
    return diskItemFilter( self.database, *args, **kwargs )
    #if diskItem.type is not None:
      #types = self.database.getTypeChildren( *self.database.getAttributeValues( '_type', {}, required ) )
      #if types and diskItem.type.name not in types:
        #if explainRejection:
          #return 'DiskItem type ' + repr(diskItem.type.name) + ' is not in ' + repr( tuple(types) )
        #return False
    #formats = self.database.getAttributeValues( '_format', {}, required )
    #if formats and not(diskItem.format is None) :
      #if diskItem.format.name not in formats:
        #if explainRejection:
          #if diskItem.format is None :
            #value = None
          #else :
            #value = diskItem.format.name
          #return 'DiskItem format ' + repr(value) + ' is not in ' + repr( tuple(formats) )
        #return False
    #for key in required:
      #if key in ( '_type', '_format' ): continue
      #values = self.database.getAttributeValues( key, {}, required )
      #itemValue = diskItem.get( key, Undefined )
      #if itemValue is Undefined or itemValue not in values:
        #if explainRejection:
          #if itemValue is Undefined:
            #return 'DiskItem do not have the required ' + repr( key ) + ' attribute'
          #else:
            #return 'DiskItem attribute ' + repr(key) + ' = ' + repr( itemValue ) + ' is not in ' + repr( tuple(values) )
        #return False
    #return True
  
  
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


  def editor( self, parent, name, context ):
    return DiskItemEditor( self, parent, name, context=context )
  
  
  def editor( self, parent, name, context ):
    return DiskItemEditor( self, parent, name, context=context, write=self._write )


  def listEditor( self, parent, name, context ):
    return DiskItemListEditor( self, parent, name, context=context, write=self._write )
