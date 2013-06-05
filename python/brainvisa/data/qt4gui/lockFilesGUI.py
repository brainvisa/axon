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

from PyQt4.QtGui import *
from PyQt4.QtCore import *
import neuroConfig
import os

class LockedFilesListEditor( QDialog ):

  def __init__( self, parent, files, setLock ):
    QWidget.__init__( self, parent )

    LockedFilesListEditor.pixProcessFinished \
      = QIcon( os.path.join( neuroConfig.iconPath, 'ok.png' ) )
    self._files = files

    if setLock:
      message = _t_( 'The following files will be locked:' ) + '\n\n' \
        + '\n'.join( [ f.fullPath() for f in files ] )
    else:
      message = _t_( 'The following files will be unlocked:' ) + '\n\n' \
        + '\n'.join( [ f.fullPath() for f in files ] )
    self.setModal( True )
    self.setObjectName( 'locked_files_list_edition' )
    vlay = QVBoxLayout( self )
    if setLock:
      self.setWindowTitle( _t_( 'Locking files' ) )
      vlay.addWidget( QLabel(
        '<html>The following files will be <b>locked</b>:</html>', self ) )
    else:
      self.setWindowTitle( _t_( 'Unlocking files' ) )
      vlay.addWidget( QLabel(
        '<html>The following files will be <b>unlocked</b>:</html>', self ) )
    tablew = QTableWidget( self )
    self._tablew = tablew
    vlay.addWidget( tablew )
    hbox = QWidget( self )
    vlay.addWidget( hbox )
    hlay = QHBoxLayout( hbox )
    ok = QPushButton( _t_( 'OK' ), hbox )
    hlay.addWidget( ok )
    ok.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    cc = QPushButton( _t_( 'Cancel' ), hbox )
    hlay.addWidget( cc )
    cc.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    add = QPushButton( _t_( 'Add to sel.' ), hbox )
    hlay.addWidget( add )
    add.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    rmv = QPushButton( _t_( 'Remove' ), hbox )
    hlay.addWidget( rmv )
    rmv.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    ok.clicked.connect( self.accept )
    cc.clicked.connect( self.reject )
    add.clicked.connect( self._addToLockSelection )
    rmv.clicked.connect( self._removeFromLockSelection )
    tablew.setColumnCount( 3 )
    tablew.setHorizontalHeaderItem(
      0, QTableWidgetItem( _t_( 'Sel.' ) ) )
    tablew.setHorizontalHeaderItem(
      1, QTableWidgetItem( _t_( 'short name' ) ) )
    tablew.horizontalHeader().setStretchLastSection( False )
    tablew.setHorizontalHeaderItem( 1, QTableWidgetItem( _t_( 'full name' ) ) )
    tablew.horizontalHeader().setResizeMode( 0, QHeaderView.ResizeToContents )
    tablew.horizontalHeader().setResizeMode( 1, QHeaderView.ResizeToContents )
    tablew.horizontalHeader().setResizeMode( 2, QHeaderView.ResizeToContents )
    tablew.setRowCount( len( files ) )
    tablew.setSortingEnabled( True )
    tablew.setSelectionMode( QTableWidget.ExtendedSelection )
    tablew.setSelectionBehavior( QTableWidget.SelectRows )
    for i, di in enumerate( files ):
      f = di.fullPath()
      item = QTableWidgetItem()
      item.setData( Qt.DecorationRole, self.pixProcessFinished )
      item.setData( Qt.DisplayRole, None )
      item.setData( Qt.UserRole, '1' )
      tablew.setItem( i, 0, item )
      item = QTableWidgetItem( os.path.basename( f ) )
      item.setData( Qt.UserRole, str(i) )
      tablew.setItem( i, 1, item )
      tablew.setItem( i, 2, QTableWidgetItem( f ) )
    self.resize( 800, 400 )


  def _addToLockSelection( self ):
    tablew = self._tablew
    for i in xrange( tablew.rowCount() ):
      item = tablew.item( i, 0 )
      if item and item.isSelected() and item.data( Qt.UserRole ) != '1':
        item = QTableWidgetItem()
        item.setData( Qt.DecorationRole, self.pixProcessFinished )
        item.setData( Qt.UserRole, '1' )
        tablew.setItem( i, 0, item )


  def _removeFromLockSelection( self ):
    tablew = self._tablew
    for i in xrange( tablew.rowCount() ):
      item = tablew.item( i, 0 )
      if item and item.isSelected() and item.data( Qt.UserRole ) == '1':
        item.setData( Qt.DecorationRole, None )
        item.setData( Qt.UserRole, '0' )


  def selectedDiskItems( self ):
    tablew = self._tablew
    selectedfiles = []
    for i in xrange( tablew.rowCount() ):
      item = tablew.item( i, 0 )
      if item and item.data( Qt.UserRole ) == '1':
        num = int( tablew.item( i, 1 ).data( Qt.UserRole ) )
        selectedfiles.append( self._files[num] )
    return selectedfiles



