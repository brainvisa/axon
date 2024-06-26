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
author: Yann Cointepas
organization: NeuroSpin
license: `CeCILL version 2 <http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>`_
'''

from __future__ import absolute_import
import soma.qt_gui.qt_backend.Qt as qt
from soma.qt4gui.api import ApplicationQt4GUI, Qt4GUI
from soma.translation import translate as _
from soma.wip.application.icons import findIconFile
from soma.qtgui.api import bigIconSize
from six.moves import zip

#------------------------------------------------------------------------------


class ConfigurationWidget(qt.QWidget):
    icon_data = \
        b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d" \
      b"\x49\x48\x44\x52\x00\x00\x00\x20\x00\x00\x00\x20" \
      b"\x08\x06\x00\x00\x00\x73\x7a\x7a\xf4\x00\x00\x06" \
      b"\x1c\x49\x44\x41\x54\x58\x85\xb5\x96\x5d\x6c\x14" \
      b"\xd7\x15\xc7\x7f\x77\x76\x66\x67\xbd\xb3\xde\x5d" \
      b"\x63\x9b\x0f\x43\xc2\x26\x18\x19\x68\x2d\x4c\xd3" \
      b"\xa8\x7c\x46\x46\x49\x1a\x3b\xb6\x14\xab\x4d\x1a" \
      b"\x15\xa9\xd5\x5a\xc9\x4b\x1e\xda\x24\x0f\x69\xa3" \
      b"\xaa\x94\x12\xd4\xc8\x52\x1b\xd2\x2a\x0f\xf5\x03" \
      b"\xd2\xba\x42\x79\x00\x11\x02\xad\x94\x44\x69\x53" \
      b"\xd3\x10\xd2\x28\xe1\x63\x85\xd2\xc4\x04\x51\x7b" \
      b"\xc1\xc6\x35\xb6\xf1\xda\xbb\xf6\xce\xce\xdc\x99" \
      b"\xdb\x07\xc7\x80\x61\x01\x19\x87\xbf\x74\xa4\xd1" \
      b"\x3d\x33\xf7\xfc\xee\xb9\xf7\x9c\xb9\x82\x12\x7a" \
      b"\xef\xbd\x7f\xc7\x85\x10\xaf\x0b\x41\x23\x88\xc4" \
      b"\x82\x05\x51\x00\x2e\x5f\x9e\x00\x54\x9f\x52\x1c" \
      b"\x52\x4a\xfd\xa9\xa9\x69\x43\x5f\xa9\xef\xe7\x22" \
      b"\x51\x6a\xf0\xdd\x77\x3f\x4e\xf8\xbe\x7f\x2a\x91" \
      b"\xa8\x89\xaf\x59\x73\xdf\x2c\x5f\x2e\x37\x49\x6f" \
      b"\xef\x20\xfd\xfd\x43\x28\xa5\x76\xb6\xb6\x6e\xf9" \
      b"\xed\x7c\x21\x4a\xea\xf0\xe1\x7f\x35\x1c\x3a\x74" \
      b"\x64\x2c\x93\x19\x54\xa5\x94\xcd\xe6\x54\x77\xf7" \
      b"\x71\xf5\xf6\xdb\xdd\xa9\xbb\x02\x00\x70\xe0\xc0" \
      b"\x07\x0d\xfb\xf7\xff\x63\xac\xb7\x77\xa0\x24\x84" \
      b"\xe3\xb8\xea\xfd\xf7\x3f\x51\xfb\xf6\xfd\xfd\xf5" \
      b"\x3b\x8d\xa1\xdd\xca\xf9\xe4\x93\x0f\xa7\xa5\x94" \
      b"\x5b\x8f\x1d\x3b\x9d\x3d\x77\xae\xff\x06\xbf\x61" \
      b"\xe8\x6c\xd9\xb2\x0e\x21\x78\x61\xef\xde\x77\x1a" \
      b"\xbf\x71\x00\x80\x6d\xdb\x9a\xd2\x52\x7a\x5b\x8f" \
      b"\x1e\x4d\x67\xbf\xfa\xea\x3c\x4a\xa9\x59\x7e\xd3" \
      b"\x34\xa8\xaf\xaf\xc5\x75\xe5\x8e\x3b\x02\xe8\xec" \
      b"\x3c\xf8\x42\x67\xe7\xc1\xe4\xad\x5e\x4a\x26\x5b" \
      b"\xd3\x52\x7a\x5b\x8f\x1c\x39\xc9\xd0\xd0\xe5\x59" \
      b"\x3e\x21\x04\x35\x35\xd5\x08\x21\x1a\x3b\x3b\x0f" \
      b"\x26\xe6\x0c\x20\xa5\x7c\x3e\x10\x10\xa9\x37\xde" \
      b"\xd8\x77\x4b\x08\xdb\x2e\x3e\x2f\xc4\x74\xda\x7d" \
      b"\xdf\x9f\x65\x86\xa1\x53\x51\x51\x8e\x94\xb2\x71" \
      b"\xce\x00\xae\x2b\x13\x2d\x2d\x9b\xd1\x34\x2d\xf5" \
      b"\xda\x6b\x6f\x96\x84\xd8\xbd\xfb\xcd\x54\x34\x6a" \
      b"\x25\x1f\x7b\x6c\x3d\x91\x48\x18\xd7\xf5\x66\x99" \
      b"\xef\xfb\x58\x56\x19\xae\x2b\x13\x73\x06\x88\x46" \
      b"\x2d\x62\xb1\x08\xd3\x10\x22\xd5\xd1\xd1\x35\x0b" \
      b"\xa2\xa3\xa3\x2b\x15\x8d\x5a\xc9\xa6\xa6\x0d\x54" \
      b"\x56\xc6\x90\x52\xde\x60\xae\x2b\x71\x1c\x17\xc7" \
      b"\x71\xe7\x1a\x1f\x2d\x9f\x2f\x20\xa5\x24\x1e\x8f" \
      b"\xd0\xda\x3a\x9d\x89\x57\x5e\xd9\x93\x04\xd8\xb5" \
      b"\x6b\xcf\xd7\xc1\x37\x62\x9a\x41\xa4\xf4\x4a\x9a" \
      b"\xeb\x4a\x8a\x45\x17\xc7\x91\x73\x07\x18\x1d\x1d" \
      b"\xc7\x71\x24\x52\x7a\x54\x54\x44\x69\x69\xd9\x4c" \
      b"\x20\xa0\xa5\xb6\x6f\xef\xec\x8e\x46\xad\x64\x73" \
      b"\xf3\x46\x42\xa1\xd2\xc1\x67\xb6\x20\x9f\x2f\x30" \
      b"\x30\x70\x09\xd7\x95\xe9\x39\x03\xb8\xae\x4c\xf7" \
      b"\xf4\xf4\xe1\xba\xd3\xe9\xac\xac\x8c\xf2\xf8\xe3" \
      b"\x9b\x58\xba\xb4\xba\x71\x3a\xb8\x89\xeb\xca\x92" \
      b"\x36\xb3\x05\xb6\x5d\xe4\xe2\xc5\x11\x3c\xcf\x3b" \
      b"\x32\x67\x00\xc7\x71\xff\xd2\xd3\xd3\x87\x6d\x3b" \
      b"\x57\x56\x54\x55\x15\xa7\xa9\x69\x03\x65\x65\xa1" \
      b"\x9b\xa6\x7d\xc6\xc6\xc7\xf3\x04\x83\x06\xb5\xb5" \
      b"\xcb\x28\x14\x8a\x73\xee\x88\xba\x94\x5e\xd7\xe9" \
      b"\xd3\xe7\x76\x2c\x5f\xbe\x24\xbe\x62\xc5\x32\x34" \
      b"\xed\xea\xff\x49\xca\xd2\x7b\x3a\xd3\x8b\xb2\xd9" \
      b"\x1c\xfd\xfd\x43\x04\x83\x06\x9b\x36\xad\x45\x78" \
      b"\x53\xc9\xcf\x76\xaf\x6f\x8b\x05\x73\x71\x5f\xd1" \
      b"\xbe\xea\x67\xff\xe9\xba\x1d\x80\x00\x78\xee\xb9" \
      b"\x8e\xa4\x61\xe8\xa9\xa7\x9f\x7e\x84\xaa\xaa\x38" \
      b"\x42\xdc\xb6\x41\x92\xcf\x4f\x31\x32\x92\x45\xd7" \
      b"\x03\xe8\x7a\x00\x43\x14\x89\x9e\x7d\x95\x50\xf0" \
      b"\x3c\xf1\xd5\x21\x06\x8f\xe6\x51\x8a\xf6\xfa\x17" \
      b"\x4b\x43\x28\xa5\xe2\x42\x88\xec\x95\xe5\x3e\xf3" \
      b"\xcc\xae\x94\x65\x95\x25\x1f\x7a\x68\x1d\x89\x44" \
      b"\x0d\xe1\x70\xa8\xd4\x67\x00\x57\x52\x1f\x08\x04" \
      b"\xd0\x75\x8d\x80\xb2\x11\x27\x7f\x83\x15\xba\xc0" \
      b"\xc2\x15\x12\x67\x30\x8f\xb1\x72\x09\x99\x7f\x4e" \
      b"\x43\x7c\xe7\xa5\x2f\x6e\x9a\x89\xc0\xcc\xc3\xa9" \
      b"\x53\xdd\x87\xeb\xea\x36\x8c\xf7\xf4\x64\x9a\x26" \
      b"\x26\xf2\xd8\x76\x11\xd7\xf5\x90\x52\x52\x2c\x3a" \
      b"\xe4\xf3\x53\x0c\x0d\x8d\x62\xdb\x0e\x65\x65\x21" \
      b"\x0c\x43\xc7\x34\x83\x98\x01\x17\xf9\xe9\x76\x4c" \
      b"\xe3\x3c\x35\xb5\x2e\x53\x47\x2f\x10\x9e\x98\xc4" \
      b"\x13\x8a\xd8\xb7\x63\x8c\xf6\xca\xb6\x67\x1f\xae" \
      b"\xce\xec\xf9\x60\xb8\x64\x85\xdc\x70\x21\xd9\xb6" \
      b"\xed\xd7\x09\xa5\xd4\x0e\xa5\x54\xb2\xbc\x3c\x4c" \
      b"\x24\x12\xc6\x34\x0d\x72\xb9\x29\x6c\xdb\x61\x72" \
      b"\xb2\x40\x73\xf3\x46\xea\xeb\x57\x62\x99\x1e\xd9" \
      b"\xee\x5f\x62\x6a\xbd\x24\x56\xda\xd8\xa7\x87\xa9" \
      b"\xb6\x7c\x34\x01\x93\x8e\xc0\x59\x16\x47\x56\x56" \
      b"\x72\xf6\xc3\x22\x4a\xd1\xbe\x79\xfb\x8d\x99\x28" \
      b"\x79\x23\x9a\xd1\x53\x4f\xbd\xdc\x08\x34\x00\x71" \
      b"\xa0\xef\x6b\xcb\x02\xdd\x4d\x8f\xac\x8d\xaf\xcc" \
      b"\xef\x25\x6c\x64\xb8\xaf\x26\x87\xba\x94\xa7\x22" \
      b"\x22\xd0\xc4\xd5\x29\x0b\x8e\xc2\xad\xb6\x28\x84" \
      b"\x2b\x38\xf3\x91\x8b\x52\xb4\x37\xee\x9c\x0d\x71" \
      b"\x4b\x80\x9b\xe9\xe7\x3f\x7d\xb6\x71\xe3\xc2\xcf" \
      b"\xbb\x13\x4b\x26\xa8\xbb\x3f\x0f\xe3\x05\x62\x11" \
      b"\x03\x71\xfd\x6c\x02\xec\xa2\x8f\x8c\x06\xc9\x89" \
      b"\x28\x5f\x7c\xec\xa1\x14\xed\x8f\xfe\xee\xcb\x2b" \
      b"\x10\xb7\x3f\xee\x25\xd4\xbc\xf4\x58\x36\xa6\x8f" \
      b"\xb3\xe8\x5e\x08\x95\x09\x62\x8b\x2c\x44\x24\x08" \
      b"\xd6\x75\x16\x0e\x12\xaa\x08\x11\x94\x8a\xb8\x96" \
      b"\x63\xd5\x83\x02\xe9\x91\x7a\xe7\xe5\xd5\xc9\x79" \
      b"\x65\x00\xe0\xaf\x2f\xad\x4e\x02\xa9\x86\xef\x29" \
      b"\xee\x59\xe2\x83\x5f\x62\x2a\x5f\x81\xe7\x83\x52" \
      b"\xf8\x9e\x8f\x30\x03\xf4\x0f\x05\x48\x7f\xa6\xa1" \
      b"\x14\xed\x4f\xfc\xe1\xcb\xae\x3b\x06\x00\x78\xeb" \
      b"\xc5\x69\x88\x07\xbe\x2b\x59\x5e\xab\x83\xae\x5f" \
      b"\x75\x7a\x3e\x8c\x4d\xce\x54\xee\x55\x09\xc8\x0c" \
      b"\x1b\x9c\x38\xa1\xe3\xfb\xac\x0b\x30\x0f\xed\xff" \
      b"\x64\x24\xfd\x83\x07\xab\x33\xfd\xfd\xa2\xcd\x32" \
      b"\x5c\x2a\x16\x05\xc0\x0a\x41\x50\x87\xb1\x29\x98" \
      b"\x72\xc1\xf5\xe1\x62\x16\x2e\xe5\x60\x34\x0f\x61" \
      b"\x93\x78\xb9\xcf\x84\xad\x71\x79\x4c\x2c\x9e\x17" \
      b"\x00\xc0\x81\x4f\x47\xd2\x4f\x3c\x50\x95\xb9\x30" \
      b"\x10\x68\xb3\x7c\x9b\x05\x8b\x75\x88\x96\x41\xef" \
      b"\x08\x48\x1f\x1c\x09\xe3\x05\xb0\x4c\x30\x0d\x18" \
      b"\x9e\x00\xcb\xc4\x8a\x28\xce\xf4\x1a\xab\xee\xe8" \
      b"\x10\x5e\xaf\x9f\xfc\xb9\xa7\xcb\x95\xb4\x7f\x78" \
      b"\xdc\xe4\xec\x47\x59\x98\x98\x82\x82\x3b\x1d\x7c" \
      b"\x61\x39\x4c\xd8\x90\x2f\x82\xae\x81\x2d\xc1\x91" \
      b"\x54\x84\x1c\x5c\x79\x4d\x27\x9c\xaf\x0e\x9f\x1c" \
      b"\x49\xb7\xac\xad\xca\xf4\x0e\x1a\x6d\x91\x7c\x96" \
      b"\xaa\x72\x0f\x1c\x0f\xee\x59\x00\x23\x79\xc8\x15" \
      b"\x40\x13\x60\xea\x60\x04\x70\x1c\x38\x79\x2e\xfc" \
      b"\xcd\x01\x00\xfc\x2d\x3d\x92\x6e\xae\xaf\xca\xfc" \
      b"\xf7\x7f\xc1\xb6\x72\xdd\xa1\xba\xac\x08\x53\x45" \
      b"\x58\x7f\x3f\x84\x8c\xe9\xe0\xae\x07\xf8\x7c\x9e" \
      b"\x09\xd1\x37\x6c\xf6\xcd\xab\x0a\x6e\xa6\x3f\xfe" \
      b"\xb8\x2e\xa9\x20\xf5\xfd\x55\x59\xd6\x2c\xbc\xa6" \
      b"\x12\x04\xa0\xc1\xf0\x64\x90\x03\xa7\x2a\x29\x4a" \
      b"\xad\xfd\xae\x00\x00\xfc\xfe\x47\x75\x49\xa5\x48" \
      b"\x7d\x6b\xf1\x24\x9b\xee\x1d\x27\x16\x92\x14\xa5" \
      b"\xc6\xf1\x81\x72\x4e\x0c\x94\x53\xf4\xb4\xae\x5f" \
      b"\xec\x3f\x73\xf7\x00\x00\x5e\xfd\x61\x5d\x83\x52" \
      b"\xec\x00\xda\xae\x19\xee\x13\x82\x9d\xbf\x7a\xeb" \
      b"\x4c\x17\xc0\xff\x01\xf5\xec\x44\x62\x6c\x55\xd6" \
      b"\x89\x00\x00\x00\x00\x49\x45\x4e\x44\xae\x42\x60" \
      b"\x82"

    def __init__(self, parent=None, name=None, flags=qt.Qt.WindowType(0)):
        super(ConfigurationWidget, self).__init__(parent, flags)
        if name:
            self.setObjectName(name)
        icon = qt.QPixmap()
        icon.loadFromData(self.icon_data, "PNG")
        self.setWindowTitle(_('Configuration'))

        self.setWindowIcon(qt.QIcon(icon))

        ConfigurationLayout = qt.QVBoxLayout()
        ConfigurationLayout.setContentsMargins(0, 0, 0, 0)
        ConfigurationLayout.setSpacing(6)
        self.setLayout(ConfigurationLayout)

        self.splitter = qt.QSplitter()
        self.splitter.setOrientation(qt.Qt.Horizontal)

        self.lbxPanels = qt.QListWidget(self.splitter)
        self.lbxPanels.setFrameShape(qt.QFrame.NoFrame)
        self.lbxPanels.setFrameShadow(qt.QFrame.Plain)
        self.lbxPanels.setIconSize(qt.QSize(*bigIconSize))
        # self.lbxPanels.setContentsMargins(6, 6, 6, 6)
        self.lbxPanels.setResizeMode(qt.QListView.Adjust)

        self.scv = qt.QScrollArea(self.splitter)
        # self.scv.setResizePolicy( qt.QScrollView.AutoOneFit )
        self.scv.setWidgetResizable(True)
        self.scv.setFrameStyle(qt.QFrame.NoFrame)
        # self.scv.setContentsMargins(0, 0, 0, 0)
        self.wstPanels = qt.QStackedWidget()
        self.scv.setWidget(self.wstPanels)

        ConfigurationLayout.addWidget(self.splitter)

    def sizeHint(self):
        lbxSize = self.lbxPanels.sizeHint()
        wstSize = self.wstPanels.sizeHint()
        return qt.QSize(lbxSize.width() + self.splitter.handleWidth() + wstSize.width(), wstSize.height())
        # size = qt.QWidget.sizeHint( self )
        # return qt.QSize(size.width()*1.1,size.height()*1.3)


#------------------------------------------------------------------------------
class Configuration_Qt4GUI(Qt4GUI):

    def editionWidget(self, object, parent=None, name=None, live=False):
        self.__widget = ConfigurationWidget(parent=parent, name=name)
        self.__widget.wstPanels.removeWidget(
            self.__widget.wstPanels.widget(0))
        self.__panels = []
        count = 0
        it = iter(object.signature)
        next(it)
        for key in it:
            group = getattr(object, key)
            qtgui = ApplicationQt4GUI().instanceQt4GUI(group)
            widget = qtgui.editionWidget(group,
                                         parent=self.__widget.wstPanels,
                                         live=live)
            if group.icon:
                icon = findIconFile(group.icon)
                if icon:
                    self.__widget.lbxPanels.addItem(
                        qt.QListWidgetItem(qt.QIcon(icon), group.label))
                else:
                    self.__widget.lbxPanels.addItem(
                        qt.QListWidgetItem(self.__widget.windowIcon(), group.label))
            else:
                self.__widget.lbxPanels.addItem(group.label)
            self.__widget.wstPanels.addWidget(widget)
            self.__panels.append((qtgui, widget))
            count += 1
        self.__widget.lbxPanels.currentRowChanged.connect(
            self.__widget.wstPanels.setCurrentIndex)
        self.__widget.lbxPanels.setCurrentRow(0)
        return self.__widget

    def closeEditionWidget(self, editionWidget):
        for qtgui, widget in self.__panels:
            qtgui.closeEditionWidget(widget)
        self.__panels = []
        self.__widget.close()
        self.__widget = None

    def setObject(self, editionWidget, object):
        itSignature = iter(object.signature)
        next(itSignature)
        for attribute, qtgui_widget in zip(itSignature, self.__panels):
            qtgui, widget = qtgui_widget
            qtgui.setObject(widget, getattr(object, attribute))

    def updateEditionWidget(self, editionWidget, object):
        itSignature = iter(object.signature)
        next(itSignature)
        for attribute, qtgui_widget in zip(itSignature, self.__panels):
            qtgui, widget = qtgui_widget
            gtgui.updateEditionWidget(widget, getattr(object, attribute))
