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
from brainvisa import registration
from brainvisa.tools import aimsGlobals
from brainvisa import shelltools
import numpy as np
import sys
from six.moves import map
from six.moves import zip

def map_list(func, thing):
    return list(map(func, thing))

name = 'Graph To Volume Converter'
userLevel = 0
roles = ('converter',)


def validation():
    from soma import aims


signature = Signature(
    'read', ReadDiskItem('Graph', 'Graph'),
    'write', WriteDiskItem('Label Volume',
                           'aims Writable Volume Formats'),
    'preferredFormat', Choice(*([('<auto>', None)]
                               + map_list(lambda x: (x, getFormat(x)),
                                          aimsGlobals.aimsVolumeFormats))),
    'removeSource', Boolean(),
    'extract_volume', String(),
    'extract_contours', Choice('Yes', 'No')
)


def findAppropriateFormat(values, proc):
    if values.preferredFormat is None:
        result = WriteDiskItem(
            '4D Volume',
            aimsGlobals.aimsVolumeFormats[0]).findValue(values.read)
    else:
        result = WriteDiskItem(
            '4D Volume', values.preferredFormat).findValue(values.read)
    return result


def initialization(self):
    self.linkParameters('write', ['read', 'preferredFormat'],
                        findAppropriateFormat)
    self.preferredFormat = None
    self.setOptional('preferredFormat', 'extract_volume')
    self.removeSource = False
    self.extract_contours = 'No'


def neighbors(t, z, y, x):
    return [(t, z, y - 1, x),
            (t, z, y + 1, x),
            (t, z, y, x - 1),
            (t, z, y, x + 1)]


def execution(self, context):
    from soma import aims
    graph = aims.read(self.read.fullPath())
    aims.GraphManip.buckets2Volume(graph)
    if self.extract_volume:
        vol = graph[self.extract_volume]
    else:
        atts = [x for x in graph.keys()
                if isinstance(graph[x], aims.rc_ptr_Volume_S16)]
        if len(atts) == 0:
            raise RuntimeError(_t_('the ROI graph contains no voxel data'))
        elif len(atts) > 1:
            raise RuntimeError(
                _t_('the ROI graph contains several volumes. '
                    'Select the extract_volume parameter as one in ')
                + '( ' + ', '.join(atts) + ' )')
        vol = graph[atts[0]]
    # handle bounding box which may have cropped the data
    bmin = graph['boundingbox_min']
    bmax = graph['boundingbox_max']
    context.write('vol:', vol)
    context.write('bmin:', bmin, ', bmax:', bmax, ', size:', vol.getSize())
    if bmin[:3] != [0, 0, 0] \
            or bmax[:3] != [x+1 for x in vol.getSize()[:3]]:
        context.write('enlarging')
        # needs expanding in a bigger volume
        vol2 = aims.Volume_S16(bmax[0] + 1, bmax[1] + 1, bmax[2] + 1)
        vol2.fill(0)
        ar = vol2.np
        ar[bmin[0]:bmax[0] + 1, bmin[1]:bmax[1] + 1, bmin[2]:bmax[2] + 1, :] \
            = vol.np

        if self.extract_contours == 'Yes':
            ar_copy = ar.copy()
            for label in [v['roi_label'] for v in graph.vertices()]:
                ind = list(zip(*np.where(ar_copy == label)))
                for i in ind:
                    erase = True
                    for neigh in neighbors(*i):
                        if ar_copy[neigh] != label:
                            erase = False
                    if erase:
                        ar[i] = 0

        vol2.copyHeaderFrom(vol.header())
        aims.write(vol2, self.write.fullPath())
    else:
        # bounding box OK
        aims.write(vol.get(), self.write.fullPath())
    registration.getTransformationManager().copyReferential(self.read,
                                                            self.write)
    if self.removeSource:
        for f in self.read.fullPaths():
            shelltools.rm(f)
