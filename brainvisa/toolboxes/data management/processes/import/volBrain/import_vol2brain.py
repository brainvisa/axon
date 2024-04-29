import glob
import os
import shutil
import zipfile

from brainvisa.processes import Signature, ReadDiskItem, WriteDiskItem, String, Boolean

name = 'Import vol2Brain results'
userLevel = 0

inputs = 'Inputs'
outputs_native = 'Outputs in native space'
outputs_mni = 'Outputs in MNI space'
report = 'VolBrain Reports'


signature = Signature(
    # Inputs
    'volBrain_zip', ReadDiskItem(
        'Any Type',
        'ZIP file',
        section=inputs),
    #'volBrain_native_zip', ReadDiskItem(
    #    'Any Type',
    #    'ZIP file',
    #    section=inputs),
    'subject', ReadDiskItem(
        'Subject',
        'Directory',
        section=inputs),
    'acquisition', String(
        section=inputs),
    'check_subject_name_in_zipfile', Boolean(
        section=inputs),
    # Outputs reports
    'report_csv', WriteDiskItem(
        'Analysis Report',
        'CSV file',
        requiredAttributes={'modality': 'vol2Brain'},
        section=report),
    'report_pdf', WriteDiskItem(
        'Analysis Report',
        'PDF file',
        requiredAttributes={'modality': 'vol2Brain'},
        section=report),
    'readme', WriteDiskItem(
        'Text file',
        'PDF file',
        requiredAttributes={'modality': 'vol2Brain'},
        section=report),
    'matrix_affine_native_to_mni', WriteDiskItem(
        'Transformation',
        'Text file',
        requiredAttributes={'modality': 'vol2Brain'},
        section=outputs_mni),
    # MNI outputs
    'mni_structures', WriteDiskItem(
        'Subcortical labels',
        'gz compressed NIFTI-1 image',
        requiredAttributes={'modality': 'vol2Brain',
                            'space': 'mni'},
        section=outputs_mni),
    'mni_macrostructures', WriteDiskItem(
        'Split Brain Mask',
        'gz compressed NIFTI-1 image',
        requiredAttributes={'modality': 'vol2Brain',
                            'space': 'mni'},
        section=outputs_mni),
    'mni_tissues', WriteDiskItem(
        'Intracranial labels',
        'gz compressed NIFTI-1 image',
        requiredAttributes={'modality': 'vol2Brain',
                            'space': 'mni'},
        section=outputs_mni),
    'mni_mask', WriteDiskItem(
        'Intracranial mask',
        'gz compressed NIFTI-1 image',
        requiredAttributes={'modality': 'vol2Brain',
                            'space': 'mni'},
        section=outputs_mni),
    'mni_lobes', WriteDiskItem(
        'Brain Lobes',
        'gz compressed NIFTI-1 image',
        requiredAttributes={'modality': 'vol2Brain',
                            'space': 'mni'},
        section=outputs_mni),
    'mni_thickness', WriteDiskItem(
        'Cortical Thickness map',
        'gz compressed NIFTI-1 image',
        requiredAttributes={'modality': 'vol2Brain',
                            'space': 'mni'},
        section=outputs_mni),
    'mni_t1', WriteDiskItem(
        'T1 MRI Denoised and Bias Corrected',
        'gz compressed NIFTI-1 image',
        requiredAttributes={'modality': 'vol2Brain',
                            'space': 'mni'},
        section=outputs_mni),
    # Native outputs
    'native_structures', WriteDiskItem(
        'Subcortical labels',
        'gz compressed NIFTI-1 image',
        requiredAttributes={'modality': 'vol2Brain',
                            'space': 'native'},
        section=outputs_native),
    'native_macrostructures', WriteDiskItem(
        'Split Brain Mask',
        'gz compressed NIFTI-1 image',
        requiredAttributes={'modality': 'vol2Brain',
                            'space': 'native'},
        section=outputs_native),
    'native_tissues', WriteDiskItem(
        'Intracranial labels',
        'gz compressed NIFTI-1 image',
        requiredAttributes={'modality': 'vol2Brain',
                            'space': 'native'},
        section=outputs_native),
    'native_mask', WriteDiskItem(
        'Intracranial mask',
        'gz compressed NIFTI-1 image',
        requiredAttributes={'modality': 'vol2Brain',
                            'space': 'native'},
        section=outputs_native),
    'native_lobes', WriteDiskItem(
        'Brain Lobes',
        'gz compressed NIFTI-1 image',
        requiredAttributes={'modality': 'vol2Brain',
                            'space': 'native'},
        section=outputs_native),
    'native_thickness', WriteDiskItem(
        'Cortical Thickness map',
        'gz compressed NIFTI-1 image',
        requiredAttributes={'modality': 'vol2Brain',
                            'space': 'native'},
        section=outputs_native),
    'native_t1', WriteDiskItem(
        'T1 MRI Denoised and Bias Corrected',
        'gz compressed NIFTI-1 image',
        requiredAttributes={'modality': 'vol2Brain',
                            'space': 'native'},
        section=outputs_native),
)


def initialization(self):
    #def linkSubject(self, proc):
        #if self.volBrain_mni_zip is not None:
            #subject = os.path.basename(self.volBrain_mni_zip.fullPath()).split('.nii.gz')[0]
        #return subject
    
    #def linkNativeZip(self, proc):
        #if self.volBrain_mni_zip is not None:
            #directory = os.path.dirname(self.volBrain_mni_zip.fullPath())
            #basename = os.path.basename(self.volBrain_mni_zip.fullPath())
            #zip_native = os.path.join(directory,
            #                          'native_' + basename)
            #return zip_native
    
    def linkVolBrainOutput(self, proc):
        if self.subject and self.acquisition:
            d = {'_database': self.subject.get('_database'),
                 '_ontology': 'brainvisa-3.2.0',
                 'center': self.subject.get('center'),
                 'subject': self.subject.get('subject'),
                 'acquisition': self.acquisition}
            return self.signature['report_csv'].findValue(d)
    
    def linkLobesMNI(self, proc):
        if self.mni_structures:
            p = self.mni_structures.fullPath().replace('structures',
                                                       'lobes')
            return p
    
    def linkLobesNative(self, proc):
        if self.native_structures:
            p = self.native_structures.fullPath().replace('structures',
                                                          'lobes')
            return p
    
    def linkThicknessMNI(self, proc):
        if self.mni_structures:
            p = self.mni_structures.fullPath().replace('structures',
                                                       'thickness')
            return p
    
    def linkThicknessNative(self, proc):
        if self.native_structures:
            p = self.native_structures.fullPath().replace('structures',
                                                          'thickness')
            return p
    
    #self.linkParameters('subject', 'volBrain_mni_zip', linkSubject)
    #self.linkParameters('volBrain_native_zip', 'volBrain_mni_zip', linkNativeZip)
    
    self.linkParameters('report_csv', ('subject', 'acquisition'), linkVolBrainOutput)
    
    #self.linkParameters('report_csv', 'mni_lab')
    self.linkParameters('report_pdf', 'report_csv')
    self.linkParameters('readme', 'report_csv')
    
    self.linkParameters('matrix_affine_native_to_mni', 'report_csv')
    self.linkParameters('mni_structures', 'report_csv')
    self.linkParameters('mni_macrostructures', 'mni_structures')
    self.linkParameters('mni_mask', 'mni_structures')
    self.linkParameters('mni_tissues', 'mni_structures')
    self.linkParameters('mni_lobes', 'mni_structures',
                        linkLobesMNI)
    self.linkParameters('mni_thickness', 'mni_structures',
                        linkThicknessMNI)
    self.linkParameters('mni_t1', 'mni_structures')
    
    self.linkParameters('native_structures', 'mni_structures')
    self.linkParameters('native_macrostructures',
                        'native_structures')
    self.linkParameters('native_mask','native_structures')
    self.linkParameters('native_tissues','native_structures')
    self.linkParameters('native_lobes', 'native_structures',
                        linkLobesNative)
    self.linkParameters('native_thickness', 'native_structures',
                        linkThicknessNative)
    self.linkParameters('native_t1','native_structures')
    
    #self.signature['volBrain_mni_zip'].mandatory = False
    #self.signature['volBrain_native_zip'].mandatory = False
    

def execution(self, context):
    
    if self.check_subject_name_in_zipfile:
        p = self.volBrain_zip.fullPath()
        if p:
            if p.find(self.subject.get('subject')) < 0:
                context.write("The zip files path do not match with the subject's name, verify your file or disable the check.")
                return
    
    dir_mni = context.temporary('Directory')
    with zipfile.ZipFile(self.volBrain_zip.fullPath(), 'r') as zip_mni:
        zip_mni.extractall(dir_mni.fullPath())
    
    transfo = glob.glob(os.path.join(dir_mni.fullPath(), 'matrix_affine_native_to_mni_job*'))[0]
    shutil.copy(transfo, self.matrix_affine_native_to_mni.fullPath())

    shutil.copy(os.path.join(dir_mni.fullPath(), 'README.pdf'),
                self.readme.fullPath())
        
    reports = glob.glob(os.path.join(dir_mni.fullPath(), 'report_job*'))
    if 'csv' in reports[0]:
        shutil.copy(reports[0], self.report_csv.fullPath())
        shutil.copy(reports[1], self.report_pdf.fullPath())
    else:
        shutil.copy(reports[1], self.report_csv.fullPath())
        shutil.copy(reports[0], self.report_pdf.fullPath())
       
    files_list = glob.glob(os.path.join(dir_mni.fullPath(), 'mni*'))
    for f in files_list:
        p = os.path.basename(f).split('_')
        p_out = '_'.join(p[:2])
        command_list = ['AimsFileConvert',
                        '-i', f,
                        '-o', self.__dict__[p_out]]
        if p_out != 'mni_t1':
            command_list += ['-t', 'S16']
        #print(command_list)
        context.system(*command_list)
    
    files_list = glob.glob(os.path.join(dir_mni.fullPath(), 'native*'))
    for f in files_list:
        p = os.path.basename(f).split('_')
        p_out = '_'.join(p[:2])
        command_list = ['AimsFileConvert',
                        '-i', f,
                        '-o', self.__dict__[p_out]]
        if p_out != 'native_t1':
            command_list += ['-t', 'S16']
        #print(command_list)
        context.system(*command_list)
