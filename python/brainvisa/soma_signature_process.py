#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCIL license version 2 under
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
# knowledge of the CeCILL version 2 license and that you accept its terms.
from soma.signature.api import HasSignature, VariableSignature

from neuroProcesses import String as BrainvisaString
from soma.signature.api import Unicode as SomaUnicode
from neuroProcesses import Number as BrainvisaNumber
from soma.signature.api import Number as SomaNumber

class SomaSignatureProcess( HasSignature ):
  # Raise an exception when an unknown (or not implemented) 
  # BrainVISA parameter type is encoutered.
  EXCEPTION_POLICY = 0
  # Ignore parameters with unknown (or not implemented) 
  # BrainVISA type.
  IGNORE_POLICY = 1
  # Replace parameters with unknown (or not implemented) 
  # BrainVISA type.
#  REPLACE_POLICY = 2
  def __init__( self, processInstance, unknownTypePolicy=EXCEPTION_POLICY ):
    super( SomaSignatureProcess, self ).__init__()
    self._process = processInstance
    self.signature = VariableSignature( self.signature )
    for name, paramType in self._process.signature.items():
      if isinstance( paramType, BrainvisaString ):
        somaParam = SomaUnicode
      elif isinstance( paramType, BrainvisaNumber ):
        somaParam = SomaNumber
      else:
        if unknownTypePolicy == self.EXCEPTION_POLICY:
          raise TypeError( _t_( 'BrainVISA signature type %s cannot be converted to a Soma signature type.' ) % ( paramType.typeInfo()[0][1], ) )
        somaParam = None
      if somaParam is not None:
        self.signature[ name ] = somaParam
        self.onAttributeChange( self._attributeChanged )
        value = getattr( self._process, name )
        if value is not  None:
          setattr( self, name, value )
  
  def _attributeChanged( self, name, value, oldValue ):
    self._process.setValue( name, value )
