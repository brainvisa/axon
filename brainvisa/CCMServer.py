#!/usr/bin/env python

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
import Pyro.core, Pyro.naming
import remoteToolkit
import threading, time
import sys, os
from remoteToolkit import *
# import cProfile

#----------------------------------------------------------------------
class CentralizedClusterManager(Pyro.core.ObjBase, remoteToolkit.CentralizedClusterManager):
  """
  Pyro implementation of the CentralizedClusterManager class.
  """
  
  def __init__(self, configPath):
    """
    Calls the remoteToolkit.CentralizedClusterManager and Pyro.core.ObjBase constructors to make 
    the class CentralizedClusterManager callable through a Pyro server.
    """
    
    remoteToolkit.CentralizedClusterManager.__init__(self, configPath)
    Pyro.core.ObjBase.__init__(self)

#----------------------------------------------------------------------
class CCMServer:
  """
  Pyro server having an instance of CentralizedClusterManager.
  """
  
  def __init__(self, nameServer, configPath):
    """
    Initializes the Pyro Server.
    
    @param nameServer: Pyro server IP.
    """
    
    self.nameServer = nameServer
    """
    Pyro server IP.
    """
    
    self.configPath = configPath
    """
    File naming the machines that are part of the cluster.
    """
    
    self.cluster = None
    """
    CentralizedClusterManager instance on the Pyro server.
    """
    
  def startServices(self):
    """
    Enables the server mode for the CentralizedClusterManager instance.
    """
    
    self.cluster = Pyro.core.getProxyForURI("PYRONAME://clusterManager")
    self.cluster.startServer(30)

  def start(self):
    """
    Initializes and starts the CCMServer.
    """
    
    Pyro.core.initServer()
    ns = Pyro.naming.NameServerLocator().getNS()
    print 'Searching for Name Server...'

    daemon = Pyro.core.Daemon(host=self.nameServer, port=9090)
    daemon.useNameServer(ns)

    remoteToolkit.UserInfosQT()  
    cluster = daemon.connect(CentralizedClusterManager(self.configPath),"clusterManager")

    services_t = threading.Timer( 1.0, self.startServices) 
    services_t.start()

    print "Server running..."
 
    try:
      daemon.requestLoop()
    except:
      print "Stopping all services..."
      self.cluster.stopServer(0)
      self.cluster.closeSessions()
      print "Server terminated."
      
#----------------------------------------------------------------------
#main

if __name__ == "__main__":
   
  ns = 'localhost'
  cf = None
  
  for arg in sys.argv:
    if arg == '-h':
      print "Usage: python ccm-server [-h] [-n nameserver] [-f configfile]"
      print "  where -s = Pyro server address"
      print "        -f = non-default cluster configuration file"
      print "        -h = print this help"
      sys.exit(0)
    if arg == '-s':
      i = sys.argv.index(arg)
      ns = sys.argv[i+1]
    elif arg == '-f':
      i = sys.argv.index(arg)
      cf = sys.argv[i+1]
  
  print 'Server name: %s'%ns
  print 'Config file: %s'%cf
  
  #try:
  server = CCMServer(ns, cf)
  #cProfile.run('server.start()', 'serverprof')
  server.start()
  #except:
  #  print "Error, try -h to see help."
    
