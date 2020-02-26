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
import os.path
import base64

from soma.wip.application.api import Application
from soma.translation import translate as _
from soma.httpupload import resourcemanager
from soma.tggui.api import TgGUI, TgUploadMultipleFiles
from soma.signature.tggui.unicode_tggui import Unicode_TgGUI, Sequence_Unicode_TgGUI
from soma.tggui import tools
import six


uploaddirectory = resourcemanager.getDirectory('httpupload.dirbasefileoutput')

#-------------------------------------------------------------------------


class FileName_TgGUI(Unicode_TgGUI):

    def editionWidget(self, value, window, parent=None, name=None, live=False):
        TgGUI.editionWidget(self, value, window, parent, name, live)

        if self._widget is not None:
            raise RuntimeError(_('editionWidget() cannot be called twice without'
                                 'a call to closeEditionWidget()'))
        self._name = name
        self._live = live
        self._widget = TgUploadMultipleFiles(label=self._name)

        if value is not None:
            self.updateEditionWidget(self._widget, value)

        if live:
            self._widget.onAttributeChange('default', self._userModification)

        return self._widget

    def getPythonValue(self, editionWidget):
        foundValue = self.dataTypeInstance.convert(
            six.text_type(editionWidget.default))
        filepath = os.path.join(
            uploaddirectory, base64.b64decode(foundValue))
        foundValue = Application().temporary.createSelfDestroyed(foundValue)
        return foundValue

#-------------------------------------------------------------------------


class Sequence_FileName_TgGUI(FileName_TgGUI):

    def setObject(self, editionWidget, object):
        values = list()
        for value in Sequence_Unicode_TgGUI.valuesFromText(six.text_type(editionWidget.default)):
            filepath = os.path.join(uploaddirectory, base64.b64decode(value))
            values.append(
                Application().temporary.createSelfDestroyed(filepath))
        object[:] = values

    def updateEditionWidget(self, editionWidget, value):
        if self._live:
            editionWidget.startInternalModification()
            editionWidget.value = ' '.join(["'" + i + "'" for i in value])
            editionWidget.stopInternalModification()
        else:
            editionWidget.value = ' '.join(["'" + i + "'" for i in value])
