# Copyright IFR 49 (1995-2009)
#
#  This software and supporting documentation were developed by
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

import inspect


#-------------------------------------------------------------------------------
def hasParameter( function, parameterName ):
  '''Return True if function can be called with a named parameter.'''
  if inspect.isfunction( function ):
    pass
  elif inspect.ismethod( function ):
    function = function.im_func
  elif inspect.isclass( function ):
    try:
      function = function.__init__
    except AttributeError:
      return ( 0, 0 )
  else:
    try:
      function = function.__call__
    except AttributeError:
      raise RuntimeError( _t_( '%s is not callable' ) % \
                          function )
  args, varargs, varkw, defaults = inspect.getargspec( function )
  return varkw is not None or parameterName in args

#-------------------------------------------------------------------------------
def numberOfParameterRange( function ):
  '''Return a two element tuples containing minimum and maximum number of 
  parameter that can be used to call a function. If the maximum number of
  argument is not defined, it is set to None.'''
  if inspect.isfunction( function ):
    addToResult = 0
  elif inspect.ismethod( function ):
    function = function.im_func
    addToResult = -1
  elif inspect.isclass( function ):
    try:
      function = function.__init__
      addToResult = -1
    except AttributeError:
      return ( 0, 0 )
  else:
    try:
      function = function.__call__
      addToResult = -1
    except AttributeError:
      raise RuntimeError( _t_( '%s is not callable' ) % \
                          ( str( function ), ) )
  args, varargs, varkw, defaults = inspect.getargspec( function )
  if defaults is None:
    lenDefault = 0
  else:
    lenDefault = len( defaults )
  minimum = len( args ) - lenDefault + addToResult
  if varargs is None:
    maximum = len( args ) + addToResult
  else:
    maximum = None
  return ( minimum, maximum )


#-------------------------------------------------------------------------------
def checkParameterCount( function, paramCount ):
  '''Check that a function or an onbect can be called with paramCount
  arguments. If not, a RuntimeError is raised.'''
  minimum, maximum = numberOfParameterRange( function )
  if ( maximum is not None and paramCount > maximum ) or \
     paramCount < minimum:
    if inspect.isfunction( function ):
      name = _t_( 'function %s' ) % ( function.__name__, )
    elif inspect.ismethod( function ):
      name = _t_( 'method %s' ) % ( function.im_class.__name__ + '.' + \
                                  function.__name__, )
    elif inspect.isclass( function ):
      name = _t_( 'class %s' ) % ( function.__name__, )
    else:
      name = str( function )
    raise RuntimeError( 
      _t_( '%s cannot be called with %d arguments' ) % \
         ( name, paramCount )  )

