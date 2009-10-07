# -*- coding: iso-8859-1 -*-
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

__author__ = "Julien Gilli <jgilli@nerim.fr>"
__version__ = "0.0"
__date__ = "October 11 2002"

"""This module contains the implementation of a network server as a
daemon. The document available at
http://www.enderunix.org/docs/eng/daemon.php has been used as a
reference to know the correct behavior of a Unix daemon.  This server
behaves classicaly : it waits for a request and then create a new
process when it receives one. The new process will handle the request,
complete the job and terminate.  """


import os
import sys
import signal
import neuroConfig
import socket
import networkUtils
import pickle
import neuroProcesses
import Protocol
if sys.platform != 'win32':
    import syslog
    import posix
    has_syslog = 1
    has_posix = 1
else:
    has_syslog = 0
    has_posix = 0

SERVER_PORT = Protocol.COMPILER_DAEMON_PORT
ABSOLUTE_PATH = os.path.abspath(sys.argv[0])
#LOCKFILE = os.path.join( os.path.dirname(ABSOLUTE_PATH), 'locks', 
#                         neuroConfig.sessionID )
# system-dependent path...
LOCKFILE = '/var/lock/subsys/brainvisad'

serverSocket = None



def set_lock_file():
    """Set a lock file to prevent multiple instances of
    the same server running."""

    global LOCKFILE
    print SERVER_PORT
    print LOCKFILE
    # Test if there is already a daemon running
    if os.path.exists( LOCKFILE ):
        # check if the PID in lockfile is actually running
        lock_file = open(LOCKFILE)
        pid = lock_file.read()
        lock_file.close()
        # ... (TODO)
        # There is a running daemon
        print >> sys.stderr, "A brainvisa daemon is already running, PID=", pid
        raise 'A brainvisa daemon is already running'

    try:
        lock_file = os.open(LOCKFILE, (os.O_CREAT | os.O_EXCL | os.O_RDWR))
        print "creation du fichier : " + LOCKFILE #neuroConfig.sessionID
        os.write(lock_file, str(neuroConfig.sessionID))
        
    except OSError:
        # no write access to lock file ? (not running as root)
        LOCKFILE = os.path.join( neuroConfig.temporaryDirectory,
                                 str(neuroConfig.sessionID) )
        try:
            lock_file = os.open(LOCKFILE, (os.O_CREAT | os.O_EXCL | os.O_RDWR))
            print "creation du fichier : " + LOCKFILE #neuroConfig.sessionID
            os.write(lock_file, str(neuroConfig.sessionID))
        
        except OSError:
            print >> sys.stderr, "Can't set lock file."
            raise


def remove_lock_file():
    """Remove the lock file. Called upon exit."""

    try:
        print "suppression du fichier : " + LOCKFILE
        os.unlink( LOCKFILE )
    except OSError:
        print "ERREUR de unlink : " + str(sys.exc_info())
        global has_syslog
        if has_syslog:
            syslog.syslog( syslog.LOG_DAEMON | syslog.LOG_ERR, \
                           "Unable to delete temporary lock file : "\
                           + LOCKFILE )

def hangup_handler(signum, frame):
    """This handler is called whenever the server process
    receive the HUP signal.
    It tries to lauch the program again with the same
    arguments.
    """

    clean_on_exit()
    if has_syslog:
        syslog.syslog(syslog.LOG_DEBUG | syslog.LOG_DAEMON,\
                      "Executing : " + ABSOLUTE_PATH)
    #    try:
    remove_lock_file()
    print >> sys.stderr, "execute : " + ABSOLUTE_PATH + " " + str(sys.argv)
    
    print >> sys.stderr, "execv"
    os.execv( os.path.join( os.path.dirname(ABSOLUTE_PATH),
                            "brainvisa" ), ["brainvisa", "-d"] )
 #   except OSError:
 #       print >> sys.stderr, "except !"
##         print >> sys.stderr, sys.exc_info()
##         syslog.syslog(LOG_ERR | LOG_DAEMON, \
##                       "Can't execv, restart failed, exiting.")
##         sys.exit(1)
    
def term_handler(signum, frame):
    """This handler is called whenever the server process
    receive the TERM signal.
    """
    
    clean_on_exit()
    remove_lock_file()
    if has_syslog:
        syslog.syslog(syslog.LOG_NOTICE | syslog.LOG_DAEMON,\
                      "BrainVISA daemon exiting.")
    sys.exit(0)


