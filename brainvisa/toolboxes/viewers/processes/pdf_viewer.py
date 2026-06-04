
from brainvisa.processes import Signature, ReadDiskItem
import subprocess

userLevel = 0
roles = ('viewer', )


signature = Signature(
    'document', ReadDiskItem('PDF file', 'PDF file'),
)


def execution(self, context):

    class KillablePopen:
        def __init__(self, popen):
            self.popen = popen

        def __del__(self):
            self.popen.terminate()
            self.popen.wait(5)
            self.popen.kill()
            self.popen.communicate()
            self.popen.wait()

    result = []
    cmd = ['bv_pdf_viewer', self.document.fullPath()]
    result.append(KillablePopen(subprocess.Popen(cmd)))
    return result
