from __future__ import print_function
from soma.singleton import Singleton
from brainvisa.data.temporary import manager as temporaryManager
from brainvisa.data.sqlFSODatabase import NoGeneratorSQLDatabase
from brainvisa.remote.server import BrainVISAServer


class DatabaseServer( Singleton ):
  def __singleton_init__( self ):
    super( DatabaseServer, self ).__singleton_init__()
    self.temporaries = []
  
  
  def initialize( self ):
    BrainVISAServer().initialize()
  
  
  def addDatabase( self, database ):
    remoteAccessURI = os.path.join( database.directory, 'remoteAccessURI' )
    if os.path.exists( remoteAccessURI ):
      print('WARNING: database', repr( database.directory ), 'has the following remote access:', open( remoteAccessURI ).read())
    else:
      if database.sqlDatabaseFile != ':memory:':
        try:
          dbfile = open( remoteAccessURI, 'w' )
          obj = Pyro.core.ObjBase()
          obj.delegateTo( NoGeneratorSQLDatabase( database ) )
          uri = BrainVISAServer().addObject( obj )
          temporaries.append( temporaryManager.createSelfDestroyed( remoteAccessURI ) )
          dbfile.write( str( uri ) )
          print('Serving database', repr( database.directory ), 'with URI', uri)
        except IOError:
          print('database', repr( database.directory ), 'cannot be used with server access')


  def serve( self ):
    BrainVISAServer().serve()
  
