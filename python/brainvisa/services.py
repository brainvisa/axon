
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
import socket, SocketServer, struct, time, weakref
from brainvisa import notifier
import threading, os, types, string, copy

import pickle
from cStringIO import StringIO
from brainvisa.Static import Static
import signal, operator, traceback, sys


ports = 0

class ServiceDied( Exception ):
  pass


def dbgmsg( *args ):
  if 1:
    file, line, function, text = traceback.extract_stack()[-2]
    print '---', function, 'in', file, 'line', line, 'thread', \
          threading.currentThread()._Thread__name, '---'
    if args: print ' ', string.join( map( str, args ) )

# Global service manager is a singleton which is application dependant.
# It is just set to None here to materialize its existance.
serviceManager = None


#debugging RLock

class RLock:
  def __init__( self ):
    self.rlock = threading.RLock()

  def acquire( self ):
    #dbgmsg( 'acquire:', self.rlock._RLock__count )
    self.rlock.acquire()

  def release( self ):
    #dbgmsg( 'release:', self.rlock._RLock__count )
    self.rlock.release()


class ObjectExchanger:
  '''Used to send/receive Python values on a socket in a safe way (i.e. no
  code execution allowed).'''

  # Only object which are exclusively built on the following types can
  # be sent.
  authorizedTypes = {
    types.NoneType: 1,
    types.IntType: 1,
    types.LongType: 1,
    types.FloatType: 1,
    types.ComplexType: 1,
    types.StringType: 1,
    types.UnicodeType: 1,
    types.TupleType: 1,
    types.ListType: 1,
    types.DictType: 1,
  }

  class CheckedPickler( pickle.Pickler ):
    def dump( self, object ):
      if not ObjectExchanger.authorizedTypes.get( type( object ), 0 ):
        raise pickle.PickleError( 
          _t_( 'forbidden to send object of type %s over the network' ) % \
          ( str(type(object)), ) )
      return pickle.Pickler.dump( self, object )

  class CheckedUnpickler( pickle.Unpickler ):
    def load_global(self):
      raise pickle.UnickleError( 
        _t_( 'forbidden to receive instance object from the network' ) )
      
  
  def dumps( object ):
    file = StringIO()
    ObjectExchanger.CheckedPickler( file, 1 ).dump( object )
    return file.getvalue()

  dumps = Static( dumps )
  

  def loads( str ):
    file = StringIO( str )
    return ObjectExchanger.CheckedUnpickler( file ).load()

  loads = Static( loads ) 

  
  def send( self, object, sck ):
    # Check object type
    #print 'send to', sck.getpeername(), ':', object
    data = self.dumps( object )
    size = struct.pack( 'l', socket.htonl( len( data ) ) )
    data = size + data
    sent = sck.send( data )
    while sent < len( data ):
      sent += sck.send( data[ sent: ] )
    #print '(sent)'

  def receive( self, sck ):
    x = sck.recv( 4 )
    while len( x ) < 4:
      x += sck.recv( 4 - len( x ) )
    size = socket.ntohl ( struct.unpack( 'l', x )[0] )
    data = sck.recv( size )
    while len( data ) < size:
      data += sck.recv( size - len( data ) )
    #print 'received from', sck.getpeername(), ':', self.loads(data)
    return self.loads( data )



class ServiceCertificate:
  '''This class is used to handle local or distant service execution
  authorization.'''
  
  def __init__( self, username ):
    self.userName = username



class RequestID:
  '''Object used to identify a service request. When a RequestID is no longer
  referenced in python, the corresponding request state in the manager may be
  deleted.
  '''
  def __init__( self, id ):
    self.id = id


class RequestState:
  '''Records all information necessary to manage an asynchronous service
  request.
  '''
  # sent to the distant server
  Sent = 1
  # started & running
  Running = 3
  # cancel requested, not yet actually stopped
  Cancelled = 4
  # stopped after a cancel
  Stopped = 5
  # normally finished
  Finished = 6
  # error during execution
  Exception = 7

  def __init__( self ):
    self.state = None
    self.returnValue = None
    self.startTime = None
    self.stopTime = None
    self.stateNotifier = notifier.Notifier( 1 )
    self.distantID = None
    self.managerAddress = None
    self._idLife = None

  def __str__( self ):
    return str( self.__dict__ )


