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


name = 'Threshold'
userLevel = 1

signature = Signature(
  'image_input', ReadDiskItem('4D Volume', 'aims readable volume formats'),
  'image_output', WriteDiskItem('4D Volume', 'aims writable volume formats'),
  'mode', Choice ( ( 'less than', 'lt' ), 
                   ( 'less or equal', 'le' ), 
                   ( 'greater than', 'gt' ),
                   ( 'greater or equal', 'ge' ),
                   ( 'equal', 'eq' ), 
                   ( 'different', 'di' ),
                   ( 'between, include both bounds', 'be' ), 
                   ( 'between, exclude lower bound', 'beel' ),
                   ( 'between, exclude higher bound', 'beeh' ),
                   ( 'between, exclude both bound', 'bee' ),
                   ( 'outside, exclude both bounds', 'ou' ),
                   ( 'outside, include lower bound', 'ouil' ),
                   ( 'outside, include higher bound', 'ouih' ),
                   ( 'outside, include both bound', 'oui' ), ),
  'threshold1', Float(),
  'threshold2', Float(),
  'binary', Boolean(),
  'background_value', Float(),
  'foreground_value', Integer(),
  )

def initialization( self ):
  self.setOptional('threshold2', 'binary')
  self.binary = 0
  self.threshold1=0
  self.mode='gt'
  self.background_value = 0.
  self.foreground_value = 32767
  self.addLink(None, 'binary', self._binaryModeChanged)

def execution( self, context ):

  command = [ 'AimsThreshold', '-i', self.image_input, '-o', self.image_output, '-m', self.mode, '-t', self.threshold1,
              '--bg', self.background_value, '--fg', self.foreground_value ]

  if self.threshold2 is not None :
    command += [ '-u', self.threshold2]

  if self.binary:
    command += [ '-b']

  context.system( *command )

def _binaryModeChanged(self, proc):
    bin = (self.binary == True)
    signature = self.signature
    signature['background_value'].userLevel = 0 if not bin else 3
    signature['foreground_value'].userLevel = 0 if bin else 3
    self.changeSignature(signature)
