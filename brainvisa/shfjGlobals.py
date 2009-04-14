# Copyright CEA and IFR 49 (2000-2005)
#
#  This software and supporting documentation were developed by
#      CEA/DSV/SHFJ and IFR 49
#      4 place du General Leclerc
#      91401 Orsay cedex
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

import os, string
from neuroDiskItems import createFormatList, getFormat, aimsFileInfo
import neuroConfig

#------------
# IMPORTANT : In a formats list, the most common formats should be placed
# at the begining of the list.
#------------

anatomistVolumeFormats = createFormatList( 
  'Anatomist volume formats', 
  ( 
    'GIS Image', 
    'SPM image',
    'VIDA Image',
    'ECAT v image',
    'ECAT i image',
    'Z Compressed GIS Image', 
    'gz Compressed GIS Image', 
    'Z compressed VIDA Image',
    'gz compressed VIDA Image',
    'Z compressed SPM image',
    'gz compressed SPM image', 
    'Z compressed ECAT v image',
    'gz compressed ECAT v image',
    'Z compressed ECAT i image',
    'gz compressed ECAT i image',
    'JPEG image',
    'GIF image',
    'PNG image',
    'MNG image',
    'BMP image',
    'PBM image',
    'PGM image',
    'PPM image',
    'XBM image',
    'XPM image',
    'TIFF image',
    'TIFF(.tif) image',
    'MINC image',
    'NIFTI-1 image',
    'gz compressed NIFTI-1 image',
    'DICOM image',
  )
)


aimsVolumeFormats = createFormatList(
  'Aims readable volume formats',
  ( 
    'GIS Image', 
    'SPM image',
    'VIDA Image',
    'ECAT v image',
    'ECAT i image',
    'JPEG image',
    'GIF image',
    'PNG image',
    'MNG image',
    'BMP image',
    'PBM image',
    'PGM image',
    'PPM image',
    'XBM image',
    'XPM image',
    'TIFF image',
    'TIFF(.tif) image',
    'MINC image',
    'NIFTI-1 image',
    'gz compressed NIFTI-1 image',
    'DICOM image',
  )
)

aimsWriteVolumeFormats = createFormatList(
  'Aims writable volume formats',
  ( 
    'GIS Image', 
    'SPM image',
    'VIDA Image',
    'ECAT v image',
    'ECAT i image',
    'JPEG image',
    'MINC image',
    'NIFTI-1 image',
    'gz compressed NIFTI-1 image',
  )
)

aimsImageFormats = createFormatList(
  'Aims image formats',
  (
    'JPEG image',
    'GIF image',
    'PNG image',
    'MNG image',
    'BMP image',
    'PBM image',
    'PGM image',
    'PPM image',
    'XBM image',
    'XPM image',
    'TIFF image',
    'TIFF(.tif) image',
  )
)
_aimsVolumeFormats = None

anatomistMeshFormats = createFormatList(
  'Anatomist mesh formats',
  (
    'MESH mesh',
    'TRI mesh',
    'Z compressed MESH mesh',
    'gz compressed MESH mesh',
    'Z compressed TRI mesh',
    'gz compressed TRI mesh',
    'PLY mesh',
    'Z compressed PLY mesh',
    'gz compressed PLY mesh',
  )
)

vipVolumeFormats = aimsVolumeFormats

aimsMeshFormats = createFormatList(
  'Aims mesh formats',
  (
    'MESH mesh',
    'TRI mesh',
    'PLY mesh',
  )
)
_fileInfoFormats = None


def aimsVolumeAttributes( item, writeOnly=0, forceFormat=0 ):
  if writeOnly: return {}
  # Get formats objects from formats names
  global _aimsVolumeFormats
  if _aimsVolumeFormats is None:
    _aimsVolumeFormats = map( getFormat, aimsVolumeFormats ) \
      + map( getFormat, map( lambda x: 'Series of ' + x.name, aimsVolumeFormats ) )
  
  result = {}
  if ( forceFormat or item.format in _aimsVolumeFormats ) and item.isReadable():
    result = aimsFileInfo( item.fullPath() )
  # Byte swapping should not be in image header but Aims gives this internal information.
  result.pop( 'byte_swapping', None )
  return result

# Try to open ftp connection to pelles to see if we are in shfj
import ftplib
from brainvisa.validation import ValidationError

inSHFJ = os.path.exists( '/product' ) # and os.path.exists( '/home/appli' )


def validationOnlyInSHFJ():
  if not inSHFJ:
    raise ValidationError( _t_( 'not available outside SHFJ' ) )

