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
@author: Dominique Geffroy
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''

from __future__ import absolute_import
from brainvisa.data.neuroData import Parameter
from brainvisa.data.qtgui.neuroDataGUI import NotImplementedEditor
from brainvisa.data.writediskitem import WriteDiskItem
from brainvisa.data.qtgui.labelSelectionGUI import LabelSelectionEditor
from brainvisa.processes import defaultContext
from brainvisa.configuration import neuroConfig
import soma.minf.api as minf
import soma.subprocess
import six

#----------------------------------------------------------------------------


class LabelSelection(Parameter):

    """
    Select labels in a nomenclature.
    """

    def __init__(self, model=None, nomencl=None, **kwargs):
        Parameter.__init__(self)
        self.value = kwargs.get('value', {})
        self.fileDI = kwargs.get('fileDI',
                                 WriteDiskItem('Labels selection', 'selection'))
        self.file = None
        if model:
            self.value['model'] = model
        if nomencl:
            self.value['nomenclature'] = nomencl

    def __str__(self):
        return "{ 'value' : " + repr( self.value ) \
            + ", 'fileDI' : WriteDiskItem( " + repr( self.fileDI.type.name ) \
          + ", " + repr(self.fileDI.formats) + " ) }"

    def findValue(self, value):
        if isinstance(value, six.string_types):
            value = LabelSelection(**eval(value))
        return value

    def editor(self, parent, name, context):
        return LabelSelectionEditor(self, parent, name)

    def listEditor(self, parent, name, context):
        return NotImplementedEditor(parent)

    def getAutoSelection(self):
        model = self.value.get('model')
        nom = self.value.get('nomenclature')
        fsel = self.file
        psel = self.value.get('selection')
        cmd = ['AimsLabelSelector', '-b']
        if model:
            cmd += ['-m', model]
        if nom:
            cmd += ['-n', nom]
        if psel:
            cmd += ['-p', '-']
        elif fsel:
            cmd += ['-p', fsel.fullPath()]
        if neuroConfig.platform == 'windows':
            pipe = soma.subprocess.Popen(cmd, stdin=soma.subprocess.PIPE,
                                    stdout=soma.subprocess.PIPE)
        else:
            pipe = soma.subprocess.Popen(cmd, stdin=soma.subprocess.PIPE,
                                    stdout=soma.subprocess.PIPE, close_fds=True)
        stdout, stdin = pipe.stdout, pipe.stdin
        if(psel):
            stdin.write(psel)
            stdin.flush()
        s = stdout.read()
        stdin.close()
        stdout.close()
        return s

    def writeSelection(self, context=None):
        if context is None:
            context = defaultContext()
        s = self.getAutoSelection().decode('utf-8')
        if not self.file:
            self.file = context.temporary('selection')
        try:
            f = open(self.file.fullPath(), 'w')
        except IOError:
            context.write('<b><font color="#c00000">Warning:</font></b> '
                          'writeSelection: file', self.file.fullPath(),
                          "can't be written<br>")
            self.file = context.temporary('selection')
            f = open(self.file.fullPath(), 'w')
        f.write(s)
        f.close()
        return s

    def isValid(self):
        if not self.file:
            return False
        m = minf.readMinf(self.file.fullPath())
        m = m[0]
        if len(m) == 0 or (len(m) == 1 and list(m.keys())[0] == '__syntax__'):
            return False
        return True
