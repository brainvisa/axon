#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCIL license version 2 under
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
# knowledge of the CeCILL version 2 license and that you accept its terms.


import neuroConfig
import neuroHierarchy
from neuroDiskItems import getDiskItemType, isSameDiskItemType, DiskItem
from neuroException import HTMLMessage
from soma import uuid
import threading

#------------------------------------------------------------------------------
class TransformationManager:
  def __init__( self ):
    # referential uuid -> referential object
    self.__referentials = {}
    # transformation uuid -> transformation object
    self.__transformations = {}
    # referential uuid -> transformation uuid list
    self.__transformationsFrom = {}
    # a reentrant lock to make this class thread safe
    self.lock=threading.RLock()
  

  def getObjectUuid( object ):
    return uuid.Uuid( object.uuid() )
  getObjectUuid = staticmethod( getObjectUuid )
  
  def addReferential( self, referential ):
    '''Add a new referential object to this manager. A referential object must
    have an 'uuid' attribute containing a unique string value (i.e. two
    referentials cannot have the same uuid).'''
    try:
      uuid = self.getObjectUuid( referential )
    except:
      print 'warning: referential', referential, 'has no UUID. Making one'
      refId = uuid.Uuid()
      referential._changeUuid( refId )
      referential.setMinf( 'dimension_count', dimension_count )
      #diskItem.setMinf( 'referential', refId )
      #referential.saveMinf()
    self.lock.acquire()
    try:
      self.__referentials[ uuid ] = referential
    finally:
      self.lock.release()
  

  def removeReferential( self, referential, removeTransformations=False ):
    '''Remove a referential from this manager. Either the uuid or the object can
    be given in referential parameter. If removeTransformations is True, all
    the transformations connected to the removed referential are removed from
    the manager. Removing a referential that is not in the manager is not
    considered as an error.'''
    
    refId = self.getObjectUuid( referential )
    self.lock.acquire()
    try:
      if self.__referenrials.pop( refId, None ) is not None:
        if removeTransformations:
          for trId in self.__transformationsFrom.pop( refId, [] ):
            del self.__transformations[ trId ]
    finally:
      self.lock.release()
  

  def referential( self, referentialId ):
    '''Return the referential object corresponding to the given uuid.
    Return None if the referential is not in the manager.'''
    if referentialId is None: return None
    self.lock.acquire()
    try:
      ref=self.__referentials.get( uuid.Uuid( referentialId ), None )
    finally:
      self.lock.release()
    return ref
  

  def referentialName( self, referential ):
    '''Return the name of a referential object or its uuid if it has no name.
    If an uuid is given and the referential is not found, the given uuid is
    returned.'''  
    refId = uuid.Uuid( referential )
    if refId is None:
      refId = self.getObjectUuid( referential )
    else:
      referential = self.referential( refId )
    if referential is not None:
      name = referential.get( 'name' )
      if name is None:
        return str( refId )
      return name
    else:
      return str( refId )
  

  def addTransformation( self, transformation ):
    '''Add a new transformation to this manager. A transfomration object must
    have three attributes:
      'uuid': a unique string value (i.e. two transformations cannot have the
            same uuid).
      'source_referential': the uuid of the source referential.
      'destination_referential': the uuid of the destination referential.'''
    try:
      trId = self.getObjectUuid( transformation )
    except:
      print 'warning: transformation with no uuid:', transformation
      return
    tsrc = transformation.get( 'source_referential' )
    if tsrc is None or transformation.get( 'destination_referential' ) is None:
      print 'warning: transformation', transformation, \
            'lacks source_referential or/and destination_referential'
      return
    self.lock.acquire()
    try:
      self.__transformations[ trId ] = transformation
      self.__transformationsFrom.setdefault( uuid.Uuid( tsrc ),
                                            [] ).append( trId )
    finally:
      self.lock.release()

  def removeTransformation( self, transformation, ):
    '''Remove a transformation from this manager. Either the uuid or the object
    can be given in transformation parameter. Removing a transformation that
    is not in the manager is not considered as an error.'''
    trId = uuid.Uuid( transformation )
    if trId is None:
      trId = self.getObjectUuid( transformation )
    self.lock.acquire()
    try:
      tr = self.__transformations.pop( trId, None )
      if tr:
        trList = self.__transformationsFrom[ uuid.Uuid( tr.get( 'source_referential' ) ) ]
        trList.remove( trId )
        if not trList:
          del self.__transformationsFrom[ uuid.Uuid( tr.get( 'source_referential' ) ) ]
    finally:
      self.lock.release()


  def transformation( self, transformationId ):
    '''Return the transformation object corresponding to the given uuid.
    Return None if the transformation is not in the manager.'''  
    if transformationId is None: return None
    self.lock.acquire()
    try:
      tr=self.__transformations.get( uuid.Uuid( transformationId ), None )
    finally:
      self.lock.release()
    return tr

  
  def transformationName( self, transformation ):
    '''Return the name of a transformation object or its uuid if it has no name.
    If an uuid is given and the transformation is not found, the given uuid is
    returned.'''
    trId = uuid.Uuid( transformation )
    if trId is None:
      trId = self.getObjectUuid( transformation )
    else:
      transformation = self.transformation( trId )
    if transformation is not None:
      name = transformation.get( 'name' )
      if name is None:
        return str( trId )
      return name
    else:
      return str( trId )


  def findPaths( self, source_referential, destination_referential,
                maxLength=None ):
    '''Return a generator object that iterate over all the transformation
    paths going from source_referential to destination_referential.
    A transformation path is a list of transformation objects. The paths
    are returned in increasing length order. If maxlength is set to a 
    non null positive value, it limits the size of the paths returned.
    Source and destination referentials can be given either as string uuid
    or as referential object.'''
    ref = uuid.Uuid( source_referential )
    if ref is not None:
      source_referential = ref
    else:
      source_referential = self.getObjectUuid( source_referential ) 
    ref = uuid.Uuid( destination_referential )
    if ref is not None:
      destination_referential = ref
    else:
      destination_referential = self.getObjectUuid( destination_referential ) 

    self.lock.acquire()
    try:
      paths = [ [ self.__transformations[ trId ] ] \
                for trId in self.__transformationsFrom.get( source_referential,
                                                            [] ) ]
    finally:
      self.lock.release()
      
    length = 1
    while paths:
      if maxLength and length > maxLength:
        break
      longerPaths = []
      for path in paths:
        # Get the last referential of the path
        lastReferential = uuid.Uuid( path[ -1 ].get( 'destination_referential' ) )
        # Check if the path reach the destination referential
        if lastReferential == destination_referential:
          yield path
          continue
        if lastReferential == source_referential:
          continue

        self.lock.acquire()
        try:
          # Get all the transformations objects starting from the last referential
          # of the path
          trList = [ self.__transformations[ trId ] \
                    for trId in self.__transformationsFrom.get( lastReferential,
                                                                [] ) ]
        finally:
          self.lock.release()
        
        for tr in trList:
          if tr not in path and uuid.Uuid( tr.get( 'destination_referential' ) ) not in \
            [uuid.Uuid( i.get( 'destination_referential' ) ) for i in path]:
            longerPaths.append( path + [ tr ] )
      paths = longerPaths
      length += 1

  def clear( self ):
    '''Remove all the referentials and transformations from the manager.'''
    self.lock.acquire()
    try:
      self.__referentials = {}
      self.__transformations = {}
      self.__transformationsFrom = {}
    finally:
      self.lock.release()



