#! /usr/bin/python
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
This module loads BrainVISA and enables to import the Brainvisa modules which are not automatically in the python path (:doc:`brainvisa`).

It is useful to write a Python script that uses Brainvisa. Usage:
  
  >>> import brainvisa.axon
  >>> brainvisa.axon.initializeProcesses()
  
Then, Brainvisa, its processes and databases are loaded and it can be used as if it were started in batch mode.

"""

import os, sys

# Force QString API version in order to be compatible with recent version
# of enthought.traits.ui (3.6 for instance)
import sip
try:
  sip.setapi( 'QString', 2 )
except:
  print "WARNING: impossible to use version 2 of API QString."

import brainvisa
brainvisa_path=os.path.join( os.path.dirname( os.path.dirname( \
    os.path.dirname( brainvisa.__file__ ))), 'brainvisa' )
argv = sys.argv
# Temporarily change argv[0] since it is used in neuroConfig initialization
# to set paths
sys.argv = [ os.path.join(brainvisa_path, 'neuro.py'), '-b' ]
sys.path.insert( 0, brainvisa_path )
import PyQt4
import neuroConfig
import neuroLog
from processes import initializeProcesses

# set back argv[0] to its original value
sys.argv = argv
del argv

# once imported and initialized, the modules do not need to be
# referenced any longer here.
del brainvisa, PyQt4, neuroConfig, neuroLog, sys, os, sip, processes
