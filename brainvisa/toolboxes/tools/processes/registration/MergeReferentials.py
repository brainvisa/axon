# -*- coding: utf-8 -*-
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
import registration
import shfjGlobals
from soma import aims


name = 'MergeReferentials'
userLevel = 2

signature = Signature( 
  #'Volume_1', ReadDiskItem( "T1 MRI", getAllFormats() ),
  #'Volume_2', ReadDiskItem( "T1 MRI", getAllFormats() ),
  'Referential_to_replace', ReadDiskItem( 'Scanner Based Referential', 'Referential' ),
  'Referential_to_keep', ReadDiskItem( 'Scanner Based Referential', 'Referential' ),
 )
  

def initialization( self ):
  pass

  
def execution( self, context ):
  #db_dict = neuroHierarchy.databases._databases
  
  #context.write('Under development')
  
  #update the scanner based referential A by the the scanner based referential B
  #if A has already a scanner based referential included in other transformation, update them too.
  #to update a scanner based referential, change the 'destination_referential' in the .trmMinf file
 
  context.write("Under Devepmt")

  #for each volume, check if there is a scanner based referential
  tm = registration.getTransformationManager()
  ref1 = tm.referential( self.Referential_to_replace )
  ref2 = tm.referential( self.Referential_to_keep )
  
  #for tests
  #ref1 = tm.referential( registration.talairachACPCReferentialId )
  #ref1= tm.referential( registration.talairachMNIReferentialId )
  
  
  #Test set(list)
  
  if (self.Referential_to_replace == self.Referential_to_keep ) :
    context.write("Referentials are the same")
  else :
    #Chek if they are type of "Scanner Based Referential" ?
        
    #context.write("ok")

    #Find transformations in which ref1 is used
    #res = tm.findPaths(acpc.uuid(), mni.uuid())
    
    #scanner tous les reférentiels de toutes les bases
    all_databases = neuroHierarchy.databases._databases
    
    #print " all databases"
    #print all_databases.values()

    AllDatabases = all_databases.values()
    
    
    if ( AllDatabases != [] ) :

      for db in all_databases.values():
        #List of paths to update
        #print "\nMise a zero de pathToUpdate"
        pathToUpdate = []
        
        #print "Parcours de la base"
        #print db
        #print db.__class__
        
        options = {'_type' : 'Referential'}
        #options = {'_type' : 'Transformation matrix'}
        listDiskItem = db.findDiskItems(**options)
        for diskItem in listDiskItem :
          #print diskItem.fileName()
          src = tm.referential(diskItem)
         
          #print "\n** FIND WITH"
          #print src.fileName()
          #print src.uuid()
          #print ref1.fileName()
          #print ref1.uuid()

          #find paths with both referential 
          res = tm.findPaths(src.uuid(), ref1.uuid(), maxLength=1, bidirectional=True)
              
          for p in res :
            for path in p :
              #print "\n** PATH FOUND"
              #print 'transfo:', path
              if path not in pathToUpdate:
                #print path.__class__
                pathToUpdate.append(path)
                
        if pathToUpdate:
          #Now update transformations
          #print "\n** PATH TO UPDATE"
          #print pathToUpdate
          for v in pathToUpdate:
            destPath = v.get('destination_referential')
            srcPath =v.get('source_referential')
            #print "ref1 %s" %(ref1.uuid())
            #print "ref2 %s" %(ref2.uuid())
            #print "destPath %s" %(destPath)
            #print "srcPath %s" %(srcPath)
            
            if destPath == ref1.uuid() :
              #print "Update the destination referential"
              #print "Change the %s referential by  %s in %s" %(ref1.uuid(), ref2.uuid() ,v)
              #print v.__class__
              #print srcPath.__class__
              #print ref2.uuid().__class__
              tm.setNewTransformationInfo( v, srcPath, ref2.uuid() )
            elif srcPath == ref1.uuid() :
              print "Update the source referential"
              print "Change the %s referential by  %s in %s" %(ref1.uuid(), ref2.uuid() ,v)
              #tm.setNewTransformationInfo( self, v, ref2.uuid(), destPath, v )

            #Remove the referantial from database OR update the value of referential ?
            #print "database en cours"
            #print db.__class__
            #print db
            #tm.removeReferential ( db, diskItems, eraseFiles=False )
            
        else :
          context.write("Not transformation found")

    else : 
      context.warning("This process is not available without databases connexions.")


  
  
  


  
  