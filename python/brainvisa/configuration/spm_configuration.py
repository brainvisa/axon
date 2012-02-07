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
__docformat__ = "epytext en"

from soma.wip.configuration import ConfigurationGroup
from soma.signature.api import Signature, Unicode, FileName, Sequence, Boolean
import os

#------------------------------------------------------------------------------
class SPMConfiguration( ConfigurationGroup ):
  label = 'SPM'
  icon = 'matlab.png'
  signature = Signature(
    'spm8_path', FileName( directoryOnly=True ), dict( defaultValue='', doc='location of SPM 8 installation directory' ),
    'spm8_standalone_command', FileName( readOnly=True ), dict( defaultValue='', doc='location of SPM 8 standalone (compiled) run script' ),
    'spm8_standalone_mcr_path', FileName( directoryOnly=True ), dict( defaultValue='', doc='location of SPM 8 standalone MCR directory (generally &lt;spm8&gt;/standalone/mcr/v713' ),
    'spm8_standalone_path', FileName( directoryOnly=True ), dict( defaultValue='', doc='location of SPM 8 standalone directory where the templates directory can be found.' ),
    'spm5_path', FileName( directoryOnly=True ), dict( defaultValue='', doc='location of SPM 5 installation directory' ),
  )

  def _get_spm5_path( self ):
    return self._spm5_path
  def _set_spm5_path( self, value ):
    self._spm5_path = value
  spm5_path = property( _get_spm5_path, _set_spm5_path )

  def _get_spm8_path( self ):
    return self._spm8_path
  def _set_spm8_path( self, value ):
    self._spm8_path = value
  spm8_path = property( _get_spm8_path, _set_spm8_path )

  def _get_spm8_standalone_command( self ):
    return self._spm8_standalone_command
  def _set_spm8_standalone_command( self, value ):
    self._spm8_standalone_command = value
  spm8_standalone_command = property( _get_spm8_standalone_command,
    _set_spm8_standalone_command )

  def _get_spm8_standalone_mcr_path( self ):
    return self._spm8_standalone_mcr_path
  def _set_spm8_standalone_mcr_path( self, value ):
    self._spm8_standalone_mcr_path = value
  spm8_standalone_mcr_path = property( _get_spm8_standalone_mcr_path,
    _set_spm8_standalone_mcr_path )


  def __init__( self, *args, **kwargs ):
    self._spm5_path = None
    self._spmpath_checked = True
    self._spm8_path = None
    self._spm8_standalone_command = None
    self._spm8_standalone_mcr_path = None
    super( SPMConfiguration, self ).__init__( *args, **kwargs )

