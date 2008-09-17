
#--------------------------------------------------------------------------
# remoteToolkit v1.1
# 
#--------------------------------------------------------------------------


from pexpect import *
import os, sys
import os.path
import getpass
import threading, time, calendar
from datetime import datetime
import re, string, math
import xml.parsers.expat
import Pyro.core
import pxxssh
from qt import *

#--------------------------------------------------------------------------
def sshSession(host, login, password=''):
  """
  Opens a ssh tunnel to the specified location.
  
  @param host: The remote machine to log on.
  @param login: The login to be used.
  @param password: The password to be used, leave empty if using public key authentication
  @return: A pexpect.spawnObject that may be considered as a remote shell.
  """

  
  remoteShell = pxxssh.pxssh()
  if not remoteShell.login (host, login, password):
    return None 
  else:
    return remoteShell

#--------------------------------------------------------------------------
class ClusterNode:
  """
  A machine registered in a cluster.
  """
  
  def __init__(self, address, policy=1.0):

    self.address = address
    """
    Node address on the network.
    """
    
    self.session = None
    """
    A virtual remote shell on the cluster node. 
    @see: L{self.sshSession}
    """
    
    self.cores_nb = 0
    """
    Number of processors available on the cluster node.
    """
    
    self.tokens = 0
    """
    Total number of tokens available on the cluster node.
    
    The tokens stand for the number of tasks that are allowed 
    to run at the same time on the machine.
    
    @note: the tokens number is based both on the number of cores and the 
    policy applied to the node.
    
    @see: L{self.cores_nb}, L{self.policy}, L{self.setPolicy}
    """
    
    self.connected = False
    """
    Flag to know if a valid ssh tunnel exists between the localhost and the cluster node.
    """
    
    self.last_workload = 0.0
    self.policy = policy
    """
    Floating number used to modify the number of tasks allowed to run at the same time on the machine.
    
    @note: policy is can be defined in the constructor. It may be changed later with L{setPolicy}.
    @see: L{self.cores_nb}, L{self.tokens}, L{self.setPolicy}
    """
    
  def connect(self, login, password):
    """
    Connects the localhost to the node through a ssh tunnel.
    Retrieves the number of processors of the machine.
    
    @see: L{self.session}, L{self.cores_nb}
    """
    
    try:
      
      self.session = sshSession(self.address, login, password)
  
      # gets the number of cores available
      self.session.sendline('grep processor /proc/cpuinfo | wc -l')
      self.session.expect('\d\r\n')
      
      cores = self.session.after
      self.cores_nb = string.atof(cores)
      
      self.setPolicy(self.policy)
      
      self.connected = True
    
    except:
      pass
  
  def disconnect(self):
    """
    Disconnects the ssh connection.
    """
  
    try:
      self.session.logout()
    except:
      pass
      
    self.connected = False            
  
  def setPolicy(self, policy):
    """
    tokens = cores * policy
    
    @see: L{self.cores_nb}, L{self.tokens}, L{self.policy}
    """
    
    self.policy = policy
    self.tokens = int(self.cores_nb * self.policy)
  
  def getTokens(self):
    """
    @return: L{self.tokens}
    """
    
    return self.tokens
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
  def probe(self):
    """
    Gets the load average of the last minute which id retrieved from /proc/loadavg

    @return: the number of tokens left to the node after the loadaverage have been subtracted.
    """ 
    
    # gets the /proc/loadavg file contents
    self.session.sendline('cat /proc/loadavg')    
    case = self.session.expect(['(\d\.\d\d\s){3}.*\r\n', EOF, TIMEOUT]) 

    # a TIMEOUT or a weird behavior may occur if the host is very busy
    # in that case, a arbitrary high load value will be returned so that the host will be ignored
    if case <> 2:
    
      try:
        loadavg_line = self.session.after
    
        regexp = re.compile('\S+')
        loadavg_all = regexp.findall(loadavg_line)
    
        workload = string.atof(loadavg_all[0])
        
        penalty = int((workload - self.last_workload)*10)
        self.last_workload = workload
        
        #print workload, ':', math.ceil(workload), '-', penalty, '=', self.tokens - math.ceil(workload) - penalty
        
        fractional, integer = math.modf(workload)
        
        if fractional >= 0.3:
          rounded_workload = math.ceil(workload)
        else:
          rounded_workload = math.floor(workload)
        
        return self.tokens - rounded_workload
        #return self.tokens - math.ceil(workload) - penalty
              
      except:
        print self.session.before, self.session.after

    self.connected = False
    return 0
                        
  def cores(self):
    """
    @return: L{self.cores_nb}
    """
    
    return self.cores_nb
  
  def address(self):
    """
    @return: L{self.address}
    """
    
    return self.address
                                                                                                  
  def isAlive(self):
    """
    Tests if the node is alive by pinging the remote machine.
    
    @attention: different from L{self.isConnected}
    @return: True or False
    """
    
    shell = spawn ('ping %s -c 1'%self.address)

    case = shell.expect(['ping statistics ---','unknown host', 'Unreachable', TIMEOUT], timeout = 4)

    if case == 0:
      return True
    else:
      return False
  
  def isConnected(self):
    """
    @return: True or False
    @see: L{self.connected}
    """
    
    return self.connected  
        
  def __str__(self):
    return self.address 

