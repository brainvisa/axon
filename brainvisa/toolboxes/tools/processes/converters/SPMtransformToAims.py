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
from brainvisa.processes import *
from brainvisa.configuration import neuroConfig
from brainvisa.tools import aimsGlobals
try:
  #errorToDisableScipyVersion() # fail until it is a bit tested and debugged.
  from scipy.io import loadmat
  import numpy
  from soma import aims
except:
  loadmat = None
  from brainvisa.tools import matlabValidation

name = 'SPM to AIMS transformation converter'
roles = ( 'converter', )
userLevel=1

def validation():
  if loadmat is None:
    try:
      matlabValidation.validation()
    except:
      raise ValidationError( 'no scipy matlab .mat IO functionality, and no '
        'working matlab installation available' )

signature = Signature(
  'read', ReadDiskItem( 'Transformation matrix', 'Matlab file',
                        enableConversion = 0 ),
  'write', WriteDiskItem( 'Transformation matrix', 'Transformation matrix' ),
  'source_volume', ReadDiskItem( '4D Volume',
                                 aimsGlobals.aimsVolumeFormats ),
  'registered_volume', ReadDiskItem( '4D Volume',
                                    aimsGlobals.aimsVolumeFormats ),
  'central_to_registered', ReadDiskItem( 'Transformation matrix', 
                                         'Matlab file' ), 
  'removeSource', Boolean(),
)

def initialization( self ):
  def writeName( self, proc ):
    if self.registered_volume and self.read:
      file = WriteDiskItem( 'Transformation matrix',
                            'Transformation matrix' ).findValue( self.read )
      name = file.fullPath()
      i = name.rfind( '.' )
      ext = ''
      if i >= 0:
        ext = name[i:]
        name = name[:i]
      name += 'TO' + self.registered_volume.fileName()
      i = name.rfind( '.' )
      if i >= 0:
        name = name[:i]
      name += ext
      # il manque une fonction pour fixer ca...
      file.name = name
      return file
    else:
      return WriteDiskItem( 'Transformation matrix',
                            'Transformation matrix' ).findValue( self.read )
  self.linkParameters( 'write', 'read' )
  self.linkParameters( 'source_volume', 'read' )
  self.linkParameters( 'registered_volume', 'read' )
  self.linkParameters( 'central_to_registered', 'registered_volume' )
  self.removeSource = 0
  self.setOptional( 'registered_volume' )
  self.setOptional( 'central_to_registered' )

def listToVectorString( l ):
  return '[ ' + ' '.join([str(x) for x in l]) + ' ]'


