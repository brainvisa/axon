# Copyright IFR 49 (1995-2009)
#
#  This software and supporting documentation were developed by
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
"""This module is useful whenever you need to be sure that a function (more
exactly anything that can be called by python) is executed in a particular
thread. 

For exemple, if you use PyMat (which is an interface between Python and a Matlab,
see http://claymore.engineer.gvsu.edu/~steriana/Python for more information) it
is necessary that all calls to pymat.eval are done by the same thread that
called pymat.open. If you want to use PyMat in a multi-threaded application,
you will have to build appropriate calling mechanism as the one proposed in
this module.

The main idea is to use a Queue containing functions to be called with their
parameters. A single thread is used to get entries from the Queue and execute
the corresponding functions. Any thread can put a call request on the Queue
either asynchonously (the requesting thread continues to run without waiting
for the call to be done) or synchronously (the requesting thread is stoped
until the call is done and can get the result).
"""

from brainvisa.Static import Static
import threading, Queue


class SingleThreadCalls:
  """Apply function calls within a single thread. These functions can be called
  from any thread."""
  
  def __init__( self, thread, queue ):
    """The thread passed in parameter is attached to this object. When started
    (which is not been done by this object) it must continuously get functions
    and parameters form the queue and execute these functions until None is
    found on the queue."""
    self._queue = queue
    self._thread = thread
  
  def call( self, function, *args, **kwargs ):
    """Calls a function synchonously on the attached thread and returns its 
       result.
       
       The required parameter is the function object to be called. Optional
       parameters and keyword parameters are used to call the function.

       If the current thread is the attached thread, the function is executed
       immediatly. Otherwise, the function and its parameters are putted on the
       queue and the current thread is stopped until the function has been
       processes by the attached thread. The returned value is the value 
       returned by the function."""
    if threading.currentThread() is self._thread:
      result = apply( function, args, kwargs )
    else:
      condition = threading.Condition()
      condition._result = None
      condition._exception = None
      condition.acquire()
      self._queue.put( ( self._executeAndNotify, (condition, function, args, kwargs), {} ) )
      condition.wait()
      if condition._exception is not None:
        e = condition._exception
        condition.release()
        raise e
      result = condition._result
      condition.release()
    return result

  def _executeAndNotify( condition, function, args, kwargs ):
    try:
      result = apply(  function, args, kwargs )
      condition.acquire()
      condition._result = result
      condition._exception = None
      condition.notifyAll()
      condition.release()
    except Exception, e:
      condition.acquire()
      condition._exception = e
      condition.notifyAll()
      condition.release()

  _executeAndNotify = Static( _executeAndNotify )

  def push( self, function, *args, **kwargs ):
    """Same as call() method but always put the function on the queue and
    returns immediatly. 
    Always returns None."""
    self._queue.put( ( function, args, kwargs ) )

  def stop( self ):
    """Tells the attached thread to stop processing calls by putting None
    on the queue"""
    self._queue.put( None )
  

class CallerThread( threading.Thread ):
  """Create a thread object that continuously get functions and parameters form
  a queue and execute these functions until None is found on the queue."""
  
  def __init__( self, queue, name=None ):
    """Attach the queue to the thread. A name can be given for the new thread"""
    threading.Thread.__init__( self, name=name )
    self._queue = queue
    
  def run( self ):
    while 1:
      action = self._queue.get()
      if action is not None:
        function, args, kwargs = action
        apply( function, args, kwargs )
      else:
        break
