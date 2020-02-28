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
from brainvisa.processing.qtgui.backwardCompatibleQt import *

import operator
from brainvisa.validation import ValidationError
import six
import numbers
import collections
qwtAvailable = True
try:
    try:
        from soma.qt_gui.qt_backend.Qwt5 import *
    except Exception as e1:
        from qwt import *
except Exception as e:
    qwtAvailable = False


def validation():
    if not qwtAvailable:
        raise ValidationError(
            'Cannot find soma.qt_gui.qt_backend.Qwt5 or qwt module')

if qwtAvailable:
    class ScalarFeatureCurvesPlotter(QwtPlot):
        _colors = [Qt.darkBlue, Qt.blue, Qt.magenta, Qt.darkRed, Qt.darkRed]

        def __init__(self, parent=None, name=''):
            QwtPlot.__init__(self, parent)
            if name:
                self.setObjectName(name)
            grid = QwtPlotGrid()
            pen = QPen()
            pen.setStyle(Qt.DashLine)
            grid.setPen(pen)
            grid.attach(self)

        def setData(self, data):
            self.clear()
            self._curves = {}
            x = data['abscissa']
            color_index = 0
            style = QwtPlotCurve.Lines

            mean = data['mean']
            stddev = data['stddev']
            mean_s_stddev = [mean[i] - stddev[i]
                             for i in six.moves.xrange(len(mean))]
            mean_p_stddev = [mean[i] + stddev[i]
                             for i in six.moves.xrange(len(mean))]

            for i in six.moves.xrange(len(mean)):
                curve = QwtPlotCurve('stddev')
                curve.setStyle(style)
                color = self._colors[color_index % len(self._colors)]
                pen = QPen(color)
                pen.setWidth(2)
                curve.setPen(pen)
                curve.setData(
                    [x[i], x[i]], [mean_p_stddev[i], mean_s_stddev[i]])
                curve.attach(self)
            color_index += 1

            curve = QwtPlotCurve('mean')
            curve.setStyle(style)
            color = self._colors[color_index % len(self._colors)]
            pen = QPen(color)
            pen.setWidth(2)
            curve.setPen(pen)
            curve.setData(x, mean)
            curve.attach(self)
            color_index += 1

            for key in ('median', 'min', 'max'):
                curve = QwtPlotCurve(key)
                curve.setStyle(style)
                self._curves[key] = curve
                color = self._colors[color_index % len(self._colors)]
                pen = QPen(color)
                pen.setWidth(2)
                curve.setPen(pen)
                curve.setData(x, data[key])
                curve.attach(self)
                color_index += 1

            self.replot()

    class ScalarFeaturesViewer(QWidget):

        def __init__(self, parent=None, name=None):
            QWidget.__init__(self, parent)
            layout = QHBoxLayout(self)
            layout.setSpacing(5)
            layout.setContentsMargins(5, 5, 5, 5)

            self._feature = None
            self._item = None

            self.lbxItems = QListWidget(self)
            layout.addWidget(self.lbxItems)
            self.lbxItems.setSizePolicy(QSizePolicy(QSizePolicy.Preferred,
                                                    QSizePolicy.Expanding))
            self.lbxItems.currentRowChanged.connect(self.selectionChanged)
            self.lbxFeatures = QListWidget(self)
            layout.addWidget(self.lbxFeatures)
            self.lbxFeatures.setSizePolicy(QSizePolicy(QSizePolicy.Preferred,
                                                       QSizePolicy.Expanding))
            self.lbxFeatures.currentRowChanged.connect(self.selectionChanged)
            self.txtFeatures = QTextEdit(self)
            self.txtFeatures.setReadOnly(True)
            self.txtFeatures.setAcceptRichText(True)
            layout.addWidget(self.txtFeatures)
            self.txtFeatures.setSizePolicy(QSizePolicy(QSizePolicy.Preferred,
                                                       QSizePolicy.Expanding))
            self.crvFeatures = ScalarFeatureCurvesPlotter(self)
            layout.addWidget(self.crvFeatures)

        def __del__(self):
            # There is a bug when using an QeventFilter on QApplication and
            # threads. The Hide event is called after the Python object has
            # started to be destroyed (after __del__ is called). Even if the
            # event filter does not propagate the event, Python crashes.
            # The easiest workaround I have found is to hide the widget in the
            # __del__ method.
            self.hide()

        def setData(self, data):
            # Check data
            if data.get('format') != 'features_1.0':
                raise RuntimeError('invalid data format')
            self.data = data

            self.setWindowTitle(self.data['content_type'])
            self.lbxItems.clear()
            self.lbxFeatures.clear()

            features = set()
            names = list(self.data.keys())
            names.sort()
            for name in names:
                if name in ('format', 'content_type'):
                    continue
                data = self.data[name]
                self.lbxItems.addItem(name)
                self.updateFeatures(features, data)
            features = [f for f in features]
            features.sort()
            for name in features:
                self.lbxFeatures.addItem(name)

        def updateFeatures(self,  features, data):
            for name, value in data.items():
                if isinstance(value, numbers.Number):
                    features.add(name)
                elif isinstance(value, collections.Mapping):
                    if value.get('mean') is not None:
                        features.add(name)
                        continue
                    self.updateFeatures(features, value)

        def selectionChanged(self, row):
            currentItem = self.lbxItems.currentItem()
            currentFeature = self.lbxFeatures.currentItem()
            if currentItem:
                self._item = str(currentItem.text())
            else:
                self._item = ""
            if currentFeature:
                self._feature = str(currentFeature.text())
            else:
                self._feature = ""

            data = self.data[self._item].get(self._feature)
            if data:
                text = '<html><body><h3>' + self._item + \
                    ': ' + self._feature + '</h3>'
                if isinstance(data, collections.Mapping):
                    for name, value in data.items():
                        if name == '_vectors':
                            continue
                        text += '<b>' + name + ':</b> ' + str(value) + '<br>'
                else:
                    text += '<b>' + self._feature + \
                        ':</b> ' + str(data) + '<br>'
                text += '</body></html>'
                if isinstance(data, collections.Mapping):
                    vectorData = data.get('_vectors')
                    if vectorData is not None:
                        self.crvFeatures.setData(vectorData)
                    else:
                        self.crvFeatures.clear()
                        self.crvFeatures.replot()
                else:
                    self.crvFeatures.clear()
                    self.crvFeatures.replot()
            else:
                text = ''
                self.crvFeatures.clear()
                self.crvFeatures.replot()
            self.txtFeatures.setHtml(text)