class LocalRequestState( RequestState ):
  '''The requested service is called from a local function and is processed on
  the same process as the ServiceManager (via a Thread). No network
  communication is required.
  '''
  def __init__( self ):
    RequestState.__init__( self ) 
    self.thread = None

class ServerRequestState( RequestState ):
  '''The requested service is called from a distant ServiceManager. The distant
  ServiceManager address and the corresponding RequestID must be stored. Each
  time the request state is changed, the distant ServiceManager must be notified
  of the change (this is done via the admin.syncRequestState service of the
  distant ServiceManager).
  '''
  def __init__( self ):
    RequestState.__init__( self ) 
    self.childPid = None
    
class ClientRequestState( RequestState ):
  '''The requested service is called from a local function and is processed on
  a distant ServiceManager. The request state is a local copy of the distant
  service  state. Therefore, it is read-only for local application and should
  only be modified by admin.syncRequestState trusted service).
  '''
  def __init__( self ):
    RequestState.__init__( self )
    # RequestState instances are kept in a dictionary in the ServiceManager with
    # weak references on RequestID. Whenever the corresponding RequestID is not
    # used by the local application anymore, the RequestState is removed from
    # the ServiceManager. But if the service is still being processed by a
    # distant ServiceManager, ...

  def __del__( self ):
    # TODO: call the server
    pass



class RequestHandler( SocketServer.BaseRequestHandler ):
  def handle( self ):
    try:
      # Receive service request
      serviceRequest = self.server.objectExchanger.receive( self.request )

      # Check service request
      if not operator.isSequenceType( serviceRequest ):
        raise TypeError( _t_( 
          'Server %s recieved a bad request object type (%s) from %s') % \
          ( str(self.server.server_address), str(type(serviceRequest),
            str(self.client_address) ) ) )
      # At least protocol, certificate and service name are required
      if len( serviceRequest ) < 3:
        raise ValueError( _t_( 
          'Server %s recieved an invalid request from %s: %s') % \
          ( str(self.server.server_address), str(self.client_address),
            str( serviceRequest) ) )

      # Find the service
      serviceName = serviceRequest[ 2 ]
      print 'request received:', serviceName
      serviceObject = self.server._findServiceObject( serviceName )
      
      # All certificate stuff is on progress. Actually, only the user name
      # is exchanged and certificate are always accepted.
      
      # Check certificate validity for this service
      certificate = ServiceCertificate( serviceRequest[ 1 ] )
      try:
        self.server.checkCertificate( certificate )
      except:
        raise RuntimeError( 
          _t_( 'Certification failure for service %s on server %s by %s' % \
               ( serviceRequest[ 1 ], str( self.server.server_address ), 
                 certificate.userName ) ) )
      #print 'request received:', serviceRequest, 'from', self.client_address
      # process request
      if serviceRequest[ 0 ] == ServiceManager.netobjSynchronousService:

        # Get request parameters
        try:
          args, kwargs = serviceRequest[ 3: ]
        except:
          raise ValueError( _t_( 
            'Server %s recieved a synchronous request with invalid parameters from %s: %s') % \
            ( str(self.server.server_address), str(self.client_address),
              str( serviceRequest) ) )
        #
        # Process synchronous service request
        #
        if isinstance( serviceObject, TrustedService ):
          # Synchronous TrustedServices can be executed by server
          result = self.server.call( serviceName, *args, **kwargs )
          answer = [ ServiceManager.netobjSuccess, result ]
          self.server.objectExchanger.send( answer, self.request )
        else:
          # TODO: under Windows, do something else...
          pid = os.fork()
          if pid:
            # Parent process
            self.server.close_request(self.request)
            return
          else:
            # Child process.
            # This must never return, hence os._exit()!
            try:
              try:
                self.server.setAuthorization( certificate )
                result = self.server.call( serviceName, *args, **kwargs )
                answer = [ ServiceManager.netobjSuccess, result ]
                self.server.objectExchanger.send( answer, self.request )
              except Exception, e:
                # Send a netobjError as an answer
                answer = [ ServiceManager.netobjError, e.__class__.__name__, e.args ]
                self.server.objectExchanger.send( answer, self.request )
            finally:
              dbgmsg( 'exiting child (synchronous)' )
              os._exit(1)
 
      elif serviceRequest[ 0 ] == ServiceManager.netobjAsynchronousService:

        # Get request parameters
        try:
          clientAddress, distantID, args, kwargs = \
            serviceRequest[ 3: ]
          # force IP of source since it should not be hard-coded in the
          # protocol and has many chances to be wrong
          clientAddress = ( self.client_address[0], clientAddress[1] )
        except:
          raise ValueError( _t_( 
            'Server %s recieved an asynchonous request with invalid parameters from %s: %s') % \
            ( str(self.server.server_address), str(self.client_address),
              str( serviceRequest) ) )

        #
        # Process asynchronous service request
        #
        if isinstance( serviceObject, TrustedService ):
          id = self.server._startClientAware( serviceName, clientAddress,
                                              distantID, *args, **kwargs )
          answer = [ ServiceManager.netobjSuccess, id.id ]
          self.server.objectExchanger.send( answer, self.request )
        else: # not trusted
          # create request
          print 'asynchronous request'
          id = self.server.createServerRequest( state = RequestState.Sent,
                                                startTime = time.time(),
                                                managerAddress = clientAddress,
                                                distantID = distantID )
          self.server.setRequestState( id, _idLife = id )
          # fork
          # TODO: under Windows, do something else...
          pid = os.fork()
          if pid:
            # Parent process
            self.server.setRequestState( id, pid = pid )
            answer = [ ServiceManager.netobjSuccess, id.id ]
            print 'server parent:', answer
            self.server.objectExchanger.send( answer, self.request )
          else:
            # Child process.
            # This must never return, hence os._exit()!
            try:
              try:
                self.server.close_request(self.request)
                self.server.setAuthorization( certificate )
                print 'server child:', serviceName
                if isinstance( serviceObject, ClientAwareService ):
                  result = self.server._callClientAware( serviceName,
                                                         clientAddress,
                                                         distantID, *args,
                                                         **kwargs )
                else:
                  result = self.server.call( serviceName, *args, **kwargs )
                # c'est le fils qui repond a son papa: server_address,
                # pas managerAddress
                print 'server child done'
                self.server.callDistant( self.server.server_address,
                                         'admin.syncRequestState', id.id, 
                                         state=RequestState.Finished,
                                         returnValue = result )
              except Exception, e:
                self.server.callDistant( self.server.server_address,
                                         'admin.syncRequestState', id.id, 
                                         state=RequestState.Exception,
                                         returnValue = ( e.__class__.__name__,
                                                         e.args  ) )
            finally:
              #dbgmsg( 'exiting child (asynchronous)' )
              os._exit(1)

      else:
        raise ValueError( _t_( 
          'Server %s recieved an invalid request type (%s= from %s') % \
          ( str(self.server.server_address), str(serviceRequest[ 0 ]),
            str(self.client_address) ) )
    except Exception, e:
      # An error occured during request processing.
      # Send a netobjError as an answer
      answer = [ ServiceManager.netobjError, e.__class__.__name__, e.args ]
      self.server.objectExchanger.send( answer, self.request )
      # Raise processed exception
      raise


