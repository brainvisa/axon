# -*- coding: iso-8859-1 -*-

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
from brainvisa import anatomist

name = 'anatomist Show fMRI-MRI Fusion'
roles = ('viewer',)
userLevel = 0


def validation():
    anatomist.validation()

signature = Signature(
    'epi_series', ReadDiskItem("fMRI", 'anatomist Volume Formats'),
  'anatomy',    ReadDiskItem("T1 MRI", 'anatomist Volume Formats'),
)


def initialization(self):
    self.setOptional('anatomy')
    self.linkParameters('anatomy', 'epi_series')


def execution(self, context):

    a = anatomist.Anatomist()
    selfdestroy = []

    epi = a.loadObject(self.epi_series)
    epi.setPalette(a.getPalette("RED TEMPERATURE"))
    selfdestroy.append(epi)

    if self.anatomy is not None:
        anat = a.loadObject(self.anatomy, forceReload=True)
        selfdestroy.append(anat)
        fusion = a.fusionObjects([epi, anat], method='Fusion2DMethod')
        a.execute("Fusion2DParams", object=fusion, mode="linear",
                  rate=0.7, reorder_objects=[epi, anat])
        window = a.createWindow("Sagittal")
        window.assignReferential(epi.referential)
        window.addObjects([fusion])
        selfdestroy.append(fusion)
        selfdestroy.append(window)
        win3 = a.createWindow('Sagittal')
        win3.assignReferential(anat.referential)
        selfdestroy.append(win3)
        win3.addObjects([anat])

    return selfdestroy
#  return Anatomist.AnatomistFusionMaskonMRI( self.epi_series, self.anatomy, "RED TEMPERATURE", "linear",0.7)
#  return Anatomist.AnatomistActivationsOnMRI( fmri=self.epi_series, mri=self.anatomy, \
#                                              transformation= self.transformation,
# palette = 'RED TEMPERATURE', mode='linear')
