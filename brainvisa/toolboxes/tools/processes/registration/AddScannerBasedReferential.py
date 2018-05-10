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
from brainvisa import registration
from brainvisa.tools import aimsGlobals
from soma import aims


name = 'AddScannerBasedReferential'
userLevel = 2

signature = Signature(
    'volume_input', ReadDiskItem("T1 MRI", 'Aims readable volume formats',
                                 enableConversion=False),
  'referential_volume_input', WriteDiskItem(
      'Referential of Raw T1 MRI', 'Referential'),
  'T1_TO_Scanner_Based', WriteDiskItem(
      'Transformation to Scanner Based Referential', 'Transformation matrix'),
  'new_referential', WriteDiskItem(
      'Scanner Based Referential', 'Referential'),
)


def initialization(self):
    self.linkParameters('referential_volume_input', 'volume_input')
    self.linkParameters('new_referential', 'volume_input')
    self.linkParameters('T1_TO_Scanner_Based', 'volume_input')


def execution(self, context):
    # Read header information
    atts = aimsGlobals.aimsVolumeAttributes(self.volume_input)
    ref = atts['referentials']
    trf = atts['transformations']
    if ("Scanner-based anatomical coordinates" in ref):
        trm_to_scannerBased = trf[
            ref.index("Scanner-based anatomical coordinates")]

    # Create a referential for Scanner-based
    tm = registration.getTransformationManager()
    dest = tm.referential(self.new_referential)
    context.write('dest:', dest)
    if dest is None:
        dest = tm.createNewReferentialFor(
            self.new_referential, referentialType='Scanner Based Referential')

    # Create a new referential if needed for the volume

    # src = tm.referential( self.volume_input )
    # print "Attributes"
    # print self.volume_input.hierarchyAttributes()
    # if src is None:
        # print "create src"
        # src = tm.createNewReferentialFor(self.volume_input)
        # print "apres"
        # print src

    src = tm.referential(self.referential_volume_input)
    context.write('src:', src)
    # print "Attributes"
    # print self.volume_input.hierarchyAttributes()
    if src is None:
        src = tm.createNewReferentialFor(self.volume_input,
                                         referentialType='Referential of Raw T1 MRI',
                                         output_diskitem=self.referential_volume_input)
    dest.setMinf('direct_referential', 1, saveMinf=True)

    # Store information into the trm file
    mot = aims.Motion(trm_to_scannerBased)
    aims.write(mot, self.T1_TO_Scanner_Based.fullPath())

    # set and update database
    tm.setNewTransformationInfo(
        self.T1_TO_Scanner_Based, source_referential=src, destination_referential=dest)
