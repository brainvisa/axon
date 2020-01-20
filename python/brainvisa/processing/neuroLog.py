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
"""
This module contains the classes for **Brainvisa log system**.

Brainvisa main log is an instance of :py:class:`LogFile`. It is stored in the global variable :py:data:`brainvisa.configuration.neuroConfig.mainLog`.
This main log is created in the function :py:func:`initializeLog`.

:Inheritance diagram:

.. inheritance-diagram:: brainvisa.processing.neuroLog

:Classes and functions:

"""
from __future__ import print_function
import os
import threading
import shutil
import time
import weakref
import sys

from soma.minf.api import iterateMinf, createMinfWriter
from brainvisa.data import temporary
from brainvisa.configuration import neuroConfig
from brainvisa.processing import neuroException
import gzip

if sys.version_info[0] >= 3:
    unicode = str

    def items(thing):
        return list(thing.items())

    #def next(iterator):
        #return iterator.__next__()
else:
    def items(thing):
        return thing.items()

    #def next(iterator):
        #return iterator.next()


#------------------------------------------------------------------------------
class FileLink:

    """
    Base virtual class for a link on a log file.
    """
    pass


#------------------------------------------------------------------------------
class TextFileLink(FileLink):

    """
    This class represents a link on the file associated to a :py:class:`SubTextLog`.
    """

    def __init__(self, fileName):
        """
        :param string fileName: name of the file
        """
        self.fileName = unicode(fileName)

    def expand(self):
        """
        Reads the file and returns its content as a string.
        """
        # print("expand text ", self)
        result = None
        try:
            if sys.version_info[0] >= 3:
                file = open(self.fileName, 'r', encoding='utf-8')
            else:
                file = open(self.fileName, 'r')
            result = file.read()
            file.close()
        except Exception:
            result = neuroException.exceptionHTML()
        return result

    def __getinitargs__(self):
        return (self.fileName, )

    def __repr__(self):
        return '<TextFileLink ' + self.fileName + '>'


#------------------------------------------------------------------------------
class LogFileLink(FileLink):

    """
    This class represents a link on the file associated to a :py:class:`LogFile`.
    """

    def __init__(self, fileName):
        self.fileName = unicode(fileName)

    def expand(self):
        """
        Reads the file and returns the content as a list of :py:class:`Item`.
        """
        # print("expand file ", self)
        try:
            reader = LogFileReader(self.fileName)
            result = reader.read()
            reader.close()
        except Exception:
            # print("error while reading log file ", self)
            result = [
                LogFile.Item(icon='error.png', what='Error', html=neuroException.exceptionHTML())]
        return result

    def __getinitargs__(self):
        return (self.fileName, )

    def __repr__(self):
        return '<LogFileLink ' + self.fileName + '>'