#--------------------------------------------------------------------------
class CentralizedClusterManager:
  """
  The goal of this class is to be able to select machines among a collection of computers
  on which it is possible to launch tasks without overloading them. 
  
  Everything from probing the computers, sorting them according to their availability and 
  waiting for ressources to be freed when necessary is handled transparently.
  
  @note:
  The cluster handler may be used in different modes:
    - Locally with a single check of the workload.
    - May be used in server mode which provides a periodical update of the workload.
    - Ultimately, the server is to be run as a Pyro server to be available as a Web Services Server.
  """
  
  def __init__(self, configPath=None, policyPath=None, homedir=None):
    """
    Retrieves the computer collection and makes a single probe of each.
    
    The cluster manager is not started in server mode by default but can be activated later through the startServer method.
    """
    self.registered_cNodes = []
    """
    Nodes defined in the config file.
    """
    
    self.eligible_cNodes   = []
    """
    Nodes from the config file that are alive and connected.
    """
    
    self.dead_cNodes       = []
    """
    Nodes from the config file that are either dead or not connected.
    """
    
    self.registered_cNodes_nb = 0
    """
    Number of registered_cNodes.
    
    @see: L{CentralizedClusterManager.registered_cNodes}
    """
    
    self.eligible_cNodes_nb      = 0
    """
    Number of eligible_cNodes.
    
    @see: L{CentralizedClusterManager.eligible_cNodes}
    """
    
    self.dataLck = threading.Lock()
    
    self.configPath = configPath 
    """
    Custom path for the cluster configuration file.
    """      

    self.policyPath = policyPath

    self.homedir = homedir
    """
    Custom path for the policy configuration file.
    """      

    self.clusterRessources = {}
    """
    The computer IPs are associated with a integer which is the number of tokens available::
        {'ip':ressources}
        
    @see: L{ClusterNode.tokens}, L{ClusterNode.policy}, L{ClusterNode.setPolicy}
    """
    
    self.sorted_cNodes = []
    """
    Sorted list of IPs according to the computer ressources availability.
    @note: the computer whose ressources are the greater is last in the list.
    """
    
    self.__write('registering cluster nodes...')
    self.update()   
    
    self.serverMode = False
  
  def update(self):
    """
    Parses the configuration file and updates the nodes lists accordingly.
    
    @see: L{CentralizedClusterManager.registered_cNodes}
    """
    
    self.dataLck.acquire()

    nodeListAsStringList = lambda nodeList: [str(cNode) for cNode in nodeList]
    
    config_cNodes =  []
    removed_cNodes = []
    
    conf = ClusterConfig(self.configPath, self.policyPath, self.homedir)
    
    config_cNodes = conf.getNodes()
    
    # tests if new nodes have been added to the cluster
    for new_cNode in config_cNodes:
               
      if not nodeListAsStringList(self.registered_cNodes).__contains__(str(new_cNode)):
        self.__write('adding \'%s\' to cluster'%str(new_cNode))
        self.registered_cNodes.append(new_cNode)
        
        if new_cNode.isAlive():
          if not new_cNode.isConnected(): new_cNode.connect(UserInfos.login, UserInfos.password)

    
    # tests if nodes have been removed from the cluster
    for old_cNode in self.registered_cNodes:
     
      if not nodeListAsStringList(config_cNodes).__contains__(str(old_cNode)):
        self.__write('\'%s\' has been removed'%str(old_cNode))
          
        try: old_cNode.disconnect()  
        except: pass
          
        removed_cNodes.append(old_cNode)
        
    for removedNode in removed_cNodes:
      try:
        self.registered_cNodes.remove(removedNode)
        del self.clusterRessources[removedNode]
      except: 
        pass
    
    # updates nodes policies
    for cNode in self.registered_cNodes:
      for group in conf.getGroups().keys():
      
        node_list = conf.getGroups()[group]
        
        if nodeListAsStringList(node_list).__contains__(str(cNode)):
          group_policy = conf.getPolicies()[group]
          cNode.setPolicy(group_policy)
    
    self.registered_cNodes_nb = len(self.registered_cNodes)
    
    self.dataLck.release()
    self.__refresh()
    self.__snapshot()
        
  def __refresh(self):
    """
    Checks if the registered nodes are alive and connected and updates the nodes lists accordingly.
    
    @see: L{CentralizedClusterManager.eligible_cNodes}, L{CentralizedClusterManager.dead_cNodes}    
    """

    self.dataLck.acquire()
   
    self.eligible_cNodes   = []
    self.dead_cNodes       = []
    
    for cNode in self.registered_cNodes:      
      isEligible = True

      if cNode.isAlive():
        if not cNode.isConnected():
          cNode.connect(UserInfos.login, UserInfos.password)
          if not cNode.isConnected():
            self.__write('SSH connection impossible on \'%s\''%str(cNode))
            isEligible = False
      else:
        self.__write('\'%s\' is unreachable'%str(cNode))
        isEligible = False
        
      if isEligible:
        self.eligible_cNodes.append(cNode)
      else:
        self.dead_cNodes.append(cNode)
        
        try: del self.clusterRessources[cNode] 
        except: pass
          
        try: cNode.disconnect()  
        except: pass
    
    self.eligible_cNodes_nb = len(self.eligible_cNodes)            
                                        
    self.dataLck.release()  
                         
  def closeSessions(self):
    """
    Close all the ssh sessions.
    """
    
    for cNode in self.registered_cNodes:
      cNode.disconnect()
  
  def __sortNodes(self):
    """
    Sorts the list containing the computer IPs according to their ressources availability.
    """
    
    IP_list = []
  
    for cNode in self.clusterRessources.keys():
      if len(IP_list) == 0:
        IP_list.append(cNode)
      else:
        for ip in IP_list:
          if self.clusterRessources[cNode] < self.clusterRessources[ip]:
            IP_list.insert(IP_list.index(ip), cNode)
            break
        else:
          IP_list.append(cNode)
          
    return IP_list
                    
  def __snapshot(self):
    """
    Probes all the computers of the cluster and stores their IPs in the sorted list.
    
    @see: Instance variable details of L{CentralizedClusterManager.sorted_cNodes}.
    """   

    self.dataLck.acquire()

    for cNode in self.eligible_cNodes:
      self.clusterRessources[cNode] = cNode.probe()
  
    self.sorted_cNodes = self.__sortNodes()
    
    self.dataLck.release()
  
  def getHost(self):
    """
    Gets the best host to execute a task on.
    
    @return: The best node on the cluster from the nodes sorted list.
    @note: 
    If all nodes are too busy, the attribution of hosts is blocked during
    90 seconds, after which another snapshot will be taken and another
    attempt to get a host undertaken.
    @see: Instance variable details of L{CentralizedClusterManager.sorted_cNodes}.
    """
    
    #self.dataLck.acquire()
    
    try:
      best_host = self.sorted_cNodes[len(self.sorted_cNodes)-1]
    except IndexError:
      self.__write('no active node is registered on the cluster, returning \'localhost\'')    
      #self.dataLck.release()
      return 'localhost'
      
    #checks if the node is still up and running between 2 snapshots
    best_host.probe() #probe just to update to connection flag
    
    if not best_host.isConnected():
      self.sorted_cNodes.pop()
      #self.dataLck.release()
      return self.getHost()
    
    oneCore = 1
    
    if self.clusterRessources[best_host] > 0:
      self.clusterRessources[best_host] -= oneCore
      self.sorted_cNodes = self.__sortNodes()
      #self.dataLck.release()
    else: 
      self.__write('cluster overloaded, blocking requests...')    
      time.sleep(90)
      #self.dataLck.release()
      self.__write('unblocking requests...')    
      self.__snapshot()
      return self.getHost()
          
    return str(best_host)
 
  def loadAverage(self):
    """
    Computes the overall workload average of the cluster.
    
    @return: percentage of the cluster usage.
    """
    
    total_load = 0.0
    total_tokens = 0.0
    
    self.dataLck.acquire()
                  
    for cNode in self.eligible_cNodes:
      total_load += self.clusterRessources[cNode]
      total_tokens += cNode.getTokens()
      
    self.dataLck.release()
    
    try:
      return (1-total_load/total_tokens)*100
    except ZeroDivisionError:
      return 100.0
    
  def activeNodes(self):
    """
    @return: The L{self.eligible_cNodes} list
    """
    
    self.dataLck.acquire()
    tmpList = [str(cNode) for cNode in self.eligible_cNodes]
    #self.__write(tmpList)    
    self.dataLck.release()
    
    return tmpList
    
  def registeredNodes(self):
    """
    @return: The L{self.registered_cNodes} list
    """
    
    self.dataLck.acquire()
    tmpList = [str(cNode) for cNode in self.registered_cNodes]
    #self.__write(tmpList)
    self.dataLck.release()
       
    return tmpList
  
  def ressources(self):
    """
    @return: string representing the cluster state
    """
     
    self.dataLck.acquire()
    
    """    
    displayed_ressources = ""

    tmpList = [cNode for cNode in self.sorted_cNodes]
    tmpList.reverse()

    
    for node in tmpList:
      displayed_ressources = displayed_ressources + str(node) + '\t:\t' + str(self.clusterRessources[node]) + '\n'
    
                str(node) + '\t:\t' + str(self.clusterRessources[node]) + '\n' for node in tmpList
    """
    ressources = {}
    
    for key in self.clusterRessources:
      ressources[str(key)] = self.clusterRessources[key]
    
    sortedList = [str(cNode) for cNode in self.sorted_cNodes]
    
    self.dataLck.release()

    return ressources, sortedList
  
  def __periodicalUpdate(self, interval):
    """
    Thread taking snapshots of the cluster at regular intervals.
    Active only when the server mode is on.
    
    @param interval: Interval between the snapshots.
    """
     
    while 1:
      time.sleep(interval)
      if self.serverMode == True:
        self.update()
        self.__write('cluster used at %d'%(self.loadAverage())+'%'+' - %d/%d'%(self.eligible_cNodes_nb,self.registered_cNodes_nb))
      else:
        self.__write('control thread terminated.')    
        break
  
  def __write(self, message):
    """
    Writes a message prefixed with the current time on the server console.
    """
    
    tic = datetime.now()
    print "%02d:%02d:%02d - %s"%(tic.hour, tic.minute, tic.second, message)
  
  def startServer(self, interval):
    """
    Enables the server mode.
    
    @param interval: Interval between the snapshots made by the server.
    """
    
    self.serverMode = True
    update_t = threading.Thread( target = self.__periodicalUpdate, args = (interval,) )
    update_t.start()
  
  def ping(self):
    """
    Used to test if the server is responding.
    
    @returns: The string 'pong' to the client.
    @note: print the string 'ping' on the server console.
    """
    
    print 'ping'
    return 'pong'


