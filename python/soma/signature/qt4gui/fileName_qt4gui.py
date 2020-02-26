# -*- coding: utf-8 -*-
#  This software and supporting documentation are distributed by
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

from __future__ import absolute_import
import os
from soma.qt_gui.qt_backend.QtGui import QWidget, QHBoxLayout, QLineEdit, QPushButton, QIcon, QFileDialog
from soma.qt_gui import qt_backend
from soma.signature.qt4gui.unicode_qt4gui import Unicode_Qt4GUI, \
    Sequence_Unicode_Qt4GUI
from soma.qt4gui.api import TimeredQLineEdit, getPixmap
from soma.wip.application.api import somaIconsDirectory
import sys
import six

#-------------------------------------------------------------------------


class FileName_Qt4GUI(Unicode_Qt4GUI):

    def editionWidget(self, value, parent=None, name=None, live=False):
        if self._widget is not None:
            raise RuntimeError(_('editionWidget() cannot be called twice without'
                                 'a call to closeEditionWidget()'))
        self._live = live
        self._widget = QWidget(parent)
        layout = QHBoxLayout()
        if name:
            self._widget.setObjectName(name)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        if live:
            self._lineEdit = TimeredQLineEdit()
            if value is not None:
                self.updateEditionWidget(self._widget, value)
            self._lineEdit.userModification.connect(self._userModification)
        else:
            self._lineEdit = QLineEdit(self._widget)
            if value is not None:
                self.updateEditionWidget(self._widget, value)
        layout.addWidget(self._lineEdit)
        self._btnBrowse = QPushButton()
        layout.addWidget(self._btnBrowse)
        self._btnBrowse.setIcon(
            QIcon(getPixmap(os.path.join(somaIconsDirectory,
                                         'browse_file.png'))))
        self._btnBrowse.clicked.connect(self._browseClicked)
        self._widget.setLayout(layout)
        return self._widget

    def closeEditionWidget(self, editionWidget):
        if self._live:
            self._lineEdit.userModification.disconnect(self._userModification)
        self._lineEdit = None
        self._widget.close()
        self._widget.deleteLater()
        self._widget = None

    def _browseClicked(self):
        if self.dataTypeInstance.directoryOnly:
            value = qt_backend.getExistingDirectory(
                self._widget, 'Select a directory', '',
              QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog)
        elif self.dataTypeInstance.readOnly:
            # workaround a bug in PyQt ? Param 5 doesn't work; try to use
            # kwargs
            import sipconfig
            if sipconfig.Configuration().sip_version >= 0x040a00:
                value = qt_backend.getOpenFileName(
                    self._widget, 'Select a file', '', '', options=QFileDialog.DontUseNativeDialog)
            else:
                value = qt_backend.getOpenFileName(
                    self._widget, 'Select a file', '', '', 0, QFileDialog.DontUseNativeDialog)
        else:
            # workaround a bug in PyQt ? Param 5 doesn't work; try to use
            # kwargs
            import sipconfig
            if sipconfig.Configuration().sip_version >= 0x040a00:
                value = qt_backend.getSaveFileName(
                    self._widget, 'Select a file', '', '', options=QFileDialog.DontUseNativeDialog)
            else:
                value = qt_backend.getSaveFileName(
                    self._widget, 'Select a file', '', '', None, QFileDialog.DontUseNativeDialog)
        self._lineEdit.setText(six.text_type(value))

    def getPythonValue(self, editionWidget):
        v = self.dataTypeInstance.convert(six.text_type(self._lineEdit.text()))
        return self.dataTypeInstance.convert(six.text_type(self._lineEdit.text()))

    def updateEditionWidget(self, editionWidget, value):
        if self._live:
            self._lineEdit.startInternalModification()
            self._lineEdit.setText(six.text_type(value))
            self._lineEdit.stopInternalModification()
        else:
            self._lineEdit.setText(six.text_type(value))


#-------------------------------------------------------------------------
class Sequence_FileName_Qt4GUI(Sequence_Unicode_Qt4GUI):
    pass
    # def setObject( self, editionWidget, object ):
        # object[:] = list( self.valuesFromText( unicode( editionWidget.text()
        # ) ) )

    # def updateEditionWidget( self, editionWidget, value ):
        # if self._live:
            # editionWidget.startInternalModification()
            # editionWidget.setText( ' '.join( ["'" + i.replace( "'", "\\'" ) + "'" for i in value] ) )
            # editionWidget.stopInternalModification()
        # else:
            # editionWidget.setText( ' '.join( value ) )
