# -*- coding: utf-8 -*-
#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL license version 2 under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the
# terms of the CeCILL license version 2 as circulated by CEA, CNRS
# and INRIA at the following URL "http://www.cecill.info".
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license version 2 and that you accept its terms.
from brainvisa.processes import *
import brainvisa.tools.spm_run as spm_run
import brainvisa.tools.spm_registration as spm_registration
from brainvisa.tools.spm_utils import moveSpmOutFiles, removeNan, merge_mat_files
from subprocess import check_call
import glob
import shutil

#------------------------------------------------------------------------------
configuration = Application().configuration

#------------------------------------------------------------------------------
def validation():
  return spm_run.validation(configuration)

#------------------------------------------------------------------------------
userLevel = 0
name = 'Mutiple coregister (using SPM)'

#------------------------------------------------------------------------------
signature = Signature(
    'sources', ListOf(ReadDiskItem('4D Volume', 'NIFTI-1 image')),
    'reference', ReadDiskItem('4D Volume', 'NIFTI-1 image'),
    'sources_warped', ListOf(WriteDiskItem('4D Volume', 'NIFTI-1 image')),
    'cost_fun', Choice(('Mutual Information', """'mi'"""),
                       ('Normalized Mutual Information', """'nmi'"""), ('Entropy Correlation Coefficient', """'ecc'"""),
                       ('Normalised Cross Correlation', """'ncc'""")),
    'sep', String(),
    'tol', String(),
    'fwhm', String(),
    'interp', Choice(('Nearest neighbour', """0"""),
                     ('Trilinear', """1"""),
                     ('2nd Degree B-spline', """2"""),
                     ('3rd Degree B-spline', """3"""),
                     ('4th Degree B-spline', """4"""),
                     ('5th Degree B-spline', """5"""),
                     ('6thd Degree B-spline', """6"""),
                     ('7th Degree B-spline', """7""")),
    'wrap', Choice(('No wrap', """[0 0 0]"""),
                   ('Wrap X', """[1 0 0]"""),
                   ('Wrap Y', """[0 1 0]"""),
                   ('Wrap X & Y', """[1 1 0]"""),
                   ('Wrap Z', """[0 0 1]"""),
                   ('Wrap X & Z', """[1 0 1]"""),
                   ('Wrap Y & Z', """[0 1 1]"""),
                   ('Wrap X, Y, Z', """[1 1 1]""")),
    'mask', Choice(('Mask images', """1"""),
                   ('Dont maks images', """0""")),
    'reset_inputs', Boolean())

#------------------------------------------------------------------------------
def initialization(self):
    spm_registration.ititializeCoregisterParameters_withSPM8DefaultValues(self) 
#    self.addLink('sources_warped', 'sources', self.update_spmSourceWarped)
    self.addLink('sources_warped', 'sources')
    self.signature['cost_fun'].userLevel = 1
    self.signature['sep'].userLevel = 1
    self.signature['tol'].userLevel = 1
    self.signature['fwhm'].userLevel = 1
    self.signature['interp'].userLevel = 1
    self.signature['wrap'].userLevel = 1
    self.signature['mask'].userLevel = 1
  
#------------------------------------------------------------------------------
def execution(self, context):  
    if self.reset_inputs:
        inputs = self.sources + [self.reference]
        for input in inputs:
            if input:
                self._resetInternalImageTransformation(input, context)

    self._removeExistingFiles()
    batch = []
    for source in self.sources:
        coregMatFile = context.temporary('Matlab script')
        spm_registration.writeCoregisteredMatFile(context,
                                                  source.fullPath(),
                                                  self.reference.fullPath(),
                                                  coregMatFile.fullPath(),
                                                  othersPath=[],
                                                  cost_fun="""'nmi'""", sep='[4 2]',
                                                  tol='[0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001]', 
                                                  fwhm='[7 7]',
                                                  interp=self.interp,
                                                  wrap='[0 0 0]', mask=0, 
                                                  prefix="""'r'""")
        batch.append(coregMatFile)
    completeMatFile = context.temporary('Matlab script')
    merge_mat_files(completeMatFile.fullPath(), *[b.fullPath() for b in batch])
    spm_run.run(context, configuration, completeMatFile.fullPath())
    
    for i in xrange(len(self.sources)):
        self._renameFile(self._addPrefix(self.sources[i].fullPath(), 'r'),
                         self.sources_warped[i].fullPath())
        self._copyMinfData(self.sources_warped[i].fullPath(),
                           self.sources[i].fullPath())

def _resetInternalImageTransformation(self, image, context):
    resetProcess = getProcessInstance("Reset internal image transformation")
    signature = resetProcess.signature
    signature['input_image'] = ReadDiskItem(image.type, 'NIFTI-1 image')
    signature['output_image'] = WriteDiskItem(image.type, 'NIFTI-1 image')
    resetProcess.changeSignature(signature)
    resetProcess.input_image = image
    resetProcess.output_image = image
    resetProcess.origin = "Center of the image"
    context.runProcess(resetProcess)

def _addPrefix(self, path, prefix):
    split = os.path.split(path)
    return os.path.join(split[0], prefix+split[1])

def _renameFile(self, currentFile, newFile):
    currentPath, ext = os.path.splitext(currentFile)
    newPath = os.path.splitext(newFile)[0]
    for f in glob.glob(currentPath + "*"):
        currentExt = os.path.splitext(f)[1]
        shutil.move(f, newPath + currentExt)

def _copyMinfData(self, newImage, refImage):
    aimsNewImage = aims.read(newImage)
    aimsRefImage = aims.read(refImage)
#    headerTags = ('modality')
    headerTags = ['modality']
    for tag in headerTags:
        try:
            aimsNewImage.header()[tag] = aimsRefImage.header()[tag]
        except:
            continue

    aims.write(aimsNewImage, newImage)

def _removeExistingFiles(self):
    for item in self.sources_warped:
        path = item.fullPath()
        for file in glob.glob(path + "*"):
            os.remove(file)
  