
from brainvisa.processes import *

userLevel = 0
roles = ('viewer', )

signature = Signature(
    'document', ReadDiskItem('PDF file', 'PDF file'),
)


def execution(self, context):
    context.pythonSystem('bv_pdf_viewer', self.document)

