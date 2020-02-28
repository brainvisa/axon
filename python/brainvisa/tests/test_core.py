from __future__ import absolute_import
import unittest

import brainvisa.axon
from brainvisa.processes import getDiskItemType, getFormat, getConversionInfo


class TestCore(unittest.TestCase):

    def setUp(self):
        brainvisa.axon.initializeProcesses()

    def test_types(self):
        # Check inheritance levels
        # Must be 0
        self.assertEqual(
            getDiskItemType('Any Type').inheritanceLevels('Any Type'), 0)
        # Must be 2
        self.assertEqual(
            getDiskItemType('3D Volume').inheritanceLevels('Any Type'), 2)
        # Must be 4
        self.assertEqual(
            getDiskItemType('Brain Mask').inheritanceLevels('Any Type'), 4)
        # Must be 2
        self.assertEqual(
            getDiskItemType('Brain Mask').inheritanceLevels('3D Volume'), 2)
        # Must be -1
        self.assertEqual(
            getDiskItemType('3D Volume').inheritanceLevels('Brain Mask'), -1)

        # Check conversion distance for the same type
        ts = getDiskItemType('3D Volume')
        fs = getFormat('GIS Image')
        td = ts
        fd = fs
        ci = getConversionInfo((ts, fs), (td, fd))
        self.assertEqual(ci.distance(useInheritanceOnly=1), (0, 0, 0))
        self.assertEqual(ci.distance(useInheritanceOnly=0), (0, 0, 0))

        # Check conversion distance for inherited type
        # and same format
        ts = getDiskItemType('Brain Mask')
        ci = getConversionInfo((ts, fs), (td, fd))
        self.assertEqual(ci.distance(useInheritanceOnly=1), (0, 2, 0))
        self.assertEqual(ci.distance(useInheritanceOnly=0), (0, 2, 0))

        # Check conversion distance between not inherited types
        # but convertible formats
        ts = getDiskItemType('3D Volume')
        td = getDiskItemType('Brain Mask')
        ci = getConversionInfo((ts, fs), (td, fd))
        self.assertEqual(ci.distance(useInheritanceOnly=1), None)
        self.assertEqual(ci.distance(useInheritanceOnly=0), (1, 1, 0))

        # Check conversion distance between formats
        ts = getDiskItemType('3D Volume')
        td = ts
        fd = getFormat('NIFTI-1 Image')
        ci = getConversionInfo((ts, fs), (td, fd))
        self.assertEqual(ci.distance(useInheritanceOnly=1), None)
        self.assertEqual(ci.distance(useInheritanceOnly=0), (1, 0, 1))

        # Check conversion distance between inherited types
        # and convertible formats
        ts = getDiskItemType('Brain Mask')
        td = getDiskItemType('3D Volume')
        fd = getFormat('NIFTI-1 Image')
        ci = getConversionInfo((ts, fs), (td, fd))
        self.assertEqual(ci.distance(useInheritanceOnly=1), None)
        self.assertEqual(ci.distance(useInheritanceOnly=0), (1, 1, 1))

        # Check conversion distance between incompatible types
        # and incompatible formats
        # Must be None None
        ts = getDiskItemType('ROI Graph')
        fs = format('ROI Graph')
        td = getDiskItemType('3D Volume')
        fd = getFormat('NIFTI-1 Image')
        ci = getConversionInfo((ts, fs), (td, fd))
        self.assertEqual(ci.distance(useInheritanceOnly=1), None)
        self.assertEqual(ci.distance(useInheritanceOnly=0), None)
        # (because I think that no converter between 4D Volume and Graph is
        # registered, but it is necessary to check)

        ts = getDiskItemType('3D Volume')
        fs = getFormat('NIFTI-1 Image')
        td = getDiskItemType('ROI Graph')
        fd = format('ROI Graph')
        ci = getConversionInfo((ts, fs), (td, fd))
        self.assertEqual(ci.distance(useInheritanceOnly=1), None)
        self.assertEqual(ci.distance(useInheritanceOnly=0), None)

    def tearDown(self):
        brainvisa.axon.cleanup()


def test_suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestCore)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
