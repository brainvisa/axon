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

from neuroProcesses import *
from neuroProcessesGUI import mainThreadActions
import neuroHierarchy
import neuroConfig
import neuroException
from brainvisa.data.databaseCheck import BVConverter_3_1
from brainvisa.data.qtgui.databaseCheckGUI import ActionsWidget
import os, shutil, sys

name = '1 - Convert Database'
userLevel = 0

signature = Signature( 
  'database', Choice(),
  'segment_default_destination', Choice(None, "t1mri", "pet"),
  'graphe_default_destination', Choice(None, "t1mri_folds", "t1mri_roi", "pet_roi"),
  'undo', Boolean()
 )

def initialization(self):
  databases=[(h.name, h) for h in reversed(neuroHierarchy.hierarchies())]
  self.signature['database'].setChoices(*databases)
  self.database=databases[0][1]
  self.segment_default_destination="t1mri"
  self.graphe_default_destination="t1mri_folds"
  self.undo=False
  
  self.setOptional("segment_default_destination")
  self.setOptional("graphe_default_destination")

def execution( self, context ):
  """
  @rtype: DBConverter
  @return : the converter if user choose to convert later. None if the database is converted.
  """
  # database is a neuroDiskItems.Directory
  context.write("database :", self.database.name)
  dbDir=self.database.name
  res=None
  if not os.path.exists(dbDir):
    raise Exception(dbDir+" does not exist.")
  converter=BVConverter_3_1(self.database, context, self.segment_default_destination, self.graphe_default_destination)
  if self.undo:
    context.write("* Run undo scripts.")
    converter.undo()
  else:
    actions=converter.findActions()
    if actions:
      # open  a widget that presents actions to the user. He can unselect some actions and choose to run immediatly or later.
      if (mainThreadActions().call(showActions, converter) == 1): # convert immediatly
        context.write("* Convert database")
        try:
          converter.process(debug=True)
        except Exception, e:
          context.error("Errors during conversion : "+str(e))
        context.write("* Generate undo scripts in database directory.")
        converter.generateUndoScripts()
      else: 
        context.write("Cancelled")
    else:
      context.write("Nothing to do !")
  return res

def showActions(actions):
  """
  Opens a dialog that presents suggested actions to the user. 
  @returns : True if the user choose to execute actions immediatly, false if he decided to run it later.
  """
  actionsWidget=ActionsWidget(actions)
  actionsWidget.runLaterButton.setEnabled(False)
  
  if sys.modules.has_key( 'PyQt4' ):
    result=actionsWidget.exec_()
  else:
    result=actionsWidget.exec_loop()
    
  return result # convert immediatly
