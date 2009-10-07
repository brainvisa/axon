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

from soma.functiontools import checkParameterCount


#-------------------------------------------------------------------------------
class Notifier:
  '''Register a series of functions which are all called when the instance is
  called. The calling order is the registering order.
  '''
  def __init__( self, parameterCount=None ):
    '''If parameterCount is not None, each registered function must be callable
    with parameterCount arguments.
    '''
    self._functions = []
    self._parameterCount = None
    
  def add( self, function ):
    '''Check function with checkParameterCount() and register it.'''
    
    if function not in self._functions:
      if self._parameterCount is not None:
        util.checkParameterCount( function, self._parameterCount )
      self._functions.append( function )
      
  def remove( self, function ):
    '''Unregister a function.'''
    
    try:
      self._functions.remove( function )
    except ValueError:
      pass
  
  def __call__( self, *args, **kwargs ):
    '''Calls all the registered functions.'''
    
    for f in self._functions:
      f( *args, **kwargs )
  
  
  
