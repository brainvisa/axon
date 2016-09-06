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
from brainvisa.data import neuroHierarchy
from brainvisa.data.databaseCheck import DBCleaner
from brainvisa.data.qtgui.databaseCheckGUI import UnknownFilesWidget


name = '3 - Clean database'
userLevel = 0

signature = Signature( 
  'database', Choice(),
  'undo', Boolean()
 )

def initialization(self):
  databases=[(dbs.directory, neuroHierarchy.databases.database(dbs.directory)) for dbs in neuroConfig.dataPath if not dbs.builtin]
  self.signature['database'].setChoices(*databases)
  if databases:
    self.database=databases[0][1]
  else:
    self.database=None
  self.undo=False

def execution( self, context ):
  """
  @rtype: DBCleaner
  @return : the cleaner if user choose to clean later. None if actions are executed immediatly..
  """
  # database is a neuroDiskItems.Directory
  cleaner=DBCleaner(self.database, context)
  res=None
  if self.undo:
    context.write("* Run undo script "+cleaner.undoScriptName)
    cleaner.undo()
  else:
    actions=cleaner.findActions()
    if actions:
      # open  a widget that presents actions to the user. He can unselect some actions and choose to run immediatly or later.
      dialogRes=mainThreadActions().call(showActions, cleaner)
      if (dialogRes==1): # convert immediatly
        context.write("* Clean database")
        try:
          cleaner.process(debug=True)
        except Exception as e:
          context.error("Errors during conversion : "+str(e))
        context.write("* Generate undo script in database directory.")
        cleaner.generateUndoScripts()
      ### returning the converter does a segmentation error, I don't know why...
      elif dialogRes==2: # return the converter, actions may be executed later
        #context.write("Cleaning not done")
        res=cleaner
      else:
        context.write("Cancelled")
    else:
      context.write("Nothing to do !")
  return res
    
def showActions(dbCleaner):
  """
  Opens a dialog that presents suggested actions to the user. 
  @returns : True if the user choose to execute actions immediatly, false if he decided to run it later.
  """
  actionsWidget=UnknownFilesWidget(dbCleaner)
  
  if sys.modules.has_key( 'PyQt4' ):
    result=actionsWidget.exec_()
  else:
    result=actionsWidget.exec_loop()

  return result # convert immediatly
