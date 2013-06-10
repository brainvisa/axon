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
#from soma.minf.api import readMinf, writeMinf
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
  itemToInsert = []
  path = ""
  
  #sort bvproc from a diretory
  history_directory = os.path.join(str(self.database.name), "history_book")
  #bvsession_directory = os.path.join(history_directory, "bvsession")
  
  if (history_directory):  
    bvsession_directory = os.path.join(history_directory, "bvsession")
    if ( not os.path.isdir(bvsession_directory) ) : os.mkdir(bvsession_directory)
    date_last_incremental_update = time.strftime('%Y-%m-%d-%H:%M',time.localtime())  
    params = neuroConfig.DatabaseSettings(self.name)
    context.write("date ", date_last_incremental_update)
    params.expert_settings.last_incremental_update = date_last_incremental_update
    try:
      print params.expert_settings
      pathExpertSettings = os.path.join( self.database.name, 'database_settings.minf' )
      print path
      writeMinf( pathExpertSettings, ( params.expert_settings, ) )
    except IOError:
      print "error"
      pass

    fileCopy = False
    for fileToCopy in os.listdir( history_directory ):
      print "FILE OR DIRECTORY", fileToCopy
      if os.path.isfile(os.path.join(history_directory, fileToCopy)) :
        print "FILE TO COPY", fileToCopy
        if fileToCopy.endswith( '.bvproc' ) :
          f = os.path.join( history_directory, fileToCopy )
          #infiles.append( ff )
          s = os.stat( f )
          date_fichier = time.strftime("%Y-%m-%d", time.gmtime(s.st_mtime))
          path = os.path.join( history_directory, date_fichier )
          if ( not os.path.isdir(path) ) : os.mkdir(path)
          to = os.path.join( path, os.path.basename(f) )
          fileCopy = True
  
        elif fileToCopy.endswith( '.bvsession' ) :
          bvsession_file = os.path.join( history_directory, fileToCopy )
          to = os.path.join( history_directory, "bvsession", fileToCopy )
          fileCopy = True
        
        if fileCopy :
          print "COPIE"
          fileToCopy = os.path.join( history_directory, fileToCopy )
  #        print fileToCopy
  #        print to
          shutil.copyfile(fileToCopy, to)  
          shutil.copystat(fileToCopy, to)  
          
          #copy the .minf
  #        minfFile = fileToCopy +  ".minf"
  #        if os.path.isfile(minfFile) :
  #          shutil.copyfile(minfFile, ( to +  ".minf" ))  
  #          shutil.copystat(minfFile, ( to +  ".minf" ))  
            
          itemToInsert.append(to)
  
          #Supprimer le fileCopy s'il correspond à un DiskItem
          print "fileToCopy", fileToCopy 
          try :
            item_to_remove = self.database.getDiskItemFromFileName( fileToCopy )  # already exists in DB:   
            print "Item to remove : ", item_to_remove
            print "Item to remove : type ", type(item_to_remove)
            if item_to_remove : 
              uuid = str( item_to_remove.uuid( saveMinf=False ) )
              print "uuid : ", uuid
              self.database.removeDiskItem(item_to_remove, eraseFiles=True) #suppression dans la base
          except :
            context.write('Warning: file', fileToCopy, 'not found in any database.')
            continue
          
          fileCopy = False
           #insérer le diskitem         
          
    item = None
    item_exist = None
    print itemToInsert
    for file in itemToInsert :
      try: 
        item_exist = self.database.getDiskItemFromFileName( file )  # already exists in DB: no need to add it
      except:
        try:
          item = self.database.createDiskItemFromFileName( file )
        except:
          context.write('Warning: file', file , 'cannot be inserted in any database.')
#          print "item none"
#  
#      print "item_exist ", item_exist
#      print "item ", item
      if item is not None and (isinstance( item, DiskItem )) and item.isReadable() and item.get("_database", None) and ( not hasattr( item, '_isTemporary' ) or not item._isTemporary ):
        tmp = os.path.splitext(item.name)
        uuid = os.path.basename(tmp[0])
        minf = {}
        minf ['uuid'] = uuid
        print "FILE", file 
        print "UUID", uuid
        print "type item", type(item)
         #bvProcDiskItem = WriteDiskItem( 'Process execution event', 'Process execution event' ).findValue( eventFileName )
        try :          
          item._writeMinf(minf)
          self.database.insertDiskItem( item, update=True, insertParentDirs=False)
          #item._writeMinf(minf)
        except:
          context.write('WARNING: file', file , 'cannot be inserted in any database.')
        
        
#        
#    if len(infiles) != 0 :
#      for f in infiles :
#        s = os.stat( f )
#        date_fichier = time.strftime("%Y-%m-%d", time.gmtime(s.st_mtime))
#        path = os.path.join( history_directory, date_fichier )
#        if ( not os.path.isdir(path) ) : os.mkdir(path)
#        to = os.path.join( path, os.path.basename(f) )
#        shutil.copyfile(f, to)  
#        shutil.copystat(f, to) 
        #insérer le diskitem
#        try:
#          item = self.database.createDiskItemFromFileName( to )
#          self.database.insertDiskItem( item, update=True )
#        except NotInDatabaseError:
#          showException() 
#        #réécrire le .minf
#        try :
#          minf = {}
#          minf ['uuid'] = os.path.basename(f)
#          bvProcMinf = WriteDiskItem( 'Process execution event', 'Process execution event' ).findValue( to )
#          bvProcMinf._writeMinf(minf)
#        except :
#          showException()
    
    context.write("The sorting is done.")
    
#    context.write("Clear Database.")
#    self.database.clear()
#    context.write("Update Database.")
#    self.database.update()    

    
  
  else : context.write("The history_book directory is not found, please check if the history is activate for this database.")
        

  