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


from brainvisa.processes import *
from brainvisa.tools import aimsGlobals
from soma import aims, aimsalgo
import numpy

name = 'Resample to Template Space'
userLevel = 0

signature = Signature(
    'image', ReadDiskItem('4D Volume', 'aims readable volume formats'),
  'transformation', ReadDiskItem('Transformation matrix',
                                 'Transformation matrix'),
  'interpolation', Choice(('nearest neighbor', 0),
                          ('linear', 1),
                          ('quadratic', 2),
                          ('cubic', 3),
                          ('quartic', 4),
                          ('quintic', 5),
                          ('galactic', 6),
                          ('intergalactic', 7)),
  'template_image', ReadDiskItem('4D Volume',
                                 'aims readable volume formats'),
  'resampled', WriteDiskItem('4D Volume', 'aims writable volume formats')
)


def initialization(self):
    self.interpolation = 1
    self.template_image = ReadDiskItem('anatomical Template', 'NIFTI-1 image'
                                       ).findValue({'databasename': 'spm', 'skull_stripped': 'no'})


def execution(self, context):
    thdr = aimsGlobals.aimsVolumeAttributes(self.template_image)
    trans = thdr.get('transformations')
    if not trans or len(trans) == 0:
        raise KeyError('transformations not set in template header')
    ttrans = aims.AffineTransformation3d(trans[-1])  # last transformation
    vol = aims.read(self.image.fullPath())
    dtype = aims.typeCode(numpy.asarray(vol).dtype.type)
    resampler = getattr(aims, 'ResamplerFactory_' + dtype)().getResampler(
        self.interpolation)
    resampler.setRef(vol)
    dims = thdr['volume_dimension']
    vs = aims.Point3df(thdr['voxel_size'][:3])
    itrans = aims.read(self.transformation.fullPath())
    trans = ttrans.inverse() * itrans
    context.write('trans:', trans)
    resampled = resampler.doit(trans, dims[0], dims[1], dims[2], vs)
    hdr = resampled.header()
    hdr['transformations'] = thdr['transformations']
    hdr['referentials'] = thdr['referentials']
    ref = thdr.get('referential')
    if ref:
        hdr['referential'] = ref
    aims.write(resampled, self.resampled.fullPath())
