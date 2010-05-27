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
from soma.undefined import Undefined
from neuroData import Parameter
from brainvisa.data.readdiskitem import ReadDiskItem
from neuroDiskItems import getFormats, getDiskItemType, DiskItem, isSameDiskItemType
from brainvisa.data.readdiskitem import ReadDiskItem
from brainvisa.data.qtgui.readdiskitemGUI import DiskItemEditor


#----------------------------------------------------------------------------
class WriteDiskItem( ReadDiskItem ):
  def __init__( self, diskItemType, formats, requiredAttributes={},
                exactType=False, ignoreAttributes=False, _debug=None ):
    ReadDiskItem.__init__( self, diskItemType, formats, requiredAttributes=requiredAttributes, ignoreAttributes=ignoreAttributes, enableConversion=False, _debug=_debug, exactType=exactType  )
    self._write = True
        
  
  def checkValue( self, name, value ):
    Parameter.checkValue( self, name, value )

  def findValue( self, selection, requiredAttributes=None, _debug=Undefined ):
    result = ReadDiskItem.findValue( self, selection, requiredAttributes=requiredAttributes, _debug=_debug )
    if result is None and isinstance( selection, DiskItem ) and \
      ( selection.type is None or selection.type is self.type or (not self.exactType and isSameDiskItemType( selection.type, self.type )) ) and \
       self.formats[ 0 ] != selection.format:
      result = self.database.changeDiskItemFormat( selection, self.formats[ 0 ].name )
    return result

  def typeInfo( self, translator = None ):
    if translator: translate = translator.translate
    else: translate = _
    ti = super( WriteDiskItem, self ).typeInfo( translator )
    return  ( ti[0], ) + ( ( translate( 'Access' ), translate( 'output' ) ), ) + ti[ 1: ]
