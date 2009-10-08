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

import types, string, re, sys, os, stat, threading, cPickle, weakref, copy
from UserDict import UserDict
from UserList import UserList
from brainvisa import notifier
from neuroException import HTMLMessage
import neuroConfig


#----------------------------------------------------------------------------
class Parameter( object ):
  def __init__( self ):
    self.mandatory = 1
    self.linkParameterWithNonDefaultValue = 0
    self.userLevel = 0
    self.valueLinkedNotifier = notifier.Notifier( 3 )
    self._name = None
    self._parameterized = None
    
  def checkReadable( self, value ):
    return 1

  def iterate( self, *args ):
    result = []
    for i in args: result.append( self.findValue( i ) )
    return result
  
  def typeInfo( self, translator = None ):
    if translator is None: translate = _t_
    else: translate = translator.translate
    return  ( ( translate( 'Type' ), translate( string.split( str( self.__class__.__name__ ), '.' )[ -1 ] ) ), )

  def editor( self, parent, name, context ):
    raise Exception( _t_('No editor implanted for type %s') % self.typeInfo()[0][ 1 ] )
  
  def listEditor( self, parent, name, context ):
    raise Exception( _t_('No list editor implanted for type %s') % self.typeInfo()[0][ 1 ] )

  def defaultValue( self ):
    return None
  
  def __getstate__( self ):
    return copy.copy( self.__dict__ )

  def __setstate__( self, state ):
    self.__dict__ = state

  def copyPostprocessing( self ):
    pass
  
  def toolTipText( self, parameterName, documentation ):
    result = '<center>' + parameterName 
    if not self.mandatory: result += ' (' + _t_( 'optional' ) + ')'
    result += '</center><hr><b>' + _t_( 'Description' ) + ':</b><br>' + \
              documentation + '<p>'
    return result
  
  def checkValue( self, name, value ):
    '''This functions check if a value is valid for the parameter. If
    the value is not valid it must raise an excpetion.'''
    if value is None and self.mandatory:
      raise Exception( HTMLMessage(_t_('argument <em>%s</em> is mandatory') % name) )
  
  def setNameAndParameterized( self, name, parameterized ):
    self._name = name
    if parameterized is None:
      self._parameterized = None
    else:
      self._parameterized = weakref.ref( parameterized )
  
  def getParameterized( self ):
    if self._parameterized is not None:
      return self._parameterized()
    return None

  def getName( self ):
    return self._name

  constructorEditor = None


#----------------------------------------------------------------------------
class String( Parameter ):

  def findValue( self, value ):
    if value is None: return None
    return str( value )
  
  
#----------------------------------------------------------------------------
class Password( String ):
  pass
 

#----------------------------------------------------------------------------
class Number( Parameter ):

  def findValue( self, value ):
    if value is None: return None
    if type( value ) in ( types.FloatType, types.IntType, types.LongType ):
      return value
    try: return int( value )
    except:
      try: return long( value )
      except:
        return float( value )        


#----------------------------------------------------------------------------
class Integer( Number ):

  def findValue( self, value ):
    if value is None: return None
    if type( value ) in ( types.IntType, types.LongType ):
      return value
    try: return int( value )
    except:
      return long( value )


#----------------------------------------------------------------------------
class Float( Number ):

  def findValue( self, value ):
    if value is None: return None
    return float( value )


#----------------------------------------------------------------------------
class Choice( Parameter ):
  def __init__( self, *args ):
    Parameter.__init__( self )
    self._warnChoices = {}
    self.values = []
    self.setChoices( *args )
    
  def setChoices( self, *args ):
    if not args: args = [ ( '', None) ]
    values = []
    for p in args:
      if type( p ) in ( types.TupleType, types.ListType ) and len( p ) == 2:
        values.append( ( unicode( p[0] ), p[1] ) )
      else:
        values.append( ( unicode( p ), p ) )
    if self.values != values:
      self.values = values
      for f in self._warnChoices.keys():
        f()
  
  def warnChoices( self, function ):
    self._warnChoices[ function ] = None
  
  def unwarnChoices( self, function ):
    try:
      del self._warnChoices[ function ]
    except KeyError: # try to del a callback that is not longer registred
      pass
  
  def findValue( self, value ):
    if value is None: return None
    i = self.findIndex( value )
    if i >= 0:
      return self.values[ i ][ 1 ]
    elif type( value ) in types.StringTypes:
      try:
        value = eval( value )
      except:
        pass
      else:
        i = self.findIndex( value )
        if i >= 0:
          return self.values[ i ][ 1 ]
    raise KeyError( HTMLMessage(_t_('<em>%s</em> is not a valid choice') % unicode(value)) )
    
  def findIndex( self, value ):
    i = 0
    for n, v in self.values:
      if value == v or str( value ) == n:
        return i
      i += 1
    return -1

  def defaultValue( self ):
    if self.values:
      return self.values[ 0 ][ 1 ]
    else:
      return None
  
  def __getstate__( self ):
    result = Parameter.__getstate__( self )
    for attrName in ( 'values', '_warnChoices' ):
      result[ attrName ] = copy.copy( result[ attrName ] )
    return result
    

