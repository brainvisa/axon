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
import shfjGlobals

name = 'Tms Target Pipeline'
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
  'cone_mesh', WriteDiskItem( 'Mesh', shfjGlobals.aimsMeshFormats ),
  'stimulation_zone', WriteDiskItem( 'Bucket', 'Bucket' ),
  'normal_mesh', WriteDiskItem( 'Mesh', shfjGlobals.aimsMeshFormats ),
  'target_line_mesh', WriteDiskItem( 'Mesh', shfjGlobals.aimsMeshFormats ),
  'base_radius', Float(),
  'depth', Float(),
  'grey_matter_mask', ReadDiskItem( 'Grey White Mask',
    shfjGlobals.aimsVolumeFormats ),
  'view_results', Boolean(),
)

def initialization( self ):
  eNode = SerialExecutionNode( self.name, parameterized=self )
  eNode.addChild( 'TMS Target',
                   ProcessExecutionNode( 'tmsTarget', optional = 1 ) )
  eNode.addChild( 'TMS Stimulation Zone',
                   ProcessExecutionNode( 'tmsStimulationZone', optional = 1 ) )

  self.setOptional( 'nasion' )
  self.setOptional( 'vertex' )
  self.setOptional( 'inion' )
  self.setOptional( 'left_ear' )
  self.setOptional( 'right_ear' )
  self.setOptional( 'stimulation_zone' )
  self.setOptional( 'normal_mesh' )
  self.setOptional( 'target_line_mesh' )
  self.setOptional( 'grey_matter_mask' )

  self.base_radius = 30
  self.depth = 50

  eNode.addLink( 'TMS Target.head_mesh', 'head_mesh' )
  eNode.addLink( 'head_mesh', 'TMS Target.head_mesh' )
  eNode.addLink( 'TMS Target.landmarks', 'landmarks' )
  eNode.addLink( 'landmarks', 'TMS Target.landmarks' )
  eNode.addLink( 'TMS Target.nasion', 'nasion' )
  eNode.addLink( 'nasion', 'TMS Target.nasion' )
  eNode.addLink( 'TMS Target.vertex', 'vertex' )
  eNode.addLink( 'vertex', 'TMS Target.vertex' )
  eNode.addLink( 'TMS Target.inion', 'inion' )
  eNode.addLink( 'inion', 'TMS Target.inion' )
  eNode.addLink( 'TMS Target.left_ear', 'left_ear' )
  eNode.addLink( 'left_ear', 'TMS Target.left_ear' )
  eNode.addLink( 'TMS Target.right_ear', 'right_ear' )
  eNode.addLink( 'right_ear', 'TMS Target.right_ear' )
  eNode.addLink( 'TMS Target.target', 'target' )
  eNode.addLink( 'target', 'TMS Target.target' )
  eNode.addLink( 'TMS Target.target_texture', 'target_texture' )
  eNode.addLink( 'target_texture', 'TMS Target.target_texture' )
  eNode.addLink( 'TMS Target.view_results', 'view_results' )
  eNode.addLink( 'view_results', 'TMS Target.view_results' )

  self.signature[ 'nasion' ].add3DLink( self, 'head_mesh' )
  self.signature[ 'vertex' ].add3DLink( self, 'head_mesh' )
  self.signature[ 'inion' ].add3DLink( self, 'head_mesh' )
  self.signature[ 'left_ear' ].add3DLink( self, 'head_mesh' )
  self.signature[ 'right_ear' ].add3DLink( self, 'head_mesh' )
  self.signature[ 'target' ].add3DLink( self, 'head_mesh' )

  eNode.addLink( 'TMS Stimulation Zone.head_mesh', 'head_mesh' )
  eNode.addLink( 'head_mesh', 'TMS Stimulation Zone.head_mesh' )
  eNode.addLink( 'TMS Stimulation Zone.landmarks', 'landmarks' )
  eNode.addLink( 'landmarks', 'TMS Stimulation Zone.landmarks' )
  eNode.addLink( 'TMS Stimulation Zone.stimulation_position', 'target' )
  eNode.addLink( 'target', 'TMS Stimulation Zone.stimulation_position' )
  eNode.addLink( 'TMS Stimulation Zone.cone_mesh', 'cone_mesh' )
  eNode.addLink( 'cone_mesh', 'TMS Stimulation Zone.cone_mesh' )
  eNode.addLink( 'TMS Stimulation Zone.stimulation_zone', 'stimulation_zone' )
  eNode.addLink( 'stimulation_zone', 'TMS Stimulation Zone.stimulation_zone' )
  eNode.addLink( 'TMS Stimulation Zone.normal_mesh', 'normal_mesh' )
  eNode.addLink( 'normal_mesh', 'TMS Stimulation Zone.normal_mesh' )
  eNode.addLink( 'TMS Stimulation Zone.target_line_mesh', 'target_line_mesh' )
  eNode.addLink( 'target_line_mesh', 'TMS Stimulation Zone.target_line_mesh' )
  eNode.addLink( 'TMS Stimulation Zone.base_radius', 'base_radius' )
  eNode.addLink( 'base_radius', 'TMS Stimulation Zone.base_radius' )
  eNode.addLink( 'TMS Stimulation Zone.depth', 'depth' )
  eNode.addLink( 'depth', 'TMS Stimulation Zone.depth' )
  eNode.addLink( 'TMS Stimulation Zone.grey_matter_mask', 'grey_matter_mask' )
  eNode.addLink( 'grey_matter_mask', 'TMS Stimulation Zone.grey_matter_mask' )
  eNode.addLink( 'TMS Stimulation Zone.view_results', 'view_results' )
  eNode.addLink( 'view_results', 'TMS Stimulation Zone.view_results' )

  self.setExecutionNode( eNode )
