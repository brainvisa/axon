import unittest
import os
import tempfile
import shutil

import brainvisa.axon
from brainvisa.configuration import neuroConfig
from brainvisa.data.sqlFSODatabase import SQLDatabase
from brainvisa.data import neuroHierarchy
from brainvisa.processes import defaultContext
from soma import aims
from brainvisa.data.writediskitem import WriteDiskItem


class TestDatabaseHistory(unittest.TestCase):
  
  def setUp(self):
    brainvisa.axon.initializeProcesses()
    tempdir=tempfile.gettempdir()
    db_directory=os.path.join(tempdir, "tmp_tests_brainvisa", "database_history")
    if not os.path.exists(db_directory):
        os.makedirs(db_directory)
    # create a database in a temporary directory
    self.dbs = neuroConfig.DatabaseSettings( db_directory )
    self.dbs.expert_settings.ontology = 'brainvisa-3.1.0'
    self.dbs.expert_settings.sqliteFileName = os.path.join(db_directory, "database.sqlite")
    self.dbs.expert_settings.activate_history = True
    neuroConfig.dataPath.append( self.dbs )
    self.db = SQLDatabase( self.dbs.expert_settings.sqliteFileName,  db_directory, 
                           self.dbs.expert_settings.ontology, context=defaultContext(), settings=self.dbs )
    neuroHierarchy.databases.add( self.db )
    self.example_data = tempfile.NamedTemporaryFile(suffix=".nii")
    self.example_data.close()
    volume=aims.Volume( 256, 256, 128, dtype='int16' )
    volume.fill(0)
    aims.write(volume, self.example_data.name)
    
  def test_store(self):
    """
    Store data history when an output data of a process is written in a database for which the history is activated.
    """
    wd=WriteDiskItem("Raw T1 MRI", "NIFTI-1 image")
    output=wd.findValue({"_database" : self.db.name, "protocol" : "myproto", "subject" : "mysubject"})
    defaultContext().runProcess("importT1MRI", self.example_data.name, output)
    diskitem = self.db.findDiskItem({"_type" : "Raw T1 MRI", "protocol" : "myproto", "subject" : "mysubject"})
    self.assertTrue(diskitem is not None)
    bvproc_uuid = diskitem.get("lastHistoricalEvent")
    self.assertTrue(bvproc_uuid is not None)
    bvproc_file = os.path.join(self.db.name, "history_book", str(bvproc_uuid)+".bvproc")
    self.assertTrue(os.path.exists(bvproc_file))
    
  def tearDown(self):
    brainvisa.axon.cleanup()
    os.remove(self.example_data.name)
    shutil.rmtree(self.dbs.directory)
    neuroConfig.dataPath.remove(self.dbs)


def test_suite():
  return unittest.TestLoader().loadTestsFromTestCase(TestDatabaseHistory)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')