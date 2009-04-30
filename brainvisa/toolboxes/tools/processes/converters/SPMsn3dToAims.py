# Copyright CEA and IFR 49 (2000-2005)
#
#  This software and supporting documentation were developed by
#      CEA/DSV/SHFJ and IFR 49
#      4 place du General Leclerc
#      91401 Orsay cedex
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

from neuroProcesses import *
import shfjGlobals, neuroConfig
import errno
import registration
try:
  #errorToDisableScipyVersion() # fail until it is a bit tested and debugged.
  import scipy
  from scipy.io import loadmat
  import numpy
  from soma import aims
except:
  loadmat = None
  import matlabValidation

name = 'SPM sn3d to AIMS transformation converter'
roles = ( 'converter', )
userLevel=1

def validation():
  if loadmat is None:
    raise ValisationError( 'no scipy matlab .mat IO functionality' )

signature = Signature(
  'read', ReadDiskItem( 'SPM normalization matrix', 'Matlab file',
                        enableConversion = 0 ),
  'write', WriteDiskItem( 'Transformation matrix', 'Transformation matrix', 
     requiredAttributes = { 'destination_referential' : \
      registration.talairachMNIReferentialId } ),
  'target', Choice( 'MNI template', 'MNI template in AIMS orientation',
    'normalized_volume in AIMS orientation' ),
  'normalized_volume', ReadDiskItem( '4D Volume', 
     shfjGlobals.aimsVolumeFormats, 
     requiredAttributes = { 'referential' : \
      registration.talairachMNIReferentialId } ),
  'removeSource', Boolean(),
)

def initialization( self ):
  self.removeSource = 0
  self.linkParameters( 'write', 'read' )
  self.linkParameters( 'normalized_volume', 'read' )
  self.setOptional( 'normalized_volume' )