class ServiceManager( SocketServer.ThreadingMixIn, SocketServer.TCPServer ):
  '''
  '''

  # Low-level server protocol is based on transmission of netobj. Netobjs are
  # python list where the first element represent the type of request or answer.
  # The other elements are the request/answer parameters values.
  #
  # A server listen for one netobj and always send one netobj as answer. Further
  # exchange may be done on the client - server communication socket.
  
  netobjSynchronousService = 0   
  # Request for a synchronous service
  # Parameters :
  #   - Service name : a dot separated series of identifiers.
  #   - Certificate
  #   - Services arguments : a list of argument values
  #   - Service named arguments : a dictionary where keys are parameter name
  #     and values are argument values
  # Returned object :
  #   - netobjSuccess with a return value
  #   - netobjError
  
  netobjAsynchronousService = 1  
  # Request for an asynchronous service
  # Parameters :
  #   - Service name : a dot separated series of identifiers.
  #   - Certificate
  #   - Client address : address of the ServiceManager requesting the service
  #   - Distant service ID : ID of the service on the ServiceManager requesting
  #     the service
  #   - Services arguments : a list of argument values
  #   - Service named arguments : a dictionary where keys are parameter name
  #     and values are argument values
  # Returned object :
  #   - netobjSuccess with the request ID on the server
  #   - netobjError

  netobjSuccess = 2
  # Answer indicating that a netobj has been successfully received and processed
  # Parameters depends on the type of netobj processed. Usualy there is no
  # parameter (simple aknowledgement) or a single return value.
  
  netobjError = 3
  # Answer indicating that an error occured during the processing of a netobj.
  # Parameters :
  # - Error type : a string corresponding to a Python exception class
  # - Error arguments. A list of arguments that have been used to raise the
  #   exception.

  
  def __init__( self, ip='', port=8458 ):
    ok = 0
    portmax = port + 1000
    while not ok:
      try:
        SocketServer.TCPServer.__init__( self, ( ip, port ), RequestHandler )
        ok = 1
      except:
        #print 'port', port, 'is not usable.'
        port += 1
        if port == portmax:
          print 'cannot find a valid port number for the server'
          raise
    print 'ServiceManager started on port', port
    self.objectExchanger = ObjectExchanger()
    self._lock = RLock()
    self._services = {}
    self._requests = weakref.WeakKeyDictionary()
    self._requestIDs = weakref.WeakValueDictionary()
    self._requestCounter = 0
    self._pendingRequests = {}
    self._joinRequests = {}
    self._thread = threading.Thread( target = self.serve_forever )
    self._thread.start()
    self.localAddress = None
    # set signal handler
    if sys.platform[:3] != 'win':
      signal.signal( signal.SIGCHLD, sigChldHandler )
    self.registerService( 'admin', AdministrationServices() )
    # broadcast our presence to a scheduler
    remote_host, remote_port = '<broadcast>', 45010
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    data = struct.pack( 'l', socket.htonl( port ) )
    print 'server broadcasting to', remote_host, remote_port
    sent = sock.sendto( data, (remote_host, remote_port) )
    #while sent < len( data ):
    #  sent += sock.sendto( data[ sent: ], (remote_host, remote_port) )
    print 'broadcast sent'


  def registerService( self, name, service ):
      self._lock.acquire()
      try:
          serv = self._services.get( name )
          if serv is not None and serv is not service:
              raise KeyError( _t_( 'Service %s is already registered' ) \
                              %( name, ) )
          self._services[ name ] = service
      finally:
          self._lock.release()

  def unregisterService( self, name ):
      self._lock.acquire()
      try:
          try:
              del self._services[name]
          except KeyError:
              pass
      finally:
          self._lock.release()

  def _findServiceObject( self, request ):
    if type( request ) is types.StringType:
      request = string.split( request, '.' )
    self._lock.acquire()
    try:
      serv = self._services.get( request[0] )
    finally:
      self._lock.release()
    if serv is None:
      raise KeyError( _t_( 'Service %s does not exist' ) \
                          %( request[0], ) )
    return serv

  def _findServiceCallable( self, request ):
    if type( request ) is types.StringType:
      request = string.split( request, '.' )
    serv = self._findServiceObject( request )
    
    # find function in service object
    i = 1
    for attr in request[1:]:
      serv = getattr( serv, attr, None )
      if serv is None:
          raise AttributeError( _t_( 'Attribute %s not found in %s' ) \
                                %( attr, string.join( request[:i],
                                                          '.' ) ) )
      i += 1
    # now serv is the callable
    return serv

  def getNewID( self ):
    self._lock.acquire()
    try:
      id = self._requestCounter
      self._requestCounter += 1
    finally:
      self._lock.release()
    return RequestID( id )

  def createLocalRequest( self, **kwargs ):
    self._lock.acquire()
    try:
      id = self.getNewID()
      self._requestIDs[ id.id ] = id
      self._requests[ id ] = LocalRequestState()
      self.setRequestState( id, **kwargs )
    finally:
      self._lock.release()
    return id

  def createClientRequest( self, **kwargs ):
    self._lock.acquire()
    try:
      id = self.getNewID()
      self._requestIDs[ id.id ] = id
      self._requests[ id ] = ClientRequestState()
      self.setRequestState( id, **kwargs )
    finally:
      self._lock.release()
    return id

  def createServerRequest( self, **kwargs ):
    self._lock.acquire()
    try:
      id = self.getNewID()
      self._requestIDs[ id.id ] = id
      self._requests[ id ] = ServerRequestState()
      self.setRequestState( id, **kwargs )
    finally:
      self._lock.release()
    return id

  def setRequestState( self, id, **kwargs ):
    self._lock.acquire()
    try:
      req = self.requestState( id )
      distantID = getattr( req, 'distantID', None )
      for n, v in kwargs.items():
          setattr( req, n, v )
      stateToSend = {}
      if not isinstance( req, ClientRequestState ) and distantID is not None:
        # Synchronize client request state
        for attributesToSynchronize in ( 'state', 'returnValue' ):
          value = kwargs.get( attributesToSynchronize )
          if value is not None:
            stateToSend[ attributesToSynchronize ] = value
      # TODO: do something for Cancelled state
      # cleanup
      if kwargs.get( 'state' ) in \
             ( RequestState.Stopped, RequestState.Finished,
               RequestState.Exception ):
        req.stopTime = time.time()
        req._idLife = None
    finally:
      self._lock.release()

    if stateToSend:
      self.callDistant( req.managerAddress, 'admin.syncRequestState',
                        req.distantID, **stateToSend )
    # notify...
    req.stateNotifier( id )

  def cancel( self, id ):
    self._lock.acquire()
    try:
      req = self.requestState( id )
      distantID = getattr( req, 'distantID', None )
      if isinstance( req, ClientRequestState ):
        if distantID is not None:
          self.callDistant( req.managerAddress, 'admin.syncRequestState',
                            req.distantID, state=RequestState.Cancelled )
    finally:
      self._lock.release()

  def requestID( self, id ):
    if isinstance( id, RequestID ):
      return id
    return self._requestIDs[ id ]

  def requestState( self, id ):
    if not isinstance( id, RequestID ):
      id = self._requestIDs[ id ]
    return self._requests[ id ]

  def call( self, request, *args, **kwargs ):
    '''Call a local synchronous service.
    '''
    print 'call', request, args, kwargs
    return self._findServiceCallable( request )( *args, **kwargs )

  def start( self, request, *args, **kwargs ):
    '''Start a local asynchronous service.
    '''
    service =  self._findServiceCallable( request )
    if isinstance( service, ServiceProxy ):
      return service.start( *args, **kwargs )
    else:
      # make a thread
      id = self.createLocalRequest( state = RequestState.Sent,
                               startTime = time.time() )
      thr = threading.Thread( target = self._doThreadService, 
                              args = ( service, id ) + args,
                              kwargs = kwargs )
      thr.start()
      return id

  def _callClientAware( self, request, managerAddress, distantID,
                        *args, **kwargs ):
    '''Call a local synchronous service with remote ID/address params.
    '''
    print '_callClientAware', request, managerAddress, distantID, args, kwargs
    return self._findServiceCallable( request )( distantID,
                                                 managerAddress,
                                                 *args, **kwargs )

  def _startClientAware( self, request, managerAddress, distantID, *args, \
                         **kwargs ):
    '''Start a local asynchronous service.
    '''
    service =  self._findServiceCallable( request )
    if isinstance( service, ServiceProxy ):
      return service.start( *args, **kwargs )
    else:
      # make a thread
      id = self.createLocalRequest( state = RequestState.Sent,
                                    startTime = time.time(),
                                    managerAddress = managerAddress,
                                    distantID = distantID )
      self.setRequestState( id, _idLife = id )
      thr = threading.Thread( target = self._doThreadService, 
                              args = ( service, id ) + args,
                              kwargs = kwargs )
      thr.start()
      return id

         
  def _doThreadService( self, service, id, *args, **kwargs ):
    '''Method executed in a thread to process local asynchronous services.
    '''
    self.setRequestState( id, thread = threading.currentThread(),
                          state = RequestState.Running )
    try:
      ret = service( *args, **kwargs )
      self.setRequestState( id, state = RequestState.Finished,
                            returnValue = ret, stopTime = time.time(),
                            thread = None )
    except Exception, e:
      self.setRequestState( id, state = RequestState.Exception,
                            returnValue = ( e.__class__.__name__, e.args  ),
                            stopTime = time.time(), thread = None )


  def callDistant( self, address, serviceName, *args, **kwargs ):
    '''Synchronous call on a distant ServiceManager.
    '''
    certif = ServiceCertificate( os.environ[ 'USER' ] )
    request = [ self.netobjSynchronousService, certif.userName, serviceName,
                args, kwargs ]
    s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    s.connect( address )
    self.objectExchanger.send( request, s )
    answer = self.objectExchanger.receive( s )
    if answer[ 0 ] == self.netobjSuccess:
      return answer[ 1 ]
    elif answer[ 0 ] == self.netobjError:
      # TODO: must not use eval here for security reasons but for testing it is
      # ok.
      print 'answer is error:', answer
      raise eval( answer[ 1 ] )( *answer[ 2 ] )
    else:
      raise ValueError(
         _t_( 'Bad answer from server %s (synchronous %s call) : %s' ) % \
         ( str( address ), serviceName, str( answer ) ) )


  def startDistantCallbacks( self, address, callbacks, serviceName,
                             *args, **kwargs ):
    '''Asynchronous call on a distant ServiceManager.
    '''
    id = self.createClientRequest()
    return self._startDistantCallbacksWithID( address, id, callbacks,
                                              serviceName, *args, **kwargs )

  def _startDistantCallbacksWithID( self, address, id, callbacks, serviceName,
                                    *args, **kwargs ):
    '''Asynchronous call on a distant ServiceManager.
    '''
    # check if we're not calling ourself
    if address == self.localAddress:
      print "startDistant: we're calling ourself. Changing to local request"
      return self.start( serviceName, *args, **kwargs )
    self._lock.acquire()
    try:
      req = self.requestState( id )
      idLife = req._idLife
      ClientRequestState.__init__( req )
      req._idLife = idLife
      del idLife    
      self.setRequestState( id, state = RequestState.Sent,
                            startTime = time.time(),
                            managerAddress = address )
      for n in callbacks:
        req.stateNotifier.add( n )
    finally:
      self._lock.release()
    # ? fill _idLife ?
    certif = ServiceCertificate( os.environ[ 'USER' ] )
    request = [ self.netobjAsynchronousService, certif.userName, serviceName,
                self.server_address, id.id, args, kwargs ]
    s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    s.connect( address )
    self.objectExchanger.send( request, s )
    answer = self.objectExchanger.receive( s )
    if answer[ 0 ] == self.netobjSuccess:
      self.setRequestState( id, distantID = answer[ 1 ] )
      return id
    elif answer[ 0 ] == self.netobjError:
      # TODO: must not use eval here for security reasons but for testing it is
      # ok.
      raise eval( answer[ 1 ] )( *answer[ 2 ] )
    else:
      raise ValueError(
         _t_( 'Bad answer from server %s (asynchronous %s call) : %s' ) % \
         ( str( address ), serviceName, str( answer ) ) )

  def startDistant( self, address, serviceName, *args, **kwargs ):
    return self.startDistantCallbacks( address, (), serviceName, *args, **kwargs )

  def distributeService( self, request, *args, **kwargs ):
    return self.distributeServiceCallbacks( (), request, *args, **kwargs )

  def distributeServiceCallbacks( self, callbacks, request, *args, **kwargs ):
    print 'distributeServiceCallbacks:', request
    from brainvisa import scheduler
    sched = scheduler.findScheduler()
    #print 'distributeServiceCallbacks: calling scheduler', sched
    id = self.startDistantCallbacks( sched, ( self._schedulerMessage, ),
                                     'scheduler.schedule', request )
    #print 'registering pending request', id
    self._pendingRequests[ id ] = ( request, args, kwargs, callbacks )
    #print 'distributeServiceCallbacks exiting'
    return id

  def _schedulerMessage( self, id ):
    if not isinstance( id, RequestID ):
      id = self._requestIDs[ id ]
    #print '_schedulerMessage', id
    x = self._pendingRequests.get( id )
    print x
    # warning; the fisrt state change is lost
    if x is not None:
      request, args, kwargs, callbacks = x
      sreq = serviceManager.requestState( id )
      #print 'requestState:', sreq
      if sreq.state == RequestState.Finished:
        address = sreq.returnValue
        del self._pendingRequests[ id ]
        #print 'clientSchedule: running:', address, id, request
        if address == self.localAddress:
          print "it's ME !"
        serviceManager._startDistantCallbacksWithID( address, id, callbacks,
                                                     request, *args,
                                                     **kwargs )
        print 'scheduled request started on', address, id, request
      elif sreq.state in ( RequestState.Stopped, RequestState.Exception,
                           RequestState.Cancelled ):
        del self._pendingRequests[ id ]
        for i in callbacks:
          #print 'calling callback:', i
          i( id )

  def join( self, *idList ):
    for id in idList:
      if not isinstance( id, RequestID ):
        id = self._requestIDs[ id ]
      #dbgmsg( 'try to join', id.id )
      self._lock.acquire()
      try:
        req = self.requestState( id )
        if req.state in ( RequestState.Stopped, RequestState.Exception, RequestState.Finished ):
          print '  join already finished'
          continue
        condition = self._joinRequests.get( id )
        if condition is None:
          condition = threading.Condition()
          self._joinRequests[ id ] = condition
          req.stateNotifier.add( self._joinNotification )
          condition.acquire()
      finally:
        self._lock.release()
      try:
        #print '  waiting'
        condition.wait()
        print '  join: wake up'
      finally:
        condition.release()
    print 'join done'


  def _joinNotification( self, id ):
    if not isinstance( id, RequestID ):
      id = self._requestIDs[ id ]
    #dbgmsg( 'joinNotification', id.id )
    self._lock.acquire()
    try:
      req = self.requestState( id )
      condition = None
      if req.state in ( RequestState.Stopped, RequestState.Exception, RequestState.Finished ):
        condition = self._joinRequests.get( id )
        if condition is None:
          print 'joinNotification: warning: request not found: already finished?'
        #print '  ending condition', condition
      #else:
        #print '  not ending yet:', req.state
    finally:
      self._lock.release()
    if condition is not None:
      condition.acquire()
      try:
        del self._joinRequests[ id ]
        condition.notifyAll()
      finally:
        condition.release()

    
  def childDead( self, pid, state ):
    self._lock.acquire()
    try:
      for id, req in self._requests.items():
        if isinstance( req, ServerRequestState ):
          p = req.pid
          if p == pid:
            self.setRequestState( id, state = RequestState.Exception,
                                  returnValue = ( 'ServiceDied', []  ) )
            break
    finally:
      self._lock.release()

  def checkCertificate( self, certif ):
    # TODO
    return 1

  def setAuthorization( self, certificate ):
    # Change user and group of the current process
    try:
      uid, gid = pwd.getpwnam( certificate.userName )[ 2:4 ]
      if os.getuid() != uid:
        os.setuid( uid )
      if os.getgid() != gid:
        os.setgid( gid )
    except Exception, e:
      RuntimeError( _t_('cannot change user identity: %s') % ( str(e), ) )

