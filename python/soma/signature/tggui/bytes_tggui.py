# -*- coding: iso-8859-1 -*-

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

'''
TgGUI implementation for L{Bytes<soma.signature.api.Bytes>}
data type.

@author: Nicolas Souedet
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
from __future__ import absolute_import
import six
__docformat__ = "epytext en"

import turbogears.widgets

from soma.translation import translate as _
from soma.tggui.api import TgGUI, TgTextField
from soma.tggui import tools

#-------------------------------------------------------------------------


class Bytes_TgGUI(TgGUI):

    def __init__(self, instance):
        super(Bytes_TgGUI, self).__init__(instance)
        self._widget = None

    def editionWidget(self, value, window, parent=None, name=None, live=False):
        TgGUI.editionWidget(self, value, window, parent, name, live)

        if self._widget is not None:
            raise RuntimeError(_('editionWidget() cannot be called twice without'
                                 'a call to closeEditionWidget()'))
        self._live = live
        self._name = name
        self._widget = TgTextField(label=self._name)

        if value is not None:
            self.updateEditionWidget(self._widget, value)

        if live:
            self._widget.onAttributeChange('default', self._userModification)

        return self._widget

    def closeEditionWidget(self, editionWidget):
        pass

    def getPythonValue(self, editionWidget):
        return eval("'" + six.text_type(editionWidget.text()) + "'")

    def updateEditionWidget(self, editionWidget, value):
        editionWidget.setText(repr(value + '"')[1: -2])

    def unserializeEditionWidgetValue(self, value, notifyObject=False):
        if (self._widget is not None):
            res = self.findValueFromParams(
                value, self._widget.widgetid, self._name, default='')
            self._widget.setText(six.text_type(res))

    def _userModification(self, ):
        self.onWidgetChange.notify(self._widget)
