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
@author: Dominique Geffroy
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
from __future__ import absolute_import
from six.moves import range
__docformat__ = "epytext en"

import os
import brainvisa.processing.qtgui.backwardCompatibleQt as qt
Qt = qt
from soma.translation import translate as _
from soma.qtgui.api import ApplicationQtGUI, QtGUI
from soma.wip.application.api import findIconFile
from soma.minf.api import writeMinf
from brainvisa.processing.neuroException import showException
from brainvisa.configuration.databases_configuration import DatabaseSettings, DatabasesConfiguration, FormatsSequence

#------------------------------------------------------------------------------


class DatabaseManagerGUI(qt.QWidget):

    def __init__(self, parent=None, name=None):
        if getattr(DatabaseManagerGUI, 'pixUp', None) is None:
            pixUp = findIconFile('up.png')
            if pixUp:
                pixUp = qt.QIcon(pixUp)
            setattr(DatabaseManagerGUI, 'pixUp', pixUp)
            pixDown = findIconFile('down.png')
            if pixDown:
                pixDown = qt.QIcon(pixDown)
            setattr(DatabaseManagerGUI, 'pixDown', pixDown)
            pixLock = findIconFile('lock.png')
            if pixLock:
                pixLock = qt.QIcon(pixLock)
            setattr(DatabaseManagerGUI, 'pixLock', pixLock)
        qt.QWidget.__init__(self, parent)
        if name:
            self.setObjectName(name)
        layout = qt.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        self.setLayout(layout)

        self._databaseEditor = None

        self.lvDatabases = qt.QListWidget(self)
        self.lvDatabases.itemSelectionChanged.connect(self._selected)
        layout.addWidget(self.lvDatabases)

        hb = qt.QHBoxLayout()
        hb.setSpacing(6)

        self.btnEdit = qt.QPushButton(_('Edit'), self)
        self.btnEdit.clicked.connect(self._edit)
        self.btnEdit.setEnabled(0)
        hb.addWidget(self.btnEdit)

        self.btnAdd = qt.QPushButton(_('Add'), self)
        self.btnAdd.clicked.connect(self._add)
        hb.addWidget(self.btnAdd)

        self.btnRemove = qt.QPushButton(_('Remove'), self)
        self.btnRemove.setEnabled(0)
        self.btnRemove.clicked.connect(self._remove)
        hb.addWidget(self.btnRemove)

        self.btnUp = qt.QPushButton(self)
        if self.pixUp:
            self.btnUp.setIcon(self.pixUp)
        self.btnUp.setEnabled(0)
        self.btnUp.clicked.connect(self._up)
        hb.addWidget(self.btnUp)

        self.btnDown = qt.QPushButton(self)
        if self.pixDown:
            self.btnDown.setIcon(self.pixDown)
        self.btnDown.setEnabled(0)
        self.btnDown.clicked.connect(self._down)
        hb.addWidget(self.btnDown)

        layout.addLayout(hb)

        hb = qt.QHBoxLayout()
        hb.setSpacing(6)

        spacer = qt.QSpacerItem(
            10, 10, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
        hb.addItem(spacer)

        layout.addLayout(hb)
        self.modification = 0
        self.setWindowTitle('Select databases directories')

    def getConfiguredDatabases(self):
        for i in range(self.lvDatabases.count()):
            item = self.lvDatabases.item(i)
            directory, selected, read_only, settings = item._value
            yield (directory, (item.checkState() == qt.Qt.Checked), read_only)

    def update(self, databases):
        from brainvisa.configuration import neuroConfig
        self.lvDatabases.clear()
        for d in databases:
            self._addDatabase(d.directory, d.selected, d.read_only,
                              neuroConfig.get_database_settings(d.directory))

    def _getDatabaseEditor(self):
        if self._databaseEditor is None:
            self._databaseEditor = self.DatabaseEditor(parent=self)
        return self._databaseEditor

    def _edit(self):
        try:
            from brainvisa.configuration import neuroConfig
            item = self.lvDatabases.currentItem()
            directory, selected, read_only, settings = item._value
            if settings is None:
                settings = neuroConfig.get_database_settings(
                    directory, selected, read_only)
            appgui = ApplicationQtGUI()
            if appgui.edit(settings, live=True, parent=self):
                if settings.directory:
                    #item = self.lvDatabases.currentItem()
                    item._value = (settings.directory, settings._selected,
                                   settings.read_only, settings)
                    item.setText(settings.directory)
                    if settings.read_only:
                        item.setIcon(self.pixLock)
                    else:
                        item.setIcon(qt.QIcon())
                    if not settings._selected:
                        item.setCheckState(qt.Qt.Unchecked)
                    self.modification = 1
                    try:
                        writeMinf(
                            os.path.join(
                                settings.directory, 'database_settings.minf'),
                                  (settings.expert_settings, ))
                    except IOError:
                        pass
        except Exception:
            showException()

    def _add(self):
        try:
            settings = DatabaseSettings()
            settings.expert_settings.ontology = 'brainvisa-3.2.0'
            appgui = ApplicationQtGUI()
            if appgui.edit(settings, live=True, parent=self):
                if settings.directory:
                    self._addDatabase(settings.directory, settings._selected,
                                      settings.read_only, settings)
                    self.modification = True
                    try:
                        writeMinf(
                            os.path.join(
                                settings.directory, 'database_settings.minf'),
                                  (settings.expert_settings, ))
                    except IOError:
                        pass
        except Exception:
            showException()

    def _remove(self):
        row = self.lvDatabases.currentRow()
        self.lvDatabases.takeItem(row)
        self._selected()
        self.modification = 1

    def _up(self):
        row = self.lvDatabases.currentRow()
        newRow = row - 1
        if newRow >= 0:
            self._moveDatabase(row, newRow)

    def _moveDatabase(self, row, otherRow):
        item = self.lvDatabases.takeItem(row)
        self.lvDatabases.insertItem(otherRow, item)
        self.lvDatabases.setCurrentItem(item)
        self.modification = 1

    def _down(self):
        row = self.lvDatabases.currentRow()
        newRow = row + 1
        if newRow < self.lvDatabases.count():
            self._moveDatabase(row, newRow)

    def _selected(self):
        item = self.lvDatabases.currentItem()
        row = self.lvDatabases.currentRow()
        if item is None:
            self.btnEdit.setEnabled(0)
            self.btnRemove.setEnabled(0)
            self.btnUp.setEnabled(0)
            self.btnDown.setEnabled(0)
        else:
            self.btnEdit.setEnabled(1)
            self.btnRemove.setEnabled(1)
            if row != 0:
                self.btnUp.setEnabled(1)
            else:
                self.btnUp.setEnabled(0)
            if (row < (self.lvDatabases.count() - 1)):
                self.btnDown.setEnabled(1)
            else:
                self.btnDown.setEnabled(0)

    def _addDatabase(self, directory, selected, read_only=False,
                     settings=None):
        item = qt.QListWidgetItem(self.lvDatabases)
        if os.path.isdir(directory) and not os.access(directory,
                                                      os.R_OK + os.W_OK + os.X_OK):
            read_only = True
        if read_only:
            from brainvisa.configuration import neuroConfig
            item.setIcon(
                qt.QIcon(os.path.join(neuroConfig.iconPath, 'lock.png')))
        item.setText(directory)
        if selected:
            item.setCheckState(qt.Qt.Checked)
        else:
            item.setCheckState(qt.Qt.Unchecked)
        item._value = (directory, selected, read_only, settings)

#------------------------------------------------------------------------------


class DatabasesConfiguration_Qt4GUI(QtGUI):

    def editionWidget(self, object, parent=None, name=None, live=False):
        editionWidget = DatabaseManagerGUI(parent=parent, name=name)
        editionWidget.update(object.fso)
        return editionWidget

    def closeEditionWidget(self, editionWidget):
        editionWidget.close()

    def setObject(self, editionWidget, object):
        fso = []
        for directory, selected, read_only \
                in editionWidget.getConfiguredDatabases():
            fso.append(DatabasesConfiguration.FileSystemOntology(
                       directory=directory, selected=selected, read_only=read_only))
        object.fso = fso

    def updateEditionWidget(self, editionWidget, object):
        '''
        Update C{editionWidget} to reflect the current state of C{object}.
        This method must be defined for both mutable and immutable DataType.
        '''
        editionWidget.update(object.fso)


class FormatsSequence_Qt4GUI(QtGUI):

    def editionWidget(self, object, parent=None, name=None, live=False):
        editionWidget = Qt.QWidget()
        l = Qt.QVBoxLayout()
        editionWidget.setLayout(l)
        edit = Qt.QListWidget()
        l.addWidget(edit)
        self.edit = edit
        self.edit.itemSelectionChanged.connect(self._selected)

        hb = Qt.QHBoxLayout()
        hb.setSpacing(6)

        #self.btnAdd = Qt.QPushButton(_('Add'), editionWidget)
        #self.btnAdd.clicked.connect(self._add)
        #hb.addWidget(self.btnAdd)

        #self.btnRemove = Qt.QPushButton(_('Remove'), editionWidget)
        #self.btnRemove.setEnabled(0)
        #self.btnRemove.clicked.connect(self._remove)
        #hb.addWidget(self.btnRemove)

        self.btnUp = Qt.QPushButton(editionWidget)
        if DatabaseManagerGUI.pixUp:
            self.btnUp.setIcon(DatabaseManagerGUI.pixUp)
        self.btnUp.setEnabled(0)
        self.btnUp.clicked.connect(self._up)
        hb.addWidget(self.btnUp)

        self.btnDown = Qt.QPushButton(editionWidget)
        if DatabaseManagerGUI.pixDown:
            self.btnDown.setIcon(DatabaseManagerGUI.pixDown)
        self.btnDown.setEnabled(0)
        self.btnDown.clicked.connect(self._down)
        hb.addWidget(self.btnDown)

        l.addLayout(hb)

        #hb = Qt.QHBoxLayout()
        #hb.setSpacing(6)

        #spacer = qt.QSpacerItem(
            #10, 10, Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Minimum)
        #hb.addItem(spacer)

        self.modification = 0

        self.updateEditionWidget(editionWidget, object)
        return editionWidget

    def closeEditionWidget(self, editionWidget):
        editionWidget.close()

    def setObject(self, editionWidget, object):
        # clear list without reinstantiating it
        while object:
            object.pop()
        for i in range(self.edit.count()):
            item = self.edit.item(i)
            object.append(item.text())
        object += [f for f in FormatsSequence.all_formats() if f not in object]

    def updateEditionWidget(self, editionWidget, object):
        self.edit.clear()
        for item in object:
            self.edit.addItem(item)

    def _add(self):
        try:
            pass
        except Exception:
            showException()

    def _remove(self):
        row = self.edit.currentRow()
        self.edit.takeItem(row)
        self._selected()
        self.modification = 1

    def _up(self):
        row = self.edit.currentRow()
        newRow = row - 1
        if newRow >= 0:
            self._moveItem(row, newRow)

    def _moveItem(self, row, otherRow):
        item = self.edit.takeItem(row)
        self.edit.insertItem(otherRow, item)
        self.edit.setCurrentItem(item)
        self.modification = 1

    def _down(self):
        row = self.edit.currentRow()
        newRow = row + 1
        if newRow < self.edit.count():
            self._moveItem(row, newRow)

    def _selected(self):
        item = self.edit.currentItem()
        row = self.edit.currentRow()
        if item is None:
            #self.btnRemove.setEnabled(0)
            self.btnUp.setEnabled(0)
            self.btnDown.setEnabled(0)
        else:
            #self.btnRemove.setEnabled(1)
            if row != 0:
                self.btnUp.setEnabled(1)
            else:
                self.btnUp.setEnabled(0)
            if (row < (self.edit.count() - 1)):
                self.btnDown.setEnabled(1)
            else:
                self.btnDown.setEnabled(0)
