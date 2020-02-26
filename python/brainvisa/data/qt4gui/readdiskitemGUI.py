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
from __future__ import print_function

from __future__ import absolute_import
from brainvisa.processing.qtgui.backwardCompatibleQt \
    import QAction, QLineEdit, QPushButton, QToolButton, QComboBox, \
           Qt, QIcon, QWidget, QWidgetAction, QFileDialog, QVBoxLayout, \
           QListWidget, QHBoxLayout, QSpacerItem, QSizePolicy, QSize, QMenu, \
           QPalette, QColor, QItemSelectionModel, QLabel, \
           QListView, QTreeView, QAbstractItemView, QPixmap
from soma.wip.application.api import findIconFile
from soma.qtgui.api import largeIconSize
from soma.path import remove_query_string, parse_query_string, \
                      update_query_string, QueryStringParamUpdateMode
from brainvisa.data.qtgui.diskItemBrowser import DiskItemBrowser
from brainvisa.data.qtgui.neuroDataGUI import DataEditor, StringListEditor, buttonMargin, buttonIconSize
import brainvisa.processes
from brainvisa.processes import getProcessInstance
from brainvisa.processing.qt4gui import neuroProcessesGUI
from brainvisa.data.neuroDiskItems import DiskItem, Directory, aimsFileInfo, \
                                          getResolutionsFromItems
from brainvisa.data.qt4gui import history as historygui
from brainvisa.configuration import neuroConfig
from brainvisa.processing.neuroException import showException, HTMLMessage
from soma.qt_gui.qt_backend import QtCore, QtGui
import sys
import os
import six
import weakref
from six.moves import map

class ComboBoxAction(QWidgetAction):
    
    def __init__(self, parent, text = None, icon_file = None):
        super(ComboBoxAction, self).__init__(parent)
        
        widget = QWidget(parent)
        layout = QHBoxLayout()
        widget.setLayout(layout)
        self._icon = QLabel(widget)
        self._text = QLabel(widget)
        self._combo = QComboBox(widget)
        layout.addWidget(self._icon)
        layout.addWidget(self._text)
        layout.addWidget(self._combo)
                
        if (icon_file):
            self.setIconFile(icon_file)
        else:
            self._icon.setVisible(False)

        if (text):
            self.setText(text)
        else:
            self._text.setVisible(False)
        
        self._combo.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding,
                                              QSizePolicy.Fixed))
        self._combo.activated.connect(self.triggered)
        self.setDefaultWidget(widget)
        
    def triggered(self, value):
        self.parentWidget().setVisible(False)
        
    def setIconFile(self, icon_file):
        if icon_file:
            self._icon.setPixmap(QPixmap(findIconFile(icon_file)))
            self._icon.setSizePolicy(QSizePolicy(QSizePolicy.Fixed,
                                                 QSizePolicy.Fixed))
            self._icon.setVisible(True)
            
        else:
            self.setVisible(False)
       
    def setText(self, text):
        if text:
            self._text.setText(text)
            self._text.setVisible(True)   
            
        else:
            self.setVisible(False)
      
    def text(self):
        return self._text.text()
    
    def comboBoxWidget(self):
        return self._combo
    
    def setVisible(self, visible):
        super(ComboBoxAction, self).setVisible(visible)
        self.defaultWidget().setVisible(visible)
        
def addComboBoxMenu(parent, menu, title, icon_file, cmb, act, update_func):

    # Create ComboBoxAction widget
    a = ComboBoxAction(menu, title, icon_file)
    c = a.comboBoxWidget()
    
    setattr(parent, act, a)
    setattr(parent, cmb, c)
    
    # Update menu with the new action
    menu.addAction(a)
    menu.aboutToShow.connect(update_func)

#----------------------------------------------------------------------------
class RightClickablePushButton(QPushButton):

    rightPressed = QtCore.Signal(QtCore.QPoint)

    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            self.rightPressed.emit(self.mapToGlobal(e.pos()))
        else:
            QPushButton.mousePressEvent(self, e)

#----------------------------------------------------------------------------


