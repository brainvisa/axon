# Qt Matplotlib widget. Load this module with a try-except
import sys
from qt import *
import matplotlib
matplotlib.use('Agg') # yes, i use agg directly
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.pylab import close, figure
import gc
import weakref

_mplversion = [ int(x) for x in matplotlib.__version__.split( '.' ) ]

# Look matplotlib's backends_qtagg.py for doc
class BVFigureCanvasContent(QWidget, FigureCanvasAgg):
    def __init__( self, parent, fig = None):
#        print "\n\n\nINIT !!! \n\n\n"
        QWidget.__init__( self, parent)
        if fig == None:
            fig = figure(dpi = 60)
            # break unused cyclic ref
            del fig.canvas
            close(fig)
        FigureCanvasAgg.__init__( self, fig )
#        print "construct(gc): ", sys.getrefcount(fig)
        self.replot = True
        self.setCursor(QCursor(2))
        self.pixmap = QPixmap()

    def setFigure(self, fig):
        self.figure = fig
        #self.figure.set_canvas(self)
        # rescale the fig if necessary
        w = self.size().width()
        h = self.size().height()
        dpival = self.figure.dpi.get()
        winch = w/dpival
        hinch = h/dpival
        if (winch, hinch) != self.figure.get_size_inches():
            self.figure.set_figsize_inches( winch, hinch )
        self.replot = True
        self.repaint(False)

    def resizeEvent( self, e ):
        w = e.size().width()
        h = e.size().height()
        dpival = self.figure.dpi.get()
        winch = w/dpival
        hinch = h/dpival
        self.figure.set_figsize_inches( winch, hinch )
        self.replot = True
        self.repaint( False )

    def paintEvent( self, e ):
        p = QPainter( self )
        FigureCanvasAgg.draw( self )
        if ( self.replot ):
            global _mplversion
            if _mplversion[0] >= 1 or _mplversion[1] >= 84:
              stringBuffer = str( self.buffer_rgba(0,0) )
            else:
              stringBuffer = str( self.buffer_rgba() )
            if ( QImage.systemByteOrder() == QImage.LittleEndian ):
                stringBuffer = self.renderer._renderer.tostring_bgra()
            else:
                stringBuffer = self.renderer._renderer.tostring_argb()
            qImage = QImage( stringBuffer, self.renderer.width,
                                self.renderer.height, 32, None, 0,
                                QImage.IgnoreEndian )
            self.pixmap.convertFromImage( qImage, QPixmap.Color )
        p.drawPixmap( QPoint( 0, 0 ), self.pixmap )
        p.end()
        self.replot = False

class BVFigureCanvas(QHBox):
    """\
Simple Qt Widget matplotlib-hosting canvas.
For programmer convenience, it uses the pylab's figure manager,
which mean you should be really carefull not messing with (potentially)
other's widgets graphics. (ie. do not use pylab's close() function
unless you're sure you own the figures you're asking to close)

If you want to takeover some QWidget's area space, do something like
the following example:
    # errorMsgLabel is a QLabel displaying 'unable to load matplotlib' ;)
    f = BVSimpleFigure(self.errorMsgLabel.parent())
    self.errorMsgLabel.parent().layout().addWidget(f)
    self.errorMsgLabel.parent().layout().remove(self.errorMsgLabel)
YMMV

To use this widget with pylab's features, you have to
- either create a pylab figure and manually break the figure->canvas link,
or user this module's newFigure() function which does that
- use pylab drawing features as you wish
- remove the figure from pylab's figure manager (ie. close(fig.number)),

Shortest Example:
    from brainvisa import matplotlibwidget as mpl
    import pylab
    
    canvas = mpl.BVFigureCanvas(parent)
    self.fig = pylab.figure()
    del self.fig.canvas
    pylab.plot([1, 2, 3], [1, 2, 3])
    close(self.fig)
    
    canvas.setFigure(self.fig)
"""
    def __init__(self, parent, *args):
        QHBox.__init__(self, parent, *args)
        self.C = BVFigureCanvasContent(self, *args)
        self.setMouseTracking(True)
    def setFigure(self, fig):
        self.C.setFigure(fig)

    def mousePressEvent( self, event ):
        x = event.pos().x()
        # flipy so y=0 is bottom of canvas
        y = self.C.figure.bbox.height() - event.pos().y()
        #FigureCanvasBase.button_press_event( self, x, y, button )
        for a in self.C.figure.get_axes():
            if x is not None and y is not None and a.in_axes(x, y):
                self.inaxes = a
                try:
                    xdata, ydata = a.transData.inverse_xy_tup((x, y))
                except ValueError:
                    pass
                else:
                    self.emit(PYSIGNAL("clicked(float, float)"), (xdata, ydata))
                break

    def __del__(self):
#        print self.C
        wc = weakref.ref(self.C)
#        print sys.getrefcount(wc())
        del self.C
#        print sys.getrefcount(wc())
        #print "and now, the referrer....."
        #print len(gc.get_referrers(wc()))
        #print gc.get_referrers(wc())
        #print "...were shown"
#        print "collect", gc.collect(), "<<"
#        print sys.getrefcount(wc()), '(type:', type(wc())

def newFigure(**kargs):
    k = figure(None, **kargs)
    del k.canvas
    return k
