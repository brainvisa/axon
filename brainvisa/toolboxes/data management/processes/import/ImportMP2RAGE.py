from brainvisa.processes import Signature, Choice, ReadDiskItem, WriteDiskItem, DiskItem, getFormat
from brainvisa.processes import neuroConfig
from brainvisa.tools     import aimsGlobals
from brainvisa           import shelltools
from brainvisa           import registration
import os
import stat
from six.moves import map


name = 'Import MP2RAGE MRI'
userLevel = 0
roles = ('importer')


# inputs/outputs definition
signature=Signature(
    'image_type', Choice('INV1', 'INV2', 'UNI', 'T1MAP'),
    'input', ReadDiskItem('Raw MP2RAGE INV1', 'Aims readable volume formats'),
    'output', WriteDiskItem('Raw MP2RAGE INV1', ['GIS image', 'NIFTI-1 image', 'gz compressed NIFTI-1 image']),
    'input_spm_orientation', Choice('Not applicable'),
)


# for SPM image, return the orientation in the header file
def isRadio(hdr):
    s2m = hdr.get('storage_to_memory')
    if s2m is None:
        radio = hdr.get('spm_radio_convention')
    else:
        radio = (s2m[0] > 0)
    return radio


# to fetch the name of the subject
def initSubject(self, inp):
    if self.input is not None and isinstance(self.input, DiskItem):
        value=self.input.hierarchyAttributes()
        if value.get("subject", None) is None:
            value["subject"]=os.path.basename(self.input.fullPath()).partition(".")[0]
    return value


def update_image_type(self, image_type):
    data_type = f'Raw MP2RAGE {image_type}'
    self.signature['input'].type = ReadDiskItem(data_type, 'Aims readable volume formats').type
    self.signature['output'].type = WriteDiskItem(data_type, ['GIS image', 'NIFTI-1 image', 'gz compressed NIFTI-1 image']).type
    self.changeSignature(self.signature)


# inputs/outputs initialization and management
def initialization(self):
    def _orient(self, proc):
        old = getattr(proc.signature['input_spm_orientation'], 'lastInput', None)
        if self.input is None \
            or old is None \
            or old.fullPath() != self.input.fullPath() \
            or proc.isDefault('input_spm_orientation'):
            hide = 1
            res = 'Not applicable'
            if self.input is not None:
                if self.input.format in list(map(getFormat, ('SPM image', 'Series of SPM image'))):
                    hide = 0
                    inputAtts = aimsGlobals.aimsVolumeAttributes(self.input)
                    radio = isRadio(inputAtts)
                    if radio is not None and radio != 0:
                        res = 'Radiological'
                    else:
                        res = 'Neurological'
            if hide:
                proc.signature['input_spm_orientation'].setChoices('Not applicable')
            else:
                proc.signature['input_spm_orientation'].setChoices('Neurological',
                                                                      'Radiological')
        else:
            # print 'using old value:', old, self.input_spm_orientation
            res = None
        proc.signature['input_spm_orientation'].lastInput = self.input
        return res

    self.addLink(None, 'image_type', self.update_image_type)
    self.linkParameters('input_spm_orientation', 'input', _orient)
    self.signature['input_spm_orientation'].linkParameterWithNonDefaultValue = 1
    self.addLink("output", "input", self.initSubject)
    self.signature['output'].browseUserLevel = 3
    self.signature['input'].databaseUserLevel = 2


