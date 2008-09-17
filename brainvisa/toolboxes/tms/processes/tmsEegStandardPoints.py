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
import shfjGlobals
import math, os


# simple vector algebra

def vectProduct( v1, v2 ):
  return ( v1[1] * v2[2] - v1[2] * v2[1],
           v1[2] * v2[0] - v1[0] * v2[2],
           v1[0] * v2[1] - v1[1] * v2[0] )

def vectDot( v1, v2 ):
  return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]

def vectAdd( v1, v2 ):
  return ( v1[0] + v2[0], v1[1] + v2[1], v1[2] + v2[2] )

def vectMult( v1, x ):
  return map( lambda y: y*x, v1 )

def vectNorm( v ):
  return math.sqrt( v[0]*v[0] + v[1]*v[1] + v[2]*v[2] )

def planeFromPoints( p1, p2, p3 ):
  v1 = vectAdd( p2, vectMult( p1, -1 ) )
  v2 = vectAdd( p3, vectMult( p1, -1 ) )
  n = vectProduct( v1, v2 )
  n = vectMult( n, 1 / vectNorm( n ) )
  return ( n[0], n[1], n[2], -vectDot( n, p1 ) )

def plane( peq, p ):
  return vectDot( peq[ :3 ], p ) + peq[3]

# call to AimsMeshLineMeasurement
def lineMeasurement( *args ):
  cargs = map( lambda x: str( x ), args )
  cmd = 'AimsMeshLineMeasurement "' + string.join( cargs, '" "' ) + '"'
  #print cmd
  c = os.popen( cmd )
  res = c.readlines()[ -3: ]
  c.close()
  # print res
  reg = re.compile( '(.*):\s+([0-9]+), position:\s+\(\s*(-?[0-9\.]+)\s*,' \
                    '\s*(-?[0-9\.]+)\s*,\s*(-?[0-9\.]+)\s*\)\s*,\s*dist:' \
                    '\s+([0-9.]+)' )
  pts = {}
  for i in xrange( 3 ):
    l = reg.match( res[i] )
    # print l.group(1), l.group(2), l.group(3), 
    pts[ l.group(1) ] = ( ( float( l.group(3) ), float( l.group(4) ),
                            float( l.group(5) ) ), l.group(2), l.group(6) )
  return pts


signature = Signature(
  'head_mesh', ReadDiskItem( 'Head mesh', shfjGlobals.aimsMeshFormats ),
  'nasion', Point3D(),
  'inion', Point3D(),
  'left_ear', Point3D(),
  'right_ear', Point3D(),
  'texture', WriteDiskItem( 'Texture', 'Texture' ),
  )

def initialization( self ):
  self.signature[ 'nasion' ].add3DLink( self, 'head_mesh' )
  self.signature[ 'inion' ].add3DLink( self, 'head_mesh' )
  self.signature[ 'left_ear' ].add3DLink( self, 'head_mesh' )
  self.signature[ 'right_ear' ].add3DLink( self, 'head_mesh' )
  self.linkParameters( 'texture', 'head_mesh' )
  self.setOptional( 'texture' )

