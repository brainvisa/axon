Axon python libraries API documentation
=======================================

Axon python API is used by BrainVISA software. It includes modules to manage BrainVISA toolboxes, processes, databases, graphical user interface, etc.

Axon libraries rely on :somabase:`soma.base <index.html>` and :somaqtgui:`soma.qtgui <index.html>` modules. 

- It may use :somaworkflow:`soma.workflow <index.html>` to generate workflows for parallel execution on a cluster
- It may also use of :py:mod:`soma.aims <soma.aims>` if available, for files conversion and identification.
- and of :py:mod:`anatomist <anatomist>` if available, for viewers.

This API can be used in several contexts:
  - in a **BrainVISA IPython shell** started with ``brainvisa --shell`` or *start shell* menu
  - in a **BrainVISA process**
  - in a script executed from brainvisa in **batch mode**: ``brainvisa -b -e myScript.py``
  - in a **Python script** where Brainvisa is loaded using the module :py:mod:`brainvisa.axon`

Modules organization
--------------------

.. toctree:: 
  :hidden:
  
  brainvisa
  python

Most of the API is in the form of classical python modules under the main brainvisa module but a few python files are in a brainvisa directory that is not in the python path and thus not accessible without running BrainVISA.

- :doc:`brainvisa`: main module executed at Brainvisa startup and a few empty modules that redirect to a new location kept only for backward compatibility.
- :doc:`python`: Modules of the axon python API: processes, data ontology, toolboxes, preferences, databases.

Examples
--------

- Setting a database: `brainvisaSetDatabase.py <../examples/brainvisaSetDatabase.py>`_
- A process with a dynamic signature: `DynamicSignature.py <../examples/processes/DynamicSignature.py>`_
- **Processes** : Any process available in BrainVISA may be used as an example to help in developing new processes. The source code of each process is available directly from BrainVISA inline documentation: just click on the file name in the technical information part of the process documentation.

Other documentation
-------------------

A **programming manual** is available `here <../bv_pg/en/html/index.html>`_. Among others, it shows how to use this API to develop new processes and toolboxes and to extend the data ontology 