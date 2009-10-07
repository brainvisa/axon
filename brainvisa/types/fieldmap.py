#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCIL license version 2 under
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
# knowledge of the CeCILL version 2 license and that you accept its terms.

include( 'builtin' )

#------------------- fieldMap -------------------------
FileType( 'Double echo complex image', '4D Volume' )
FileType( 'Echo magnitude image', '3D Volume' )
FileType( 'Difference Phase Map', '3D Volume' )
#Correlation maps to weight the least square criterion used in phase unwrapping
FileType( 'Correlation Quality Map', '3D Volume' )
#FileType( '', 'Label volume' )
FileType( 'Undistorted Shift Map', '3D Volume' )
#FileType( 'BRUKER raw data', 'Any Type', ['TAR-Archive BRUKER raw data', 'compressed TAR-Archive BRUKER raw data' ] )
#FileType( 'BRUKER EPI raw data', 'BRUKER raw data' )
#FileType( 'BRUKER T1 MRI raw data', 'BRUKER raw data' )
#FileType( 'BRUKER Fieldmap raw data', 'BRUKER raw data' )
#FileType( 'BRUKER reconstructed data', 'Any Type', ['TAR-Archive BRUKER reconstructed data', 'compressed TAR-Archive BRUKER reconstructed data' ] )
#FileType( 'BRUKER EPI reconstructed data', 'BRUKER reconstructed data' )
#FileType( 'BRUKER T1 MRI reconstructed data', 'BRUKER reconstructed data' )

#FileType( 'GEMS raw data', 'Any Type', 'TAR-Archive GEMS raw data' )
#FileType( 'GEMS raw EPI', 'GEMS raw data' )
#FileType( 'GEMS raw Fieldmap', 'GEMS raw data' )
#FileType( 'GEMS reconstructed data', 'Any Type', 'TAR-Archive GEMS reconstructed data' )
#FileType( 'GEMS reconstructed EPI', 'GEMS reconstructed data' )
#FileType( 'GEMS reconstructed Fieldmap', 'GEMS reconstructed data' )

#FileType( 'GEMS raw FieldMap', '3D Volume', 'GIS image' )
#HierarchyDirectoryType( 'fieldmap' )
FileType( 'EPI distorsion parameters', 'Text file' )
#FileType( 'FIELDMAP series', 'Any Type', ['BRUKER fieldmap' , 'Z compressed BRUKER fieldmap', 'gz compressed BRUKER fieldmap'] )
#FileType( 'Phase Map', 'Any Type', 'Phase image' )
