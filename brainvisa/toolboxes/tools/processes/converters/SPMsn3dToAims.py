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
import brainvisa.tools.aimsGlobals as shfjGlobals
import errno
from brainvisa import registration
from brainvisa.data.neuroHierarchy import databases
try:
    # errorToDisableScipyVersion() # fail until it is a bit tested and
    # debugged.
    import scipy
    from scipy.io import loadmat
    import numpy
    from soma import aims
except:
    loadmat = None

name = 'SPM sn3d to AIMS transformation converter'
roles = ('converter', )
userLevel = 0


def validation():
    try:
        from scipy.io import loadmat
    except:
        raise ValidationError('no scipy matlab .mat IO functionality ')
    try:
        from soma import aims
    except:
        raise ValidationError('no soma.aims module')

signature = Signature(
    'read', ReadDiskItem('SPM normalization matrix', 'Matlab file',
                         enableConversion=0),
  'write', WriteDiskItem('Transformation matrix', 'Transformation matrix'),
  'target', Choice('MNI template', 'unspecified template',
                   'normalized_volume in AIMS orientation'),
  'source_volume', ReadDiskItem('4D Volume',
                                ['NIFTI-1 image', 'SPM image']),
  'normalized_volume', ReadDiskItem('4D Volume',
                                    ['NIFTI-1 image', 'SPM image'],
                                    requiredAttributes={'referential':
                                                        str(registration.talairachMNIReferentialId)}),
  'removeSource', Boolean(),
)


def initialization(self):
    def linkSource(proc, param):
        if self.read is None:
            return None
        x = self.signature['source_volume'].findValue(self.read)
        if x is not None:
            return x
        filetype = self.read.type
        if filetype is getDiskItemType( 'SPM99 normalization matrix' ) \
                or self.read.fullName()[-5:] == '_sn3d':
            spm2 = 0
        else:
            spm2 = 1
        if spm2:
            srcim = self.read.fullName()[:-3]
        else:
            srcim = self.read.fullName()[:-5]
        di = ReadDiskItem('4D Volume', shfjGlobals.aimsVolumeFormats)
        for format in shfjGlobals.aimsVolumeFormats:
            f = databases.formats.getFormat(format.name)
            ext = f.extensions()[0]
            src = di.findValue(srcim + '.' + ext)
            if src is not None and src.isReadable():
                return src
        return di.findValue(self.read)

    def linkMNItransformation(proc, dummy):
        if proc.source_volume:
            tm = registration.getTransformationManager()
            ref = tm.referential(registration.talairachMNIReferentialId)
            if ref and tm.referential(proc.source_volume):
                trans = tm.createNewTransformation('Transformation matrix',
                                                   proc.source_volume, ref, simulation=True)
                return trans
            else:
                return WriteDiskItem('Transform Raw T1 MRI to Talairach-MNI template-SPM', 'Transformation Matrix').findValue(proc.source_volume)

    self.removeSource = 0
    self.linkParameters('write', 'source_volume',
                        linkMNItransformation)
    self.linkParameters('source_volume', 'read', linkSource)
    self.linkParameters('normalized_volume', 'read')
    self.setOptional('normalized_volume')
    self.setOptional('source_volume')


def execution(self, context):
    filetype = self.read.type
    if filetype is getDiskItemType( 'SPM99 normalization matrix' ) \
       or self.read.fullName()[-5:] == '_sn3d':
        spm2 = 0
    else:
        spm2 = 1

    AtoT = aims.readSpmNormalization(self.read.fullPath(),
                                     self.source_volume.fullPath())
    srcref = None
    h = AtoT.header()
    if 'source_referential' in h:
        srcref = h['source_referential']
    tm = registration.getTransformationManager()

    if self.target != 'normalized_volume in AIMS orientation':
        aims.write(AtoT, self.write.fullPath())
        if self.target == 'MNI template':
            destref = tm.referential(registration.talairachMNIReferentialId)
        else:
            destref = None

    else:  # normalized_volume in AIMS orientation

        nim = self.normalized_volume
        if not nim or not nim.isReadable():
            raise RuntimeError(
                _t_('normalized_volume shoud be specified when using this target mode')
            )
        context.write('use normalized image:', nim.fullPath(), '\n')
        hasnorm = 1
        attrs = shfjGlobals.aimsVolumeAttributes(nim)
        t1 = aims.Motion(attrs['transformations'][-1])
        AIMS = t1.inverse() * AtoT
        AIMS.header().update(AtoT.header())
        destref = tm.referential(nim)
        aims.write(AIMS, self.write.fullPath())

    if srcref or destref:
        tm.setNewTransformationInfo(self.write, srcref, destref)

    if self.removeSource:
        for f in self.read.fullPaths():
            os.unlink(f)
