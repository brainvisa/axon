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
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
from __future__ import absolute_import
__docformat__ = "epytext en"

from soma.configuration import ConfigurationGroup
from soma.signature.api import Signature, Unicode, FileName, Sequence, Boolean
import os

#------------------------------------------------------------------------------


class SPMConfiguration(ConfigurationGroup):
    label = 'SPM'
    icon = 'matlab.png'
    signature = Signature(
        'spm12_path', FileName(directoryOnly=True, readOnly=True), dict(
            defaultValue='', doc='location of SPM 12 installation directory'),
      'spm12_standalone_command', FileName(directoryOnly=False, readOnly=True), dict(
          defaultValue='', doc='location of SPM 12 standalone (compiled) run script'),
      'spm12_standalone_mcr_path', FileName(directoryOnly=True, readOnly=True), dict(
          defaultValue='', doc='location of SPM 12 standalone MCR directory (generally ./spm12-standalone/mcr/v713'),
      'spm12_standalone_path', FileName(directoryOnly=True, readOnly=True), dict(
          defaultValue='', doc='location of SPM 12 standalone directory where the templates directory can be found.(Maybe ./spm12-standalone/spm12_mcr/spm12)'),
      'spm8_path', FileName(directoryOnly=True, readOnly=True), dict(
          defaultValue='', doc='location of SPM 8 installation directory'),
      'spm8_standalone_command', FileName(directoryOnly=False, readOnly=True), dict(
          defaultValue='', doc='location of SPM 8 standalone (compiled) run script'),
      'spm8_standalone_mcr_path', FileName(directoryOnly=True, readOnly=True), dict(
          defaultValue='', doc='location of SPM 8 standalone MCR directory (generally &lt;spm8&gt;/standalone/mcr/v713'),
      'spm8_standalone_path', FileName(directoryOnly=True, readOnly=True), dict(
          defaultValue='', doc='location of SPM 8 standalone directory where the templates directory can be found.'),
      'spm8_wfu_pickatlas_path', FileName(directoryOnly=True, readOnly=True), dict(
          defaultValue='', doc='location of SPM8 WFU PickAtlas directory where the atlases can be found.'),
      'spm5_path', FileName(directoryOnly=True, readOnly=True), dict(
          defaultValue='', doc='location of SPM 5 installation directory'),
    )

    def __init__(self, *args, **kwargs):
        super(SPMConfiguration, self).__init__(*args, **kwargs)
