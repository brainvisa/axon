# -*- coding: utf-8 -*-

from shutil import rmtree

from neuroProcesses import *
from brainvisa.registration import getTransformationManager
from brainvisa.configuration import neuroConfig
from brainvisa.data import neuroHierarchy

userLevel = 2

signature = Signature(
  'number_of_subjects', Integer(),
  'number_of_sulci', Integer(),
  'test_database_directory', WriteDiskItem( 'Directory', 'Directory' ),
)

def initialization( self ):
  self.number_of_subjects = 5
  self.number_of_sulci = 30
  self.test_database_directory = '/tmp/axon_test_database'


def create_uuid( id ):
  if not isinstance( id, tuple ):
    id = ( id, )
  a, b, c, d, e = ( ( 0, 0, 0, 0 ) + id )[ -5: ]
  result = ( '0' * 7 + str( a ) )[ -8: ] + '-' + \
    ( '0' * 3 + str( b ) )[ -4: ] + '-' + \
    ( '0' * 3 + str( c ) )[ -4: ] + '-' + \
    ( '0' * 3 + str( d ) )[ -4: ] + '-' + \
    ( '0' * 11 + str( e ) )[ -12: ]
  return result


def create_referential( registration_directory, label, referential_id ):
  referential_uuid = create_uuid( referential_id )
  referential = open( os.path.join( registration_directory, referential_uuid + '.referential' ), 'w' )
  d = { 'uuid': referential_uuid, 'name': label }
  print >> referential, 'attributes =', repr( d )



def create_transformation( registration_directory, transformation_id, source_id, destination_id ):
  transformation_uuid = create_uuid( transformation_id )
  source_uuid = create_uuid( source_id )
  destination_uuid = create_uuid( destination_id )
  trm = open( os.path.join( registration_directory, transformation_uuid + '.trm' ), 'w' )
  print >> trm, '0 0 0\n1 0 0\n0 1 0\n0 0 1'
  trm_minf = open( os.path.join( registration_directory, transformation_uuid + '.trm.minf' ), 'w' )
  d = { 'uuid': transformation_uuid, 'source_referential': source_uuid, 'destination_referential': destination_uuid }
  print >> trm_minf, 'attributes =', repr( d )



def create_test_database( self ):
  database_directory = os.path.join( self.test_database_directory.fullPath(), 'database' )
  for database in neuroConfig.dataPath:
    if database.directory == database_directory:
      return neuroHierarchy.databases.database( database.directory )

  if not os.path.exists( database_directory ):
    os.makedirs( database_directory )
  database_settings = neuroConfig.DatabaseSettings( database_directory )
  database_settings.builtin = True
  database = neuroHierarchy.SQLDatabase( database_settings.expert_settings.sqliteFileName, database_directory, 'brainvisa-3.1.0', settings=database_settings )
  neuroHierarchy.databases.add( database )
  neuroConfig.dataPath.insert( 1, database_settings )
  return database

def execution( self, context ):
  # Create test databases
  database = self.create_test_database()
  registration_directory = os.path.join( database.directory, 'transformation_manager', 'registration' )
  if os.path.exists( registration_directory ):
    rmtree( registration_directory )
  os.makedirs( registration_directory )
  
  # Fill test database
  transformations = {}
  create_referential( registration_directory, 'Template for all subjects', 0 )
  for s in xrange( 1, self.number_of_subjects + 1 ):
    create_referential( registration_directory, 'Subject ' + str( s ), s )
    create_transformation( registration_directory, ( 1, 0, 0, 0, s ), s, 0 )
    for s2 in xrange( s+1, self.number_of_subjects + 1 ):
      create_transformation( registration_directory, ( 1, 0, 0, s, s2 ), s, s2 )
    for n in xrange( 1, self.number_of_sulci + 1 ):
      create_referential( registration_directory, 'Sulci ' + str( n ) + ' of subject ' + str(s), ( s, n  ) )
      create_transformation( registration_directory, ( 1, 0, 1, s, n ), s, ( s, n ) )

  database.clear()
  database.update( context=context )  
      
  # Run tests
  for path in getTransformationManager().findPaths( create_uuid( ( 1, 1 ) ), create_uuid( ( self.number_of_subjects, self.number_of_sulci ) ) ):
    context.write( path )
    context.write()