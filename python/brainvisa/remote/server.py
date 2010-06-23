# -*- coding: utf-8 -*-
import Pyro, Pyro.core

from soma.singleton import Singleton
from soma.qtgui.api import QtThreadCall


class BrainVISAServer( Singleton ):
  def __singleton_init__( self ):
    self.daemon = None
  
  def initialize( self ):
    if self.daemon is None:
      Pyro.config.PYRO_TRACELEVEL = 3
      Pyro.config.PYRO_USER_TRACELEVEL = 3
      Pyro.config.PYRO_LOGFILE='/dev/stderr'
      Pyro.config.PYRO_STDLOGGING = 1
      Pyro.core.initServer()
      self.daemon = Pyro.core.Daemon()
      self.qtThread = QtThreadCall()
  
  def addObject( self, obj ):
    return self.daemon.connect( obj )
  
  def serve( self ):
    while True:
      self.daemon.handleRequests( 1.0 )
      self.qtThread.doAction()

