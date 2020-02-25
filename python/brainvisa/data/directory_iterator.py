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
import os


class DirectoryIterator(object):

    def __init__(self, fileOrDirectory):
        self.__fileOrDirectory = fileOrDirectory
        self.__isDir = os.path.isdir(fileOrDirectory)

    def fullPath(self):
        return self.__fileOrDirectory

    def fileName(self):
        return os.path.basename(self.__fileOrDirectory)

    def isDir(self):
        return self.__isDir

    def listDir(self):
        return (DirectoryIterator(f) for f in (os.path.join(self.__fileOrDirectory, i) for i in os.listdir(self.__fileOrDirectory)))


class VirtualDirectoryIterator(object):

    def __init__(self, baseDirectory, content):
        self.__baseDirectory = baseDirectory
        self.__content = content

    def fullPath(self):
        return self.__baseDirectory

    def fileName(self):
        return os.path.basename(self.__baseDirectory)

    def isDir(self):
        return self.__content is not None

    def listDir(self):
        return (VirtualDirectoryIterator(f, content) for f, content in ((os.path.join(self.__baseDirectory, name), c) for name, c in self.__content))
