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
"""
This module defines several lists of formats (:py:class:`neuroDiskItems.NamedFormatList`):

.. py:data:: anatomistVolumeFormats

  The name of the list is *Anatomist volume formats* and it contains the volume formats which are handled by Anatomist.
  
.. py:data:: aimsVolumeFormats
             vipVolumeFormats

  The name of the list is *Aims readable volume formats* and it contains the volume formats which can be read with Aims.
  
.. py:data:: aimsWriteVolumeFormats

  The name of the list is *Aims writable volume formats* and it contains the volume formats which can be written with Aims.

.. py:data:: aimsImageFormats

  The name of the list is *Aims image formats* and it contains the 2D image formats which are readable with Aims.

.. py:data:: anatomistMeshFormats

  The name of the list is *Anatomist mesh formats* and it contains the mesh formats which are handled by Anatomist.

.. py:data:: aimsMeshFormats

  The name of the list is *Aims mesh formats* and it contains the mesh formats which are handled by Aims.

.. py:data:: aimsTextureFormats

  The name of the list is *Aims texture formats* and it contains the texture formats which are handled by Aims.

.. py:data:: anatomistTextureFormats

  The name of the list is *Anatomist texture formats* and it contains the texture formats which are handled by Anatomist.

.. py:data:: html_pdf_formats

  Formats list for HTML format, and PDF if the wkhtmltopdf tool is installed on
  the system and available in the PATH.

These global variables are initialized through the function :py:func:`initializeFormatLists`.
"""
import os, string
from brainvisa.data.neuroDiskItems import createFormatList, getFormat, \
  aimsFileInfo, DiskItem
from soma.path import find_in_path

#------------
# IMPORTANT : In a formats list, the most common formats should be placed
# at the begining of the list.
#------------

def initializeFormatLists():
  """
  Initializes several lists of formats. The lists are stored in global variables.
  """
  global anatomistVolumeFormats
  anatomistVolumeFormats = createFormatList(
    'Anatomist volume formats',
    (
      'gz compressed NIFTI-1 image',
      'NIFTI-1 image',
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
      'gz compressed MINC image',
      'DICOM image',
      'Directory', # dicom dir
      'FDF image',
    )
  )
  global aimsVolumeFormats
  aimsVolumeFormats = createFormatList(
    'Aims readable volume formats',
    (
      'gz compressed NIFTI-1 image',
      'NIFTI-1 image',
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
      'gz compressed MINC image',
      'DICOM image',
      'Directory', # dicom dir
      'FDF image',
    )
  )

  global aimsWriteVolumeFormats
  aimsWriteVolumeFormats = createFormatList(
    'Aims writable volume formats',
    (
      'gz compressed NIFTI-1 image',
      'NIFTI-1 image',
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
      'MINC image',
      'gz compressed MINC image',
      'DICOM image',
      'Directory', # dicom dir
    )
  )

  global aimsImageFormats
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
  
  global _aimsVolumeFormats
  _aimsVolumeFormats = None

  global anatomistMeshFormats
  anatomistMeshFormats = createFormatList(
    'Anatomist mesh formats',
    (
      'GIFTI file',
      'MESH mesh',
      'TRI mesh',
      'Z compressed MESH mesh',
      'gz compressed MESH mesh',
      'Z compressed TRI mesh',
      'gz compressed TRI mesh',
      'PLY mesh',
      'Z compressed PLY mesh',
      'gz compressed PLY mesh',
      'Z compressed GIFTI file',
      'gz compressed GIFTI file',
      'MNI OBJ mesh',
      'Z compressed MNI OBJ mesh',
      'gz compressed MNI OBJ mesh',
    )
  )

  global vipVolumeFormats
  vipVolumeFormats = aimsVolumeFormats

  global aimsMeshFormats
  aimsMeshFormats = createFormatList(
    'Aims mesh formats',
    (
      'GIFTI file',
      'MESH mesh',
      'TRI mesh',
      'PLY mesh',
      'MNI OBJ mesh',
    )
  )

  global aimsTextureFormats
  aimsTextureFormats = createFormatList(
    'Aims texture formats',
    (
      'GIFTI file',
      'Texture',
    )
  )

  global anatomistTextureFormats
  anatomistTextureFormats = createFormatList(
    'Anatomist texture formats',
    (
      'GIFTI file',
      'Texture',
      'Z compressed Texture',
      'gz compressed texture',
      'Z compressed GIFTI file',
      'gz compressed GIFTI file',
    )
  )

  wkhtmltopdf = find_in_path('wkhtmltopdf')
  if wkhtmltopdf is not None:
      html_pdf_formats_l = ('HTML', 'PDF file')
  else:
      html_pdf_formats_l = ('HTML')
  global html_pdf_formats
  html_pdf_formats = createFormatList( 'HTML PDF', html_pdf_formats_l)



def aimsVolumeAttributes( item, writeOnly=0, forceFormat=0 ):
  """
  Gets the header attributes of a :py:class:`DiskItem` if the item is a readable volume. 
  
  :param item: the diskitem
  :param writeonly: if True, the function just returns an empty dictionary
  :param forceFormat: if True, the format of the diskitem is not checked
  :returns: a dictionary containing the attributes of the header.
  """
  if writeOnly: return {}
  # Get formats objects from formats names
  global _aimsVolumeFormats
  if _aimsVolumeFormats is None:
    _aimsVolumeFormats = list(map(getFormat, aimsVolumeFormats)) \
      + list(map(getFormat, map(lambda x: 'Series of ' + x.name,
                                aimsVolumeFormats)))

  result = {}
  if isinstance(item, DiskItem) and \
      (forceFormat or item.format in _aimsVolumeFormats) \
      and item.isReadable():
    result = aimsFileInfo(item.fullPath())
  else:
    # item is a string, use FileInfo directly
    result = aimsFileInfo(item)
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

