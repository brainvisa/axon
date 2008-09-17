# -*- coding: iso-8859-1 -*-

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

# TODO
'''

* logs:
  - contexte (à renvoyer par réseau)
  - log du serveur
  - log du scheduler

PROBLEMES DE CONCEPTION

* non-séparation client / serveur: les clients ont besoin d'un serveur associé
  qui tourne dans le même process qu'eux. Le serveur en question ne peut donc
  pas avoir les droits root et ne peut servir que des requêtes du même
  utilisateur. Ca veut dire que les "vrais" serveurs (qui vont vraiment
  traiter des requêtes extérieures) doivent tourner en plus du serveur du
  client (et écouter un autre port). C'est un peu ballot.

* callabcks envoyées par les services (serveur) vers le client (par ex. les
  sorties des commandes):
  - les services callbacks doivent tourner sur le même process que le client,
    ils ne doivent pas être forkés par le serveur du client. Ca doit donc
    forcément être des services Trusted. Dangereux, donc. Enfin en fait ils
    sont trusted sur un serveur qui appartient au client (pas root)
  - ces callbacks sont émises par le process qui traite la requête du côté
    serveur: le process fils (non-root) du serveur (root). Ce fils n'a
    (normalement) pas de boucle d'écoute, ce n'est pas un vrai serveur. Or
    le destinataire (serveur du client) va renvoyer des messages de changement
    d'état de cette requête callback. Ces messages seront en fait reçus par
    le serveur parent, qui lui, n'est pas au courant du deal, et va râler.
    On évite peut-être ça si on rend ces envois de messages "callback"
    synchrones, mais ça oblige le process qui traite à attendre une réponse
    du client avant de continuer: perte de temps.
  - peut-être que toutes ces callbacks devraient être émises sous la forme de
    syncRequestState (avec des états "user-defined"), mais dans cette
    configuration ça ne marcherait pas mieux je pense (ces requêtes d'état sont
    normalement émises par le serveur parent, pas par le fils)

* Les services synchrones n'ont pas de RequestID, donc pas d'état et pas de
  trace de l'adresse du client qui a demandé leur exécution. Ils ne peuvent
  donc renvoyer qu'un résultat final, et pas déclencher de callbacks sur le
  client (par ex. pour lui envoyer ses sorties standard et/ou d'erreur en plus
  d'un code de retour, un état de progression etc). Bon on pourrait aussi
  considérer que le returnValue contient tout et que le client n'a qu'à le
  décortiquer à la fin, mais c'est pas très homogène avec le mode asynchrone,
  et un service (traitement) "clientAware" ne peut pas se comporter de la même
  manière s'il est exécuté en mode synchrone ou asynchrone.

* Le scheduler donne une adresse de serveur sur lequel exécuter la requête.
  Mais il peut très bien répondre par l'adresse du client lui-même (et il ne
  s'en prive pas! et il a bien raison d'ailleurs). Dans ce cas la requête doit
  être exécutée en local sur le client. Le système actuel ne le permet pas: il
  s'appelle lui-même et tout se bloque. D'ailleurs les requêtes locales n'ont
  pas la même tête que les requêtes distantes. Il faudrait homogénéiser tout
  ça.
'
'''

from neuroProcesses import *
from brainvisa import services


class ProcessServices( services.ClientAwareService ):
    '''Process run/start services on server side'''

    def runProcess( self, distantID, managerAddress, procname, userLevel,
                    debug, *args, **kwargs ):
        print 'ProcessServices.runProcess: distantID=', distantID, \
              'managerAddress=',managerAddress, \
              'procname=', procname, 'userLevel=', userLevel, \
              'debug=', debug
        nc = NetworkExecutionContext( userLevel, debug )
        nc.remoteHost = managerAddress
        nc.requestID = distantID
        print 'args:', args
        print 'kwargs:', kwargs
        return nc.runProcess( procname, *args, **kwargs )


