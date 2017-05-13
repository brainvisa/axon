# -*- coding: utf-8 -*-
#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
#      Equipe Cogimage
#      UPMC, CRICM, UMR-S975
#      CNRS, UMR 7225
#      INSERM, U975
#      Hopital Pitie Salpetriere
#      47 boulevard de l'Hopital
#      75651 Paris cedex 13
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

from __future__ import print_function
from brainvisa.processes import *
try:
  from soma import aims, aimsalgo
  import numpy
except:
  pass

def validation():
  try:
    from soma import aims
    import numpy
  except:
    raise ValidationError('PyAims is not available')

userLevel = 0
name = 'DICE index'


signature = Signature(
    'label_images', ListOf(ReadDiskItem(
        'Label Volume', 'aims readable volume formats')),
    'csv_output', WriteDiskItem('CSV file', 'CSV file'),
    'image_labels', ListOf(String()),
    'output_format', Choice('matrix', 'linear'),
    'reference_space_image', ReadDiskItem('Label Volume',
        'aims readable volume formats'),
    'transformations', ListOf(ListOf(ReadDiskItem('Transformation matrix',
                                           'Transformation matrix'))),
)


def initialization(self):
    def linkLabels(self, dummy):
        if self.label_images is not None:
            labels = []
            for i, ts in enumerate(self.label_images):
                analysis = os.path.basename(ts.fullName())
                labels.append(analysis)
            return labels

    self.setOptional('reference_space_image', 'transformations')
    self.linkParameters('image_labels', 'label_images', linkLabels)


def build_transformation(self, trans_path, volume):
    ref_s = volume.header()['referential']
    result_tr = aims.AffineTransformation3d()
    for tr in trans_path:
        tr_o = aims.read(tr.fullPath())
        ref_s1 = tr_o.header()['source_referential']
        ref_d1 = tr_o.header()['destination_referential']
        if ref_d1 == ref_s:
            tr_o = tr_o.inverse()
            ref_s = ref_s1
        else:
            ref_s = ref_d1
        result_tr = tr_o * result_tr
    return result_tr


def resample_volume(self, volume, ref_dims, ref_vs, trans):
    resampler = aims.ResamplerFactory_S16().getResampler(0)
    resampler.setRef(volume)
    resampled = resampler.doit(trans, ref_dims[0], ref_dims[1], ref_dims[2],
                               ref_vs)
    return resampled.volume()


def check_resampled(self, i, volume, ref_dims, ref_vs):
    if self.reference_space_image is not None \
            and len(self.transformations)> i \
            and self.transformations[i]:
        trans = self.build_transformation(self.transformations[i], volume)
        vol1 = self.resample_volume(volume, ref_dims, ref_vs, trans)
        return vol1
    else:
        return volume


def execution(self, context):

    count = 0
    ntot = (len(self.label_images)+ 2)\
        * (len(self.label_images)- 1)/ 2
    context.progress(0, ntot, self)

    n = len(self.label_images)
    results = {}
    if self.reference_space_image is not None:
        f = aims.Finder()
        f.check(self.reference_space_image.fullPath())
        try:
            ref_dims = f.header()['volume_dimension']
        except:
            ref_dims = [f.header()['sizeX'], f.header()['sizeY'],
                        f.header()['sizeZ']]
        else:
            ref_dims = ref_dims[:3]
        ref_vs = f.header()['voxel_size'][:3]

    for i, seg1 in enumerate(self.label_images[:-1]):
        context.write('comparisons with %s (%d / %d)' \
            % (self.image_labels[i], count+1, ntot))
        vol1 = aims.read(seg1.fullPath())
        vol1 = self.check_resampled(i, vol1, ref_dims, ref_vs)

        avol1 = numpy.asarray(vol1)
        objects = numpy.unique(avol1)
        objects = [ o for o in objects if o != 0 ]
        vol = {}
        for l in objects:
            vol[l] = len(numpy.where(avol1 == l)[0])
        count += 1
        context.progress(count, ntot, self)
        for j, seg2 in enumerate(self.label_images[i+1:]):
            c = j + i + 1
            count += 1
            context.write('processing: %s - %s (%d / %d)' \
                % (self.image_labels[i], self.image_labels[c],
                    count, ntot))
            vol2 = aims.read(seg2.fullPath())
            vol2 = self.check_resampled(c, vol2, ref_dims, ref_vs)
            avol2 = numpy.asarray(vol2)
            for l in objects:
                w = numpy.where(avol2 == l)
                overlap = numpy.where(avol1[ w ] == l)[0].shape[0]
                res = results.setdefault(l, numpy.zeros((n, n)))
                res[ i, c ] = float(overlap * 2)\
                    / (w[0].shape[0] +vol[l])
            context.progress(count, ntot, self)

    if self.output_format == 'matrix':
        out = open(self.csv_output.fullPath(), 'w')
        print('method, label,', ', '.join(self.image_labels[1:]), file=out)
        for l in sorted(results.keys()):
            d = results[ l ]
            # symmetrize results
            d += d.transpose()
            d[ numpy.arange(d.shape[0]), numpy.arange(d.shape[0])] = 1.
            for i in xrange(d.shape[0]-1):
                out.write(self.image_labels[i] + ', %d, ' % l)
                out.write(', '.join([ str(x)for x in d[ i, 1: ] ])+ '\n')

    else: # linear format
        out = open(self.csv_output.fullPath(), 'w')
        print('label, method1, method2, DICE', file=out)
        for l in sorted(results.keys()):
            d = results[ l ]
            # symmetrize results
            d += d.transpose()
            d[ numpy.arange(d.shape[0]), numpy.arange(d.shape[0])] = 1.
            for i in xrange(d.shape[0]-1):
                for j in xrange(i+1, d.shape[1]):
                    out.write('%d, %s, %s, %f\n' \
                        % (l, self.image_labels[i], self.image_labels[j],
                            d[ i, j ]))
