import neuroConfig, types

def setDataBase( mydb ):
  if type( mydb ) is not types.StringType:
    if len( mydb ) < 2:
      dbname = mydb[0]
      dbhierarchy = None
    else:
      dbname, dbhierarchy = mydb
  else:
    dbname = mydb
    dbhierarchy = None
  existing = False
  newdbdirs = []
  for x in neuroConfig.options._addDatabaseDirectory:
    if x[0] == dbname and x[1] == dbhierarchy:
      existing = True
      newdbdirs.append( x[:-1] + ( 1, ) )
    else:
      newdbdirs.append( x[:-1] + ( 0, ) )
  if not existing:
    newdbdirs.append( ( dbname, dbhierarchy, None, None, 1 ) )
  neuroConfig.options._addDatabaseDirectory = newdbdirs

setDataBase( '/data/basetests' )

