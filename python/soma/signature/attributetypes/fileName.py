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
import os
from soma.signature.attributetypes.six.text_type import Unicode
import six

#-------------------------------------------------------------------------


class FileName(Unicode):

    def __init__(self, readOnly=False, directoryOnly=False):
        Unicode.__init__(self)
        self.readOnly = bool(readOnly)
        self.directoryOnly = bool(directoryOnly)

    def __getinitkwargs__(self):
        args, kwargs = Unicode.__getinitkwargs__(self)
        if self.readOnly:
            kwargs['readOnly'] = True
        if self.directoryOnly:
            kwargs['directoryOnly'] = True
        return (), kwargs

    def checkValue(self, value):
        if value is not None and value != '':
            if os.path.exists(value):
                if self.directoryOnly and not os.path.isdir(value):
                    raise ValueError('Not a directory: "' + value + '"')
            elif self.readOnly:
                raise ValueError('No such file or directory: "' + value + '"')
        return value
