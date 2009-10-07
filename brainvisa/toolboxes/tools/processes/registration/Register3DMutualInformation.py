# -*- coding: iso-8859-1 -*-

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


from neuroProcesses import *
import shfjGlobals
from brainvisa import anatomist
import os

name = 'Rigid registration with mutual information'
userLevel = 0

signature = Signature(
  
  'source_image', ReadDiskItem( '4D Volume', shfjGlobals.aimsVolumeFormats ),
  'reference_image', ReadDiskItem( '4D Volume', shfjGlobals.aimsVolumeFormats ),
  'source_to_reference', WriteDiskItem( 'Transformation matrix', 'Transformation matrix' ),
  'reference_to_source', WriteDiskItem( 'Transformation matrix', 'Transformation matrix' ),
  
  'init_with_gravity_center',Boolean(),
  'reference_threshold', Float(),
  'source_threshold', Float(),
  
  'reference_reduction_factor', Integer(), # 0, 1 (reduction facteur 8), 2 (reduction facteur 64), taille voxel isotrope
  
  'initial_translation_x', Float(),
  'initial_translation_y', Float(),
  'initial_translation_z', Float(),
  'initial_rotation_x', Float(),
  'initial_rotation_y', Float(),
  'initial_rotation_z', Float(),
  'step_translation_x', Float(),
  'step_translation_y', Float(),
  'step_translation_z', Float(),
  'step_rotation_x', Float(),
  'step_rotation_y', Float(),
  'step_rotation_z', Float(),
  'error_epsilon', Float(),
  'resampled_image', WriteDiskItem( '4D Volume', shfjGlobals.aimsWriteVolumeFormats ),
  'resampled_interpolation', Choice ( ('nearest neighbor', 0),
                            ('linear', 1), 
                            ('quadratic', 2), 
                            ('cubic', 3), 
                            ('quartic', 4), 
                            ('quintic', 5), 
                            ('galactic', 6), 
                            ('intergalactic', 7) ),
  )

#def validation():
  #anatomist.validation()

def initialization( self ):
  self.setOptional( 'initial_translation_x' )
  self.setOptional( 'initial_translation_y' )
  self.setOptional( 'initial_translation_z' )
  self.setOptional( 'initial_rotation_x' )
  self.setOptional( 'initial_rotation_y' )
  self.setOptional( 'initial_rotation_z' )
  
  self.setOptional( 'step_translation_x' )
  self.setOptional( 'step_translation_y' )
  self.setOptional( 'step_translation_z' )
  self.setOptional( 'step_rotation_x' )
  self.setOptional( 'step_rotation_y' )
  self.setOptional( 'step_rotation_z' )
  
  self.reference_reduction_factor=0
  self.init_with_gravity_center = True
  self.reference_threshold = 0.05
  self.source_threshold = 0.1 
  self.error_epsilon = 0.01
  self.setOptional( 'resampled_image' )
  self.resampled_interpolation = 1
  
def execution( self, context ):
  
  #IMAGE REF :
  reference_image = self.reference_image
  dims = self.reference_image.get( 'volume_dimension',  [ 1, 1, 1, 1 ] )
  if dims[ 3 ] > 1:
    reference_image = context.temporary( 'GIS Image' )
    context.warning( 'Reference image is a 4D Volume ==> Conversion to 3D' )
    context.system( 'AimsSumFrame', '-i', self.reference_image, '-o', reference_image )


  #IMAGE TEST :
  source_image = self.source_image
  dims = self.source_image.get( 'volume_dimension',  [ 1, 1, 1, 1 ] )
  if dims[ 3 ] > 1:
    source_image = context.temporary( 'GIS Image' )
    context.warning('Test image is a 4D Volume ==> Conversion to 3D')
    context.system( 'AimsSumFrame', '-i', self.source_image, '-o', source_image )


  command = [ 'AimsMIRegister', 
    '-r', reference_image, 
    '-t', source_image, 
    '--dir', self.source_to_reference,
    '--inv', self.reference_to_source, 
    '--index', 'mi',
    '--refstartpyr', self.reference_reduction_factor,
    '--seuilref', self.reference_threshold,
    '--seuiltest', self.source_threshold, 
    '--error', self.error_epsilon
  ]
  
  if self.init_with_gravity_center:
    command += [ '--gcinit', 'yes' ]
  else:
    command += [ '--gcinit', 'no' ]
  
  if self.initial_translation_x is not None:
    command += [ '--Tx', self.initial_translation_x]
  if self.initial_translation_y is not None:
    command += [ '--Ty', self.initial_translation_y]
  if self.initial_translation_z is not None:
    command += [ '--Tz', self.initial_translation_z]
  if self.initial_rotation_x is not None:
    command += [ '--Rx', self.initial_rotation_x]
  if self.initial_rotation_y is not None:
    command += [ '--Ry', self.initial_rotation_y]
  if self.initial_rotation_z is not None:
    command += [ '--Rz', self.initial_rotation_z]
  
  if self.step_translation_x is not None:
    command += [ '--dTx', self.step_translation_x]
  if self.step_translation_y is not None:
    command += [ '--dTy', self.step_translation_y]
  if self.step_translation_z is not None:
    command += [ '--dTz', self.step_translation_z]
  if self.step_rotation_x is not None:
    command += [ '--dRx', self.step_rotation_x]
  if self.step_rotation_y is not None:
    command += [ '--dRy', self.step_rotation_y]
  if self.step_rotation_z is not None:
    command += [ '--dRz', self.step_rotation_z]
  
  context.system( *command )


  if self.resampled_image is not None :
    context.runProcess( 'ApplyTransformation', 
      image = self.source_image, 
      transformation = self.source_to_reference,
      interpolation = self.resampled_interpolation,
      resampled_grid_geometry = self.source_image,
      resampled = self.resampled_image )

    #Appel de la visualisation.
    #a=anatomist.Anatomist()
    #return a.viewActivationsOnMRI( mriFile=self.reference_image, fmriFile=self.source_image, transformation=self.source_to_reference, palette=a.getPalette('RED TEMPERATURE'), mode='linear' )	


  #Ne fonctionne pas
  #context.runProcess( 'AnatomistShowRegistration', test_to_ref=self.source_to_reference, image_reference=self.reference_image, image_source=self.source_image)
