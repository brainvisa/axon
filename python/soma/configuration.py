# -*- coding: iso-8859-1 -*-

#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL-B license under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the 
# terms of the CeCILL-B license as circulated by CEA, CNRS
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
# knowledge of the CeCILL-B license and that you accept its terms.


'''
@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''

import sys
from soma.signature.api import (HasSignature, Signature, VariableSignature,
                                Sequence)
from soma.minf.api import readMinf, writeMinf
from soma.translation import translate as _
import six

#------------------------------------------------------------------------------
class Configuration( HasSignature ):
  '''
  A L{Configuration} instance is a list that must contains only objects deriving
  from L{ConfigurationGroup}.
  '''
  
  def __init__( self ):
    super( Configuration, self ).__init__()
    self.signature = VariableSignature( self.signature )
    self._loaded = {}

  def add( self, key, value ):
    self.signature[ key ] = ConfigurationGroup
    setattr( self, key, value )
    module_config = self._loaded.get(key)
    if module_config is not None:
        self.set_module_config(value, module_config)
  
  
  def save( self, minf ):
    writeMinf( minf,( self, ) )
  
  
  def load( self, minf ):
    exceptions=[]
    read = readMinf(minf, stop_on_error=False, 
                    exceptions=exceptions)[0]
    if not exceptions:
        try:
            for name in self.signature:
                module_config = read.get(name)
                if module_config is not None:
                    self.set_module_config(getattr(self,name), module_config)
            self._loaded.update(read)                
        except:
            exceptions = [sys.exc_info()]
    return exceptions


  @classmethod
  def _create_and_set(cls, targetType, values):
    result = targetType.createValue()
    cls.set_module_config(result, values)
    return result    
        

  @classmethod
  def set_module_config(cls, module, module_config):
    for k, v in six.iteritems(module_config):
        done = False
        if isinstance(v, dict):
            target = getattr(module, k, None)
            if target is not None:
                cls.set_module_config(target, v)
            done = True
        elif isinstance(v, list):
            targetType = module.signature.get(k, None)
            if targetType is not None:
                targetType = targetType.type
            if isinstance(targetType, Sequence) and targetType.elementType.mutable:
                v = [cls._create_and_set(targetType.elementType, i) for i in v]
                setattr(module, k, v)
                done = True
        if not done:
            setattr(module, k, v)

#------------------------------------------------------------------------------
class ConfigurationGroup( HasSignature ):
  '''
  Represent one element of a L{Configuration} object.
  '''
