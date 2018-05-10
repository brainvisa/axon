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
try:
    from soma import aims
except:
    def validation():
        raise RuntimeError(_t_('module <em>aims</em> not available'))
import os


name = 'Create points ROI'
userLevel = 2


# Creation of a S16 image from a text file

signature = Signature(
    'file_of_point', ReadDiskItem('Coordinates File', 'Text file'),
  'image_output', WriteDiskItem('3D Volume',  'aims Writable Volume Formats'),
  'dimX', Integer(),
  'dimY', Integer(),
  'dimZ', Integer(),
  'sizeX', Float(),
  'sizeY', Float(),
  'sizeZ', Float(),
  'create_roigraph', Choice('yes', 'no'),
  'graph_output', WriteDiskItem('Roi graph', 'Graph')
)


def initialization(self):
    self.dimX = 256
    self.dimY = 256
    self.dimZ = 120
    self.sizeX = 1
    self.sizeY = 1
    self.sizeZ = 1
    self.setOptional('create_roigraph', 'graph_output')


def execution(self, context):

    fic = self.file_of_point
    a = aims.AimsData_S16(self.dimX, self.dimY, self.dimZ)
    a.setSizeXYZT(self.sizeX, self.sizeY, self.sizeZ)
    # mettre les valeurs :

    fic = open(self.file_of_point.fullPath(), 'r')
    tmp = 'x'
    b = 1  # en cas d'erreurs
    while tmp != '':
        tmp = fic.readline()
        tab = tmp.split()

        if len(tab) == 4:

            v = tab[0]
            v = int(v)

            x = tab[1]
            x = int(x)

            y = tab[2]
            y = int(y)

            z = tab[3]
            z = int(z)

            if (x <= self.dimX) and (y <= self.dimY) and (z <= self.dimZ):
                a.setValue(v, x, y, z)
            elif (x > self.dimX):
                context.write(
                    'dimX is strong - too long - perhaps "file_of_point" contains error')
                b = 0
                break
            elif (y > self.dimY):
                context.write(
                    'dimY is strong - too long - perhaps "file_of_point" contains error')
                b = 0
                break
            elif (z > self.dimZ):
                context.write(
                    'dimZ is strong - too long - perhaps "file_of_point" contains error')
                b = 0
                break

    fic.close()

    # write image
    if (b == 1):

        context.write('write image')
        aims.write(a, self.image_output.fullPath())

        if self.create_roigraph == 'yes':
            if self.graph_output is not None:
                command = ['AimsGraphConvert', '-i', self.image_output,
                           '-o', self.graph_output, '--roi', '--bucket']
                context.system(*command)
            else:
                context.write(
                    'graph_output is mandatory because you are chose create_roigraph=yes !')
    else:

        context.write('correct error and try again')