# process execution
def execution(self, context):
    # to fetch all parameters of the input image (type, transfo, dimension, voxel size, ...)
    inputAtts = aimsGlobals.aimsVolumeAttributes(self.input)
    dtype = inputAtts.get('data_type')
    input1 = self.input

    if input1.format is not self.output.format or dtype != 'S16':
        # Convert input to appropriate output format
        converter = context.getConverter(input1, self.output)
        if converter is None:
            raise RuntimeError('Cannot convert input data')
        if self.input.format in list(map(getFormat, ('SPM image', 'Series of SPM image'))):
            radio = isRadio(inputAtts)
            iradio = 0
            if self.input_spm_orientation == 'Radiological':
                iradio = 1
            if radio is None or radio != iradio:
                input1 = context.temporary(input1.format, 'Raw FLAIR MRI')
                if neuroConfig.platform != 'windows':
                    os.symlink(self.input.fullName() + '.img',
                                input1.fullName() + '.img')
                    os.symlink(self.input.fullName() + '.hdr',
                                input1.fullName() + '.hdr')
                else:
                    shelltools.cp(self.input.fullName() + '.img',
                                   input1.fullName() + '.img')
                    shelltools.cp(self.input.fullName() + '.hdr',
                                   input1.fullName() + '.hdr')
                if os.path.exists(self.input.fullName() + '.img.minf'):
                    ominf = input1.fullName() + '.img.minf'
                    shelltools.cp(self.input.fullName() + '.img.minf', ominf)
                    s = os.stat(ominf)
                    os.chmod(ominf, s.st_mode | stat.S_IWUSR | stat.S_IWGRP)
                input1.readAndUpdateMinf()
                input1.setMinf('spm_radio_convention', iradio)
        input = input1
        if dtype in ('FLOAT', 'DOUBLE'):
            # in float/double images, NaN values may have been introduced
            # (typically by SPM after a normalization)
            input2 = context.temporary('NIFTI-1 image', 'Raw T1 MRI')
            context.system('AimsRemoveNaN', '-i', input1, '-o', input2)
            input1 = input2
            input = input2
        if converter._id != 'AimsConverter' or dtype == 'S16':
            if dtype == 'S16':
                input = self.output
            else:
                input = context.temporary('NIFTI-1 image', 'Raw T1 MRI')
            context.runProcess(converter, input1, input)
        if dtype != 'S16':
            # here we must convert to S16 data type
            cmd = ['AimsFileConvert', '-i', input.fullPath(), '-o',
                    self.output.fullPath(), '-t', 'S16']
            if dtype not in ('U8', 'S8', 'U16'):
                # apply rescaling if input type is wider than S16 to avoid losing any precision
                cmd += ['-r', '--omin', 0, '--omax', 4095]
            context.system(*cmd)

    else:
        # Copy input files to output files
        inputFiles = self.input.fullPaths()
        outputFiles = self.output.fullPaths()
        if len(inputFiles) != len(outputFiles):
            raise RuntimeError('input and output do not have the same number of files')
        inputMinf = self.input.minfFileName()
        if os.path.isfile(inputMinf):
            # if there is a .minf file with the input file, copy it.
            ominf = self.output.fullPath() + '.minf'
            shelltools.cp(inputMinf, ominf)
            s = os.stat(ominf)
            os.chmod(ominf, s.st_mode | stat.S_IWUSR | stat.S_IWGRP)
        for i in range(len(inputFiles)):
            # copy input file in the brainvisa database
            context.write('cp', inputFiles[i], outputFiles[i])
            shelltools.cp(inputFiles[i], outputFiles[i])
        outputAtts = aimsGlobals.aimsVolumeAttributes(self.output)
        for x, y in outputAtts.items():
            if x != "dicom":
                # force completing .minf, without dicom information
                self.output.setMinf(x, y)
        self.output.saveMinf()
        self.output.readAndUpdateMinf()
        if self.input.format in list(map(getFormat,('SPM image', 'Series of SPM image'))):
            radio = isRadio(inputAtts)
            if self.input_spm_orientation == 'Neurological':
                radio = 0
            elif self.input_spm_orientation == 'Radiological':
                radio = 1
            # force completing spm_radio_convention in the .minf file
            self.output.setMinf('spm_radio_convention', radio)
        self.output.saveMinf()
    # the referential can be written in the file header (nifti)
    if self.output.minf().get('referential', None):
        self.output.removeMinf('referential')
    # save referential
    tm = registration.getTransformationManager()
    ref = tm.createNewReferentialFor(self.output, name='Raw FLAIR MRI')