#------------------------------------------------------------------------------
class LogFile:

    """
    This class represents Brainvisa log file.
    This object is structured hierarchically. A LogFile can have a parent log and can be the parent log of other logs.

    This hierarchical structure is useful in Brainvisa because several threads may have to add log information at the same time,
    so we have to use several temporary log files to avoid concurrent access to the same file.
    So each process have its own LogFile which can have sub logs if the process calls other processes or system commands.
    The different log files are merged in the main log file when the process ends.

    The content of the file is in minf xml format.

    The elements written in the file are :py:class:`Item` objects. They are written through the method :py:meth:`append`.
    """

    #-------------------------------------------------------------------------
    class SubTextLog(TextFileLink):

        """
        This class is a kind of leaf in the tree of log files. It cannot be a parent for another log file.
        It only stores text information.
        """

        def __init__(self, fileName, parentLog):
            """
            :param string fileName: path to the file where the log information will be written.
            :param parentLog: parent :py:class:`brainvisa.processing.neuroLog.LogFile`.
            """
            self.fileName = fileName
            # print("SubTextLog ", fileName, " of parent ", parentLog)
            # Create empty file
            if sys.version_info[0] >= 3:
                file = open(unicode(self.fileName), 'w', encoding='utf-8')
            else:
                file = open(unicode(self.fileName), 'w')
            file.close()
            self._parent = parentLog

        def __del__(self):
            self.close()

        def close(self):
            """
            Warns the parent log that this file is closed.
            """
            if self.fileName is not None:
                self._parent._subLogClosed(self)
                self.fileName = None

    #-------------------------------------------------------------------------
    class Item:

        """
        An entry in a log file. It can have a list of children items.
        """
        icon = 'logItem.png'

        def __init__(self, what, when=None, html='', children=[], icon=None):
            """
            :param string what: title of the entry
            :param when: date of creation returned by :py:func:`time.time` by default.
            :param html: the content associated to this item in HTML format. String or :py:class:`FileLink`.
            :param children: sub items: a list of Items or a LogFile (which contains Items)
            :param string icon: An icon file associated to this entry.
            """
            self._what = unicode(what)
            if when is None:
                self._when = time.time()
            else:
                if not isinstance(when, float):
                    raise RuntimeError(_t_('Invalid when value'))
                self._when = when
            self._html = html
            if isinstance(children, LogFile):
                self._children = LogFileLink(children.fileName)
            else:
                self._children = children
            self._icon = icon

        def what(self):
            """
            Returns the title of the entry.
            """
            return self._what

        def when(self):
            """
            Returns the date of the entry.
            """
            return self._when

        def html(self):
            """
            Returns the HTML content of the log entry.
            """
            if isinstance(self._html, FileLink):
                return self._html.expand()
            return unicode(self._html)

        def children(self):
            """
            Returns the children of the item as a list of :py:class:`Item`.
            If children items are in a log file, this log file is read to extract its items.
            """
            children = self._children
            if isinstance(children, FileLink):
                children = children.expand()
            else:
                for child in self._children:
                    if isinstance(child, LogFile.Item):
                        child._expand({})
            return children

        def icon(self):
            """
            Returns the icon file associated to this item.
            """
            return self._icon

        def _expand(self, openedFiles):
            """
            If html content of the item is a :py:class:`FileLink` and the associated file is not opened,
            the html content is replaced by the content of the file (text).
            If the children items are in a log file and the associated file is not opened,
            the file is read and the list of its children is stored directly in the current item.
            """
            # print("expand item ", self._what)
            if isinstance( self._html, FileLink ) and \
               self._html.fileName not in openedFiles:
                self._html = self._html.expand()
            if isinstance( self._children, FileLink ) and \
               self._children.fileName not in openedFiles:
                children = []
                # print("expand children")
                for child in self.children():
                    # print("a child : ", child)
                    if isinstance( child, FileLink )and \
                            child.fileName not in openedFiles:
                        children.append(child.expand())
                    else:
                        child._expand(openedFiles)
                        children.append(child)
                self._children = children

        def __getinitkwargs__(self):
            """
            This function enable to save this object in a minf file.
            """
            kwattrs = dict(what=self._what)
            if self._when:
                kwattrs['when'] = self._when
            if self._html:
                kwattrs['html'] = self._html
            if self._children:
                kwattrs['children'] = self._children
            if self._icon:
                kwattrs['icon'] = self._icon
            return ((), kwattrs)

    #-------------------------------------------------------------------------
    def __init__(self, fileName, parentLog, lock, file=None, temporary=False):
        """
        :param string fileName: path to the file where the log information will be written.
        :param parentLog: parent :py:class:`Logfile`.
        :param lock: :py:func:`threading.RLock`, a lock to prevent from concurrent access to the file.
        :parent file: stream on the opened file.
        """
        # print("New log file ", fileName, " of parent ", parentLog)
        self._writer = None
        self._lock = lock
        self.fileName = fileName
        self._parent = parentLog
        self._opened = weakref.WeakValueDictionary()
        self._closed = set()
        self._temporary = temporary
        if file is None:
            if sys.version_info[0] >= 3:
                self._file = open(fileName, 'w', encoding='utf-8')
            else:
                self._file = open(fileName, 'w')
        else:
            self._file = file
        self._writer = createMinfWriter(self._file, format='XML',
                                        reducer='brainvisa-log_2.0')
        self._writer.flush()

    def __del__(self):
        if self._writer is not None:
            self.close()

    def __getstate__(self):
        raise RuntimeError(_t_('Cannot get state of LogFile'))

    def __repr__(self):
        return '<LogFile ' + self.fileName + '>'

    def close(self):
        """
        Closes all files related to this LogFile.
        """
        if self._lock is None:
            return
        try:
            self._lock.acquire()
        except TypeError:
            self._lock = None
        try:
            for n, children in items(self._opened):
                children.close()
            if self._writer is not None:
                self._writer.flush()
                self._writer.close()
                self._writer = None
                self._file.close()
                self._file = None
                if self._parent is not None:
                    self._parent._subLogClosed(self)
                self.fileName = None
        finally:
            if self._lock is not None:
                self._lock.release()
                self._lock = None
        if self._temporary:
            os.unlink(self.fileName)

    def subLog(self, fileName=None):
        """
        Creates a sub log, that is to say a new :py:class:`LogFile` which have this log as parent log.

        :param string fileName: name of the file where log information will be written. If None, the sublog is associated to a new temporary file created with :py:meth:`brainvisa.data.temporary.TemporaryFileManager.new`.

        :rtype: :py:class:`LogFile`
        :returns: The new sub log.
        """
        self._lock.acquire()
        try:
            if fileName is None:
                fileName = temporary.manager.new()
            # print("Creating sublog...")
            result = LogFile(fileName, self, self._lock)
            self._opened[unicode(result.fileName)] = result
        finally:
            self._lock.release()
        return result

    def subTextLog(self, fileName=None):
        """
        Creates a :py:class:`SubTextLog` as a child of the current log. The sub log have the current log as parent log.
        This type of sub log is used for example to store the output of a system command.

        :param string fileName: name of the file where log information will be written. If None, the sublog is associated to a new temporary file created with :py:meth:`brainvisa.data.temporary.TemporaryFileManager.new`.
        :rtype: :py:class:`SubTextLog`
        :returns: The new sub log.
        """
        self._lock.acquire()
        try:
            if fileName is None:
                fileName = temporary.manager.new()
            # print("Creating subTextLog...")
            result = self.SubTextLog(fileName, self)
            self._opened[unicode(result.fileName)] = result
        finally:
            self._lock.release()
        return result

    def _subLogClosed(self, subLog):
        """
        Stores the information that this sublog is closed.
        """
        if self._lock is None:
            return
        self._lock.acquire()
        try:
            self._closed.add(subLog.fileName)
            # keep a link on the sub files to avoid their deletion before the
            # log file is expanded
            if getattr(subLog, "_closed", None):
                self._closed.update(subLog._closed)
            self._opened.pop(unicode(subLog.fileName), None)
            # print("subLogClosed ", subLog, "remaining opened : ",
            # self._opened.values())
        finally:
            self._lock.release()

    def append(self, *args, **kwargs):
        """
        Writes an :py:class:`Item` in the current log file.
        This method can take in parameters a :py:class:`Item` or the parameters needed to create a new :py:class:`Item`.
        """
        self._lock.acquire()
        try:
            if not kwargs and \
               len(args) == 1 and isinstance(args[0], LogFile.Item):
                result = args[0]
            else:
                result = LogFile.Item(*args, **kwargs)
            self._writer.write(result)
            self._writer.flush()
        finally:
            self._lock.release()
        return result

    def expand(self, force=False):
        """
        Reads the current log file and the sub logs and items files and merges all their content in a same file.
        """
        # print("expand ", self)
        if force:
            opened = {}
        else:
            opened = self._opened
        self._lock.acquire()
        try:
            self._writer.flush()
            self._file.close()
            self._file = None
            reader = LogFileReader(self.fileName)
            tmp = temporary.manager.new()
            # print("Create temporary new log file for expand ", tmp)
            writer = newLogFile(tmp)
            logItem = reader.readItem()
            while logItem is not None:
                logItem._expand(opened)
                writer.append(logItem)
                logItem = reader.readItem()
            reader.close()
            self._closed.clear()
            shutil.copyfile(tmp, self.fileName)
            if sys.version_info[0] >= 3:
                self._file = open(self.fileName, 'a+', encoding='utf-8')
            else:
                self._file = open(self.fileName, 'a+')
            self._writer.change_file(self._file)
        finally:
            self._lock.release()

    def flush(self):
        """
        Really writes the file on disk.
        """
        if self._writer is not None:
            self._writer.flush()


