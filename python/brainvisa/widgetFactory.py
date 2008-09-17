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

import os, errno
import qt, qtui


class UIWidgetFactory:
  def __init__( self, uiFile,
                translationFile = None,
                ignoreInvalidCustomWidgets = False ):
    if not os.path.exists( uiFile ):
      raise IOError( errno.ENOENT, os.strerror( errno.ENOENT )+': '+ `uiFile` )
    self.uiFile = uiFile

    self.translationFile = translationFile
    if translationFile is None:
      self.translator = None
    else:
      if not os.path.exists( translationFile ):
        raise IOError( errno.ENOENT, 
                       os.strerror( errno.ENOENT )+': '+ `translationFile` )
      self.translator = qt.QTranslator()
      if not self.translator.load( translationFile ):
        raise RuntimeError( 'Invalid translation file: ' + `translationFile` )

    self.ignoreInvalidCustomWidgets = ignoreInvalidCustomWidgets

  def __call__( self, parent, name ):
    if self.translator is not None:
     qt.qApp.installTranslator( self.translator )
    try:
      mainWidget = qtui.QWidgetFactory.create( self.uiFile, None, parent, name )
    finally:
      if self.translator is not None:
       qt.qApp.removeTranslator( self.translator )
    if mainWidget is None:
      raise RuntimeError( 'Invalid qtui file:' + `self.uiFile` )
    for childWidget in mainWidget.queryList( 'QWidget', None ):
      qwidgetFactory = getattr( childWidget, '_qwidgetFactory', None )
      if qwidgetFactory is not None:
        del childWidget._qwidgetFactory
        qwidgetFactory._preservedSipWidgets.discard( childWidget )
      self.processChildWidget( mainWidget, childWidget )
    return mainWidget


  def processChildWidget( self, mainWidget, childWidget ):
    name = str( childWidget.name() )
    if not self.ignoreInvalidCustomWidgets and hasattr( childWidget, '_invalid_custom_widget' ):
      raise RuntimeError( 'Unknown custom widget class: ' + childWidget._invalid_custom_widget )
    if name.startswith( 'EXPORT_' ):
      name = name[ 7: ]
      childWidget.setName( name )
      setattr( mainWidget, name, childWidget )
  

class CustomizedQWidgetFactory( qtui.QWidgetFactory ):

  '''This class manages the creation of custom widgets embedded in *.ui files.
  In order to work, instances of CustomizedQWidgetFactory must be registered in
  an application global set of QWidgetFactory instances:

    import qt, qtui
    qApp = qt.QApplication( sys.argv )
    customizedQWidgetFactory = CustomizedQWidgetFactory()
    qtui.QWidgetFactory.addWidgetFactory( customizedQWidgetFactory )
  '''
  
  def __init__( self ):
    qtui.QWidgetFactory.__init__( self )
    self.__registeredFactories = {}
    # It is mandatory to keep a Python reference to any widget that need
    # to preserve the link between C++ widget and Python widget. These
    # references are kept in self._preservedSipWidgets and must be removed by
    # the various widget factories after the call to QWidgetFactory.create().
    self._preservedSipWidgets = set()
    
  def createWidget( self, className, parent, name ):
    className = str( className )
    widgetFactory = self.__registeredFactories.get( className )
    if widgetFactory is not None:
      w = widgetFactory( parent, name )
      self._preservedSipWidgets.add( w )
      w._qwidgetFactory = self
    else:
      w = qt.QWidget( parent, name )
      w._invalid_custom_widget = className
    return w


  def addWidgetFactory( self, className, widgetFactory ):
    '''Register a WidgetFactory that will create widgets whose class is
    className. If a factory is already registered for className, KeyError
    is raised.'''
    existingFactory = self.__registeredFactories.get( className )
    if existingFactory is None:
      self.__registeredFactories[ className ] = widgetFactory
    else:
      raise KeyError( 'A WidgetFactory is already registered for widget class ' + className )

  def removeWidgetFactory( self, className ):
    '''Remove a factory previously registered with addWidgetFactory(). Returns
    the removed factory or None if no factory is registered for className.'''
    return self.__registeredFactories.pop( className )


def createWidget( uiFile, parent=None, name=None,
                  translationFile = None,
                  ignoreInvalidCustomWidgets=False ):
  return UIWidgetFactory( 
    uiFile,
    translationFile = translationFile,
    ignoreInvalidCustomWidgets = ignoreInvalidCustomWidgets 
  )( parent, name )
