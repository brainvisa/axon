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

name = 'Import SPMt for structural analysis'

userLevel = 2

signature = Signature(
     'input', ReadDiskItem( 'SPMt map', shfjGlobals.aimsVolumeFormats ),
     'output', WriteDiskItem( 'SPMt map', 'Aims writable volume formats',
     exactType = 1,
     # Referential attribute must have the same value as subject attribute
     requiredAttributes = { 'referential': \
     lambda attribute, value, item : value == item.get( 'subject' )  },
  ),
  )


def initialization( self ):
     init=0

def execution( self, context ):
     context.system( 'AimsFileConvert', '-i', self.input.fullPath(), '-o',  self.output.fullPath() )
#      context.sysrtem(
#      if input1.format is not self.output.format:
#           # Convert input to appropriate output format
#           cmd = [ 'AimsFileConvert', '-i', input.fullPath(), '-o',
#               self.output.fullPath() ]
#      else:
#           # Copy input files to output files
#           inputFiles = input1.fullPaths()
#           outputFiles = self.output.fullPaths()
#           if len( inputFiles ) != len( outputFiles ):
#                raise RuntimeError( _t_('input and output do not have the same number of files') )
#           InputMinf = self.input.minfFileName()
#           if os.path.isfile( InputMinf ):
#                 shelltools.cp( InputMinf, self.output.fullPath() + '.minf' )
#           for i in xrange( len(inputFiles) ):
#                context.write( 'cp', inputFiles[ i ], outputFiles[ i ] )
#                shelltools.cp( inputFiles[ i ], outputFiles[ i ] )
#           self.output.readAndUpdateMinf( )
#           if input1.format in map( getFormat,( 'SPM image', 'Series of SPM image' ) ):
#                radio = atts.get( 'spm_radio_convention' )
#                if self.input_spm_orientation == 'Neurological':
#                     radio = 0
#                elif self.input_spm_orientation == 'Radiological':
#                     radio = 1
#                self.output.setMinf( 'spm_radio_convention', radio )
#           self.output.saveMinf()
