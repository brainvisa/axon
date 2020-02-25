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
This module defines the class :py:class:`WriteDiskItem` which is a subclass :py:class:`brainvisa.data.neuroData.Parameter`.
It is used to define an output data file as a parameter in a :py:class:`brainvisa.processes.Process` :py:class:`brainvisa.data.neuroData.Signature`.
"""

from __future__ import absolute_import
from soma.undefined import Undefined
from brainvisa.data.neuroData import Parameter
from brainvisa.data.readdiskitem import ReadDiskItem
from brainvisa.data.neuroDiskItems import getFormats, getDiskItemType, DiskItem, isSameDiskItemType
from brainvisa.data.readdiskitem import ReadDiskItem


#----------------------------------------------------------------------------
class WriteDiskItem(ReadDiskItem):

    """
    The expected value for this parameter must be a writable :py:class:`brainvisa.data.neuroDiskItems.DiskItem`.

    :Syntax:

    ::

      WriteDiskItem( file_type_name, formats [, required_attributes={}, exactType=0, ignoreAttributes=0] )
      formats <- format_name
      formats <- [ format_name, ... ]


    This parameter type is very close to ReadDiskItem (WriteDiskItem derives from ReadDiskItem), but it accepts writable files. That is to say, it accepts not only files that are accepted by a ReadDiskItem but also files that doesn't exist yet. It has the same search methods as the ReadDiskItem class but these methods generate diskitems that may not exist yet, using data ontology information.
    """

    def __init__(self, diskItemType, formats, requiredAttributes={},
                 exactType=False, ignoreAttributes=False, _debug=None, section=None):
        ReadDiskItem.__init__(self, diskItemType,
                              formats, requiredAttributes=requiredAttributes, ignoreAttributes=ignoreAttributes, enableConversion=False, _debug=_debug, exactType=exactType, section=section)
        self._write = True

    def checkValue(self, name, value):
        Parameter.checkValue(self, name, value)

    def typeInfo(self, translator=None):
        if translator:
            translate = translator.translate
        else:
            translate = _t_
        ti = super(WriteDiskItem, self).typeInfo(translator)
        return (ti[0], ) + ((translate('Access'), translate('output')), ) + ti[2:]
