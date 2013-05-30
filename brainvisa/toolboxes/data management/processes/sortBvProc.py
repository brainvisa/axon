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

from brainvisa.processes import *
#from brainvisa.data import neuroHierarchy
import sys, os


name = 'BvProc sorting'
userLevel = 0

signature = Signature( 
  'database', Choice()
 )

def initialization(self):
  databases=[(dbs.directory, neuroHierarchy.databases.database(dbs.directory)) for dbs in neuroConfig.dataPath if not dbs.builtin]
  self.signature['database'].setChoices(*databases)
  if databases:
    self.database=databases[0][1]
  else:
    self.database=None
    
    
def execution(self, context):
  '''
    Sort bvproc files by date into a new directory 
    directory parameter is for example history_book
  '''
  
  infiles = []
  path = ""
  
  #sort bvproc from a diretory
  history_directory = os.path.join(str(self.database.name), "history_book")
  bvsession_directory = os.path.join(history_directory, "bvsession")
  
  if (history_directory):  
    bvsession_directory = os.path.join(history_directory, "bvsession")
    if ( not os.path.isdir(bvsession_directory) ) : os.mkdir(bvsession_directory)
    date_last_incremental_update = time.strftime('%Y-%m-%d-%H:%M',time.localtime())  
    params = neuroConfig.DatabaseSettings(self.name)
    context.write("date ", date_last_incremental_update)
    params.expert_settings.last_incremental_update = date_last_incremental_update
    
    for bvproc in os.listdir( history_directory ):
      if bvproc.endswith( '.bvproc' ) or bvproc.endswith( '.bvproc.minf' ) :
        ff = os.path.join( history_directory, bvproc )
        infiles.append( ff )
      elif bvproc.endswith( '.bvsession' ) or bvproc.endswith( '.bvsession.minf' ) :
        bvsession_file = os.path.join( history_directory, bvproc )
        to = os.path.join( history_directory, "bvsession", bvproc )
        shutil.copyfile(bvsession_file, to)  
        shutil.copystat(bvsession_file, to)  
        
    if len(infiles) != 0 :
      for f in infiles :
        s = os.stat( f )
        date_fichier = time.strftime("%Y-%m-%d", time.gmtime(s.st_mtime))
        path = os.path.join( history_directory, date_fichier )
        if ( not os.path.isdir(path) ) : os.mkdir(path)

        to = os.path.join( path, os.path.basename(f) )
        shutil.copyfile(f, to)  
        shutil.copystat(f, to)  
        
    context.write("The sorting is done.")
    
  
  else : context.write("The history_book directory is not found, please check if the history is activate for this database.")
        

  