def matlabExecution( self, context ):
  aim = self.source_volume
  amat = self.read
  bim = self.registered_volume
  if self.registered_volume is not None:
    bmatname = self.registered_volume.fullName() + '.mat'
    bmat = self.central_to_registered
    if bmat is None:
      context.write( 'No destination transformation - ' \
                     'taking its origin translation' )
      # bim = None
  else:
    bmat = None
    context.write( 'No destination volume - going only to central ref' )

  aattrs = aimsGlobals.aimsVolumeAttributes( aim )
  #context.write( 'aatrs: ', aattrs )
  if bim:
    battrs = aimsGlobals.aimsVolumeAttributes( bim )
    #context.write( 'battrs: ', battrs )


  dim1 = aattrs[ 'volume_dimension' ][:3]
  vox1 = aattrs[ 'voxel_size' ][:3]
  origin1 = aattrs.get( 'spm_origin' )
  if not origin1:
      origin1 = ( 0, 0, 0 )
  if bim:
    dim2 = battrs[ 'volume_dimension' ][:3]
    vox2 = battrs[ 'voxel_size' ][:3]
    origin2 = battrs.get( 'spm_origin' )
    if not origin2:
      origin2 = ( 0, 0, 0 )
  else:
    dim2 = [ 0, 0, 0 ]
    vox2 = [ 1, 1, 1 ]
    origin2 = [ 0, 0, 0 ]

  # context.write( 'dim1:', str( dim1 ) )
  # context.write( 'vox1:', str( vox1 ) )
  # context.write( 'origin1:', str( origin1 ) )
  # context.write( 'dim2', str( dim2 ) )
  # context.write( 'vox2:', str( vox2 ) )
  # context.write( 'origin2:', str( origin2 ) )

  # create matlab script

  matlabcom = "amat = '"
  if amat:
      matlabcom += amat.fullPath()
  matlabcom += "';\n"
  if bmat:
    matlabcom += "bmat = '" + bmat.fullPath() + "';\n"
  matlabcom += "DIM1 = " + listToVectorString( dim1 ) + ";\n"
  matlabcom += "VOX1 = " + listToVectorString( vox1 ) + ";\n"
  matlabcom += "ORIGIN1 = " + listToVectorString( origin1 ) + ";\n"
  matlabcom += "DIM2 = " + listToVectorString( dim2 ) + ";\n"
  matlabcom += "VOX2 = " + listToVectorString( vox2 ) + ";\n"
  matlabcom += "ORIGIN2 = " + listToVectorString( origin2 ) + ";\n"
  matlabcom += "trans1 = '" + self.write.fullPath() + "';\n"

  matlabcom += '''if( exist( amat ) )
  a = load( amat );
  a.M = a.M * diag( [ 1/VOX1(1) 1/VOX1(2) 1/VOX1(3) 1 ] );
  disp( [ amat ' read' ] );
else
  a.M = diag( [ 1 1 1 1 ] );  % diag( [ VOX1(1) VOX1(2) VOX1(3) 1 ] );
  a.M( 1:3, 4 ) = - ( ORIGIN1 .* VOX1 )';
end

ainv = inv( a.M );
o1 = ainv( :, 4 );
% Y and Z axis are flipped
o1( 2:3 ) = -o1( 2:3 ) + ( ( DIM1(2:3) - 1 ) .* VOX1(2:3) )';

'''
  if bmat:
    matlabcom += '''if( exist( bmat ) )
  b = load( bmat );
  b.M = b.M * diag( [ 1/VOX2(1) 1/VOX2(2) 1/VOX2(3) 1 ] );
  disp( [ bmat ' read' ] );
else
  b.M = diag( [ 1 1 1 1 ] ); % diag( [ VOX2(1) VOX2(2) VOX2(3) 1 ] );
  b.M( 1:3, 4 ) = - ( ORIGIN2 .* VOX2 )';
end
'''
  else:
    matlabcom += '''b.M = diag( [ 1 1 1 1 ] ); % diag( [ VOX2(1) VOX2(2) VOX2(3) 1 ] );
b.M( 1:3, 4 ) = - ( ORIGIN2 .* VOX2 )';
'''
  matlabcom += '''binv = inv( b.M );
o2 = binv( :, 4 );
% Y and Z axis are flipped
o2( 2:3 ) = -o2( 2:3, 1 ) + ( ( DIM2(2:3) - 1 ) .* VOX2(2:3) )';

% flip Y and Z axis to go to Aims/Anatomist world
aflip = diag( [ 1 -1 -1 1 ] );
aflip( 2:3, 4 ) = ( ( DIM1(2:3) - 1 ) .* VOX1(2:3) )';
a.M = a.M * aflip;
% verify origin still transforms to 0
%a.M * o1
bflip = diag( [ 1 -1 -1 1 ] );
bflip( 2:3, 4 ) = ( ( DIM2(2:3) - 1 ) .* VOX2(2:3) )';
b.M = b.M * bflip;
% verify origin still transforms to 0
%b.M * o2

M = inv(b.M) * a.M;

disp( 'Result matrix :' );
M

%M * o1 - o2

T = M( 1:3, 4 )';


disp( [ 'writing ' trans1 ] );
fid = fopen( trans1, 'w' );
if( fid == -1 )
  disp( [ 'could not write ' trans1 ] );
  exit 1
end

fprintf( fid, '%f %f %f\\n', T );
fprintf( fid, '%f %f %f\\n', M(1:3,1:3)' );
fclose( fid );

%disp( [ 'writing ' trans2 ] );
%fid = fopen( trans2, 'w' );
%if( fid == -1 )
%  disp( [ 'could not write ' trans2 ] );
%  exit 1
%end

%M = inv( M );
%T = M( 1:3, 4 )';

%fprintf( fid, '%f %f %f\\n', T );
%fprintf( fid, '%f %f %f\\n', M(1:3,1:3)' );
%fclose( fid );

'''

  ml = matlab.matlab()
  ml.eval( matlabcom )
  if self.removeSource:
    for f in self.read.fullPaths():
      os.unlink( f )


