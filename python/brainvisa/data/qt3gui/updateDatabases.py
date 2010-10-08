# -*- coding: iso-8859-1 -*-

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
__docformat__ = "epytext en"

import backwardCompatibleQt as qt
#from soma.functiontools import partial
import neuroConfig
import neuroHierarchy
from neuroProcesses import getProcessInstance
from neuroProcessesGUI import ProcessView

class UpdateDatabasesGUI( qt.QWidget ):
  def __init__( self, parent ):
    super( UpdateDatabasesGUI, self ).__init__( parent )
    layout = qt.QVBoxLayout( self, 11, 6 )
    self.lvDatabases = qt.QListView( self )
    self.lvDatabases.addColumn( _t_( 'Database' ) )
    self.lvDatabases.header().hide()
    self.lvDatabases.setSorting( -1 )
    layout.addWidget( self.lvDatabases )
    
    lastItem = None
    selected = False
    for database in neuroHierarchy.databases.iterDatabases():
      item = qt.QCheckListItem( self.lvDatabases, lastItem, database.name, qt.QCheckListItem.CheckBox )
      item.setOn( selected )
      selected = True
      lastItem = item

    layout1 = qt.QHBoxLayout(None,0,6)
    layout.addLayout( layout1 )
    spacer1 = qt.QSpacerItem(1,1,qt.QSizePolicy.Expanding,qt.QSizePolicy.Minimum)
    layout1.addItem(spacer1)

    self.btnClearAndUpdate = qt.QPushButton( _t_( '&Update' ), self )
    layout1.addWidget( self.btnClearAndUpdate )
    
    #self.btnClear = qt.QPushButton( _t_( '&Clear' ), self )
    #layout1.addWidget( self.btnClear )
    
    spacer2 = qt.QSpacerItem(1,1,qt.QSizePolicy.Expanding,qt.QSizePolicy.Minimum)
    layout1.addItem(spacer2)
  
  def selectedDatabases( self ):
    result = []
    item = self.lvDatabases.firstChild()
    while item is not None:
      if item.isOn():
        result.append( neuroHierarchy.databases.database( unicode( item.text( 0 ) ) ) )
      item = item.nextSibling()
    return result


_ontologiesModificationDialog = None

def warnUserAboutDatabasesToUpdate():
  global _ontologiesModificationDialog
  
  if [i for i in neuroHierarchy.databases.iterDatabases() if getattr( i, '_mustBeUpdated', False )]:
    if _ontologiesModificationDialog is not None:
      # Detect if underlying C++ object has been destroyed (i.e. the window has been closed)
      try:
        _ontologiesModificationDialog.name()
      except RuntimeError:
        _ontologiesModificationDialog = None
    if _ontologiesModificationDialog is None:
      _ontologiesModificationDialog = ProcessView( getProcessInstance( 'updateDatabases' ) )
      _ontologiesModificationDialog.labName.setText( '<font color=red>' + _t_( 'Some ontologies (i.e. databases organization) have been modified but are used by currently selected databases. To take this modification into account, it is necessary to update the databases selected below. Please click on the "Update" button below.' ) +'</font>' )
      item = _ontologiesModificationDialog.inlineGUI.lvDatabases.firstChild()
      while item is not None:
        item.setOn( False )
        item = item.nextSibling()
    item = _ontologiesModificationDialog.inlineGUI.lvDatabases.firstChild()
    while item is not None:
      if getattr( neuroHierarchy.databases.database( unicode( item.text() ) ), '_mustBeUpdated', False ):
        item.setOn( True )
      item = item.nextSibling()
    _ontologiesModificationDialog.show()
    _ontologiesModificationDialog.raiseW()
