#!/usr/bin/env python
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

"""
brainvisa.axon.runprocess is not a real python module, but rather an executable script with commandline arguments and options parsing. It is provided as a module just to be easily called via the python command in a portable way:
python -m brainvisa.axon.runprocess <process name> <process arguments>
"""

from brainvisa import axon
from brainvisa.configuration import neuroConfig
import brainvisa.processes
import sys, re, types
from optparse import OptionParser

usage = '''Usage: %prog [options] processname [arg1] [arg2] ... [argx=valuex] [argy=valuey] ...

Example:
%prog --enabledb threshold ~/data/irm.ima /tmp/th.nii threshold1=80

Named arguments (in the shape argx=valuex) may address sub-processes of a pipeline, using the dot separator:

PrepareSubject.t1mri=/home/myself/mymri.nii
'''

parser = OptionParser(description = 'Run a single BrainVISA / Axon process',
    usage=usage)
parser.add_option('--enabledb', dest='enabledb', action='store_true',
    default=False,
    help='enable databasing (slower startup, but all features enabled)')
parser.add_option('--historyBook', dest='historyBook', action='append',
    help='store history information files in this directory (otherwise '
    'disabled unless dabasing is enabled)')
#parser.add_option('--enablegui', dest='enablegui', action='store_true',
    #default=False,
    #help='enable graphical user interface for interactive processes')

parser.disable_interspersed_args()
(options, args) = parser.parse_args()

#if options.enablegui:
    #neuroConfig.gui = True
    #from PyQt4 import QtGui
    #qapp = QtGui.QApplication([])
#else:
neuroConfig.gui = False
if not options.enabledb:
    neuroConfig.fastStart = True
if options.historyBook:
    neuroConfig.historyBookDirectory = options.historyBook
if not options.enabledb and not options.historyBook:
    neuroConfig.logFileName = ''

axon.initializeProcesses()

args = tuple((neuroConfig.convertCommandLineParameter(i) for i in args))
kwre = re.compile('([a-zA-Z_](\.?[a-zA-Z0-9_])*)\s*=\s*(.*)$')
kwargs = {}
todel = []
for arg in args:
    if type(arg) in types.StringTypes:
        m = kwre.match(arg)
        if m is not None:
            kwargs[m.group(1)] = \
                neuroConfig.convertCommandLineParameter(m.group(3))
            todel.append(arg)
args = [arg for arg in args if arg not in todel]

brainvisa.processes.defaultContext().runProcess(*args, **kwargs)

sys.exit(neuroConfig.exitValue)


