import unittest
import doctest
import os
import brainvisa.config


def test_suite():
  sphinx_dir=os.path.join(os.path.dirname(__file__), ".." , "..", "..", "share", "doc", "axon-"+brainvisa.config.shortVersion, 'sphinx', '_sources')
  return unittest.TestSuite(doctest.DocFileSuite(os.path.join(sphinx_dir, "usecases.txt"), module_relative=False, optionflags=doctest.ELLIPSIS))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
