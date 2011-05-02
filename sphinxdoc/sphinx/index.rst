Axon python libraries API documentation
=======================================

Axon libraries rely on :somabase:`soma.base <index.html>` and :somaqtgui:`soma.qtgui <index.html>` modules. 

- It may use :somaworkflow:`soma.workflow <index.html>` to generate workflows for parallel execution on a cluster
- It may also maye use of :py:mod:`soma.aims <soma.aims>` if available, for files conversion and identification.
- and of :py:mod:`anatomist <anatomist>` if available, for viewers.

brainvisa.* modules
-------------------

brainvisa.config
++++++++++++++++

.. automodule:: brainvisa.config
  :members:


brainvisa.configuration
+++++++++++++++++++++++

.. automodule:: brainvisa.configuration.api
  :members:


brainvisa.data.actions
++++++++++++++++++++++

.. automodule:: brainvisa.data.actions
  :members:


brainvisa.data.readdiskitem
+++++++++++++++++++++++++++

.. automodule:: brainvisa.data.readdiskitem
  :members:


Modules under the main brainvisa directory
------------------------------------------

neuroConfig
+++++++++++

.. automodule:: neuroConfig
  :members:


neuroProcesses
++++++++++++++

.. automodule:: neuroProcesses
  :members:


neuroProcessesGUI
+++++++++++++++++

.. automodule:: neuroProcessesGUI
  :members:


brainvisa.anatomist: a specialized wrapper for Anatomist
--------------------------------------------------------

.. automodule:: brainvisa.anatomist
  :members:


