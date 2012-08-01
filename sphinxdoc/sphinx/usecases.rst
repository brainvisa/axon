Use cases of Axon python API
============================

Load Brainvisa
--------------

The following lines enable to load Brainvisa without the graphical user interface through a python script:

>>> import brainvisa.axon
>>> brainvisa.axon.initializeProcesses()
Loading toolbox ...

Call a process
--------------

The module :py:mod:`brainvisa.processes` manages the processes, pipelines and their execution.

The object :py:class:`brainvisa.processes.ExecutionContext` enables to start a Brainvisa process using the method :py:meth:`brainvisa.processes.ExecutionContext.runProcess`.
When Brainvisa is loaded, a default execution context exists and is returned by the function :py:func:`brainvisa.processes.defaultContext`

The following example will run the process Threshold on an image:

>>> import brainvisa.processes
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

Select a step in a pipeline
---------------------------

In a pipeline, some steps may be optional and can be selected or unselected for execution. 
It is possible to select or unselect a step of a pipeline before running it through a python script. 
A pipeline is a process that have execution nodes. The method :py:meth:`brainvisa.processes.Process.executionNode` returns an :py:class:`brainvisa.processes.ExecutionNode`.
The execution node of the pipeline contains child nodes, the name of these nodes can be obtained with the method :py:meth:`brainvisa.processes.ExecutionNode.childrenNames`.
To get a specific child node, the method :py:meth:`brainvisa.processes.ExecutionNode.child` can be used.

The following examples gets an instance of the Morphologist pipeline and selects it *sulci recognition* step:

>>> pipeline=brainvisa.processes.getProcessInstance("morphologist")
>>> nodes=pipeline.executionNode()

>>> nodes.childrenNames()
['PrepareSubject', 'BiasCorrection', ...
>>> nodes.child("SulciRecognition").setSelected(1)
<BLANKLINE>
Process Check SPAM models ...
>>> nodes.child("SulciRecognition").isSelected()
1

The process instance can be given as a parameter for the :py:meth:`brainvisa.processes.ExecutionContext.runProcess` method instead of the process id. 
In the following exemple, the parameters of the process should be filled in to really execute the pipeline:

>>> brainvisa.processes.defaultContext().runProcess(pipeline)
Traceback (most recent call last):
    ...
Exception: Mandatory argument <em>mri</em> has not a valid value

Query a database
----------------

At Brainvisa startup, an internal database and the database selected in the user's preferences are loaded. 
The list of databases (:py:class:`brainvisa.data.sqlFSODatabase.SQLDatabases`) is stored in the global variable :py:data:`brainvisa.data.neuroHierarchy.databases`.
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


Here is a request for all DiskItems of type "Model graph" with the value of *side* attribute is "left":


>>> items = databases.findDiskItems({"_type" : "Model graph", "side": "left"})
>>> items
<generator object ...>
>>> model_filename = items.next().fileName()
>>> model_filename.startswith(os.path.join(getSharePath(), bvShareDirectory, "models"))
True

The object :py:class:`brainvisa.data.readdiskitem.ReadDiskItem` enables to search for an existing DiskItem in the databases using the method :py:meth:`ReadDiskItem.findValue`. If the request is not precise enought and several DiskItems match, the method returns nothing.

>>> from brainvisa.data.readdiskitem import ReadDiskItem
>>> rd=ReadDiskItem("Model graph", "Graph and Data")
>>> rd.findValue({"side" : "left"})
>>> model = rd.findValue({"side" : "left", "sulci_database" : "2001"})
>>> model.fileName().startswith(os.path.join(getSharePath(), bvShareDirectory, "models"))
True

The object :py:class:`brainvisa.data.writediskitem.WriteDiskItem` enables to create new DiskItems to write output data according to Brainvisa hierarchy of directories.

>>> from brainvisa.data.writediskitem import WriteDiskItem
>>> wd=WriteDiskItem("Raw T1 MRI", "NIFTI-1 image")
>>> item=wd.findValue({"protocol" : 'test', "subject" : "mysubject"})
>>> item.isReadable()
0

Quit Brainvisa
--------------

The function :py:func:`brainvisa.axon.processes.cleanup` should be called at the end of the script to quit properly Brainvisa.

>>> brainvisa.axon.cleanup()
