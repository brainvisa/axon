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
from brainvisa.tools import aimsGlobals
from brainvisa import shelltools
import sys

if sys.version_info[0] >= 3:
    def map_list(func, thing):
        return list(map(func, thing))
else:
    map_list = map

name = 'Aims Converter'
roles = ('converter',)
userLevel = 0

signature = Signature(
    'read', ReadDiskItem('4D Volume', aimsGlobals.aimsVolumeFormats,
                         enableConversion=False),
    'write', WriteDiskItem('4D Volume',  aimsGlobals.aimsWriteVolumeFormats),
    'preferredFormat', Choice(*([('<auto>', None)]
                               + map_list(lambda x: (x, getFormat(x)),
                                          aimsGlobals.aimsWriteVolumeFormats))),
    'removeSource', Boolean(),
    'ascii', Boolean(),
    'voxelType', Choice(('<Same as input>', None), 'U8', 'S8', 'U16', 'S16',
                        'U32', 'S32', 'FLOAT', 'DOUBLE', 'RGB', 'RGBA', 'HSV'),
    'rescaleDynamic', Boolean(),
    'useInputTypeLimits', Boolean(),
    'inputDynamicMin', Float(),
    'inputDynamicMax', Float(),
    'outputDynamicMin', Float(),
    'outputDynamicMax', Float(),
)


def findAppropriateFormat(values, proc):
    result = None
    if values.read is not None:
        if values.preferredFormat is not None:
            format = values.preferredFormat
        else:
            format = aimsGlobals.aimsWriteVolumeFormats[0]
        fobj = getFormat(format)
        if fobj is None:
            return None
        # I found no method to get the file extension from a format.
        fp = fobj.patterns.patterns[0].pattern.split('|*')
        if len(fp) == 2:
            filename = values.read.fullName() + fp[1]
            result = WriteDiskItem('4D Volume', format).findValue(filename)

    return result


def initialization(self):
    self.linkParameters('write', ['read', 'preferredFormat'],
                        findAppropriateFormat)
    self.preferredFormat = None
    self.setOptional('preferredFormat',
                     'voxelType',
                     'inputDynamicMin',
                     'inputDynamicMax',
                     'outputDynamicMin',
                     'outputDynamicMax')
    self.removeSource = False
    self.ascii = False
    self.voxelType = None
    self.rescaleDynamic = False
    self.useInputTypeLimits = False
    self.inputDynamicMin = None
    self.inputDynamicMax = None
    self.outputDynamicMin = None
    self.outputDynamicMax = None

    self.signature['rescaleDynamic'].userLevel = 2
    self.signature['useInputTypeLimits'].userLevel = 2
    self.signature['inputDynamicMin'].userLevel = 2
    self.signature['inputDynamicMax'].userLevel = 2
    self.signature['outputDynamicMin'].userLevel = 2
    self.signature['outputDynamicMax'].userLevel = 2


def execution(self, context):
    command = ['AimsFileConvert', '-i', self.read, '-o', self.write]
    if self.ascii:
        command += ['-a']
    if self.voxelType is not None:
        command += ['-t', self.voxelType]

    if self.rescaleDynamic:
        command += ['-r']

        if self.useInputTypeLimits:
            command += ['--itypelimits']

        if self.inputDynamicMin != None:
            command += ['--imin', self.inputDynamicMin]

        if self.inputDynamicMax != None:
            command += ['--imax', self.inputDynamicMax]

        if self.outputDynamicMin != None:
            command += ['--omin', self.outputDynamicMin]

        if self.outputDynamicMax != None:
            command += ['--omax', self.outputDynamicMax]

    if context.system(*command):
        raise RuntimeError(_t_(
            'Error while converting <em>%s</em> to <em>%s</em>')
            % (command[2], command[4]))
    if self.removeSource:
        for f in self.read.fullPaths():
            shelltools.rm(f)