class DiskItemEditor(QWidget, DataEditor):

    noDefault = QtCore.Signal(six.text_type)
    newValidValue = QtCore.Signal(six.text_type, object)

    def __init__(self, parameter, parent, name, write=False, context=None,
                 process=None):
        if getattr(DiskItemEditor, 'pixShow', None) is None:
            setattr(DiskItemEditor, 'pixShow',
                    QIcon(findIconFile('eye.png')))
            setattr(DiskItemEditor, 'pixEdit',
                    QIcon(findIconFile('pencil.png')))
            setattr(DiskItemEditor, 'pixDatabaseRead',
                    QIcon(findIconFile('database_read.png')))
            setattr(DiskItemEditor, 'pixDatabaseWrite',
                    QIcon(findIconFile('database_write.png')))
            setattr(DiskItemEditor, 'pixBrowseRead',
                    QIcon(findIconFile('browse_read.png')))
            setattr(DiskItemEditor, 'pixBrowseWrite',
                    QIcon(findIconFile('browse_write.png')))
            setattr(DiskItemEditor, 'pixHistory',
                    QIcon(findIconFile('history.png')))
        QWidget.__init__(self, parent)
        DataEditor.__init__(self)
        if name:
            self.setObjectName(name)
        hLayout = QHBoxLayout()
        self.setLayout(hLayout)
        if sys.platform == 'darwin' and QtCore.qVersion() == '4.6.2':
            # is this layout problem a bug in qt/Mac 4.6.2 ?
            hLayout.setSpacing(14)
        else:
            hLayout.setSpacing(2)
        hLayout.setContentsMargins(0, 0, 0, 0)
        self._write = write
        self.parameter = parameter
        self.led = QLineEdit()
        hLayout.addWidget(self.led)
        self.led.textChanged.connect(self.textChanged)
        self.led.returnPressed.connect(self.checkValue)
        self.setFocusProxy(self.led)
        self.diskItem = None
        self.forceDefault = False
        self._context = context
        if process is None:
            self.process = None
        else:
            if isinstance(process, weakref.ProxyType):
                self.process = process
            else:
                self.process = weakref.proxy(process)

        self.btnShow = RightClickablePushButton()
        hLayout.addWidget(self.btnShow)
        self.btnShow.setCheckable(True)
        self.btnShow.setIcon(self.pixShow)
        self.btnShow.setIconSize(buttonIconSize)
        self.btnShow.setFixedSize(buttonIconSize + buttonMargin)
        self.btnShow.setFocusPolicy(Qt.NoFocus)
        self.btnShow.setEnabled(False)

        # Sets default viewers list
        self._viewers = None
        self.actViewers = None
        self.cmbViewersSeparator = None
        self.cmbViewers = None
        self.newValidValue.connect(self.updateViewers)

        # Sets default data editors list
        self._editors = None
        self.actDataEditors = None
        self.cmbDataEditorsSeparator = None
        self.cmbDataEditors = None
        self.newValidValue.connect(self.updateDataEditors)

        # Sets default resolutions list
        self.actResolutions = None
        self.cmbResolutionsSeparator = None
        self.cmbResolutions = None
    
        self._view = None
        self.btnShow.clicked.connect(self.showPressed)
        self.btnShow.rightPressed.connect(self.openViewerPressed)
        self._edit = None
        self.btnEdit = RightClickablePushButton()
        hLayout.addWidget(self.btnEdit)
        self.btnEdit.setCheckable(True)
        self.btnEdit.setIcon(self.pixEdit)
        self.btnEdit.setIconSize(buttonIconSize)
        self.btnEdit.setFixedSize(buttonIconSize + buttonMargin)
        self.btnEdit.setFocusPolicy(Qt.NoFocus)
        self.btnEdit.setEnabled(0)
        self.btnEdit.clicked.connect(self.editPressed)
        self.btnEdit.rightPressed.connect(self.openEditorPressed)
        self.btnDatabase = QPushButton()
        hLayout.addWidget(self.btnDatabase)
        if write:
            self.btnDatabase.setIcon(self.pixDatabaseWrite)
            self.btnDatabase.setIconSize(buttonIconSize)
            self.btnDatabase.setToolTip(_t_("Browse the database (save mode)"))
        else:
            self.btnDatabase.setIcon(self.pixDatabaseRead)
            self.btnDatabase.setIconSize(buttonIconSize)
            self.btnDatabase.setToolTip(_t_("Browse the database (load mode)"))
        self.btnDatabase.setFixedSize(buttonIconSize + buttonMargin)
        self.btnDatabase.setFocusPolicy(Qt.NoFocus)

        self.customFileDialog = None
        if hasattr(parameter, 'fileDialog'):
            self.customFileDialog = parameter.fileDialog

        if hasattr(parameter, 'databaseUserLevel'):
            x = parameter.databaseUserLevel
            if x > neuroConfig.userLevel:
                self.btnDatabase.hide()
        self.btnDatabase.clicked.connect(self.databasePressed)
        self.databaseDialog = None
        self.btnBrowse = QPushButton()
        hLayout.addWidget(self.btnBrowse)
        if write:
            self.btnBrowse.setIcon(self.pixBrowseWrite)
            self.btnBrowse.setIconSize(buttonIconSize)
            self.btnBrowse.setToolTip(_t_("Browse the filesystem (save mode)"))
        else:
            self.btnBrowse.setIcon(self.pixBrowseRead)
            self.btnBrowse.setIconSize(buttonIconSize)
            self.btnBrowse.setToolTip(_t_("Browse the filesystem (load mode)"))
        self.btnBrowse.setFixedSize(buttonIconSize + buttonMargin)
        self.btnBrowse.setFocusPolicy(Qt.NoFocus)
        if hasattr(parameter, 'browseUserLevel'):
            x = parameter.browseUserLevel
            if x > neuroConfig.userLevel:
                self.btnBrowse.hide()
        self.btnBrowse.clicked.connect(self.browsePressed)
        self.browseDialog = None
        self._textChanged = False

    def isViewable(self):
        viewers = self.getViewers()
        return self.diskItem is not None and self.diskItem.isReadable() \
               and len(viewers) > 0
    
    def isEditable(self):
        editors = self.getDataEditors()
        return self.diskItem is not None and not self.diskItem.isLockData() \
           and self.diskItem.isWriteable() and len(editors) > 0

    def set_read_only(self, read_only):
        self.btnDatabase.setEnabled(not read_only)
        self.btnBrowse.setEnabled(not read_only)
        self.btnEdit.setEnabled(not read_only and self.isEditable())
        self.led.setReadOnly(read_only)
        self.led.setFrame(not read_only)

    def createPopupMenu(self, popup):
        if self.parameter.enableMultiResolution:
            self.cmbResolutionsSeparator = popup.addSeparator()
            addComboBoxMenu(self, popup, 
                            'resolution','resolution.png', 
                            'cmbResolutions', 'actResolutions', 
                            self.updateResolutions)
            self.cmbResolutions.currentIndexChanged[int].connect(
                self.setResolutionLevel)
        
        self.cmbViewersSeparator = popup.addSeparator()
        addComboBoxMenu(self, popup, 
                        'viewer', 'eye.png', 
                        'cmbViewers', 'actViewers',
                        self.updateViewersComboBox)

        self.cmbDataEditorsSeparator = popup.addSeparator()
        addComboBoxMenu(self, popup, 
                        'editor', 'pencil.png',
                        'cmbDataEditors', 'actDataEditors',
                        self.updateDataEditorsComboBox)

    def setResolutionLevel(self, resolution_level):
        v = self.getValue()
        if v is not None:
            v.setResolutionLevel(resolution_level)
            self.setValue(v)

    def updateResolutions(self):
        if self.parameter.enableMultiResolution:
            v = self.getValue()
            self.cmbResolutions.clear()
            
            if v is not None:
                res_infos = getResolutionsFromItems(v)
                
                if res_infos is not None and len(res_infos) > 1:           
                    
                    for level in six.moves.xrange(len(res_infos)):
                        self.cmbResolutions.addItem(res_infos[level], 
                                                    str(level))
                    resolution_level = v.resolutionLevel()                        
                        
                    if resolution_level is None:
                        resolution_level = len(res_infos) - 1
                        
                    self.cmbResolutions.setCurrentIndex(resolution_level)
                        
                    visible = True
                    
                else:
                    visible = False
                    
            else:
                visible = False
                
            # Display or hide the viewer action in popup menu
            self.cmbResolutionsSeparator.setVisible(visible)
            self.actResolutions.setVisible(visible)
      
    def setContext(self, newContext):
        oldContext = (self.btnShow.isChecked(), self._view,
                      self.btnEdit.isChecked(), self._edit)
        if newContext is None:
            self.btnShow.setChecked(False)
            self.btnEdit.setChecked(False)
            self._view = None
            self._edit = None
        else:
            if len(newContext) >= 4:
                o, v, z, e = newContext
            else:
                o, v = newContext
                z = e = 0
            self.btnShow.setChecked(o)
            self._view = v
            self.btnEdit.setChecked(z)
            self._edit = e
        return oldContext

    def getValue(self):
        return self.diskItem

    def setValue(self, value, default=0):
        self.forceDefault = default
        pal = QPalette()
        if self.diskItem != value or \
           (not(value is None and self.led.text() == '') \
            and (value != self.led.text())):
            self.diskItem = self.parameter.findValue(value)
            
            if self.diskItem is None:
                if value is None:
                    self.led.setText('')
                else:
                    # value is not None but is invalid: make it appear
                    pal.setColor(QPalette.Base, QColor(240, 150, 150))
                if self.btnShow:
                    self.btnShow.setEnabled(0)
                if self.btnEdit:
                    self.btnEdit.setEnabled(0)
                self.newValidValue.emit(
                    six.text_type(self.objectName()), self.diskItem)
            else:
                self.led.setText(self.diskItem.fullPath())
                self.checkReadable()
                self.newValidValue.emit(
                    six.text_type(self.objectName()), self.diskItem)
        self._textChanged = 0
        self.forceDefault = 0
        self.led.setPalette(pal)
        self.valuePropertiesChanged(default)

    def valuePropertiesChanged(self, isDefault):
        pal = self.led.palette()
        if not isDefault:
            pal.setColor(QPalette.Text, QColor(0, 0, 255))
        if self.diskItem is not None and self.diskItem.isLockData():
            pal.setColor(QPalette.Base, QColor(255, 230, 230))
        self.led.setPalette(pal)

    def lockChanged(self, locked):
        pal = self.led.palette()
        if self.diskItem is not None and self.diskItem.isLockData():
            pal.setColor(QPalette.Base, QColor(255, 230, 230))
        else:
            pal2 = QPalette()
            pal.setColor(QPalette.Base, pal2.color(QPalette.Base))
        self.led.setPalette(pal)

    def checkReadable(self):
        if self.btnShow:
            enabled = 0
            if self.diskItem:
                if len(self.getViewers()) > 0:
                    self.btnShow.show()
                else:
                    self.btnShow.hide()
                enabled = self.isViewable()
                
            self.btnShow.setEnabled(enabled)
            
        if self.btnEdit:
            enabled = 0
            if self.diskItem:
                if len(self.getDataEditors()) > 0:
                    self.btnEdit.show()
                else:
                    self.btnEdit.hide()
                enabled = self.isEditable()
            self.btnEdit.setEnabled(enabled)

    def textChanged(self):
        self._textChanged = 1
        if not self.forceDefault:
            self.noDefault.emit(six.text_type(self.objectName()))

    def checkValue(self):
        if self._textChanged:
            self.setValue(six.text_type(self.led.text()))

    def showPressed(self):
        if self.btnShow.isChecked():
            self.btnShow.setEnabled(0)
            v = self.getValue()
            viewerExists = False
            try:
                for viewer in self.viewersToTry():
                    try:
                        viewer = getProcessInstance(viewer)
                        viewerExists = True
                        if self.process is not None \
                                and hasattr(viewer, 'allowed_processes'):
                            viewer.reference_process = self.process
                        brainvisa.processes.defaultContext().runInteractiveProcess(
                            self._viewerExited, viewer, v)
                        self.btnShow.setEnabled(True)
                        return

                    except Exception:
                        # Try another viewer if possible
                        brainvisa.processes.defaultContext().log(
                            _t_('Warning for %s') % _t_(viewer.name),
                          html=_t_('Viewer aborted for type=<em>%s</em> and '
                                   'format=<em>%s</em> value=<em>%s</em> '
                                   '(try using it interactively by '
                                   'right-clicking on the eye icon)')
                          % (six.text_type(v.type), six.text_type(v.format), six.text_type(v)),
                          icon='eye.png')
                        continue

                # if a viewer exists, still keep the button enabled to allow using the
                # right-click options
                self.btnShow.setEnabled(viewerExists)
                self.btnShow.setChecked(False)
                raise RuntimeError(
                    HTMLMessage(_t_('No viewer could be found for type=<em>%s</em> and format=<em>%s</em>') % (six.text_type(v.type), six.text_type(v.format))))

            except Exception as error:
                    # transform the exception into a print message, and return.
                    # We are in a Qt slot here, raising an exception results in
                    # undefined behaviour, which happens to have changed between PyQt 5.4
                    # and PyQt 5.5
                print(error)
                import traceback
                traceback.print_exc()
        else:
            self._view = None

    def _viewerExited(self, result):
        if isinstance(result, Exception):
            showException(parent=self)
        else:
            self._view = result
        neuroProcessesGUI.mainThreadActions().push(
            self.btnShow.setEnabled, True)
        if result is None:
            neuroProcessesGUI.mainThreadActions().push(
                self.btnShow.setChecked, False)

    def close_viewer(self):
        if self._view is not None:
            self._view = None
            neuroProcessesGUI.mainThreadActions().push(
                self.btnShow.setChecked, False)
            neuroProcessesGUI.mainThreadActions().push(
                self.btnShow.setEnabled, True)

    def openViewerPressed(self, pos):
        v = self.getValue()
        if v.get('lastHistoricalEvent'):
            popup = QMenu(self)
            op = popup.addAction(DiskItemEditor.pixShow, 'open viewer')
            sh = popup.addAction(DiskItemEditor.pixHistory, 'show history')
            ac = popup.exec_(pos)
            if ac is not None:
                if ac is sh:
                    self.openHistory()
                else:
                    self.openViewer()
        else:
            self.openViewer()

    def openViewer(self):
        # Normally it is not possible to try to open viewer if none is
        # available
        try:
            viewer = getProcessInstance(self.viewersToTry()[0])
            v = self.getValue()
            if self.process is not None \
                    and hasattr(viewer, 'allowed_processes'):
                viewer.reference_process = self.process
            neuroProcessesGUI.showProcess(viewer, v)
        except Exception as e:
            print('openViewer failed:', e)
            import traceback
            traceback.print_exc()

    def getViewers(self, update = False):
        if self._viewers is None or update:
            self.updateViewers()
        
        return self._viewers

    def selectedViewer(self):
        # Current index is shifted in Combo box due to the 'Default value' item
        if self.cmbViewers is not None:
            index = self.cmbViewers.currentIndex()
            if index != -1 and index > 0 and index <= len(self._viewers):
                return self._viewers[index - 1]

        return None

    def updateViewers(self):
        if self.diskItem is None:
            format = None
            if len(self.parameter.formats) != 0:
                format = self.parameter.formats[0]
            source = (self.parameter.type, format)
        else:
            source = self.diskItem

        self._viewers = brainvisa.processes.getViewers(
            source, 1, checkUpdate=False, process=self.process,
                                check_values=True)

    def updateViewersComboBox(self):
        if self.cmbViewers is not None:
            v = self.selectedViewer()
            # print('selected viewer:', v)

            # Update viewers in combo box
            self.cmbViewers.clear()
            self.cmbViewers.addItem(_t_('Default'), None)
            self.getViewers() # to update if needed
            for viewer in self._viewers:
                self.cmbViewers.addItem(_t_(viewer.name), viewer)

            if v is not None and v in self._viewers:
                i = self._viewers.index(v)
                self.cmbViewers.setCurrentIndex(i + 1)

            # else:
                # print('Selecting default item with index', self.cmbViewers.findText(_t_('Default')))
                # Select default value
                # self.cmbViewers.setCurrentIndex(0)

            # Display or hide the viewer action in popup menu
            visible = len(self._viewers) > 1
            self.cmbViewersSeparator.setVisible(visible)
            self.actViewers.setVisible(visible)

        if len(self._viewers) == 0:
            self.btnShow.hide()

    def viewersToTry(self):
        viewer = getProcessInstance(self.selectedViewer())
        if viewer is None:
            return self.getViewers()
        else:
            return [viewer]

    def openHistory(self):
        v = self.getValue()
        bvproc_uuid = v.get("lastHistoricalEvent", None)
        if bvproc_uuid is not None:
            history_window = historygui.DataHistoryWindow(v, bvproc_uuid,
                                                          parent=self)
            history_window.setAttribute(Qt.WA_DeleteOnClose)
            history_window.show()

    def getDataEditors(self, update = False):
        if self._editors is None or update:
            self.updateDataEditors()

        return self._editors

    def selectedDataEditor(self):
        # Current index is shifted in Combo box due to the 'Default value' item
        self.getDataEditors() # trigger update if needed
        if self.cmbDataEditors is not None:
            index = self.cmbDataEditors.currentIndex()
            if index != -1 and index > 0 and index <= len(self._editors):
                return self._editors[index - 1]

        return None

    def editPressed(self):
        if self.btnEdit.isChecked():
            self.btnEdit.setEnabled(0)
            v = self.getValue()
            editorExists = False
            try:
                for editor in self.dataEditorsToTry():
                    # print('try editor:', editor.name)
                    try:
                        editor = getProcessInstance(editor())
                        editorExists = True
                        if self.process is not None \
                                and hasattr(editor, 'allowed_processes'):
                            editor.reference_process = self.process
                        brainvisa.processes.defaultContext().runInteractiveProcess(
                            self._editorExited, editor, v)
                        self.btnEdit.setEnabled(True)
                        return

                    except Exception:
                        # Log an error then try another editor if possible
                        brainvisa.processes.defaultContext().log(
                            _t_('Warning for %s') % _t_(editor.name),
                          html=_t_('Editor aborted for type=<em>%s</em> and '
                                   'format=<em>%s</em> value=<em>%s</em> '
                                   '(try using it interactively by '
                                   'right-clicking on the pencil icon)')
                          % (six.text_type(v.type), six.text_type(v.format), six.text_type(v)),
                          icon='pencil.png')
                        continue

                self.btnEdit.setEnabled(False)
                self.btnEdit.setChecked(False)
                raise RuntimeError(HTMLMessage(_t_('No editor could be found for '
                                                   'type=<em>%s</em> and format=<em>%s</em>')
                                               % (six.text_type(v.type), six.text_type(v.format))))

            except Exception as error:
                    # transform the exception into a print message, and return.
                    # We are in a Qt slot here, raising an exception results in
                    # undefined behaviour, which happens to have changed between PyQt 5.4
                    # and PyQt 5.5
                print(error)
                import traceback
                traceback.print_stack()
        else:
            self._edit = None

    def _editorExited(self, result):
        if isinstance(result, Exception):
            showException(parent=self)
        else:
            self._view = result
        neuroProcessesGUI.mainThreadActions().push(
            self.btnEdit.setEnabled, True)
        if result is None:
            neuroProcessesGUI.mainThreadActions().push(
                self.btnEdit.setChecked, False)

    def close_editor(self):
        if self._edit is not None:
            self._edit = None
            neuroProcessesGUI.mainThreadActions().push(
                self.btnShow.setChecked, False)
            neuroProcessesGUI.mainThreadActions().push(
                self.btnShow.setEnabled, True)

    def openEditorPressed(self):
        editor = getProcessInstance(self.dataEditorsToTry()[0]())
        v = self.getValue()
        if self.process is not None \
                and hasattr(editor, 'allowed_processes'):
            editor.reference_process = self.process
        neuroProcessesGUI.showProcess(editor, v)

    def updateDataEditors(self):
        if self.diskItem is None:
            format = None
            if len(self.parameter.formats) != 0:
                format = self.parameter.formats[0]
            source = (self.parameter.type, format)
        else:
            source = self.diskItem

        try:
            self._editors = brainvisa.processes.getDataEditors(
                source, 0, checkUpdate=False, process=self.process)
        except Exception:
            self._editors = None

    def updateDataEditorsComboBox(self):
        if self.cmbDataEditors is not None:
            e = self.selectedDataEditor()
            # print('selected data editor:', v)

            # Update editors in combo box
            self.cmbDataEditors.clear()
            self.cmbDataEditors.addItem(_t_('Default'), None)
            self.getDataEditors() # update if needed
            for editor in self._editors:
                self.cmbDataEditors.addItem(_t_(editor.name), editor)

            if e is not None and e in self._editors:
                i = self._editors.index(e)
                self.cmbDataEditors.setCurrentIndex(i + 1)

            # else:
                # print('Selecting default item with index', self.cmbDataEditors.findText(_t_('Default')))
                # Select default value
                # self.cmbDataEditors.setCurrentIndex(0)

            # Display or hide the data editor action in popup menu
            visible = len(self._editors) > 1
            self.cmbDataEditorsSeparator.setVisible(visible)
            self.actDataEditors.setVisible(visible)

        if len(self._editors) == 0:
            self.btnEdit.hide()

    def dataEditorsToTry(self):
        editor = getProcessInstance(self.selectedDataEditor())
        if editor is None:
            return self.getDataEditors()
        else:
            return [editor]

    def databasePressed(self):
        try:
            if self.databaseDialog is None or self.parameter._modified:
                self.parameter._modified = 0
                if self.diskItem:  # this parameter has already a value, use it to initialize the browser
                    selection = self.diskItem.hierarchyAttributes()
                    if self.diskItem.type is None:
                        selection['_type'] = None
                    else:
                        selection['_type'] = self.diskItem.type.name
                    if self.diskItem.format is None:
                        selection['_format'] = None
                    else:
                        selection['_format'] = self.diskItem.format.name

                    self.databaseDialog = DiskItemBrowser(
                        self.parameter.database, selection=selection, required=self.parameter.requiredAttributes, parent=self, write=self._write,
                        enableConversion=self.parameter.enableConversion, exactType=self.parameter.exactType)
                else:  # if there is no value, we could have some selected attributes from a linked value, use it to initialize the browser
                    self.databaseDialog = DiskItemBrowser(
                        self.parameter.database, selection=self.parameter._selectedAttributes, required=self.parameter.requiredAttributes,
                                                          parent=self, write=self._write, enableConversion=self.parameter.enableConversion, exactType=self.parameter.exactType)
                self.databaseDialog.setWindowTitle(_t_(self.parameter.type.name))
                self.databaseDialog.accepted.connect(self.databaseAccepted)
            else:
                self.databaseDialog.resetSelectedAttributes(
                    self.diskItem, self.parameter._selectedAttributes)
            self.databaseDialog.show()
        except Exception:
            showException(parent=self)

    def databaseAccepted(self):
        values = self.databaseDialog.getValues()
        if values:
            self.setValue(values[0])

    def browsePressed(self):
        if self.browseDialog is None or self.parameter._modified:
            self.parameter._modified = False
            if self.customFileDialog:
                self.browseDialog = self.customFileDialog(self)
            else:
                self.browseDialog = QFileDialog(self)
            if self._write:
                mode = QFileDialog.AnyFile
            else:
                mode = QFileDialog.ExistingFile
            filters = []
            allPatterns = {}
            dirOnly = True
            formats = set(self.parameter.formats)
            if self.parameter.enableConversion:
                for t in [self.parameter.type] + self.parameter.type.parents():
                    for f in self.parameter.formats:
                        conv = brainvisa.processes.getConvertersTo((t, f))
                        for t2, f2 in six.iterkeys(conv):
                            formats.add(f2)
            for f in formats:
                if f.fileOrDirectory() is not Directory:
                    dirOnly = False
                flt = f.getPatterns().unmatch(
                    {}, {'filename_variable': '*'})[0]
                allPatterns[flt] = 1
                filters.append(_t_(f.name) + ' (' + flt + ')')
            filters.insert(0, _t_('Recognized formats') + ' ('
                           + ' '.join(list(allPatterns.keys())) + ')')
            filters.append(_t_('All files') + ' (*)')
            if dirOnly:
                mode = QFileDialog.Directory
            self.browseDialog.setFileMode(mode)
            self.browseDialog.setNameFilters(filters)
            if self.customFileDialog and self.customFileDialog.customFilter != "":
                self.browseDialog.selectFilter(
                    self.customFileDialog.customFilter)
            self.browseDialog.accepted.connect(self.browseAccepted)
        # set current directory
        parent = self._context
        if hasattr(parent, '_currentDirectory') and parent._currentDirectory:
            self.browseDialog.setDirectory(parent._currentDirectory)
        else:
            self.browseDialog.setDirectory(os.getcwd())
        self.browseDialog.show()

    def browseAccepted(self):
        value = self.browseDialog.selectedFiles()
        if (len(value) > 0):
            value = six.text_type(value[0])
        else:
            value = None
        parent = self._context
        if hasattr(parent, '_currentDirectory'):
            parent._currentDirectory = six.text_type(
                self.browseDialog.directory().path())
        self.setValue(value)

    def releaseCallbacks(self):
        self._view = None
        self._edit = None


