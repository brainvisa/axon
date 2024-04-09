from brainvisa.processes import Signature, Choice, String, ReadDiskItem, WriteDiskItem, DiskItem
from brainvisa.processes import getFormat, neuroConfig
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
    'inv1', ReadDiskItem('Raw MP2RAGE INV1', 'Aims readable volume formats'),
    'inv2', ReadDiskItem('Raw MP2RAGE INV2', 'Aims readable volume formats'),
    't1map', ReadDiskItem('Raw MP2RAGE T1MAP', 'Aims readable volume formats'),
    'uni', ReadDiskItem('Raw MP2RAGE UNI', 'Aims readable volume formats'),
    'output_inv1', WriteDiskItem('Raw MP2RAGE INV1', ['GIS image', 'NIFTI-1 image', 'gz compressed NIFTI-1 image']),
    'output_inv2', WriteDiskItem('Raw MP2RAGE INV2', ['GIS image', 'NIFTI-1 image', 'gz compressed NIFTI-1 image']),
    'output_t1map', WriteDiskItem('Raw MP2RAGE T1MAP', ['GIS image', 'NIFTI-1 image', 'gz compressed NIFTI-1 image']),
    'output_uni', WriteDiskItem('Raw MP2RAGE UNI', ['GIS image', 'NIFTI-1 image', 'gz compressed NIFTI-1 image']),
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
    if inp is not None and isinstance(inp, DiskItem):
        value = inp.hierarchyAttributes()
        if value.get("subject", None) is None:
            value["subject"] = os.path.basename(inp.fullPath()).partition(".")[0]
    return value


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

    self.setOptional('inv1', 'inv2', 't1map', 'uni',
                     'output_inv1', 'output_inv2', 'output_t1map', 'output_uni')
    # self.linkParameters('input_spm_orientation', 'input', _orient)
    self.signature['input_spm_orientation'].linkParameterWithNonDefaultValue = 1
    self.addLink("output_inv1", "inv1", self.initSubject)
    self.addLink("output_inv2", "inv2", self.initSubject)
    self.addLink("output_t1map", "t1map", self.initSubject)
    self.addLink("output_uni", "uni", self.initSubject)
    self.signature['output_inv1'].browseUserLevel = 3
    self.signature['output_inv2'].browseUserLevel = 3
    self.signature['output_t1map'].browseUserLevel = 3
    self.signature['output_uni'].browseUserLevel = 3
    self.signature['inv1'].databaseUserLevel = 2
    self.signature['inv2'].databaseUserLevel = 2
    self.signature['t1map'].databaseUserLevel = 2
    self.signature['uni'].databaseUserLevel = 2


# process execution
def execution(self, context):
    tm = registration.getTransformationManager()
    ref = None
    
    for input_image, output_image in zip([self.inv1, self.inv2, self.t1map, self.uni],
                                         [self.output_inv1, self.output_inv2, self.output_t1map, self.output_uni]):
        # to fetch all parameters of the input image (type, transfo, dimension, voxel size, ...)
        if input_image is None and output_image is None:
            continue
        inputAtts = aimsGlobals.aimsVolumeAttributes(input_image)
        dtype = inputAtts.get('data_type')
        input1 = input_image

        if input1.format is not output_image.format or dtype != 'S16':
            # Convert input to appropriate output format
            converter = context.getConverter(input1, output_image)
            if converter is None:
                raise RuntimeError('Cannot convert input data')
            if input_image.format in list(map(getFormat, ('SPM image', 'Series of SPM image'))):
                radio = isRadio(inputAtts)
                iradio = 0
                if self.input_spm_orientation == 'Radiological':
                    iradio = 1
                if radio is None or radio != iradio:
                    input1 = context.temporary(input1.format, 'Raw FLAIR MRI')
                    if neuroConfig.platform != 'windows':
                        os.symlink(input_image.fullName() + '.img',
                                    input1.fullName() + '.img')
                        os.symlink(input_image.fullName() + '.hdr',
                                    input1.fullName() + '.hdr')
                    else:
                        shelltools.cp(input_image.fullName() + '.img',
                                    input1.fullName() + '.img')
                        shelltools.cp(input_image.fullName() + '.hdr',
                                    input1.fullName() + '.hdr')
                    if os.path.exists(input_image.fullName() + '.img.minf'):
                        ominf = input1.fullName() + '.img.minf'
                        shelltools.cp(input_image.fullName() + '.img.minf', ominf)
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
                    input = output_image
                else:
                    input = context.temporary('NIFTI-1 image', 'Raw T1 MRI')
                context.runProcess(converter, input1, input)
            if dtype != 'S16':
                # here we must convert to S16 data type
                cmd = ['AimsFileConvert', '-i', input.fullPath(), '-o',
                        output_image.fullPath(), '-t', 'S16']
                if dtype not in ('U8', 'S8', 'U16'):
                    # apply rescaling if input type is wider than S16 to avoid losing any precision
                    cmd += ['-r', '--omin', 0, '--omax', 4095]
                context.system(*cmd)

        else:
            # Copy input files to output files
            inputFiles = input_image.fullPaths()
            outputFiles = output_image.fullPaths()
            if len(inputFiles) != len(outputFiles):
                raise RuntimeError('input and output do not have the same number of files')
            inputMinf = input_image.minfFileName()
            if os.path.isfile(inputMinf):
                # if there is a .minf file with the input file, copy it.
                ominf = output_image.fullPath() + '.minf'
                shelltools.cp(inputMinf, ominf)
                s = os.stat(ominf)
                os.chmod(ominf, s.st_mode | stat.S_IWUSR | stat.S_IWGRP)
            for i in range(len(inputFiles)):
                # copy input file in the brainvisa database
                context.write('cp', inputFiles[i], outputFiles[i])
                shelltools.cp(inputFiles[i], outputFiles[i])
            outputAtts = aimsGlobals.aimsVolumeAttributes(output_image)
            for x, y in outputAtts.items():
                if x != "dicom":
                    # force completing .minf, without dicom information
                    output_image.setMinf(x, y)
            output_image.saveMinf()
            output_image.readAndUpdateMinf()
            if input_image.format in list(map(getFormat,('SPM image', 'Series of SPM image'))):
                radio = isRadio(inputAtts)
                if self.input_spm_orientation == 'Neurological':
                    radio = 0
                elif self.input_spm_orientation == 'Radiological':
                    radio = 1
                # force completing spm_radio_convention in the .minf file
                output_image.setMinf('spm_radio_convention', radio)
            output_image.saveMinf()
        
        # the referential can be written in the file header (nifti)
        if output_image.minf().get('referential', None):
            output_image.removeMinf('referential')
        
        # save referential
        if ref is None:
            ref = tm.createNewReferentialFor(output_image, name='Raw MP2RAGE')
        else:
            tm.setReferentialTo(output_image, ref)

