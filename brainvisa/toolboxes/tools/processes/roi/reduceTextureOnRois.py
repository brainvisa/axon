
from brainvisa.processes import *
from soma import aims
import numpy as np

name = 'Reduce Texture on ROIs'
userLevel = 1


def mesh_type():
    if 'White Mesh' in [x.name for x in getAllDiskItemTypes()]:
        return 'White Mesh'
    return 'Mesh'


signature = Signature(
    'input_texture', ReadDiskItem('Texture', 'Aims texture formats'),
    'roi_texture', ReadDiskItem('ROI Texture', 'Aims texture formats'),
    'mesh', ReadDiskItem(mesh_type(), 'aims mesh formats'),
    'output_reduced_data', WriteDiskItem('Numpy array', 'Numpy array')
)


def initialization(self):
    self.linkParameters('roi_texture', 'input_texture')
    self.linkParameters('mesh', 'roi_texture')
    self.setOptional('mesh')


def execution(self, context):
    intex = aims.read(self.input_texture.fullPath())
    roi = aims.read(self.roi_texture.fullPath())
    aroi = roi[0].arraydata()

    if self.mesh is not None:
        mesh = aims.read(self.mesh.fullPath())
        vert = mesh.vertex()
        poly = np.asarray(mesh.polygon())
        abl = [vert[p[1]] - vert[p[0]] for p in poly]
        acl = [vert[p[2]] - vert[p[0]] for p in poly]
        # polygons areas
        parea = np.sqrt(np.asarray(
            [ab.norm2() * ac.norm2() - np.square(ab.dot(ac))
             for ab, ac in zip(abl, acl)])) * 0.5
        context.write('area:', np.sum(parea))
        # assign areas to vertices
        weights = np.zeros((intex[0].arraydata().shape[0], ))
        for i, p in enumerate(poly):
            weights[p[0]] += parea[i]
            weights[p[1]] += parea[i]
            weights[p[2]] += parea[i]
        context.write('v area:', np.sum(weights) / 3)
    else:
        context.warning('mesh is not provided: averaging without weighting by '
                        'vertices regions areas')
        weights = np.ones((intex[0].arraydata().shape[0], ))

    rois = np.unique(aroi)
    nt = len(intex)
    shape = (np.max(rois) + 1, nt)
    out_data = np.zeros(shape, dtype=intex[0].arraydata().dtype)
    for value in rois:
        index = value
        if value < 0:
            index = 0
        for t in range(nt):
            out_data[index, t] = np.average(
                intex[t].arraydata()[aroi == value],
                weights=weights[aroi == value])
    if nt == 1:
        out_data = out_data.ravel()
    np.save(self.output_reduced_data.fullPath(), out_data)

