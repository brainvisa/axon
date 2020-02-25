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
from __future__ import print_function
from __future__ import absolute_import
from soma.qt_gui.qt_backend.QtGui import QWidget, QHBoxLayout, QPushButton
from soma.qt_gui.qt_backend.QtCore import QSize
from soma.qt_gui.qt_backend import Qt
from brainvisa.data.qtgui.neuroDataGUI import DataEditor
from brainvisa.data.qtgui.readdiskitemGUI import DiskItemEditor
from brainvisa.configuration import neuroConfig

import threading
import soma.subprocess
import sys
import six

if sys.version_info[0] >= 3:
    six.text_type = str

#----------------------------------------------------------------------------


class LabelSelectionEditor(QWidget, DataEditor):

    noDefault = Qt.Signal(six.text_type)
    newValidValue = Qt.Signal(six.text_type, object)

    def __init__(self, parameter, parent, name):
        DataEditor.__init__(self)
        QWidget.__init__(self, parent)
        self.setObjectName(name)
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.value = parameter
        self._disk = DiskItemEditor(self.value.fileDI, self, 'diskitem', 1)
        layout.addWidget(self._disk)
        self._edit = QPushButton('...', self)
        self._edit.setObjectName('edit')
        layout.addWidget(self._edit)
        self._edit.clicked.connect(self.run)
        self._labelsel = 0
        self._disk.newValidValue.connect(self.diskItemChanged)

    def setValue(self, value, default=0):
        if value is not None and value != self.value:
            self.value = value
            if not default:
                self.noDefault.emit(six.text_type(self.objectName()))
            self.newValidValue.emit(six.text_type(self.objectName()), self.value)

    def getValue(self):
        return self.value

    def run(self):
        if self._labelsel == 0:
            self._labelsel = 1
            model = self.value.value.get('model')
            nom = self.value.value.get('nomenclature')
            fsel = self.value.file
            psel = self.value.value.get('selection')
            cmd = ['AimsLabelSelector']
            if model:
                cmd += ['-m', model]
            if nom:
                cmd += ['-n', nom]
            if psel:
                cmd += ['-p', '-']
            elif fsel:
                cmd += ['-p', fsel.fullPath()]
            sys.stdout.flush()
            if neuroConfig.platform == 'windows':
                pipe = soma.subprocess.Popen(cmd, stdin=soma.subprocess.PIPE,
                                        stdout=soma.subprocess.PIPE)
            else:
                pipe = soma.subprocess.Popen(cmd, stdin=soma.subprocess.PIPE,
                                        stdout=soma.subprocess.PIPE, close_fds=True)
            self._stdout, self._stdin = pipe.stdout, pipe.stdin
            if(psel):
                # print('writing selection:', psel)
                self._stdin.write(psel)
                self._stdin.flush()
            self._thread = threading.Thread(target=self.read)
            self._thread.start()

    def read(self):
        val = self._stdout.read()
        sys.stdout.flush()
        del self._stdout
        del self._stdin
        if val:
            self.value.value['selection'] = val
            self.newValue()
        self._labelsel = 0
        del self._thread

    def newValue(self):
        self.newValidValue.emit(six.text_type(self.objectName()), self.value)
        # self.emit( PYSIGNAL('noDefault'), ( self.name(),) )

    def diskItemChanged(self, name, val):
        print('Selector: file changed:', val)
        self.value.file = val
        if val is None:
            print('temp')
        else:
            file = val.fullPath()
            print(file)
            if self.value.value.get('selection'):
                del self.value.value['selection']
