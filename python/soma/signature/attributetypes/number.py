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

from __future__ import absolute_import
from soma.translation import translate as _
from soma.signature.api import DataType

#-------------------------------------------------------------------------


class Number(DataType):

    '''
    Parameter value is any number type.
    '''

    def __init__(self, minimum=None, maximum=None):
        DataType.__init__(self)
        self.mutable = False

        if minimum is None:
            self.minimum = None
        else:
            self.minimum = float(minimum)
        if maximum is None:
            self.maximum = None
        else:
            self.maximum = float(maximum)

    def __getinitkwargs__(self):
        args, kwargs = DataType.__getinitkwargs__(self)
        if self.minimum is not None:
            kwargs['minimum'] = self.minimum
        if self.maximum is not None:
            kwargs['maximum'] = self.maximum
        return (), kwargs

    def checkValue(self, value):
        if isinstance( value, int ) or isinstance( value, float ):
            if ( self.minimum is not None and value < self.minimum ) or \
               (self.maximum is not None and value > self.maximum):
                if self.maximum is None:
                    message = _(
                        'Value should be greater or equal to %(minimum)g')
                elif self.minimum is None:
                    message = _(
                        'Value should be less or equal to %(maximum)g')
                else:
                    message = _(
                        'Value should be between %(minimum)g and %(maximum)g')
                raise ValueError(_(message) %
                                 {'minimum': self.minimum, 'maximum': self.maximum})
            return value

        self._checkValueError(value)

    def convert(self, value, checkValue=None):
        try:
            value = int(value)
        except ValueError:
            value = float(value)
        return value

    def createValue(self):
        return 0
