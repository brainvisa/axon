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
- :py:mod:`brainvisa.configuration.mpegConfig`
- :py:mod:`brainvisa.configuration.qt4gui.neuroConfigGUI`: Bug report dialog.


.. _brainvisa.data:

brainvisa.data
++++++++++++++

- :py:mod:`brainvisa.data.neuroData`: classes defining the signature of a process, parameter types.
- :py:mod:`brainvisa.data.neuroDiskItems`: class DiskItem that defines data and matching files.
- :py:mod:`brainvisa.data.neuroHierarchy`: databases creation and initialization.
- :py:mod:`brainvisa.data.fileSystemOntology`: classes to define a BrainVISA ontology.
- :py:mod:`brainvisa.data.sqlFSODatabase`
- :py:mod:`brainvisa.data.readdiskitem` 
- :py:mod:`brainvisa.data.writediskitem`
- :py:mod:`brainvisa.data.actions`
- :py:mod:`brainvisa.data.databaseCheck`
- :py:mod:`brainvisa.data.directory_iterator`
- :py:mod:`brainvisa.data.fileformats` 
- :py:mod:`brainvisa.data.ftpDirectory`
- :py:mod:`brainvisa.data.labelSelection`
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
- :py:mod:`brainvisa.tools.mainthreadlife`: ensure an object is deleted in the main thread.
- :py:mod:`brainvisa.tools.matlabValidation`: validation function that checks if matlab is enabled.
- :py:mod:`brainvisa.tools.spm_conversion`
- :py:mod:`brainvisa.tools.spm_registration`
- :py:mod:`brainvisa.tools.spm_results`
- :py:mod:`brainvisa.tools.spm_run`
- :py:mod:`brainvisa.tools.spm_segmentation`
- :py:mod:`brainvisa.tools.spm_utils`
- :py:mod:`brainvisa.tools.DisplayResultsFromSPM`
- :py:mod:`brainvisa.tools.displayTitledGrid`


.. _brainvisa.processing.qt4gui:

brainvisa.processing.qt4gui: GUI Modules
+++++++++++++++++++++++++++++++++++++++++

The classes related to the graphical user interface are located in ``qt4gui`` modules. They use `PyQt API <http://www.riverbankcomputing.co.uk/software/pyqt/intro>`_, a set of Python bindings for `Qt application framework <http://qt.nokia.com/>`_:

  - :py:mod:`brainvisa.processing.qtgui.backwardCompatibleQt`: it has been used to keep backward compatibility with old versions of PyQt.
  - :py:mod:`brainvisa.processing.qt4gui.neuroProcessesGUI`: BrainVISA main window and processes windows.
  - :py:mod:`brainvisa.processing.qt4gui.neuroExceptionGUI`: Error and warning messages window.
  - :py:mod:`brainvisa.processing.qt4gui.neuroLogGUI`: Log window.
  - :py:mod:`brainvisa.processing.qt4gui.command`: class CommandWithQProcess used to call commands in Brainvisa processes. This module is not related to the graphical user interface but it uses Qt, that's why it is in ``qt4gui`` module.

Some ``qtgui`` modules also exist but are mainly just redirections to the corresponding ``qt4gui`` module. It was useful when we maintained the compatibility with qt3 but is no more the case.


brainvisa.data.qt4gui: GUI Modules
++++++++++++++++++++++++++++++++++

  - :py:mod:`brainvisa.data.qt4gui.databaseCheckGUI`
  - :py:mod:`brainvisa.data.qt4gui.diskItemBrowser`
  - :py:mod:`brainvisa.data.qt4gui.hierarchyBrowser`
  - :py:mod:`brainvisa.data.qt4gui.history`
  - :py:mod:`brainvisa.data.qt4gui.labelSelectionGUI`
  - :py:mod:`brainvisa.data.qt4gui.neuroDataGUI`: Editor windows for the parameter types defined in :py:mod:`brainvisa.data.neuroData`.
  - :py:mod:`brainvisa.data.qt4gui.readdiskitemGUI`
  - :py:mod:`brainvisa.data.qt4gui.scalarFeaturesViewer`
  - :py:mod:`brainvisa.data.qt4gui.updateDatabases`


brainvisa.shelltools
--------------------

.. automodule:: brainvisa.shelltools
  :members:
  :show-inheritance:

brainvisa.anatomist: a specialized wrapper for Anatomist
--------------------------------------------------------

.. automodule:: brainvisa.anatomist
  :members:
  :show-inheritance:

brainvisa.toolboxes
-------------------

.. automodule:: brainvisa.toolboxes
  :members:
  :show-inheritance:

brainvisa.workflow
------------------

.. automodule:: brainvisa.workflow
  :members:
  :show-inheritance:


brainvisa.validation
--------------------

.. automodule:: brainvisa.validation
  :members:
  :show-inheritance:

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
  :show-inheritance:


brainvisa.configuration.api
---------------------------

.. automodule:: brainvisa.configuration.api
  :members:
  :show-inheritance:

brainvisa.configuration.neuroConfig
-----------------------------------

.. automodule:: brainvisa.configuration.neuroConfig
  :members:
  :show-inheritance:

brainvisa.configuration.mpegConfig
----------------------------------

.. automodule:: brainvisa.configuration.mpegConfig
  :members:
  :show-inheritance:

brainvisa.configuration.brainvisa_configuration
-----------------------------------------------

.. automodule:: brainvisa.configuration.brainvisa_configuration
  :members:
  :show-inheritance:

brainvisa.configuration.anatomist_configuration
-----------------------------------------------

.. automodule:: brainvisa.configuration.anatomist_configuration
  :members:
  :show-inheritance:

brainvisa.configuration.databases_configuration
-----------------------------------------------

.. automodule:: brainvisa.configuration.databases_configuration
  :members:
  :show-inheritance:

brainvisa.configuration.fsl_configuration
-----------------------------------------

.. automodule:: brainvisa.configuration.fsl_configuration
  :members:
  :show-inheritance:

brainvisa.configuration.matlab_configuration
--------------------------------------------

.. automodule:: brainvisa.configuration.matlab_configuration
  :members:
  :show-inheritance:

brainvisa.configuration.spm_configuration
-----------------------------------------

.. automodule:: brainvisa.configuration.spm_configuration
  :members:
  :show-inheritance:

brainvisa.configuration.r_configuration
-----------------------------------

.. automodule:: brainvisa.configuration.r_configuration
  :members:
  :show-inheritance:

brainvisa.tools.aimsGlobals
---------------------------

.. automodule:: brainvisa.tools.aimsGlobals
  :members:
  :show-inheritance:

brainvisa.tools.mainthreadlife
------------------------------

.. automodule:: brainvisa.tools.mainthreadlife
  :members:
  :show-inheritance:

brainvisa.tools.matlabValidation
--------------------------------

.. automodule:: brainvisa.tools.matlabValidation
  :members:
  :show-inheritance:

brainvisa.tools.spm_conversion
------------------------------

.. automodule:: brainvisa.tools.spm_conversion
  :members:
  :show-inheritance:

brainvisa.tools.spm_registration
--------------------------------

.. automodule:: brainvisa.tools.spm_registration
  :members:
  :show-inheritance:

brainvisa.tools.spm_results
---------------------------

.. automodule:: brainvisa.tools.spm_results
  :members:
  :show-inheritance:

brainvisa.tools.spm_run
-----------------------

.. automodule:: brainvisa.tools.spm_run
  :members:
  :show-inheritance:

brainvisa.tools.spm_segmentation
--------------------------------

.. automodule:: brainvisa.tools.spm_segmentation
  :members:
  :show-inheritance:

brainvisa.tools.spm_utils
-------------------------

.. automodule:: brainvisa.tools.spm_utils
  :members:
  :show-inheritance:

brainvisa.tools.DisplayResultsFromSPM
-------------------------------------

.. automodule:: brainvisa.tools.DisplayResultsFromSPM
  :members:
  :show-inheritance:

brainvisa.tools.displayTitledGrid
---------------------------------

.. automodule:: brainvisa.tools.displayTitledGrid
  :members:
  :show-inheritance:

