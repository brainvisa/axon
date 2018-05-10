# -*- coding: utf-8 -*-

from soma.qt_gui.qt_backend.QtGui import QDialog, QMessageBox, QIcon
from soma.qt_gui.qt_backend.QtGui import QVBoxLayout, QHBoxLayout, QFormLayout
from soma.qt_gui.qt_backend.QtGui import QLabel, QLineEdit, QPushButton, QPlainTextEdit
from soma.qt_gui.qt_backend.QtGui import QSplitter, QWidget, QTreeWidget, QTreeWidgetItem, QComboBox
from soma.qt_gui.qt_backend.QtCore import Qt
from soma.minf.api import readMinf, createMinfWriter
from brainvisa.processes import getProcessInstance
from brainvisa.configuration import neuroConfig
from brainvisa.processing.qt4gui.neuroProcessesGUI import showProcess

import json
import os


class SaveProcessSetupsGUI(QDialog):

    """This GUI is used when the user want to save the current configuration of one process/pipeline"""

    def __init__(self, process_view_instance):
        QDialog.__init__(self)
        self.setWindowTitle('Save process setups')
#==============================================================================
# Variables member
#==============================================================================
        self.process_view_instance = process_view_instance
        self.current_process = process_view_instance.process
        self.output_path = None
#==============================================================================
# Qt Objects
#==============================================================================
        self.process_name_label = QLabel(self.current_process.name)
        self.process_name_label.setAlignment(Qt.AlignCenter)
        self.new_name_line_edit = QLineEdit()
        self.new_name_line_edit.setPlaceholderText(
            "Enter name for your saving")
        self.new_name_line_edit.setToolTip(
            "Only alphanumeric characters and underscore allowed")
        self.description_plain_text = QPlainTextEdit()
        self.save_button = QPushButton('Save')
        self.cancel_button = QPushButton('Cancel')

#==============================================================================
# Layout Design
#==============================================================================
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        button_layout = QHBoxLayout()

        form_layout.addRow("Name : ", self.new_name_line_edit)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        main_layout.addWidget(self.process_name_label)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.description_plain_text)
        main_layout.addLayout(button_layout)
#==============================================================================
# signal connection
#==============================================================================
        self.new_name_line_edit.textChanged.connect(self._checkIfValid)
        self.save_button.clicked.connect(self._savePreference)
        self.cancel_button.clicked.connect(self.close)
#==============================================================================
# Initialisation
#==============================================================================
        self._checkIfValid(self.new_name_line_edit.text())

    def _checkIfValid(self, text):
        """only alphanumerics characters are allowed"""
        text = str(text)
        if text == '':
            self.save_button.setEnabled(False)
            self.new_name_line_edit.setStyleSheet(
                'background-color: rgb(255,255,153);')
        else:
            text_without_underscore = text.replace('_', '')
            if text_without_underscore.isalnum():
                self.save_button.setEnabled(True)
                self.new_name_line_edit.setStyleSheet('background-color: none')
            else:
                self.save_button.setEnabled(False)
                self.new_name_line_edit.setStyleSheet(
                    'background-color: rgb(255,255,153);')

    def _savePreference(self):
        """store the user preferences (bvproc) about the current process"""
        home_directory = os.path.expanduser('~')
        name = (self.new_name_line_edit.text())
        full_name = '.'.join([name, "bvproc"])
        self.output_path = os.path.join(home_directory,
                                        ".brainvisa",
                                        "setting_preferences",
                                        str(self.current_process.category),
                                        str(self.current_process.id()),
                                        full_name)
        if os.path.exists(self.output_path):
            reply = QMessageBox.question(self,
                                         '',
                                         "bvproc already exists do you wish to overwrite ?",
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if reply == QMessageBox.No:
                self.output_path = None
            else:
                self.close()
        elif not os.path.exists(os.path.dirname(self.output_path)):
            os.makedirs(os.path.dirname(self.output_path))
            self.close()
        else:
            self.close()

    def _saveDataInMinf(self):
        """process name and description will be stored in bvproc minf"""
        minf_path = self.output_path + '.minf'
        data = readMinf(minf_path)[0]
        data["process_name"] = self.current_process.name
        data["description"] = str(self.description_plain_text.toPlainText())
        writer = createMinfWriter(minf_path)
        writer.write(data)
        writer.close()

    def closeEvent(self, *args, **kwargs):
        if self.output_path is not None:
            self.process_view_instance.readUserValues()
            event = self.process_view_instance.createProcessExecutionEvent()
            self.process_view_instance.process._savedAs = self.output_path
            event.save(self.output_path)
            self._saveDataInMinf()
        return QDialog.closeEvent(self, *args, **kwargs)

#===============================================================================
#
#=========================================================================


class LoadProcessSetupsGUI(QDialog):

    """This GUI is used to load previous process/pipeline configuration (bvprov)"""

    def __init__(self):
        QDialog.__init__(self)
        self.setWindowTitle('Load process setups')
#==============================================================================
# Qt Objects
#==============================================================================
        self.process_tree = QTreeWidget()
        self.process_tree.setHeaderHidden(True)
        self.process_tree.setColumnCount(2)
        self.process_tree.setColumnHidden(1, True)
        self.process_name_combo_box = QComboBox()
        self.description_plain_text = QPlainTextEdit()
        self.description_plain_text.setEnabled(False)
        self.load_button = QPushButton('Load')
        self.delete_button = QPushButton('Delete')
        self.cancel_button = QPushButton('Cancel')
        right_widget = QWidget()
#==============================================================================
# Layout Design
#==============================================================================
        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        right_layout = QVBoxLayout(right_widget)
        button_layout = QHBoxLayout()

        splitter.addWidget(self.process_tree)
        splitter.setStretchFactor(0, 1)
        splitter.addWidget(right_widget)
        main_layout.addWidget(splitter)

        button_layout.addStretch()
        button_layout.addWidget(self.load_button)
        button_layout.addStretch()
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()

        right_layout.addWidget(self.process_name_combo_box)
        right_layout.addWidget(self.description_plain_text)
        right_layout.addLayout(button_layout)
#==============================================================================
# signal connection
#==============================================================================
        self.process_tree.itemClicked.connect(self._updateWidgetEnabled)
        self.process_tree.itemClicked.connect(self._updateComboBox)
        self.process_name_combo_box.currentIndexChanged.connect(
            self._updateDescription)
        self.load_button.clicked.connect(self._loadProcess)
        self.delete_button.clicked.connect(self._deleteProcess)
        self.cancel_button.clicked.connect(self.close)
#==============================================================================
# Initialisation
#==============================================================================
        self._buildProcessesTree()
        self._setEnableWidgets(False)

    def _updateWidgetEnabled(self, item, column):
        if item.data(0, Qt.UserRole) is not None:
            enable = True
        else:
            enable = False
        self._setEnableWidgets(enable)

    def _setEnableWidgets(self, enable):
        self.process_name_combo_box.setEnabled(enable)
        self.load_button.setEnabled(enable)
        self.delete_button.setEnabled(enable)

    def _updateComboBox(self, item, column):
        if item.data(0, Qt.UserRole) is not None:
            self.process_name_combo_box.clear()
            process_data_list = item.data(0, Qt.UserRole)
            for process_data in process_data_list:
                self.process_name_combo_box.addItem(
                    process_data[0], process_data[1])
        else:
            self.process_name_combo_box.clear()

    def _updateDescription(self, index):
        data = self.process_name_combo_box.itemData(index)
        if data is not None:
            description = data[0]
            self.description_plain_text.setPlainText(description)
        else:
            self.description_plain_text.clear()

    def _loadProcess(self):
        data = self.process_name_combo_box.itemData(
            self.process_name_combo_box.currentIndex())
        if data is not None:
            process_path = data[1]
            try:
                showProcess(getProcessInstance(process_path))
            except:
                QMessageBox.warning(
                    self, '', "Brainvisa process read error occured")

    def _deleteProcess(self):
        data = self.process_name_combo_box.itemData(
            self.process_name_combo_box.currentIndex())
        if data is not None:
            reply = QMessageBox.question(self,
                                         '',
                                         "Are you sure that you want to permanently delete this saving ?",
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if reply == QMessageBox.Yes:
                process_path = data[1]
                os.remove(process_path)
                os.remove(process_path + ".minf")
                self.process_tree.clear()
                self._buildProcessesTree()
                # clear information about process removed
                self.process_name_combo_box.clear()
                self.description_plain_text.clear()

    def _buildProcessesTree(self):
        """the all configurations saved must be merged from paths to QTreeWidget"""
        home_directory = os.path.expanduser('~')
        root_directory = os.path.join(
            home_directory, ".brainvisa", "setting_preferences")
        for root, dirs, files in os.walk(root_directory):
            for proc_file in files:
                path = os.path.join(root, proc_file)
                if path.endswith(".bvproc"):
                    directory = os.path.dirname(path)
                    basename = os.path.basename(path)
                    directory_without_root = directory.replace(
                        root_directory, '')
                    directories_names_list = directory_without_root.split('/')
                    directories_names_list.pop(0)
                    #
                    process_nickname = basename.replace(".bvproc", '')
                    minf_path = path + '.minf'
                    data = readMinf(minf_path)[0]
                    process_name = data["process_name"]
                    description = data["description"]
                    process_id = directories_names_list.pop()
                    categories_list = directories_names_list
                    #
                    top_level = categories_list.pop(0)
                    current_node = self._findOrCreateTopLevelItem(top_level)
                    self._findOrCreateChildNode(
                        current_node, categories_list, process_name, (process_nickname, (description, path)))
        self.process_tree.sortItems(1, Qt.AscendingOrder)

    def _findOrCreateTopLevelItem(self, text):
        if self.process_tree.topLevelItemCount() != 0:
            for top_item_index in range(self.process_tree.topLevelItemCount()):
                if self.process_tree.topLevelItem(top_item_index).text(0) == text:
                    return self.process_tree.topLevelItem(top_item_index)
        # if not found, we have to create it
        top_level_tree = QTreeWidgetItem(self.process_tree)
        top_level_tree.setText(0, text)
        return top_level_tree

    def _findOrCreateChildNode(self, current_node, directory_list, process_id, process_data):
        directory_found = False
        if directory_list:
            first_directory = directory_list.pop(0)
            for child_index in range(current_node.childCount()):
                if first_directory == current_node.child(child_index).text(0):
                    self._findOrCreateChildNode(
                        current_node.child(child_index), directory_list, process_id, process_data)
                    directory_found = True
            if not directory_found:
                current_node = self._addQTreeChild(
                    current_node, first_directory, None)
                self._findOrCreateChildNode(
                    current_node, directory_list, process_id, process_data)
        else:
            process_found = False
            for child_index in range(current_node.childCount()):
                if process_id == current_node.child(child_index).text(0):
                    current_data_list = current_node.child(
                        child_index).data(0, Qt.UserRole)
                    current_data_list.append(process_data)
                    current_node.child(child_index).setData(
                        0, Qt.UserRole, current_data_list)
                    process_found = True
            if not process_found:
                self._addQTreeChild(current_node, process_id, [process_data])

    def _addQTreeChild(self, parent, title, data):
        item = QTreeWidgetItem(parent, [title])
        if data is not None:
            item.setData(0, Qt.UserRole, data)
            item.setText(1, "process_" + title)
                         #only use to sort it (first directory then processes)
            item.setIcon(
                0, QIcon(os.path.join(neuroConfig.iconPath, "icon_process_0.png")))
        else:
            item.setIcon(
                0, QIcon(os.path.join(neuroConfig.iconPath, "folder.png")))
            item.setText(1, "directory_" + title)
                         #only use to sort it (first directory then processes)
        return item
