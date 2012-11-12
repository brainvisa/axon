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

from brainvisa.configuration import neuroConfig

# Build-in formats
Format( 'Matlab script', "f|*.m" )
Format( 'Matlab file', 'f|*.mat' )
Format( 'gz Matlab file', 'f|*.mat.gz', attributes={'compressed': 'gz'}  )
Format( 'bz2 Matlab file', 'f|*.mat.bz2', attributes={'compressed': 'bz2'} )

# Volume formats
Format( 'GIS image', [ "f|*.ima", "f|*.dim" ] )
Format( 'Z compressed GIS image', [ "f|*.ima.Z", "f|*.dim.Z" ] )
Format( 'gz compressed GIS image', [ "f|*.ima.gz", "f|*.dim.gz" ] )
Format( 'VIDA image', [ "f|*.vimg", "f|*.vinfo", "f|*.vhdr" ] )
Format( 'Z compressed VIDA image', [ "f|*.vimg.Z", "f|*.vinfo.Z", "f|*.vhdr.Z" ], attributes={'compressed': 'Z'} )
Format( 'gz compressed VIDA image', [ "f|*.vimg.gz", "f|*.vinfo.gz", "f|*.vhdr.gz" ], attributes={'compressed': 'gz'} )
Format( 'Phase image', "f|*.pm" )
Format( 'SPM image', [ 'f|*.img', 'f|*.hdr' ] )
Format( 'Z compressed SPM image', [ 'f|*.img.Z', 'f|*.hdr.Z' ], attributes={'compressed': 'Z'} )
Format( 'gz compressed SPM image', [ 'f|*.img.gz', 'f|*.hdr.gz' ], attributes={'compressed': 'gz'} )
Format( 'ECAT v image', [ 'f|*.v' ] )
Format( 'Z compressed ECAT v image', [ 'f|*.v.Z' ], attributes={'compressed': 'Z'} )
Format( 'gz compressed ECAT v image', [ 'f|*.v.gz' ], attributes={'compressed': 'gz'} )
Format( 'ECAT i image', [ 'f|*.i' ] )
Format( 'Z compressed ECAT i image', [ 'f|*.i.Z' ], attributes={'compressed': 'Z'} )
Format( 'gz compressed ECAT i image', [ 'f|*.i.gz' ], attributes={'compressed': 'gz'} )
Format( 'DICOM image', [ '*.dcm' ], exclusive=1, ignoreExclusive=1 )
#Format( 'VISTA image', "f|*.v" )
Format( 'MINC image', "f|*.mnc" )
Format( 'gz compressed MINC image', "f|*.mnc.gz", attributes={'compressed': 'gz'} )
Format( 'NIFTI-1 image', "f|*.nii" )
Format( 'gz compressed NIFTI-1 image', "f|*.nii.gz", attributes={'compressed': 'gz'} )
#Format( 'BRUKER fieldmap', "f|*.raw" )
#Format( 'Z compressed BRUKER fieldmap', "f|*.raw.Z", attributes={'compressed': 'Z'} )
#Format( 'gz compressed BRUKER fieldmap', "f|*.raw.gz", attributes={'compressed': 'gz'} )

Format( 'TRI mesh', "f|*.tri" )
Format( 'Z compressed TRI mesh', "f|*.tri.Z" )
Format( 'gz compressed TRI mesh', "f|*.tri.gz" )
Format( 'MESH mesh', "f|*.mesh" )
Format( 'Z compressed MESH mesh', "f|*.mesh.Z" )
Format( 'gz compressed MESH mesh', "f|*.mesh.gz" )
Format( 'PLY mesh', 'f|*.ply' )
Format( 'Z compressed PLY mesh', 'f|*.ply.Z' )
Format( 'gz compressed PLY mesh', 'f|*.ply.gz' )
Format( 'GIFTI file', "f|*.gii" )
Format( 'Z compressed GIFTI file', 'f|*.gii.Z' )
Format( 'gz compressed GIFTI file', 'f|*.gii.gz' )
Format( 'MNI OBJ mesh', "f|*.obj" )
Format( 'Z compressed MNI OBJ mesh', 'f|*.obj.Z' )
Format( 'gz compressed MNI OBJ mesh', 'f|*.obj.gz' )

Format( 'Texture', 'f|*.tex' )
Format( 'Z compressed Texture', 'f|*.tex.Z' )
Format( 'gz compressed Texture', 'f|*.tex.gz' )

Format( 'Moment Vector', "f|*.inv" )

