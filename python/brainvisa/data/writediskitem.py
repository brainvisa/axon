from soma.undefined import Undefined
from neuroData import Parameter
from brainvisa.data.readdiskitem import ReadDiskItem
from neuroDiskItems import getFormats, getDiskItemType, DiskItem, isSameDiskItemType
from brainvisa.data.readdiskitem import ReadDiskItem, DiskItemEditor


#----------------------------------------------------------------------------
class WriteDiskItem( ReadDiskItem ):
  def __init__( self, diskItemType, formats, requiredAttributes={},
                exactType=False, ignoreAttributes=False, _debug=None ):
    ReadDiskItem.__init__( self, diskItemType, formats, requiredAttributes=requiredAttributes, ignoreAttributes=ignoreAttributes, enableConversion=False, _debug=_debug  )
    self.exactType = exactType
    self._write = True
        
  
  def checkValue( self, name, value ):
    Parameter.checkValue( self, name, value )

  def findValue( self, selection, requiredAttributes=None, _debug=Undefined ):
    result = ReadDiskItem.findValue( self, selection, requiredAttributes=requiredAttributes, _debug=_debug )
    if result is None and isinstance( selection, DiskItem ) and \
      ( selection.type is None or isSameDiskItemType( selection.type, self.type ) ) and self.formats[ 0 ] != selection.format:
      result = self.database.changeDiskItemFormat( selection, self.formats[ 0 ].name )
    return result

  def typeInfo( self, translator = None ):
    if translator: translate = translator.translate
    else: translate = _
    ti = super( WriteDiskItem, self ).typeInfo( translator )
    return  ( ti[0], ) + ( ( translate( 'Access' ), translate( 'output' ) ), ) + ti[ 1: ]
