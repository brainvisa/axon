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
@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

import os
from soma.configuration import ConfigurationGroup
from soma.signature.api import HasSignature, Signature, FileName, \
                               Boolean, OpenedChoice, Sequence, Unicode, \
                               Choice, Any
from soma.minf.api import readMinf
import neuroConfig


#------------------------------------------------------------------------------
class DatabasesConfiguration( ConfigurationGroup ):
  label = 'Databases'
  icon = 'database_read.png'
  
  class FileSystemOntology( HasSignature ):
    signature = Signature(
      'directory', FileName, dict( defaultValue='' ),
      'selected', Boolean, dict( defaultValue=True ),
    )
  
    def __init__( self, directory='', selected=True ):
      super( DatabasesConfiguration.FileSystemOntology, self ).__init__()
      self.directory = directory
      self.selected = bool( selected )
      self.onAttributeChange( 'directory', self._directoryChanged )

    def _directoryChanged(self, newDirectory):
      if newDirectory and not os.path.exists(newDirectory):
        self.selected=False
  
  signature = Signature(
    'fso', Sequence( FileSystemOntology ), dict( defaultValue=[]),
  )


#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
class ExpertDatabaseSettings( HasSignature ):
  signature = Signature(
    'ontology', OpenedChoice(), dict( defaultValue='brainvisa-3.2.0',
                                      writeIfDefault=True ),
    'sqliteFileName', FileName, dict( defaultValue='' ),
    'activate_history', Boolean, dict( defaultValue=False ),
    #'fedji_backend', Boolean, dict( defaultValue=False ),
    'uuid', Unicode(), dict( defaultValue='', visible = False),
    # for compatibility only
    'lastIncrementalUpdate', Unicode(), dict(defaultValue='', visible=False),
    # no type dict defined in signature types, using Any
    'lastIncrementalUpdates', Any(), dict(defaultValue={}, visible=False),
  )

  def __init__( self ):
    #The list of ontolgies is never empty, so this test cannot to update this list and new ontology such as freesurfer are not added
    #in the expert_settings
    #if not ExpertDatabaseSettings.signature[ 'ontology' ].type.values:
    #  ExpertDatabaseSettings.signature[ 'ontology' ].type.setChoices( *ExpertDatabaseSettings.availableOntologies() )
    ExpertDatabaseSettings.signature[ 'ontology' ].type.setChoices( *ExpertDatabaseSettings.availableOntologies() )

    super( ExpertDatabaseSettings, self ).__init__()
    # fedj is hidden up to now, so is not in the signature but exists as an
    # instance variable. To activate it again:
    # * uncomment the fedji_backend item in the signature above
    # * remove the following line
    self.fedji_backend = False

  def __eq__( self , other):
    return ((self.ontology == other.ontology) and (self.sqliteFileName == other.sqliteFileName) and (self.activate_history == other.activate_history))
      
  @staticmethod
  def availableOntologies():
    ontologies = [ 'brainvisa-3.2.0', 'brainvisa-3.1.0', 'brainvisa-3.0',
      'shared' ]
    moreOntologies = set()
    for path in neuroConfig.fileSystemOntologiesPath:
      if os.path.exists( path ):
        for ontology in os.listdir( path ):
          if ontology == 'flat': continue
          if ontology not in ontologies and ontology not in moreOntologies:
            moreOntologies.add( ontology )
    ontologies += sorted( moreOntologies )
    return ontologies

#------------------------------------------------------------------------------
class DatabaseSettings( HasSignature ):
  signature = Signature(
    'directory', FileName( readOnly=True, directoryOnly=True ), #dict( defaultValue='' ),
    'expert_settings', ExpertDatabaseSettings, dict( collapsed=True ),
  )

  def __init__( self, directory=None, selected=True):
    HasSignature.__init__( self )
    self.expert_settings = ExpertDatabaseSettings()
    if directory :
      if os.path.exists( directory ) :
        self.directory = os.path.normpath(directory)
        self._selected = selected
      else :
        self._selected = False
    else :
      self._selected = selected
    self.builtin=False
    self.onAttributeChange( 'directory', self._directoryChanged )
    self._directoryChanged( directory )

  def __eq__( self , other):
    return ((self.directory == other.directory) and (self.expert_settings == other.expert_settings))

  def _directoryChanged( self, newDirectory ):
    if newDirectory:
      minf = os.path.join( newDirectory, 'database_settings.minf' )
      if os.path.exists( minf ):
        readMinf( minf, targets=( self.expert_settings, ) )
      else:
        it = self.expert_settings.signature.iteritems()
        it.next()
        for n, v in it:
          if n == 'ontology':
            self.expert_settings.ontology = 'brainvisa-3.2.0'
          else:
            setattr( self.expert_settings, n, v.defaultValue )
