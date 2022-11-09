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


'''
@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
from __future__ import absolute_import
__docformat__ = "epytext en"


from brainvisa.processes import *
import brainvisa.processing.qtgui.backwardCompatibleQt as qt
from brainvisa.configuration import neuroConfig
from brainvisa.data.neuroHierarchy import databases
from brainvisa.data.qtgui.updateDatabases import UpdateDatabasesGUI

name = 'Update databases'
userLevel = 0

signature = Signature(
    'databases', ListOf(ReadDiskItem('Directory', 'Directory'),
                        userLevel=1000),
    'method', Choice('full', 'incremental', 'full_history', userLevel=1000),
)


def initialization(self):
    self.method = 'full'


def execution(self, context):
    dbases = [databases.database(d.fullPath()) for d in self.databases]
    classic_method = (self.method == 'full')
    quick_hf_method = (self.method == 'incremental')
    history_files_method = (self.method == 'full_history')

    for database in dbases:
        # must close the connection currently opened in the main thread before
        # clearing and updating the database
        #mainThreadActions().call(database.currentThreadCleanup)
        if classic_method:
            database.clear(context=context)
            context.write('<b>Clear database:', database.name, '</b>')
        context.write('<b>Update database:', database.name, '</b>')

        if classic_method:
            database.update(context=context)
        elif database.activate_history:
            if quick_hf_method:
                database.updateHistoryFiles(
                    context=context, scanAllBvproc=False)
            elif history_files_method:
                database.updateHistoryFiles(
                    context=context, scanAllBvproc=True)
        else:
            context.write("The history option is not activated.")


def inlineGUI(self, values, context, parent, externalRunButton=False):
    result = UpdateDatabasesGUI(parent)
    self.context = context
    result.btnClearAndUpdate.clicked.connect(self.run_button_clicked)
    return result


def run_button_clicked(self, checked=False):
    try:
        databases = self.context.inlineGUI.selectedDatabases()
        # must close the connection currently opened in the main thread before
        # clearing and updating the database
        database = None
        for database in databases:
            database.currentThreadCleanup()
        del database

        self.databases = [x.directory for x in databases]
        if self.context.inlineGUI.quick_hf_method():
            self.method = 'incremental'
        elif self.context.inlineGUI.history_files_method():
            self.method = 'full_history'
        else:
            self.method = 'full'
        self.context._runButton()
    except Exception as e:
        #self.context.showException()
        import traceback
        traceback.print_exc()
