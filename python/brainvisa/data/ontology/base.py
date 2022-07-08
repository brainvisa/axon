
from brainvisa.data.fileSystemOntology import *


# Constants for default attributes values
default_center = "subjects"
default_acquisition = "default_acquisition"
default_analysis = "default_analysis"
default_session = "default_session"
default_graph_version = "3.1"


db_entries = lambda: (
    'scripts', SetContent('*', SetType('Script')),
                        # directory that contains scripts to undo conversion
                        # or cleaning database processes
    'history_book', SetContent(
        'bvsession', SetType('Bvsession'), SetContent(
            '*', SetType('BrainVISA session event'),),
        '*', SetContent('*', SetType('Process execution event'),),
    ),
    'database_fso', SetType('Database description page'),
    'database_settings', SetType('Database settings'),
    'trash',  # directory containing files that must be deleted
    '*', SetType('Database Cache file'),
)


