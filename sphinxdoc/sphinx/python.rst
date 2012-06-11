Axon python API modules
=======================

This part of the API is in the Python path, it may be imported without running Brainvisa.

Modules organization
--------------------

- :py:mod:`brainvisa.axon`: loading Brainvisa in a Python script.
- :py:mod:`brainvisa.processes`: classes about processes and pipelines.
- :py:mod:`brainvisa.anatomist`: specialization of pyanatomist API for Brainvisa. Used by most of Brainvisa viewers.
- :py:mod:`brainvisa.toolboxes`: Toolbox class representing a BrainVISA toolbox.
- :py:mod:`brainvisa.shelltools`: functions to copy, move, delete files.
- :py:mod:`brainvisa.workflow`: Conversion of a Process into a Workflow usable in :somaworkflow:`Soma-workflow <index.html>`.
- :py:mod:`brainvisa.validation`: Definition of an exception that can be raised by processes validation functions.
- :py:mod:`brainvisa.history`: Framework to manage history of processes.
- :py:mod:`brainvisa.multipleExecfile`: A class to load several inter-dependent python files.
- :py:mod:`brainvisa.registration`: referentials and transformations management.


brainvisa.configuration
+++++++++++++++++++++++

This module contains the classes that manage BrainVisa set of options, accessible throught the menu BrainVISA -> Preferences.

- :py:mod:`brainvisa.configuration.api`: Initialization of the configuration object that contains the user preferences.
- :py:mod:`brainvisa.configuration.neuroConfig`: global variables describing configuration parameters and user preferences.
- :py:mod:`brainvisa.configuration.anatomist_configuration`: options about Anatomist.
- :py:mod:`brainvisa.configuration.brainvisa_configuration`:  general options.
- :py:mod:`brainvisa.configuration.databases_configuration`:  options about the databases.
- :py:mod:`brainvisa.configuration.fsl_configuration`: options about FSL.
- :py:mod:`brainvisa.configuration.matlab_configuration`: options about Matlab. 
- :py:mod:`brainvisa.configuration.spm_configuration`: options about SPM.
- :py:mod:`brainvisa.configuration.r_configuration`: options about R.
- :py:mod:`brainvisa.configuration.qt4gui`: specific graphical user interface for options about databases and Matlab.

.. _brainvisa.data:

brainvisa.data
++++++++++++++

- :py:mod:`brainvisa.data.neuroData`: classes defining the signature of a process, parameter types.
- :py:mod:`brainvisa.data.neuroDiskItems`: class DiskItem that defines data and matching files.
- :py:mod:`brainvisa.data.neuroHierarchy`: databases creation and initialization.
- :py:mod:`brainvisa.data.sqlFSODatabase`
- :py:mod:`brainvisa.data.readdiskitem` 
- :py:mod:`brainvisa.data.writediskitem`
- :py:mod:`brainvisa.data.actions`
- :py:mod:`brainvisa.data.databaseCheck`
- :py:mod:`brainvisa.data.directory_iterator`
- :py:mod:`brainvisa.data.fileformats` 
- :py:mod:`brainvisa.data.fileSystemOntology`: classes to define a BrainVISA ontology.
- :py:mod:`brainvisa.data.ftpDirectory`
- :py:mod:`brainvisa.data.labelSelection`
- :py:mod:`brainvisa.data.localDirectory`
- :py:mod:`brainvisa.data.minfExtensions`: declaration of the type of objects that can be written in minf format.
- :py:mod:`brainvisa.data.patterns`
- :py:mod:`brainvisa.data.sql` 
- :py:mod:`brainvisa.data.temporary`
- :py:mod:`brainvisa.data.virtualDirectory`
- :py:mod:`brainvisa.data.qt4gui`


brainvisa.processing
++++++++++++++++++++

- :py:mod:`brainvisa.processing.neuroException`: classes and functions defining error and warning messages.
- :py:mod:`brainvisa.processing.neuroLog`: creation of BrainVISA log file.

  
brainvisa.tools
+++++++++++++++
- :py:mod:`brainvisa.tools.aimsGlobals`: definition of named lists of formats.
- :py:mod:`brainvisa.tools.matlabValidation`: validation function that checks if matlab is enable.
  

.. _brainvisa.processing.qt4gui:

brainvisa.processing.qt4gui: GUI Modules
+++++++++++++++++++++++++++++++++++++++++

