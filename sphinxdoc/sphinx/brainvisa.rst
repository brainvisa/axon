Modules under the main brainvisa directory
==========================================

This part of the API is available only when brainvisa is running. The modules described here can used in several contexts:
  - in a BrainVISA IPython shell started with ``brainvisa --shell`` or *start shell* menu
  - in a BrainVISA process
  - in a script executed from brainvisa in batch mode: ``brainvisa -b -e myScript.py``

Modules organization
--------------------

Main modules
++++++++++++

  - :py:mod:`neuro`: the main module, it is executed by brainvisa command.
  - :py:mod:`neuroConfig`: global variables describing configuration parameters and user preferences.
  - :py:mod:`neuroProcesses`: classes about processes and pipelines.
  - :py:mod:`neuroException`: classes and functions defining error and warning messages.
  - :py:mod:`neuroLog`: creation of BrainVISA log file.

  
Data modules
++++++++++++
  
  - :py:mod:`neuroData`: classes defining the signature of a process, parameter types.
  - :py:mod:`neuroDiskItems`: class DiskItem that defines data and matching files.
  - :py:mod:`neuroHierarchy`: databases creation and initialization.
  - :py:mod:`fileSystemOntology`: classes to define a BrainVISA ontology.
  - :py:mod:`shfjGlobals`: definition of named lists of formats.
  - :py:mod:`registration`: referentials and transformations management.

GUI Modules
+++++++++++

The classes related to the graphical user interface are located in ``qt4gui`` module. They use `PyQt API <http://www.riverbankcomputing.co.uk/software/pyqt/intro>`_, a set of Python bindings for `Nokia's Qt application framework <http://qt.nokia.com/>`_:
  
  - :py:mod:`qt4gui.neuroConfigGUI`: Bug report dialog.
  - :py:mod:`qt4gui.neuroProcessesGUI`: BrainVISA main window and processes windows.
  - :py:mod:`qt4gui.neuroDataGUI`: Editor windows for the parameter types defined in :py:mod:`neuroData`.
  - :py:mod:`qt4gui.neuroExceptionGUI`: Error and warning messages window.
  - :py:mod:`qt4gui.neuroLogGUI`: Log window.
  - :py:mod:`qt4gui.command`: class CommandWithQProcess used to call commands in Brainvisa processes. This module is not related to the graphical user interface but it uses Qt, that's why it is in ``qt4gui`` module.
  
A module ``qt3gui`` also exists because we had to duplicate the graphical interface modules during the change from Qt3 to Qt4 for backward compatibility. That's why there is a ``qtgui`` module that just switches to ``qt3gui`` or ``qt4gui`` module according to the current version of Qt.

Miscellaneous modules
+++++++++++++++++++++

  - :py:mod:`neuroPopen2`
  - :py:mod:`backwardCompatibleQt`: it has been used to keep backward compatibility with old versions of PyQt.
  - :py:mod:`matlabValidation`: validation function that checks if matlab is enable.
  - :py:mod:`minfExtensions`: declaration of the type of objects that can be written in minf format.

neuro
-----

.. automodule:: neuro

.. autofunction:: neuro.main
.. autofunction:: neuro.setQtApplicationStyle
.. autofunction:: system_exit_handler
.. autofunction:: qt_exit_handler

neuroConfig
-----------

.. automodule:: neuroConfig
  :members:


neuroProcesses
--------------

.. automodule:: neuroProcesses

neuroException
--------------

.. automodule:: neuroException
  :members:

neuroLog
--------

.. automodule:: neuroLog
  :members:

neuroData
---------

.. automodule:: neuroData
  :members:

neuroDiskItems
--------------

.. automodule:: neuroDiskItems
  :members:

neuroHierarchy
--------------

.. automodule:: neuroHierarchy
  :members:

fileSystemOntology
------------------

.. automodule:: fileSystemOntology
  :members:

shfjGlobals
-----------

.. automodule:: shfjGlobals
  :members:

registration
------------

.. automodule:: registration
  :members:

qt4gui.neuroConfigGUI
---------------------

.. automodule:: qt4gui.neuroConfigGUI
  :members:

qt4gui.neuroProcessesGUI
------------------------

.. automodule:: qt4gui.neuroProcessesGUI
  :members:

qt4gui.neuroDataGUI
-------------------

.. automodule:: qt4gui.neuroDataGUI
  :members:

qt4gui.neuroExceptionGUI
------------------------

.. automodule:: qt4gui.neuroExceptionGUI
  :members:

qt4gui.neuroLogGUI
------------------

.. automodule:: qt4gui.neuroLogGUI
  :members:

qt4gui.command
------------------

.. automodule:: qt4gui.command
  :members:

neuroPopen2
-----------

.. automodule:: neuroPopen2
  :members:
 
backwardCompatibleQt
--------------------

.. automodule:: backwardCompatibleQt
  :members:

matlabValidation
----------------

.. automodule:: matlabValidation
  :members:

minfExtensions
--------------

.. automodule:: minfExtensions
  :members:
