# -*- coding: utf-8 -*-
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
This module contains classes used to define the signature of Brainvisa processes, 
that is to say a list of typed parameters.

The main class is :py:class:`Signature`. It contains a list of parameters names and types. 
Each parameter is an instance of a sublcass of :py:class:`Parameter`:

* :py:class:`String`
* :py:class:`Number`: an integer or float number.
* :py:class:`Integer`
* :py:class:`Float`
* :py:class:`Choice`: a choice between several constant values.
* :py:class:`Boolean`
* :py:class:`Point`, :py:class:`Point2D`, :py:class:`Point3D`: coordinates of a point.
* :py:class:`ListOfVector`: a list of vectors of numbers.
* :py:class:`Matrix`: a matrix of numbers.
* :py:class:`ListOf`: a list of :py:class:`Parameter`.
* :py:class:`brainvisa.data.readdiskitem.ReadDiskItem`: a :py:class:`brainvisa.data.neuroDiskItems.DiskItem` as an input parameter.
* :py:class:`brainvisa.data.writediskitem.WriteDiskItem`: a :py:class:`brainvisa.data.neuroDiskItems.DiskItem` as an output parameter.

**Example**

>>> signature = Signature(
>>>   'input', ReadDiskItem( "Volume 4D", [ 'GIS Image', 'VIDA image' ] ),
>>>   'output', WriteDiskItem( 'Volume 4D', 'GIS Image' ),
>>>   'threshold', Number(),
>>>   'method', Choice( 'gt', 'ge', 'lt', 'le' )
>>> )

Matching graphical editors classes are defined in :py:mod:`brainvisa.data.qt4gui.neuroDataGUI`.

:Inheritance diagram:
  
.. inheritance-diagram:: brainvisa.data.neuroData
       
:Classes:
  
