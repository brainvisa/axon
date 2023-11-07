import os

from brainvisa.processes import Signature, ReadDiskItem, WriteDiskItem
from brainvisa.processes import String, Float, Choice, Boolean

userLevel = 1
name = 'Run AssemblyNet'

assemblynet_options = 'AssemblyNet options'

signature = Signature(
    'assemblynet_image', String(),
    't1mri', ReadDiskItem('Raw T1 MRI', ['gz compressed NIFTI-1 image', 'NIFTI-1 image']),
    'subject_folder', ReadDiskItem('Subject', 'Directory'),
    'output_folder', WriteDiskItem('Directory', 'Directory'),

    'age', Float(section=assemblynet_options),
    'sex', Choice(None, 'Male', 'Female', section=assemblynet_options),
    'pdf_report', Boolean(section=assemblynet_options),
)


def validation():
    if os.system('apptainer'):
        raise OSError('Apptainer is not on the environment')


def initialization(self):
    self.pdf_report = True
    self.setOptional('age', 'sex')

    self.linkParameters('output_folder', 'subject_folder', self.update_output_folder)
    self.addLink('subject_folder', 't1mri', self.update_subject_folder)


def update_subject_folder(self, t1mri):
    sub = self.t1mri.get('subject')
    center = self.t1mri.get('center')
    database = self.t1mri.get('_database')
    return self.signature['subject_folder'].findValue({'subject': sub, 'center': center, '_database': database})


def update_output_folder(self, proc, dummy):
    tp = self.t1mri.get('acquisition')
    return os.path.join(self.subject_folder.fullPath(), 'assemblynet', tp)


def execution(self, context):
    command = [
        'apptainer',
        'run',
        '-B',
        f'{self.subject_folder.fullPath()}:/data',
        self.assemblynet_image,
    ]

    if self.age:
        command.extend(['-age', self.age])
    if self.sex:
        command.extend(['-sex', self.sex])
    if not self.pdf_report:
        command += '-no-pdf-report'
    
    if not os.path.exists(self.output_folder.fullPath()):
        os.makedirs(self.output_folder.fullPath())

    command.extend([
        self.t1mri.fullPath().replace(self.subject_folder.fullPath(), '/data'),
        self.output_folder.fullPath().replace(self.subject_folder.fullPath(), '/data')
    ])

    context.system(*command)
