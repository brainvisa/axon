# Copyright CEA and IFR 49 (2000-2005)
#
#  This software and supporting documentation were developed by
#      CEA/DSV/SHFJ and IFR 49
#      4 place du General Leclerc
#      91401 Orsay cedex
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

from backwardCompatibleQt import *
from sets import Set
import operator
from brainvisa.validation import ValidationError
qwtAvailable=True
try:
  try:
    from Qwt4 import *
  except:
    from qwt import *
except:
  qwtAvailable=False
    
def validation():
  if not qwtAvailable:
    raise ValidationError('Cannot find Qwt4 or qwt module')

if qwtAvailable:
  class ScalarFeatureCurvesPlotter( QwtPlot ):
    _colors = [ Qt.darkBlue, Qt.blue, Qt.magenta, Qt.darkRed, Qt.darkRed ]
  
    def __init__( self, parent = None, name = '' ):
      QwtPlot.__init__( self, name, parent )
      
    def setData( self, data ):
      self.clear()
      self._curves = {}
      x = data[ 'abscissa' ]
      color_index = 0
      style = QwtCurve.Lines
      
      mean = data[ 'mean' ]
      stddev = data[ 'stddev' ]
      mean_s_stddev = [ mean[ i ] - stddev[ i ] for i in xrange( len( mean ) ) ]
      mean_p_stddev = [ mean[ i ] + stddev[ i ] for i in xrange( len( mean ) ) ]
      
      for i in xrange( len( mean ) ):
        curve = self.insertCurve( 'stddev' )
        self.setCurveStyle( curve, QwtCurve.Lines )
        color = self._colors[ color_index % len( self._colors ) ]
        self.setCurvePen( curve, QPen( color, 2 ) )
        self.setCurveData( curve, [ x[i], x[i] ], [ mean_p_stddev[ i ], mean_s_stddev[ i ] ] )
      color_index += 1      
      
      curve = self.insertCurve( 'mean' )
      self.setCurveStyle( curve, style )
      color = self._colors[ color_index % len( self._colors ) ]
      self.setCurvePen( curve, QPen( color, 2 ) )
      self.setCurveData( curve, x, mean )
      color_index += 1
      
      for key in ( 'median', 'min', 'max' ):
        curve = self.insertCurve( key )
        self.setCurveStyle( curve, style )
        self._curves[ key ] = curve
        color = self._colors[ color_index % len( self._colors ) ]
        self.setCurvePen( curve, QPen( color, 2 ) )
        self.setCurveData( curve, x, data[ key ] )
        color_index += 1
      self.replot()
      
      
  class ScalarFeaturesViewer( QWidget ):
    def __init__( self, parent = None, name = None ):
      QWidget.__init__( self, parent )
      layout=QHBoxLayout(self)
      layout.setSpacing( 5 )
      layout.setMargin( 5 )
  
      self._feature = None
      self._item = None
      
      self.lbxItems = QListWidget( self )
      layout.addWidget(self.lbxItems)
      self.lbxItems.setSizePolicy( QSizePolicy( QSizePolicy.Preferred, 
                                                QSizePolicy.Expanding ) )
      self.connect( self.lbxItems, SIGNAL( 'currentRowChanged ( int ) ' ),
                    self.selectionChanged )
      self.lbxFeatures = QListWidget( self )
      layout.addWidget(self.lbxFeatures)
      self.lbxFeatures.setSizePolicy( QSizePolicy( QSizePolicy.Preferred, 
                                                  QSizePolicy.Expanding ) )
      self.connect( self.lbxFeatures, SIGNAL( 'currentRowChanged ( int ) ' ),
                    self.selectionChanged )
      self.txtFeatures = QTextBrowser( self )
      layout.addWidget(self.txtFeatures)
      self.txtFeatures.setSizePolicy( QSizePolicy( QSizePolicy.Preferred, 
                                                  QSizePolicy.Expanding ) )
      self.crvFeatures = ScalarFeatureCurvesPlotter( self )
      layout.addWidget(self.crvFeatures)
      
    def __del__( self ):
      # There is a bug when using an QeventFilter on QApplication and
      # threads. The Hide event is called after the Python object has
      # started to be destroyed (after __del__ is called). Even if the
      # event filter does not propagate the event, Python crashes.
      # The easiest workaround I have found is to hide the widget in the
      # __del__ method.
      self.hide()
  
    def setData( self, data ):
      # Check data
      if data.get( 'format' ) != 'features_1.0':
        raise RuntimeError( 'invalid data format' )
      self.data = data
      
      self.setWindowTitle( self.data[ 'content_type'  ] )
      self.lbxItems.clear()
      self.lbxFeatures.clear()
      
      features = Set()
      names = self.data.keys()
      names.sort()
      for name in names:
        if name in ( 'format', 'content_type' ): continue
        data = self.data[ name ]
        self.lbxItems.addItem( name )
        self.updateFeatures( features, data )
      features = [f for f in features]
      features.sort()
      for name in features:
        self.lbxFeatures.addItem( name )
    
    def updateFeatures(self,  features, data ):
      for name, value in data.items():
        if operator.isNumberType( value ):
          features.add( name )
        elif operator.isMappingType( value ):
          if value.get( 'mean' ) is not None:
            features.add( name )
            continue
          self.updateFeatures( features, value )
    
    def selectionChanged( self, row ):
      self._item = str(self.lbxItems.currentItem().text())
      self._feature = str(self.lbxFeatures.currentItem().text())
      
      data = self.data[ self._item ].get( self._feature )
      if data:
        text = '<html><body><h3>' + self._item + ': ' + self._feature + '</h3>'
        if operator.isMappingType( data ):
          for name, value in data.items():
            if name == '_vectors': continue
            text += '<b>' + name + ':</b> ' + str(value) + '<br>'
        else:
          text += '<b>' + self._feature + ':</b> ' + str(data) + '<br>'
        text += '</body></html>'
  
        if operator.isMappingType( data ):
          vectorData = data.get( '_vectors' )
          if vectorData is not None:
            self.crvFeatures.setData( vectorData )
          else:
            self.crvFeatures.clear()
            self.crvFeatures.replot()
      else:
        text = ''
        self.crvFeatures.clear()
        self.crvFeatures.replot()
      self.txtFeatures.setText( text )
