 # -*- coding: utf-8 -*-
from neuroProcesses import *
from neuroHierarchy import databases
import os

name = 'Rename denoised_* to nobias_*'
userLevel = 0

def validation():
  if not os.path.isdir( '/i2bm' ):
    raise ValidationError( 'This process is only valid in CEA-I2BM platforms (SHFJ, NeuroSpin and MirCEN)' )

signature = Signature(
  'undo_python_script', WriteDiskItem( 'Any type', 'Python script' ),
)


def initialization( self ):
  self.setOptional( 'undo_python_script' )

GOOD_PREFIX = 'nobias_'
BAD_PREFIX = 'denoised_'

def find_denoised( directory ):
  for f in os.listdir( directory ):
    subdirs = []
    df = os.path.join( directory, f )
    if os.path.isdir( df ):
      subdirs.append( df )
    elif f.startswith( BAD_PREFIX ):
      yield df
    for df in subdirs:
      for r in find_denoised( df ):
        yield r

def execution( self, context ):
  #brainvisa_options = readMinf( os.path.join( os.environ[ 'HOME' ], '.brainvisa', 'options.minf' ) )[0]
  #for d in (i[ 'directory' ] for i in brainvisa_options.get( 'databases', {} ).get( 'fso', [] )):
  if self.undo_python_script is not None:
    undo_python_script = self.undo_python_script.fullPath()
    if os.path.exists( undo_python_script ):
      r = context.ask( 'File ' + undo_python_script + ' exists. Do you want to overwirte it ?', 'Yes, erase it', 'No, keep it', 'Stop, this process' )
      if r == 0:
        # Backup Python script
        open( undo_python_script + '~', 'w' ).write( open( undo_python_script ).read() )
      elif r == 1:
        undo_python_script = None
      else:
        context.write( '<font color="orange">Operation cancelled</font>' )
        return
      if undo_python_script:
        undo_python_script = open( undo_python_script, 'w' )
        print >> undo_python_script, 'import os\n\nrename = []'
  else:
    undo_python_script = None
  it = databases.iterDatabases()
  it.next() # Skip shared database
  for database in it:
    rename = []
    for databaseDirectory in database.directories:
      if os.path.exists( databaseDirectory ):
        for f in find_denoised( databaseDirectory ):
          rename.append( os.path.split( f ) )
    if rename:
      context.write( '<font color="orange"><b>' + database.name + ':</b><br></font>' )
      if undo_python_script is not None:
        print >> undo_python_script, '\n#', database.name
      for d,b in rename:
        context.write( os.path.join( d, b ) )
        src = os.path.join( d, b )
        dest = os.path.join( d, GOOD_PREFIX + b[ len( BAD_PREFIX ): ] )
        os.rename( src, dest )
        if undo_python_script is not None:
          print >> undo_python_script, 'rename.append( (', repr( dest ) + ',\n               ', repr( src ), ') )'
    else:
      context.write( '<font color="darkgreen"><b>' + database.name + '</b></font>' )
  if undo_python_script is not None:
    print >> undo_python_script, '\n\nfor src, dest in rename: os.rename( src, dest )'


