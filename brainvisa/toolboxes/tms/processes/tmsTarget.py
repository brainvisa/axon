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

name = 'Tms Target'
userLevel = 0

signature = Signature(
  'head_mesh', ReadDiskItem( 'Head Mesh', shfjGlobals.aimsMeshFormats ),
  'landmarks', WriteDiskItem( 'TMS position file', 'TMS position file' ),
  'nasion', Point3D(),
  'vertex', Point3D(),
  'inion', Point3D(),
  'left_ear', Point3D(),
  'right_ear', Point3D(),
  'target', Point3D(),
  'target_texture', WriteDiskItem( 'Texture', 'Texture' ),
  'neighbour_estimation_size', Integer(),
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
  self.neighbour_estimation_size = 10
  self.view_results = True
  self.linkParameters( 'landmarks', 'head_mesh' )
  self.linkParameters( 'target_texture', 'landmarks' )
  self.linkParameters( 'nasion', 'landmarks', landmarkreader( 'nasion' ) )
  self.signature[ 'nasion' ].add3DLink( self, 'head_mesh' )
  self.setOptional( 'nasion' )
  self.linkParameters( 'vertex', 'landmarks', landmarkreader( 'vertex' ) )
  self.signature[ 'vertex' ].add3DLink( self, 'head_mesh' )
  self.setOptional( 'vertex' )
  self.linkParameters( 'inion', 'landmarks', landmarkreader( 'inion', 'eperon' ) )
  self.signature[ 'inion' ].add3DLink( self, 'head_mesh' )
  self.setOptional( 'inion' )
  self.linkParameters( 'left_ear', 'landmarks', landmarkreader( 'og', 'left_ear' ) )
  self.signature[ 'left_ear' ].add3DLink( self, 'head_mesh' )
  self.setOptional( 'left_ear' )
  self.linkParameters( 'right_ear', 'landmarks', landmarkreader( 'od', 'right_ear' ) )
  self.signature[ 'right_ear' ].add3DLink( self, 'head_mesh' )
  self.setOptional( 'right_ear' )
  self.linkParameters( 'target', 'landmarks', landmarkreader( 'target' ) )
  self.signature[ 'target' ].add3DLink( self, 'head_mesh' )
  #self.setOptional( 'target' )

def execution( self, context ):
  nldm = 0
  if self.nasion:
    nldm += 1
  if self.inion:
    nldm += 1
  if self.vertex:
    nldm += 1
  if self.left_ear:
    nldm += 1
  if self.right_ear:
    nldm += 1
  if nldm < 3:
    raise RuntimeError( 'At leat 3 landmark points must be provided in addition to the target' )
  if nldm != 5:
    context.warning( 'Not all landmark points have been specified. I can ' \
      'run but will be less accurate...' )
  lmrk = open( self.landmarks.fullPath(), 'w' )
  if self.nasion:
    print >> lmrk, 'nasion:', self.nasion[0], self.nasion[1], self.nasion[2]
  if self.vertex:
    print >> lmrk, 'vertex:', self.vertex[0], self.vertex[1], self.vertex[2]
  if self.inion:
    print >> lmrk, 'inion:', self.inion[0], self.inion[1], self.inion[2]
  if self.left_ear:
    print >> lmrk, 'og:', self.left_ear[0], self.left_ear[1], self.left_ear[2]
  if self.right_ear:
    print >> lmrk, 'od:', self.right_ear[0], self.right_ear[1], self.right_ear[2]
  if self.target:
    print >> lmrk, 'target:', self.target[0], self.target[1], self.target[2]
  lmrk.close()
  cmd = [ 'AimsTMStarget', '-i', self.head_mesh, '-o', self.target_texture,
    '-l', self.landmarks, '-n', self.neighbour_estimation_size ]
  context.system( *cmd )

  if self.view_results:
    good = False
    objects = []
    if neuroConfig.gui and neuroConfig.guiLoaded:
      from brainvisa import anatomist
      a = anatomist.Anatomist()
      if a:
        good = True
        texture = a.loadObject( self.target_texture )
        head = a.loadObject( self.head_mesh )
        a.execute( 'SetObjectPalette', objects=[texture], palette = 'zfun-EosA' )
        fus = a.fusionObjects( [ head, texture ], method='FusionTexSurfMethod' )
        objects = [ texture, head, fus ]
        w = a.createWindow( '3D' )
        w.addObjects( fus )
        objects.append( w )
    if not good:
      context.warning( 'visualization step is not executed because either ' \
        'GUI mode or Anatomist is disabled' )
    return objects

