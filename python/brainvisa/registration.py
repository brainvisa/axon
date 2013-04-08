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


from brainvisa.configuration import neuroConfig
from brainvisa.data import neuroHierarchy
from brainvisa.data.neuroDiskItems import getDiskItemType, isSameDiskItemType, DiskItem
from brainvisa.processing.neuroException import HTMLMessage
from brainvisa.data.writediskitem import WriteDiskItem
from soma import uuid
import threading


#------------------------------------------------------------------------------
class DatabasesTransformationManager( object ):

  '''TransformationsManager linked with BrainVISA database system.'''

  def __init__( self ):
    self.lock = threading.RLock()

  def referential( self, diskItemOrId ):
    '''Return the referential object corresponding to the given diskItem
    or uuid. Return None if the diskItem has no referential or the referential
    is not in the manager.'''
    if isinstance( diskItemOrId, DiskItem ):
      if diskItemOrId.type is not None and diskItemOrId.type.isA( 'Referential' ):
        uuid = diskItemOrId.uuid()
        if uuid is not None: 
            return diskItemOrId
      else:
        try:
          uuid = diskItemOrId.get( 'referential' )
        except ( AttributeError, KeyError ):
          uuid = None
    else:
      uuid = diskItemOrId
    if uuid is None: return None
    return neuroHierarchy.databases.getDiskItemFromUuid( uuid, None )


  def findPaths( self, source_referential, destination_referential, maxLength=None, bidirectional=False ):
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

    for path in neuroHierarchy.databases.findTransformationPaths( source_referential, destination_referential, maxLength, bidirectional ):
      try:
        yield [ neuroHierarchy.databases.getDiskItemFromUuid( i[0] ) for i in path ]
      except neuroHierarchy.DatabaseError, e:
        print e
        print '  no transformation corresponds to this uuid: %s, used in a ' \
          'possible path to link refs %s (%s) and %s (%s)' % \
          ( i[0], source_referential,
          neuroHierarchy.databases.getDiskItemFromUuid( source_referential ),
          destination_referential,
          neuroHierarchy.databases.getDiskItemFromUuid(
            destination_referential ) )


  def setReferentialTo( self, diskItem, referential ):
    '''Assign to the given diskItem the given referential (as Referential
    object or uuid)'''
    ref = self.referential( referential )
    if not ref:
      raise RuntimeError( 'Referential ' + str( referential ) + \
        ' is not in a configured database' )
    diskItem.readAndUpdateMinf()
    diskItem.setMinf( 'referential', ref.uuid() )
    try:
      neuroHierarchy.databases.insertDiskItem( diskItem, update=True )
    except:
      pass


  def createNewReferentialFor( self,
                              diskItem,
                              name = None,
                              description = None,
                              dimension_count = 3,
                              referentialType = None,
                              simulation = False,
                              output_diskitem = None ):
    '''Create a new referential for an object stored in a DiskItem and
    record it in the database. Returns None if the referential has not been
    created because its location in the database cannot be found with
    ReadDiskItem( 'Referential', 'Referential' ).findValue( diskItem ).'''
    # Find a location for the referential in the database
    referential = output_diskitem
    if referentialType is None:
      try:
        if diskItem.type is not None:
          referentialType = getDiskItemType( 'Referential of ' + diskItem.type.name )
      except ValueError:
        referentialType =None
    else:
      referentialType = getDiskItemType( referentialType )
    while referential is None and referentialType is not None:
      wdi = WriteDiskItem( referentialType, 'Referential', exactType=True )
      referential = wdi.findValue( diskItem )
      referentialType = referentialType.parent
    if referential is None:
      wdi = WriteDiskItem( 'Referential', 'Referential', exactType=True )
      referential = wdi.findValue( diskItem )
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
        neuroHierarchy.databases.insertDiskItem( referential, update=True )
        neuroHierarchy.databases.insertDiskItem( diskItem, update=True )
        # write a transformation between this referential and MNI template if needed
        if diskItem.get( 'normalized' ) == 'yes':
          from brainvisa.tools.aimsGlobals import aimsVolumeAttributes
          atts = aimsVolumeAttributes(diskItem)
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
              try:
                path = self.findTransformationPaths( referential.uuid(), dref.uuid(),
                  maxLength=1 ).next()
              except StopIteration:
                tdi = self.createNewTransformation( 'Transformation Matrix',
                  referential, dref )
              else:
                tdi = self.transformation( path[ 0 ][ 0 ] )
              if tdi:
                trm = open( tdi.fullPath(), 'w' )
                print >> trm, tr[3], tr[7], tr[11]
                print >> trm, tr[0], tr[1], tr[2]
                print >> trm, tr[4], tr[5], tr[6]
                print >> trm, tr[8], tr[9], tr[10]
                trm.close()
    return referential


  def createNewReferential( self, referential ):
    """
    Creates the file for the referential diskitem and add it to the database and to the transformation manager.
    """
    try:
      referential.createParentDirectory()
      referential.saveMinf()
      neuroHierarchy.databases.insertDiskItem( referential, update=True )
    except:
      referential=None
    return referential
    


  def removeReferential (self, db, diskItem, uuid, eraseFiles=False) :
    """
    Test if there is no transformation with uuid then remove the diskItem
    """ 
    val =  neuroHierarchy.databases.findTransformationWith( uuid )
    if val is None :
      db.removeDiskItem(diskItem, eraseFiles=eraseFiles) 
      return True
    else :
      return False
    
      


  def copyReferential( self,
                      sourceDiskItem,
                      destinationDiskItem ):
    '''Copy the referential of sourceDiskItem to the one of destinationDiskItem.
    The minf file of destinationDiskItem is saved by this function.'''
    if destinationDiskItem is None or not destinationDiskItem.isReadable():
      return # do not create a .minf file for a diskitem that doesn't exist
    refId = self.referential( sourceDiskItem )
    from brainvisa.tools.aimsGlobals import aimsVolumeAttributes
    atts = aimsVolumeAttributes( sourceDiskItem, forceFormat=True )
    uuid = None
    if refId is not None:
      if isinstance( refId, DiskItem ):
        uuid = refId.get( 'referential' )
        if uuid is None:
          uuid = refId.uuid()
    else:
        # get ref uuid from source minf (maybe outside databases)
        uuid = atts.get( 'referential' )
    if uuid is not None:
      destinationDiskItem.readAndUpdateMinf()
      destinationDiskItem.setMinf( 'referential', uuid )
      refs = atts.get( 'referentials' )
      trans = atts.get( 'transformations' )
      if refs and trans:
        destinationDiskItem.setMinf( 'referentials', refs )
        destinationDiskItem.setMinf( 'transformations', trans )
      try:
        neuroHierarchy.databases.insertDiskItem( destinationDiskItem, update=True )
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

    wdi = WriteDiskItem( trType, format, exactType=True )
    # it would be a good idea to take into account the source and destination diskitems but it is not
    # possible for the moment, these attributes source and destintation doesn't exist and are not used.
    # Moreover, this request can return a wrong transformation, if there is only one transformation of that type in the datbase.
    #transformation = wdi.findValue( { 'source': sourceDiskItem,
                                      #'destination': destDiskItem } )
    #if transformation is None:
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
        neuroHierarchy.databases.insertDiskItem( transformation, update=True )
    return transformation


  def setNewTransformationInfo( self, transformation,
        source_referential,
        destination_referential,
        name = None,
        description = None ):
    if name is None and isinstance( transformation, DiskItem ):
      if transformation.type is not None:
        name = transformation.type.name
      else:
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
      transformation.setMinf( 'description', description )
    try:
      #transformation.saveMinf()
      neuroHierarchy.databases.insertDiskItem( transformation, update=True )
    except:
      pass


  def findOrCreateReferential( self, referentialType,
                              diskItem,
                              name = None,
                              description = None,
                              dimension_count = 3,
                              simulation = False, assign=False,
                              output_diskitem = None ):
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
                              simulation = True,
                              output_diskitem = output_diskitem )
    if result is not None:
      if not simulation:
        if not result.isReadable():
          try:
            result.createParentDirectory()
            result.saveMinf()
            neuroHierarchy.databases.insertDiskItem( result, update=True )
          except OSError:
            result = None
        else:
          # in case it is not inserted in a database
          result.saveMinf()
          neuroHierarchy.databases.insertDiskItem( result, update=True )
        if assign:
          if str(result.uuid()) != oldref and diskItem.isWriteable():
            diskItem.setMinf( 'referential', result.uuid() )
            #diskItem.saveMinf()
            neuroHierarchy.databases.insertDiskItem( diskItem, update=True )

    return result


#------------------------------------------------------------------------------
_transformationManager = None


#------------------------------------------------------------------------------
def getTransformationManager():
  global _transformationManager
  if _transformationManager is None:
    _transformationManager = DatabasesTransformationManager()
  return _transformationManager

#------------------------------------------------------------------------------
# standard referentials
talairachACPCReferentialId = uuid.Uuid(
  'a2a820ac-a686-461e-bcf8-856400740a6c' )
talairachMNIReferentialId = uuid.Uuid(
  '803552a6-ac4d-491d-99f5-b938392b674b' )
globallyRegistredSPAMReferentialId = uuid.Uuid(
  '5f83f18d-e211-6705-99a0-720c4707901b' )