#------------------------------------------------------------------------------
def newLogFile(fileName, file=None):
    """
    Returns a new :py:class:`LogFile` object that will write in `fileName`.
    """
    return LogFile(fileName, None, threading.RLock(), file=file)


#------------------------------------------------------------------------------
class LogFileReader:

    """
    This objects enables to read :py:class:`LogFile` :py:class:`Logfile.Item` from a filename.
    """

    def __init__(self, source):
        self._iterator = iterateMinf(source)

    def close(self):
        self._iterator = None

    def readItem(self):
        """
        Returns the next :py:class:`Item` in the current file.
        """
        try:
            return next(self._iterator)
        except StopIteration:
            return None

    def read(self):
        """
        Returns the list of all :py:class:`Item` in the current file.
        """
        return list(self._iterator)


#------------------------------------------------------------------------------
def expandedCopy(source, destFileName, destFile=None):
    """
    Returns a copy of the source log file with all its items expanded (file links replaced by the content of the file).
    """
    writer = newLogFile(destFileName, file=destFile)
    for item in expandedReader(source):
        writer.append(item.what(), when=item.when(), html=item.html(),
                      children=item.children(), icon=item.icon())
    writer.flush()
    writer.close()


#------------------------------------------------------------------------------
def expandedReader(source):
    """
    Generator on the :py:class:`Item` of the source file. Each item is expanded,
    that is to say each file link that they contains is also read.
    """
    reader = LogFileReader(source)
    item = reader.readItem()
    while item is not None:
        item._expand({})
        yield item
        item = reader.readItem()
    reader.close()


