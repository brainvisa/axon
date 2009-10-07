#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCIL license version 2 under
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
# knowledge of the CeCILL version 2 license and that you accept its terms.

from neuroProcesses import *
import neuroHierarchy, neuroDiskItems
from brainvisa.data.databaseCheck import BVChecker_3_1
from brainvisa.data.qtgui.databaseCheckGUI import CheckFilesWidget
import shfjGlobals


name = '2 - Check database'
userLevel = 0

signature = Signature( 
  'database', Choice()
 )

def initialization(self):
  databases=[(h.name, h) for h in reversed(neuroHierarchy.hierarchies())]
  self.signature['database'].setChoices(*databases)
  self.database=databases[0][1]
  
def execution( self, context ):
  """
  """
  res=None
  checker=BVChecker_3_1(self.database, context)
  checker.findActions()
  dialogRes=mainThreadActions().call(show, checker)
  if (dialogRes==1):
    context.write("run actions")
    try:
      checker.process(debug=True)
    except Exception, e:
      context.error("Errors during conversion : "+str(e))
  elif dialogRes==2:
    res=checker
  else:
    context.write("Cancelled")
  return res
  
def show(checker):
  """
  Opens a dialog that presents suggested actions to the user. 
  @returns : True if the user choose to execute actions immediatly, false if he decided to run it later.
  """
  widget=CheckFilesWidget(checker)
  result=widget.exec_loop()
  return result # convert immediatly