#----------------------------------------------------------------------------
class OpenChoice( Choice ):
  def __init__( self, *args ):
    Choice.__init__( self, *args )

  def findValue( self, value ):
    if value is None: return None
    i = self.findIndex( value )
    if i >= 0:
      return self.values[ i ][ 1 ]
    else:
      return str( value )


#----------------------------------------------------------------------------
class Boolean( Choice ):
  def __init__( self ):
    Choice.__init__( self, ( 'True', True ), ( 'False', False ) )

#-------------------------------------------------------------------------------
class Point( Parameter ):
  def __init__( self, dimension = 1 ):
    Parameter.__init__( self )
#    self.linkParameterWithNonDefaultValue = 1
    self.dimension = dimension
    self._Link = None

  def findValue( self, value ):
    if isinstance( value, list ):
      return map( float, value )

  def addLink( self, sourceParameterized, sourceParameter ):
    sourceParameterized.addLink( None, sourceParameter, self._setLink )

  def _setLink( self, value ):
    self._Link = value

#-------------------------------------------------------------------------------
class Point2D( Point ):
  def __init__( self, dimension = 2 ):
    Point.__init__( self, dimension )

#-------------------------------------------------------------------------------
class Point3D( Point ):
  def __init__( self, dimension = 3 ):
    Point.__init__( self, dimension )

  # We only keep the following method to have back compatibility with old
  # codes
  def add3DLink( self, sourceParameterized, sourceParameter ):
    Point.addLink( self, sourceParameterized, sourceParameter )  

#----------------------------------------------------------------------------
class MatrixValue( UserList ):
  def __init__( self, value, requiredLength=None, requiredWidth=None ):
    self.data = []
    if value is None:
      self.size = ( 0, 0 )
    else:
      length = len( value )
      width = None
      n = Number()
      for line in value:
        if width is not None:
          if len( line ) != width:
            raise Exception( _t_( 'Invalid matrix size' ) )
        else:
          width = len( line )
        self.data.append( map( lambda x, n=n: n.findValue( x ), line ) )
      if width is None: width = 0
      if ( requiredLength is not None and length != requiredLength ) or \
         ( requiredWidth is not None and width != requiredWidth ):
        raise Exception( _t_( 'Invalid matrix size' ) )
      self.size = ( length, width )


#----------------------------------------------------------------------------
class ListOfVectorValue( UserList ):
  def __init__( self, value, requiredLength=None ):
    self.data = []
    if value is not None:
      length = len( value )
      n = Number()
      for line in value:
        self.data.append( map( lambda x, n=n: n.findValue( x ), line ) )
      if ( requiredLength is not None and length != requiredLength ):
        raise Exception( _t_( 'Invalid vector list size' ) )
      self.size = length


#----------------------------------------------------------------------------
class ListOfVector( Parameter ):
  def __init__( self, length=None ):
    Parameter.__init__( self )
    self.length =length
  
  def findValue( self, value ):
    if value is None: return None
    return ListOfVectorValue( value, self.length )


#----------------------------------------------------------------------------
class Matrix( Parameter ):
  def __init__( self, length=None, width=None ):
    Parameter.__init__( self )
    self.length =length
    self.width = width
  
  def findValue( self, value ):
    if not value: return None
    return MatrixValue( value, self.length, self.width )

  
#----------------------------------------------------------------------------
class ListOf( Parameter ):
  def __init__( self, contentType ):
    Parameter.__init__( self )
    self.contentType = contentType

  def checkValue( self, name, value ):
    '''This functions check if a value is valid for the parameter. If
    the value is not valid it must raise an excpetion.'''
    Parameter.checkValue( self, name, value )
    
    if ( not value is None ) and ( type( value ) in ( types.ListType, types.TupleType ) ):
      for listvalue in value :
        self.contentType.checkValue( name, listvalue )

  def findValue( self, value ):
    if value is None:
      return []
    elif type( value ) in ( types.ListType, types.TupleType ):
      return map( self.contentType.findValue, value )
    else:
      return [ self.contentType.findValue( value ) ]


#----------------------------------------------------------------------------
class Signature( UserDict ):
  def __init__( self, *params ):
    self.sortedKeys = []
    self.data = {}
    i = 0
    while i < len( params ):
      ( name, value ) = params[i:i+2]
      self.sortedKeys.append( name,)
      self.data[ name ] = value
      i += 2
  
  def keys( self ):
    return self.sortedKeys
  
  def items( self ):
    return [(x, self.data[x]) for x in self.sortedKeys]

  def values( self ):
    return [self.data[x] for x in self.sortedKeys]

  def __getstate__( self ):
    result = copy.copy( self.__dict__ )
    result[ 'data' ] = copy.copy( result[ 'data' ] )
    return result
    
  def __setstate__( self, state ):
    self.__dict__ = state

  def __delitem__(self, k):
    del self.data[k]
    self.sortedKeys.remove(k)

  def __setitem__(self, k, value):
    if not self.data.has_key(k):
	    self.sortedKeys.append(k)
    self.data[k] = value

  def shallowCopy(self):
    import copy
    new = copy.copy(self)
    new.sortedKeys = copy.copy(self.sortedKeys)
    return new

   
#----------------------------------------------------------------------------

def initializeData():
  pass
