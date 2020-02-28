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

from __future__ import absolute_import
from brainvisa.processes import *

name = 'Linear Combination'
userLevel = 1

signature = Signature(
    'read1', ReadDiskItem('3D Volume', 'aims readable Volume Formats'),
  'multiplicative_coefficient1', Float(),
  'divisor_coefficient1', Float(),

  'read2', ReadDiskItem('3D Volume', 'aims readable Volume Formats'),

  'multiplicative_coefficient2', Float(),
  'divisor_coefficient2', Float(),
  'constant', Integer(),

  'write', WriteDiskItem('3D Volume', 'aims writable Volume Formats'),
  'type', Choice(('<Same as input>', None), 'U8', 'S8',
                 'U16', 'S16', 'U32', 'S32', 'FLOAT', 'DOUBLE'),
)


def initialization(self):
    self.setOptional(
        'multiplicative_coefficient1', 'divisor_coefficient1', 'read2',
                     'multiplicative_coefficient2', 'divisor_coefficient2', 'constant', 'type')
    self.multiplicative_coefficient1 = 1
    self.multiplicative_coefficient2 = 1
    self.divisor_coefficient1 = 1
    self.divisor_coefficient2 = 1
    self.constant = 0
    self.type = None


def execution(self, context):
    command = ['cartoLinearComb.py', '-i', self.read1, '-o', self.write]

    formula = 'I1'
    if self.multiplicative_coefficient1 is not None:
        formula += ' * %f' % self.multiplicative_coefficient1

    if self.divisor_coefficient1 is not None:
        formula += ' / %f' % self.divisor_coefficient1

    if self.read2 is not None:
        command += ['-i', self.read2]
        formula += ' + I2'

        if self.multiplicative_coefficient2 is not None:
            formula += ' * %f' % self.multiplicative_coefficient2

        if self.divisor_coefficient2 is not None:
            formula += ' / %f' % self.divisor_coefficient2

    if self.constant:
        formula += ' + %f' % self.constant

    if self.type is not None:
        formula = '(%s).astype(%f)' % (formula, self.type)

    command += ['-f', formula]

    context.pythonSystem(*command)
