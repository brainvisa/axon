# Copyright CEA and IFR 49 (2000-2005)
#
#  This software and supporting documentation were developed by
#      CEA/DSV/SHFJ and IFR 49
#      4 place du General Leclerc
#      91401 Orsay cedex
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
import qt
import neuroConfig
import neuroException
from brainvisa.data.databaseCheck import BVConverter_3_1
from brainvisa.data.databaseCheckGUI import ActionsWidget

name = 'Convert old database'
userLevel = 0

signature = Signature( 
  'database', Choice(), 
  'segment_default_destination', Choice(None, "t1mri", "pet"),
  'graphe_default_destination', Choice(None, "t1mri_folds", "t1mri_roi", "pet_roi"),
  'undo', Boolean()
 )
 
def setCheckSelection( self, undo ):
  eNode = self.executionNode()
  if undo:
    eNode.CheckDatabase.setSelected( False )
  else:
    eNode.CheckDatabase.setSelected( True )


def initialization( self ):
  databases=[(h.name, h) for h in reversed(neuroHierarchy.hierarchies())]# reverse order of hierarchies to have brainvisa shared hierarchy at the end of the list
  self.signature['database'].setChoices(*databases)
  self.database=databases[0][1]
  self.segment_default_destination="t1mri"
  self.graphe_default_destination="t1mri_folds"
  self.undo=False

  self.setOptional("segment_default_destination")
  self.setOptional("graphe_default_destination")

  eNode = SerialExecutionNode( self.name, parameterized=self )

  eNode.addChild( 'ConvertDatabase',
                  ProcessExecutionNode( 'convertDatabase', optional = 1 ) )

  eNode.addChild( 'CheckDatabase',
                   ProcessExecutionNode( 'checkDatabase',
                                         optional = 1 ) )
   
  eNode.addChild( 'CleanDatabase',
                  ProcessExecutionNode( 'cleanDatabase',
                                        optional = 1, selected=False ) )

 # links
  eNode.addLink( 'ConvertDatabase.database', 'database' )
  eNode.addLink( 'database', 'ConvertDatabase.database' )

  eNode.addLink( 'CleanDatabase.database', 'database' )
  eNode.addLink( 'database', 'CleanDatabase.database' )

  eNode.addLink( 'CheckDatabase.database', 'database' )
  eNode.addLink( 'database', 'CheckDatabase.database' )

  eNode.addLink( 'ConvertDatabase.segment_default_destination', 'segment_default_destination' )
  eNode.addLink( 'segment_default_destination', 'ConvertDatabase.segment_default_destination' )
  
  eNode.addLink( 'ConvertDatabase.graphe_default_destination', 'graphe_default_destination' )
  eNode.addLink( 'graphe_default_destination', 'ConvertDatabase.graphe_default_destination' )

  eNode.addLink( 'ConvertDatabase.undo', 'undo' )
  eNode.addLink( 'undo',  'ConvertDatabase.undo' )
  
  eNode.addLink( 'CleanDatabase.undo', 'undo' )
  eNode.addLink( 'undo',  'CleanDatabase.undo' )
   
  eNode.addLink( None, 'undo', self.setCheckSelection )
  
  self.setExecutionNode( eNode )

def execution( self, context ):
  res=Process.execution(self, context)
  if res:
    for processor in res:
      if processor:
        context.write("* Process database with ", str(processor.__class__))
        try:
            processor.process(debug=True)
        except Exception, e:
            context.error("Errors during processing : "+str(e))
        context.write("* Generate undo scripts in database directory.")
        processor.generateUndoScripts()

  
