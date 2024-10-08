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

'''
Registration of all BrainVISA specific minf formats.

@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
from __future__ import absolute_import
__docformat__ = "epytext en"

from soma.minf.api import createReducerAndExpander, registerClass, \
    registerClassAs

#------------------------------------------------------------------------------


def initializeMinfExtensions():
    from soma.notification import ObservableList, EditableTree
    registerClass('minf_2.0', EditableTree, 'EditableTree')
    registerClass('minf_2.0', EditableTree.Branch, 'EditableTree.Branch')
    registerClass('minf_2.0', EditableTree.Leaf, 'EditableTree.Leaf')
    registerClass('minf_2.0', ObservableList, 'ObservableList')

    createReducerAndExpander('brainvisa_2.0', 'minf_2.0')

    # Logging extensions
    from brainvisa.processing.neuroLog import TextFileLink, LogFileLink, LogFile
    registerClass('brainvisa_2.0', TextFileLink, 'TextFileLink')
    registerClass('brainvisa_2.0', LogFileLink, 'LogFileLink')
    registerClass('brainvisa_2.0', LogFile.Item, 'LogFile.Item')
    registerClassAs('brainvisa_2.0', LogFile.SubTextLog, TextFileLink)
    createReducerAndExpander('brainvisa-log_2.0', 'brainvisa_2.0')

    from brainvisa.processes import ProcessTree
    registerClass('brainvisa_2.0', ProcessTree, 'ProcessTree')
    registerClass('brainvisa_2.0', ProcessTree.Branch, 'ProcessTree.Branch')
    registerClass('brainvisa_2.0', ProcessTree.Leaf, 'ProcessTree.Leaf')
    createReducerAndExpander('brainvisa-tree_2.0', 'brainvisa_2.0')

    from brainvisa.history import minfHistory, ProcessExecutionEvent, BrainVISASessionEvent
    registerClass('brainvisa_2.0', ProcessExecutionEvent,
                  ProcessExecutionEvent.eventType)
    registerClass('brainvisa_2.0', BrainVISASessionEvent,
                  BrainVISASessionEvent.eventType)
    createReducerAndExpander(minfHistory, 'brainvisa_2.0')
