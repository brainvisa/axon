# -*- coding: utf-8 -*-

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

"""Robust enumerated type support in Python

This package provides a module for robust enumerations in Python.

An enumeration object is created with a sequence of string arguments
to the Enum() constructor::

    >>> from enum import Enum
    >>> Colours = Enum('red', 'blue', 'green')
    >>> Weekdays = Enum('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')

The return value is an immutable sequence object with a value for each
of the string arguments. Each value is also available as an attribute
named from the corresponding string argument::

    >>> pizza_night = Weekdays[4]
    >>> shirt_colour = Colours.green

The values are constants that can be compared only with values from
the same enumeration; comparison with other values will invoke
Python's fallback comparisons::

    >>> pizza_night == Weekdays.fri
    True
    >>> shirt_colour > Colours.red
    True
    >>> shirt_colour == "green"
    False

Each value from an enumeration exports its sequence index
as an integer, and can be coerced to a simple string matching the
original arguments used to create the enumeration::

    >>> str(pizza_night)
    'fri'
    >>> shirt_colour.index
    2
"""
from __future__ import absolute_import
import math
import six

__author_name__ = "Ben Finney"
__author_email__ = "ben+python@benfinney.id.au"
__author__ = "%s <%s>" % (__author_name__, __author_email__)
__date__ = "2007-01-24"
__copyright__ = "Copyright © %s %s" % (
    __date__.split('-')[0], __author_name__
)
__license__ = "Choice of GPL or Python license"
__url__ = "http://cheeseshop.python.org/pypi/enum/"
__version__ = "0.4.3"


class EnumException(Exception):

    """ Base class for all exceptions in this module """

    def __init__(self):
        if self.__class__ is EnumException:
            raise NotImplementedError(
                "%s is an abstract class for subclassing" % self.__class__)


class EnumEmptyError(AssertionError, EnumException):

    """ Raised when attempting to create an empty enumeration """

    def __str__(self):
        return "Enumerations cannot be empty"


class EnumBadKeyError(TypeError, EnumException):

    """ Raised when creating an Enum with non-string keys """

    def __init__(self, key):
        self.key = key

    def __str__(self):
        return "Enumeration keys must be strings: %s" % (self.key,)


class EnumMissingKeyError(TypeError, EnumException):

    """ Raised when creating an Enum with non-string keys """

    def __init__(self, enumtype, key):
        self.__enumtype = enumtype
        self.key = key

    def __str__(self):
        return "Enumeration key '%s' does not exists in enumeration : %s" % (self.key, self.__enumtype)


class EnumImmutableError(TypeError, EnumException):

    """ Raised when attempting to modify an Enum """

    def __init__(self, *args):
        self.args = args

    def __str__(self):
        return "Enumeration does not allow modification"


class EnumValues(object):

    """ Values of an enumerated type """

    def __init__(self, enumtype, values=0):
        """ Set up a new instance """
        super(EnumValues, self).__init__()

        self.__enumtype = enumtype
        self.__values = 0

        if not hasattr(values, '__iter__'):
            values = [values]

        for value in values:
            try:
                self.__values |= int(value)
            except Exception as e:
                try:
                    self |= self.__enumtype.__dict__.get(value)
                except Exception as e:
                    try:
                        self |= value
                    except Exception as e:
                        raise EnumMissingKeyError(values, self.__enumtype)

    def __contains__(self, enumval):
        if (enumval not in self.__enumtype):
            raise EnumMissingKeyError(self.__enumtype, enumval)

        return int(self.__values) & int(math.pow(2, enumval.index))

    def __eq__(self, enumval):
        if (type(enumval) == EnumValues) and (enumval.__enumtype == self.__enumtype):
            return (self.__values == enumval.__values)
        elif (enumval in self.__enumtype):
            return (self.__values == int(math.pow(2, enumval.index)))
        else:
            raise EnumMissingKeyError(self.__enumtype, enumval)

    def __ne__(self, enumval):
        return not (self == enumval)

    def __ior__(self, enumval):
        if (enumval not in self.__enumtype):
            raise EnumMissingKeyError(self.__enumtype, enumval)

        self.__values |= int(math.pow(2, enumval.index))
        return self

    def __ixor__(self, enumval):
        if (enumval not in self.__enumtype):
            raise EnumMissingKeyError(self.__enumtype, enumval)

        self.__values ^= int(math.pow(2, enumval.index))
        return self

    def __iter__(self):
        for value in self.__enumtype:
            if value in self:
                yield value

    def __len__(self):
        return len(list(iter(self)))

    def empty(self):
        return (self.__values == 0)

    def __str__(self):
        return str(list(iter(self)))


class EnumValue(object):

    """ A specific value of an enumerated type """

    def __init__(self, enumtype, index, key):
        """ Set up a new instance """
        self.__enumtype = enumtype
        self.__index = index
        self.__key = key

    def __get_enumtype(self):
        return self.__enumtype
    enumtype = property(__get_enumtype)

    def __get_key(self):
        return self.__key
    key = property(__get_key)

    def __str__(self):
        return "%s" % (self.key)

    def __get_index(self):
        return self.__index
    index = property(__get_index)

    def __repr__(self):
        return "EnumValue(%s, %s, %s)" % (
            repr(self.__enumtype),
            repr(self.__index),
            repr(self.__key),
        )

    def __hash__(self):
        return hash(self.__index)

    def __cmp__(self, other):
        result = NotImplemented
        self_type = self.enumtype
        try:
            assert self_type == other.enumtype
            result = cmp(self.index, other.index)
        except (AssertionError, AttributeError):
            result = NotImplemented

        return result


class Enum(object):

    """ Enumerated type """

    def __init__(self, *keys, **kwargs):
        """ Create an enumeration instance """

        value_type = kwargs.get('value_type', EnumValue)

        if not keys:
            raise EnumEmptyError()

        keys = tuple(keys)
        values = [None] * len(keys)

        for i, key in enumerate(keys):
            value = value_type(self, i, key)
            values[i] = value
            try:
                super(Enum, self).__setattr__(key, value)
            except TypeError as e:
                raise EnumBadKeyError(key)

        super(Enum, self).__setattr__('_keys', keys)
        super(Enum, self).__setattr__('_values', values)

    def __setattr__(self, name, value):
        raise EnumImmutableError(name)

    def __delattr__(self, name):
        raise EnumImmutableError(name)

    def __len__(self):
        return len(self._values)

    def __getitem__(self, index):
        return self._values[index]

    def __setitem__(self, index, value):
        raise EnumImmutableError(index)

    def __delitem__(self, index):
        raise EnumImmutableError(index)

    def __iter__(self):
        return iter(self._values)

    def __contains__(self, value):
        is_member = False
        if isinstance(value, six.string_types):
            is_member = (value in self._keys)
        else:
            try:
                is_member = (value in self._values)
            except EnumValueCompareError as e:
                is_member = False
        return is_member
