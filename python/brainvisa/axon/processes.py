# -*- coding: utf-8 -*-
#
#  This software and supporting documentation were developed by
#      CEA/DSV/SHFJ and IFR 49
#      4 place du General Leclerc
#      91401 Orsay cedex
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


# This script is intended to get run using BrainVISA (BV) script support ('-e'
# option). A independent GUI is displayed from BV and operates processes.

from __future__ import print_function
from __future__ import absolute_import
import brainvisa.axon
import atexit
import os
import sys
from brainvisa.configuration import neuroConfig
import brainvisa.processes
from brainvisa.data import neuroHierarchy, neuroData, temporary
from brainvisa.data.minfExtensions import initializeMinfExtensions
import brainvisa.toolboxes
from brainvisa.processing import neuroException, neuroLog
# the environment has to contain everything necessary as neuroConfig
# used to do: import many things here...
from brainvisa.processes import *
import six

_count = 0


def cleanup():
    """
    Cleanup to be done at Brainvisa exiting. This function is registered in atexit.
    """
    # cleanup only when cleanup() has been called the same number of times
    # as initializeProcesses()
    global _count
    _count -= 1
    if _count != 0:
        return

    try:
        if sys.version_info[0] >= 3:
            atexit.unregister(cleanup)
        else:
            atexit._exithandlers.remove((cleanup, (), {}))
    except ValueError:
        pass
    if neuroConfig.runsInfo:
        neuroConfig.runsInfo.delete()
    neuroConfig.clearObjects()
    neuroHierarchy.databases.currentThreadCleanup()
    brainvisa.processes.cleanupProcesses()
    neuroLog.closeMainLog()
    # print('closing manager:', temporary.manager, file=open('/tmp/log', 'a'))
    sys.stdout.flush()
    try:
        temporary.manager.close()
        # print('(set to None)', file=open('/tmp/log', 'a'))
    except Exception as e:
        print(e)
        raise
    sys.stdout.flush()


def initializeProcesses():
    '''
    This method intends to retrieve a list of all existing types in the
    BrainVISA ontology, of all processes and databases. This replicates the
    job which is usually done at the very beginning when BrainVISA starts,
    but here no GUI is created.

    The processes are available through functions in :py:mod:`brainvisa.processes`.
    The databases are in :py:data:`brainvisa.data.neuroHierarchy.databases`.
    The types are available through functions in :py:mod:`brainvisa.data.neuroDiskItems`.

    '''
    # protect agains recursive calls
    global _count
    _count += 1
    if _count != 1:
        return

    atexit.register(cleanup)
    if not neuroConfig.noToolBox:
        brainvisa.toolboxes.readToolboxes(neuroConfig.toolboxesDir,
                                          neuroConfig.homeBrainVISADir)
    for toolbox in brainvisa.toolboxes.allToolboxes():
        toolbox.init()

    temporary.initializeTemporaryFiles(
        defaultTemporaryDirectory=neuroConfig.temporaryDirectory)

    initializeMinfExtensions()

    if not neuroConfig.fastStart or neuroConfig.historyBookDirectory:
        # check for expired run information : ask user what to do
        if neuroConfig.fastStart:
            dontrecordruns = True
        else:
            dontrecordruns = False
        neuroConfig.runsInfo = neuroConfig.RunsInfo(
            dontrecordruns=dontrecordruns)

    neuroLog.initializeLog()
    neuroData.initializeData()
    neuroHierarchy.initializeDatabases()
    brainvisa.processes.initializeProcesses()
    if neuroConfig.gui:
        from brainvisa.data.qtgui.neuroDataGUI import initializeDataGUI
        initializeDataGUI()
        from brainvisa.processing.qtgui.neuroProcessesGUI import initializeProcessesGUI
        initializeProcessesGUI()

    if not neuroConfig.fastStart:
        # write information about brainvisa log file
        brainvisa.processes.defaultContext().write(
            "The log file for this session is " + repr(neuroConfig.logFileName))
        neuroConfig.runsInfo.check(brainvisa.processes.defaultContext())

    # brainvisa.processes.readTypes() (actually imported from neuroDiskItems)
    # lists all existing types in the ontology
    brainvisa.processes.readTypes()
    # neuroHierarchy.databases gets populated

    # Databases loading is skipped when no toolbox is loaded because specific
    # hierarchies from unloaded toolboxes may be needed to define the ontology
    # describing a given database organization
    if not neuroConfig.noToolBox and not neuroConfig.fastStart:
        neuroHierarchy.openDatabases()

    # Makes the list of all processes availables in the processes path
    brainvisa.processes.readProcesses(neuroConfig.processesPath)

    if not neuroConfig.fastStart:
        for toolbox in brainvisa.toolboxes.allToolboxes():
            # executes startup.py of each toolbox if it exists
            if os.path.exists(toolbox.startupFile):
                try:
                    print('exec:', toolbox.startupFile)
                    fopts = {'encoding': 'utf-8'} if sys.version_info[0] >= 3 else {}
                    with open(toolbox.startupFile, **fopts) as f:
                        six.exec_(f.read(), globals(), {})
                except Exception:
                    neuroException.showException()

    localsStartup = {}
    for f in neuroConfig.startup:
        try:
            if isinstance(f, six.string_types):
                localsStartup = globals().copy()
                six.exec_(f, localsStartup, localsStartup)
            else:
                f()
        except Exception:
            neuroException.showException()
    del localsStartup