#------------------------------------------------------------------------------
class DatabasesTransformationManager( TransformationManager ):

  '''TransformationsManager linked with BrainVISA database system. This
  object imports all the transformations and referentials of a series of
  BrainVISA databases (i.e. DiskItem directories).'''
  
  def __init__( self, database = None ):
    '''If databases is None, this constructor uses all the selected databases
    of BrainVISA (i.e. neuroHierarchy.hierarchies()).'''
    TransformationManager.__init__( self )
    self.__databases = database
    # update transformation manager when the databases are updated
    if database is not None:
      database.onUpdateNotifier.add(self.update)
    self.update()

  def update( self ):
    '''Clear the manager content and re-read the databases.'''
    #print "Update transformation manager."
    self.lock.acquire()
    try:
      self.clear()
      if neuroConfig.newDatabases:
        for item in self.__databases.findDiskItems( _type='Referential' ):
          self.addReferential( item )
        for item in self.__databases.findDiskItems( _type='Transformation' ):
          self.addTransformation( item )
      else:
        referentialType = getDiskItemType( 'referential' )
        transformationType = getDiskItemType( 'transformation' )
        if self.__databases is None:
          stack = neuroHierarchy.hierarchies()[:]
        else:
          stack = self.__databases[:]
        while stack:
          item = stack.pop()
          scanner = getattr( item, 'scanner', None )
          if scanner is not None and ( scanner.possibleTypes.get( transformationType )\
            or scanner.possibleTypes.get( referentialType ) ):
            try:
              c = item.childs()
              if c is not None:
                stack += c
            except:
              raise
          elif item.type is not None:
            if item.type.isA( transformationType ):
              try:
                self.addTransformation( item )
              except:
                pass
            elif item.type.isA( referentialType ):
              try:
                self.addReferential( item )
              except:
                pass
    finally:
      self.lock.release()
  
  
  def referential( self, diskItemOrId ):
    '''Return the referential object corresponding to the given diskItem
    or uuid. Return None if the diskItem has no referential or the referential
    is not in the manager.'''
    if isinstance( diskItemOrId, DiskItem ):
      if diskItemOrId.type is not None and diskItemOrId.type.isA( 'Referential' ):
        #try:
        uuid = diskItemOrId.uuid()
        #except Exception, e:
        #  uuid = None
      else:
        try:
          uuid = diskItemOrId.get( 'referential' )
        except ( AttributeError, KeyError ):
          uuid = None
    else:
      uuid = diskItemOrId
    if uuid is None: return None
    return TransformationManager.referential( self, uuid )


  def setReferentialTo( self, diskItem, referential ):
    '''Assign to the given diskItem the given referential (as Referential
    object or uuid)'''
    ref = self.referential( referential )
    if not ref:
      raise RuntimeError( 'Referential ' + str( referential ) + \
        ' does not exist' )
    diskItem.readAndUpdateMinf()
    diskItem.setMinf( 'referential', ref.uuid() )
    #diskItem.saveMinf()
    if neuroConfig.newDatabases:
      self.__databases.insertDiskItem( diskItem, update=True )


  def createNewReferentialFor( self,
                              diskItem, 
                              name = None, 
                              description = None,
                              dimension_count = 3,
                              referentialType = None,
                              simulation = False ):
    '''Create a new referential for an object stored in a DiskItem and
    record it in the database. Returns None if the referential has not been
    created because its location in the database cannot be found with 
    ReadDiskItem( 'Referential', 'Referential' ).findValue( diskItem ).'''
    # Find a location for the referential in the database
    referential = None
    if referentialType is None:
      try:
        if diskItem.type is not None:
          referentialType = getDiskItemType( 'Referential of ' + diskItem.type.name )
      except ValueError:
        referentialType =None
    else:
      referentialType = getDiskItemType( referentialType )
    while referential is None and referentialType is not None:
      wdi = neuroHierarchy.WriteDiskItem( referentialType, 'Referential' )
      referential = wdi.findValue( diskItem )
      #if referential is None:
        #wdi.requiredAttributes = { 'filename_variable':  refId }
        #referential = wdi.findValue( diskItem )
      referentialType = referentialType.parent
    if referential is None:
      wdi = neuroHierarchy.WriteDiskItem( 'Referential', 'Referential' )
      referential = wdi.findValue( diskItem )
      #if referential is None:
        #wdi = neuroHierarchy.WriteDiskItem( 'Referential', 'Referential' )
        #wdi.requiredAttributes[ 'filename_variable' ] = refId
        #referential = wdi.findValue( diskItem )
    if referential is not None:
      if name is None:
        if referentialType is not None:
          name = referentialType.name
        elif diskItem.type is not None:
          name = diskItem.type.name
        else:
          name = referential.name
      referential.setMinf( 'dimension_count', dimension_count, saveMinf=False )
      if name is not None:    
        referential.setMinf( 'name', name, saveMinf=False )
      if description is not None:    
        referential.setMinf( 'description', description, saveMinf=False)
      if not simulation:
        diskItem.readAndUpdateMinf()
        referential.createParentDirectory()
        diskItem.setMinf( 'referential', referential.uuid() )
        referential.saveMinf()
        #diskItem.saveMinf()
        if neuroConfig.newDatabases:
          self.__databases.insertDiskItem( referential, update=True )
          self.__databases.insertDiskItem( diskItem, update=True )
        self.addReferential( referential )
        # write a transformation between this referential and MNI template if needed
        if diskItem.get( 'normalized' ) == 'yes':
          import shfjGlobals
          atts = shfjGlobals.aimsVolumeAttributes(diskItem)
          refs = atts.get( 'referentials' )
          if refs:
            foundmni = False
            for i in range( len( refs ) ):
              r = refs[i]
              if r == 'Talairach-MNI template-SPM':
                foundmni = True
                break
            if not foundmni:
              # force target ref info since SPM doesn't set it
              i = 0
              refs[0] = 'Talairach-MNI template-SPM'
              diskItem.setMinf( 'referentials', refs )
              #diskItem.saveMinf()
            # write a .trm transformation to MNI space here
            trans = atts.get( 'transformations' )
            if trans:
              tr = trans[i]
              dref = self.referential( talairachMNIReferentialId )
              paths = self.findPaths( referential.uuid(), dref.uuid(),
                maxLength=1 )
              tdi = None
              for p in paths:
                tdi = p[0]
                break
              if not tdi:
                tdi = self.createNewTransformation( 'Transformation Matrix',
                  referential, dref )
              if tdi:
                trm = open( tdi.fullPath(), 'w' )
                print >> trm, tr[3], tr[7], tr[11]
                print >> trm, tr[0], tr[1], tr[2]
                print >> trm, tr[4], tr[5], tr[6]
                print >> trm, tr[8], tr[9], tr[10]
                trm.close()

    return referential

  def createNewReferential(self, referential):
    """
    Creates the file for the referential diskitem and add it to the database and to the transformation manager.
    """
    try:
      referential.createParentDirectory()
      referential.saveMinf()
      if neuroConfig.newDatabases:
        self.__databases.insertDiskItem( referential, update=True )
      self.addReferential( referential )
    except:
      referential=None
    return referential
    
  def copyReferential( self,
                      sourceDiskItem, 
                      destinationDiskItem ):
    '''Copy the referential of sourceDiskItem to the one of destinationDiskItem.
    The minf file of destinationDiskItem is saved by this function.'''
    if destinationDiskItem is None or not destinationDiskItem.isReadable(): return # do not create a .minf file for a diskitem that doesn't exist
    refId = self.referential( sourceDiskItem )
    import shfjGlobals
    atts = shfjGlobals.aimsVolumeAttributes( sourceDiskItem, forceFormat=True )
    uuid = None
    if refId is not None:
      if isinstance( refId, DiskItem ):
        uuid = refId.get( 'referential' )
        if uuid is None:
          # Referential diskitem ?
          #try:
          uuid = refId.uuid()
          #except:
          #  uuid = None
          # maybe this needs a cleaner test/error message if uuid() fails
      if uuid is not None:
        destinationDiskItem.readAndUpdateMinf()
        destinationDiskItem.setMinf( 'referential', uuid )
        refs = atts.get( 'referentials' )
        trans = atts.get( 'transformations' )
        if refs and trans:
          destinationDiskItem.setMinf( 'referentials', refs )
          destinationDiskItem.setMinf( 'transformations', trans )
        #destinationDiskItem.saveMinf()
        if neuroConfig.newDatabases:
          try:
            self.__databases.insertDiskItem( destinationDiskItem, update=True )
          except:
            pass

  def createNewTransformation( self,
                              format,
                              sourceDiskItem, 
                              destDiskItem, 
                              name = None, 
                              description = None,
                              simulation = False ):
    if isSameDiskItemType( sourceDiskItem.type, 'Referential' ):
      sourceRef = sourceDiskItem
    else:
      sourceRef = self.referential( sourceDiskItem.get( 'referential' ) )
      if sourceRef is None:
        raise RuntimeError( HTMLMessage(_t_( 'Object <em>%s</em> does not have referential' ) % ( str( sourceDiskItem ), )) )

    if isSameDiskItemType( destDiskItem.type, 'Referential' ):
      destRef = destDiskItem
    else:
      destRef = self.referential( destDiskItem.get( 'referential' ) )
    if destRef is None:
      raise RuntimeError( HTMLMessage(_t_( 'Object <em>%s</em> does not have referential' ) % ( str( destDiskItem ), )) )
    
    trType = None
    # try to find the transformation's type name with source and destination referentials
    
    sourceRefName = sourceRef.get( 'name' )
    destRefName = destRef.get( 'name' )
    sourceRefType=sourceRef.type.name
    if sourceRefType.startswith("Referential of "):
      sourceRefType=sourceRefType.replace("Referential of ", "")
    destRefType=destRef.type.name
    if destRefType.startswith("Referential of "):
      destRefType=destRefType.replace("Referential of ", "")
    # Transform sourceRefName to destRefName
    if sourceRefName is not None and destRefName is not None:
        trType = 'Transform ' + sourceRefName + ' to ' + destRefName
        try:
          trType = getDiskItemType( trType )
        except ValueError:
          trType = None
    # Transform sourceRefType to destRefName
    if trType is None:
      if sourceRefType is not None and destRefName is not None:
        trType = 'Transform ' + sourceRefType + ' to ' + destRefName
        try:
          trType = getDiskItemType( trType )
        except ValueError:
          trType = None
    # Transform sourceRefName to destRefType
      if trType is None:
        if sourceRefName is not None and destRefType is not None:
            trType = 'Transform ' + sourceRefName + ' to ' + destRefType
            try:
              trType = getDiskItemType( trType )
            except ValueError:
              trType = None
    # Transform sourceRefType to destRefType
    if trType is None:
      if sourceRefType is not None and destRefType is not None:
        trType = 'Transform ' + sourceRefType + ' to ' + destRefName
        try:
          trType = getDiskItemType( trType )
        except ValueError:
          trType = None
    if trType is None:
      trType = getDiskItemType( 'Transformation' )

    wdi = neuroHierarchy.WriteDiskItem( trType, format )
    transformation = wdi.findValue( { 'source': sourceDiskItem,
                                      'destination': destDiskItem } )
    if transformation is None:
        transformation = wdi.findValue( sourceDiskItem )
    if transformation is None:
        transformation = wdi.findValue( destDiskItem )
        
    if transformation is not None:
      try:
        transformation.setMinf( 'source_referential', sourceRef.uuid(), saveMinf=False )
        transformation.setMinf( 'destination_referential', destRef.uuid(), saveMinf=False )
      except:
        return None
      if name is not None:
        transformation.setMinf( 'name', name, saveMinf=False )
      if description is not None:
        transformation.setMinf( 'description', description, saveMinf=False )
      if not simulation:
        transformation.createParentDirectory()
        transformation.saveMinf()
        if neuroConfig.newDatabases:
          self.__databases.insertDiskItem( transformation, update=True )
        self.addTransformation( transformation )
    return transformation


  def setNewTransformationInfo( self, transformation,
        source_referential, 
        destination_referential,
        name = None,
        description = None ):
    if name is None and isinstance( transformation, DiskItem ):
      name = transformation.name
    source_referential = self.referential( source_referential )
    destination_referential = self.referential( destination_referential )
    transformation.createParentDirectory()
    if source_referential is not None:
      transformation.setMinf( 'source_referential', source_referential.uuid() )
    if destination_referential is not None:
      transformation.setMinf( 'destination_referential', destination_referential.uuid() )
    if name is not None:
      transformation.setMinf( 'name', name )
    if description is not None:
      transformation.setMinf( 'description', name )
    try:
      #transformation.saveMinf()
      if neuroConfig.newDatabases:
        self.__databases.insertDiskItem( transformation, update=True )
      self.addTransformation( transformation )
    except:
      pass


  def findOrCreateReferential( self, referentialType,
                              diskItem, 
                              name = None, 
                              description = None,
                              dimension_count = 3,
                              simulation = False, assign=False ):
    """
    Search a referential of type referentialType for the data diskitem. 
    if simulation is false, the referential will be created and added to the database and transformation manager. 
    if assign is True, the referential will be assign to the diskitem.
    """
    try:
      oldref = diskItem.get( 'referential' )
    except:
      oldref = None
    result = self.createNewReferentialFor( diskItem,
                              name = name, 
                              description = description,
                              dimension_count = dimension_count,
                              referentialType = referentialType,
                              simulation = True )
    if result is not None:
      if not simulation:
        if not result.isReadable():
          try:
            result.createParentDirectory()
            result.saveMinf()
            if neuroConfig.newDatabases:
              self.__databases.insertDiskItem( result, update=True )
            self.addReferential( result )
          except OSError:
            result = None
        if assign:
          if str(result.uuid()) != oldref and diskItem.isWriteable():
            diskItem.setMinf( 'referential', result.uuid() )
            #diskItem.saveMinf()
          if neuroConfig.newDatabases:
            self.__databases.insertDiskItem( diskItem, update=True )
 
    return result


#------------------------------------------------------------------------------
_transformationManager = None


#------------------------------------------------------------------------------
def getTransformationManager():
  global _transformationManager
  if _transformationManager is None:
    if neuroConfig.newDatabases:
      _transformationManager = DatabasesTransformationManager( neuroHierarchy.databases )
    else:
      _transformationManager = DatabasesTransformationManager()
  else: # not later update transformation manager each it is got with new database system. It is updated only when databases are updated.
    if not neuroConfig.newDatabases:
      _transformationManager.update()
  return _transformationManager

#------------------------------------------------------------------------------
# standard referentials
talairachACPCReferentialId = uuid.Uuid(
  'a2a820ac-a686-461e-bcf8-856400740a6c' )
talairachMNIReferentialId = uuid.Uuid(
  '803552a6-ac4d-491d-99f5-b938392b674b' )
