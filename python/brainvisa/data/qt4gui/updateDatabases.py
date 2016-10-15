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


'''
@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
from __future__ import print_function
__docformat__ = "epytext en"

import sys
from brainvisa.processing.qtgui import backwardCompatibleQt as qt
from brainvisa.configuration import neuroConfig
from brainvisa.data import neuroHierarchy
import brainvisa.processes
from brainvisa.processing.qt4gui import neuroProcessesGUI

if sys.version_info[0] >= 3:
    xrange = range
    unicode = str


class UpdateDatabasesGUI( qt.QWidget ):
  def __init__( self, parent ):
    super( UpdateDatabasesGUI, self ).__init__( parent )
    layout = qt.QVBoxLayout( self)
    layout.setContentsMargins(11, 11, 11, 11)
    layout.setSpacing( 6 )
    self.setLayout(layout)
    self.lvDatabases = qt.QListWidget( )
    layout.addWidget( self.lvDatabases )
    
    lastItem = None
    for dbs in neuroConfig.dataPath:
      try:
        database=neuroHierarchy.databases.database(dbs.directory)
      except:
        print('PROBLEM: database', dbs.directory, 'is missing')
        continue
      selected=not dbs.builtin
      item = qt.QListWidgetItem( database.name, self.lvDatabases )
      if selected:
        item.setCheckState(qt.Qt.Checked)
      else:
        item.setCheckState(qt.Qt.Unchecked)

    layout1 = qt.QHBoxLayout()
    layout1.setContentsMargins(0, 0, 0, 0)
    layout1.setSpacing(6)
    layout.addLayout( layout1 )
    spacer1 = qt.QSpacerItem(1,1,qt.QSizePolicy.Expanding,qt.QSizePolicy.Minimum)
    layout1.addItem(spacer1)
    
    
    self.classic_chkbx = qt.QCheckBox( _t_( 'full update' ) )
    layout1.addWidget( self.classic_chkbx )
    self.classic_chkbx.setCheckable(True)
    self.classic_chkbx.setChecked( True )
    self.classic_chkbx.setToolTip( _t_(
      '<h4>Perform full update by parsing all data files in the database directories.</h4><p align="justify">This method is the safest, since it completely rebuilds the databases, but takes a long time for big databases. Anyway if other methods fail or leave "invisible" data, this method should be used. It should also be used when an ontology change has occurred (new types installed by new toolboxes, or new version of the ontologies), or in case of corrupted databases.</p>' ) )

    self.quick_hf_method_chkbx = qt.QCheckBox( _t_( 'incremental (history)') )
    layout1.addWidget( self.quick_hf_method_chkbx )
    self.quick_hf_method_chkbx.setCheckable(True)
    self.quick_hf_method_chkbx.setChecked( False )
    self.quick_hf_method_chkbx.setToolTip( _t_(
      '<h4>Perform incremental update by parsing history files newer than the last update.</h4><p align="justify">This method needs having activated the history feature in the selected databases (see in preferences, database settings, check the expert settings of databases). It parses the processing history in an incremental way, looking at history events since the last database update. However if some processing has been performed without the history feature activated, or completely outside of BrainVisa control, the corresponding files will not be indexed in the databases. If such situation occurs, then a full update will be needed.</p><p align="justify">In classical situations, this method should be the fastest, especially when processing additional data in large databases.</p>' ) )

    self.history_files_method_chkbx= qt.QCheckBox( _t_( 'full history') )
    layout1.addWidget( self.history_files_method_chkbx )
    self.history_files_method_chkbx.setCheckable(True)
    self.history_files_method_chkbx.setChecked( False )
    self.history_files_method_chkbx.setToolTip( _t_(
      '<h4>Perform incremental update by parsing all history files in the databases.</h4><p align="justify">This method is the same as the incremental one, except that it will parse all history files present in the database, regardless of date or already indexed data. It may be useful if the last database update date gets wrong for some reason. However for large databases, it may get even longer than the full update.</p>' ) )

    self.button_group = qt.QButtonGroup(self)
    self.button_group.addButton(self.history_files_method_chkbx)
    self.button_group.addButton(self.quick_hf_method_chkbx)
    self.button_group.addButton(self.classic_chkbx)

    self.btnClearAndUpdate = qt.QPushButton( _t_( '&Update' ) )
    layout1.addWidget( self.btnClearAndUpdate )

    #self.btnClear = qt.QPushButton( _t_( '&Clear' ), self )
    #layout1.addWidget( self.btnClear )
    
    spacer2 = qt.QSpacerItem(1,1,qt.QSizePolicy.Expanding,qt.QSizePolicy.Minimum)
    layout1.addItem(spacer2)
    
        
  def selectedDatabases( self ):
    result = []
    i=0
    while i<self.lvDatabases.count():
      item = self.lvDatabases.item(i)
      if item.checkState() == qt.Qt.Checked:
        result.append( neuroHierarchy.databases.database( unicode( item.text( ) ) ) )
      i+=1
    return result

  def classic_method( self ):
    return self.classic_chkbx.isChecked()

  def quick_hf_method( self ):
    return self.quick_hf_method_chkbx.isChecked()

  def history_files_method( self ):
    return self.history_files_method_chkbx.isChecked()

  
  
_ontologiesModificationDialog = None


def warnUserAboutDatabasesToUpdate():
  global _ontologiesModificationDialog
  
  if [i for i in neuroHierarchy.databases.iterDatabases() if getattr( i, '_mustBeUpdated', False )]:
    if _ontologiesModificationDialog is not None:
      # Detect if underlying C++ object has been destroyed (i.e. the window has been closed)
      try:
        _ontologiesModificationDialog.objectName()
      except RuntimeError:
        _ontologiesModificationDialog = None
    if _ontologiesModificationDialog is None or _ontologiesModificationDialog.info is None:
      _ontologiesModificationDialog = neuroProcessesGUI.ProcessView( brainvisa.processes.getProcessInstance( 'updateDatabases' ) )
      if _ontologiesModificationDialog is None:
        print('updateDatabases process cannot be found.')
        return
      _ontologiesModificationDialog.labName.setText( '<html><body><font color=red>' + _t_( 'Some ontologies (i.e. databases organization) have been modified but are used by currently selected databases. To take this modification into account, it is necessary to update the databases selected below. Please click on the "Update" button below.' ) +'</font></body></html>' )
      from soma.qt_gui.qt_backend import QtCore
      _ontologiesModificationDialog.setAttribute( QtCore.Qt.WA_DeleteOnClose )
      for i in xrange( _ontologiesModificationDialog.inlineGUI.lvDatabases.count() ):
        _ontologiesModificationDialog.inlineGUI.lvDatabases.item( i ).setCheckState(qt.Qt.Unchecked)
      #item = _ontologiesModificationDialog.inlineGUI.lvDatabases.firstChild()
      #while item is not None:
        #item.setOn( False )
        #item = item.nextSibling()
    #item = _ontologiesModificationDialog.inlineGUI.lvDatabases.firstChild()
    #while item is not None:
    for i in xrange( _ontologiesModificationDialog.inlineGUI.lvDatabases.count() ):
      item = _ontologiesModificationDialog.inlineGUI.lvDatabases.item( i )
      if getattr( neuroHierarchy.databases.database( unicode( item.text() ) ), '_mustBeUpdated', False ):
        item.setCheckState(qt.Qt.Checked)
      #item = item.nextSibling()
    _ontologiesModificationDialog.show()
    _ontologiesModificationDialog.raise_()
    def clean_close():
      global _ontologiesModificationDialog
      _ontologiesModificationDialog = None
    from soma.functiontools import partial
    _ontologiesModificationDialog.destroyed.connect(clean_close)
