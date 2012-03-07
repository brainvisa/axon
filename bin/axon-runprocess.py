#!/usr/bin/env python
# -*- coding: utf-8 -*-

from brainvisa import axon
import neuroConfig, neuroProcesses
import sys, re, types
from optparse import OptionParser

usage = 'Usage: %prog [options] processname [arg1] [arg2] ... [argx=valuex] [argy=valuey] ...\n\nExample:\naxon-runprocess.py --enabledb threshold ~/data/irm.ima /tmp/th.nii threshold1=80'
parser = OptionParser( description = 'Run a single BrainVISA / Axon process',
  usage=usage )
parser.add_option( '--enabledb', dest='enabledb', action='store_true', default=False, help='enable databasing (slower startup, but all features enabled)' )

(options, args) = parser.parse_args()

if not options.enabledb:
  neuroConfig.fastStart = True
neuroConfig.gui = False
neuroConfig.logFileName = ''

axon.initializeProcesses()

args = tuple( ( neuroConfig._convertCommandLineParameter( i ) for i in args ) )
kwre = re.compile( '([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*)$' )
kwargs = {}
todel = []
for arg in args:
  if type( arg ) in types.StringTypes:
    m = kwre.match( arg )
    if m is not None:
      kwargs[ m.group(1) ] = \
        neuroConfig._convertCommandLineParameter( m.group(2) )
      todel.append( arg )
args = ( arg for arg in args if arg not in todel )

neuroProcesses.defaultContext().runProcess( *args, **kwargs )

