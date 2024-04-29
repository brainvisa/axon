include('base')
include('anatomy')


def assemblynet_space(space):
    return (
        f"{space}_lobes_<subject>", SetType("Brain Lobes"),
        f"{space}_macrostructures_<subject>", SetType("Split Brain Mask"),
        f"{space}_mask_<subject>", SetType("Intracranial mask"),
        f"{space}_structures_<subject>", SetType("Brain Structures"),
        f"{space}_t1_<subject>", SetType("T1 MRI Denoised and Bias Corrected"),
        f"{space}_tissues_<subject>", SetType("Intracranial labels"),
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
    "assemblyNet",
    SetWeakAttr("modality", "assemblyNet"),
    SetContent(
        "{acquisition}",
        SetType("Acquisition"),
        SetDefaultAttributeValue("acquisition", default_acquisition),
        SetContent(
            "mni",
            SetWeakAttr("space", "mni"),
            SetContent(
                # *(("<subject>_affine_transformation", SetType("Transformation"), SetWeakAttr("space", "mni")) + assemblynet_space("mni")),
                *(("matrix_affine_native_to_mni_<subject>", SetType("Transformation"), SetWeakAttr("space", "mni")) + assemblynet_space("mni")),
            ),
            "native",
            SetWeakAttr("space", "native"),
            SetContent(
                *assemblynet_space("native")
            ),
            "report_<subject>",
            SetType("Analysis Report"),
            "metadata_<subject>",
            SetType('Metadata Execution')
        ),
    ),
)

insert('{center}/{subject}',
    'vol2Brain', SetWeakAttr('modality', 'vol2Brain'), SetContent(
        '{acquisition}', SetType('Acquisition'),
        SetDefaultAttributeValue('acquisition', default_acquisition), SetContent(
            'matrix_affine_native_to_mni_<subject>', SetType('Transformation'),
            'mni_t1_<subject>', SetType('T1 MRI Denoised and Bias Corrected'), SetWeakAttr('space', 'mni'),
            'mni_mask_<subject>', SetType('Intracranial mask'), SetWeakAttr('space', 'mni'),
            'mni_tissues_<subject>', SetType('Intracranial labels'), SetWeakAttr('space', 'mni'),
            'mni_macrostructures_<subject>', SetType('Split Brain Mask'), SetWeakAttr('space', 'mni'),
            'mni_lobes_<subject>', SetType('Brain Lobes'), SetWeakAttr('space', 'mni'),
            'mni_structures_<subject>', SetType('Subcortical labels'), SetWeakAttr('space', 'mni'),
            'mni_thickness_<subject>', SetType('Cortical Thickness map'), SetWeakAttr('space', 'mni'),
            'native_t1_<subject>', SetType('T1 MRI Denoised and Bias Corrected'), SetWeakAttr('space', 'native'),
            'native_mask_<subject>', SetType('Intracranial mask'), SetWeakAttr('space', 'native'),
            'native_tissues_<subject>', SetType('Intracranial labels'), SetWeakAttr('space', 'native'),
            'native_macrostructures_<subject>', SetType('Split Brain Mask'), SetWeakAttr('space', 'native'),
            'native_lobes_<subject>', SetType('Brain Lobes'), SetWeakAttr('space', 'native'),
            'native_structures_<subject>', SetType('Subcortical labels'), SetWeakAttr('space', 'native'),
            'native_thickness_<subject>', SetType('Cortical Thickness map'), SetWeakAttr('space', 'native'),
            'report_<subject>', SetType('Analysis Report'),
            'readme_<subject>', SetType('Text file'),
        ),
    ),
)