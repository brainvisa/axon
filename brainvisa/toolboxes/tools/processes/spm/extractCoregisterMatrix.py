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

from brainvisa.processes import *
from brainvisa.tools.spm_registration import initializeCoregisterEstimateParameters_withSPM8DefaultValues,\
 writeCoregisteredEstimateMatFile
import nuclearImaging.SPM as spm
from soma import aims
import numpy

configuration = Application().configuration

name = 'Extract coregister matrix (using SPM Coregister Estimate Only)'
userLevel = 0

#------------------------------------------------------------------------------

def validation():
  return spm.validation(configuration)

#------------------------------------------------------------------------------

signature = Signature(
    'reference', ReadDiskItem('4D Volume', 'NIFTI-1 image'),
    'reference_referential', ReadDiskItem( 'Referential', 'Referential' ),
    'source', ReadDiskItem('4D Volume', 'NIFTI-1 image'),
    'source_referential', ReadDiskItem( 'Referential', 'Referential' ),
    'cost_fun', Choice(('Mutual Information', """'mi'"""), ('Normalized Mutual Information', """'nmi'"""), ('Entropy Correlation Coefficient', """'ecc'"""), ('Normalised Cross Correlation', """'ncc'""")),
    'sep', String(),
    'tol', String(),
    'fwhm', String(),
    'source_to_reference_trm', WriteDiskItem( 'Transformation matrix' , 'Transformation matrix' ),
    'compute_inverse_trm', Boolean(),
    'reference_to_source_trm', WriteDiskItem( 'Transformation matrix' , 'Transformation matrix' ),
  )

#------------------------------------------------------------------------------

def initialization(self):
  self.setOptional( 'reference_referential', 'source_referential' )
  initializeCoregisterEstimateParameters_withSPM8DefaultValues( self )

  self.signature['cost_fun'].userLevel = 1
  self.signature['sep'].userLevel = 1
  self.signature['tol'].userLevel = 1
  self.signature['fwhm'].userLevel = 1

  self.addLink( None, 'compute_inverse_trm', self.updateSignature )

def updateSignature( self, proc ):
  signature = self.signature
  if self.compute_inverse_trm:
    signature[ 'reference_to_source_trm' ].userLevel = 1
    signature[ 'reference_to_source_trm' ].mandatory = True
  else:
    signature[ 'reference_to_source_trm' ].userLevel = 3
    signature[ 'reference_to_source_trm' ].mandatory = False
  self.changeSignature( signature )


def execution(self, context):
  print "\n start ", name, "\n"

  source_path = self.source.fullPath()
  source_dir = source_path[:source_path.rindex('/')]
  spm_job_file = source_dir + '/coregisterSPM_estimate_job.m'

  reference_path = self.reference.fullPath()

  source_reseted = context.temporary( 'NIFTI-1 image' )
  self.resetInternalTransformation( context, source_path, source_reseted.fullPath() )

  reference_reseted = context.temporary( 'NIFTI-1 image' )
  self.resetInternalTransformation( context, reference_path, reference_reseted.fullPath() )

  matfilePath = writeCoregisteredEstimateMatFile( context, \
                                                  sourcePath=source_reseted.fullPath(), \
                                                  refPath=reference_reseted.fullPath(), \
                                                  spmJobFile=spm_job_file, \
                                                  othersPath=None, \
                                                  cost_fun=self.cost_fun, \
                                                  sep=self.sep, \
                                                  tol=self.tol, \
                                                  fwhm=self.fwhm \
                                                )

  spm.run( context, configuration, matfilePath )

  source_reseted.clearMinf()
  reference_reseted.clearMinf()

  self.writeCoregisterMatrix( source_reseted.fullPath(), reference_reseted.fullPath(), self.source_to_reference_trm.fullPath() )

  if not None in [ self.source_referential, self.reference_referential ]:
    source_uuid = readMinf( self.source_referential.fullPath() )[0][ 'uuid' ]
    reference_uuid = readMinf( self.reference_referential.fullPath() )[0][ 'uuid' ]
    self.source_to_reference_trm.updateMinf( { 'source_referential':source_uuid, \
                                               'destination_referential':reference_uuid \
                                             }
                                           )


  if self.compute_inverse_trm:
    context.runProcess( 'matrixInvert', \
                        transformation=self.source_to_reference_trm.fullPath(), \
                        inverted_transformation=self.reference_to_source_trm.fullPath() \
                      )
    if not None in [ self.source_referential, self.reference_referential ]:
      source_uuid = readMinf( self.source_referential.fullPath() )[0][ 'uuid' ]
      reference_uuid = readMinf( self.reference_referential.fullPath() )[0][ 'uuid' ]
      self.source_to_reference_trm.updateMinf( { 'source_referential':reference_uuid, \
                                                 'destination_referential':source_uuid \
                                               }
                                             )

  print "\n stop ", name, "\n"

def resetInternalTransformation( self, context, source_path, source_reseted_path ):
  context.runProcess( 'resetInternalImageTransformation', \
                      input_image=source_path, \
                      output_image=source_reseted_path \
                    )

def writeCoregisterMatrix(self, source_path, reference_path, output_path):

  source_vol = aims.read( source_path )
  source_aligned_trm = aims.AffineTransformation3d(source_vol.header()['transformations'][1])
  reference_vol = aims.read( reference_path )
  #If reference volume has two transformations (scanner + aligned)
  #the "aligned" trm of source "go" to the "aligned" of reference
  #else go to the "scanner" of reference
  if len(reference_vol.header()['transformations']) > 1:
    reference_aligned_trm = aims.AffineTransformation3d(reference_vol.header()['transformations'][1])
    reference_trm = reference_aligned_trm.inverse()
  else:
    reference_scanner_trm = aims.AffineTransformation3d(reference_vol.header()['transformations'][0])
    reference_trm = reference_scanner_trm.inverse()

  aims.write( reference_trm * source_aligned_trm, output_path )




