# -*- coding: utf-8 -*-
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
from __future__ import print_function
import sys, time
import six

from brainvisa.data.sqlFSODatabase import SQLDatabase, SQLDatabases
from brainvisa.data.readdiskitem import ReadDiskItem
from brainvisa.data.writediskitem import WriteDiskItem

#------------------------------------------------------------------------------
def timeDifferenceToString( difference ):
  days = int( difference / 86400 )
  difference -= days * 86400
  hours = int( difference / 3600 )
  difference -= hours * 3600
  minutes = int( difference / 60 )
  seconds = int( difference - minutes * 60 )
  result = ''
  if days:
    return( _t_( '%d days %d hours %d minutes %d seconds' ) % ( days, hours, minutes, seconds ) )
  if hours:
    return( _t_( '%d hours %d minutes %d seconds' ) % ( hours, minutes, seconds ) )
  if minutes:
    return( _t_( '%d minutes %d seconds' ) % ( minutes, seconds ) )
  return( _t_( '%d seconds' ) % ( seconds, ) )

#------------------------------------------------------------------------------
directories = [ 
  '/neurospin/lnao/Pmad/jumeaux',
  '/neurospin/lnao/Pmad/AnneLaure/base',
  '/neurospin/lnao/Panabase/data',
  '/neurospin/lnao/Panabase/data_icbm',
  '/neurospin/lnao/Panabase/data_diffusion/autisme',
  '/neurospin/lnao/Panabase/BaseCADASIL',
  '/neurospin/lnao/Panabase/data_Kochunov',
  '/neurospin/lnao/Panabase/data_alan',
  '/neurospin/lnao/Panabase/data_alzheimer',
  '/neurospin/lnao/Panabase/data_cadasil',
  '/neurospin/lnao/Panabase/data_chicoutimi',
  '/neurospin/lnao/Panabase/data_distonie',
  '/neurospin/lnao/Panabase/data_epilepsy',
  '/neurospin/lnao/Panabase/data_glasel',
  '/neurospin/lnao/Panabase/data_gtwins',
  '/neurospin/lnao/Panabase/data_sulci_ccrt/base2000/graphs/brainvisa_hierarchy',
  '/neurospin/lnao/Panabase/data_sulci_ccrt/base_pauline/graphes/brainvisa_hierarchy',
  '/neurospin/lnao/Panabase/data_twins/twins06',
  '/neurospin/lnao/Panabase/data_twins',
  '/neurospin/lnao/Panabase/data_update',
  '/neurospin/lnao/Panabase/demos/new_data',
  '/neurospin/lnao/Panabase/demosII/SPMvsAnatomist/database',
  '/neurospin/lnao/Panabase/demosII/demo_jirfni_lyon_2006/data_brainvisa',
  '/neurospin/lnao/Panabase/edouard/data_shfj',
  '/neurospin/lnao/Panabase/huntington',
  '/neurospin/lnao/Panabase/jeff/data/nih_chp',
  '/neurospin/lnao/Panabase/jeff/data/production',
  '/neurospin/lnao/Panabase/jeff/people/narly',
  '/neurospin/lnao/Panabase/muriel/brainvisa',
  '/neurospin/lnao/Panabase/testbase',
  '/neurospin/lnao/Panabase/testbase2',
  '/neurospin/lnao/Panabase/vincent',
  '/neurospin/lnao/Pgipsy/jeff/data06_cadasil',
  '/neurospin/lnao/Pgipsy/jeff/data06_chicoutimi',
  '/neurospin/lnao/Pgipsy/jeff/data06_distonie',
  '/neurospin/lnao/Pgipsy/jeff/data06_epilepsy',
  '/neurospin/lnao/Pgipsy/jeff/data06_icbm',
  '/neurospin/lnao/Pgipsy/jeff/data06_nih',
  '/neurospin/lnao/Pmad/Localizer_Database',
  '/neurospin/unicog/protocols/IRMf',
  '/neurospin/unicog/people/Dyslexiq/base_enfant',
]
#databaseDir = '/neurospin/lnao/Pmad/AnneLaure/base'

