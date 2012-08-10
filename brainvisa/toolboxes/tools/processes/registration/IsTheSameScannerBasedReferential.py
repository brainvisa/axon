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


name = 'IsTheSameScannerBasedReferential'
userLevel = 2

signature = Signature( 
  #'Volume_1', ReadDiskItem( "T1 MRI", getAllFormats() ),
  #'Volume_2', ReadDiskItem( "T1 MRI", getAllFormats() ),
  'Scanner_Based_1', ReadDiskItem( 'Scanner Based Referential', 'Referential' ),
  'Scanner_Based_2', ReadDiskItem( 'Scanner Based Referential', 'Referential' ),
 )
  

def initialization( self ):
  pass

  
def execution( self, context ):
  #db_dict = neuroHierarchy.databases._databases
  
  #context.write('Under development')
  
  #update the scanner based referential A by the the scanner based referential B
  #if A has already a scanner based referential included in other transformation, update them too.
  #to update a scanner based referential, change the 'destination_referential' in the .trmMinf file
 
  context.write("under devepmt")

  #for each volume, check if there is a scanner based referential
  tm = registration.getTransformationManager()
  ref1 = tm.referential( self.Scanner_Based_1 )
  ref2 = tm.referential( self.Scanner_Based_2 )
  
  #for tests
  #ref1 = tm.referential( registration.talairachACPCReferentialId )
  #ref1= tm.referential( registration.talairachMNIReferentialId )
  
  
  #Test set(list)
  
  if (self.Scanner_Based_1 == self.Scanner_Based_2 ) :
    context.write("Scanner Based Referential are the same")
  else :
    #Chek if they are type of "Scanner Based Referential" ?
        
    context.write("ok")
    
    #List of paths to update
    pathToUpdate = []
    
    
    #Find transformations in which ref1 is used
    #res = tm.findPaths(acpc.uuid(), mni.uuid())
    
    #scanner tous les reférentiels de toutes les bases
    all_databases = neuroHierarchy.databases._databases
    
    #print " all databases"
    #print all_databases.values()

    AllDatabases = all_databases.values()
    
    if ( AllDatabases != [] ) :
      for db in all_databases.values():
        options = {'_type' : 'Referential'}
        #options = {'_type' : 'Transformation matrix'}
        listDiskItem = db.findDiskItems(**options)
        for diskItem in listDiskItem :
          print "DiskItem"
          #print diskItem
          print diskItem.fileName()
          src = tm.referential(diskItem)
          print "\n** FIND WITH"
          print src.fileName()
          print src.uuid()
          print ref1.fileName()
          print ref1.uuid()
          #def findPaths( self, source_referential, destination_referential, maxLength=None, bidirectional=False ):
          res = tm.findPaths(src.uuid(), ref1.uuid(), maxLength=1, bidirectional=True)

          #for i in  tm.findPaths(dest.uuid(), ref1.uuid()):
              #print "lecture du generator"
              #print i
          
          print res
              
          for p in res :
            print 'path:'
            print p
            print '====='
            for path in p :
              print 'begin iter'
              print "\n** PATH FOUND"
              #print "Used to find"
              #print ref1.uuid()
              #print src.uuid()
              print 'transfo:', path
              print '-----'
              #print "referential values for the path"
              #print path.get('destination_referential')
              #print path.get('source_referential')
              if path not in pathToUpdate:
                pathToUpdate.append(path)
              print 'iter done'
            print 'path finished.'

      #Now update transformations
      print pathToUpdate
      for v in pathToUpdate:
        destPath = v.get('destination_referential')
        srcPath =v.get('source_referential')
        print ref1.uuid()
        print destPath
        print srcPath 
        if destPath == ref1.uuid() :
          print "cas destPath"
          #setNewTransformationInfo( self, v, srcPath, ref2.uuid())
        elif srcPath == ref1.uuid() :
          print  "cas srcPath"
        #setNewTransformationInfo( self, v, ref2.uuid(), destPath )
          
          
    else : 
      context.warning("This process is not avvailable without databases connexions.")


  
  
  


  
  