class NetworkExecutionContext(ExecutionContext):
  """This class is used to transparently communicate runtime
  informations (error messages, exceptions, etc.) to the client
  that requested a distributed execution of a process."""
  
  def __init__( self, userLevel = neuroConfig.userLevel, debug = None ):
      ExecutionContext.__init__( self, userLevel, debug )
      self.remoteHost = None
      self.requestID = None
      print 'NetworkExecutionContext created'
    
  def write(self, *messages, **kwargs):
      print 'NetworkContext write to:', self.remoteHost, ', id:', \
            self.requestID, ':', messages
      self.checkInterruption()
      linebreak = kwargs.get( 'linebreak', 1 )
      if messages:
          msg = string.join( map( str, messages ) )
          if linebreak: msg += '<br>'
          services.serviceManager.callDistant( self.remoteHost,
                                               'ClientCallbacks.contextWrite',
                                               self.requestID, msg, **kwargs )

  def log( self, *args, **kwargs ):
      print 'NetworkContext log:', messages
      if self._processStack:
          log = self._processStack[ -1 ].log
      else:
          log = neuroConfig.mainLog
      if log:
          services.serviceManager.callDistant( self.remoteHost,
                                               'ClientCallbacks.contextLog',
                                               self.requestID,
                                               *args, **kwargs )

class ClientContextCallbacks:

    class ClientCallbacks( services.TrustedService ):
        '''  Callback services must be Trusted services, otherwise they will
        be forked and run in a different process than the specified client.
        This is a conception mistake I think.
        '''

        def contextWrite( self, requestID, msg, **kwargs ):
            print 'contextWrite:', msg, ', id:', requestID
            # find context attached to requestID
            context = clientContextCallbacks.findContext( requestID )
            context.write( msg, **kwargs )

        def contextLog( self, requestID, *args, **kwargs ):
            # find context attached to requestID
            context = clientContextCallbacks.findContext( requestID )
            print 'contextLog:', args, kwargs
            context.log( *args, **kwargs )


    def __init__( self ):
        self._lock = threading.RLock()
        self.ids = {}
        self.contextcb = ClientContextCallbacks.ClientCallbacks()

    def findContext( self, id ):
        self._lock.acquire()
        try:
            id = services.serviceManager.requestID( id )
            c = self.ids.get( id )
            if c is not None:
                return c
        finally:
            self._lock.release()
        print 'findContext: specific context not found for req:', id
        print 'ids:', self.ids
        return defaultContext()

    def registerContext( self, id, context ):
        self._lock.acquire()
        try:
            self.ids[ id ] = context
        finally:
            self._lock.release()

    def _stateChanged( self, id ):
        if not isinstance( id, services.RequestID ):
            id = services.serviceManager._requestIDs[ id ]
        print '** callback for:', id.id, '***'
        state = services.serviceManager.requestState( id )
        # find context attached to requestID
        context = self.findContext( id )
        context.write( 'request state changed:', id.id, state )
        if state.state == services.RequestState.Exception:
            raise state.returnValue
        elif state.state == services.RequestState.Finished:
            context.log( 'Result:', state.returnValue )
        elif state.state == services.RequestState.Stopped:
            context.log( 'Process stopped' )
        # cleanup requests list
        if state.state in ( services.RequestState.Stopped,
                            services.RequestState.Finished, \
                            services.RequestState.Exception ):
            self._lock.acquire()
            try:
                del self.ids[ id ]
            finally:
                self._lock.release()

clientContextCallbacks = ClientContextCallbacks()

def _registerServices():
    manager = services.serviceManager
    if manager is None:
        port = 48000 + services.ports
        services.startServiceManager( '', port )
        manager = services.serviceManager
    # register to manager
    ce = clientContextCallbacks
    manager.registerService( 'ProcessServices', ProcessServices() )
    manager.registerService( 'ClientCallbacks', ce.contextcb )



_registerServices()

