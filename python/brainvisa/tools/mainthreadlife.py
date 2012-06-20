#!/usr/bin/env python
# -*- coding: utf-8 -*-

from brainvisa.processing.qtgui.neuroProcessesGUI import mainThreadActions
import threading

class MainThreadLife( object ):
  '''This wrapper class ensures the contained object is deleted in the main
  thread, and not in the current non-GUI thread. The principle is the
  following:
  - acquire a lock
  - pass the object to something in the main thread
  - the main thread waits on the lock while holding a reference on the object
  - we delete the object in the calling thread
  - the lock is releasd from the calling thread
  - now the main thread can go on, and del / release the ref on the object: it
    is the last ref on it, so it is actually deleted there.
  '''
  def __init__( self, obj ):
    self.object = obj
  def __del__( self ):
    if not isinstance( threading.currentThread(), threading._MainThread ):
      lock = threading.Lock()
      lock.acquire()
      mainThreadActions().push( self.delInMainThread, lock, self.object )
      del self.object
      lock.release()
  @staticmethod
  def delInMainThread( lock, thing ):
    # wait for the lock to be released in the process thread
    lock.acquire()
    lock.release()
    # now the process thread should have removed its reference on thing:
    # we can safely delete it fom here, in the main thread.
    del thing # probably useless