#--------------------------------------------------------------------------
class ClusterConfig:
  """
  Parses the cluster configuration file which is a xml file.
  
  @note: the xml file describing the cluster has the following structure::
  
    <cluster>
      <group id="ClusterGroup1" policy="0.5">
        <workstation name="pc1"/>
        <workstation name="pc2"/>
        ...
      </group>
      <group id="ClusterGroup2" policy="2.0">
        <workstation name="pc3"/>
        <workstation name="pc4"/>
        <workstation name="pc5"/>
        ...
      </group>
      ...
    </cluster>
  """
  
  def __init__(self, configPath=None, policyPath=None, homedir=None):
    
    self.groups_workstations = {}
    """
    Dictionnary associating the cluster group names with the list of machines they contain.
    """
    
    self.groups_policies = {}
    self.homedir = homedir
    """
    Dictionnary associating the cluster group names with the policy to apply to their machines.
    """

    if configPath == None or policyPath == None:
      defconfigPath, defpolicyPath = self.__getDefaultPath()
      if configPath == None:
        configPath = defconfigPath
      if policyPath == None:
        policyPath = defpolicyPath
    
    configFile = open(configPath, 'r')
    policyFile = open(policyPath, 'r')
    
    configXML = configFile.read()
    policyXML = policyFile.read()
    
    configFile.close()
    policyFile.close()

    p_cluster = xml.parsers.expat.ParserCreate()
    p_policy  = xml.parsers.expat.ParserCreate()

    p_cluster.StartElementHandler = self.__buildCluster
    p_policy.StartElementHandler  = self.__buildPolicy

    
    try:
      p_policy.Parse(policyXML, 1)
      p_cluster.Parse(configXML, 1)
    except xml.parsers.expat.ExpatError:
      configPath, policyPath = self.__getDefaultPath(True)
      self.__init__(configPath, policyPath)
    
    """
    for group_name in self.groups_workstations.keys():
      for station in self.groups_workstations[group_name]:
        print group_name, station, station.isConnected(), station.getTokens()
    """

  def __buildCluster(self, name, attrs):
    """
    Fills the data structures with the parsing results of the configuration file.
    
    @see: L{ClusterConfig.groups_workstations}, L{ClusterConfig.groups_policies}
    """
    
    if name == 'group':
      self.group_id = str(attrs['id'])
      #self.group_policy = string.atof(attrs['policy'])
      
      self.groups_workstations[self.group_id] = []
      if not self.groups_policies.has_key( self.group_id ):
        self.groups_policies[self.group_id] = self.group_policy
      
    if name == 'workstation':
      workstation_id = str(attrs['name'])

      if not self.groups_workstations.has_key(self.group_id):
        self.groups_workstations[self.group_id] = []
      self.groups_workstations[self.group_id].append(ClusterNode( workstation_id, self.groups_policies[self.group_id] ))

  def __buildPolicy(self, name, attrs):
    """
    Fills the data structures with the parsing results of the configuration file.
    
    @see: L{ClusterConfig.groups_workstations}, L{ClusterConfig.groups_policies}
    """
    
    if name == 'group':
      self.group_id = str(attrs['id'])

    if name == 'schedule':
      self.start = str(attrs['start'])
      self.end = str(attrs['end'])
      self.group_policy = string.atof(attrs['policy'])
      
      # retrieves schedule
      current_time = datetime.now()
      
      timeformat = re.compile(':')
      
      start_hour, start_minute = timeformat.split(self.start)
      start_time = datetime(current_time.year, current_time.month, current_time.day, 
                            string.atoi(start_hour), string.atoi(start_minute), 0, 0 )
                            
      end_hour, end_minute = timeformat.split(self.end)                     
      end_time = datetime(current_time.year, current_time.month, current_time.day, 
                            string.atoi(end_hour), string.atoi(end_minute), 0, 0 )
      
      # the end time may actually be the next day  
      if start_time >= end_time:
        day = datetime(2007, 7, 10, 0, 0, 0, 0 )
        nextday = datetime(2007, 7, 11, 0, 0, 0, 0 )
        oneday = nextday - day
        
        end_time = end_time + oneday
        
      if current_time < end_time and current_time >= start_time:
        self.groups_policies[self.group_id] = self.group_policy
      else:
        try:
          self.groups_policies[self.group_id]
        except KeyError:
          self.groups_policies[self.group_id] = 1.0

  def __getDefaultPath(self, forceDefault=False):
    """
    If no path is given for the configuration file, some default locations are probe for it.
    """

    if self.homedir is None:
      homedir = os.getenv( 'HOME' )
    else:
      homedir = self.homedir
    cluster_defaultPath = os.path.join(homedir, "cluster.xml")
    policy_defaultPath  = os.path.join(homedir, "policy.xml")

    if (not os.path.exists(cluster_defaultPath) and not forceDefault) or forceDefault:
      defaultConfig = "<?xml version=\"1.0\"?>\
      \n<cluster>\
      \n\t<group id=\"default\">\
      \n\t\t<workstation name=\"localhost\"></workstation>\
      \n\t</group>\
      \n</cluster>"
      configFile = open(cluster_defaultPath, 'w')
      configXML = configFile.write(defaultConfig)  
      configFile.close()
    
    if (not os.path.exists(policy_defaultPath) and not forceDefault) or forceDefault:
      defaultConfig = "<?xml version=\"1.0\"?>\
      \n<cluster>\
      \n\t<group id=\"default\">\
      \n\t\t<schedule start=\"00:00\" end=\"00:00\" policy='1.0'></schedule>\
      \n\t</group>\
      \n</cluster>"
      print "A default cluster policy file has just been created. It may not work with the current cluster configuration file"
      configFile = open(policy_defaultPath, 'w')
      configXML = configFile.write(defaultConfig)  
      configFile.close()
      
    return cluster_defaultPath, policy_defaultPath
    
  def getNodes(self):
    """
    @return: the node list defined in the file, independently from their groups.
    """
    
    cNodes = []
    
    for nodes_list in self.groups_workstations.values():
      cNodes.extend(nodes_list)
      
    return cNodes
  
  def getGroups(self):
    """
    @return: L{ClusterConfig.groups_workstations}
    """
    
    return self.groups_workstations
    
  def getPolicies(self):
    """
    @return: L{ClusterConfig.groups_policies}
    """
   
    return self.groups_policies
    
                            
