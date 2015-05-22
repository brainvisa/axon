============================
Axon developer documentation
============================

* :axon:`Slides of a development course <Programming_with_brainvisa.pdf>`, with :axon:`training course data <Programming_with_brainvisa.zip>`
* :doc:`Developer manual <developer_manual>`

* :axonusr:`Axon user documentation <index.html>`

Python API documentation
========================

Axon python API is used by BrainVISA software. It includes modules to manage BrainVISA toolboxes, processes, databases, graphical user interface, etc.

Axon libraries rely on :somabase:`soma.base <index.html>` modules.

- It may use :somaworkflow:`soma_workflow <index.html>` to generate workflows for parallel execution on a cluster
- It may also use of :py:mod:`soma.aims <soma.aims>` if available, for files conversion and identification.
- and of :py:mod:`anatomist <anatomist>` if available, for viewers.

This API can be used in several contexts:
  - in a **BrainVISA IPython shell** started with ``brainvisa --shell`` or *start shell* menu
  - in a **BrainVISA process**
  - in a script executed from brainvisa in **batch mode**: ``brainvisa -b -e myScript.py``
  - in a **Python script** where Brainvisa is loaded using the module :py:mod:`brainvisa.axon`

To determine the version of the API, use ``brainvisa.config.shortVersion`` (|version|) or ``brainvisa.config.fullVersion`` (|release|).

Modules organization
--------------------

The modules of Axon python API are in the top-level package brainvisa.

Main modules
++++++++++++

- :py:mod:`brainvisa.axon`: loading Brainvisa in a Python script.
- :py:mod:`brainvisa.processes`: classes about processes and pipelines.
- :ref:`brainvisa.data`: sub-package containing modules about Brainvisa databases and process parameters.
- :py:mod:`brainvisa.registration`: referentials and transformations management.
- :py:mod:`brainvisa.anatomist`: specialization of pyanatomist API for Brainvisa. Used by most of Brainvisa viewers.
- :ref:`brainvisa.processing.qt4gui`
- :py:mod:`brainvisa.toolboxes`: Toolbox class representing a BrainVISA toolbox.
- :py:mod:`brainvisa.workflow`: Conversion of a Process into a Workflow usable in :somaworkflow:`Soma-workflow <index.html>`.
- :py:mod:`brainvisa.history`: Framework to manage history of processes.

Detailled list of modules in here: :doc:`python`.
  
Use cases & examples
--------------------

.. toctree::

  usecases

**Processes** : Any process available in BrainVISA may be used as an example to help in developing new processes. The source code of each process is available directly from BrainVISA inline documentation: just click on the file name in the technical information part of the process documentation.


.. toctree::
   :hidden:

   developer_manual
   usecases
   python
   python_bv_data
   python_bv_data_gui
   python_bv_processing
   python_bv_processing_gui
