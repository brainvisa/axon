#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCIL license version 2 under
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
# knowledge of the CeCILL version 2 license and that you accept its terms.

from qwt import *
from backwardCompatibleQt import *

class MultiPlot( QVBox ):
  '''A PyQt widget to draw several curves aligned on x axis'''
  
  _colors = [ Qt.darkBlue, Qt.darkGreen, Qt.darkMagenta, Qt.darkYellow,
             Qt.darkRed, Qt.darkCyan ]
             
  def __init__( self, parent=None, name=None ):
    QVBox.__init__( self, parent, name )
    self._plots = []
    self._scale = None
    self.setMargin( 5 )
    
  def addPlot( self, name, color= None ):
    if color is None:
      color = self._colors[ len( self._plots ) % len( self._colors ) ]
    p = QwtPlot( self )
    p.setMinimumHeight( 30 )
    p.setTitle( name )
    c = p.insertCurve( name )
    p.setCurveStyle( c, QwtCurve.Steps, 0 )
    pen = QPen( color, 2 )
    p.setCurvePen( c, pen )
    brush = QBrush( Qt.Dense4Pattern )
    brush.setColor( color.light() )
    p.setCurveBrush( c, brush )
    result = len( self._plots )
    self._plots.append( ( p, c ) )
    return result

  def setData( self, index, x, y ):
    p, c = self._plots[ index ]
    p.setCurveData( c, x, y )
    p.replot()
    if self._scale is None:
      self._scale = ( p.axisScaleDraw( QwtPlot.xBottom ).d1(),
                      p.axisScaleDraw( QwtPlot.xBottom ).d2() )
    else:
      low = p.axisScaleDraw( QwtPlot.xBottom ).d1()
      high = p.axisScaleDraw( QwtPlot.xBottom ).d2()
      if low < self._scale[0] or high > self._scale[1]:
        self._scale = ( min( low,self._scale[0] ),max( high, self._scale[1] ) )
        for p, c in self._plots:
          p.setAxisScale( QwtPlot.xBottom, self._scale[0], self._scale[1] )
          p.replot()
      elif low != self._scale[0] or high != self._scale[1]:
        p.setAxisScale( QwtPlot.xBottom, self._scale[0], self._scale[1] )
        p.replot()