def daemonize():

    """Set up everything (working directory, umask, file descriptors,
    handlers, etc.) to make the program into a daemon, as specified at
    http://www.enderunix.org/docs/eng/daemon.php. This function must
    be called before any other, and returns nothing"""

    if (os.access(str(neuroConfig.sessionID), os.F_OK)):
        print >> sys.stderr, "Daemon already started, exiting."
        sys.exit(1)
        return 0
        
    signal.signal(signal.SIGHUP, hangup_handler)
    signal.signal(signal.SIGTERM, term_handler)
        
    # Detach the daemon from the controlling terminal
    try:
        pid = os.fork()
    except os.error:
        return 0
    if pid:
        sys.exit(0)
    else:
        set_lock_file()
        posix.setsid()
        
    try:
        sys.path.append(os.getcwd())
        os.chdir("/")

    except OSError:
        if has_syslog:
            syslog.syslog(syslog.LOG_ERR | syslog.LOG_DAEMON, \
                          "Unable to change directory to : " \
                          + "/")
        return 0

    # avoid a too permisive umask if the daemon is run as root
    os.umask(027)
    
    # close all file descriptors inherited from the father
    try:
        import resource
        try:
            resource_id = resource.RLIMIT_NOFILE
        except NameError:
            resource_id = resource.RLIMIT_OFILE
            
            fds_soft, fds_hard = resource.getrlimit(resource_id)
            # Under python, the close function raises OSError
            # upon failure (because here we try to close an unopened fd)
            for fd_soft in range(fds_soft):
                # FIXME : don't skip the fd number 2
                if fd_soft == 2 or fd_soft == 1: continue
                try:
                    os.close(fd_soft)
                except OSError:
                    pass
    except ImportError:
        try:
            max_open_files = os.sysconf('SC_OPEN_MAX')
        except OSError:
            max_open_files = 0
        for fd in range(max_open_files):
            try:
                os.close(fd)
            except OSError:
                pass
    try:        
        sys.stdin = open('/dev/null', 'r')
        #sys.stdout = open('/dev/null', 'w')
        #sys.stderr = open('/dev/null', 'w')
    except OSError:
        if has_syslog:
            syslog.syslog(syslog.LOG_WARNING | LOG_DAEMON, \
                          "Can't redirect standard streams to /dev/null.")
        return 0

    
def clean_on_exit():
    """Clean ressources used by the server, such as
    lock file, sockets, etc."""

    serverSocket.close()

def startServer():
    """Start listening for requests made by clients."""
    global serverSocket
    #    try:
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(('', SERVER_PORT))
    serverSocket.listen(5)
    
    while 1:
        connection, address = serverSocket.accept()
        pid = os.fork()
        if not pid:
            handle_request(connection, address)
    #   except:
    #       print "except"
    

def check_uid(uid):
    """Check if the uid "uid" can be used as an uid to run a process. Return true if so, false otherwise."""
    #FIXME: implement
    return 1

def get_and_set_uid_client(connection):
    """Get the uid of the client that performs the request,
    control if he has the right to perform it, and perform
    the uid change.
    connection is the communication channel through which
    the uid is passed, as a string.
    Return 0 if the uid change has been performed, other
    value otherwise.
    """
    uid = int(networkUtils.recv_data(connection))
    if check_uid(uid):
        os.setuid(uid)
        return 0
    return 1
    
def execute_process(connection):
    """Execute a process remotely, as requested by the client."""

    print "execute process"
    
    # acknowledge the request
    networkUtils.send_data(connection, "OKR")
    print "requete ok"
    
    get_and_set_uid_client(connection)
    print "changement d'uid"
    
    process_name = networkUtils.recv_data(connection)
    print "nom du processus a executer : " + str(process_name)
    
    socket_file = os.fdopen(connection.fileno(), "r")
    parameter_values_unpickler = pickle.Unpickler(socket_file)
    attribute_name = networkUtils.recv_data(connection)
    parameters = {}
    while attribute_name != "END":
        print "attribut : " + str(attribute_name)
         
        parameters[attribute_name] = parameter_values_unpickler.load()
        print "attribut : " + attribute_name + ", valeur : "\
              + "valeur : " + str(parameters[attribute_name])

        # acknowledge
        networkUtils.send_data(connection, "DUMMY")
        attribute_name = networkUtils.recv_data(connection)
        
    apply(neuroProcesses.defaultContext().runProcess, (process_name,), parameters)
    
def handle_request(connection, adress):

    """Handle the request made by the client at adress "adress"
    through the connection "connection" """

    requests = {
        "EXEC" : execute_process
        }

    request = networkUtils.recv_data(connection)
    print "requete recue : " + str(request)
    try:
        requests[request](connection)
    except KeyError:
        networkUtils.send_data("NOK")
    
    
        
    
    
