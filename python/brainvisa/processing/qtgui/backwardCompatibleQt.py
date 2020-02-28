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

from __future__ import absolute_import
import os
import sys
USES_PYSIDE = False
from soma.qt_gui.qt_backend.QtCore import *
from soma.qt_gui.qt_backend.QtGui import *
from soma.qt_gui.qt_backend import QtCore
# PyQt / PySide compatibility for signals/slots
if hasattr(QtCore, 'pyqtSignal'):
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
    QtCore.Property = QtCore.pyqtProperty
else:
    USES_PYSIDE = True


# In BrainVISA, we try to use the latest version of PyQt. Unfortunately
# some attributes name are changed between PyQt versions. When such a
# problem is detected, we replace the old attribute name by the new one
# in all BrainVISA and here, we define the new attribute for older PyQt
# versions.

# Qt.WStyle_Dialog has been replaced by Qt.WType_Dialog in PyQt 3.0
if not hasattr(Qt, 'WType_Dialog'):
    if hasattr(Qt, 'WStyle_Dialog'):
        Qt.WType_Dialog = Qt.WStyle_Dialog
    if hasattr(Qt, 'Dialog'):
        Qt.WType_Dialog = Qt.Dialog

# Qt.WType_Modal has been replaced by Qt.WShowModal in PyQt 3.0
if not hasattr(Qt, 'WShowModal'):
    if hasattr(Qt, 'WType_Modal'):
        Qt.WShowModal = Qt.WType_Modal

# QWidget.setBackgroundColor has been removed in PyQt 3.0.
# We use QWidget.setPaletteBackgroundColor instead.
if not hasattr(QWidget, 'setPaletteBackgroundColor'):
    if hasattr(QWidget, 'setBackgroundColor'):
        def setPaletteBackgroundColor(self, color):
            self.setBackgroundColor(color)
        QWidget.setPaletteBackgroundColor = setPaletteBackgroundColor

# QComboBox.setCurrentText does not exists before Qt 3.0
if not hasattr(QComboBox, 'setCurrentText'):
    def setCurrentText(self, text):
        return self.lineEdit().setText(text)
    QComboBox.setCurrentText = setCurrentText

# set plugins path for binary packages (needed on MacOSX/Fink version of Qt)


def setPluginPath():
    if sys.platform[:6] != 'darwin':
        return  # not needed on other platforms right now
    try:
        from soma.config import BRAINVISA_SHARE
        shared = BRAINVISA_SHARE
    except ImportError:
        path = os.getenv('PATH').split(os.pathsep)
        for p in path:
            if p.endswith('/bin') or p.endswith('\\bin'):
                p = p[:len(p) - 4]
            elif p.endswith( '/bin/commands-links' ) \
                    or p.endswith('\\bin\\commands-links'):
                p = p[:len(p) - 19]
            p = os.path.join(p, 'share')
            if os.path.isdir(p):
                shared = p
                break
    if shared is not None:
        p = os.path.normpath(
            os.path.join(shared, '..', 'lib', 'qt3-plugins'))
        QApplication.addLibraryPath(p)

setPluginPath()
