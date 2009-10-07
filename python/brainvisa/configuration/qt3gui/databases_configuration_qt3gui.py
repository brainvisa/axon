# -*- coding: iso-8859-1 -*-

# Copyright IFR 49 (1995-2009)
#
#  This software and supporting documentation were developed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL-B license under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the 
# terms of the CeCILL-B license as circulated by CEA, CNRS
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
# knowledge of the CeCILL-B license and that you accept its terms.

'''
@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

import os
import backwardCompatibleQt as qt
from soma.translation import translate as _
from soma.qtgui.api import ApplicationQtGUI, QtGUI
from soma.wip.application.api import findIconFile
from soma.minf.api import writeMinf
from neuroException import showException
from brainvisa.configuration.databases_configuration import DatabaseSettings, DatabasesConfiguration

#------------------------------------------------------------------------------
class DatabaseManagerGUI( qt.QWidget ):
  def __init__( self, parent=None, name=None ):
    if getattr( DatabaseManagerGUI, 'pixUp', None ) is None:
      pixUp= findIconFile( 'up.png' )
      if pixUp:
        pixUp=qt.QPixmap( pixUp )
      setattr( DatabaseManagerGUI, 'pixUp', pixUp )
      pixDown=findIconFile( 'down.png' )
      if pixDown:
        pixDown=qt.QPixmap( pixDown )
      setattr( DatabaseManagerGUI, 'pixDown', pixDown )
    qt.QWidget.__init__( self, parent, name )
    layout = qt.QVBoxLayout( self )
    layout.setMargin( 10 )
    layout.setSpacing( 5 )

    self._databaseEditor = None
    
    self.lvDatabases = qt.QListView( self )
    self.lvDatabases.addColumn( _( 'Database' ) )
    self.lvDatabases.header().hide()
    self.lvDatabases.setSorting( -1 )
    self.connect( self.lvDatabases, qt.SIGNAL( 'selectionChanged( QListViewItem * )' ), self._selected )
    layout.addWidget( self.lvDatabases )
    self._lvDatabaseLastItem = None
    
    hb = qt.QHBoxLayout()
    hb.setSpacing( 6 )

    self.btnEdit = qt.QPushButton( _( 'Edit' ), self )
    self.connect( self.btnEdit, qt.SIGNAL( 'clicked()' ), self._edit )
    self.btnEdit.setEnabled( 0 )
    hb.addWidget( self.btnEdit )

    self.btnAdd = qt.QPushButton( _( 'Add' ), self )
    self.connect( self.btnAdd, qt.SIGNAL( 'clicked()' ), self._add )
    hb.addWidget( self.btnAdd )

    self.btnRemove = qt.QPushButton( _( 'Remove' ), self )
    self.btnRemove.setEnabled( 0 )
    self.connect( self.btnRemove, qt.SIGNAL( 'clicked()' ), self._remove )
    hb.addWidget( self.btnRemove )

    self.btnUp = qt.QPushButton( self )
    self.btnUp.setPixmap( self.pixUp )
    self.btnUp.setEnabled( 0 )
    self.connect( self.btnUp, qt.SIGNAL( 'clicked()' ), self._up )
    hb.addWidget( self.btnUp )

    self.btnDown = qt.QPushButton( self )
    self.btnDown.setPixmap( self.pixDown )
    self.btnDown.setEnabled( 0 )
    self.connect( self.btnDown, qt.SIGNAL( 'clicked()' ), self._down )
    hb.addWidget( self.btnDown )

    layout.addLayout( hb )

    hb = qt.QHBoxLayout()
    hb.setSpacing( 6 )

    spacer = qt.QSpacerItem( 10, 10, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum )
    hb.addItem( spacer )

    layout.addLayout( hb )
    self.modification = 0
    self.setCaption( 'Select databases directories' )
    
    
  def getConfiguredDatabases( self ):
    item = self.lvDatabases.firstChild()
    while item is not None:
      directory, selected = item._value
      yield ( directory, item.isOn() )
      item = item.nextSibling()

 
  def update( self, databases ):
    self.lvDatabases.clear()
    self._lvDatabaseLastItem = None
    for d in databases:
      self._addDatabase( d.directory, d.selected )
  
  
  def _getDatabaseEditor( self ):
    if self._databaseEditor is None:
      self._databaseEditor = self.DatabaseEditor( parent=self )
    return self._databaseEditor
  
  
  def _edit( self ):
    try:
      settings = DatabaseSettings( *self.lvDatabases.currentItem()._value )
      appgui = ApplicationQtGUI()
      if appgui.edit( settings, live=True, parent=self ):
        if settings.directory:
          item = self.lvDatabases.currentItem()
          item._value = ( settings.directory, settings._selected )
          item.setText( 0, settings.directory )
          if not settings._selected: item.setOn( 0 )
          self.modification = 1
          try:
            writeMinf( os.path.join( settings.directory, 'database_settings.minf' ),
                      ( settings.expert_settings, ) )
          except IOError:
            pass
    except:
      showException()


  def _add( self ):
    try:
      settings = DatabaseSettings()
      settings.expert_settings.ontology = 'brainvisa-3.1.0'
      appgui = ApplicationQtGUI()
      if appgui.edit( settings, live=True, parent=self ):
        if settings.directory:
          self._addDatabase( settings.directory, settings._selected )
          self.modification = True
          try:
            writeMinf( os.path.join( settings.directory, 'database_settings.minf' ),
                      ( settings.expert_settings, ) )
          except IOError:
            pass
    except:
      showException()


  def _remove( self ):
    item = self.lvDatabases.currentItem()
    self.lvDatabases.takeItem( item )
    self._selected( self.lvDatabases.currentItem() )
    self.modification = 1

  def _up( self ):
    item = self.lvDatabases.currentItem()
    other = item.itemAbove().itemAbove()
    self._moveDatabase( item, other )
    
  def _moveDatabase( self, item, other ):
    self.lvDatabases.takeItem( item )
    items = []
    if other is None: items.append( item )
    current =  self.lvDatabases.firstChild()
    while current is not None:
      items.insert( 0, current )
      if current is other:
        items.insert( 0, item )
      self.lvDatabases.takeItem( current )
      current =  self.lvDatabases.firstChild()
    for current in items:
      self.lvDatabases.insertItem( current )
    self.lvDatabases.setCurrentItem( item )
    self.modification = 1

  def _down( self ):
    item = self.lvDatabases.currentItem()
    other = item.itemBelow()
    self._moveDatabase( item, other )

  def _selected( self, item ):
    if item is None:
      self.btnEdit.setEnabled( 0 )
      self.btnRemove.setEnabled( 0 )
      self.btnUp.setEnabled( 0 )
      self.btnDown.setEnabled( 0 )
    else:
      self.btnEdit.setEnabled( 1 )
      self.btnRemove.setEnabled( 1 )
      if item.itemAbove() is not None:
        self.btnUp.setEnabled( 1 )
      else:
        self.btnUp.setEnabled( 0 )
      if item.itemBelow() is not None:
        self.btnDown.setEnabled( 1 )
      else:
        self.btnDown.setEnabled( 0 )

  def _addDatabase( self, directory, selected ):
    item = qt.QCheckListItem( self.lvDatabases, self._lvDatabaseLastItem, directory, qt.QCheckListItem.CheckBox )
    item.setOn( selected )
    item._value = ( directory, selected )
    self._lvDatabaseLastItem = item

#------------------------------------------------------------------------------
class DatabasesConfiguration_Qt3GUI( QtGUI ):
  def editionWidget( self, object, parent=None, name=None, live=False ):
    editionWidget = DatabaseManagerGUI( parent=parent, name=name )
    editionWidget.update( object.fso )
    return editionWidget
  
  
  def closeEditionWidget( self, editionWidget ):
    editionWidget.close()
  
  
  def setObject( self, editionWidget, object ):
    fso = []
    for directory, selected in editionWidget.getConfiguredDatabases():
      fso.append( DatabasesConfiguration.FileSystemOntology( directory=directory, selected=selected ) )
    object.fso = fso
  

  def updateEditionWidget( self, editionWidget, object ):
    '''
    Update C{editionWidget} to reflect the current state of C{object}.
    This method must be defined for both mutable and immutable DataType.
    '''
    editionWidget.update( object.fso )
