import unittest
import doctest
import os
import tempfile
import shutil
import sys

# set en empty temporary user dir
# BRAINVISA_USER_DIR shoult be set before neuroConfig is imported
homedir = tempfile.mkdtemp(prefix='bv_home')
os.environ['BRAINVISA_USER_DIR'] = homedir

try:
    import brainvisa.tests.test_core
    import brainvisa.tests.test_history
    import brainvisa.tests.test_registration

    import brainvisa.axon
    from brainvisa.configuration import neuroConfig
    from brainvisa.data import neuroHierarchy
    from brainvisa.processes import defaultContext

    def setup_doctest(test):
        brainvisa.axon.initializeProcesses()
        # set english language because doctest tests the output of commands which
        # can be different according to the selected language
        neuroConfig.language = "en"
        neuroConfig.__builtin__.__dict__['_t_'] \
            = neuroConfig.Translator(neuroConfig.language).translate
        # update share database
        db = list(neuroHierarchy.databases.iterDatabases())[0]
        db.clear(context=defaultContext())
        db.update(context=defaultContext())
        brainvisa.axon.cleanup()

    def teardown_doctest(test):
        pass

    def test_suite():
        suite = unittest.TestSuite()
        doctest_suite = unittest.TestSuite(doctest.DocFileSuite(
            "usecases.rst", setUp=setup_doctest,
            tearDown=teardown_doctest,
            optionflags=doctest.ELLIPSIS))
        suite.addTest(doctest_suite)
        suite.addTest(brainvisa.tests.test_core.test_suite())
        suite.addTest(brainvisa.tests.test_history.test_suite())
        suite.addTest(brainvisa.tests.test_registration.test_suite())
        return suite

    if __name__ == '__main__':
        # try the notebook version if it can be processed on this system
        from soma.test_utils import test_notebook as tnb
        try:
            if tnb.test_notebook(
                os.path.join(os.path.dirname(sys.argv[0]),
                             'usecases_nb.ipynb')):
                sys.exit(0)
            else:
                sys.exit(1)
        except Warning:
            unittest.main(defaultTest='test_suite')
finally:
    shutil.rmtree(homedir)
    del homedir

# WARNING: if this file is imported as a module, homedir will be removed,
# and later processing will issue errors
