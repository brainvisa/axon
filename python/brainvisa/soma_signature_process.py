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
