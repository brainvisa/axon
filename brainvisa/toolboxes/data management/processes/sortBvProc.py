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

from brainvisa.processes import *
import sys
import os


name = 'BvProc sorting'
userLevel = 0

signature = Signature(
    'database', Choice()
)


def initialization(self):
    databases = [(dbs.directory, neuroHierarchy.databases.database(dbs.directory))
                 for dbs in neuroConfig.dataPath if not dbs.builtin]
    self.signature['database'].setChoices(*databases)
    if databases:
        self.database = databases[0][1]
    else:
        self.database = None


def execution(self, context):
    '''
      Sort bvproc files by date into a new directory
      directory parameter is for example history_book
    '''

    itemToInsert = []
    bvProcDirectory = ""

    # sort bvproc from the history_book directory
    historyDirectory = os.path.join(str(self.database.name), "history_book")

    if os.path.exists(historyDirectory):
        bvSessionDirectory = os.path.join(historyDirectory, "bvsession")
        if not os.path.isdir(bvSessionDirectory):
            os.mkdir(bvSessionDirectory)

        for fileToCopy in os.listdir(historyDirectory):
            fileCopy = False
            if os.path.isfile(os.path.join(historyDirectory, fileToCopy)):
                if fileToCopy.endswith('.bvproc'):
                    f = os.path.join(historyDirectory, fileToCopy)
                    s = os.stat(f)
                    dateFile = time.strftime(
                        "%Y-%m-%d", time.gmtime(s.st_mtime))
                    bvProcDirectory = os.path.join(historyDirectory, dateFile)
                    if not os.path.isdir(bvProcDirectory):
                        os.mkdir(bvProcDirectory)
                    to = os.path.join(bvProcDirectory, os.path.basename(f))
                    fileCopy = True

                elif fileToCopy.endswith('.bvsession'):
                    to = os.path.join(
                        historyDirectory, "bvsession", fileToCopy)
                    fileCopy = True

                if fileCopy:
                    fileToCopy = os.path.join(historyDirectory, fileToCopy)
                    shutil.copyfile(fileToCopy, to)
                    shutil.copystat(fileToCopy, to)
                    itemToInsert.append(to)

                    # remove the diskItem if exists
                    try:
                        item_to_remove = self.database.getDiskItemFromFileName(
                            fileToCopy)  # already exists in DB
                        if item_to_remove:
                            uuid = str(item_to_remove.uuid(saveMinf=False))
                            self.database.removeDiskItem(
                                item_to_remove, eraseFiles=True)
                    except:
                        context.write(
                            'Warning: file', fileToCopy, 'not found in any database.')

        # insert bvproc and bvsession files
        item = None
        itemExist = None
#    print itemToInsert
        for f in itemToInsert:
            try:
                itemExist = self.database.getDiskItemFromFileName(
                    f)  # already exists in DB: no need to add it
            except:
                try:
                    item = self.database.createDiskItemFromFileName(f)
                except:
                    context.write(
                        'Warning: file', file, 'cannot be inserted in any database.')

            if item is not None and (isinstance(item, DiskItem)) and item.isReadable() and item.get("_database", None) and (not hasattr(item, '_isTemporary') or not item._isTemporary):
                tmp = os.path.splitext(item.name)
                uuid = os.path.basename(tmp[0])
                minf = {}
                minf['uuid'] = uuid
                try:
                    # item._writeMinf( minf )
                    item.saveMinf(minf)
                    self.database.insertDiskItem(
                        item, update=True, insertParentDirs=False)
                except:
                    context.write(
                        'WARNING: file', f, 'cannot be inserted in any database.')

        if len(itemToInsert) != 0:
            context.write("The sorting is done.")
        else:
            context.write(
                "No bvproc or bvsession found, please check if the history book directory is empty !")

    else:
        context.write(
            "The history_book directory was not found, please check if the history option has been activated for this database.")
