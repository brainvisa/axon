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
This module defines functions to load Brainvisa **databases**.

The databases objects are stored in a global variable:

  .. py:data:: databases

    :py:class:`brainvisa.data.sqlFSODatabase.SQLDatabases` object which contains the loaded Brainvisa databases.

This object is created with the function :py:func:`initializeDatabases`.

Then each each database can be loaded with the function :py:func:`openDatabases`.
An object :py:class:`brainvisa.data.sqlFSODatabase.SQLDatabase` is created for each database selected in Brainvisa options.

The function :py:func:`hierarchies` enables to get the list of databases objects.

"""

from __future__ import print_function
from __future__ import absolute_import
import os

from brainvisa.data.sqlFSODatabase import SQLDatabase, SQLDatabases, DatabaseError, databaseVersion, databaseVersions
from brainvisa.processing.neuroException import showException, showWarning
from brainvisa.configuration import neuroConfig
# Import read and write diskitem because neuroHierarchy.ReadDiskItem and
# neuroHierarchy.WriteDiskItem is used in some processes
from brainvisa.data.readdiskitem import ReadDiskItem
from brainvisa.data.writediskitem import WriteDiskItem

databases = None


def initializeDatabases():
    """
    Creates the object :py:data:`databases` which is an instance of :py:class:`brainvisa.data.sqlFSODatabase.SQLDatabases`.
    It will contain all loaded databases.
    """
    global databases
    databases = SQLDatabases()


def openDatabases():
    """
    Loads databases which are selected in Brainvisa options.
    For each database, an object :py:class:`brainvisa.data.sqlFSODatabase.SQLDatabase` is created.
    The new database objects are added to :py:data:`databases`, any existing database in this object is previously removed.

    Warning messages may be displayed if a database is readonly or uses a deprecated ontology (*brainvisa-3.0*).
    """
    from brainvisa.processes import defaultContext
    global databases

    newDatabases = []
    for dbSettings in neuroConfig.dataPath:
        try:
            if getattr(dbSettings, "builtin", False) and databases.hasDatabase(dbSettings.directory):  # builtin databases are not re created
                newDatabases.append(databases.database(dbSettings.directory))
            else:
                databases.remove(dbSettings.directory)
                if dbSettings.expert_settings.fedji_backend:
                    from fedji.axon_frontend import AxonFedjiDatabase
                    base = AxonFedjiDatabase(
                        dbSettings.directory, fom_name=dbSettings.expert_settings.ontology)
                    newDatabases.append(base)
                else:
                    remoteAccessURI = os.path.join(
                        dbSettings.directory, 'remoteAccessURI')
                    if os.path.exists(remoteAccessURI):
                        raise NotImplementedError(
                            'Remote database access has been removed from '
                            'BrainVISA, it was an experimental feature. '
                            'Please remove {0} and check your database '
                            'configuration.'.format(remoteAccessURI)
                        )
                    else:
                        otherSqliteFiles = []
                        if dbSettings.expert_settings.sqliteFileName != ":memory:" and dbSettings.expert_settings.sqliteFileName != ":temporary:":
                            if dbSettings.expert_settings.sqliteFileName:
                                path, ext = os.path.splitext(
                                    dbSettings.expert_settings.sqliteFileName)
                            else:
                                path = os.path.join(
                                    dbSettings.directory, 'database')
                                ext = '.sqlite'

                            sqlite = path + "-" + databaseVersion + ext
                            # other versions of sqlite file
                            other = path + ext
                            if os.path.exists(other):
                                otherSqliteFiles.append(other)
                            for version in databaseVersions.keys():
                                if version != databaseVersion:
                                    other = path + "-" + version + ext
                                    if os.path.exists(other):
                                        otherSqliteFiles.append(
                                            path + "-" + version + ext)
                        else:
                            sqlite = dbSettings.expert_settings.sqliteFileName

                        base = SQLDatabase(
                            sqlite, dbSettings.directory, fso=dbSettings.expert_settings.ontology,
                                           context=defaultContext(), otherSqliteFiles=otherSqliteFiles, settings=dbSettings)
                        newDatabases.append(base)

                        # Usually users do not have to modify a builtin
                        # database. Therefore no warning is shown for these
                        # databases.
                        if ((not dbSettings.builtin) and (not os.access(dbSettings.directory, os.W_OK) or (os.path.exists(sqlite) and not os.access(sqlite, os.W_OK)))):
                            showWarning(
                                _t_("The database " + base.name + " is read only, you will not be able to add new items in this database."))
                        if base.fso.name == "brainvisa-3.0":
                            showWarning(
                                _t_("The database " + base.name + " uses brainvisa-3.0 ontology which is deprecated. You should convert this database to the new ontology using the process Data management -> Convert Old database."))
        except Exception:
            showException()
    # update SQLDatabases object
    databases.removeDatabases()
    for db in newDatabases:
        databases.add(db)


def hierarchies():
    """
    Returns a list of :py:class:`brainvisa.data.sqlFSODatabase.SQLDatabase` objects representing the databases currently loaded in Brainvisa.
    """
    return list(databases._databases.values())


def update_soma_workflow_translations():
    if not neuroConfig.fastStart:
        translation_file = open(
            os.path.join(neuroConfig.homeBrainVISADir, 'soma-workflow.translation'), 'w')
        for db in databases.iterDatabases():
            uuid = getattr(db, 'uuid', None)
            if uuid:
                print(uuid, db.name, file=translation_file)
            else:
                print("warning: " + repr(db.name) + " has no uuid")
        translation_file.close()