#----------------------------------------------------------------------------
class DiskItemListEditor(QWidget, DataEditor):

    noDefault = QtCore.Signal(six.text_type)
    newValidValue = QtCore.Signal(six.text_type, object)

    class DiskItemListSelect(QWidget):  # Ex QSemiModal

        accepted = QtCore.Signal((six.text_type, ), (list,))
        # accepted = QtCore.Signal(list)

        def __init__(self, dilEditor, name, write, context=None,
                     databaseUserLevel=0, browseUserLevel=0):
            self._context = context
            if getattr(DiskItemListEditor.DiskItemListSelect, 'pixUp', None) is None:
                setattr(DiskItemListEditor.DiskItemListSelect, 'pixUp',
                        QIcon(findIconFile('up.png')))
                setattr(DiskItemListEditor.DiskItemListSelect, 'pixDown',
                        QIcon(findIconFile('down.png')))
                setattr(DiskItemListEditor.DiskItemListSelect, 'pixFindRead',
                        QIcon(findIconFile('database_read.png')))
                setattr(DiskItemListEditor.DiskItemListSelect, 'pixFindWrite',
                        QIcon(findIconFile('database_write.png')))
                setattr(DiskItemListEditor.DiskItemListSelect, 'pixBrowseRead',
                        QIcon(findIconFile('browse_read.png')))
                setattr(
                    DiskItemListEditor.DiskItemListSelect, 'pixBrowseWrite',
                  QIcon(findIconFile('browse_write.png')))
                setattr(
                    DiskItemListEditor.DiskItemListSelect, 'pixBrowseUpdate',
                  QIcon(findIconFile('browse_update.png')))
            QWidget.__init__(
                self, dilEditor.window(), Qt.Dialog | Qt.WindowStaysOnTopHint)
            if name:
                self.setObjectName(name)
            self.setAttribute(Qt.WA_DeleteOnClose, True)
            self.setWindowModality(Qt.WindowModal)
            layout = QVBoxLayout()
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(5)
            self.setLayout(layout)

            self.dilEditor = dilEditor
            self.parameter = dilEditor.parameter
            self.values = []
            self.browseDialog = None
            self.findDialog = None

            self.lbxValues = QListWidget()
            self.lbxValues.setSelectionMode(QListWidget.ExtendedSelection)
            # self.lbxValues.currentRowChanged.connect(self._currentChanged)
            self.lbxValues.itemSelectionChanged.connect(self._selectionChanged)
            layout.addWidget(self.lbxValues)

            self.textLine = QLabel()
            layout.addWidget(self.textLine)

            hb = QHBoxLayout()
            hb.setSpacing(6)

            self.btnAdd = QPushButton(_t_('Add'))
            self.btnAdd.setEnabled(0)
            self.btnAdd.clicked.connect(self._add)
            hb.addWidget(self.btnAdd)

            self.btnRemove = QPushButton(_t_('Remove'))
            self.btnRemove.setEnabled(0)
            self.btnRemove.clicked.connect(self._remove)
            hb.addWidget(self.btnRemove)

            self.btnUp = QPushButton()
            self.btnUp.setIcon(self.pixUp)
            self.btnUp.setIconSize(buttonIconSize)
            self.btnUp.setEnabled(0)
            self.btnUp.clicked.connect(self._up)
            hb.addWidget(self.btnUp)

            self.btnDown = QPushButton()
            self.btnDown.setIcon(self.pixDown)
            self.btnDown.setIconSize(buttonIconSize)
            self.btnDown.setEnabled(0)
            self.btnDown.clicked.connect(self._down)
            hb.addWidget(self.btnDown)

            if write:
                # Add a button to change output directories of selected items
                self.btnSetDirectory = QPushButton()
                self.btnSetDirectory.setIcon(self.pixBrowseUpdate)
                self.btnSetDirectory.setIconSize(buttonIconSize)
                self.btnSetDirectory.setEnabled(0)
                self.btnSetDirectory.clicked.connect(self._setDirectory)
                hb.addWidget(self.btnSetDirectory)

            spacer = QSpacerItem(
                10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)
            hb.addItem(spacer)

            layout.addLayout(hb)

            hb = QHBoxLayout()
            hb.setSpacing(6)

            self.sle = StringListEditor(None, six.text_type(self.objectName()))
            self.sle.newValidValue.connect(self.checkUI)
            hb.addWidget(self.sle)

            btn = QPushButton()
            if write:
                btn.setIcon(self.pixFindWrite)
            else:
                btn.setIcon(self.pixFindRead)
            btn.setIconSize(buttonIconSize)
            if databaseUserLevel > neuroConfig.userLevel:
                btn.hide()
            btn.clicked.connect(self.findPressed)
            hb.addWidget(btn)

            btn = QPushButton()
            if write:
                btn.setIcon(self.pixBrowseWrite)
            else:
                btn.setIcon(self.pixBrowseRead)
            btn.setIconSize(buttonIconSize)
            if browseUserLevel > neuroConfig.userLevel:
                btn.hide()
            btn.clicked.connect(self.browsePressed)
            hb.addWidget(btn)

            layout.addLayout(hb)

