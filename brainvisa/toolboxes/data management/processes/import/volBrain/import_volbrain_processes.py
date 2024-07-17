import json
from pathlib import Path
import shutil
import yaml
import zipfile

from brainvisa.processes import Signature, ReadDiskItem, WriteDiskItem, String, Choice, Boolean

name = "Import volBrain processes results"
userLevel = 0

inputs = "Inputs"
outputs_native = "Outputs in native space"
outputs_mni = "Outputs in MNI space"
report = "VolBrain Reports"

default_format = ["gz compressed NIFTI-1 image", "NIFTI-1 image"]
modality = "assemblyNet"

signature = Signature(
    "volbrain_process", Choice('assemblyNet', 'vol2Brain'),
    "process_zip", ReadDiskItem("Any Type", "ZIP file", section=inputs),
    "check_subject_name_in_zipfile", Boolean(section=inputs),
    "t1mri", ReadDiskItem("Raw T1 MRI", default_format, section=inputs),
    "subject", ReadDiskItem("Subject", "Directory", section=inputs),
    "acquisition", String(section=inputs),
    "output_folder", WriteDiskItem("Acquisition", "Directory", requiredAttributes={"modality": "t1mri"}, section=inputs),

    # Output reports
    "report_csv", WriteDiskItem("Analysis Report", "CSV file", section=report),
    "report_pdf", WriteDiskItem("Analysis Report", "PDF file", section=report),
    "metadata", WriteDiskItem("Metadata Execution", "JSON file", section=report),

    # MNI outputs
    "transformation_to_mni", WriteDiskItem(
        "Transformation", "Text file", section=outputs_mni,
    ),
    "mni_lobes", WriteDiskItem(
        "Brain Lobes", default_format, section=outputs_mni,
        requiredAttributes={"space": "mni"}
    ),
    "mni_macrostructures", WriteDiskItem(
        "Split Brain Mask", default_format, section=outputs_mni,
        requiredAttributes={"space": "mni"}
    ),
    "mni_mask", WriteDiskItem(
        "Intracranial mask", default_format, section=outputs_mni,
        requiredAttributes={"space": "mni"}
    ),
    "mni_structures", WriteDiskItem(
        "Brain Structures", default_format, section=outputs_mni,
        requiredAttributes={"space": "mni"}
    ),
    "mni_t1", WriteDiskItem(
        "T1 MRI Denoised and Bias Corrected", default_format, section=outputs_mni,
        requiredAttributes={"space": "mni"}
    ),
    "mni_tissues", WriteDiskItem(
        "Intracranial labels", default_format, section=outputs_mni,
        requiredAttributes={"space": "mni"}
    ),
    "mni_thickness", WriteDiskItem(
        "Cortical Thickness map",default_format, section=outputs_mni,
        requiredAttributes={"space": "mni"},
    ),
    # native outputs
    "native_lobes", WriteDiskItem(
        "Brain Lobes", default_format, section=outputs_native,
        requiredAttributes={"space": "native"}
    ),
    "native_macrostructures", WriteDiskItem(
        "Split Brain Mask", default_format, section=outputs_native,
        requiredAttributes={"space": "native"}
    ),
    "native_mask", WriteDiskItem(
        "Intracranial mask", default_format, section=outputs_native,
        requiredAttributes={"space": "native"}
    ),
    "native_structures", WriteDiskItem(
        "Brain Structures", default_format, section=outputs_native,
        requiredAttributes={"space": "native"}
    ),
    "native_t1", WriteDiskItem(
        "T1 MRI Denoised and Bias Corrected", default_format, section=outputs_native,
        requiredAttributes={"space": "native"}
    ),
    "native_tissues", WriteDiskItem(
        "Intracranial labels", default_format, section=outputs_native,
        requiredAttributes={"space": "native"}
    ),
    "native_thickness", WriteDiskItem(
        "Cortical Thickness map", default_format, section=outputs_native,
        requiredAttributes={"space": "native"},
    ),
)

VOL2BRAIN_PARAMETERS = ["mni_thickness", "native_thickness"]
ASSEMBLYNET_PARAMETERS = ["metadata"]

def link_outputs(self, *proc):
    print('link_outputs')
    print(self.subject)
    print(self.acquisition)
    if self.subject and self.acquisition:
        print('IF')
        d = {
            "_database": self.subject.get("_database"),
            "_ontology": self.subject.get("_ontology"),
            "center": self.subject.get("center"),
            "subject": self.subject.get("subject"),
            "acquisition": self.acquisition,
        }
        print(d)
        return self.signature["output_folder"].findValue(d)


def extract_zip(self, context, zip_path):
    if zip_path:
        dir_zip = context.temporary("Directory")
        with zipfile.ZipFile(zip_path.fullPath(), "r") as zip_file:
            zip_file.extractall(dir_zip.fullPath())
        return dir_zip


def update_modality(self, volbrain_process):
    for p in self.assemblynet_output_parameters:
        self.signature[p].requiredAttributes.update({'modality': volbrain_process})

    match volbrain_process:
        case "assemblyNet":
            self.setEnable(*ASSEMBLYNET_PARAMETERS)
            self.setDisable(*VOL2BRAIN_PARAMETERS)
        case "vol2Brain":
            self.setEnable(*VOL2BRAIN_PARAMETERS)
            self.setDisable(*ASSEMBLYNET_PARAMETERS)

    self.changeSignature(self.signature)


def initialization(self):
    self.setOptional("t1mri")

    self.assemblynet_image_parameters = [p for p in self.signature if (p.startswith("mni") or p.startswith("native"))]
    self.assemblynet_output_parameters = self.assemblynet_image_parameters + ["report_csv", "report_pdf", "transformation_to_mni", "metadata"]
    for param in self.assemblynet_output_parameters:
        self.addLink(param, "output_folder")
    self.addLink("output_folder", ("subject", "acquisition"), self.link_outputs)
    self.addLink("subject", "t1mri")
    self.addLink("acquisition", "t1mri", lambda x: x.get("acquisition") if x else None)

    self.update_modality(self.volbrain_process)
    self.addLink(None, "volbrain_process", self.update_modality)


def execution(self, context):
    if self.check_subject_name_in_zipfile:
        p = self.process_zip.fullPath()
        if p and p.find(self.subject.get("subject")) < 0:
            context.write("The zip files path do not match with the subject's name, verify your file or disable the check.")
            return

    dir_zip = self.extract_zip(context, self.process_zip)

    # Convert NIfTI files
    files_list = Path(dir_zip.fullPath()).glob("*.nii.gz")
    for f in files_list:
        file_type = f.name.split("_job")[0]

        command_list = ["AimsFileConvert", "-i", f, "-o", self.__dict__[file_type]]
        if file_type != "mni_t1":
            command_list += ["-t", "S16"]

        context.system(*command_list)

    # Move other files
    other_files = [
        ("matrix_affine*", self.transformation_to_mni),
        ("report_job*csv", self.report_csv),
        ("report_job*pdf", self.report_pdf),
    ]

    for pattern, output_file in other_files:
        input_file = list(Path(dir_zip.fullPath()).glob(pattern))[0]
        shutil.copy(input_file, output_file.fullPath())

    if self.volbrain_process == "assemblyNet":
        metadata_input = list(Path(dir_zip.fullPath()).glob("metadata_job*"))[0]
        with open(metadata_input, "r") as yaml_file, open(self.metadata.fullPath(), "w") as json_file:
            data = yaml.safe_load(yaml_file)
            json.dump(data, json_file, indent=4)
