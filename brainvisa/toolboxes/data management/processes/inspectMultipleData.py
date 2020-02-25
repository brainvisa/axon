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

from __future__ import absolute_import
from brainvisa.processes import *
from brainvisa.data.neuroHierarchy import databases

name = 'Inspect Multiple Data'
userLevel = 0


def allowed_processes(process):
    return True


signature = Signature(
    'items', ListOf(ReadDiskItem('Any Type', getAllFormats())),
    'data_type', Choice('Any Type'),
)


def dataTypeChanged(self, dataType):
    if dataType:
        formats = list(databases.getTypesFormats(dataType))
        if not formats:
            formats = getAllFormats()
        self.signature['items'] = ListOf(ReadDiskItem(dataType, formats))
        self.signatureChangeNotifier.notify(self)


def initialization(self):
    possibleTypes = [t.name for t in getAllDiskItemTypes()]
    self.signature['data_type'].setChoices(*sorted(possibleTypes))
    self.data_type = 'Any Type'
    self.addLink('items', 'data_type', self.dataTypeChanged)


def execution(self, context):
    if len(self.items) == 0:
        return
    proc = Process()
    proc._id = 'MultipleDataInspector'
    proc.name = 'Multiple data inspector'
    proc.inlineGUI = lambda self, parent=None, other=None: QWidget(parent)
    if self.data_type != 'Any Type':
        formats = list(databases.getTypesFormats(self.data_type))
    else:
        formats = list(databases.getTypesFormats(self.items[0].type.name))
    sign = []
    params = {}
    itemtypes = self.signature['items']
    for i, p in enumerate(self.items):
        sign += ['item_%d' %
                 i, ReadDiskItem(self.items[i].type.name, formats)]
        params['item_%d' % i] = p
    proc.signature = Signature(*sign)
    proc.__dict__.update(params)
    ref_proc = getattr(self, 'reference_process', None)
    if ref_proc is not None:
        proc.allowed_processes = lambda proc: True
        proc.reference_process = ref_proc
    pv = mainThreadActions().call(ProcessView, proc)
    mainThreadActions().call(pv.info.hide)
    return pv
