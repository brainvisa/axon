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
import gzip
import shutil

name = 'uncompress GIS'
roles = ('converter',)
userLevel = 1

signature = Signature(
    'read', ReadDiskItem('4D Volume', ['gz Compressed GIS Image',
                                       'Z Compressed GIS Image'],
                         enableConversion=0),
  'write', WriteDiskItem('4D Volume', 'GIS image'),
  'removeSource', Boolean(),
)


def initialization(self):
    self.linkParameters('write', 'read')
    self.removeSource = 0


def execution(self, context):
    source = self.read.fullPaths()
    dest = self.write.fullPaths()
    for i in xrange(len(source)):
        f = gzip.open(source[i], 'rb')
        g = open(dest[i], 'wb')
        while 1:
            buf = f.read(1000)
            if len(buf) == 0:
                break
            g.write(buf)
        f.close()
        g.close()
        if self.removeSource:
            os.unlink(source[i])
    # copy minf file
    if os.path.exists(self.read.minfFileName()):
        shutil.copyfile(self.read.minfFileName(), self.write.minfFileName())
