import unittest
import doctest
import os
import brainvisa.config
import brainvisa.tests.test_history
import brainvisa.tests.test_registration


def test_suite():
  suite =unittest.TestSuite()
#  sphinx_dir=os.path.join(os.path.dirname(__file__), ".." , "..", "..", "share", "doc", "axon-"+brainvisa.config.shortVersion, 'sphinx', '_sources')
#  doctest_suite = unittest.TestSuite(doctest.DocFileSuite(os.path.join(sphinx_dir, "usecases.txt"), module_relative=False, optionflags=doctest.ELLIPSIS))
#  suite.addTest(doctest_suite)
  suite.addTest(brainvisa.tests.test_history.test_suite())
  suite.addTest(brainvisa.tests.test_registration.test_suite())
  return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
