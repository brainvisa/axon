import shutil
import os
import tempfile
from optparse import OptionParser
import subprocess
import stat

from soma import aims


class Importer:

    @classmethod
    def import_t1mri(cls, input_filename, output_filename):
        temp_input = None
        temp_file = None
        return_value = 0

        try:
            input_vol = aims.read(input_filename)
        except (aims.aimssip.IOError, IOError), e:
            raise ImportationError(e.message)

        if cls._conversion_needed(input_filename, input_vol, output_filename):
            try:
                if cls._remove_nan_needed(input_vol):
                    ext = cls._file_extension(input_filename)
                    temp_file = tempfile.NamedTemporaryFile(suffix=ext)
                    temp_filename = temp_file.name
                    command = ["AimsRemoveNaN", "-i", input_filename, "-o",
                               temp_filename]
                    return_value = subprocess.call(command)
                    if return_value != 0:
                        raise ImportationError(
                            "The following command failed : \"%s\"" % '" "'
                            .join(command))
                    input_filename = temp_file.name

                command_list = ['AimsFileConvert', '-i', input_filename,
                                '-o', output_filename,
                                '-t', 'S16']
                if cls._resampling_needed(input_vol):
                    command_list.extend(['-r', '--omin', "0", '--omax',
                                         "4095"])
                return_value = subprocess.call(command_list)
                if return_value != 0:
                    raise ImportationError(
                        "The following command failed : \"%s\"" % '" "'
                        .join(command_list))
            finally:
                if temp_file is not None:
                    if os.path.exists(temp_file.name + '.minf'):
                        os.unlink(temp_file.name + '.minf')
                    temp_file.close()
                if temp_input is not None:
                    os.remove(temp_input)

        elif os.path.abspath(os.path.normpath(os.path.realpath(
                input_filename))) == \
                os.path.abspath(os.path.normpath(os.path.realpath(
                    output_filename))):
            print 'Warning: input and output files are the same, ' \
                'copy is skipped.'

        else:
            try:
                shutil.copy(input_filename, output_filename)
                if input_filename.endswith(".ima"):
                    shutil.copy(input_filename.replace(".ima", ".dim"),
                                output_filename.replace(".ima", ".dim"))
                if os.path.exists(input_filename + ".minf"):
                    ominf = output_filename + ".minf"
                    shutil.copy(input_filename + ".minf", ominf)
                    # .minf needs Read/write permission
                    s = os.stat(ominf)
                    os.chmod(ominf, s.st_mode | stat.S_IREAD | stat.S_IWUSR)
            except IOError, e:
                raise ImportationError(e.message)
        return return_value

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
            convert = ((file_format != "NIFTI1") and (file_format != 'GIS')) \
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
        else:
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

    parser = OptionParser(usage='%prog input_file output_file')
    options, args = parser.parse_args()
    if len(args) != 2:
        parser.error(
            'Invalid arguments : input_file and output_file are mandatory.')
    Importer.import_t1mri(args[0], args[1])

