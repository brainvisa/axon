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
This module provides a few functions using pyaims (soma.aims module), and defines several lists of formats (:py:class:`neuroDiskItems.NamedFormatList`):

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

import os
import sys
from brainvisa.data.neuroDiskItems import createFormatList, getFormat, \
    aimsFileInfo, DiskItem, Directory
from brainvisa.processes import defaultContext
from brainvisa.processing.neuroException import exceptionMessageHTML
from soma.path import find_in_path

#------------
# IMPORTANT : In a formats list, the most common formats should be placed
# at the begining of the list.
#------------

_formats_table = {
    'NIFTI-1': ('gz compressed NIFTI-1 image', 'NIFTI-1 image'),
    'GIS': 'GIS Image',
    'SPM': 'SPM image',
    'VIDA': 'VIDA Image',
    'ECAT': ('ECAT v image', 'ECAT i image'),
    'JPEG': 'JPEG image',
    'JPEG(Qt)': 'JPEG image',
    'JPG': 'JPEG image',
    'GIF': 'GIF image',
    'PNG': 'PNG image',
    'MNG': 'MNG image',
    'BMP': 'BMP image',
    'PBM': 'PBM image',
    'PGM': 'PGM image',
    'PPM': 'PPM image',
    'XBM': 'XBM image',
    'XPM': 'XPM image',
    'TIFF': ('TIFF image', 'TIFF(.tif) image'),
    'TIFF(Qt)': ('TIFF image', 'TIFF(.tif) image'),
    'MINC': ('MINC image', 'gz compressed MINC image'), # might be modified
    'FREESURFER-MINC': ('FreesurferMGZ', 'FreesurferMGH'),
    'DICOM': ('DICOM image', 'Directory'),
    'FDF': 'FDF image',
    'GIFTI': 'GIFTI file',
    'MESH': 'MESH mesh',
    'TRI': 'TRI mesh',
    'PLY': 'PLY mesh',
    'MNI_OBJ': 'MNI OBJ mesh',
    #'WAVEFRONT': 'WAVEFRONT mesh',
    'TEX': 'Texture',
}


_default_formats_priority = [
    # volumes
    'gz compressed NIFTI-1 image',
    'NIFTI-1 image',
    'GIS Image',
    'MINC image',
    'gz compressed MINC image',
    'SPM image',
    'Z Compressed GIS Image',
    'gz Compressed GIS Image',
    'ECAT v image',
    'ECAT i image',
    'FreesurferMGZ',
    'FreesurferMGH',
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
    'DICOM image',
    'Directory',  # dicom dir
    'FDF image',
    'VIDA Image',
    # meshes
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
    # textures
    # 'GIFTI file', # already in meshes
    'Texture',
    'Z compressed Texture',
    'gz compressed texture',
    'Z compressed GIFTI file',
    'gz compressed GIFTI file',
]


def aims_to_bv_formats(formats):
    '''
    Translates formats (single string or list) from AIMS formats names into
    BrainVISA's
    '''
    if isinstance(formats, (type(''), type(u''))):
        formats = [formats]
    oformats = []
    sformats = set()
    for format in formats:
        f = _formats_table.get(format)
        if f is not None:
            if isinstance(f, (list, tuple, set)):
                oformats += [x for x in f
                             if x not in sformats
                                and getFormat(x, None) is not None]
                sformats.update(f)
            elif f not in sformats and getFormat(f, None) is not None:
                  oformats.append(f)
                  sformats.add(f)
        elif format not in sformats and getFormat(format, None) is not None:
            oformats.append(format)
            sformats.add(format)
    return oformats


def zipped_bv_formats(formats):
    '''
    Translates formats (single string or list) from AIMS formats names into
    BrainVISA's, and adds gz/Z compressed versions
    '''
    if isinstance(formats, (type(''), type(u''))):
        formats = [formats]
    sformats = set()
    oformats = []
    for format in formats:
        bv_formats = aims_to_bv_formats(format)
        if isinstance(bv_formats, (tuple, list, set)):
            oformats += [x for x in bv_formats if x not in sformats]
            sformats.update(bv_formats)
        else:
            bv_formats = [bv_formats]
            if bv_format not in sformats:
                oformats.append(bv_format)
                sformats.add(bv_format)
        for bv_format in bv_formats:
            if bv_format.startswith('gz compressed ') \
                    or getFormat(bv_format).fileOrDirectory() is Directory:
                continue # OK done
            zf = 'gz compressed %s' % bv_format
            if zf not in sformats:
                oformats.append(zf)
                sformats.add(zf)
            zf = 'Z compressed %s' % bv_format
            if zf not in sformats:
                oformats.append(zf)
                sformats.add(zf)
    return oformats


def reordered_formats(formats, priority_list=_default_formats_priority):
    '''
    Reorder brainvisa formats according to a priority list: set formats from
    the priority list first (in their order) when they are part of the formats
    list, then append the remaining ones (in their order also)
    '''
    oformats = []
    sformats = set(formats)
    for format in priority_list:
        if format in sformats and getFormat(format, None) is not None:
            oformats.append(format)
    done = set(oformats)
    oformats += [f for f in formats
                 if f not in done and getFormat(f, None) is not None]
    return oformats


