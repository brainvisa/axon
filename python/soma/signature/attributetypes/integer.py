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

from __future__ import absolute_import
import types
import sys
from soma.signature.attributetypes.number import Number

import six

if not six.PY2:
    long = int

#-------------------------------------------------------------------------


class Integer(Number):

    '''Parameter value is an integer (either a Python int or a Python long).'''

    def __init__(self, minimum=None, maximum=None):
        Number.__init__(self)
        if minimum is None:
            self.minimum = None
        else:
            self.minimum = long(minimum)
        if maximum is None:
            self.maximum = None
        else:
            self.maximum = long(maximum)

    def checkValue(self, value):
        if not isinstance(value, float):
            return Number.checkValue(self, value)
        self._checkValueError(value)

    def convert(self, value, checkValue=None):
        value = int(value)
        return value


#-------------------------------------------------------------------------
class IntegerU8(Integer):

    def __init__(self):
        Integer.__init__(self, 0, 255)


#-------------------------------------------------------------------------
class IntegerS8(Integer):

    def __init__(self):
        Integer.__init__(self, -128, 127)


#-------------------------------------------------------------------------
class IntegerU16(Integer):

    def __init__(self):
        Integer.__init__(self, 0, 65535)


#-------------------------------------------------------------------------
class IntegerS16(Integer):

    def __init__(self):
        Integer.__init__(self, -32768, 32767)

#-------------------------------------------------------------------------


class IntegerU32(Integer):

    def __init__(self):
        Integer.__init__(self, 0, 4294967295)


#-------------------------------------------------------------------------
class IntegerS32(Integer):

    def __init__(self):
        Integer.__init__(self, -2147483648, 2147483647)


#-------------------------------------------------------------------------
class IntegerU64(Integer):

    def __init__(self):
        Integer.__init__(self, 0, 18446744073709551615)


#-------------------------------------------------------------------------
class IntegerS64(Integer):

    def __init__(self):
        Integer.__init__(self, -9223372036854775808, 9223372036854775807)
