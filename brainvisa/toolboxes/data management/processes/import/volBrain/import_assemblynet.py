import json
from pathlib import Path
import shutil
import yaml
import zipfile

from brainvisa.processes import Signature, ReadDiskItem, WriteDiskItem, String

name = "Import AssemblyNet results"
userLevel = 0

inputs = "Inputs"
outputs_native = "Outputs in native space"
outputs_mni = "Outputs in MNI space"
report = "VolBrain Reports"

default_format = ["gz compressed NIFTI-1 image", "NIFTI-1 image"]
modality = "assemblyNet"

signature = Signature(
    "assemblynet_zip", ReadDiskItem("Any Type", "ZIP file", section=inputs),
    "t1mri", ReadDiskItem("Raw T1 MRI", default_format, section=inputs),
    "subject", ReadDiskItem("Subject", "Directory", section=inputs),
    "acquisition", String(section=inputs),
    "output_folder", WriteDiskItem("Acquisition", "Directory", requiredAttributes={"modality": modality}, section=inputs),

    # Output reports
    "report_csv", WriteDiskItem("Analysis Report", "CSV file", requiredAttributes={"modality": modality}, section=report),
    "report_pdf", WriteDiskItem("Analysis Report", "PDF file", requiredAttributes={"modality": modality}, section=report),
    "metadata", WriteDiskItem("Metadata Execution", "JSON file", requiredAttributes={"modality": modality}, section=report),

    # MNI outputs
    "transformation_to_mni", WriteDiskItem(
        "Transformation", "Text file", section=outputs_mni,
        requiredAttributes={"space": "mni", "modality": modality}
    ),
    "mni_lobes", WriteDiskItem(
        "Brain Lobes", default_format, section=outputs_mni,
        requiredAttributes={"modality": modality, "space": "mni"}
    ),
    "mni_macrostructures", WriteDiskItem(
        "Split Brain Mask", default_format, section=outputs_mni,
        requiredAttributes={"space": "mni", "modality": modality}
    ),
    "mni_mask", WriteDiskItem(
        "Intracranial mask", default_format, section=outputs_mni,
        requiredAttributes={"space": "mni", "modality": modality}
    ),
    "mni_structures", WriteDiskItem(
        "Brain Structures", default_format, section=outputs_mni,
        requiredAttributes={"space": "mni", "modality": modality}
    ),
    "mni_t1", WriteDiskItem(
        "T1 MRI Denoised and Bias Corrected", default_format, section=outputs_mni,
        requiredAttributes={"space": "mni", "modality": modality}
    ),
    "mni_tissues", WriteDiskItem(
        "Intracranial labels", default_format, section=outputs_mni,
        requiredAttributes={"space": "mni", "modality": modality}
    ),

    # native outputs
    "native_lobes", WriteDiskItem(
        "Brain Lobes", default_format, section=outputs_native,
        requiredAttributes={"space": "native", "modality": modality}
    ),
    "native_macrostructures", WriteDiskItem(
        "Split Brain Mask", default_format, section=outputs_native,
        requiredAttributes={"space": "native", "modality": modality}
    ),
    "native_mask", WriteDiskItem(
        "Intracranial mask", default_format, section=outputs_native,
        requiredAttributes={"space": "native", "modality": modality}
    ),
    "native_structures", WriteDiskItem(
        "Brain Structures", default_format, section=outputs_native,
        requiredAttributes={"space": "native", "modality": modality}
    ),
    "native_tissues", WriteDiskItem(
        "Intracranial labels", default_format, section=outputs_native,
        requiredAttributes={"space": "native", "modality": modality}
    ),
)


def link_outputs(self, *proc):
    if self.subject and self.acquisition:
        d = {
            "_database": self.subject.get("_database"),
            "_ontology": self.subject.get("_ontology"),
            "center": self.subject.get("center"),
            "subject": self.subject.get("subject"),
            "acquisition": self.acquisition,
        }
        return self.signature["output_folder"].findValue(d)


def update_acquisition(self, t1mri):
    if t1mri:
        return t1mri.get('acquisition')


def extract_zip(self, context, zip_path):
    if zip_path:
        dir_mni = context.temporary("Directory")
        with zipfile.ZipFile(zip_path.fullPath(), "r") as zip_file:
            zip_file.extractall(dir_mni.fullPath())
        return dir_mni


def initialization(self):
    self.setOptional("t1mri")

    assemblynet_output_parameters = [p for p in self.signature if (p.startswith("mni") or p.startswith("native") or p.startswith("report"))]
    assemblynet_output_parameters += ["transformation_to_mni", "metadata"]
    for param in assemblynet_output_parameters:
        self.addLink(param, "output_folder")
    self.addLink("output_folder", ("subject", "acquisition"), self.link_outputs)
    self.addLink("subject", "t1mri")
    self.addLink("acquisition", "t1mri", self.update_acquisition)


def execution(self, context):
    dir_zip = self.extract_zip(context, self.assemblynet_zip)
    print(dir_zip)
    files_list = Path(dir_zip.fullPath()).glob("*.nii.gz")
    for f in files_list:
        file_type = f.name.split("_job")[0]

        command_list = ["AimsFileConvert", "-i", f, "-o", self.__dict__[file_type]]
        if file_type != "mni_t1":
            command_list += ["-t", "S16"]

        context.system(*command_list)

    other_files = [
        ("matrix_affine*", self.transformation_to_mni),
        ("report_job*csv", self.report_csv),
        ("report_job*pdf", self.report_pdf)
    ]

    for pattern, output_file in other_files:
        input_file = list(Path(dir_zip.fullPath()).glob(pattern))[0]
        shutil.copy(input_file, output_file.fullPath())

    metadata_input = list(Path(dir_zip.fullPath()).glob('metadata_job*'))[0]
    with open(metadata_input, 'r') as yaml_file, open(self.metadata.fullPath(), 'w') as json_file:
        data = yaml.safe_load(yaml_file)
        json.dump(data, json_file, indent=4)