def initializeFormatLists():
    """
    Initializes several lists of formats. The lists are stored in global variables.
    """
    from soma.qt_gui import headless
    try:
        from soma import aims
        # handle headless Qt if needed
        try:
            from soma.qt_gui.qt_backend import QtWidgets
        except ImportError:
            pass  # never mind
        # fix mgz format
        aims.carto.PluginLoader.load()
        io = aims.supported_io_formats() # to test is works
        del io
        if 'mgz' in aims.Finder.extensions('MINC'):
            global _formats_table
            _formats_table['MINC'] = (
                'MINC image', 'gz compressed MINC image', 'FreesurferMGZ',
                'FreesurferMGH')
    except Exception as exc:
        msg = 'ERROR in aims loading: ' + str(exc) \
            + '<br/><p>AIMS could not be loaded. BrainVISA will work ' \
              'in degraded mode, AIMS format lists will be empty and ' \
              'processes that depend on AIMS will not load.</p>'
        print(msg, file=sys.stderr)
        defaultContext().showException(msg)

        # no aims, formats lists are empty
        class FakeAims(object):
            @staticmethod
            def supported_io_formats(*args, **kwargs):
                return set()
        aims = FakeAims()

    global anatomistVolumeFormats
    anatomistVolumeFormats = createFormatList(
        'Anatomist volume formats',
        reordered_formats(zipped_bv_formats(
            aims.supported_io_formats('Volume', 'r'))))

    global aimsVolumeFormats
    aimsVolumeFormats = createFormatList(
        'Aims readable volume formats',
        reordered_formats(aims_to_bv_formats(
            aims.supported_io_formats('Volume', 'r'))))

    global aimsWriteVolumeFormats
    # handle an exception for Minc/Mgz support in aims 4.6
    fvolformats = aims_to_bv_formats(aims.supported_io_formats('Volume', 'w'))
    if 'FreesurferMGH' in fvolformats \
            and 'mgz' in aims.Finder.extensions('MINC'):
        fvolformats.remove('FreesurferMGH')
        fvolformats.remove('FreesurferMGZ')
    aimsWriteVolumeFormats = createFormatList(
        'Aims writable volume formats',
        reordered_formats(fvolformats))

    global aimsImageFormats
    aimsImageFormats = createFormatList(
        'Aims image formats',
      reordered_formats((
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
      ))
    )

    global _aimsVolumeFormats
    _aimsVolumeFormats = None

    global anatomistMeshFormats
    anatomistMeshFormats = createFormatList(
        'Anatomist mesh formats',
        reordered_formats(zipped_bv_formats(
            aims.supported_io_formats('Mesh', 'r'))))

    global vipVolumeFormats
    vipVolumeFormats = aimsVolumeFormats

    global aimsMeshFormats
    aimsMeshFormats = createFormatList(
        'Aims mesh formats',
        reordered_formats(aims_to_bv_formats(
            aims.supported_io_formats('Mesh', 'rw'))))

    global aimsTextureFormats
    aimsTextureFormats = createFormatList(
        'Aims texture formats',
        reordered_formats(aims_to_bv_formats(
            aims.supported_io_formats('Texture', 'rw'))))

    global anatomistTextureFormats
    anatomistTextureFormats = createFormatList(
        'Anatomist texture formats',
        reordered_formats(zipped_bv_formats(
            aims.supported_io_formats('Texture', 'r'))))

    wkhtmltopdf = find_in_path('wkhtmltopdf')
    if wkhtmltopdf is not None:
        html_pdf_formats_l = ('HTML', 'PDF file')
    else:
        html_pdf_formats_l = ('HTML', )
    global html_pdf_formats
    html_pdf_formats = createFormatList('HTML PDF', html_pdf_formats_l)


def aimsVolumeAttributes(item, writeOnly=0, forceFormat=0):
    """
    Gets the header attributes of a :py:class:`DiskItem` if the item is a readable volume.

    :param item: the diskitem
    :param writeonly: if True, the function just returns an empty dictionary
    :param forceFormat: if True, the format of the diskitem is not checked
    :returns: a dictionary containing the attributes of the header.
    """
    if writeOnly:
        return {}
    # Get formats objects from formats names
    global _aimsVolumeFormats
    if _aimsVolumeFormats is None:
        _aimsVolumeFormats = [getFormat(x) for x in aimsVolumeFormats] \
            + [getFormat(y) for y in ['Series of ' + x.name
                                      for x in aimsVolumeFormats]]

    result = {}
    if isinstance(item, DiskItem) and \
        (forceFormat or item.format in _aimsVolumeFormats) \
            and item.isReadable():
        result = aimsFileInfo(item.fullPath())
    else:
        # item is a string, use FileInfo directly
        result = aimsFileInfo(item)
    # Byte swapping should not be in image header but Aims gives this internal
    # information.
    result.pop('byte_swapping', None)
    return result

# Try to open ftp connection to pelles to see if we are in shfj
import ftplib
from brainvisa.validation import ValidationError

inSHFJ = os.path.exists('/product')  # and os.path.exists( '/home/appli' )


def validationOnlyInSHFJ():
    if not inSHFJ:
        raise ValidationError(_t_('not available outside SHFJ'))
