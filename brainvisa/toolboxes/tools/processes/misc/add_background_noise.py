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
from brainvisa.tools import aimsGlobals

name = 'Add gaussian noise in image background'
userLevel = 0

signature = Signature(
    'input_image',
        ReadDiskItem('3D Volume', 'aims readable volume formats'),
    'output_image', WriteDiskItem(
        'Raw T1 MRI', 'aims writable volume formats'),
    'noise_average', Float(),
    'noise_stdev', Float(),
)


def initialization(self):
    self.noise_average = 20.
    self.noise_stdev = 10.


def execution(self, context):
    from soma import aims
    import numpy as np
    vol = aims.read(self.input_image.fullPath())
    vol_arr = np.asarray(vol)
    w = np.where(vol_arr == 0)
    noise = np.random.normal(
        self.noise_average, self.noise_stdev, w[0].shape)
    noise[noise < 0] = 0
    vol_arr[w] = noise
    aims.write(vol, self.output_image.fullPath())