def execution( self, context ):
  # convert points to tuples
  inion = ( self.inion[0], self.inion[1], self.inion[2] )
  nasion = ( self.nasion[0], self.nasion[1], self.nasion[2] )
  left_ear = ( self.left_ear[0], self.left_ear[1], self.left_ear[2] )
  right_ear = ( self.right_ear[0], self.right_ear[1], self.right_ear[2] )

  # interhemi plane: includes nasion and inion, as othogonal as possible to
  # the ears line
  v1 = vectAdd( inion, vectMult( nasion, -1 ) )
  v2 = vectAdd( right_ear, vectMult( left_ear, -1 ) )
  v3 = vectProduct( v1, v2 )
  n = vectProduct( v1, v3 )
  n = vectMult( n, 1 / vectNorm( n ) )
  ihplane = ( n[0], n[1], n[2], -vectDot( n, nasion ) )
  centear = vectMult( vectAdd( left_ear, right_ear ) , 0.5 )
  context.write( 'ear mid-point: ', centear, '\n' )
  context.write( 'interhemi plane: ', ihplane, '\n' )
  context.write( 'distance ear mid-point - IH plane: ',
                 abs( plane( ihplane, centear ) ), ' mm\n' )

  # get vertex point
  texargs = []
  if self.texture is not None:
    texargs = [ '-o', self.texture ]

  lm = lineMeasurement( *( [ '-i', self.head_mesh, '-p1', nasion, '-p2',
                             inion, '-m', 'plane', '-pe', ihplane,
                             '-r', 0.5, '-pe2',
                             (0,0,-1,nasion[2]) ] + texargs ) )[ 'target' ]
  vertex = lm[0]
  context.write( 'vertex: ', vertex, '\n' )

  # get C3 point
  if self.texture is not None:
    tmp = context.temporary( 'Texture' )
    texargs = [ '-o', tmp ]

  earplane = planeFromPoints( left_ear, right_ear, vertex )
  lm = lineMeasurement( *( [ '-i', self.head_mesh, '-p1', vertex, '-p2',
                             left_ear, '-m', 'plane', '-pe', earplane,
                             '-r', 0.1, '-pe2',
                             (-1,0,0,nasion[0]) ] + texargs ) )[ 'target' ]
  left_C3 = lm[0]
  context.write( 'left_C3: ', left_C3, '\n' )
  if self.texture is not None:
    context.system( 'AimsLinearComb', '-i', tmp, '-j', self.texture, '-o',
                    self.texture )

  lm = lineMeasurement( *( [ '-i', self.head_mesh, '-p1', vertex, '-p2',
                             right_ear, '-m', 'plane', '-pe', earplane,
                             '-r', 0.1, '-pe2',
                             (1,0,0,-nasion[0]) ] + texargs ) )[ 'target' ]
  right_C3 = lm[0]
  context.write( 'right_C3: ', right_C3, '\n' )
  if self.texture is not None:
    context.system( 'AimsLinearComb', '-i', tmp, '-j', self.texture, '-o', 
                    self.texture )

  # get T5 point
  n2 = vectProduct( v1, n )
  n2 = vectMult( n2, 1 / vectNorm( n2 ) )
  axialplane = ( n2[0], n2[1], n2[2], -vectDot( n2, nasion ) )
  context.write( 'axial plane: ', axialplane, '\n' )
  lm = lineMeasurement( *( [ '-i', self.head_mesh, '-p1', inion, '-p2',
                             nasion, '-m', 'plane', '-pe', axialplane,
                             '-r', 0.35, '-pe2',
                             (-1,0,0,nasion[0]) ] + texargs ) )[ 'target' ]
  left_T5 = lm[0]
  context.write( 'left_T5: ', left_T5, '\n' )
  if self.texture is not None:
    context.system( 'AimsLinearComb', '-i', tmp, '-j', self.texture, '-o',
                    self.texture )

  lm = lineMeasurement( *( [ '-i', self.head_mesh, '-p1', inion, '-p2',
                             nasion, '-m', 'plane', '-pe', axialplane,
                             '-r', 0.35, '-pe2',
                             (1,0,0,-nasion[0]) ] + texargs ) )[ 'target' ]
  right_T5 = lm[0]
  context.write( 'right_T5: ', right_T5, '\n' )
  if self.texture is not None:
    context.system( 'AimsLinearComb', '-i', tmp, '-j', self.texture, '-o',
                    self.texture )

  # get CP5 point
  lm = lineMeasurement( *( [ '-i', self.head_mesh, '-p1', left_C3, '-p2',
                             left_T5, '-r', 0.5 ] + texargs ) )[ 'target' ]
  left_CP5 = lm[0]
  context.write( 'left_CP5: ', left_CP5, '\n' )
  if self.texture is not None:
    context.system( 'AimsLinearComb', '-i', tmp, '-j', self.texture, '-o',
                    self.texture )

  lm = lineMeasurement( *( [ '-i', self.head_mesh, '-p1', right_C3, '-p2',
                             right_T5, '-r', 0.5 ] + texargs ) )[ 'target' ]
  right_CP5 = lm[0]
  context.write( 'right_CP5: ', right_CP5, '\n' )
  if self.texture is not None:
    context.system( 'AimsLinearComb', '-i', tmp, '-j', self.texture, '-o', 
                    self.texture )
