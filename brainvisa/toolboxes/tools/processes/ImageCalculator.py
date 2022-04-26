from brainvisa.processes import Signature
from brainvisa.processes import ListOf, ReadDiskItem, WriteDiskItem
from brainvisa.processes import String, Boolean, Integer

userLevel = 1
name = "Image calculator (cartoLinearComb)"

signature = Signature(
    "images", ListOf(ReadDiskItem('3D Volume', 'aims readable Volume Formats')),
    "formula", String(),
    "lazy", Boolean(),
    "threads", Integer(),
    "output", WriteDiskItem('3D Volume', 'aims readable Volume Formats')
)


def initialization(self):
    self.setUserLevel(2, 'lazy', 'threads')
    self.lazy = False
    self.threads = 1


def execution(self, context):
    inputs = [f'{image.fullPath()}' for image in self.images]
    command = ['cartoLinearComb.py',
               '-f', self.formula,
               '-t', self.threads,
               '-o', self.output.fullPath(),
               '-i'] + inputs
    
    if self.lazy:
        command.append('-l')
    
    context.pythonSystem(*command)
    