#Format( 'Lipsia design', 'f|*.des' )
Format( 'Transformation matrix', 'f|*.trm' )
Format( 'MINC transformation matrix', 'f|*.xfm' )

Format( 'Graph', "f|*.arg" )
Format( 'Graph and data', [ "f|*.arg", "d|*.data" ] )
Format( 'Config file', "f|*.cfg" )
Format( 'Hierarchy', "f|*.hie" )
Format( 'Tree', "f|*.tree" )

#Format( 'Ecat', 'f|*.i' )

Format( 'BrainVISA/Anatomist animation', 'f|*.banim' )
Format( 'MPEG film', 'f|*.mpg' )
Format( 'AVI film', 'f|*.avi' )
Format( 'QuickTime film', 'f|*.mov' )
Format( 'JPEG image', 'f|*.jpg' )
Format( 'GIF image', 'f|*.gif' )
Format( 'PNG image', 'f|*.png' )
Format( 'MNG image', 'f|*.mng' )
Format( 'BMP image', 'f|*.bmp' )
Format( 'PBM image', 'f|*.pbm' )
Format( 'PGM image', 'f|*.pgm' )
Format( 'PPM image', 'f|*.ppm' )
Format( 'XBM image', 'f|*.xbm' )
Format( 'XPM image', 'f|*.xpm' )
Format( 'TIFF image', 'f|*.tiff' )
Format( 'TIFF(.tif) image', 'f|*.tif' )

Format( 'Text file', 'f|*.txt' )
Format( 'CSV file', 'f|*.csv' )
Format( 'ASCII results', 'f|*.asc' )
Format( 'XML', 'f|*.xml' )
Format( 'gzipped XML', 'f|*.xml.gz' )
Format( 'Info file', "f|*.info" )
Format( 'ZIP file', 'f|*.zip' )

#Format( 'Matlab design file', 'f|*DesMtx.mat' )
#Postscript files for SPM results
Format( 'PS file', "f|*.ps" )
Format( 'gz compressed PS file', "f|*.ps.gz" )

Format( 'Log file', 'f|*.log' )
Format( 'pickle file', 'f|*.pickle')
Format( 'Database Cache file', 'f|*.fsd')
Format( 'SQLite Database File', 'f|*.sqlite' )
Format ( 'Python Script', "f|*.py" )

#For lessons and demo
Format( 'gz compressed TAR archive', 'f|*.tar.gz' )

# Scalar features
Format( 'Aims scalar features', 'f|*.features' )

Format( 'Bucket', 'f|*.bck' )

# selector files
Format( 'Selection', 'f|*.sel' )

# Data table files
Format( 'Text Data Table', 'f|*.dat' )

Format( 'Minf', 'f|*.minf' )
Format( 'HTML', 'f|*.html' )

# Make 'Series of SPM image' format exists
changeToFormatSeries( getFormat( 'SPM image' ) )

import brainvisa.tools.aimsGlobals as shfjGlobals
shfjGlobals.initializeFormatLists()

#-------------- General types ---------------------

FileType( 'Any Type', None, [] )

FileType( 'Directory', 'Any Type', 'Directory' )
# Remove DICOM format from default '4D Volume' formats because
# there is no specific file name extension for this format.
volumeFormats = list( shfjGlobals.anatomistVolumeFormats )
del volumeFormats[ volumeFormats.index( getFormat( 'DICOM image' ) ) ]
createFormatList( 'BrainVISA volume formats', volumeFormats )
createFormatList( 'BrainVISA image formats', 'Aims image formats' )
createFormatList( 'BrainVISA mesh formats', 'Anatomist mesh formats' )
createFormatList( 'BrainVISA texture formats', 'Anatomist texture formats' )


FileType( '4D Volume', 'Any Type', 'BrainVISA volume formats') #minfAttributes=shfjGlobals.aimsVolumeAttributes )
FileType( '3D Volume', '4D Volume' )
FileType( '2D Image', '3D Volume', 'BrainVISA image formats' )
FileType( 'Mesh', 'Any Type', 'BrainVISA mesh formats' )
FileType( 'Texture', 'Any Type', 'BrainVISA texture formats' )
FileType( 'Label Texture', 'Texture' )
FileType( 'Log file', 'Any Type', [ 'Log file', 'Text file' ] )
FileType( 'Text file', 'Any Type' )
FileType( 'CSV file', 'Text file', 'CSV file' )
FileType( 'HTML file', "Any Type", 'HTML')
FileType( 'GIFTI geometry', 'Any type', 'GIFTI file' )
FileType( 'Bucket', 'Any Type', 'Bucket' )