#------------------------------------------------------------------------------
def initializeLog():
    """
    Creates Brainvisa main log as an instance of :py:class:`LogFile` which is stored in the variable :py:data:`brainvisa.configuration.neuroConfig.mainLog`.
    The associated file is :py:data:`brainvisa.configuration.neuroConfig.logFileName`.
    """
    neuroConfig.mainLog = None
    try:
        if neuroConfig.logFileName:
            if os.path.exists(neuroConfig.logFileName):
                shutil.copyfile(neuroConfig.logFileName,
                                neuroConfig.logFileName + '~')
            neuroConfig.mainLog = newLogFile(neuroConfig.logFileName)
            neuroConfig.brainvisaSessionLog = neuroConfig.mainLog.subLog()
            neuroConfig.brainvisaSessionLogItem = neuroConfig.mainLog.Item(
                _t_('BrainVISA session'),
                html=neuroConfig.environmentHTML(),
                children=neuroConfig.brainvisaSessionLog, icon='brainvisa_small.png')
            neuroConfig.mainLog.append(neuroConfig.brainvisaSessionLogItem)
    except Exception as e:
        import traceback
        traceback.print_exc()
        neuroConfig.mainLog = None


#------------------------------------------------------------------------------
def closeMainLog():
    """
    Closes Brainvisa main log. The log file content is expanded and the file is compressed with :py:class:`gzip.GzipFile`.
    """
    if neuroConfig.mainLog is not None:
        tmpFileName = temporary.manager.new()
        logFileName = neuroConfig.mainLog.fileName
        neuroConfig.mainLog.close()

        dest = gzip.GzipFile(tmpFileName, 'wb', 9)
#    dest = open( tmpFileName, 'wb' )
        expandedCopy(logFileName, tmpFileName, dest)
        dest = None
        shutil.copyfile(tmpFileName, logFileName)
        neuroConfig.mainLog = None


#------------------------------------------------------------------------------
def log(*args, **kwargs):
    """
    Adds an :py:class:`Item` in Brainvisa main log.
    """
    if neuroConfig.mainLog is not None:
        neuroConfig.mainLog.append(*args, **kwargs)
