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

from __future__ import absolute_import
from brainvisa.processes import *

name = '1 - Mask from SPMt'

userLevel = 2

signature = Signature(
    'spmt', ReadDiskItem('SPMt map', 'Aims readable volume formats'),
    'mask', WriteDiskItem('Functional mask', 'Aims writable volume formats'),
    'dilation', Float()
)


def initialization(self):
    self.linkParameters('mask', 'spmt')
    self.dilation = 8.0


def execution(self, context):
    tAbove = context.temporary('GIS image')
    tBelow = context.temporary('GIS image')
    tAdd = context.temporary('GIS image')
    dilate = context.temporary('GIS image')

    context.write('Creating Mask from SPMt')

    context.write('First threshold')
    ThreshA = ['AimsThreshold',
               '-i', self.spmt.fullPath(),
               '-o', tAbove.fullPath(),
               '-m', 'gt',
               '-t', '0',
               '-b']
    context.write('Second threshold')
    ThreshB = ['AimsThreshold',
               '-i', self.spmt.fullPath(),
               '-o', tBelow.fullPath(),
               '-m', 'lt',
               '-t', '0',
               '-b']
    context.write('Sum')
    Addition = ['AimsLinearComb',
                '-i', tAbove.fullPath(),
                '-a', '1',
                '-j', tBelow.fullPath(),
                '-c', '1',
                '-o', tAdd.fullPath()]
    context.write('Dilation')
    MaskDilation = ['AimsMorphoMath', '-m', 'dil',
                    '-i', tAdd.fullPath(),
                    '-o', dilate.fullPath(),
                    '-r', self.dilation]
    context.write('Conversion to float...')
    Conversion = ['AimsFileConvert',
                  '-i', dilate.fullPath(),
                  '-o', self.mask.fullPath(),
                  '-t', 'FLOAT']

    context.system(*ThreshA)
    context.system(*ThreshB)
    context.system(*Addition)
    context.system(*MaskDilation)
    context.system(*Conversion)

    context.write('Finished')
