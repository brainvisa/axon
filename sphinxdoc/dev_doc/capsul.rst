
============================
CAPSUL: what are the plans ?
============================

:capsul:`CAPSUL <index.html>` is a new pipelining system designed to replace Axon processes and pipelines API in the future. It is designed as an independent library, and has a different philosophy from Axon legacy system.

CAPSUL is released with BrainVISA 4.5 but is not fully integrated yet.

Why ?
=====

The pipelining system in Axon has a number of drawbacks:

* Having evolved and grown with years along not-really-planned needs, it has heavy design flaws: not very clear APIs, source code difficult to read, lack of documentation, somewhat mixed processing, dadabasing and GUI parts...
* It is not very easy to write pipelines with proper links between sub-processes parameters, it is quite error prone and difficult to debug.
* There are some performance bottlenecks which cannot be solved using the current design.

In other words, a new design, with cleaner code and documentation, was needed.


How will Axon and CAPSUL processes integrate ?
==============================================

CAPSUL can make use of :somaworkflow:`Soma-Workflow <index.html>` processing distribution infrastructure, like Axon is.

The process and pipeline APIs are different, with some similar principles: a process has input and output parameters, processes parameters are linked in pipelines. But parameters typing is very different in Axon and Capsul: Capsul is a simplified interface, only knowing "files", numbers or strings, and list parameters types: there is no notion of "bias corrected T1 MRI" for instance.

Thus parameters types and filename completion is based on a different approach.


Can I convert my old Axon processes and pipelines to CAPSUL, or will I have to rewrite them all ?
=================================================================================================

Conversion tools have been designed (and may evolve in next releases):

* ``axon_to_capsul.py`` or ``python -m brainvisa.processing.axon_to_capsul`` can convert Axon processes and pipelines to CAPSUL APIs. It will write Python source files as converted processes, so that they can be modified afterwards. Indeed, conversions are not always perfect due to typing incompatibilities, tuning in Axon processes and parameters links which cannot be automatically converted, etc.
* ``axon_fso_to_fom.py`` or ``python -m brainvisa.processing.axon_fso_to_fom`` converts Axon ontologies (files hierarchy descriptions) to CAPSUL FOM (File Organization Model).
* ``capsul_to_axon.py`` converts CAPSUL processes or pipelines to Axon processes (does not convert pipeline structures). It writes Python code files as outputs, in a similar way as the reverse tool. Again, parameters types are not fully converted, and parameters links are lost.


Can we use CAPSUL processes in BrainVISA/Axon ?
===============================================

Yes, partly.

It is possible to declare an Axon process which wraps a Capsul process or pipeline. Capsul parameters are translated to Axon ones, so Axon GUI will display all the parameters. But again, files typing and links do not work, at least not yet.

Capsul process execution will be triggered by Axon pipeline execution, and their workflows will integrate, so distributed execution should work as expected in Soma-Workflow.

How ?
-----

An Axon process can be a Capsul wrapper. Such a process is a python file, as any other Axon process. But this one has simply to declare that it wraps a Capsul process, and tell which one.

Typically it will look like this:

::

    from brainvisa.processes import *
    from brainvisa.processing import capsul_process

    name = 'Capsul-Morphologist'
    userLevel = 0

    base_class = capsul_process.CapsulProcess
    capsul_process = 'morphologist.capsul.morphologist.Morphologist'

Here, the ``base_class`` variable tells that this process inherits the special :py:class:`CapsulProcess <brainvisa.processing.capsul_process.CapsulProcess>` class, which handles Capsul/Axon conversion and connection.

The ``capsul_process`` variable tells which Capsul process is wrapped. Naming follonw the python module/class model, exactly like :capsul:`get_process_instance <api_tree/generated/capsul-process/capsul.process.loader.get_process_instance.html>` function.


Limitations
-----------

* Parameters completion is disabled:
  Links between parameters are not done, and FOM completion is not performed on the underlying CAPSUL process.
  Maybe this can be improved in the future.

* Soma-Workflow files sharing and transfers policy is not exactly the same in Axon and Capsul: in Axon, file transfers can be set differently for input and output files. In Capsul, all files corresponding to a given directory tree are handled the same way. Thus there can be a few behaviour differences in Capsul parts of a workflow.


What's the current state ?
==========================

Axon / Capsul integratioon is just beginning in BrainVisa 4.5.

By now just a few processes and pipelines have been ported to Capsul (:morphologist:`Morphologist <index.html>` is a typical example of it), and are currently used through dedicated processes or applications, like :morphoui:`Morphologist-UI <index.html>`


How will it evolve ?
====================

The transition phase will probably last several years, so we have to provide bridges between both pipelining systems.

We can probably improve automatic bridging (through the :py:mod:`capsul_process <brainvisa.processing.capsul_process>` module and the ``axon_to_capsul.py`` utility).

Especially we may be able to specify FOM rules and completion in Capsul processes and make links work this way in Axon interfaces.

In a longer term, we haven't decided yet if the Axon main graphical interface (the ``brainvisa`` program) will remain or if we will switch to another one.


