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

content = (
    "<filename>_TO_talairach", SetType('Transformation matrix'),
  'talairach_TO_<filename>', SetType('Transformation matrix'),
  "<filename>_t1", SetType('Raw T1 MRI'),
  "<filename>_t2", SetType('T2 MRI'),
  "normalized_<filename>", SetType(
      'Raw T1 MRI'), SetWeakAttr('normalized', 'yes'),

  "unflip_<filename>", SetType(
      'Display BIC drawing'), SetWeakAttr('side', 'both'),
  "FCMunflip_<filename>", SetType(
      'Anatomist BIC drawing'), SetWeakAttr('side', 'both'),

  '<filename>', SetType('MPEG film'),
  '<filename>', SetType('BrainVISA/Anatomist animation'),
  '<filename>', SetType('2D Image'),
)

hierarchy = (
    SetContent(*content),
)
