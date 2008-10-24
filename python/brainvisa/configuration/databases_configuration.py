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


import os, qt, time
from soma.wip.configuration import ConfigurationGroup
from soma.signature.api import HasSignature, Signature, Unicode, FileName, \
                               Boolean, Choice, Sequence
from soma.translation import translate as _
from soma.qt3gui.api import ApplicationQt3GUI, Qt3GUI, QFileDialogWithSignals
from soma.wip.application.api import findIconFile
from soma.minf.api import readMinf, writeMinf
from brainvisa.data import temporary
from neuroException import showException
import neuroConfig


#------------------------------------------------------------------------------
class DatabasesConfiguration( ConfigurationGroup ):
  label = 'Databases'
  icon = 'database_read.png'
  
  class FileSystemOntology( HasSignature ):
    signature = Signature(
      'directory', FileName, dict( defaultValue='' ),
      'selected', Boolean, dict( defaultValue=True ),
    )
  
    def __init__( self, directory='', selected=True ):
      super( DatabasesConfiguration.FileSystemOntology, self ).__init__()
      self.directory = directory
      self.selected = bool( selected )

  
  signature = Signature(
    'fso', Sequence( FileSystemOntology ), dict( defaultValue=[] ),
  )


#------------------------------------------------------------------------------
class ExpertDatabaseSettings( HasSignature ):
  signature = Signature(
    'ontology', Choice( 'brainvisa-3.1.0', 'brainvisa-3.0', 'shared' ), dict( defaultValue='brainvisa-3.0' ),
    'sqliteFileName', FileName, dict( defaultValue='' ),
    'activate_history', Boolean, dict( defaultValue=False ),
  )


#------------------------------------------------------------------------------
class DatabaseSettings( HasSignature ):
  signature = Signature(
    'directory', FileName( readOnly=True, directoryOnly=True ), dict( defaultValue='' ),
    'expert_settings', ExpertDatabaseSettings, dict( defaultValue=ExpertDatabaseSettings(), collapsed=True ),
  )

  def __init__( self, directory=None, selected=True ):
    HasSignature.__init__( self )
    if directory :
      if os.path.exists( directory ) :
        self.directory = directory
        self._selected = selected
      else :
        self._selected = False
    else :
      self._selected = selected

    self.onAttributeChange( 'directory', self._directoryChanged )
    self._directoryChanged( directory )


  def _directoryChanged( self, newDirectory ):
    if newDirectory:
      minf = os.path.join( newDirectory, 'database_settings.minf' )
      if os.path.exists( minf ):
        readMinf( minf, targets=( self.expert_settings, ) )
      else:
        it = self.expert_settings.signature.iteritems()
        it.next()
        for n, v in it:
          if n == 'ontology':
            self.expert_settings.ontology = 'brainvisa-3.1.0'
          else:
            setattr( self.expert_settings, n, v.defaultValue )


#------------------------------------------------------------------------------
class DatabaseManagerGUI( qt.QWidget ):
  def __init__( self, parent=None, name=None ):
    if getattr( DatabaseManagerGUI, 'pixUp', None ) is None:
      setattr( DatabaseManagerGUI, 'pixUp', 
        qt.QPixmap( findIconFile( 'up.png' ) ) )
      setattr( DatabaseManagerGUI, 'pixDown', 
        qt.QPixmap( findIconFile( 'down.png' ) ) )
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
      appgui = ApplicationQt3GUI()
      if appgui.edit( settings, live=True, parent=self ):
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
      appgui = ApplicationQt3GUI()
      if appgui.edit( settings, live=True, parent=self ):
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
class DatabasesConfiguration_Qt3GUI( Qt3GUI ):
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
