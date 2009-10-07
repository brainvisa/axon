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