"""
import types, string, weakref, copy
import sys
import six
if sys.version_info[0] >= 3:
    from collections import UserDict, UserList
    unicode = str
else:
    from UserDict import UserDict
    from UserList import UserList
from soma.notification import Notifier
from brainvisa.processing.neuroException import HTMLMessage

#----------------------------------------------------------------------------
class Parameter( object ):
  """
  This class represents a type of parameter in a :py:class:`Signature`.
  
  :Attributes:
  
  .. py:attribute:: mandatory
  
  Boolean. Indicates if the parameter is mandatory, that is to say it must have a non null value.
  Default is True.
  
  .. py:attribute:: userLevel
  
  Integer. Indicates the minimum userLevel needed to see this parameter. Default is 0.
  
  .. py:attribute:: databaseUserLevel
  
  Integer. Indicates the minimum userLevel needed to allow database selection for this parameter (useful only for diskitems).
  
  .. py:attribute:: browseUserLevel
  
  Integer. Indicates the minimum userLevel needed to allow filesystem selection for this parameter (useful only for diskitems).
  
  .. py:attribute:: linkParameterWithNonDefaultValue
  
  Boolean. Indicates if the value of the parameter can be changed by the activation of a link between parameters even if the parameter has no more a default value (it has been changed by the user). Default is False.
  
  .. py:attribute:: valueLinkedNotifier
  
  :py:class:`soma.notification.Notifier`. This notifier will notify its observers when a link to this parameter is activated.
  
  :Methods:
  
  """
  def __init__( self, section=None ):
    self.mandatory = 1
    self.linkParameterWithNonDefaultValue = 0
    self.userLevel = 0
    self.valueLinkedNotifier = Notifier( 3 )
    self._name = None
    self._parameterized = None
    self._section = section   
    
  def checkReadable( self, value ):
    """
    This is a virtual function (returns always True) that could be overriden in derived class. 
    It should return True if the value given in parameter is *readable*.
    """
    return 1

  def iterate( self, *args ):
    """
    Calls :py:meth:`findValue` on each value given in parameter. 
    Returns the list of results.
    """
    result = []
    for i in args: result.append( self.findValue( i ) )
    return result
  
  def typeInfo( self, translator = None ):
    """
    Returns a tuple containing ("Type", type_name). 
    The type_name is the name of the class possibly translated with the give translator or Brainvisa default translator if None.
    """
    if translator is None: translate = _t_
    else: translate = translator.translate
    return  ((translate('Type'),
              translate(str(self.__class__.__name__).split('.')[ -1 ])), )

  def editor( self, parent, name, context ):
    """
    Virtual function that can be overriden in derived class. The function should return an object that can be used to edit the value of the parameter.
    This one raises an exception saying that no editor exist for this type.
    """
    raise Exception( _t_('No editor implanted for type %s') % self.typeInfo()[0][ 1 ] )
  
  def listEditor( self, parent, name, context ):
    """
    Virtual function that can be overriden in derived class. The function should return an object that can be used to edit a list of values for the parameter.
    This one raises an exception saying that no list editor exist for this type.
    """
    raise Exception( _t_('No list editor implanted for type %s') % self.typeInfo()[0][ 1 ] )

  def defaultValue( self ):
    """
    Virtual function. Returns a default value for the parameter (here None).
    """
    return None
  
  def getSectionTitleIfDefined(self):
    """
    return section title if defined and return None otherwise
    """
    return self._section
  
  def __getstate__( self ):
    return copy.copy( self.__dict__ )

  def __setstate__( self, state ):
    self.__dict__ = state

  def copyPostprocessing( self ):
    pass
  
  def toolTipText( self, parameterName, documentation ):
    """
    Returns the text of a tooltip (in HTML format) for this parameter. Can be displayed as information in a GUI.
    The tooltip shows the name of the parameter, indicates if it is optional, and shows ``documentation`` as a description of the parameter.
    """
    result = '<center>' + parameterName 
    if not self.mandatory:
      result += ' (' + _t_( 'optional' ) + ')'
    result += '</center><hr><b>' + _t_( 'Type' ) + \
              ':</b> ' + self.typeInfo()[0][1] + '<br>' + \
              '<b>' + _t_( 'Description' ) + ':</b><br>' + \
              documentation + '<p>'
    return result

  def checkValue( self, name, value ):
    '''This functions check if the given value is valid for the parameter. 
    If the value is not valid it raises an exception.'''
    if value is None and self.mandatory:
      raise Exception( HTMLMessage(_t_('Mandatory argument <em>%s</em> has no value') % name) )
  
  def setNameAndParameterized( self, name, parameterized ):
    """
    Stores a name and an associated :py:class:`brainvisa.processes.Parameterized` object in this parameter.
    """
    self._name = name
    if parameterized is None:
      self._parameterized = None
    else:
      self._parameterized = weakref.ref( parameterized )
  
  def getParameterized( self ):
    """
    Returns the :py:class:`brainvisa.processes.Parameterized` object associated to this parameter. 
    Generally the Process that have this parameter in its signature.
    """
    if self._parameterized is not None:
      return self._parameterized()
    return None

  def getName( self ):
    """
    Returns the name of the parameter.
    """
    return self._name

  constructorEditor = None


#----------------------------------------------------------------------------
class String( Parameter ):
  """
  This class represents a string parameter.
  """

  def findValue( self, value ):
    """
    Returns ``str(value)``.
    """
    if value is None: return None
    return str( value )
  
  
#----------------------------------------------------------------------------
class Password( String ):
  """
  This class represents a string parameter that is used as a Password.
  """
  pass
 

#----------------------------------------------------------------------------
class Number( Parameter ):
  """
  This class represents a parameter that is a number, integer of float.
  """

  def findValue( self, value ):
    """
    If the value is not a python number, tries to convert it to a number with :py:func:`int`, :py:func:`long`, :py:func:`float`.
    """
    if value is None: return None
    if type( value ) in six.integer_types + (six.types.FloatType,):
      return value
    try: return int( value )
    except:
      try: return long( value )
      except:
        return float( value )        


#----------------------------------------------------------------------------
class Integer( Number ):
  """
  This class represents a parameter that is an integer.
  """

  def findValue( self, value ):
    """
    If the value is not a python integer, tries to convert it to an integer with :py:func:`int`, :py:func:`long`.
    """
    if value is None: return None
    if type( value ) in six.integer_types:
      return value
    try: return int( value )
    except:
      return long( value )


#----------------------------------------------------------------------------
class Float( Number ):
  """
  This class represents a parameter that is float number.
  """

  def _makeValueReasonable( self, value ):
    """limit float number to 10 decimal maximum, because of truncation with
    QString/unicode convertion may cause comparison trouble"""
    try:
      return float("%.10e" % float(value))
    except Exception as e:
      # unvalid value (maybe :'' or None)
      return None

  def findValue( self, value ):
    """
    Tries to convert the value to a float with :py:func:`float`.
    """
    if value is None: return None
    return self._makeValueReasonable( value )


#----------------------------------------------------------------------------
class Choice( Parameter ):
  """
  A Choice parameter allows the user to choose a value among a set of possible values. 
  This set is given as parameter to the constructor. Each value is associated to a label, which is the string shown in the graphical interface, possibly after a translation. That's why a choice item can be a couple (label, value). 
  When a choice item is a simple value, the label will be the string representation of the value ( ``label=unicode(value)`` ).
  
  **Examples**
  
  >>> c = Choice( 1, 2, 3 )
  >>> c = Choice( ( 'first', 1 ), ( 'second', 2 ), ( 'third', 3 ) )
            
  """
  def __init__( self, *args, **kwargs ):
    """
    
    :param list args: list of possible value, each value can be a string or a tuple. 
    """
    if 'section' in kwargs.keys():
      section = kwargs['section']
    else:
      section = None
    Parameter.__init__( self, section )
    self._warnChoices = {}
    self.values = []
    self.setChoices( *args )
    
  def setChoices( self, *args ):
    """
    Sets the list of possible values. 
    
    :param list args: list of possible value, each value can be a string or a tuple. 
    """
    if not args: args = [ ( '', None) ]
    values = []
    for p in args:
      if type(p) in (tuple, list) and len(p) == 2:
        values.append( ( unicode( p[0] ), p[1] ) )
      else:
        values.append( ( unicode( p ), p ) )
    if self.values != values:
      self.values = values
      for f in self._warnChoices.keys():
        f()
  
  def warnChoices( self, function ):
    """
    Stores a callback function that will be called if the list of choices changes.
    
    :param function: the callback function
    """
    self._warnChoices[ function ] = None
  
  def unwarnChoices( self, function ):
    """
    Removes the function from the callback functions associated to the list of choices modification.
    
    :param function: the callback function
    """
    try:
      del self._warnChoices[ function ]
    except KeyError: # try to del a callback that is not longer registred
      pass
  
  def findValue( self, value ):
    """
    Finds a value in the list of choices that matches the one given in parameter.
    Raises :py:class:`exceptions.KeyError` if not found.
    """
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
    raise KeyError( '%s is not a valid choice' % unicode(value) )
    
  def findIndex( self, value ):
    """
    Finds the index of a value in the list of possible choices. 
    
    :param value: could be the label or the associated value of the choice
    :rtype: integer
    :returns: the index of the value if found, else -1.
    """
    i = 0
    for n, v in self.values:
      if value == v or str( value ) == n:
        return i
      i += 1
    return -1

  def defaultValue( self ):
    """
    The default value for a choice parameter is the first of the list of choices or None if the list of choices is empty.
    """
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
  """
  An OpenChoice enables to choose a value in the list of choice or a new value that is not in the list.
  """
  def __init__( self, *args, **kwargs ):
    Choice.__init__( self, *args, **kwargs )

  def findValue( self, value ):
    """
    If the value is not in the list of choices, returns ``str(value)``.
    """
    if value is None: return None
    i = self.findIndex( value )
    if i >= 0:
      return self.values[ i ][ 1 ]
    else:
      return str( value )
   
#----------------------------------------------------------------------------
class Boolean( Parameter ):
  """
  A choice between 2 values: True or False.
  """

  def findValue( self, value ):
    """
    Returns ``bool(value)``.
    """
    if value is None: return True # default is True
    # convert to int first because if value is a string, '0' or '1',
    # direct bool conversion will not work.
    if type( value ) in ( str, unicode ):
      if value == 'True':
        return True
      elif value == 'False':
        return False
    return bool( int( value ) )


#-------------------------------------------------------------------------------
class Point( Parameter ):
  """
  This parameter type represents the coordinates of a point.
  """
  def __init__( self, dimension = 1, precision = None, section=None ):
    """
    :param int dimension: dimension of the space in which the coordinates are given.
    :param int precision: precision of the coordinates.
    """
    Parameter.__init__( self, section )
#    self.linkParameterWithNonDefaultValue = 1
    self.dimension = dimension
    self.precision = precision
    self._Link = None

  def findValue( self, value ):
    """
    Checks that the value is a list and returns a list with each valus converted to a float value.
    """
    if isinstance( value, list ):
      return map( float, value )

  def addLink( self, sourceParameterized, sourceParameter ):
    """
    Associates a specific link function between the source parameter and this parameter.
    When the source parameter changes, its value is stored in this object.
    
    :param sourceParameterized: :py:class:`brainvisa.processes.Parameterized` object that contains the parameters in its signature
    :param sourceParameter: :py:class:`Parameter` object that is the source of the link
    """
    sourceParameterized.addLink( None, sourceParameter, self._setLink )

  def _setLink( self, value ):
    self._Link = value

#-------------------------------------------------------------------------------
class Point2D( Point ):
  """
  :py:class:`Point` in a two dimensions space.
  """
  def __init__( self, dimension = 2, precision = None, section=None ):
    Point.__init__( self, dimension, precision, section )

#-------------------------------------------------------------------------------
class Point3D( Point ):
  """
  :py:class:`Point` in a three dimensions space.
  """
  def __init__( self, dimension = 3, precision = None, section=None ):
    Point.__init__( self, dimension, precision, section )

  # We only keep the following method to have back compatibility with old
  # codes
  def add3DLink( self, sourceParameterized, sourceParameter ):
    """
    Deprecated. Use :py:meth:`Point.addLink` instead.
    """
    Point.addLink( self, sourceParameterized, sourceParameter )  

#----------------------------------------------------------------------------
class MatrixValue( UserList ):
  """
  This object represents a matrix. 
  
  :Attributes:
  
  .. py:attribute:: data (list)
  
    Content of the matrix: a list of lines, each line is a list of number.
  
  .. py:attribute:: size (tuple)
  
    Dimension of the matrix (nb lines, nb columns)
  
  """
  def __init__( self, value, requiredLength=None, requiredWidth=None ):
    """
    :param list value: content of the matrix: a list of lines, each line is a list of value. Each value should be a number of a string that can be converted to a number. 
    :param int requiredLength: required number of lines of the matrix. An exception is raised if this condition is not met.
    :param int requiredWidth: required number of columns of the matrix. An exception is raised if this condition is not met.
    """
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
  """
  This object represents a list of vectors.
  
  :Attributes:
  
  .. py:attribute:: data
  
    The content of the list of vectors: a list of vectors, each vector is a list of number. The vectors can have different sizes.
  
  .. py:attribute:: size
  
    The number of vectors in the list.
  
  """
  def __init__( self, value, requiredLength=None ):
    """
    
    :param list value: the content of the list of vector: a list of vector, each vector is a list of value. Each value should be number or a string that can be converted to a number.
    :param int requiredLength: required number of vectors in the list. An exception is raised if this condition is not met.
    """
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
  """
  This parameter expects a list of vectors value.
  """
  def __init__( self, length=None, section=None ):
    """
    :param int length: number of vectors.
    """
    Parameter.__init__( self, section )
    self.length =length
  
  def findValue( self, value ):
    """
    Returns a :py:class:`ListOfVectorValue` created from the given value, checking that the required length is respected.
    """
    if value is None: return None
    return ListOfVectorValue( value, self.length )


#----------------------------------------------------------------------------
class Matrix( Parameter ):
  """
  This parameter expects a matrix value.
  """
  def __init__( self, length=None, width=None, section=None ):
    """
    :param int length: required number of lines of the matrix
    :param int width: required number of columns of the matrix.
    """
    Parameter.__init__( self, section )
    self.length =length
    self.width = width
  
  def findValue( self, value ):
    """
    Returns a :py:class:`MatrixValue` created from the given value, checking that the required dimensions are respected.
    """
    if not value: return None
    return MatrixValue( value, self.length, self.width )

  
#----------------------------------------------------------------------------
class ListOf( Parameter ):
  """
  This parameter represents a list of elements of the same type.
  
  :Attributes:
  
  .. py:attribute:: contentType
  
    Required :py:class:`Parameter` type for the elements of the list.
  
  :Methods:
  
  """
  def __init__( self, contentType, allowNone=False, section=None ):
    """
    :param contentType: type of the elements of the list.
    """
    Parameter.__init__( self, section )
    self.contentType = contentType
    self._allowNone = allowNone

  def checkValue( self, name, value ):
    '''
    Checks if the given value is valid for this parameter. 
    The value should be a list or a tuple and each element should match the content type of the parameter.
    An exception is raised if these conditions are not met.
    '''
    Parameter.checkValue( self, name, value )

    if (not value is None) and (type(value) in (list, tuple)):
      for listvalue in value :
        if not self._allowNone or listvalue is not None:
          self.contentType.checkValue( name, listvalue )

  def findValue( self, value ):
    """
    Returns a suitable value for this parameter from the given value. 
    If the value is None, ``[]`` is returned. 
    It it is a list, a new list with each value checked and possibly converted to the appropriate type is returned.
    If it is not a list (only one element), a list containing this element possibly converted to the appropriate type is returned.
    """
    if value is None:
      return []
    elif type(value) in (list, tuple):
      if self._allowNone:
        values = []
        for val in value:
          if val is None:
            values.append( None )
          else:
            values.append( self.contentType.findValue( val ) )
        return values
      else:
        return map( self.contentType.findValue, value )
    else:
      return [ self.contentType.findValue( value ) ]

  def editor( self, parent, name, context ):
    """
    Returns the list editor of the content type parameter.
    """
    # report visibility params to contentType
    if hasattr( self, 'databaseUserLevel' ):
      self.contentType.databaseUserLevel = self.databaseUserLevel
    if hasattr( self, 'browseUserLevel' ):
      self.contentType.browseUserLevel = self.browseUserLevel
    return self.contentType.listEditor( parent, name, context )

  def typeInfo(self, translator = None):
    if translator is None:
      translate = _t_
    else:
      translate = translator.translate
    subti = self.contentType.typeInfo()
    tdescr = (translate('Type'),
             translate('ListOf') + '( ' + subti[0][1] + ' )')
    return tuple((tdescr,) + subti[1:])


#----------------------------------------------------------------------------
class Signature( UserDict ):
  """
  A list of parameters with the name and the type of each parameter.
  
  This object can be used as a dictionary whose keys are the name of the parameters 
  and the values are the types of the parameters.
  But unlike a python dictionary, the keys are **ordered** according their insertion in the signature object.
  """
  def __init__( self, *params ):
    """
    The constructor expects a list formatted as follow:
    parameter1_name (string), parameter1_type (:py:class:`Parameter`), ...
    
    Each couple parameter_name, parameter_type defines a parameter. The parameter name is a string which must also be a Python variable name, so it can contain only letters (uppercase or lowercase), digits or underscore character. Moreover some Python reserved word are forbidden (and, assert, break, class, continue, def, del, elif, else, except, exec, finally, for, from, global, if, import, in, print, is, lambda, not ,or , pass, raise, return, try, why). The parameter type is an instance of :py:class:`Parameter` class and indicates the supported value type for this parameter. 
    """
    self.sortedKeys = []
    self.data = {}
    i = 0
    while i < len( params ):
      ( name, value ) = params[i:i+2]
      self.sortedKeys.append( name,)
      self.data[ name ] = value
      i += 2

  def keys( self ):
    """
    Returns the list of parameters names.
    """
    return self.sortedKeys

  def iteritems( self ):
    """
    iterates over a list of tuple (parameter_name, parameter_type) for each parameter.
    """
    for x in self.sortedKeys:
      yield (x, self.data[x])

  def items( self ):
    """
    Returns a list of tuple (parameter_name, parameter_type) for each parameter.
    """
    return [(x, self.data[x]) for x in self.sortedKeys]

  def values( self ):
    """
    Returns the list of parameters types.
    """
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
    if k not in self.data:
      self.sortedKeys.append(k)
    self.data[k] = value

  def shallowCopy(self):
    """
    Returns a shallow copy of the current signature. Only the parameters names are duplicated, the list of parameters types is shared.
    """
    new = copy.copy(self)
    new.sortedKeys = copy.copy(self.sortedKeys)
    return new

  def deepCopy(self):
    """
    Returns a deep copy of the current signature. Both the parameters names and list of parameters types are duplicated.
    """
    def copyType( t ):
      n = copy.copy( t )
      if hasattr(n, 'contentType') :
        n.contentType = copyType( n.contentType )
      
      return n
      
    new = copy.copy(self)
    new.sortedKeys = copy.copy(self.sortedKeys)
    new.data = copy.copy( self.data )
    
    for k, i in six.iteritems(new.data):
      new.data[ k ] = copyType( i )

    return new
    
#----------------------------------------------------------------------------

def initializeData():
  pass
