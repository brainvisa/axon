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

# Constants for default attributes values
default_center="subjects"
default_acquisition="default_acquisition"
default_analysis="default_analysis"
default_session="default_session"
default_graph_version="3.0"

hierarchy = (
  SetWeakAttr( 'database', '%f' ),
  SetContent(
    'scripts', SetContent('*', SetType('Script')), # directory that contains scripts to undo conversion or cleaning database processes
    'database', SetType( 'Database Cache file' ),
    'database_fso', SetType( 'Database description page' ),
    'database_settings', SetType( 'Database settings' ),
    '*', SetType('Database Cache file'), # database cache
    'trash', #directory containing files that must be deleted
    'analyzes', 
    SetContent(
      '{analysis}', SetType( 'Analysis Dir' ), 
      SetContent(# Set Content must be present even if it is empty, otherwise it is impossible to insert something in subject directory
      ),
    ),
    '{center}', SetFileNameStrongAttribute( 'center' ), SetType( 'Center' ), SetDefaultAttributeValue( 'center', default_center ),
    SetContent(
      "group_analysis",
      SetContent( '{group_of_subjects}',
        SetContent( '<group_of_subjects>_group', SetType( 'Group definition' ),
        ),
      ),
      '{subject}', SetFileNameStrongAttribute( 'subject' ), SetType( 'Subject' ),
      SetContent( # Set Content must be present even if it is empty, otherwise it is impossible to insert something in subject directory
      ),
    ),
  ),
)

# analysis

insert( 'analyzes/',
  '{analysis}', SetType( 'Analysis Dir' ), SetContent(),) # SetContent() because it is a directory