#--------------------------------------------------------------------------
class UserInfos:
  """
  Stores informations about the user needed to open ssh tunnels.
  """

  login = None
  password = None

  def __init__(self):
    """
    Gets user login and password.  
      - The login is retrieved automatically.
      - The password is asked if needed.
    """
		
    UserInfos.login = os.getenv('USER') # os.getlogin() is very bad
    
    if self._needPass():
      self._askPass()
    elif UserInfos.password is None:
      UserInfos.password = ''
  
  def _needPass(self):
    """
    Checks if a password is needed or not to open a ssh tunnel.
    
    @return: True or False
    """

    if UserInfos.password <> None:
      return False

    #print "Identifying authentification method..."
    # tests if a password is needed by trying to open a tunnel with a false password.
    # if the connection was opened, it means no password was asked...
    remoteShell = sshSession('localhost', self.login, 'apasswordthatshouldnotbeyours')
    if remoteShell is not None:
    	return False
    else:
    	return True
      
  def _checkPass(self, password):
    """
    Checks if the given password is valid or not.
    
    @param password: the password to check.
    @return: True or False
    """
    
    #print "Checking ssh password..."
    remoteShell = sshSession('localhost', self.login, password)
    if remoteShell is not None:
    	return True
    else:
    	return False
      
  def _askPass(self): 
    pass

#--------------------------------------------------------------------------
class UserInfosQT( UserInfos ):
  """
  Stores informations about the user needed to open ssh tunnels.
  Opens a QInputDialog to ask for the password.
  
  @attention: The class launches a QApplication and there should be no more than one in a
  single Python interpreter. 
  """
   
  def __init__(self):  
    
    app=QApplication(['pass'])
    UserInfos.__init__(self)
  
  def _askPass(self): 
    password, accept = QInputDialog.getText("OpenSSH Password", "Enter your password:", QLineEdit.Password)
    
    if not accept:
      sys.exit(0)
    
    if not self._checkPass(str(password)):
      self._askPass()
      return False
     
    UserInfos.password = str(password)      
    return True 

#--------------------------------------------------------------------------
class UserInfosShell( UserInfos ):
  """
  Stores informations about the user needed to open ssh tunnels.
  Asks for the password on a shell. 
  """
  
  def __init__(self):  
    UserInfos.__init__(self)
    
  def _askPass(self): 
    """
    Asks for user password and checks its validity.
    
    @see: L{UserInfos._checkPass}
    """
    
    password = getpass.getpass('Enter Password: ')
    
    UserInfos.password = password
    
    if not self._checkPass(UserInfos.password):
      self._askPass()


