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

from brainvisa.processes import (
    Signature, Choice, OpenChoice, neuroConfig,
)
from brainvisa.data import neuroHierarchy
from brainvisa.data.databaseCheck import BVChecker_3_1


name = 'Check database batch'
userLevel = 0
require_databasing = True

signature = Signature(
    'database', Choice()
)


def initialization(self):
    if len(neuroHierarchy.databases._databases) == 0:
        self.signature['database'] = OpenChoice()
        databases = None
    else:
        databases = [dbs.directory
                     for dbs in neuroConfig.dataPath if not dbs.builtin]
        self.signature['database'].setChoices(*databases)
    if databases:
        self.database = databases[0]
    else:
        self.database = None


def execution(self, context):
    database = self.database
    print('neuroConfig.dataPath:', [dbs.directory for dbs in neuroConfig.dataPath])
    print('neuroHierarchy.databases:', neuroHierarchy.databases._databases)
    database = neuroHierarchy.databases.database(self.database)
    checker = BVChecker_3_1(database, context)
    checker.findActions()
    checker.process(debug=True)
