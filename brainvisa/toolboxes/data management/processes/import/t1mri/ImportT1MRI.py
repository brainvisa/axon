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
from brainvisa import shelltools
from brainvisa.tools import aimsGlobals
import stat
from brainvisa import registration
from brainvisa.data import neuroHierarchy

from brainvisa.tools.data_management.image_importation import Importer
import six
from six.moves import map

name = 'Import T1 MRI'
roles = ('importer',)
userLevel = 0


signature = Signature(
    'input', ReadDiskItem(
        'T1 MRI',
        'Aims readable volume formats'),
    'output', WriteDiskItem(
        'Raw T1 MRI',
        'Aims writable volume formats'),
    'referential', WriteDiskItem('Referential of Raw T1 MRI', 'Referential'),
    'output_database', Choice(),
    'attributes_merging', Choice('BrainVisa', 'header',
                                 'selected_from_header'),
    'selected_attributes_from_header', ListOf(String()),
)


def initSubject(self, proc, dummy):
    if not self.input:
        return None
    if not isinstance(self.input, DiskItem):
        return self.input
    value = self.input.hierarchyAttributes()
    if self.output_database:
        value['_database'] = self.output_database
        for a in ['_ontology', ]:  #'_declared_attributes_location', ]:
            if a in value:
                del value[a]

        if 'session' not in value:
            fso_names = [h.fso.name for h in neuroHierarchy.hierarchies()
                         if h.name == self.output_database]
            if len(fso_names) != 0 and 'bids' in fso_names[0]:
                # this default value should be filled automatically
                # - but is not...
                value['session'] = '1'
    hvalues = {}
    if value.get("subject", None) is None:
        value["subject"] = os.path.basename(
            self.input.fullPath()).partition(".")[0]
    if self.attributes_merging in ('header', 'selected_from_header'):
        hvalues = aimsGlobals.aimsVolumeAttributes(self.input)
        if self.attributes_merging == 'selected_from_header':
            hvalues = dict([(k, v) for k, v in six.iteritems(hvalues)
                            if k in
                                self.selected_attributes_from_header])
        value.update(hvalues)
    return value


def initialization(self):
    # list of possible databases, while respecting the ontology
    # ontology: brainvisa-3.2.0
    databases = [h.name for h in neuroHierarchy.hierarchies()
                 if not h.builtin and (h.fso.name == "brainvisa-3.2.0"
                                       or 'morphologist' in h.fso.name)]
    self.signature["output_database"].setChoices(*databases)
    if len(databases) != 0:
        self.output_database = databases[0]
    else:
        self.signature["output_database"] = OpenChoice()

    self.linkParameters("output",
                        ("input", "output_database", "attributes_merging",
                         "selected_attributes_from_header"), self.initSubject)
    self.signature['output'].browseUserLevel = 3
    self.signature['input'].databaseUserLevel = 2
    self.signature['referential'].userLevel = 2
    self.setOptional('referential', 'output_database', 'attributes_merging',
                     'selected_attributes_from_header')
    self.linkParameters('referential', 'output')


def execution(self, context):
    if self.input.format in list(map(getFormat,
                                ('SPM image', 'Series of SPM image'))):
        context.warning("The image is in Analyze format: be careful, the image"
                        " orientation could be wrong.")
    results = Importer.import_t1mri(self.input.fullPath(),
                                    self.output.fullPath())
    if results['return_value'] != 0:
        raise RuntimeError('Importation failed.')
    if 'warnings' in results:
        for message in results['warnings']:
            context.warning(message)
    # merge hierarchy and minf attributes
    hatt = self.output.hierarchyAttributes()
    # force completing .minf
    minfatt = aimsGlobals.aimsVolumeAttributes(self.output)
    for x, y in minfatt.items():
        if x in hatt and y != hatt[x]:
            # conflicting value, the hierarchy wins.
            context.warning('conflicting attribute %s:' % x, y, 'becomes',
                            hatt[x])
            y = hatt[x]
        if x != "dicom":
            self.output.setMinf(x, y)
    self.output.saveMinf()
    self.output.readAndUpdateMinf()
    # the referential can be written in the file header (nifti)
    if self.output.minf().get('referential', None):
        self.output.removeMinf('referential')
    tm = registration.getTransformationManager()
    if self.referential is not None:
        tm.createNewReferential(self.referential)
        tm.setReferentialTo(self.output, self.referential)
    else:
        ref = tm.createNewReferentialFor(self.output, name='Raw T1 MRI')