# There's a bug in BrainVISA when using 'Directory' as base type
# FileType( 'Protocol','Directory' )
# FileType( 'Subject','Directory' )
# FileType( 'Session','Directory' )
HierarchyDirectoryType( 'Protocol', 'Any type' )
HierarchyDirectoryType( 'Subject', 'Any type' )
HierarchyDirectoryType( 'Session', 'Any type' )

FileType( 'gz compressed TAR archive', 'Any Type', 'gz compressed TAR archive' )
FileType( 'Scalar features', 'Any Type', 'Aims scalar features' )
FileType( 'Bundles scalar features', 'Scalar features' )
FileType( 'Roi scalar features', 'Scalar features' )

FileType( 'Data Table', 'Any Type', 'Text Data Table' )


FileType( 'XML parameters', 'Text file', 'XML')

FileType( 'pickle file', 'Any Type', 'pickle file' )
FileType( 'Database Cache file', 'Any Type', ('Database Cache file', 'SQLite Database File'))
FileType( 'Database description page', 'HTML file' )
FileType( 'Database settings', 'Text file', 'Minf' )
FileType( 'Script', 'Text file', 'Python Script')

# ROI can be either a 'Graph and data' or a 'Volume 3D'
# It should be a subtype of 'Graph' but the default format
# for 'Graph' is 'Graph' but BrainVISA processes needs to
# kwnow all format file names in order to build temporary
# values. This is why I suggest to use 'Graph and data' instead 'Graph'.
# All of this has to be discussed.
FileType( 'ROI', 'Any Type', [ 'Graph and Data' ] + getDiskItemType( '3D Volume' ).formats )
FileType( 'Error mask', 'ROI' )
FileType( 'Curves graph', 'ROI' )

# selector files
FileType( 'Labels selection', None, 'Selection' )

#----------- Visualization / Animation ------------

FileType( 'BrainVISA/Anatomist animation', 'Any Type',
          'BrainVISA/Anatomist animation' )
FileType( 'MPEG film', 'Any Type', ( 'MPEG film', 'AVI film' ) )

FileType( 'MINC image', 'Any Type', 'MINC image')
FileType( 'Display BIC drawing', 'MINC image' )
FileType( 'Anatomist BIC drawing', '3D Volume' )


#----------------- Toolbox ----------------------
FileType( 'Coordinates File', 'Text file' )

#--------------- Subject Info -------------------
FileType( 'Subject Info', 'Any Type', 'Info file' )

#----------------- Anatomy (base) ---------------

FileType( 'T1 MRI', '3D Volume' )
FileType( 'T2 MRI', '3D Volume' )
FileType( 'Raw T1 MRI', 'T1 MRI' )
FileType( 'Label volume', '3D Volume' )
FileType( 'Rainbow 3D volume', '3D Volume' )
FileType( 'Split Brain Mask', 'Label Volume' )

#----------------- Graphs -------------------------

Format( 'Label Translation', "f|*.trl" )
Format( 'DEF Label Translation', "f|*.def" )

FileType( 'Graph', 'Any Type', 'Graph' )
FileType( 'Data graph', 'Graph' )
FileType( 'Model graph', 'Graph' )
FileType( 'Data description', 'HTML file' )
FileType( 'Roi graph', 'Data graph' )
FileType( 'Label translation or Nomenclature', 'Any Type',
          [ 'Label Translation', 'DEF Label Translation', 'Hierarchy' ] )
FileType( 'Hierarchy', 'Label translation or Nomenclature', 'Hierarchy' )
FileType( 'Nomenclature', 'Hierarchy' )
FileType( 'Label translation', 'Label translation or Nomenclature',
          [ 'Label Translation', 'DEF Label Translation' ] )

#--- General types for fMRI ---------------------
#FileType( 'Functional volume', '4D Volume' )
FileType( '3D Functional volume', '3D Volume' )
FileType( '4D Functional volume', '4D Volume' )
FileType( 'fMRI', '4D Volume' )
FileType( 'fMRI activations', '3D functional volume' )

# Group analysis
FileType( 'Group definition', 'XML parameters', 'XML' )

FileType( 'Matlab SPM file', 'Any Type', [ 'Matlab file', 'gz Matlab file', 'bz2 Matlab file' ] )
#Postscript files for SPM results
FileType( 'Postscript file', 'Any Type', [ 'PS file', 'gz compressed PS file'] )
