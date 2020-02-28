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
import time

from brainvisa.tools.data_management.image_importation import Importer

name = 'Import T1 MRI, longitudinal version'
# roles = ('importer',)
userLevel = 0


signature = Signature(
    'input', ReadDiskItem('Raw T1 MRI', 'Aims readable volume formats'),
    'output_database', Choice(),
    'center', String(),
    'subject', String(),
    'acquisition', String(),
    'time_point', String(),
    'time_duration', String(),
    'rescan', String(),
    'acquisition_date', String(),
    'output', WriteDiskItem('Raw T1 MRI',
                            ['gz compressed NIFTI-1 image', 'NIFTI-1 image', 'GIS image']),
    'referential', WriteDiskItem('Referential of Raw T1 MRI', 'Referential'),
)


def initialization(self):

    def linkDB(proc, dummy):
        if proc.input is not None:
            idbn = proc.input.get('_database')
            if idbn is not None:
                return idbn
        return proc.output_database

    def linkSubject(proc, dummy):
        subject = ''
        if proc.input is not None and isinstance(proc.input, DiskItem):
            value = proc.input.hierarchyAttributes()
            subject = value.get("subject", None)
            if subject is None:
                subject = \
                    os.path.basename(proc.input.fullPath()).partition(".")[0]
        return subject

    def initSubject(proc, dummy):
        value = proc.input
        if proc.input is not None and isinstance(proc.input, DiskItem):
            value = proc.input.hierarchyAttributes()
            if proc.output_database:
                value['_database'] = proc.output_database.directory
            for attribute in ('center', 'subject', 'acquisition', ):
                attval = getattr(proc, attribute, None)
                if attval:
                    value[attribute] = attval
        return value

    databases = [
        (dbs.directory, neuroHierarchy.databases.database(dbs.directory))
        for dbs in neuroConfig.dataPath
        if not dbs.builtin
            and dbs.expert_settings.ontology.startswith('brainvisa-')]
    self.signature['output_database'].setChoices(*databases)
    if len(databases) != 0:
        self.output_database = databases[0][0]
    self.linkParameters('output_database', 'input', linkDB)
    self.linkParameters('subject', 'input', linkSubject)
    self.linkParameters("output",
                        ['input', 'output_database', 'center', 'subject', 'acquisition',
                         'time_point', 'time_duration', 'rescan', 'acquisition_date'],
                        initSubject)
    self.signature['output'].browseUserLevel = 3
    self.signature['input'].databaseUserLevel = 2
    self.signature['referential'].userLevel = 2
    self.setOptional('referential')
    self.linkParameters('referential', 'output')
    self.acquisition_date = time.strftime("%Y/%m/%d")
    self.time_point = 'timepoint_0'
    self.time_duration = '0'
    self.setOptional('center', 'acquisition', 'time_point', 'time_duration',
                     'rescan', 'acquisition_date')


def execution(self, context):
    acq_dir = os.path.dirname(self.output.fullPath())
    values = {}
    for attribute in ('time_point', 'time_duration', 'rescan',
                      'acquisition_date'):
        value = getattr(self, attribute)
        if value:
            values[attribute] = value
    if len(values) != 0:
        f = open(os.path.join(acq_dir, 'fso_attributes.json'), 'w')
        json.dump(values, f)
    del f
    context.runProcess('ImportT1MRI', input=self.input, output=self.output,
                       referential=self.referential)
    self.output.readAndUpdateDeclaredAttributes()
