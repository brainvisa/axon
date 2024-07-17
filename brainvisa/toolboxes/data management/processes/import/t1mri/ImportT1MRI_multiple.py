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

from brainvisa.processes import *
from brainvisa.tools import aimsGlobals
from brainvisa import registration
from brainvisa.data import neuroHierarchy
import os.path as osp
import json

from brainvisa.tools.data_management.image_importation import Importer

name = 'Import T1 MRI (multiple)'
roles = ('importer',)
userLevel = 0


signature = Signature(
    'inputs', ListOf(ReadDiskItem(
        'T1 MRI',
        'Aims readable volume formats')),
    'outputs', ListOf(WriteDiskItem(
        'Raw T1 MRI',
        'Aims writable volume formats')),
    'referentials', ListOf(
        WriteDiskItem('Referential of Raw T1 MRI', 'Referential')),
    'output_database', Choice(),
    'attributes_merging', Choice('BrainVisa', 'header',
                                 'selected_from_header'),
    'selected_attributes_from_header', ListOf(String()),
    'subjects', ListOf(String()),
    'center', String(),
    'acquisition', String(),
    'other_attributes', String(),
)


def initSubjects(self, proc, dummy):
    if not self.inputs:
        return None
    subjects = []

    for input in self.inputs:
        subject = None
        if isinstance(input, DiskItem):
            value = input.hierarchyAttributes()
            subject = value.get("subject", None)
            input = input.fullPath()
        if subject is None:
            bn = osp.basename(input)
            bne = bn.split('.')
            while len(bne) > 2 and bne[-1] in ('gz', 'Z', 'zip', 'tar'):
                del bne[-1]
            subject = '.'.join(bne[:-1])
        subjects.append(subject)

    return subjects


def initOutputs(self, proc, dummy):
    if not self.inputs:
        return None
    values = []

    for num, input in enumerate(self.inputs):
        subject = None
        value = {}
        if self.subjects and len(self.subjects) > num:
            subject = self.subjects[num]
        if isinstance(input, DiskItem):
            value = input.hierarchyAttributes()
        if self.output_database:
            value['_database'] = self.output_database
            for a in ['_ontology', ]:  # '_declared_attributes_location', ]:
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
        if self.center is not None:
            value['center'] = self.center
        if self.acquisition is not None:
            value['acquisition'] = self.acquisition
        if self.other_attributes is not None:
            attr = json.loads(self.other_attributes)
            value.update(attr)
        if subject is not None:
            value['subject'] = subject
        elif value.get("subject", None) is None \
                and isinstance(input, DiskItem):
            value["subject"] = osp.basename(
                input.fullPath()).partition(".")[0]
        if self.attributes_merging in ('header', 'selected_from_header'):
            hvalues = aimsGlobals.aimsVolumeAttributes(input)
            if self.attributes_merging == 'selected_from_header':
                hvalues = dict([(k, v) for k, v in hvalues.items()
                                if k in self.selected_attributes_from_header])
            value.update(hvalues)
        if 'subject' not in value:
            value = None

        values.append(value)

    return values


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

    self.linkParameters("subjects",
                        ("inputs", "attributes_merging",
                         "selected_attributes_from_header"), self.initSubjects)
    self.linkParameters("outputs",
                        ("inputs", "output_database", "attributes_merging",
                         "selected_attributes_from_header", "subjects",
                         "acquisition"), self.initOutputs)
    self.signature['outputs'].browseUserLevel = 3
    self.signature['inputs'].databaseUserLevel = 2
    self.signature['referentials'].userLevel = 2
    self.setOptional('referentials', 'output_database', 'attributes_merging',
                     'selected_attributes_from_header', 'acquisition',
                     'center', 'other_attributes')
    self.linkParameters('referentials', 'outputs')


def execution(self, context):
    for num, (input, output) in enumerate(zip(self.inputs, self.outputs)):

        results = Importer.import_t1mri(input.fullPath(),
                                        output.fullPath())
        if results['return_value'] != 0:
            raise RuntimeError('Importation failed for %s into %s'
                               % (input.fullPath(), output.fullPath()))
        if 'warnings' in results:
            for message in results['warnings']:
                context.warning(message)
        # merge hierarchy and minf attributes
        hatt = output.hierarchyAttributes()
        # force completing .minf
        minfatt = aimsGlobals.aimsVolumeAttributes(output)
        for x, y in minfatt.items():
            if x in hatt and y != hatt[x]:
                # conflicting value, the hierarchy wins.
                context.warning('conflicting attribute %s:' % x, y, 'becomes',
                                hatt[x])
                y = hatt[x]
            if x != "dicom":
                output.setMinf(x, y)
        output.saveMinf()
        output.readAndUpdateMinf()
        # the referential can be written in the file header (nifti)
        if output.minf().get('referential', None):
            output.removeMinf('referential')
        tm = registration.getTransformationManager()
        referential = None
        if self.referentials is not None and len(self.referentials) > num:
            referential = self.referentials[num]
            if referential is not None:
                tm.createNewReferential(referential)
                tm.setReferentialTo(output, referential)
        if referential is None:
            ref = tm.createNewReferentialFor(output, name='Raw T1 MRI')