def execution( self, context ):
  filetype = self.read.type
  if filetype is getDiskItemType( 'SPM99 normalization matrix' ) \
     or self.read.fullName()[-5:] == '_sn3d':
    spm2 = 0
  else:
    spm2 = 1

  tm = registration.getTransformationManager()
  if spm2:
    srcim = self.read.fullName()[:-3]
  else:
    srcim = self.read.fullName()[:-5]
  srcref = None
  try:
    context.write( 'source volume:', srcim )
    atts = shfjGlobals.aimsFileInfo( srcim )
    r = atts.get( 'referential', None )
    if r:
      srcref = tm.referential( r )
      context.write( 'source_referential:', srcref.uuid() )
  except:
    atts = {}
  if not srcref:
    context.warning( 'source referential cannot be determined, ' \
    'I will not set it on the output transformation' )

  nim = self.normalized_volume
  if self.target != 'normalized_volume in AIMS orientation' or nim is None \
    or not nim.isReadable():
    #context.write( 'Can\'t find normalized image, calculating transformation'
                   #'to the template, not to the normalized image' )
    hasnorm = 0
    if self.target == 'normalized_volume in AIMS orientation':
      raise RuntimeError( \
    _t_( 'normalized_volume shoud be specified when using this target mode' ) )
  else:
    context.write( 'normalized image: ', nim.fullPath(), '\n' )
    hasnorm = 1
    attrs = shfjGlobals.aimsVolumeAttributes( nim )
    nvs = attrs[ 'voxel_size' ][ :3 ]
    ndim = attrs[ 'volume_dimension' ][ :3 ]
    t1 = aims.Motion( attrs[ 'transformations' ][0] )
    s2m = aims.Motion( attrs[ 'storage_to_memory' ] )
    mvs = aims.Motion()
    mvs.rotation().setValue( nvs[0], 0, 0 )
    mvs.rotation().setValue( nvs[1], 1, 1 )
    mvs.rotation().setValue( nvs[2], 2, 2 )
    tn = t1 * s2m * mvs
    norg = tn.inverse().transform( aims.Point3df( 0, 0, 0 ) )
    norg += aims.Point3df( 1, 1, 1 ) # add 1 to matlab coords
    destref = tm.referential( nim )

  if hasnorm:
    vsN = numpy.transpose( numpy.mat( nvs ) )
    dimN = numpy.transpose( numpy.mat( ndim ) )
    orgN = numpy.transpose( numpy.mat( norg ) )

  sn3d = loadmat( self.read.fullPath() )

  if spm2:
    VF = sn3d[ 'VF' ]
    VG = sn3d[ 'VG' ]
    spm5 = False
    newmat = False
    if [ int(x) for x in scipy.version.version.split('.') ] >= [ 0, 7 ]:
      # mat format representation has changed...
      newmat = True
      VF = VF[0,0]
      VG = VG[0,0]
    if len(numpy.where(numpy.diag(numpy.diag(VF.mat[:3,:3])) \
            ==VF.mat[:3,:3])[0]) != 9:
      spm5 = True
    MA = numpy.mat( VF.mat ).astype( numpy.double )
    MT = numpy.mat( VG.mat ).astype( numpy.double )
    dimA = numpy.transpose( numpy.mat( VF.dim[:3] ).astype( numpy.double ) )
    dimT = numpy.transpose( numpy.mat( VG.dim[:3] ).astype( numpy.double ) )
    Affine = numpy.mat( sn3d[ 'Affine' ] ).astype( numpy.double )
  else:
    Dims = numpy.mat( sn3d[ 'Dims' ] ).astype( numpy.double )
    Affine = numpy.mat( sn3d[ 'Affine' ] ).astype( numpy.double )
    MF = numpy.mat( sn3d[ 'MF' ] ).astype( numpy.double )
    MG = numpy.mat( sn3d[ 'MG' ] ).astype( numpy.double )
    dimA = numpy.transpose( Dims[ 4, : ] )
    dimT = numpy.transpose( Dims[ 0, : ] )
    if Affine[ 0, 0 ] < 0:
      # input image in radio convention
      MA = numpy.mat( numpy.diag( [ -1., 1., 1., 1. ] ) ) * MF
    else:
      # input image in neuro convention
      MA = MF
    MT = MG

  ASA = None
  if spm5:
    try:
      # test atts
      s2mv = atts[ 'storage_to_memory' ]
      s2m = numpy.mat( [ s2mv[:4], s2mv[4:8], s2mv[8:12], s2mv[12:16] ] )
      vsA = numpy.mat( numpy.diag( [1.,1.,1.,1.] ) )
      vsA[0:3,0:3] = numpy.diag( atts[ 'voxel_size' ][:3] )
      ASA = MA * numpy.linalg.inv( vsA * s2m )
    except:
      context.warning( 'Source image or header information could not be ' \
        'accessed. The resulting transformation may be wrong due to missing ' \
        'information.' )
  if ASA is None:
    vsA = numpy.transpose( numpy.abs( numpy.mat( numpy.diag( \
      MA[ 0:3, 0:3 ] ) ) ) )
    vsT = numpy.transpose( numpy.abs( numpy.mat( numpy.diag( \
      MT[ 0:3, 0:3 ] ) ) ) )

    # if no normalized volume, take the template instead
    if not hasnorm:
      vsN = vsT
      dimN = dimT

    # translation to origin
    OA = numpy.mat( numpy.diag( [ 1., 1., 1., 1.] ) )
    OA[ 0:3,3 ] = - numpy.abs( numpy.transpose( numpy.mat( numpy.diag( \
      MA[0:3,0:3] ) ) ) + MA[ 0:3,3 ] )

    # Flip Aims -> SPM standard refs
    # (and change org to other side of image)
    FA = numpy.mat( numpy.diag( [ -1., -1., -1., 1. ] ) )
    FA[ 0:3, 3 ] = numpy.multiply( (dimA - 1), vsA )

    # Aims -> SPM with origin:
    ASA = OA * FA

  if self.target == 'MNI template':
    # MT * Affine^-1 * MA^-1 * ASA
    AIMS = MT * numpy.linalg.inv(Affine) * numpy.linalg.inv(MA) * ASA
    destref = tm.referential( registration.talairachMNIReferentialId )

  else:
    # same for normalized refs:
    ASN = None
    if spm5:
      try:
        # test atts
        s2mv = attrs[ 'storage_to_memory' ]
        s2m = numpy.mat( [ s2mv[:4], s2mv[4:8], s2mv[8:12], s2mv[12:16] ] )
        ASN = MT * numpy.linalg.inv( vsN * s2m )
      except:
        context.warning( 'Destination image or header information could not ' \
          'be accessed. The resulting transformation may be wrong due to ' \
          'missing information.' )
    if ASN is None:
      # translation to origin
      ON = numpy.mat( numpy.diag( [ 1., 1., 1., 1. ] ) )
      if hasnorm:
        ON[ 0:3, 3 ] = - numpy.multiply( (orgN-1), vsN )
      else:
        ON[ 0:3, 3 ] = - numpy.abs( numpy.transpose( numpy.mat( numpy.diag( \
          MT[ 0:3, 0:3 ] ) ) ) + MT[ 0:3, 3 ] )
        # MNI ref in AIMS orientation
        destref = tm.referential( 'f3848046-b581-cae4-ecb9-d80ada0278d5' )

      # Flip Aims -> SPM standard refs
      # (and change org to other side of image)
      FN = numpy.mat( numpy.diag( [ -1, -1, -1, 1 ] ) )
      FN[ 0:3, 3 ] = numpy.multiply( (dimN - 1), vsN )

      # Aims -> SPM with origin:
      ASN = ON * FN

    # resulting Aims transformation
    AIMS = numpy.linalg.inv(ASN) * MT * numpy.linalg.inv(Affine) \
      * numpy.linalg.inv(MA) * ASA

  # return matrix in Aims output file order
  AIMSfile = numpy.zeros( ( 4, 3 ) )
  AIMSfile[ 0, : ] = numpy.transpose( AIMS[ 0:3, 3 ] )
  AIMSfile[ 1:4, 0:3 ] = AIMS[ 0:3, 0:3 ]

  # write result
  fid = file( self.write.fullPath(), 'w' )
  print >> fid, '%f %f %f' % tuple( AIMSfile[ 0, : ] )
  print >> fid, '%f %f %f' % tuple( AIMSfile[ 1, : ] )
  print >> fid, '%f %f %f' % tuple( AIMSfile[ 2, : ] )
  print >> fid, '%f %f %f' % tuple( AIMSfile[ 3, : ] )
  fid.close()

  tm.setNewTransformationInfo( self.write, srcref, destref )

  if self.removeSource:
    for f in self.read.fullPaths():
      os.unlink( f )

