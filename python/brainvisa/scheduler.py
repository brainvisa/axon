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

#
#   Copyright (C) 2003 IFR 49
# 
#   This software and supporting documentation were developed by
#       IFR 49
#       4 place du General Leclerc
#       91401 Orsay cedex
#       France
#

from brainvisa import services
import  time, threading
import os, sys, socket, struct, string

class ServerInfo:
    def __init__( self, address ):
        self.address = address
        self.services = services.serviceManager.callDistant( \
            address, 'admin.servicesList', yourAddress=address )
        print 'services for', address, ':', self.services


home = os.getenv( 'HOME' )
if home:
    conf = os.path.join( home, '.brainvisa', 'schedulerconf.py' )
    if os.path.isfile( conf ):
        p = sys.path
        sys.path.insert( 0, os.path.join( home, '.brainvisa' ) )
        try:
            import schedulerconf
        finally:
            sys.path = p
            del p
    del conf
del home


class Scheduler( services.TrustedService ):
    def __init__( self ):
        self.servers = {}
        try:
            serv = schedulerconf.servers
            if serv:
                for x in serv:
                    a = ( x[0], x[1] + services.ports )
                    self.servers[ a ] = ServerInfo( a )
        except:
            pass
        self._lock = threading.RLock()
        self.currentserver = 0
        # run a broadcast-listening thread
        brd = threading.Thread( target = self._broadcastListener )
        brd.start()

    def schedule( self, servicename ):
        name = string.split( servicename, '.' )[0]
        self._lock.acquire()
        try:
            inis = self.currentserver
            #print 'scheduling:', servicename
            if len( self.servers ) == 0:
                print '<no servers>'
                return None
            serv = None
            notfound = 0
            while serv is None and notfound == 0:
                serv = self.servers.keys()[ self.currentserver ]
                self.currentserver = ( self.currentserver + 1 ) \
                                     % len( self.servers )
                s = self.servers[ serv ]
                if name in s.services:
                    print 'Scheduler: send', servicename, 'to:', serv
                    return serv
                serv = None
                if self.currentserver == inis:
                    notfound = 1
        finally:
            self._lock.release()
        print '<no matching server found>'
        return None

    def _broadcastListener( self ):
        print '_broadcastListener listening'
        #manager = services.serviceManager
        port = 45010
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('',port))
        while 1:
            x, addr = sock.recvfrom( 4 )
            print 'message from:', addr
            while len( x ) < 4:
              x += sock.recv( 4 - len( x ) )
            port = socket.ntohl( struct.unpack( 'l', x )[0] )
            addr = ( addr[0], port )
            print 'new server:', addr
            try:
                si = ServerInfo( addr )
                self.servers[ addr ] = si
                print 'servers list is now:', self.servers
            except:
                print 'could not retreive server info'
                pass

def findScheduler():
    try:
        sched = schedulerconf.scheduler
        return ( sched[0], sched[1] + services.ports )
    except:
        return ('', 45000+services.ports )


if __name__ == '__main__':
    serviceManager = services.startServiceManager( *findScheduler() )
    serviceManager.registerService( 'scheduler', Scheduler() )
    while 1:
        time.sleep( 100 )

