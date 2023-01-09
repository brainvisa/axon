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
import re
import string
import ftplib

from brainvisa.data import virtualDirectory


class Splitter(object):
    re = re.compile('([^ ]*)([ ]*)([^ ]?.*)')

    def __init__(self, s):
        self.s = s

    def get(self):
        if self.s:
            match = self.re.match(self.s)
            if match is None:
                raise RuntimeError('No match !')
            else:
                result = match.group(1, 2)
                self.s = match.group(3)
        else:
            result = None
        return result


class EnhancedFTP(object):

    class Item(object):

        def __init__(self, ftpDirString, parentName):
            splitter = Splitter(ftpDirString)
            self.flags = splitter.get()[0]
            splitter.get()
            self.user = splitter.get()[0]
            self.group = splitter.get()[0]
            self.size = int(splitter.get()[0])
            self.date = string.join(
                (splitter.get()[0], splitter.get()[0], splitter.get()[0]))
            if self.flags[0] == 'l':
                self.name = splitter.s.split(' -> ')[0]
            else:
                self.name = splitter.s
            self.fullName = parentName + '/' + self.name
            self.isDirectory = self.flags[0] == 'd'

    class __Reader(object):

        def __init__(self, ftp, socket, bufferSize):
            self.__ftp = ftp
            self.__socket = socket
            self.__bufferSize = bufferSize

        def __del__(self):
            self.close()

        def read(self, bufferSize):
            result = ''
            while len(result) < bufferSize:
                data = self.__socket.recv(bufferSize - len(result))
                if not data:
                    break
                result += data
            return result

        def close(self):
            if self.__socket is not None:
                self.__socket.close()
                self.__ftp.voidresp()
                self.__socket = None

    def __init__(self, host, login, password):
        self._ftp = None
        self.host = host
        self.login = login
        self.password = password

    def __del__(self):
        self._disconnect()

    def _connect(self):
        if self._ftp is None:
            self._ftp = ftplib.FTP(self.host)
#      self._ftp.set_pasv( False )
            self._ftp.login(self.login, self.password)

    def _disconnect(self):
        if self._ftp is not None:
            self._ftp.quit()
            self._ftp = None

    def ls(self, directory=None):
        self._connect()
        if directory is not None:
            self._ftp.cwd(directory)
        try:
            l = self._ftp.nlst()
        except ftplib.error_perm as e:
            if e.args[0][:3] == '550':
                # Error thrown when directory is empty
                l = []
            else:
                raise
        return result

    def dir(self, directory):
        self._connect()
        if directory is not None:
            self._ftp.cwd(directory)
        self._dir = []
        self._ftp.dir(self._buildDir)
        self._disconnect()
        result = self._dir[1:]  # Suppress 'total ...' line
        del self._dir
        return [self.Item(x, directory) for x in result]

    def getItem(self, path):
        i = path.rfind('/')
        parent = path[: i]
        me = path[i + 1:]
        for item in self.dir(parent):
            if item.name == me:
                return item
        return None

    def getReader(self, fileName, bufferSize=None):
        self._connect()
        self._ftp.voidcmd('TYPE I')
        sock = self._ftp.transfercmd('RETR ' + fileName)
        return self.__Reader(self._ftp, sock, bufferSize)
# result = sock.makefile( 'rb', bufferSize )
# sock.close()
# self._ftp.voidresp()
# return result

    def retrieve(self, fileName, destination, progressFunction=None):
        self._connect()
        self._output = open(destination, 'wb')
        self._progressFunction = progressFunction
        self._ftp.retrbinary('RETR ' + fileName, self._download)
        self._output.close()
        del self._output
        del self._progressFunction

    def _download(self, data):
        self._output.write(data)
        self._output.flush()
        if self._progressFunction:
            self._progressFunction(data)

    def _buildDir(self, line):
        self._dir.append(line)


class FTPDirectory(virtualDirectory.VirtualDirectory):

    class Item(virtualDirectory.VirtualDirectory.Item):

        def __init__(self, s, ftp, path):
            virtualDirectory.VirtualDirectory.Item.__init__(self, s)
            self.__ftp = ftp
            if isinstance(path, EnhancedFTP.Item):
                self.__path = path.fullName
                self.__item = path
            else:
                self.__path = str(path)
                self.__item = None

        def __getItem(self):
            if self.__item is None:
                self.__item = self.__ftp.getItem(self.__path)

        def size(self):
            self.__getItem()
            if self.__item is not None and not self.__item.isDirectory:
                return self.__item.size
            return None

        def reader(self):
            return self.__ftp.getReader(self.__path)

        def hasChildren(self):
            self.__getItem()
            return self.__item.isDirectory

        def children(self):
            result = []
            for item in self.__ftp.dir(self.__path):
                result.append(
                    FTPDirectory.Item(self.virtualDirectory, self.__ftp, item))
            return result

        def name(self):
            if self.__item is None:
                return self.__path[self.__path.rfind('/') + 1:]
            return self.__item.name

        def fullName(self):
            if self.virtualDirectory:
                return self.virtualDirectory._FTPDirectory__binIdFromPath(self.__path)
            return self.__path

        def parentFullName(self):
            index = self.__path.rfind('/')
            if index >= 0:
                return self.__path[:index]
            return ''

    def __init__(self, name, server, login, password, baseDirectory='/'):
        virtualDirectory.VirtualDirectory.__init__(self)
        self.__name = name
        self.__ftp = EnhancedFTP(server, login, password)
        self.__baseDirectory = baseDirectory

    def __pathFromBinId(self, binId):
        if binId:
            if self.__baseDirectory == '/':
                base = ''
            else:
                base = self.__baseDirectory
            if binId[0] == '/':
                return base + '/' + binId[1:]
            return base + '/' + binId
        else:
            return self.__baseDirectory

    def __binIdFromPath(self, path):
        if self.__baseDirectory == '/':
            return path[1:]
        else:
            return path[len(self.__baseDirectory) + 1:]

    def get(self, binId):
        return self.Item(self, self.__ftp, self.__pathFromBinId(binId))

    def name(self):
        return self.__name
