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
from __future__ import print_function
from __future__ import absolute_import
from brainvisa.wip.newProcess import NewProcess
from soma.signature.api import Signature, Unicode, Number


class TestProcess(NewProcess):
    name = '/tests/new signature/test'
    signature = Signature(
        's', Unicode,
      'n', Number,
    )

    def __init__(self):
        super(TestProcess, self).__init__()
        self.s = 'test'
        self.n = 42

    def run(self):
        for n in list(self.signature.keys())[1:]:
            print(repr(n), '=', repr(getattr(self, n)),
                  file=self.userContext.stdout)


class TestProcess2(TestProcess):
    name = '/tests/new signature/test2'


class TestProcess3(TestProcess):
    name = '/tests2/new signature/test3'


class TestProcess4(TestProcess):
    name = '/tests2/new signature2/test4'


TestProcess.registerInBrainVISA()
TestProcess2.registerInBrainVISA()
TestProcess3.registerInBrainVISA()
TestProcess4.registerInBrainVISA()

# mainWindow = neuroProcessesGUI._mainWindow

# testTree = neuroProcesses.ProcessTree( name='tests', editable=False, user=False )
# signatureTree = testTree.Branch( name='new signature', editable=False )
# testTree.append( signatureTree )
# processLeaf = testTree.Leaf( processId=TestProcess, icon='icon_process_3.png', name='test', editable=False )
# signatureTree.append( processLeaf )
# mainWindow.processTrees.model.append( testTree )
