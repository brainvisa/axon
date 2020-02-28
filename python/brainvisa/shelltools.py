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

from __future__ import print_function
from __future__ import absolute_import
import sys
import os
import string
import time
import shutil
import glob
import errno


def filesFromShPatterns(*args):
    result = []
    for pattern in args:
        result += glob.glob(pattern)
    return result


def cp(*args, **kwargs):
    def copy_as_you_can(source, dest, keepdate):
        if keepdate:
            copy = shutil.copy2
        else:
            copy = shutil.copy
        try:
            copy(source, dest)
        except Exception as e:
            # some filesystems (CIFS) do not accept changing file stat info
            # and raise an exception in shutil.copy2() or shutil.copy()
            if keepdate:
                try:
                    shutil.copy(source, dest)
                    return
                except OSError:
                    pass
            try:
                shutil.copyfile(source, dest)
                return
            except OSError:
                pass
            # nothing has worked
            raise

    keepdate = kwargs.get('keepdate', 0)
    sources = filesFromShPatterns(*args[:-1])
    if not sources:
        return
    dest = args[-1]
    symlinks = kwargs.get('symlinks', 0)

    if os.path.exists(dest):
        if not os.path.isdir(dest):
            if len(sources) > 1:
                raise IOError(
                    errno.ENOTDIR, os.strerror(errno.ENOTDIR), dest)
            source = sources[0]
            try:
                os.remove(dest)
            except OSError:
                # try forcing permissions
                os.chmod(dest, 0o770)
                os.remove(dest)
            copy_as_you_can(source, dest, keepdate)
            return
    else:
        if len(sources) == 1 and not os.path.isdir(sources[0]):
            copy_as_you_can(sources[0], dest, keepdate)
            return
        try:
            os.mkdir(dest)
        except OSError as e:
            if not e.errno == errno.EEXIST:
                # filter out 'File exists' exception, if the same dir has been created
                # concurrently by another instance of BrainVisa or another
                # thread
                raise

    for path in sources:
        newpath = os.path.join(
            dest, os.path.normpath(os.path.basename(path)))
        if os.path.isdir(path):
            if not os.path.isdir(newpath):
                try:
                    os.mkdir(newpath)
                except OSError as e:
                    if not e.errno == errno.EEXIST:
                        # filter out 'File exists' exception, if the same dir has been created
                        # concurrently by another instance of BrainVisa or
                        # another thread
                        raise
            cp(os.path.join(path, '*'), os.path.join(
                path, '.*'), newpath, symlinks=symlinks)
        elif symlinks and os.path.islink(path):
            if os.path.exists(newpath):
                try:
                    os.remove(newpath)
                except OSError:
                    # try forcing permissions
                    os.chmod(newpath, 0o770)
                    os.remove(newpath)
            os.symlink(os.readlink(path), newpath)
        else:
            if os.path.exists(newpath):
                try:
                    os.remove(newpath)
                except OSError:
                    # try forcing permissions
                    os.chmod(newpath, 0o770)
                    os.remove(newpath)
            copy_as_you_can(path, newpath, keepdate)


def symlink(*args):
    sources = filesFromShPatterns(*args[:-1])
    if not sources:
        return
    dest = args[-1]
    if not os.path.isdir(dest):
        raise IOError(errno.ENOTDIR, os.strerror(errno.ENOTDIR), dest)
    for link in sources:
        os.symlink(
            link, os.path.join(dest, os.path.basename(os.path.normpath(link))))


def rm(*args):
    def forceremove(func, path, excionfo):
        os.chmod(path, 0o770)
        return func(path)
    sources = filesFromShPatterns(*args)
    for path in sources:
        if os.path.isdir(path):
            shutil.rmtree(path, False, forceremove)
        else:
            try:
                os.remove(path)
            except OSError:
                # try forcing permissions
                os.chmod(path, 0o770)
                os.remove(path)


def touch(*args):
    sources = filesFromShPatterns(*args)
    for x in args:
        print(x)
        if x not in sources and x.find('*') < 0 and x.find('*') < 0:
            sources.append(x)
    for path in sources:
        if not os.path.exists(path):
            f = open(path, 'w')
            f.close()
        else:
            os.utime(path, None)


def mv(*args, **kwargs):
    cp(*args, **kwargs)
    rm(*args[:-1])