#      self.editor = self.parameter.editor( self, self.name() )
#      layout.addWidget( self.editor )

            hb = QHBoxLayout()
            hb.setSpacing(6)
            hb.setContentsMargins(6, 6, 6, 6)
            spacer = QSpacerItem(
                20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            hb.addItem(spacer)
            btn = QPushButton(_t_('Ok'))
            hb.addWidget(btn)
            btn.clicked.connect(self._ok)
            btn = QPushButton(_t_('Cancel'))
            hb.addWidget(btn)
            btn.clicked.connect(self._cancel)
            layout.addLayout(hb)

            neuroConfig.registerObject(self)

        def closeEvent(self, event):
            neuroConfig.unregisterObject(self)
            QWidget.closeEvent(self, event)

        def checkUI(self):
            # Check that user interface buttons are coherent with values

            sindexes = [i.row() for i in self.lbxValues.selectedIndexes()]
            sindexes.sort()

            if len(sindexes) > 0:
                self.btnRemove.setEnabled(1)

                if hasattr(self, 'btnSetDirectory'):
                    self.btnSetDirectory.setEnabled(1)

                if (sindexes[0] > 0) or (len(sindexes) > 1):
                    self.btnUp.setEnabled(1)
                else:
                    self.btnUp.setEnabled(0)

                if (sindexes[-1] < (len(self.values) - 1)) or (len(sindexes) > 1):
                    self.btnDown.setEnabled(1)
                else:
                    self.btnDown.setEnabled(0)

            else:
                self.btnRemove.setEnabled(0)
                if hasattr(self, 'btnSetDirectory'):
                    self.btnSetDirectory.setEnabled(0)
                self.btnUp.setEnabled(0)
                self.btnDown.setEnabled(0)

            self.btnAdd.setEnabled(self.sle.getValue() is not None)

            return None

        # def _currentChanged( self, index ):
            # if index >= 0 and index < len( self.values ):
                # if self.values[ index ] :
                    # self.sle.setValue( [ self.values[ index ].fullPath() ] )
                # else :
                    # self.sle.setValue( None )

            # else:
                # self.sle.setValue( None )

        def updateEditorValue(self):
            if len(self.lbxValues.selectedIndexes()) > 0:
                v = [self.values[s.row()]
                     for s in self.lbxValues.selectedIndexes()]
                self.sle.setValue(v)
            else:
                self.sle.setValue(None)

        def _selectionChanged(self):
            self.checkUI()
            self.updateEditorValue()
            self.textLine.setText('items: %d, selected: %d'
                                  % (self.lbxValues.count(), len(self.lbxValues.selectedIndexes())))

        def _add(self):
            try:
                for v in map(self.parameter.findValue, self.sle.getValue()):
                    self.values.append(v)
                    if v is None:
                        self.lbxValues.addItem('<' + _t_('None') + '>')
                    else:
                        self.lbxValues.addItem(v.fileName())

                self.lbxValues.clearSelection()
                self.lbxValues.setCurrentRow(len(self.values) - 1,
                                             QItemSelectionModel.SelectCurrent)
            except Exception:
                showException(parent=self)

        def _remove(self):
            indexes = [i.row() for i in self.lbxValues.selectedIndexes()]
            rindexes = list(indexes)
            rindexes.sort()
            lindex = rindexes.index(indexes[-1])
            rindexes.reverse()
            for index in rindexes:
                del self.values[index]
                self.lbxValues.takeItem(index)

            # Select the item preceding the last deleted item
            if (indexes[-1] - lindex) <= 0:
                c = 0
            elif (indexes[-1] - lindex) >= (len(self.values) - 1):
                c = len(self.values) - 1
            else:
                c = indexes[-1] - lindex

            self.lbxValues.setCurrentRow(c,
                                         QItemSelectionModel.SelectCurrent)

            # if (c == indexes[-1]) :
                # Artificially ensure that value was changed
                # self.updateEditorValues()

        def _up(self):
            indexes = [i.row() for i in self.lbxValues.selectedIndexes()]
            sindexes = list(indexes)
            sindexes.sort()

            for index in sindexes:
                if index > 0:
                    tmp = self.values[index]
                    self.values[index] = self.values[index - 1]
                    self.values[index - 1] = tmp
                    item = self.lbxValues.takeItem(index)
                    self.lbxValues.insertItem(index - 1, item)
                    self.lbxValues.setItemSelected(item, 1)

        def _down(self):
            indexes = [i.row() for i in self.lbxValues.selectedIndexes()]
            rindexes = list(indexes)
            rindexes.sort()
            rindexes.reverse()
            for index in rindexes:
                if (index + 1) < len(self.values):
                    tmp = self.values[index]
                    self.values[index] = self.values[index + 1]
                    self.values[index + 1] = tmp
                    item = self.lbxValues.takeItem(index)
                    self.lbxValues.insertItem(index + 1, item)
                    self.lbxValues.setItemSelected(item, 1)

        def _setDirectory(self):
            self.browseDirectoryDialog = QFileDialog(self.window())
            self.browseDirectoryDialog.accepted.connect(
                self._setDirectoryAccepted)
            self.browseDirectoryDialog.setFileMode(QFileDialog.Directory)
            self.browseDirectoryDialog.setOption(
                QFileDialog.ShowDirsOnly, True)
            parent = self._context
            if hasattr(parent, '_currentDirectory') and parent._currentDirectory:
                self.browseDirectoryDialog.setDirectory(
                    parent._currentDirectory)
            else:
                self.browseDirectoryDialog.setDirectory(os.getcwd())
            self.browseDirectoryDialog.show()

        def _setDirectoryAccepted(self):
            parent = self._context
            # Get the selected directory
            directory = six.text_type(self.browseDirectoryDialog.selectedFiles()[0])
            if hasattr(parent, '_currentDirectory'):
                parent._currentDirectory = directory

            if self.isVisible():
                indexes = [i.row() for i in self.lbxValues.selectedIndexes()]
                for index in indexes:
                    # Replaces the disk item with a new one
                    self.values[index] = brainvisa.data.neuroDiskItems.File(
                        os.path.join(directory,
                                     os.path.basename(
                                     self.values[index].fullPath(
                                     ))),
                        None)
                    self.lbxValues.item(index).setText(
                        self.values[index].fullPath())

                # Updates current editor value
                self.updateEditorValue()

            else:
                self.accepted.emit(six.text_type(directory))

        def setValue(self, value):
            if isinstance(value, (list, tuple)):
                self.values = []
                self.lbxValues.clear()
                for v in value:
                    self.values.append(v)
                    if v is None:
                        self.lbxValues.addItem('<' + _t_('None') + '>')
                    else:
                        self.lbxValues.addItem(v.fileName())

        def _ok(self):
            self.dilEditor._newValue(self.values)
            self.close()

        def _cancel(self):
            self.close()

        def findPressed(self):
            if self.findDialog is None:
                self.findDialog = DiskItemBrowser(self.parameter.database,
                                                  required=self.parameter.requiredAttributes,
                                                  parent=self,
                                                  write=self.parameter._write,
                                                  enableConversion=self.parameter.enableConversion,
                                                  multiple=True,
                                                  exactType=self.parameter.exactType)
                self.findDialog.accepted[()].connect(self.findAccepted)
            else:
                self.findDialog.rescan()
            self.findDialog.show()

        def findAccepted(self):
            value = [x.fullPath() for x in self.findDialog.getValues()]
            if self.isVisible():
                self.sle.setValue(value)
                self._add()
            else:
                self.accepted[list].emit(value)

        def browsePressed(self):
            if self.browseDialog is None:
                self.browseDialog = QFileDialog(self.window())
                if not self.parameter._write:
                    self.browseDialog.setFileMode(QFileDialog.ExistingFiles)
                else:
                    self.browseDialog.setFileMode(QFileDialog.AnyFile)

                filters = []
                allPatterns = {}
                dirOnly = 1
                formats = set(self.parameter.formats)
                if self.parameter.enableConversion:
                    for t in [self.parameter.type] + self.parameter.type.parents():
                        for f in self.parameter.formats:
                            conv = brainvisa.processes.getConvertersTo(
                                (t, f))
                            for t2, f2 in six.iterkeys(conv):
                                formats.add(f2)
                for f in formats:
                    if f.fileOrDirectory() is not Directory:
                        dirOnly = 0
                    flt = f.getPatterns().unmatch(
                        {}, {'filename_variable': '*'})[0]
                    allPatterns[flt] = 1
                    filters.append(_t_(f.name) + ' (' + flt + ')')
                filters.insert(0, _t_('Recognized formats') + ' ('
                               + ' '.join(list(allPatterns.keys())) + ')')
                filters.append(_t_('All files') + ' (*)')
                self.browseDialog.setNameFilters(filters)
                # self.browseDialog.fileSelected.connect(self.browseAccepted)
                self.browseDialog.accepted.connect(self.browseAccepted)
                if dirOnly:
                    self.browseDialog.setFileMode(QFileDialog.Directory)
                    self.browseDialog.setOption(QFileDialog.ShowDirsOnly)
                parent = self._context
                if hasattr(parent, '_currentDirectory') and parent._currentDirectory:
                    self.browseDialog.setDirectory(parent._currentDirectory)
                else:
                    self.browseDialog.setDirectory(os.getcwd())

                # Set multiselection even for Directory and AnyFile modes
                self.browseDialog.setOption(
                    QFileDialog.DontUseNativeDialog, True)
                l = self.browseDialog.findChild(QListView, "listView")
                if l:
                    l.setSelectionMode(QAbstractItemView.ExtendedSelection)
                t = self.browseDialog.findChild(QTreeView)
                if t:
                    t.setSelectionMode(QAbstractItemView.ExtendedSelection)
                e = self.browseDialog.findChild(QLineEdit)
                if e:
                    # Increases QLineEdit maximum length wich default was to 32767
                    e.setMaxLength(2**20)

            self.browseDialog.show()

        def browseAccepted(self):
            parent = self._context
            if hasattr(parent, '_currentDirectory'):
                parent._currentDirectory = six.text_type(
                    self.browseDialog.directory().path())
            l = [str(i) for i in self.browseDialog.selectedFiles()]
            if self.isVisible():
                self.sle.setValue(l)
                self._add()
            else:
                self.accepted[list].emit(l)

    def __init__(self, parameter, parent, name, write=0, context=None,
                 process=None):
        if getattr(DiskItemListEditor, 'pixFindRead', None) is None:
            setattr(DiskItemListEditor, 'pixShow',
                    QIcon(findIconFile('eye.png')))
            setattr(DiskItemListEditor, 'pixEdit',
                    QIcon(findIconFile('pencil.png')))
            setattr(DiskItemListEditor, 'pixFindRead',
                    QIcon(findIconFile('database_read.png')))
            setattr(DiskItemListEditor, 'pixFindWrite',
                    QIcon(findIconFile('database_write.png')))
            setattr(DiskItemListEditor, 'pixBrowseRead',
                    QIcon(findIconFile('browse_read.png')))
            setattr(DiskItemListEditor, 'pixBrowseWrite',
                    QIcon(findIconFile('browse_write.png')))
        QWidget.__init__(self, parent)
        if name:
            self.setObjectName(name)
        hb = QHBoxLayout()
        self.setLayout(hb)
        hb.setContentsMargins(0, 0, 0, 0)
        hb.setSpacing(2)
        self._context = context
        self.parameter = parameter
        self.write = write
        self.sle = StringListEditor(None, name)
        hb.addWidget(self.sle)
        self._value = None
        self.sle.newValidValue.connect(self._newTextValue)

        self.btnShow = RightClickablePushButton()
        hb.addWidget(self.btnShow)
        self.btnShow.setCheckable(True)
        self.btnShow.setIcon(self.pixShow)
        self.btnShow.setIconSize(buttonIconSize)
        self.btnShow.setFixedSize(buttonIconSize + buttonMargin)
        self.btnShow.setFocusPolicy(Qt.NoFocus)
        self.btnShow.setEnabled(False)
        if process is None:
            self.process = None
        else:
            if isinstance(process, weakref.ProxyType):
                self.process = process
            else:
                self.process = weakref.proxy(process)

        # Sets default viewers list
        self._viewers = None
        self.actViewers = None
        self.cmbViewersSeparator = None
        self.cmbViewers = None
        self.newValidValue.connect(self.updateViewers)

        self._view = None
        self.btnShow.clicked.connect(self.showPressed)
        self.btnShow.rightPressed.connect(self.openViewerPressed)

        self._edit = None
        self.btnEdit = RightClickablePushButton()
        hb.addWidget(self.btnEdit)
        self.btnEdit.setCheckable(True)
        self.btnEdit.setIcon(self.pixEdit)
        self.btnEdit.setIconSize(buttonIconSize)
        self.btnEdit.setFixedSize(buttonIconSize + buttonMargin)
        self.btnEdit.setFocusPolicy(Qt.NoFocus)
        self.btnEdit.setEnabled(0)
        # if not brainvisa.processes.getDataEditor( (self.parameter.type, self.parameter.formats ), checkUpdate=False, listof=True ):
            # self.btnEdit.hide()
        self.btnEdit.clicked.connect(self.editPressed)
        self.btnEdit.rightPressed.connect(self.openEditorPressed)

        # Sets default data editors list
        self._editors = None
        self.actDataEditors = None
        self.cmbDataEditorsSeparator = None
        self.cmbDataEditors = None
        self.newValidValue.connect(self.updateDataEditors)
        
        # Sets default resolutions list
        self.actResolutions = None
        self.cmbResolutionsSeparator = None
        self.cmbResolutions = None
        self._res_infos = None

        self.btnFind = RightClickablePushButton()
        hb.addWidget(self.btnFind)
        if write:
            self.btnFind.setIcon(self.pixFindWrite)
        else:
            self.btnFind.setIcon(self.pixFindRead)
        self.btnFind.setIconSize(buttonIconSize)
        self.btnFind.setFixedSize(buttonIconSize + buttonMargin)
        self.btnFind.setFocusPolicy(Qt.NoFocus)
        if hasattr(parameter, 'databaseUserLevel'):
            x = parameter.databaseUserLevel
            if x > neuroConfig.userLevel:
                self.btnFind.hide()
        self.btnFind.clicked.connect(self.findPressed)
        self.btnFind.rightPressed.connect(self.findRightPressed)
        self.btnBrowse = QPushButton()
        hb.addWidget(self.btnBrowse)
        if write:
            self.btnBrowse.setIcon(self.pixBrowseWrite)
        else:
            self.btnBrowse.setIcon(self.pixBrowseRead)
        self.btnBrowse.setIconSize(buttonIconSize)
        self.btnBrowse.setFixedSize(buttonIconSize + buttonMargin)
        self.btnBrowse.setFocusPolicy(Qt.NoFocus)
        if hasattr(parameter, 'browseUserLevel'):
            x = parameter.browseUserLevel
            if x > neuroConfig.userLevel:
                self.btnBrowse.hide()
        # only one click on the browse button : always open the diskItemListSelect widget
        # as we often need to select files in the filesystem in several steps
        # when the files are not all in the same directory.
        self.btnBrowse.clicked.connect(self.browsePressed)

        self.setValue(None, 1)

    def createPopupMenu(self, popup):
        if self.parameter.enableMultiResolution:
            self.cmbResolutionsSeparator = popup.addSeparator()
            addComboBoxMenu(self, popup, 
                            'resolution','resolution.png', 
                            'cmbResolutions', 'actResolutions', 
                            self.updateResolutions)
            self.cmbResolutions.currentIndexChanged[int].connect(
                self.setResolutionLevel)
        
        self.cmbViewersSeparator = popup.addSeparator()
        addComboBoxMenu(self, popup, 
                        'viewer', 'eye.png', 
                        'cmbViewers', 'actViewers',
                        self.updateViewersComboBox)

        self.cmbDataEditorsSeparator = popup.addSeparator()
        addComboBoxMenu(self, popup, 
                        'editor', 'pencil.png',
                        'cmbDataEditors', 'actDataEditors',
                         self.updateDataEditorsComboBox)

    def setResolutionLevel(self, resolution_level):
        v = self.getValue()
        if v is not None:
            for i in v:
                if i is not None:
                    i.setResolutionLevel(resolution_level)
            self.setValue(v)

    def updateResolutions(self):
        v = self.getValue()
        visible = False
        
        if v is not None and None not in v:
            res_infos = getResolutionsFromItems(v)
            
            if self._res_infos != res_infos:
                self._res_infos = res_infos
                if res_infos is not None and len(res_infos) > 1:
                    self.cmbResolutions.clear()
                    for level in six.moves.xrange(len(res_infos)):
                        self.cmbResolutions.addItem(res_infos[level], 
                                                    str(level))
                    
                    resolution_level = None
                    for i in six.moves.xrange(len(v)):
                        if i == 0:
                            resolution_level = v[i].resolutionLevel()
                            
                        else:
                            r = v[i].resolutionLevel()
                            
                            # If 2 items do not have the same resolution level
                            # select default (this choice can be discussed)
                            if resolution_level != r:
                                resolution_level = None
                                break
                            
                    if resolution_level is None:
                        resolution_level = len(res_infos) - 1
                        
                    self.cmbResolutions.setCurrentIndex(resolution_level)
                    
                    visible = True
            
            else:
                visible = res_infos is not None and len(res_infos) > 1
                
        # Display or hide the viewer action in popup menu
        self.cmbResolutionsSeparator.setVisible(visible)
        self.actResolutions.setVisible(visible)

    def getValue(self):
        return self._value

    def _setValue(self, value):
        self._value = value
        if isinstance(value, (list, tuple)):
            r = []
            for v in value:
                if v is None:
                    r.append('')
                else:
                    r.append(str(v))
            value = r
        self.sle._setValue(value)

    def setValue(self, value, default=0):
        self.forceDefault = default
        self._value = value
        if isinstance(value, (list, tuple)):
            r = []
            for v in value:
                if v is None:
                    r.append('')
                else:
                    r.append(str(v))
            value = r
        if value:
            self.checkReadable()
        else:
            if self.btnShow:
                self.btnShow.setEnabled(0)
            if self.btnEdit:
                self.btnEdit.setEnabled(0)
        
        self.sle.setValue(value, default)
        self.forceDefault = 0

    def isViewable(self):
        if self._value:
            viewable = True
            viewers = self.getViewers()
            for v in self._value:
                if not (v and isinstance(v, DiskItem) and v.isReadable()):
                    viewable = False
                    break
                
            return viewable and len(viewers) > 0
        
        return False
    
    def isEditable(self):
        if self._value:
            editable = True
            editors = self.getDataEditors()
            for v in self._value:
                if v is None or not isinstance(v, DiskItem) or v.isLockData() \
                   or not v.isWriteable():
                    editable = False
                    break
                
            return editable and len(editors) > 0
        
        return False

    def set_read_only(self, read_only):
        self.btnFind.setEnabled(not read_only)
        self.btnBrowse.setEnabled(not read_only)
        self.btnEdit.setEnabled(not read_only and self.isEditable())
        self.sle.setReadOnly(read_only)
        self.sle.setFrame(not read_only)
        
    def checkReadable(self):
        if self.btnShow:
            enabled = True
            
            if len(self.getViewers()) > 0:
                self.btnShow.show()
            else:
                self.btnShow.hide()
                
            self.btnShow.setEnabled(self.isViewable())
            
        if self.btnEdit:
            enabled = True
            
            if len(self.getDataEditors()) > 0:
                self.btnEdit.show()
            else:
                self.btnEdit.hide()

            self.btnEdit.setEnabled(self.isEditable())

    def showPressed(self):
        if self.btnShow.isChecked():
            self.btnShow.setEnabled(0)
            v = self.getValue()
            viewerExists = False
            try:
                for viewer in self.viewersToTry():
                    try:
                        viewer = getProcessInstance(viewer)
                        viewerExists = True
                        if self.process is not None \
                                and hasattr(viewer, 'allowed_processes'):
                            viewer.reference_process = self.process
                        brainvisa.processes.defaultContext().runInteractiveProcess(
                            self._viewerExited, viewer, v)
                        self.btnShow.setEnabled(True)
                        return

                    except Exception:
                        # Log an error then try another viewer if possible
                        brainvisa.processes.defaultContext().log(
                            _t_('Warning for %s') % _t_(viewer.name),
                          html=_t_('Viewer aborted for type=<em>ListOf(%s)</em> and '
                                   'format=<em>%s</em> value=<em>%s</em> '
                                   '(try using it interactively by '
                                   'right-clicking on the eye icon)')
                          % (six.text_type(self.parameter.type),
                             six.text_type(self.parameter.formats), six.text_type(v)),
                          icon='eye.png')
                        continue

                self.btnShow.setEnabled(False)
                self.btnShow.setChecked(False)
                raise RuntimeError(HTMLMessage(_t_('No viewer could be found for '
                                                   'type=<em>%s</em> and format=<em>%s</em>')
                                               % (six.text_type(self.parameter.type),
                                                  six.text_type(self.parameter.formats))))

            except Exception as error:
                    # transform the exception into a print message, and return.
                    # We are in a Qt slot here, raising an exception results in
                    # undefined behaviour, which happens to have changed between PyQt 5.4
                    # and PyQt 5.5
                print(error)
                import traceback
                traceback.print_exc()
        else:
            self._view = None

    def _viewerExited(self, result):
        if isinstance(result, Exception):
            showException(parent=self)
        else:
            self._view = result
        neuroProcessesGUI.mainThreadActions().push(
            self.btnShow.setEnabled, True)
        if result is None:
            neuroProcessesGUI.mainThreadActions().push(
                self.btnShow.setChecked, False)

    def close_viewer(self):
        if self._view is not None:
            self._view = None
            neuroProcessesGUI.mainThreadActions().push(
                self.btnShow.setChecked, False)
            neuroProcessesGUI.mainThreadActions().push(
                self.btnShow.setEnabled, True)

    def openViewerPressed(self):
        # Normally it is not possible to try to open viewer if none is
        # available
        viewer = self.viewersToTry()[0]
        viewer = getProcessInstance(viewer)
        v = self.getValue()
        if self.process is not None \
                and hasattr(viewer, 'allowed_processes'):
            viewer.reference_process = self.process
        neuroProcessesGUI.showProcess(viewer, v)

    def getViewers(self, update = False):
        if self._viewers is None or update:
            self.updateViewers()
        
        return self._viewers
    
    def selectedViewer(self):
        # Current index is shifted in Combo box due to the 'Default value' item
        if self.cmbViewers is not None:
            index = self.cmbViewers.currentIndex()
            if index != -1 and index > 0 and index <= len(self._viewers):
                return self._viewers[index - 1]

        return None

    def updateViewers(self):
        v = self.getValue()
        if v is None or len(v) == 0:
            format = None
            if len(self.parameter.formats) != 0:
                format = self.parameter.formats[0]
            source = (self.parameter.type, format)
        else:
            source = v

        try:
            self._viewers = brainvisa.processes.getViewers(
                source, 1, checkUpdate=False, listof=True,
                                  process=self.process, check_values=True)
        except Exception:
            self._viewers = []
            
    def updateViewersComboBox(self):
        if self.cmbViewers is not None:
            v = self.selectedViewer()
            # print('selected viewer:', v)

            # Update viewers in combo box
            self.cmbViewers.clear()
            self.cmbViewers.addItem(_t_('Default'), None)
            for viewer in self._viewers:
                self.cmbViewers.addItem(_t_(viewer.name), viewer)

            if v is not None and v in self._viewers:
                i = self._viewers.index(v)
                self.cmbViewers.setCurrentIndex(i + 1)

            # else:
                # print('Selecting default item with index', self.cmbViewers.findText(_t_('Default')))
                # Select default value
                # self.cmbViewers.setCurrentIndex(0)

            # Display or hide the viewer action in popup menu
            visible = len(self._viewers) > 1
            self.cmbViewersSeparator.setVisible(visible)
            self.actViewers.setVisible(visible)

        if len(self._viewers) == 0:
            self.btnShow.hide()

    def viewersToTry(self):
        viewer = getProcessInstance(self.selectedViewer())
        if viewer is None:
            return self._viewers
        else:
            return [viewer]


    def getDataEditors(self, update = False):
        if self._editors is None or update:
            self.updateDataEditors()
        
        return self._editors
    
    def selectedDataEditor(self):
        # Current index is shifted in Combo box due to the 'Default value' item
        if self.cmbDataEditors is not None:
            index = self.cmbDataEditors.currentIndex()
            if index != -1 and index > 0 and index <= len(self._editors):
                return self._editors[index - 1]

        return None

    def editPressed(self):
        if self.btnEdit.isChecked():
            self.btnEdit.setEnabled(0)
            v = self.getValue()
            editorExists = False
            try:
                for editor in self.dataEditorsToTry():
                    try:
                        editor = getProcessInstance(editor())
                        editorExists = True
                        if self.process is not None \
                                and hasattr(editor, 'allowed_processes'):
                            editor.reference_process = self.process
                        brainvisa.processes.defaultContext().runInteractiveProcess(
                            self._editorExited, editor, v)
                        self.btnEdit.setEnabled(True)
                        return

                    except Exception:
                        # Log an error then try another editor if possible
                        brainvisa.processes.defaultContext().log(
                            _t_('Warning for %s') % _t_(editor.name),
                          html=_t_('Editor aborted for type=<em>%s</em> and '
                                   'format=<em>%s</em> value=<em>%s</em> '
                                   '(try using it interactively by '
                                   'right-clicking on the pencil icon)')
                          % (six.text_type(v.type), six.text_type(v.format), six.text_type(v)),
                          icon='pencil.png')
                        continue

                self.btnEdit.setEnabled(False)
                self.btnEdit.setChecked(False)
                raise RuntimeError(HTMLMessage(_t_('No editor could be found for '
                                                   'type=<em>%s</em> and format=<em>%s</em>')
                                               % (six.text_type(v.type), six.text_type(v.format))))

            except Exception as error:
                    # transform the exception into a print message, and return.
                    # We are in a Qt slot here, raising an exception results in
                    # undefined behaviour, which happens to have changed between PyQt 5.4
                    # and PyQt 5.5
                print(error)
                import traceback
                traceback.print_stack()
        else:
            self._edit = None

    def _editorExited(self, result):
        if isinstance(result, Exception):
            showException(parent=self)
        else:
            self._view = result
        neuroProcessesGUI.mainThreadActions().push(
            self.btnEdit.setEnabled, True)
        if result is None:
            neuroProcessesGUI.mainThreadActions().push(
                self.btnEdit.setChecked, False)

    def close_editor(self):
        if self._edit is not None:
            self._edit = None
            neuroProcessesGUI.mainThreadActions().push(
                self.btnShow.setChecked, False)
            neuroProcessesGUI.mainThreadActions().push(
                self.btnShow.setEnabled, True)

    def openEditorPressed(self):
        editor = getProcessInstance(self.dataEditorsToTry()[0]())
        v = self.getValue()
        if self.process is not None \
                and hasattr(editor, 'allowed_processes'):
            editor.reference_process = self.process
        neuroProcessesGUI.showProcess(editor, v)

    def updateDataEditors(self):
        v = self.getValue()
        if v is None or len(v) == 0:
            format = None
            if len(self.parameter.formats) != 0:
                format = self.parameter.formats[0]
            source = (self.parameter.type, format)
        else:
            source = v

        try:
            proc = self.process
            if proc is not None:
                proc = proc()
            self._editors = brainvisa.processes.getDataEditors(
                source, 0, checkUpdate=False, listof=True,
                                process=proc)
        except Exception:
            self._editors = []

    def updateDataEditorsComboBox(self):
        if self.cmbDataEditors is not None:
            e = self.selectedDataEditor()
            # print('selected data editor:', v)

            # Update editors in combo box
            self.cmbDataEditors.clear()
            self.cmbDataEditors.addItem(_t_('Default'), None)
            for editor in self._editors:
                self.cmbDataEditors.addItem(_t_(editor.name), editor)

            if e is not None and e in self._editors:
                i = self._editors.index(e)
                self.cmbDataEditors.setCurrentIndex(i + 1)

            # else:
                # print('Selecting default item with index', self.cmbDataEditors.findText(_t_('Default')))
                # Select default value
                # self.cmbDataEditors.setCurrentIndex(0)

            # Display or hide the data editor action in popup menu
            visible = len(self._editors) > 1
            self.cmbDataEditorsSeparator.setVisible(visible)
            self.actDataEditors.setVisible(visible)

        if len(self._editors) == 0:
            self.btnEdit.hide()

    def dataEditorsToTry(self):
        editor = getProcessInstance(self.selectedDataEditor())
        if editor is None:
            return self._editors
        else:
            return [editor]

    def findPressed(self):
        dul = 0
        bul = 0
        if hasattr(self.parameter, 'databaseUserLevel'):
            dul = self.parameter.databaseUserLevel
        if hasattr(self.parameter, 'browseUserLevel'):
            bul = self.parameter.browseUserLevel
        w = self.DiskItemListSelect(
            self, six.text_type(self.objectName()), self.write,
          databaseUserLevel=dul, browseUserLevel=bul)
        try:
            w.setValue(self.getValue())
        except Exception:
            showException(parent=self)
        w.accepted[list].connect(self._newValue)
        w.findPressed()

    def findRightPressed(self):
        dul = 0
        bul = 0
        if hasattr(self.parameter, 'databaseUserLevel'):
            dul = self.parameter.databaseUserLevel
        if hasattr(self.parameter, 'browseUserLevel'):
            bul = self.parameter.browseUserLevel
        w = self.DiskItemListSelect(
            self, six.text_type(self.objectName()), self.write,
          databaseUserLevel=dul, browseUserLevel=bul)
        try:
            w.setValue(self.getValue())
        except Exception:
            showException(parent=self)
        w.show()
        w.findPressed()

    # def browsePressed( self ):
        # dul = 0
        # bul = 0
        # if hasattr( self.parameter, 'databaseUserLevel' ):
            # dul = self.parameter.databaseUserLevel
        # if hasattr( self.parameter, 'browseUserLevel' ):
            # bul = self.parameter.browseUserLevel
        # w = self.DiskItemListSelect( self, unicode(self.objectName()), self.write,
            # context = self._context, databaseUserLevel=dul, browseUserLevel=bul )
        # try:
            # w.setValue( self.getValue() )
        # except Exception:
            # showException( parent = self )
        # w.accepted.connect(self._newValue)
        # w.browsePressed()

    def browsePressed(self):
        dul = 0
        bul = 0
        if hasattr(self.parameter, 'databaseUserLevel'):
            dul = self.parameter.databaseUserLevel
        if hasattr(self.parameter, 'browseUserLevel'):
            bul = self.parameter.browseUserLevel
        w = self.DiskItemListSelect(
            self, six.text_type(self.objectName()), self.write,
          context=self._context, databaseUserLevel=dul, browseUserLevel=bul)
        try:
            w.setValue(self.getValue())
        except Exception:
            showException(parent=self)
        w.show()
        if len(self.sle.getValue()) == 0:
            # Only opens browser when no values were selected
            w.browsePressed()

    def _newTextValue(self):
        textValues = self.sle.getValue()
        if textValues is not None:
            self._newValue([self.parameter.findValue(x) for x in textValues])
        else:
            self._newValue(None)
        return None

    def _newValue(self, v):
        self._setValue(v)
        self.newValidValue.emit(six.text_type(self.objectName()), v)
        if not self.forceDefault:
            self.noDefault.emit(six.text_type(self.objectName()))

    def checkValue(self):
        self.sle.checkValue()
