# -*- coding: iso-8859-1 -*-

#  This software and supporting documentation were developed by
#  NeuroSpin and IFR 49
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


from neuroProcesses import *
import qt
#from soma.functiontools import partial
import neuroConfig
if neuroConfig.newDatabases:
  from neuroHierarchy import databases

name = 'Update databases'
userLevel = 0


class UpdateDatabasesGUI( qt.QWidget ):
  def __init__( self, parent ):
    super( UpdateDatabasesGUI, self ).__init__( parent )
    layout = qt.QVBoxLayout( self, 11, 6 )
    self.lvDatabases = QListView( self )
    self.lvDatabases.addColumn( _t_( 'Database' ) )
    self.lvDatabases.header().hide()
    self.lvDatabases.setSorting( -1 )
    layout.addWidget( self.lvDatabases )
    
    lastItem = None
    selected = False
    if neuroConfig.newDatabases:
      for database in databases.iterDatabases():
        item = qt.QCheckListItem( self.lvDatabases, lastItem, database.name, qt.QCheckListItem.CheckBox )
        item.setOn( selected )
        selected = True
        lastItem = item
    else:
      for h in hierarchies():
        item = qt.QCheckListItem( self.lvDatabases, lastItem, h.fullPath(), qt.QCheckListItem.CheckBox )
        item.setOn( selected )
        selected = True
        lastItem = item

    layout1 = qt.QHBoxLayout(None,0,6)
    layout.addLayout( layout1 )
    spacer1 = qt.QSpacerItem(1,1,qt.QSizePolicy.Expanding,qt.QSizePolicy.Minimum)
    layout1.addItem(spacer1)

    self.btnClearAndUpdate = qt.QPushButton( _t_( '&Clear and Update' ), self )
    layout1.addWidget( self.btnClearAndUpdate )
    
    #self.btnClear = qt.QPushButton( _t_( '&Clear' ), self )
    #layout1.addWidget( self.btnClear )
    
    spacer2 = qt.QSpacerItem(1,1,qt.QSizePolicy.Expanding,qt.QSizePolicy.Minimum)
    layout1.addItem(spacer2)
  

if neuroConfig.newDatabases:
  def selectedDatabases( self, context ):
    result = []
    item = context.inlineGUI.lvDatabases.firstChild()
    while item is not None:
      if item.isOn():
        result.append( databases.database( unicode( item.text( 0 ) ) ) )
      item = item.nextSibling()
    return result
else:
  def selectedDatabases( self, context ):
    result = []
    item = context.inlineGUI.lvDatabases.firstChild()
    while item is not None:
      if item.isOn():
        directory = unicode( item.text( 0 ) )
        for h in hierarchies():
          if h.fullPath() == directory:
            result.append( h )
      item = item.nextSibling()
    return result


#def clearDatabases( self, context ):
  #databases = mainThreadActions().call( self.selectedDatabases, context )
  #for database in databases:
    #context.write( 'Clear database:', database.name )
    #if neuroConfig.newDatabases:
      #database.clear(context=context)
    #else:
      #databaseFile = os.path.join( database.fullPath(),
        #FileSystemOntology.get( database.get( 'ontology' ) ).cacheName )
      #if os.path.exists( databaseFile ):
        #try:
          #file = open( databaseFile, 'w' )
          #file.close()
        #except Exception, e:
          #context.warning( _t_( 'Cannot clear file %(file)s. %(error)' ) % \
                          #{ 'file': databaseFile, 'error': str( e ) } )
      
      #del database._childs[:]
      #database.lastModified = 0

def execution( self, context ):
  databases = mainThreadActions().call( self.selectedDatabases, context )
  for database in databases:
    context.write( '<b>Clear database:', database.name, '</b>' )
    if neuroConfig.newDatabases:
      database.clear(context=context)
    else:
      databaseFile = os.path.join( database.fullPath(),
        FileSystemOntology.get( database.get( 'ontology' ) ).cacheName )
      if os.path.exists( databaseFile ):
        try:
          file = open( databaseFile, 'w' )
          file.close()
        except Exception, e:
          context.warning( _t_( 'Cannot clear file %(file)s. %(error)' ) % \
                          { 'file': databaseFile, 'error': str( e ) } )
      del database._childs[:]
      database.lastModified = 0
    context.write( '<b>Update database:', database.name, '</b>' )
    if neuroConfig.newDatabases:
      database.update(context=context)
    else:
      cacheUpdate( [ database ] )


def inlineGUI( self, values, context, parent, externalRunButton=False ):
  result = UpdateDatabasesGUI( parent )
  result.btnClearAndUpdate.connect( result.btnClearAndUpdate, qt.SIGNAL( 'clicked()' ), 
                                    context._runButton )
  #result.runClearDatabases = partial( context._runButton, executionFunction=self.clearDatabases, )
  #result.btnClear.connect( result.btnClear, qt.SIGNAL( 'clicked()' ), result.runClearDatabases )
  return result

