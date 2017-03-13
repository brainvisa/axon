
from brainvisa.processes import *
from soma import aims
import numpy as np

name = 'Reduce Texture on ROIs'
userLevel = 1

signature = Signature(
    'input_texture', ReadDiskItem('Texture', 'Aims texture formats'),
    'roi_texture', ReadDiskItem('ROI Texture', 'Aims texture formats'),
    'output_reduced_data', WriteDiskItem('Numpy array', 'Numpy array')
)


def execution(self, context):
    intex = aims.read(self.input_texture.fullPath())
    roi = aims.read(self.roi_texture.fullPath())
    rois = np.unique(roi[0].arraydata())
    nt = len(intex)
    shape = (np.max(rois) + 1, nt)
    out_data = np.zeros(shape, dtype=intex[0].arraydata().dtype)
    for value in rois:
        index = value
        if value < 0:
            index = 0
        for t in range(nt):
            out_data[index, t] = np.average(
                intex[t].arraydata()[roi[0].arraydata() == value])
    if nt == 1:
        out_data = out_data.ravel()
    np.save(self.output_reduced_data.fullPath(), out_data)