The classes related to the graphical user interface are located in ``qt4gui`` modules. They use `PyQt API <http://www.riverbankcomputing.co.uk/software/pyqt/intro>`_, a set of Python bindings for `Nokia's Qt application framework <http://qt.nokia.com/>`_:
  
  - :py:mod:`brainvisa.processing.qtgui.backwardCompatibleQt`: it has been used to keep backward compatibility with old versions of PyQt.
  - :py:mod:`brainvisa.processing.qt4gui.neuroConfigGUI`: Bug report dialog.
  - :py:mod:`brainvisa.processing.qt4gui.neuroProcessesGUI`: BrainVISA main window and processes windows.
  - :py:mod:`brainvisa.processing.qt4gui.neuroLogGUI`: Log window.
  - :py:mod:`brainvisa.processing.qt4gui.command`: class CommandWithQProcess used to call commands in Brainvisa processes. This module is not related to the graphical user interface but it uses Qt, that's why it is in ``qt4gui`` module.
  - :py:mod:`brainvisa.data.qt4gui.neuroExceptionGUI`: Error and warning messages window.
  
  - :py:mod:`brainvisa.data.qt4gui.databaseCheckGUI`
  - :py:mod:`brainvisa.data.qt4gui.diskItemBrowser`
  - :py:mod:`brainvisa.data.qt4gui.hierarchyBrowser`
  - :py:mod:`brainvisa.data.qt4gui.history`
  - :py:mod:`brainvisa.data.qt4gui.labelSelectionGUI`
  - :py:mod:`brainvisa.data.qt4gui.neuroDataGUI`: Editor windows for the parameter types defined in :py:mod:`brainvisa.data.neuroData`.
  - :py:mod:`brainvisa.data.qt4gui.readdiskitemGUI`
  - :py:mod:`brainvisa.data.qt4gui.scalarFeaturesViewer`
  - :py:mod:`brainvisa.data.qt4gui.updateDatabases`
  
A module ``qtgui`` also exists but it is just a redirection to the ``qt4gui`` module. It was useful when we maintained the compatibility with qt3 but is no more the case.
  

brainvisa.axon
--------------

.. automodule:: brainvisa.axon
  :members:
    
.. automodule:: brainvisa.axon.processes
  :members:

brainvisa.processes
-------------------

.. automodule:: brainvisa.processes


brainvisa.anatomist: a specialized wrapper for Anatomist
--------------------------------------------------------

.. automodule:: brainvisa.anatomist
  :members:

brainvisa.toolboxes
-------------------

.. automodule:: brainvisa.toolboxes
  :members:

brainvisa.workflow
------------------

.. automodule:: brainvisa.workflow
  :members:


brainvisa.validation
--------------------

.. automodule:: brainvisa.validation
  :members:

brainvisa.history
-----------------

.. automodule:: brainvisa.history
  :members:
  :show-inheritance:

brainvisa.multipleExecfile
--------------------------

.. automodule:: brainvisa.multipleExecfile
  :members:
  :show-inheritance:

brainvisa.registration
----------------------

.. automodule:: brainvisa.registration
  :members:


brainvisa.configuration.neuroConfig
-----------------------------------

.. automodule:: brainvisa.configuration.neuroConfig
  :members:
  :show-inheritance:

brainvisa.data.neuroData
------------------------

.. automodule:: brainvisa.data.neuroData
  :members:
  :show-inheritance:

brainvisa.data.neuroDiskItems
-----------------------------

.. automodule:: brainvisa.data.neuroDiskItems
  :members:
  :show-inheritance:

brainvisa.data.neuroHierarchy
-----------------------------

.. automodule:: brainvisa.data.neuroHierarchy
  :members:
  :show-inheritance:

brainvisa.data.fileSystemOntology
---------------------------------

.. automodule:: brainvisa.data.fileSystemOntology
  :members:
  :show-inheritance:


brainvisa.data.sqlFSODatabase
-----------------------------

.. automodule:: brainvisa.data.sqlFSODatabase
  :members:

brainvisa.data.readdiskitem
---------------------------

.. automodule:: brainvisa.data.readdiskitem
  :members:

brainvisa.data.writediskitem
----------------------------

.. automodule:: brainvisa.data.writediskitem
  :members:

brainvisa.data.patterns
-----------------------

.. automodule:: brainvisa.data.patterns
  :members:
    
    
brainvisa.data.temporary
------------------------

.. automodule:: brainvisa.data.temporary
  :members:
    
    
brainvisa.data.virtualDirectory
-------------------------------

.. automodule:: brainvisa.data.virtualDirectory
  :members:
    
    
brainvisa.processing.neuroException
-----------------------------------

.. automodule:: brainvisa.processing.neuroException
  :members:
  :show-inheritance:

brainvisa.processing.neuroLog
-----------------------------

.. automodule:: brainvisa.processing.neuroLog
  :members:
  :show-inheritance:


brainvisa.tools.aimsGlobals
---------------------------

.. automodule:: brainvisa.tools.aimsGlobals
  :members:
  :show-inheritance:

brainvisa.processing.qt4gui.neuroProcessesGUI
---------------------------------------------

.. automodule:: brainvisa.processing.qt4gui.neuroProcessesGUI
  :members:
  :show-inheritance:


brainvisa.processing.qt4gui.neuroLogGUI
---------------------------------------

.. automodule:: brainvisa.processing.qt4gui.neuroLogGUI
  :members:
  :show-inheritance:
