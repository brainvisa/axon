# -*- coding: utf-8 -*-
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

from __future__ import absolute_import, division, print_function

import os
import shutil
import tempfile
import sys

from six.moves import input


temp_test_dir = None

def setUpModule_axon(init_hooks=[]):
    """Spawn an isolated Axon instance for running tests.

    This function should be called from the setUpModule function of each test
    module. Make sure that you also call tearDownModule_axon from
    tearDownModule.

    You can pass a list of functions in init_hooks that will be called after
    brainvisa.axon has been imported, but *before*
    brainvisa.axon.initializeProcesses(). This can be used to set up
    configuration state that affects the import of processes (e.g. configuring
    external tools such as MATLAB and SPM).
    """
    global temp_test_dir

    try:
        # BRAINVISA_USER_DIR must be set before brainvisa.axon is imported. We
        # set it to an empty temporary directory to avoid inheriting and
        # interfering with the user config.
        temp_test_dir = tempfile.mkdtemp(prefix='axon_test_')
        os.mkdir(os.path.join(temp_test_dir, 'bv_home'))
        os.mkdir(os.path.join(temp_test_dir, 'tmp'))
        os.environ['BRAINVISA_USER_DIR'] = os.path.join(temp_test_dir,
                                                        'bv_home')
        os.environ['TMPDIR'] = os.path.join(temp_test_dir, 'tmp')
        tempfile.tempdir = os.path.join(temp_test_dir, 'tmp')
        print('Starting tests under {0}'.format(temp_test_dir))
        sys.stdout.flush()

        # import brainvisa.axon will fail if it finds arguments in sys.argv
        # that it does not recognize (such as arguments to unittest)
        argv_saved = sys.argv
        try:
            sys.argv = []
            import brainvisa.axon
        finally:
            sys.argv = argv_saved

        for hook in init_hooks:
            hook()

        brainvisa.axon.initializeProcesses()
        import brainvisa.processes

        # update shared database
        from brainvisa.data.neuroHierarchy import databases
        from brainvisa.processes import defaultContext
        for db in databases.iterDatabases():
            # The shared database must be updated during tests of a build tree,
            # but not in the case of a read-only installed BrainVISA.
            if db.fso.name == 'shared' and os.access(
                    db.directory, os.R_OK | os.W_OK | os.X_OK):
                db.clear(context=defaultContext())
                db.update(context=defaultContext())
    except BaseException:
        if temp_test_dir is not None:
            shutil.rmtree(temp_test_dir)
        try:
            brainvisa.axon.cleanup()
        except UnboundLocalError:
            pass  # brainvisa.axon has not been imported, nothing to clean up
        raise


def tearDownModule_axon():
    """Clean up the isolated Axon instance.

    This function should be called from the tearDownModule function of each
    test module.
    """
    import brainvisa
    if os.environ.get('AXON_TESTS_KEEP_TEMPORARY'):
        try:
            input('About to clean up the test environment: {0}. '
                  'Press ENTER to proceed.'.format(temp_test_dir))
        except EOFError:
            pass  # no stdin, proceed to cleanup
    brainvisa.axon.cleanup()
    shutil.rmtree(temp_test_dir)
