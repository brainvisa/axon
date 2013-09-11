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
from brainvisa import shelltools
import shfjGlobals, stat
import registration

from brainvisa.tools.data_management.image_importation import Importer

name = 'Import T1 MRI'
roles = ('importer',)
userLevel = 0


signature=Signature(
  'input', ReadDiskItem( 'Raw T1 MRI', 'Aims readable volume formats' ),
  'output', WriteDiskItem( 'Raw T1 MRI', [ 'gz compressed NIFTI-1 image', 'NIFTI-1 image', 'GIS image' ] ),
  'referential', WriteDiskItem( 'Referential of Raw T1 MRI', 'Referential' ),
)

def initSubject( self, inp ):
  value=self.input
  if self.input is not None and isinstance(self.input, DiskItem):
    value=self.input.hierarchyAttributes()
    if value.get("subject", None) is None:
      value["subject"]=os.path.basename(self.input.fullPath()).partition(".")[0]
  return value

def initialization( self ):
  self.addLink( "output", "input", self.initSubject )
  self.signature[ 'output' ].browseUserLevel = 3
  self.signature[ 'input' ].databaseUserLevel = 2
  self.signature[ 'referential' ].userLevel = 2
  self.setOptional( 'referential' )
  self.linkParameters( 'referential', 'output' )


def execution( self, context ):
  if self.input.format in map( getFormat,
                             ( 'SPM image', 'Series of SPM image' ) ):
    context.warning("The image is in Analyze format: be careful, the image"
                      " orientation could be wrong.")
  Importer.import_t1mri(self.input.fullPath(), self.output.fullPath())
  # force completing .minf
  minfatt = shfjGlobals.aimsVolumeAttributes( self.output )
  for x, y in minfatt.items():
    if x != "dicom":
      self.output.setMinf( x, y )
  self.output.saveMinf()
  self.output.readAndUpdateMinf( )
  # the referential can be written in the file header (nifti)
  if self.output.minf().get( 'referential', None ):
    self.output.removeMinf( 'referential' )
  tm = registration.getTransformationManager()
  if self.referential is not None:
    tm.createNewReferential( self.referential )
    tm.setReferentialTo(self.output, self.referential)
  else:
    ref = tm.createNewReferentialFor( self.output, name='Raw T1 MRI' )

