# Copyright CEA and IFR 49 (2008)
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
import shfjGlobals, registration, neuroConfig

name = 'Tms Stimulation Zone'
userLevel = 0

signature = Signature(
  'head_mesh', ReadDiskItem( 'Head Mesh', shfjGlobals.aimsMeshFormats ),
  'landmarks', ReadDiskItem( 'TMS position file', 'TMS position file' ),
  'stimulation_position', Point3D(),
  'cone_mesh', WriteDiskItem( 'Mesh', shfjGlobals.aimsMeshFormats ),
  'stimulation_zone', WriteDiskItem( 'Bucket', 'Bucket' ),
  'normal_mesh', WriteDiskItem( 'Mesh', shfjGlobals.aimsMeshFormats ),
  'target_line_mesh', WriteDiskItem( 'Mesh', shfjGlobals.aimsMeshFormats ),
  'base_radius', Float(),
  'depth', Float(),
  'normal_radius', Float(),
  'grey_matter_mask', ReadDiskItem( 'Grey White Mask',
    shfjGlobals.aimsVolumeFormats ),
  'view_results', Boolean(),
)

class landmarkreader:
  def __init__( self, *keys ):
    self._keys = keys

  def __call__( self, values, process ):
    lmrk = None
    if values.landmarks is not None:
      lmrk = values.landmarks
    if lmrk is not None and lmrk.isReadable():
      f = open( lmrk.fullPath() )
      for l in f.readlines():
        ls = l.split()
        if len(ls) >= 2 and len(ls[0]) >= 2 and ls[0][:-1] in self._keys:
          return [ float(x) for x in ls[1:] ]
    return None

def initialization( self ):
  self.base_radius = 30
  self.depth = 50
  self.normal_radius = 20
  self.view_results = True
  self.setOptional( 'stimulation_zone' )
  self.setOptional( 'normal_mesh' )
  self.setOptional( 'target_line_mesh' )
  self.setOptional( 'grey_matter_mask' )
  self.setOptional( 'landmarks' )
  self.signature[ 'stimulation_position' ].add3DLink( self, 'head_mesh' )
  self.linkParameters( 'stimulation_position', 'landmarks',
    landmarkreader( 'target' ) )
  self.linkParameters( 'grey_matter_mask', 'head_mesh' )
  #self.linkParameters( 'cone_mesh', 'head_mesh' )
  #self.linkParameters( 'normal_mesh', 'cone_mesh' )

def execution( self, context ):
  if self.stimulation_zone and not self.grey_matter_mask:
    raise ValueError( 'grey_matter_mask parameter should be specified if ' \
      'stimulation_zone is specified' )
  res = context.temporary( 'Text File' )
  args = [ 'AimsTMSCone.py', '-i', self.head_mesh, '-o', self.cone_mesh,
    '-r', self.base_radius, '-d', self.depth, '-n', self.normal_radius,
    '-s', self.stimulation_position[0], self.stimulation_position[1],
    self.stimulation_position[2], '-w', res ]
  if self.normal_mesh:
    args += [ '-m', self.normal_mesh ]
  if self.target_line_mesh:
    args += [ '-t', self.target_line_mesh ]
  if self.stimulation_zone:
    args += [ '-z', self.stimulation_zone, '-b', self.grey_matter_mask,
      '-c', 100 ]
  context.system( *args )
  f = open( res.fullPath() )
  for l in f.xreadlines():
    i = l.find( ':' )
    n = l[:i]
    x = l[i+1:]
    if n == 'normal_target_angle':
      context.write( n, ':', float(x), 'radian (', float(x) / math.pi * 180,
        'degrees)' )
    else:
      #y = [ round(i, 3) for i in x ]
      context.write( n, ':', x )
  f.close()
  tm = registration.getTransformationManager()
  tm.copyReferential( self.head_mesh, self.cone_mesh )
  if self.normal_mesh:
    tm.copyReferential( self.head_mesh, self.normal_mesh )
  if self.target_line_mesh:
    tm.copyReferential( self.head_mesh, self.target_line_mesh )
  if self.stimulation_zone:
    tm.copyReferential( self.head_mesh, self.stimulation_zone )
  if self.view_results:
    good = False
    objects = []
    if neuroConfig.gui and neuroConfig.guiLoaded:
      from brainvisa import anatomist
      a = anatomist.Anatomist()
      if a:
        good = True
        cone = a.loadObject( self.cone_mesh )
        head = a.loadObject( self.head_mesh, duplicate=True )
        a.execute( 'SetMaterial', objects=[head],
          diffuse=[ 0.8, 0.8, 0.8, 0.45 ] )
        a.execute( 'SetMaterial', objects=[cone],
          diffuse=[ 1., 0., 0., 0.5 ], face_culling=0 )
        #head.setMaterial( diffuse = [ 0.8, 0.8, 0.8, 0.45 ] )
        #cone.setMaterial( diffuse = [ 1., 0., 0., 0.5 ], face_culling=0 )
        objects = [ cone, head ]
        normal = None
        if self.normal_mesh:
          normal = a.loadObject( self.normal_mesh )
          objects.append( normal )
          a.execute( 'SetMaterial', objects=[normal],
            diffuse=[ 0., 0., 1., 1. ] )
          #normal.setMaterial( diffuse=[ 0., 0., 1., 1. ] )
        if self.target_line_mesh:
          tline = a.loadObject( self.target_line_mesh )
          objects.append( tline )
          a.execute( 'SetMaterial', objects=[tline],
            diffuse=[ 0., 1., 0., 1. ] )
        zone = None
        if self.stimulation_zone:
          zone = a.loadObject( self.stimulation_zone )
          objects.append( zone )
          a.execute( 'SetMaterial', objects=[zone],
            diffuse=[ 1., 1., 0., 1. ] )
          #zone.setMaterial( diffuse = [ 1., 1., 0., 1. ] )
        w = a.createWindow( '3D' )
        w.addObjects( objects )
        objects.append( w )
    if not good:
      context.warning( 'visualization step is not executed because either ' \
        'GUI mode or Anatomist is disabled' )
    return objects
