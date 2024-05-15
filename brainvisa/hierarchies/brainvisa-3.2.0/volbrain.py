include('base')
include('anatomy')


def volbrain_processes_space(space):
    return (
        f"{space}_lobes_<subject>", SetType("Brain Lobes"), SetWeakAttr("space", space),
        f"{space}_macrostructures_<subject>", SetType("Split Brain Mask"), SetWeakAttr("space", space),
        f"{space}_mask_<subject>", SetType("Intracranial mask"), SetWeakAttr("space", space),
        f"{space}_structures_<subject>", SetType("Brain Structures"), SetWeakAttr("space", space),
        f"{space}_t1_<subject>", SetType("T1 MRI Denoised and Bias Corrected"), SetWeakAttr("space", space),
        f"{space}_tissues_<subject>", SetType("Intracranial labels"), SetWeakAttr("space", space),
    )


def volbrain_space(space):
    return (
        f'<subject>_{space}_crisp', SetType('Intracranial labels'),
        f'<subject>_{space}_hemi', SetType('Split Brain Mask'),
        f'<subject>_{space}_lab', SetType('Subcortical labels'),
        f'<subject>_{space}_mask', SetType('Intracranial mask'),
        f'<subject>_{space}_filtered', SetType('T1 MRI Denoised'),
        f'<subject>_{space}_normalised', SetType('T1 MRI Denoised and Bias Corrected'),
        f'<subject>_{space}_readme', SetType('Text file'),
    )

insert('{center}/{subject}',
    'volBrain', SetWeakAttr('modality', 'volBrain'), SetContent(
        '{acquisition}', SetType('Acquisition'),
        SetDefaultAttributeValue('acquisition', default_acquisition), SetContent(
            'native', SetWeakAttr('space', 'native'), SetContent(*volbrain_space('native')),
            'mni', SetWeakAttr('space', 'mni'), SetContent(*(
                volbrain_space('mni') + (
                    '<subject>_mni_wm', SetType('tissue probability map'),
                    SetWeakAttr('tissue_class', 'white'),
                    '<subject>_mni_gm', SetType('tissue probability map'),
                    SetWeakAttr('tissue_class', 'grey'),
                    '<subject>_mni_csf', SetType('tissue probability map'),
                    SetWeakAttr('tissue_class', 'csf'),
                    '<subject>_affine_transformation', SetType('Transformation'),
                )
            )),
            '<subject>_report', SetType('Analysis Report'),
        ),
    ),
    "assemblyNet", SetWeakAttr("modality", "assemblyNet"), SetContent(
        "{acquisition}",
        SetType("Acquisition"),
        SetDefaultAttributeValue("acquisition", default_acquisition),
        SetContent(
            *volbrain_processes_space("mni"),
            *volbrain_processes_space("native"),
            "matrix_affine_native_to_mni_<subject>", SetType("Transformation"),
            "report_<subject>", SetType("Analysis Report"),
            "metadata_<subject>", SetType('Metadata Execution'),
        ),
    ),
    "vol2Brain", SetWeakAttr("modality", "vol2Brain"), SetContent(
        "{acquisition}",
        SetType("Acquisition"),
        SetDefaultAttributeValue("acquisition", default_acquisition),
        SetContent(
            *volbrain_processes_space("mni"),
            *volbrain_processes_space("native"),
            "matrix_affine_native_to_mni_<subject>", SetType("Transformation"),
            "mni_thickness_<subject>", SetType("Cortical Thickness map"), SetWeakAttr("space", "mni"),
            "native_thickness_<subject>", SetType("Cortical Thickness map"), SetWeakAttr("space", "native"),
            "report_<subject>", SetType("Analysis Report"),
            "readme_<subject>", SetType("Text file"),
        ),
    ),
)