def execution( self, context ):
  if loadmat is None:
    return self.matlabExecution( context )

  # scipy / numpy / pyaims execution
  aim = self.source_volume
  amat = self.read
  bim = self.registered_volume
  if self.registered_volume is not None:
    bmatname = self.registered_volume.fullName() + '.mat'
    bmat = self.central_to_registered
    if bmat is None:
      context.write( 'No destination transformation - ' \
                     'taking its origin translation' )
      # bim = None
  else:
    bmat = None
    context.write( 'No destination volume - going only to central ref' )

  aattrs = aimsGlobals.aimsVolumeAttributes( aim )
  #context.write( 'aatrs: ', aattrs )
  if bim:
    battrs = aimsGlobals.aimsVolumeAttributes( bim )
    #context.write( 'battrs: ', battrs )

  dim1 = aattrs[ 'volume_dimension' ][:3]
  vox1 = aattrs[ 'voxel_size' ][:3]
  t1 = aims.Motion( aattrs[ 'transformations' ][0] )
  s2m = aims.Motion( aattrs[ 'storage_to_memory' ] )
  mvox1 = aims.Motion()
  mvox1.rotation().setValue( vox1[0], 0, 0 )
  mvox1.rotation().setValue( vox1[1], 1, 1 )
  mvox1.rotation().setValue( vox1[2], 2, 2 )
  tn = t1 * s2m * mvox1
  origin1 = tn.inverse().transform( aims.Point3df( 0, 0, 0 ) )
  origin1 += aims.Point3df( 1, 1, 1 ) # add 1 to matlab coords
  if bim:
    dim2 = battrs[ 'volume_dimension' ][:3]
    vox2 = battrs[ 'voxel_size' ][:3]
    t2 = aims.Motion( battrs[ 'transformations' ][0] )
    s2m2 = aims.Motion( battrs[ 'storage_to_memory' ] )
    mvox2 = aims.Motion()
    mvox2.rotation().setValue( vox2[0], 0, 0 )
    mvox2.rotation().setValue( vox2[1], 1, 1 )
    mvox2.rotation().setValue( vox2[2], 2, 2 )
    tn = t2 * s2m2 * mvox2
    origin2 = tn.inverse().transform( aims.Point3df( 0, 0, 0 ) )
    origin2 += aims.Point3df( 1, 1, 1 ) # add 1 to matlab coords
  else:
    dim2 = [ 0, 0, 0 ]
    vox2 = [ 1, 1, 1 ]
    origin2 = [ 0, 0, 0 ]

  # context.write( 'dim1:', str( dim1 ) )
  # context.write( 'vox1:', str( vox1 ) )
  # context.write( 'origin1:', str( origin1 ) )
  # context.write( 'dim2', str( dim2 ) )
  # context.write( 'vox2:', str( vox2 ) )
  # context.write( 'origin2:', str( origin2 ) )

  # create matlab script

  DIM1 = numpy.transpose( numpy.mat( dim1 ) )
  VOX1 = numpy.transpose( numpy.mat( vox1 ) )
  ORIGIN1 = numpy.transpose( numpy.mat( origin1 ) )
  DIM2 = numpy.transpose( numpy.mat( dim2 ) )
  VOX2 = numpy.transpose( numpy.mat( vox2 ) )
  ORIGIN2 = numpy.transpose( numpy.mat( origin2 ) )
  trans1 = self.write.fullPath()

  if os.path.exists( amat.fullPath() ):
    a = loadmat( amat.fullPath() )
    aM = numpy.mat( a[ 'M' ] ).astype( numpy.double )
    aM = aM * numpy.mat( numpy.diag( [ 1./vox1[0], 1./vox1[1], 1./vox1[2],
      1. ] ) )
  else:
    aM = numpy.mat( numpy.diag( [ 1., 1., 1., 1., ] ) )
    aM[ 0:3, 3 ] = - numpy.multiply( ORIGIN1, VOX1 )

  ainv = numpy.linalg.inv( aM )
  o1 = ainv[ :, 3 ]
  # Y and Z axis are flipped
  o1[ 1:3 ] = -o1[ 1:3 ] + numpy.multiply( ( DIM1[1:3] - 1 ), VOX1[1:3] )

  if bmat:
    if os.path.exists( bmat.fullPath() ):
      b = loadmat( bmat.fullPath() );
      bM = numpy.mat( b[ 'M' ] ).astype( numpy.double )
      bM = bM * numpy.mat( numpy.diag( [ 1./vox2[0], 1./vox2[1], 1./vox2[2],
        1. ] ) )
    else:
      bM = numpy.mat( numpy.diag( [ 1., 1., 1., 1. ] ) )
      bM[ 0:3, 3 ] = - numpy.multiply( ORIGIN2, VOX2 )
  else:
    bM =  numpy.mat( numpy.diag( [ 1., 1., 1., 1. ] ) )
  bM[ 0:3, 3 ] = - numpy.multiply( ORIGIN2, VOX2 )
  binv = numpy.linalg.inv( bM )
  o2 = binv[ :, 3 ]
  # Y and Z axis are flipped
  o2[ 1:3 ] = -o2[ 1:3, 0 ] + numpy.multiply( ( DIM2[1:3] - 1 ), VOX2[1:3] )

  # flip Y and Z axis to go to Aims/Anatomist world
  aflip = numpy.mat( numpy.diag( [ 1., -1., -1., 1. ] ) )
  aflip[ 1:3, 3 ] = numpy.multiply( ( DIM1[1:3] - 1 ), VOX1[1:3] )
  aM = aM * aflip
  # verify origin still transforms to 0
  #aM * o1
  bflip = numpy.mat( numpy.diag( [ 1., -1., -1., 1. ] ) )
  bflip[ 1:3, 3 ] = numpy.multiply( ( DIM2[1:3] - 1 ), VOX2[1:3] )
  bM = bM * bflip
  # verify origin still transforms to 0
  #bM * o2

  M = numpy.linalg.inv(bM) * aM

  #M * o1 - o2

  T = numpy.array( numpy.transpose( M[ 0:3, 3 ] ) )[ 0, : ]

  context.write( 'writing ', trans1 )
  fid = open( trans1, 'w' )

  Mt = numpy.array( numpy.transpose( M[0:3,0:3] ) )
  print('%f %f %f' % tuple( T ), file=fid)
  print('%f %f %f' % tuple( Mt[ 0, : ] ), file=fid)
  print('%f %f %f' % tuple( Mt[ 1, : ] ), file=fid)
  print('%f %f %f' % tuple( Mt[ 2, : ] ), file=fid)
  fid.close()