directories = [ 'AnneLaure_base', 'data_icbm' ]
import brainvisa.data, os
baseDir = os.path.dirname( brainvisa.data.__file__ )
databases = [ SQLDatabase( os.path.join( baseDir, i + '.sqlite' ), i, 'brainvisa-3.1' ) for i in directories ]
for database in databases:
  if database.createTables():
    print(database.name + ': parse directories and insert items')
    t0 = time.time()
    database.insertDiskItems( database.scanDatabaseDirectories() )
    duration = time.time() - t0
    d = database._getDatabaseConnection()
    c = d.cursor()
    fileCount = c.execute( 'select COUNT(*) from _filenames_' ).fetchone()[0]
    diskItemCount = c.execute( 'select COUNT(*) from _diskitems_' ).fetchone()[0]
    print(fileCount, 'files identified as', diskItemCount, 'DiskItems in', timeDifferenceToString( duration ))

bases = SQLDatabases( databases )
ReadDiskItem.database = bases




from brainvisa.processes import Parameterized, Signature, String
from brainvisa.processing.qtgui.neuroProcessesGUI import ParameterizedWidget

p = Parameterized( 
  Signature(
    't1', ReadDiskItem( 'T1 MRI', 'Aims readable volume formats' ),
    'raw', ReadDiskItem( 'Raw T1 MRI', 'Aims readable volume formats' ),
    'corrected', WriteDiskItem( 'T1 MRI Bias Corrected', 'GIS image' ),
    'left_graph', WriteDiskItem( 'Cortical folds graph', 'Graph',
                                 requiredAttributes = { 'labelled' : 'No',
                                                        'side' : 'left',
                                                        'graph_version' : '3.0'
                                                        }, _debug=sys.stdout ),
    'fmri', ReadDiskItem( 'fMRI', 'Aims readable volume formats' ),
  )
)
p.linkParameters( 'corrected', 'raw' )
p.linkParameters( 'left_graph', 'corrected' )


w = ParameterizedWidget( p, None )
w.show()












#database.fsoToHTML( database.fso.name + '.html' )
#import cProfile
#cProfile.run( 'database.scanDatabaseDirectory()', 'profile' )


#print('Parsing', databaseDir, 'with new system')
#newItems = {}
#for diskItem in database.scanDatabaseDirectory( open( 'test.html', 'w' ) ):
  #newItems[ diskItem.fullPath() ] = diskItem

#print('Parsing', databaseDir, 'with current system')
#oldItems = {}
#d = Directory( os.path.abspath( databaseDir ), None )
#d.scanner = [i for i in database.fso.content if isinstance(i,SetContent)][0].scanner
#stack = [d]
#while stack:
  #diskItem = stack.pop( 0 )
  #if diskItem.type is not None and diskItem.format is not None:
    #oldItems[ diskItem.fullPath() ] = diskItem
  #children = diskItem.childs()
  #if children: stack += children
#import cPickle
#oldItems = cPickle.load( open( 'oldItems.pickle' ) )

#print('Checking differences')
#new = 0
#both = 0
#oldItemsCopy = oldItems.copy()
#for newItemName, newItem in six.iteritems(newItems):
  #oldItem = oldItemsCopy.pop( newItemName, None )
  #if not oldItem:
    #new += 1
    #print('  +NEW+', newItemName)
  #else:
    #both += 1
    #oldAttributes = oldItem.hierarchyAttributes()
    #newAttributes = newItem.hierarchyAttributes()
    #del newAttributes[ 'ontology' ]
    #del newAttributes[ 'database' ]
    #if oldAttributes.get( 'filename_variable' ) == '':
      #del oldAttributes[ 'filename_variable' ]
    #if oldAttributes != newAttributes:
      #print('  ~DIF~', newItemName)
      #for newKey, newValue in six.iteritems(newAttributes):
        #oldValue = oldAttributes.pop( newKey, None )
        #if oldValue is None:
          #print('    ++', newKey, '=', repr( newValue ))
        #elif oldValue != newValue:
          #print('    !=', newKey, ': new =', repr( newValue )+ ',', 'old =', repr( oldValue ))
      #for oldKey, oldValue in six.iteritems(oldAttributes):
        #print('    --', oldKey, '=', repr( oldValue ))
#for oldItem in oldItemsCopy:
  #print('  -OLD-', oldItem)
#print('Items in both systems:', both)
#print('Items only in new system:', new)
#print('Items only in old system:', len( oldItemsCopy ))
