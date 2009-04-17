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

import backwardCompatibleQt as qt
import neuroConfig
if neuroConfig.newDatabases:
  from neuroHierarchy import databases


class UpdateDatabasesGUI( qt.QWidget ):
  def __init__( self, parent ):
    super( UpdateDatabasesGUI, self ).__init__( parent )
    layout = qt.QVBoxLayout( self)
    layout.setMargin( 11 )
    layout.setSpacing( 6 )
    self.setLayout(layout)
    self.lvDatabases = qt.QListWidget( )
    layout.addWidget( self.lvDatabases )
    
    lastItem = None
    selected = False
    if neuroConfig.newDatabases:
      for database in databases.iterDatabases():
        item = qt.QListWidgetItem( database.name, self.lvDatabases )
        if selected:
          item.setCheckState(qt.Qt.Checked)
        else:
          item.setCheckState(qt.Qt.Unchecked)
        selected = True
    else:
      for h in hierarchies():
        item = qt.QCheckListItem( h.fullPath(), self.lvDatabases )
        if selected:
          item.setCheckState(qt.Qt.Checked)
        else:
          item.setCheckState(qt.Qt.Unchecked)
        selected = True

    layout1 = qt.QHBoxLayout()
    layout1.setMargin(0)
    layout1.setSpacing(6)
    layout.addLayout( layout1 )
    spacer1 = qt.QSpacerItem(1,1,qt.QSizePolicy.Expanding,qt.QSizePolicy.Minimum)
    layout1.addItem(spacer1)

    self.btnClearAndUpdate = qt.QPushButton( _t_( '&Update' ) )
    layout1.addWidget( self.btnClearAndUpdate )
    
    #self.btnClear = qt.QPushButton( _t_( '&Clear' ), self )
    #layout1.addWidget( self.btnClear )
    
    spacer2 = qt.QSpacerItem(1,1,qt.QSizePolicy.Expanding,qt.QSizePolicy.Minimum)
    layout1.addItem(spacer2)
  
  def selectedDatabases( self ):
    if neuroConfig.newDatabases:
      result = []
      i=0
      while i<self.lvDatabases.count():
        item = self.lvDatabases.item(i)
        if item.checkState() == qt.Qt.Checked:
          result.append( databases.database( unicode( item.text( ) ) ) )
        i+=1
      return result
    else:
      result = []
      i=0
      while i<self.lvDatabases.count():
        item = self.lvDatabases.item(i)
        if item.checkState() == qt.Qt.Checked:
          directory = unicode( item.text( ) )
          for h in hierarchies():
            if h.fullPath() == directory:
              result.append( h )
        i+=1
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
