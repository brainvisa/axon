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

from __future__ import print_function
from brainvisa.configuration import neuroConfig
import six

if neuroConfig.anatomistImplementation != 'socket':

  import anatomist.cpp as anacpp
  from soma.qt_gui.qt_backend import QtGui, QtCore
  from soma.wip.application.api import findIconFile
  from soma import aims
  try:
    from soma.aims import aimsgui
  except:
    print('Warning: pyaimsgui not available')

  class ReusableWindowAction( QtGui.QAction ):
    _actions = {} # dict to kee buttons alive

    def __init__( self, icon, text, parent ):
      QtGui.QAction.__init__( self, icon, text, parent )
      from brainvisa import anatomist
      a = anatomist.Anatomist( [ '-b' ] )
      win = a.AWindow( a, parent, refType='Weak' )
      ReusableWindowAction._actions[win] = self
      acts = ReusableWindowAction._actions
      # filter out dead windows
      ReusableWindowAction._actions = {}
      for w,b in six.iteritems(acts):
        if w.get() is not None:
          ReusableWindowAction._actions[w] = b

    def toggleReuseWindow( self, state ):
      win = self.parent()
      from brainvisa import anatomist
      a = anatomist.Anatomist( [ '-b' ] )
      a.setReusableWindow( a.AWindow( a, win, refType='WeakShared' ), state )

  class ReusableWindowBlockAction( QtGui.QAction ):
    _actions = {}

    def __init__( self, icon, text, parent ):
      QtGui.QAction.__init__( self, icon, text, parent )
      ReusableWindowBlockAction._actions[parent] = [ self ]
      parent.destroyed.connect( self.removeparent )

    def toggleReuseWindow( self, state ):
      win = self.parent()
      from brainvisa import anatomist
      a = anatomist.Anatomist( [ '-b' ] )
      a.setReusableWindowBlock( win, state )
      reuseaction = win.findChild( QtGui.QAction, 'reuseAllAction' )
      if state:
        reuseaction.setText( self.tr( \
          'Don\'t reuse any longer block and windows', 'QAWindowBlock' ) )
      else:
        reuseaction.setText( self.tr( \
          'Keep and reuse in BrainVisa, with all current views',
          'QAWindowBlock' ) )

    def removeparent( self, parent ):
      del ReusableWindowBlockAction._actions[parent]

  class ReusableWindowBlockWithViewsAction( QtGui.QAction ):

    def __init__( self, icon, text, parent ):
      QtGui.QAction.__init__( self, icon, text, parent )
      ReusableWindowBlockAction._actions[parent].append( self )

    def toggleReuseWindowWithViews( self ):
      win = self.parent()
      reuseaction = win.findChild( QtGui.QAction, 'reuseAction' )
      state = not reuseaction.isChecked()
      reuseaction.setChecked( state )
      awins =  win.findChildren( anacpp.QAWindow )
      from brainvisa import anatomist
      a = anatomist.Anatomist( [ '-b' ] )
      awins = [ a.AWindow(a, w) for w in awins ]
      a.setReusableWindow( awins, state )
      if state:
        self.setText( self.tr( 'Don\'t reuse any longer block and windows', 'QAWindowBlock' ) )
      else:
        self.setText( self.tr( \
          'Keep and reuse in BrainVisa, with all current views',
          'QAWindowBlock' ) )

  class ReusableWindowHook( anacpp.EventHandler ):
    def doit( self, event ):
      if event.eventType() == 'CreateWindow':
        win = event.contents()[ '_window' ]
        if isinstance( win, QtGui.QMainWindow ):
          toolbar = win.findChild( QtGui.QToolBar, 'mutations' )
          if toolbar is None:
            toolbar = win.findChild( QtGui.QToolBar )
            if toolbar is None:
              toolbar = win.addToolBar( 'BV toolbar' )
              if win.toolBarsVisible():
                toolbar.show()
              else:
                toolbar.hide()
          if toolbar is not None:
            toolbar.addSeparator()
            icon = QtGui.QIcon( findIconFile( 'eye.png' ))
            ac = ReusableWindowAction( icon,
              win.tr( 'Keep and reuse in BrainVisa', 'QAWindowBlock' ), win )
            ac.setCheckable( True )
            ac.toggled.connect( ac.toggleReuseWindow )
            toolbar.addAction( ac )

  class ReusableWindowBlockHook( anacpp.EventHandler ):
    def doit( self, event ):
      if event.eventType() == 'CreateWindowBlock':
        block = event.contents()[ '_block' ]
        if isinstance( block, QtGui.QMainWindow ):
          menubar = block.menuBar()
          menu = menubar.addMenu( 'BrainVISA' )
          icon = QtGui.QIcon( findIconFile( 'eye.png' ))
          ac = ReusableWindowBlockAction( icon,
            block.tr( 'Keep and reuse in BrainVisa', 'QAWindowBlock' ), block )
          ac.setCheckable( True )
          ac.toggled.connect( ac.toggleReuseWindow )
          ac.setObjectName( 'reuseAction' )
          menu.addAction( ac )
          ac = ReusableWindowBlockWithViewsAction( icon,
            block.tr( 'Keep and reuse in BrainVisa, with all current views',
              'QAWindowBlock' ), block )
          ac.triggered.connect( ac.toggleReuseWindowWithViews )
          ac.setObjectName( 'reuseAllAction' )
          menu.addAction( ac )

  handlers = None

  def installWindowHandler():
    global handlers
    handlers = [ ReusableWindowHook(), ReusableWindowBlockHook() ]
    anacpp.EventHandler.registerHandler( 'CreateWindow', handlers[0] )
    anacpp.CommandContext.defaultContext().evfilter.filter( 'CreateWindow' )
    anacpp.EventHandler.registerHandler( 'CreateWindowBlock', handlers[1] )
    anacpp.CommandContext.defaultContext().evfilter.filter( 'CreateWindowBlock' )

  def uninstallWindowHandler():
    global handlers
    if handlers:
      anacpp.EventHandler.unregisterHandler( 'CreateWindow', handlers[0] )
      anacpp.EventHandler.unregisterHandler( 'CreateWindowBlock', handlers[1] )
      handlers = None

