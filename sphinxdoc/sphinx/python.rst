brainvisa.* modules
===================

This part of the API is in the Python path, it may be imported without running Brainvisa.

Modules organization
--------------------

- :py:mod:`brainvisa.config`: information about BrainVISA version.
- :py:mod:`brainvisa.anatomist`: specialization of pyanatomist API for Brainvisa. Used by most of Brainvisa viewers.
- :py:mod:`brainvisa.toolboxes`: Toolbox class representing a BrainVISA toolbox.
- :py:mod:`brainvisa.shelltools`: functions to copy, move, delete files.
- :py:mod:`brainvisa.workflow`: Conversion of a Process into a Workflow usable in :somaworkflow:`Soma-workflow <index.html>`.
- :py:mod:`brainvisa.validation`: Definition of an exception that can be raised by processes validation functions.
- :py:mod:`brainvisa.history`: Framework to manage history of processes.

brainvisa.configuration
+++++++++++++++++++++++

This module contains the classes that manage BrainVisa set of options, accessible throught the menu BrainVISA -> Preferences.

- :py:mod:`brainvisa.configuration.api`: Initialization of the configuration object that contains the user preferences. 
- :py:mod:`brainvisa.configuration.anatomist_configuration`: options about Anatomist.
- :py:mod:`brainvisa.configuration.brainvisa_configuration`:  general options.
- :py:mod:`brainvisa.configuration.databases_configuration`:  options about the databases.
- :py:mod:`brainvisa.configuration.distributed_configuration`: options about remote execution.
- :py:mod:`brainvisa.configuration.fsl_configuration`: options about FSL.
- :py:mod:`brainvisa.configuration.matlab_configuration`: options about Matlab. 
- :py:mod:`brainvisa.configuration.spm_configuration`: options about SPM.
- :py:mod:`brainvisa.configuration.r_configuration`: options about R.
- :py:mod:`brainvisa.configuration.qt4gui`: specific graphical user interface for options about databases and Matlab.

brainvisa.data
++++++++++++++

- :py:mod:`brainvisa.data.sqlFSODatabase`
- :py:mod:`brainvisa.data.readdiskitem` 
- :py:mod:`brainvisa.data.writediskitem`
- :py:mod:`brainvisa.data.diskItemBrowser`
- :py:mod:`brainvisa.data.HierarchyBrowser`
- :py:mod:`brainvisa.data.actions`
- :py:mod:`brainvisa.data.databaseCheck`
- :py:mod:`brainvisa.data.directory_iterator`
- :py:mod:`brainvisa.data.fileformats` 
- :py:mod:`brainvisa.data.ftpDirectory`
- :py:mod:`brainvisa.data.labelSelection`
- :py:mod:`brainvisa.data.localDirectory`
- :py:mod:`brainvisa.data.patterns`
- :py:mod:`brainvisa.data.sql` 
- :py:mod:`brainvisa.data.temporary`
- :py:mod:`brainvisa.data.test`
- :py:mod:`brainvisa.data.virtualDirectory`
- :py:mod:`brainvisa.data.qt4gui`

brainvisa.config
----------------

.. automodule:: brainvisa.config
  :members:

brainvisa.anatomist: a specialized wrapper for Anatomist
--------------------------------------------------------

.. automodule:: brainvisa.anatomist
  :members:

brainvisa.toolboxes
-------------------

.. automodule:: brainvisa.toolboxes
  :members:


brainvisa.shelltools
--------------------

.. automodule:: brainvisa.shelltools
  :members:

brainvisa.workflow
------------------

.. automodule:: brainvisa.workflow
  :members:


brainvisa.validation
------------------

.. automodule:: brainvisa.validation
  :members:

brainvisa.history
------------------

.. automodule:: brainvisa.history
  :members:
  :show-inheritance:

brainvisa.configuration
-----------------------

.. automodule:: brainvisa.configuration.api
  :members:


brainvisa.data.actions
----------------------

.. automodule:: brainvisa.data.actions
  :members:

brainvisa.data.databaseCheck
----------------------------

.. automodule:: brainvisa.data.databaseCheck
  :members:

brainvisa.data.diskItemBrowser
------------------------------

.. automodule:: brainvisa.data.diskItemBrowser
  :members:

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

brainvisa.data.HierarchyBrowser
-------------------------------

brainvisa.data.directory_iterator
---------------------------------

..automodule:: brainvisa.data.directory_iterator
  :members:
    
brainvisa.data.fileformats
--------------------------

.. automodule:: brainvisa.data.fileformats
  :members:

brainvisa.data.ftpDirectory
---------------------------

.. automodule:: brainvisa.data.ftpDirectory
  :members:
    
brainvisa.data.labelSelection
-----------------------------

.. automodule:: brainvisa.data.labelSelection
  :members:
    
brainvisa.data.localDirectory
-----------------------------

.. automodule:: brainvisa.data.localDirectory
  :members:
    
brainvisa.data.patterns
-----------------------

.. automodule:: brainvisa.data.patterns
  :members:
    
brainvisa.data.sql
------------------

.. automodule:: brainvisa.data.sql
  :members:
    
brainvisa.data.temporary
------------------------

.. automodule:: brainvisa.data.temporary
  :members:
    
brainvisa.data.test
-------------------

    
brainvisa.data.virtualDirectory
-------------------------------

.. automodule:: brainvisa.data.virtualDirectory
  :members:
    
brainvisa.data.qt4gui
---------------------

.. automodule:: brainvisa.data.qt4gui
  :members:
