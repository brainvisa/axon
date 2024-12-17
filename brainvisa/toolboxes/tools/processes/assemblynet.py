import shutil
from pathlib import Path

from brainvisa.processes import Signature, ReadDiskItem, WriteDiskItem
from brainvisa.processes import String, Float, Choice, Boolean
from brainvisa.data.neuroHierarchy import databases

userLevel = 1
name = 'Run AssemblyNet'

assemblynet_options = 'AssemblyNet options'
assemblynet_outputs = 'AssemblyNet outputs'

default_format = ["gz compressed NIFTI-1 image", "NIFTI-1 image"]

signature = Signature(
    "assemblynet_image", String(), #TODO readDiskItem AnyType
    "t1mri", ReadDiskItem("Raw T1 MRI", ["gz compressed NIFTI-1 image", "NIFTI-1 image"]),
    "output_folder", WriteDiskItem("Acquisition", "Directory", requiredAttributes={"modality": "assemblyNet"}),

    "age", Float(section=assemblynet_options),
    "sex", Choice(None, "Male", "Female", section=assemblynet_options),
    "pdf_report", Boolean(section=assemblynet_options),

    "transformation_to_mni", WriteDiskItem("Transformation", "Text file", section=assemblynet_outputs,
                                           requiredAttributes={"modality": "assemblyNet"}),
    "mni_lobes", WriteDiskItem("Brain Lobes", default_format, section=assemblynet_outputs,
                               requiredAttributes={"space": "mni", "modality": "assemblyNet"}),
    "mni_macrostructures", WriteDiskItem("Split Brain Mask", default_format, section=assemblynet_outputs,
                                         requiredAttributes={"space": "mni", "modality": "assemblyNet"}),
    "mni_mask", WriteDiskItem("Intracranial mask", default_format, section=assemblynet_outputs,
                              requiredAttributes={"space": "mni", "modality": "assemblyNet"}),
    "mni_structures", WriteDiskItem("Brain Structures", default_format, section=assemblynet_outputs,
                                    requiredAttributes={"space": "mni", "modality": "assemblyNet"}),
    "mni_t1", WriteDiskItem("T1 MRI Denoised and Bias Corrected", default_format, section=assemblynet_outputs,
                            requiredAttributes={"space": "mni", "modality": "assemblyNet"}),
    "mni_tissues", WriteDiskItem("Intracranial labels", default_format, section=assemblynet_outputs,
                                 requiredAttributes={"space": "mni", "modality": "assemblyNet"}),
    "native_lobes", WriteDiskItem("Brain Lobes", default_format, section=assemblynet_outputs,
                                  requiredAttributes={"space": "native", "modality": "assemblyNet"}),
    "native_macrostructures", WriteDiskItem("Split Brain Mask", default_format, section=assemblynet_outputs,
                                            requiredAttributes={"space": "native", "modality": "assemblyNet"}),
    "native_mask", WriteDiskItem("Intracranial mask", default_format, section=assemblynet_outputs,
                                 requiredAttributes={"space": "native", "modality": "assemblyNet"}),
    "native_structures", WriteDiskItem("Brain Structures", default_format, section=assemblynet_outputs,
                                       requiredAttributes={"space": "native", "modality": "assemblyNet"}),
    "native_t1", WriteDiskItem("T1 MRI Denoised and Bias Corrected", default_format, section=assemblynet_outputs,
                               requiredAttributes={"space": "native", "modality": "assemblyNet"}),
    "native_tissues", WriteDiskItem("Intracranial labels", default_format, section=assemblynet_outputs,
                                    requiredAttributes={"space": "native", "modality": "assemblyNet"}),
    "report_csv", WriteDiskItem("Analysis Report", "CSV file", section=assemblynet_outputs,
                                requiredAttributes={"modality": "assemblyNet"}),
    "report_pdf", WriteDiskItem("Analysis Report", "CSV file", section=assemblynet_outputs,
                                requiredAttributes={"modality": "assemblyNet"})
)


def validation():
    if not shutil.which('apptainer'):
        raise OSError('Apptainer is not on the environment')


def initialization(self):
    self.pdf_report = True
    self.setOptional('age', 'sex')

    assemblynet_output_parameters = [p for p in self.signature if (p.startswith('mni') or p.startswith('native'))]
    assemblynet_output_parameters += ["transformation_to_mni", "report"]
    self.setUserLevel(1, *assemblynet_output_parameters)
    for param in assemblynet_output_parameters:
        self.addLink(param, "output_folder")

    self.addLink("output_folder", "t1mri")
    # self.addLink("output_folder", "t1mri", self._update_output_folder)


def _update_output_folder(self, t1mri):
    attr = {
        'acquisition': t1mri.get('acquisition'),
        'subject': t1mri.get('subject'),
    }
    print(f'attr, {attr}')
    return self.signature['output_folder'].findValue(attr)


def execution(self, context):
    output_folder = Path(self.output_folder.fullPath())
    output_folder.mkdir(exist_ok=True)

    # Run AssemblyNet
    context.runProcess(
        "assemblynet_generic",
        assemblynet_image=self.assemblynet_image,
        t1mri=self.t1mri,
        output_folder=self.output_folder.fullPath(),
        age=self.age,
        sex=self.sex,
        pdf_report=self.pdf_report
    )

    for file_path in output_folder.iterdir():
        if file_path.is_dir():
            continue
        # if file_path.name.startswith("mni") or file_path.name.startswith("matrix"):
        if file_path.name.startswith("mni") or file_path.name.startswith("native"):
            signature_name = '_'.join(file_path.name.split('_')[:2])
            output_file = getattr(self, signature_name).fullPath()
            if not Path(output_file).exists():
                file_path.rename(output_file)
        elif file_path.name.startswith("matrix_affine"):
            output_file = self.tranformation_to_mni.fullPath()
            if not Path(output_file).exists():
                file_path.rename(output_file)
        elif file_path.name.startswith("report"):
            output_file = self.report.fullPath()
            if not Path(output_file).exists():
                file_path.rename(output_file)

    # Update brainvisa database to take into account results
    db = databases.database(self.output_folder.get('_database'))
    db.update(directoriesToScan=[self.output_folder.fullPath()])
