from __future__ import print_function
from __future__ import absolute_import
import shutil
import os
from optparse import OptionParser
import soma.subprocess
import stat

from soma import aims
from soma import uuid
import soma.minf.api as minf
import brainvisa.data.temporary as temporary
import six


class Importer(object):
    
    @classmethod
    def import_image(cls, input_filename, output_filename, 
                     conversion_needed = False,
                     remove_nan_needed = False,
                     resampling_needed = False,
                     conversion_data_type = None, 
                     conversion_omin = None, 
                     conversion_omax = None,
                     resolution_level = None):
        """
        Import the input image file to the output filename location.
        Some checking and conversions may be done during the
        process.

        Parameters:
        -----------
        input_filename: string
            input image location
        output_filename: string
            output image location after importation
        conversion_needed: bool
            wether conversion is needed or not
        remove_nan_needed: bool
            wether remove nan is needed or not
        resampling_needed: bool
            wether resampling is needed or not
        conversion_data_type: string
            data type to use if conversion is needed
        conversion_omin: numeric
            output minimum dynamic value if resampling is needed
        conversion_omax: numeric
            output maximum dynamic value if resampling is needed
        resolution_level: int
            resolution level to import
            
        Returns:
        --------
        return_value: 0 upon success. Exceptions may be raised in case of
                      failure anyway.
        """
        from soma.path                     import update_query_string
        
        temp_input = None
        temp_filename = None
        return_value = 0
 
        if conversion_needed or resolution_level is not None:
            try:
                if resolution_level is not None:
                    input_filename = update_query_string(input_filename,
                                                         {'resolution_level':
                                                          resolution_level})
                    
                if remove_nan_needed:
                    ext = cls._file_extension(input_filename)
                    if temporary.manager is None:
                        temporary.initializeTemporaryFiles(
                            temporary.getSystemDefaultTempDir())
                    temp_filename = temporary.manager.new(suffix=ext)
                    command = ["AimsRemoveNaN", "-i", input_filename, "-o",
                               temp_filename]
                    return_value = soma.subprocess.call(command)
                    if return_value != 0:
                        raise ImportationError(
                            "The following command failed : \"%s\"" % '" "'
                            .join(command))
                    input_filename = temp_filename

                command_list = ['AimsFileConvert', '-i', input_filename,
                                '-o', output_filename]
                
                if conversion_data_type is not None:
                    command_list.extend(['-t', conversion_data_type])
                
                if resampling_needed:
                    if conversion_omin is not None \
                       or conversion_omax is not None:
                       command_list.append('-r')
                       
                       if conversion_omin is not None:
                           command_list.extend(['--omin', str(conversion_omin)])
                           
                       if conversion_omax is not None:
                           command_list.extend(['--omax', str(conversion_omax)])

                return_value = soma.subprocess.call(command_list)
                if return_value != 0:
                    raise ImportationError(
                        "The following command failed : \"%s\"" % '" "'
                        .join(command_list))
            finally:
                if temp_filename is not None:
                    if os.path.exists(temp_filename + '.minf'):
                        os.unlink(temp_filename + '.minf')
                if temp_input is not None:
                    os.remove(temp_input)

        elif os.path.abspath(os.path.normpath(os.path.realpath(
                input_filename))) == \
                os.path.abspath(os.path.normpath(os.path.realpath(
                    output_filename))):
            print('Warning: input and output files are the same, '
                  'copy is skipped.')

        else:
            try:
                shutil.copy(input_filename, output_filename)
                exts = {'.ima': ['.dim'], '.img': ['.hdr'],
                        '.vimg': ['.vinfo', '.vhdr']}
                for ext, other_exts in six.iteritems(exts):
                    if input_filename.endswith(ext):
                        for oext in other_exts:
                            shutil.copy(input_filename.replace(ext, oext),
                                        output_filename.replace(ext, oext))
                if os.path.exists(input_filename + ".minf"):
                    ominf = output_filename + ".minf"
                    shutil.copy(input_filename + ".minf", ominf)
                    # .minf needs Read/write permission
                    s = os.stat(ominf)
                    os.chmod(ominf, s.st_mode | stat.S_IREAD | stat.S_IWUSR)
            except IOError as e:
                raise ImportationError(str(e))
            
        return return_value
    
    @classmethod
    def import_t1mri(cls, input_filename, output_filename,
                     output_referential_filename=None,
                     referential_name='Referential of Raw T1 MRI'):
        """
        Import the input T1 MRI file to the output filename location.
        Importation is specialized for T1 MRI and for subsequent Morphologist
        processing. Some checking and conversions may be done during the
        process.

        NaN/infinite values are replaced by 0.
        Voxel type is converted to 16 bit int.
        Values dynamics is rescaled to 0-4095 if it exceeds this range.

        Parameters:
        -----------
        input_filename: string
            input image location
        output_filename: string
            output image location after importation
        output_referential_filename: string (optional)
            if specified a referential file (.refetential) will be created with
            a new UUID at this location, and the imported image header will
            reference it as referential.

        Returns:
        --------
        res_state: dict
            * return_value: 0 upon success. Exceptions may be raised in case of
              failure anyway.
            * warnings (if any): list of warning strings, meant to grant
              notify to the user any unexpected images sizes, resolutions...
        """
        #temp_input = None
        #temp_filename = None
        return_value = 0
    
        try:
            input_vol = aims.read(input_filename)
        except (aims.aimssip.IOError, IOError) as e:
            raise ImportationError(str(e))
        
        conversion_needed = cls._conversion_needed(input_filename, input_vol,
                                                   output_filename)
        remove_nan_needed = cls._remove_nan_needed(input_vol)
        resampling_needed = cls._resampling_needed(input_vol)
        
        return_value = cls.import_image(input_filename, 
                                        output_filename,
                                        conversion_needed = conversion_needed,
                                        remove_nan_needed = remove_nan_needed,
                                        resampling_needed = resampling_needed,
                                        conversion_data_type = 'S16',
                                        conversion_omin = 0,
                                        conversion_omax = 4095)

        if output_referential_filename:
            # write referential file and set the ref uuid in the image .minf
            ouuid = str(uuid.Uuid())
            ref_dict = {
                'uuid': ouuid,
                'dimension_count': 3,
                'name': referential_name,
            }
            open(output_referential_filename, 'w').write(
                'attributes = ' + repr(ref_dict))
            ominf = output_filename + ".minf"
            if os.path.exists(ominf):
                minf_content = minf.readMinf(ominf)[0]
            else:
                minf_content = {}
            minf_content['referential'] = ouuid
            open(ominf, 'w').write('attributes = ' + repr(minf_content))

        # check dimensions for unexpected values
        dims = input_vol.getSize()
        vs = input_vol.getVoxelSize()
        res_state = {'return_value': return_value}
        warns = []
        if vs[0] <= 0.6 or vs[1] <= 0.6 or vs[2] <= 0.6:
            warns.append(
                'Voxel size is unexpectedly small for a standard human T1 MRI (%fx%fx%f) - Your image is probably oversampled (possibly from the scanner reconstruction). Results are likely to be less accurate or erroneous. Please check.' % tuple(vs[:3]))
        if dims[0] >= 400 or dims[1] >= 400 or dims[2] >= 400:
            warns.append(
                'Image size is unexpectedly large for a standard human T1 MRI (%dx%dx%d) - Your image is probably oversampled (possibly from the scanner reconstruction). The Morphologist pipeline is tuned for about 1mm resolution images (typically 256x256x128 voxels). Processing will be longer, and require more memory. Please check.' % tuple(dims[:3]))
        if warns:
            res_state['warnings'] = warns
        return res_state

    @classmethod
    def _conversion_needed(cls, input_filename, input_vol, output_filename):
        convert = False
        if (cls._file_extension(input_filename)
                != cls._file_extension(output_filename)):
            convert = True
        else:
            header = input_vol.header()
            data_type = header["data_type"]
            file_format = header["file_type"]
            supported_formats = ['NIFTI-1', 'NIFTI-2', 'GIS', 'VIDA', 'MINC',
                                 'OpenSlide']
            convert = (file_format not in supported_formats) \
                or (data_type != "S16")
        return convert

    @staticmethod
    def _file_extension(filename):
        extension = ""
        name, ext = os.path.splitext(filename)
        while ext:
            extension = ext + extension
            name, ext = os.path.splitext(name)
        return extension

    @staticmethod
    def _resampling_needed(input_vol):
        header = input_vol.header()
        data_type = header["data_type"]
        need_resampling = False
        if data_type in ('FLOAT', 'DOUBLE'):
            need_resampling = True
        elif data_type not in ('RGB', 'RGBA', 'HSV'):
            min_value = input_vol.arraydata().min()
            max_value = input_vol.arraydata().max()
            if (min_value < 0) or (max_value < 100) or (max_value > 20000):
                need_resampling = True
        return need_resampling

    @staticmethod
    def _remove_nan_needed(input_vol):
        header = input_vol.header()
        data_type = header["data_type"]
        return data_type in ('FLOAT', 'DOUBLE')


class ImportationError(Exception):
    pass


if __name__ == '__main__':

    parser = OptionParser(usage='%prog input_file output_file '
                          '[output_referential_file]')
    options, args = parser.parse_args()
    if len(args) < 2 or len(args) > 3:
        parser.error(
            'Invalid arguments : input_file and output_file are mandatory.')
    res = Importer.import_t1mri(*args)
    if res['return_value'] != 0:
        raise RuntimeError('importation failed')
