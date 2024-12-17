import os, shutil

from brainvisa.processes import Signature, ReadDiskItem, WriteDiskItem
from brainvisa.processes import String, Float, Choice, Boolean

userLevel = 2
name = 'Run AssemblyNet - generic'

assemblynet_options = 'AssemblyNet options'

signature = Signature(
    'assemblynet_image', String(),
    't1mri', ReadDiskItem('4D Volume', ['gz compressed NIFTI-1 image', 'NIFTI-1 image']),
    'output_folder', WriteDiskItem('Directory', 'Directory'),

    'age', Float(section=assemblynet_options),
    'sex', Choice(None, 'Male', 'Female', section=assemblynet_options),
    'pdf_report', Boolean(section=assemblynet_options),
)


def validation():
    if not shutil.which('apptainer'):
        raise OSError('Apptainer is not on the environment')


def initialization(self):
    self.pdf_report = True
    self.setOptional('age', 'sex')


def execution(self, context):
    t1mri_parent = os.path.dirname(self.t1mri.fullPath())
    tmp_dir = context.temporary('Directory')
    command = [
        'apptainer',
        'run',
        '-B',
        f'{tmp_dir.fullPath()}:/tmp',
        '-B',
        f'{t1mri_parent}:/data',
        '-B',
        f'{self.output_folder.fullPath()}:/data_output',
        self.assemblynet_image,
    ]

    if self.age:
        command.extend(['-age', self.age])
    if self.sex:
        command.extend(['-sex', self.sex])
    if not self.pdf_report:
        command += '-no-pdf-report'

    os.makedirs(self.output_folder.fullPath(), exist_ok=True)

    command.extend([
        self.t1mri.fullPath().replace(t1mri_parent, '/data'),
        '/data_output'
    ])

    context.system(*command)
