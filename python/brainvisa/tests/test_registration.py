
from __future__ import print_function
from __future__ import absolute_import
import unittest
import tempfile
import os
import shutil

import brainvisa.axon
from brainvisa.configuration import neuroConfig
from brainvisa.data import neuroHierarchy
from brainvisa.processes import defaultContext
from brainvisa import registration
import six


class TestTransformationManager(unittest.TestCase):

    def create_uuid(self, uuid):
        if not isinstance(uuid, tuple):
            uuid = (uuid, )
        a, b, c, d, e = ((0, 0, 0, 0) + uuid)[-5:]
        result = ( '0' * 7 + str( a ) )[ -8: ] + '-' + \
            ( '0' * 3 + str( b ) )[ -4: ] + '-' + \
            ( '0' * 3 + str( c ) )[ -4: ] + '-' + \
            ( '0' * 3 + str( d ) )[ -4: ] + '-' + \
            ('0' * 11 + str(e))[-12:]
        return result

    def create_referential(self, registration_directory, label, referential_id):
        referential_uuid = self.create_uuid(referential_id)
        with open(
                os.path.join(registration_directory,
                             referential_uuid + '.referential'), 'w') \
                as referential:
            d = {'uuid': referential_uuid, 'name': label}
            print('attributes =', repr(d), file=referential)

    def create_transformation(self, registration_directory, transformation_id, source_id, destination_id):
        transformation_uuid = self.create_uuid(transformation_id)
        source_uuid = self.create_uuid(source_id)
        destination_uuid = self.create_uuid(destination_id)
        trm = open(
            os.path.join(registration_directory, transformation_uuid + '.trm'), 'w')
        print('0 0 0\n1 0 0\n0 1 0\n0 0 1', file=trm)
        trm.close()
        trm_minf = open(
            os.path.join(registration_directory, transformation_uuid + '.trm.minf'), 'w')
        d = {'uuid': transformation_uuid, 'source_referential':
             source_uuid, 'destination_referential': destination_uuid}
        print('attributes =', repr(d), file=trm_minf)
        trm_minf.close()

    def create_test_database(self):
        database_directory = os.path.join(
            self.test_database_directory, 'database')
        for database in neuroConfig.dataPath:
            if database.directory == database_directory:
                return neuroHierarchy.databases.database(database.directory)
        if not os.path.exists(database_directory):
            os.makedirs(database_directory)
        self.database_settings = neuroConfig.DatabaseSettings(
            database_directory)
        database = neuroHierarchy.SQLDatabase(
            self.database_settings.expert_settings.sqliteFileName,
                                               database_directory, 'brainvisa-3.2.0', context=defaultContext(), settings=self.database_settings)
        neuroHierarchy.databases.add(database)
        neuroConfig.dataPath.append(self.database_settings)
        return database

    def setUp(self):
        self.number_of_subjects = 5
        self.number_of_sulci = 30
        brainvisa.axon.initializeProcesses()
        tests_dir = os.getenv("BRAINVISA_TEST_RUN_DATA_DIR")
        if not tests_dir:
            tests_dir = tempfile.gettempdir()
        self.test_database_directory = os.path.join(
            tests_dir, "tmp_tests_brainvisa", "database_registration")
        # Create test databases
        self.database = self.create_test_database()
        registration_directory = os.path.join(
            self.database.directory, 'transformation_manager', 'registration')
        if os.path.exists(registration_directory):
            shutil.rmtree(registration_directory)
        os.makedirs(registration_directory)
        # Fill test database
        self.create_referential(
            registration_directory, 'Template for all subjects', 0)
        for s in six.moves.xrange(1, self.number_of_subjects + 1):
            self.create_referential(
                registration_directory, 'Subject ' + str(s), s)
            self.create_transformation(
                registration_directory, (1, 0, 0, 0, s), s, 0)
            for s2 in six.moves.xrange(s + 1, self.number_of_subjects + 1):
                self.create_transformation(
                    registration_directory, (1, 0, 0, s, s2), s, s2)
            for n in six.moves.xrange(1, self.number_of_sulci + 1):
                self.create_referential(
                    registration_directory, 'Sulci ' + str(n) + ' of subject ' + str(s), (s, n))
                self.create_transformation(
                    registration_directory, (1, 0, 1, s, n), s, (s, n))
        self.database.clear(context=defaultContext())
        self.database.update(context=defaultContext())

    def test_find_paths(self):
        """
        Tests the number of paths found between the referentials defined in the temporary database.
        """
        tr = registration.getTransformationManager()
        paths = list(tr.findPaths(self.create_uuid(1),
                                  self.create_uuid(self.number_of_subjects),
                                  maxLength=None, bidirectional=False))
        self.assertEqual(len(paths), 8)
        paths = list(tr.findPaths(self.create_uuid((1, 1)),
                                  self.create_uuid((self.number_of_subjects,
                                                    self.number_of_sulci)),
                                  maxLength=None, bidirectional=True))
        self.assertEquals(len(paths), 65)
        paths = list(tr.findPaths(self.create_uuid((1, 1)),
                                  self.create_uuid((self.number_of_subjects,
                                                    self.number_of_sulci))))
        self.assertEquals(len(paths), 0)

    def tearDown(self):
        brainvisa.axon.cleanup()
        shutil.rmtree(self.test_database_directory)
        neuroConfig.dataPath.remove(self.database_settings)


def test_suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestTransformationManager)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
