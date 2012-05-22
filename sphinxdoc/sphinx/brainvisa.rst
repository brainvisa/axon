Modules under the main brainvisa directory
==========================================

This part of the API is available only when brainvisa is running. The modules described here can used in several contexts:
  - in a **BrainVISA IPython shell** started with ``brainvisa --shell`` or *start shell* menu
  - in a **BrainVISA process**
  - in a script executed from brainvisa in **batch mode**: ``brainvisa -b -e myScript.py``
  - in a **Python script** where Brainvisa is loaded using the module :py:mod:`brainvisa.axon`

Modules organization
--------------------

Main modules
++++++++++++

  - :py:mod:`neuro`: the main module, it is executed by brainvisa command.

neuro
-----

.. automodule:: neuro

.. autofunction:: neuro.main
.. autofunction:: neuro.setQtApplicationStyle
.. autofunction:: system_exit_handler
.. autofunction:: qt_exit_handler

