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
from neuroHierarchy import databases
import shfjGlobals
import registration
"""
This process search for a specific importer according to the type of output and execute it. 
If there is no specific importer, ImportData process is called (it only copy files).
"""
userLevel=0

signature=Signature(
  'input', ReadDiskItem( 'Any Type', getAllFormats() ),
  'output', WriteDiskItem( 'Any Type', getAllFormats() ),
  'data_type', Choice( 'Any Type' ),
  'copy_referential_of', ReadDiskItem( 'Any Type', getAllFormats() ),
  'input_spm_orientation', Choice( 'Not applicable' ), 

)

def dataTypeChanged(self, dataType):
  if dataType:
    formats=list(databases.getTypesFormats(dataType))
    if not formats:
      formats=getAllFormats()
    self.signature['output']=WriteDiskItem( dataType, formats )
    self.signatureChangeNotifier.notify(self)

def orient( self, input ):
  old = getattr( self.signature[ 'input_spm_orientation' ], 'lastInput',
                  None )
  if self.input is None or old is None \
          or old.fullPath() != self.input.fullPath() \
          or self.isDefault( 'input_spm_orientation' ):
    hide = 1
    res = 'Not applicable'
    if self.input is not None:
      if self.input.format in map( getFormat, ( 'SPM image', 'Series of SPM image' ) ):
        hide = 0
        atts = shfjGlobals.aimsVolumeAttributes( self.input )
        radio = atts.get( 'spm_radio_convention' )
        if radio is not None and radio != 0:
          res = 'Radiological'
        else:
          res = 'Neurological'
    if hide:
      self.signature[ 'input_spm_orientation' ].setChoices( \
          'Not applicable' )
    else:
      self.signature[ 'input_spm_orientation' ].setChoices( 'Neurological',
                                                            'Radiological' )
  else:
    res = self.input_spm_orientation
  self.signature[ 'input_spm_orientation' ].lastInput = self.input
  return res

def initialization( self ):
  possibleTypes = [t.name for t in getAllDiskItemTypes()]
  self.signature['data_type'].setChoices(*sorted(possibleTypes))
  self.data_type='Any Type'
  self.setOptional("copy_referential_of")
  self.addLink( 'input_spm_orientation', 'input', self.orient )
  self.signature[ 'input_spm_orientation' \
                  ].linkParameterWithNonDefaultValue = 1
  self.addLink('output', 'data_type' , self.dataTypeChanged)

def execution( self, context ):
  # search for a specific importer for this data
  importer=getImporter(self.output)
  if not importer:
    importer="ImportData"
  # must pass the filename to the importer and not a diskitem because it is potentially not in the database (findValue on a diskitem that is not in the database will fail and the parameter will not be taken into account)
  context.runProcess(importer, input=self.input.fullPath(), output=self.output)
  if self.copy_referential_of:
    tm=registration.getTransformationManager()
    tm.copyReferential(self.copy_referential_of, self.output)
