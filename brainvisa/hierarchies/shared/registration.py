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

include('base')

insert('',
       'registration', SetContent(
           '*', SetType('Referential'),
       ),
)

insert('',
       'transformation', SetContent(
           '*', SetType('Transformation matrix'),
       ),
)

insert('hemitemplate',
       'RawT1-Template_TO_Talairach-ACPC', SetType(
           "Template Pole To Talairach Tranformation"),
)

insert('',
       'anatomical_templates', SetContent(
           'MNI152_T1_1mm', SetType('anatomical Template'),
           SetWeakAttr('normalized', 'yes', 'skull_stripped', 'no',
                       'Size', '1 mm', 'referential', '49e6b349-b115-211a-c8b9-20d0ece9846d',
                       ),
           'MNI152_T1_2mm', SetType('anatomical Template'),
           SetWeakAttr('normalized', 'yes', 'skull_stripped', 'no', 'Size',
                       '2 mm', 'referential', '19bfee8e-51b1-4d9e-8721-990b9f88b12f',
                       ),
           'MNI152_T1_1mm_brain', SetType('anatomical Template'), SetWeakAttr(
               'Size', '1 mm'), SetWeakAttr('skull_stripped', 'yes'),
           'MNI152_T1_2mm_brain', SetType('anatomical Template'), SetWeakAttr(
               'Size', '2 mm'), SetWeakAttr('skull_stripped', 'yes'),
           'MNI152_T1_1mm_brain_mask', SetType(
               'anatomical Mask Template'), SetWeakAttr('Size', '1 mm'),
           'MNI152_T1_2mm_brain_mask', SetType(
               'anatomical Mask Template'), SetWeakAttr('Size', '2 mm'),
           'MNI152_T1_3mm_brain_mask', SetType(
               'anatomical Mask Template'), SetWeakAttr('Size', '3 mm'),
           'mni_icbm152_nlin_asym_09c', SetType('anatomical Template'),
            SetWeakAttr('Size', '1 mm', 'normalized', 'yes',
                        'skull_stripped', 'no',
                        'referential', '84b1989b-eb68-8665-0049-8feaf3c22679'),
            SetPriority(-1)
       )
)
