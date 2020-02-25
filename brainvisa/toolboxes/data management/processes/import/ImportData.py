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

from __future__ import absolute_import
from brainvisa.processes import *
from brainvisa import shelltools
from brainvisa.tools import aimsGlobals
import six
from six.moves import map

# This process should not be called directly unless you
# exactly know what you are doing. Import processes for
# specific data type should be used instead. No data checking
# is done here.
userLevel = 2

signature = Signature(
    'input', ReadDiskItem('Any Type', getAllFormats()),
  'output', WriteDiskItem('Any Type', getAllFormats()),
  'input_spm_orientation', Choice('Not applicable'),
  'converter', Choice('Any converter'),
)


def initialization(self):
    def _orient(self, proc):
        old = getattr(proc.signature['input_spm_orientation'], 'lastInput',
                      None)
        if self.input is None or old is None \
            or old.fullPath() != self.input.fullPath() \
                or proc.isDefault('input_spm_orientation'):
            hide = 1
            res = 'Not applicable'
            if self.input is not None:
                if self.input.format in list(map(getFormat, ('SPM image', 'Series of SPM image'))):
                    hide = 0
                    atts = aimsGlobals.aimsVolumeAttributes(self.input)
                    tr = atts.get('storage_to_memory')
                    if tr is not None and tr[0] < 0:
                        res = 'Neurological'
                    else:
                        res = 'Radiological'
            if hide:
                proc.signature['input_spm_orientation'].setChoices(
                    'Not applicable')
            else:
                proc.signature[
                    'input_spm_orientation'].setChoices('Neurological',
                                                        'Radiological')
        else:
            res = self.input_spm_orientation
        proc.signature['input_spm_orientation'].lastInput = self.input
        return res

    self.linkParameters('input_spm_orientation', 'input', _orient)
    self.signature['input_spm_orientation'
                   ].linkParameterWithNonDefaultValue = 1
    self.linkParameters('output', 'input')
    self.signature['output'].browseUserLevel = 3
    self.signature['input'].databaseUserLevel = 2

    self.signature['converter'].userLevel = 2
    self.signature['converter'].setChoices('Any converter', *getConverters())
    self.converter = 'Any converter'


def execution(self, context):
    if self.input.format is not self.output.format:
        # Convert input to appropriate output format
        inp = self.input
        if inp.type is None \
                or inp.type == ReadDiskItem('Any Type', inp.format).type:
            # if the input type is not recognized (data not in database),
            # assume it is the same type as the output
            inp = (self.output.type, inp.format)
        if self.converter == 'Any converter':
            converter = context.getConverter(inp, self.output)
        else:
            converter = getProcess(self.converter)
        if converter is None:
            raise RuntimeError(_t_('Cannot convert input data'))
        input = self.input
        if self.input.format in list(map(getFormat,
                                    ('SPM image', 'Series of SPM image'))):
            atts = aimsGlobals.aimsVolumeAttributes(self.input)
            tr = atts.get('storage_to_memory')
            radio = None
            if tr:
                radio = (tr[0] > 0)
            iradio = 0
            if self.input_spm_orientation == 'Radiological':
                iradio = 1
            context.write(
                'input_spm_orientation:', self.input_spm_orientation)
            if radio is None or radio != iradio:
                context.write('changing SPM orientation')
                input = context.temporary(self.input.format)
                inputFiles = self.input.fullPaths()
                outputFiles = input.fullPaths()
                if len(inputFiles) != len(outputFiles):
                    raise RuntimeError(
                        _t_('input and output do not have the same number of files'))
                for i in six.moves.xrange(len(inputFiles)):
                    if neuroConfig.platform != 'windows':
                        os.symlink(inputFiles[i], outputFiles[i])
                    else:
                        shelltools.cp(inputFiles[i], outputFiles[i])
                if os.path.exists(input.fullPath() + '.minf'):
                    os.unlink(input.fullPath() + '.minf')
                if os.path.exists(self.input.fullPath() + '.minf'):
                    shelltools.cp(self.input.fullPath() + '.minf',
                                  input.fullPath() + '.minf')
                input.readAndUpdateMinf()
                if iradio != 1:
                    iradio = -1
                if tr is None:
                    tr = [1, 0, 0, 0,  0, -1, 0, 0,  0, 0, -1, 0,  0, 0, 0, 1]
                    tr[7] = atts['volume_dimension'][1] - 1
                    tr[11] = atts['volume_dimension'][2] - 1
                tr[0] = iradio
                if tr[0] < 0:
                    tr[3] = atts['volume_dimension'][0] - 1
                else:
                    tr[3] = 0
                input.setMinf('storage_to_memory', tr)
        context.runProcess(converter, input, self.output)

    else:
        # Copy input files to output files
        inputFiles = self.input.fullPaths()
        outputFiles = self.output.fullPaths()
        if len(inputFiles) != len(outputFiles):
            raise RuntimeError(
                _t_('input and output do not have the same number of files'))
        for i in six.moves.xrange(len(inputFiles)):
            context.write('cp', inputFiles[i], outputFiles[i])
            shelltools.cp(inputFiles[i], outputFiles[i])

        if self.input.format in list(map(getFormat,
                                    ('SPM image', 'Series of SPM image'))):
            atts = aimsGlobals.aimsVolumeAttributes(self.input)
            radio = atts.get('spm_radio_convention')
            if self.input_spm_orientation == 'Neurological':
                radio = 0
            elif self.input_spm_orientation == 'Radiological':
                radio = 1
            self.output.readAndUpdateMinf()
            self.output.setMinf('spm_radio_convention', radio)