def startServiceManager( ip, port ):
  global serviceManager
  serviceManager = ServiceManager( ip, port )
  return serviceManager


class TrustedService:
  '''When a TrustedService instance is registered in a ServiceManager, all its
  methods may be executed with higher privilege than the client privilege.
  '''
  pass


class ClientAwareService:
  '''A ClientAwareService gets additional parameters which gives information
  about the client who asked the request:
  - requestID
  - managerAddress
  As synchronous executions don't have requestIDs, there is no generic way to
  provide all information at the moment.
  '''
  pass


class AdministrationServices( TrustedService ):
  '''Contains all methods used to manage ServiceManager'''
  def syncRequestState( self, localID, **kwargs ):
    serviceManager.setRequestState( localID, **kwargs )

  def servicesList( self, yourAddress=None, **kwargs ):
    if yourAddress is not None:
      # our own address is difficult to obtain so we let the scheduler
      # tell us which IP address it uses to contact us
      serviceManager.localAddress = yourAddress
    return serviceManager._services.keys()


class ServiceProxy:
  '''
  '''
  def __init__( self, address, serviceName ):
    self._address = address
    if type( serviceName ) is types.StringType:
      self._serviceNameList = string.split( serviceName, '.' )
    else:
      self._serviceNameList = serviceName

  def __getattr__( self, name ):
    return ServiceProxy( self._address, self._serviceNameList + [ name ] )

  def __call__( self, *args, **kwargs ):
    return serviceManager.callDistant( self._address, self._serviceNameList,
                                       *args, **kwargs )

  def start( self, *args, **kwargs ):
    return serviceManager.startDistant( self._address, self._serviceNameList,
                                        *args, **kwargs )

#
# handle SIGCHLD
#

def sigChldHandler( number, frame ):
  dbgmsg( 'Child dead' )
  try:
    pid, status = os.waitpid( 0, os.WNOHANG )
    dbgmsg( '(pid ' + str( pid ) + ' )' )
    # check if pid is an asynchronous request
    serviceManager.childDead( pid, status )
  except:
    pass
