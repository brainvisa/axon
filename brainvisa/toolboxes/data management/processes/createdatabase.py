
from brainvisa.configuration import neuroConfig
from brainvisa import processes
from brainvisa.data import neuroHierarchy
from soma.wip.application.api import Application
from brainvisa.configuration import databases_configuration
from brainvisa.processes import Signature, WriteDiskItem, OpenChoice, Boolean
import os

name = 'Create database'
userLevel = 0

def availableOntologies():
    ontologies = ['brainvisa-3.2.0', 'brainvisa-3.1.0', 'brainvisa-3.0',
                  'shared']
    moreOntologies = set()

    try:
        from brainvisa.configuration import neuroConfig

        for path in neuroConfig.fileSystemOntologiesPath:
            if os.path.exists(path):
                for ontology in os.listdir(path):
                    if ontology == 'flat':
                        continue
                    if ontology not in ontologies and ontology not in moreOntologies:
                        moreOntologies.add(ontology)
    except ImportError:
        # may happen at startup:
        # neuroConfig is using DatabaseSettings and ExpertDatabaseSettings
        # in its initialization, and here we cannot import neuroConfig which
        # is currently initializing.
        pass
    ontologies += sorted(moreOntologies)
    return ontologies


signature = Signature(
    'database_directory', WriteDiskItem('Directory', 'Directory'),
    'ontology', OpenChoice(*availableOntologies()),
    'read_only', Boolean(),
    'temporary', Boolean(),
)

def initialization(self):
    self.read_only = False
    self.temporary = False


def create_database(database_directory, ontology='brainvisa-3.2.0',
                    allow_ro=False, persistent=False):
    if not os.path.exists(database_directory):
        os.makedirs(database_directory)
    database_settings = neuroConfig.DatabaseSettings(database_directory)
    database = neuroHierarchy.SQLDatabase(
        os.path.join(database_directory, "database.sqlite"),
        database_directory,
        ontology,
        context=processes.defaultContext(),
        settings=database_settings)
    neuroHierarchy.databases.add(database)
    neuroConfig.dataPath.append(database_settings)
    try:
        database.clear(context=processes.defaultContext())
        database.update(context=processes.defaultContext())
    except:
        if not allow_ro:
            raise
    if persistent:
        configuration = Application().configuration
        configuration.databases.fso.append(
            databases_configuration.DatabasesConfiguration.FileSystemOntology(
                database_directory, selected=True, read_only=allow_ro))
        configuration.save(neuroConfig.userOptionFile)
    return database


def execution(self, context):
    create_database(self.database_directory.fullPath(), self.ontology,
                    self.read_only, not self.temporary)
