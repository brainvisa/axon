Use cases of Axon python API
============================

Calling a process
-----------------

The module :py:mod:`brainvisa.processes` manages the processes, pipelines and their execution.

The object :py:class:`brainvisa.processes.ExcecutionContext` enables to start a Brainvisa process using the method :py:meth:`brainvisa.processes.ExcecutionContext.runProcess`. 
When Brainvisa is loaded, a default execution context exists and is returned by the function :py:func:`brainvisa.processes.`

The following example will load Brainvisa and run the process Threshold on an image:

>>> import brainvisa.axon
>>> import brainvisa.processes
>>> brainvisa.axon.initializeProcesses()
Loading toolbox ...
>>> context = brainvisa.processes.defaultContext()

>>> # Just to get an example data for running the process
>>> from brainvisa.configuration.neuroConfig import getSharePath, bvShareDirectory
>>> import os
>>> example_data = os.path.join(getSharePath(), bvShareDirectory, "anatomical_templates", "MNI152_T1_1mm_brain_mask.nii")
>>> # creating a temporary file for the output
>>> output_data = context.temporary("NIFTI-1 image")

>>> context.runProcess("threshold", image_input=example_data, image_output=output_data, threshold1=100)
<BLANKLINE>
Process Threshold started ...


Querying a database
-------------------

At Brainvisa startup, an internal database and the database selected in the user's preferences are loaded. 
The list of databases (:py:class:`brainvisa.data.sqlFSODatabase.SQLDatabases`) is stored in the global variable :py:var:`brainvisa.data.neuroHierarchy.databases`.
Each database is an instance of the class :py:class:`brainvisa.data.sqlFSODatabase.SQLDatabase`.
Several methods enable to query a database or a list of databases. The results of queries are generally :py:class:`brainvisa.data.neuroDiskItems.DiskItem` objects. A DiskItem represents data stored in files and indexed in a database with additionnal information.

In the following example, a DiskItem is searched in the databases by filename:

>>> from brainvisa.data.neuroHierarchy import databases
>>> from brainvisa.data.neuroDiskItems import DiskItem
>>> item = databases.getDiskItemFromFileName(example_data)
>>> isinstance(item, DiskItem)
True
>>> item.type
<anatomical Mask Template>
>>> item.format
'NIFTI-1 image'

>>> items = databases.findDiskItems({"_type" : "Model graph", "side": "left"})
>>> items
<generator object findDiskItems at ...>
>>> model_filename = items.next().fileName()
>>> model_filename.startswith(os.path.join(getSharePath(), bvShareDirectory, "models"))
True


>>> brainvisa.axon.cleanup()
