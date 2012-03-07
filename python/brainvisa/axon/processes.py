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

import brainvisa.axon
import sys, atexit, os
import neuroConfig, neuroData, neuroProcesses, neuroHierarchy, neuroLog
from minfExtensions import initializeMinfExtensions
from brainvisa.data import temporary
import brainvisa.toolboxes
import neuroException
# the environment has to contain everything necessary as neuroConfig
# used to do: import many things here...
from neuroProcesses import *

def cleanup():
  """
  Cleanup to be done at Brainvisa exiting. This function is registered in atexit.
  """
  if neuroConfig.runsInfo:
    neuroConfig.runsInfo.delete()
  neuroConfig.clearObjects()
  neuroHierarchy.databases.currentThreadCleanup()
  neuroProcesses.cleanupProcesses()
  neuroLog.closeMainLog()
  temporary.manager.close()


def initializeProcesses():
    '''
    This method intends to retrieve a list of all existing types in the
    BrainVISA ontology, of all processes and databases. This replicates the
    job which is usually done at the very beginning when BrainVISA starts,
    but here no GUI is created.

    The processes are available through functions in :py:mod:`neuroProcesses`.
    The databases are in :py:data:`neuroHierarchy.databases`.
    The types are available through functions in :py:mod:`neuroDiskItems`.

    '''
    atexit.register(cleanup)
    if not neuroConfig.noToolBox:
        brainvisa.toolboxes.readToolboxes( neuroConfig.toolboxesDir,
            neuroConfig.homeBrainVISADir )
    for toolbox in brainvisa.toolboxes.allToolboxes():
      toolbox.init()

    temporary.initializeTemporaryFiles(
            defaultTemporaryDirectory = neuroConfig.temporaryDirectory )

    initializeMinfExtensions()
    neuroLog.initializeLog()

    #neuroConfig.qtApplication = QApplication( sys.argv, QApplication.Tty )
    #   I removed this neuroConfig.qtApplication line because it hangs the
    #   Anatomist instance which has also a QApplication
    neuroData.initializeData()
    neuroHierarchy.initializeDatabases()
    neuroProcesses.initializeProcesses()
    if neuroConfig.gui:
        from neuroDataGUI import initializeDataGUI
        initializeDataGUI()
        from neuroProcessesGUI import initializeProcessesGUI
        initializeProcessesGUI()

    if not neuroConfig.fastStart:
        # write information about brainvisa log file
        neuroProcesses.defaultContext().write("The log file for this session is " + repr(neuroConfig.logFileName) )
        # check for expired run information : ask user what to do
        neuroConfig.runsInfo = neuroConfig.RunsInfo()
        neuroConfig.runsInfo.check(neuroProcesses.defaultContext())

    # neuroProcesses.readTypes() (actually imported from neuroDiskItems)
    # lists all existing types in the ontology
    neuroProcesses.readTypes()
    # neuroHierarchy.databases gets populated

    # Databases loading is skipped when no toolbox is loaded because specific
    # hierarchies from unloaded toolboxes may be needed to define the ontology
    # describing a given database organization
    if not neuroConfig.noToolBox and not neuroConfig.fastStart:
        neuroHierarchy.openDatabases()

    neuroConfig.brainvisaSessionLogItem = neuroLog.log( 'starting BrainVISA',
        html=neuroConfig.environmentHTML(), icon='brainvisa_small.png' )

    # Makes the list of all processes availables in the processes path
    neuroProcesses.readProcesses(neuroConfig.processesPath)

    if not neuroConfig.fastStart:
        # executes brainvisa startup.py if it exists. there's no use to execute user startup.py here because .brainvisa is a toolbox and its startup.py will be executed with the toolboxes' ones.
        if os.path.exists(neuroConfig.siteStartupFile):
              execfile( neuroConfig.siteStartupFile, globals(), {} )
        # Search for hierarchy and types paths in toolboxes
        for toolbox in brainvisa.toolboxes.allToolboxes():
              # executes startup.py of each toolbox if it exists
              if os.path.exists( toolbox.startupFile ):
                  execfile( toolbox.startupFile, globals(), {} )

    localsStartup = {}
    for f in neuroConfig.startup:
        try:
            if isinstance( f, basestring ):
                localsStartup = globals().copy()
                exec f in localsStartup, localsStartup
            else:
                f()
        except:
            neuroException.showException()
    del localsStartup
