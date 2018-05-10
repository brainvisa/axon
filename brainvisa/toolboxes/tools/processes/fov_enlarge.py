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


# Interface de la serie de script fusionXContrastes datant de la version
# d'anatomist 1.24 environ.


from brainvisa.processes import *
from soma import aims

name = 'FOV enlarge'
userLevel = 2

signature = Signature(
    'read', ReadDiskItem('3D Volume', 'aims readable volume formats'),
    'write', WriteDiskItem('3D Volume', 'aims writable volume formats'),
    'added_border', Integer(),
)


def initialization(self):
    self.added_border = 5
    self.linkParameters('write', 'read')


def execution(self, context):
    finder = aims.Finder()
    finder.check(self.read.fullPath())
    hdr = finder.header()
    dims = hdr['volume_dimension'][:3]
    vs = hdr['voxel_size'][:3]
    dims[0] += self.added_border * 2
    dims[1] += self.added_border * 2
    dims[2] += self.added_border * 2
    transfile = context.temporary('Transformation matrix')
    trans = aims.AffineTransformation3d()
    trans.setTranslation([self.added_border * vs[0], self.added_border * vs[1],
                          self.added_border * vs[2]])
    aims.write(trans, transfile.fullPath())
    cmd = ['AimsResample', '-t', 'n', '-i', self.read, '-o', self.write,
           '--dx', dims[0], '--dy', dims[1], '--dz', dims[2], '-m', transfile]
    context.system(*cmd)
