=====================
Axon developer manual
=====================

Introduction
============

This document should teach how to program BrainVisa and to create custom processes. The audience is supposed to be familiar with `Python language <http://python.org>`_.

If you are not, you are encouraged to look at the `Python tutorial <https://docs.python.org/tutorial/index.html>`_ and the `Python documentation <http://docs.python.org>`_.


Data management</classname>
---------------

The data management interface allows to organize data stored on a file system according to a (possibly user-defined) ontology. A *BrainVisa* user can provide a *files and directories ontology* (**FDO**) that is associated with a directory to define the organization of the whole directory's content (including sub-directories). The *FDO* contains naming conventions that allow to identify any file according to an ontology. *BrainVisa* provides a database system which is based on *FDO*. This system is organized in three layers (See the :ref:`figure below <figDataManagementSystem>`):

* File formats

  This layer groups the files in data items according to a set of file format definitions. All files corresponding to the same data are grouped in a single data item. For example, a data item can represent the header file (``*.hdr``) and the data file (``*.img``) of an *Analyze* format image, or it can represent a set of *DICOM* files composing one MR acquisition.

* Files/Directories ontology

  This layer uses an *FDO* definition to identify the data items. It sets the  item's data type and the item's ontology attributes. The data type identifies the contents of a data item (image, mesh, functional image, anatomical MRI, etc). The data types are organized in a hierarchy making it possible to decline a generic type in several specialized types. For example, there is a **4D Image** type which is specialized in **3D Image** (indeed, a three-dimensional image is a particular case of a four-dimensional one); the type **3D Image** is itself declined in several types, of which **T1 MRI** and **Brain mask** both belong indirectly. The ontology attributes define the way the data items are grouped and linked together. For example, all the data from one *center* could have the same value for the *center* attribute.

* Query interface

  This layer is the user entry point to the *BrainVisa* database system. It provides a query system that rely on data type and ontology attributes. A data query is composed of a file type and a set of attributes filters. The result of a query is a set of data items. For example, querying for data of type **T1 MRI** with attribute *subject* equal to ``John Doe`` would return all T1-weighted exams of John Doe (provided that the *FDO* of the database defines a type named **T1 MRI** and a *subject* attribute).

.. _figDataManagementSystem:

.. figure:: images/data_layers.jpg
  :align: center

  Architecture of *BrainVisa* data management system.


Software management
-------------------

The software management system contains the architecture for the integration of various programs and libraries in a common environment. It provides a developpement environement that facilitates the integration of neuroimaging data processing or visualization software. This integration is done via a set of **processes**. A *process* is a Python script that declares its input and output parameters, it is composed of three parts (See the :ref:`figure below <figTresholdProcess>`):

* Signature

  The signature contains the definition of its parameters. A parameter has a name and a type. The knowledge of the parameter type makes it possible to *BrainVisa* to automatically generate a graphical interface to select values for the parameter. Some parameter types are related to the data management system and allows to select only specific values in the database. For instance it is possible to build a parameter that will only accept normalized fMRI images. In the example of :ref:`the figure here <figTresholdProcess>`, the *image_input* parameter only accepts data of type **4D Volume**, therefore *BrainVisa* will raise an error if this process is called with an inappropriate data type such as a *mesh*.

* Initialization

  An initialization function called whenever a new instance of this process is created. It allows, for example, to set the default values of the parameters.

* Body

  The body is a function which is the entry point for the process execution. In the threshold example of the :ref:`figure <figTresholdProcess>`, it calls an external command-line program (``AimsThreshold``) to actually perform the thresholding.

.. _figTresholdProcess:

.. figure:: images/thresholdProcess.jpg
  :align: center

  An example of a simple BrainVISA process: thresholding an image


.. data:

Data ontology
=============

*BrainVisa* uses a data ontology to organize its databases. This ontology describes data types, and the name and place of each data in the file system according to its type. *BrainVisa* has a default ontology but it is possible to complete it or to create another one.

Data ontology is described through:

* *types* files that contain data types and formats
* *hierarchies* files that contain rules to associate name, place in file system and attributes to each data type.


Types
-----

Types files are in the ``brainvisa/types`` directory or in the types directory of a toolbox (See :ref:`toolboxes`). They describe all data types and formats that will be recognized by *BrainVisa*. These files are written in Python. It is not mandatory to write several files but it is more practical to organize information. When a file uses types or formats described in another file, it is necessary to include a reference to this file. For example, ``registration.py`` uses ``builtin.py``, so ``registration.py`` begins with:

::

  include('builtin')

* Format

  A format is defined by a name and a pattern to identify files in this format. Generally the data format can be found with the files extensions. Some data may exist in different formats. For example, an MRI image can be written in *Analyze*, *GIS*, *NIFTI* formats...

  ::

    Format(format name, list of the patterns, [attributes])

  Example:

  ::

    Format('GIS image', ["f|*.ima", "f|*.dim"])

  In this example, the *GIS* image format defines a couple of files, one with ``.ima`` extension  and the other with ``.dim`` extension.

  A pattern begins with ``"f|"`` to match a file or with ``"d|"`` to match a directory. In the rest of the pattern, ``"*"`` stands for any string.

  .. currentmodule:: brainvisa.data.neuroDiskItems

  The above code lines creates an instance of the class :py:class:`Format` which is defined in the module :py:mod:`brainvisa.data.neuroDiskItems`. At startup, *BrainVisa* loads all formats. It is possible to retrieve a particular format by its name using the function :py:func:`getFormat` or to get all existing formats with :py:func:`getAllFormats()`.

* Type

  A data type is defined by a name, a parent type and optionally a list of possible formats. Types are organized in a hierarchy.

  ::

    FileType(<type name>, <parent type>, [<format name or list of format names>], [<attributes>])

  Example:

  ::

    FileType('4D Volume', 'Any Type', 'BrainVISA volume formats')
    FileType('3D Volume', '4D Volume')
    FileType('Texture', 'Any Type', 'Texture')

  In this example, the **3D Volume** type is a specialization of the **4D volume** type and accept formats defined in the list named ``"BrainVISA volume formats"``. It is also possible to directly put the list of formats names or only one format as for the **Texture** type. All types derive from the general type **Any Type**.

  As for formats, :py:class:`FileType` is a class defined in the module :py:mod:`brainvisa.data.neuroDiskItems`. Use :py:func:`getDiskItemType` or :py:func:`getAllDiskItemTypes` to retrieve types. To check if a type is a sub-type of another, use :py:meth:`a_type.isA(another_type) <DiskItemType.isA>`.

  .. _T1MRI_inheritance:

  .. figure:: images/T1_MRI_inheritance.png
    :align: center

    Example: Inheritance graph of the **T1 MRI** type


Hierarchies
-----------

A hierarchy in *BrainVisa* describes the organization of data in the database file system. Thanks to this description, the name and place of a file allows to guess its type and some information about it, as for example the *center*, *subject* or *acquisition* attributes associated to this data. It also makes it possible to write data in the database using the same rules, so the information can be retrieved when the data is reloaded later.

Hierarchy files are in the ``brainvisa/hierarchies`` directory or in the ``hierarchies`` directory of a toolbox (See :ref:`toolboxes`). *BrainVisa* can use several hierarchies whose files are grouped in a directory named as the hierarchy. *BrainVisa* comes with three hierarchies: ``brainvisa-<version>``, ``flat`` and ``shared``. As for type files, hierarchy files are written in Python and information is generally spread across several files.

.. currentmodule:: brainvisa.data.fileSystemOntology

Syntax of hierarchy files
+++++++++++++++++++++++++

::

  hierarchy=(<ScannerRuleBuilder>+)

``<ScannerRuleBuilder>`` can be:

::

  SetAttr(<attribute name>, <value>)
  SetWeakAttr(<attribute name>, <value>) # associate this attribute with this value to the parent item.
  SetType(<type name>) # set the type of the parent item. This type must be defined in types files.
  SetContent(<pattern item>, [<ScannerRuleBuilder>]...) # describes the content of the parent item, which then must be a directory.
  SetFileNameAttribute(<attribute name>)
  SetFileNameStrongAttribute(<attribute name>)
  SetDefaultAttributeValue(<attribute name>, <value>) # associate a default value to an attribute
  SetPriority(<value>) # associate a priority to the rule, it helps *BrainVisa* to choose a rule if several match. The rule with highest priority will be used.
  SetPriorityOffset([+-]<value>)
  SetFormats(<formats list>)

The :py:class:`ScannerRuleBuilder` class and derived classes are defined in :py:mod:`brainvisa.data.fileSystemOntology`.


Example
+++++++

::

  hierarchy = (
      SetWeakAttr('database', '%f'), # the database directory item will have an attribute "database" with the directory name as value
      SetContent( # describes the content of the database directory
          'scripts', SetContent('*', SetType('Script')), # describes a directory named "scripts" that contains files of type "Script".
          '*', SetType('Database Cache file'), # the database directory contains files of type "Database Cache file"
          '{center}', SetFileNameStrongAttribute('center'), SetType('Center'), # a directory whose name becomes the value of center attribute for any items below
          SetContent(
              '{subject}', SetFileNameStrongAttribute('subject'), SetType('Subject'), # a directory whose name becomes the value of subject attribute
                  SetContent(
                      ...
                ),
            ),
        ),
  )


Links between hierarchy files
+++++++++++++++++++++++++++++

A hierarchy description is spread across several files. Only one file defines the value of a hierarchy variable which describes the organization of the database directory.

The other files can add information using the functions :py:func:`insert` and :py:func:`insertFirst`. These functions enable to add rules in the content of a previously described directory.

::

  include('base')

  allKindsOfRefAndTrans = (
      '*', SetType('Referential'),
      '*', SetType('Transformation matrix'),
  )

  insertFirst('{center}/{subject}',
      'registration', SetType('Registration Directory'),
      SetContent(*allKindsOfRefAndTrans),
  )

In this example, the call to :py:func:`insertFirst` adds information about subject directory described in ``base.py``: it can contain a directory named ``registration`` that contains referential and transformation files.

It is also possible to add rules in the root directory of the database. To so, use :py:func:`insert("", ...) <insert>`.

**Example** (from the ``shared`` hierarchy in *Morphologist* toolbox):

::

  include('base')

  insert('',
      'anatomical_templates', SetContent(
          'MNI152_T1_1mm', SetType('anatomical Template'),
          SetWeakAttr('normalized', 'yes', 'skull_stripped', 'no',
              'Size', '1 mm', 'referential', '49e6b349-b115-211a-c8b9-20d0ece9846d',),))


Processes
=========

.. currentmodule:: brainvisa.processes

A process is described in a Python file in the directory ``brainvisa/processes`` or in the processes directory of a toolbox (See :ref:`toolboxes`), which may be divided into subdirectories to organize the processes. Each process file is read at *BrainVisa* start and used to create a class derived from the :py:class:`Process` class, or more precisely from the :py:class:`NewProcess` class, defined in :py:mod:`brainvisa.processes`.
To retrieve a particular *BrainVisa* process, use the function :py:func:`getProcess(\<process name or id\>) <getProcess>`. The name is the one defined in the process script. The id is the script filename without extension.

The Python script contains :

* imports of Python modules used in the script. It must import at least :py:mod:`brainvisa.processes` *BrainVisa* file:

  ::

    from brainvisa.processes import *

* a declarative part: some variables initialization to set process :py:attr:`name <NewProcess.name>`, :py:attr:`category <NewProcess.category>`, :py:attr:`visibility level <NewProcess.userLevel>`, parameters...

* :py:meth:`initialization <Parameterized.initialization>`, :py:meth:`validation <Process.validation>` and :py:meth:`execution <Process.execution>` methods


Declarative part
----------------

Name
++++

::

  name = string

The string defines the process english name. This name will appear in *BrainVisa* interface, possibly after a translation, see :ref:`translation`.


Category
++++++++

::

  category = string

The string defines the english name of the process category. In *BrainVisa* interface, processes are grouped by category, it is useful to organize processes. As processes names, categories names may be translated.

**Optional**: if this attribute is missing, *BrainVisa* will set it to the parent directory path relative to ``brainvisa/processes``. For example, the process ``p1`` which Python script is ``brainvisa/processes/c1/c2/p1.py`` will have ``"c1/c2"`` as category.


Visibility level
++++++++++++++++

::

  userLevel = integer

This attribute defines the minimum user level required to see the process in *BrainVisa* interface. If the user level, defined in the preferences is lower than the process visibility level, the process will be hidden. **Warning: this level does not limit process execution, a hidden process can be executed yet, through another process for example.

**Optional**: The default visibility level is 0. The process is visible for all users.


Window maximized state
++++++++++++++++++++++

::

  showMaximized = boolean

This attribute indicates if the process window is maximized or not.

**Optional**: The default maximized state is set to false.


.. _roles:

Role
----

::

  roles = (role, ...)
  role <- viewer | editor | converter | importer

When a process defines one or more pre-defined roles, it can be used automatically by *BrainVisa*.

* Viewer

  A viewer is called when the user asks to see a data. Viewers are indexed by the type and format of data that they enable to display. To retrieve the viewer available for a specific data, use :py:func:`getViewer(data[, enableConversion=1]) <getViewer>`. This function is defined in :py:mod:`brainvisa.processes`.

* Converter

  A converter is called automatically when the user gives input or output process parameters that are not in a format supported by the process. A converter must have two parameters: the source and destination data. Converters are indexed by destination type and format and by source type and format. To retrieve a converter, use :py:func:`getConverter(source, destination) <getConverter>`, or ::py:func:`getConvertersTo(destination) <getConvertersTo>` to get all possible converters for a destination data, or :py:func:`getConvertersFrom(source) <getConvertersFrom>` to get all possible converters for a source data.

* Editor

  An editor is used when the user asks to edit a data. An editor has one parameter: the data to edit. Editors are indexed by data type and format. To retrieve an editor, use :py:func:`getDataEditor(source[, enableConversion=1]) <getDataEditor>`.

* Importer

  An importer is a process designed to import some data in the database. It is used mainly by a generic importer process to choose a specific importation process according to the data type.  An importer must have one parameter: the source data. Importers are indexed by destintation data type. To retrieve an importer, use :py:func:`getImporter(dataType) <getImporter>`.


Signature
+++++++++

Signature attribute defines input and output parameters of the process.

.. currentmodule:: brainvisa.data.neuroData

::

  signature = Signature(parameter_list)
  parameter_list <- parameter_name, parameter_type, ...
  parameter_name <- identifier (see below)
  parameter_type <- Parameter object (see below)

Each couple *parameter_name, parameter_type* defines a parameter. The parameter name is a string which must also be a possible Python identifier, so it contains only letters (uppercase or lowerrcase), digits or underscore character. Moreover some Python reserved word are forbidden (*and, assert, break, class, continue, def, del, elif, else, except, exec, finally, for, from, global, if, import, in, print, is, lambda, not ,or , pass, raise, return, try, why*). The parameter type is an instance of :py:class:`Parameter` class and indicates the supported value type for this parameter. This class is defined in :py:mod:`brainvisa.data.neuroData` with several derived classes.

To create an instance, you can use one of the following constructors:

* :py:func:`String`: the parameter value is a string.
* :py:func:`Number`: the parameter value is an integer or floatting point number.
* :py:func:`Integer`: the parameter value is an integer number.
* :py:func:`Float`: the parameter value is a float number.
* :py:func:`Choice`: the parameter value is choosen among a list of values given in the constructor's parameters (see below :ref:`choice`).
* :py:func:`Boolean`: the parameter has two possible values: 0 (false) and 1 (true). This object is equivalent to :py:func:`Choice(('true', 1), ('false', 0)) <Choice>`.
* :py:func:`Point`, :py:func:`Point2D`, :py:func:`Point3D`: the parameter represents the coordinates of a point.
* :py:func:`ListOfVector`: a list of vectors of numbers.
* :py:func:`Matrix`: a matrix of numbers.
* :py:func:`ListOf`: a list of Parameters.
* :py:class:`ReadDiskItem <brainvisa.data.readdiskitem.ReadDiskItem>`: the parameter value is a :py:class:`DiskItem <brainvisa.data.neuroDiskItems.DiskItem>` object and represents one or several readeable files (see below :ref:`readDiskItem`).
* :py:class:`WriteDiskItem <brainvisa.data.writediskitem.WriteDiskItem>`: the parameter value is a :py:class:`DiskItem <brainvisa.data.neuroDiskItems.DiskItem>` object and represents one or several writeable files (see below :ref:`writeDiskItem`).

**Example**: Here is the signature of a thresholding process. *input* is the input image, *output* is the output image. *threshold* is the threshold value and *method* enables to choose the thresholding method.

::

  signature = Signature(
      'input', ReadDiskItem("Volume 4D", ['GIS Image', 'VIDA image']),
      'output', WriteDiskItem('Volume 4D', 'GIS Image'),
      'threshold', Number(),
      'method', Choice('gt', 'ge', 'lt', 'le')
  )

Some of these parameter types will be detailled below.

.. _parameter:

Parameter
#########

Some attributes are common to all parameters:

* *mandatory*: indicates if the parameter must have a value or not, default is True.
* *userLevel*: indicates the minimum userLevel needed to see this parameter. Default is 0.
* *databaseUserLevel*: Indicates the minimum userLevel needed to allow database selection for this parameter (useful only for diskitems).
* *browseUserLevel*: Indicates the minimum userLevel needed to allow filesystem selection for this parameter (useful only for diskitems).


.. _choice:

Choice
######

**Syntax**

::

  Choice(choice_list)
  choice_list <- choice_item, ...
  choice_item <- value
  choice_item <- (label, value)

A :py:class:`Choice` parameter allows the user to choose a value among a set of possible values. This set is given as parameter to the constructor. Each value is associated to a label, which is the string shown in the graphical interface, possibly after a translation. That's why a choice item can be a couple *(label, value)*. When a choice item is a simple value, the label will be the string representation of the value (``label = str(value)``).

**Examples**

In the following example, the user can choose a number among three.

::

  Choice(1, 2, 3)

The following example associates a label to each number.

::

  Choice(('first', 1), ('second', 2), ('third', 3))

.. _readDiskItem:

ReadDiskItem
############

.. currentmodule:: brainvisa.data.readdiskitem

The :py:class:`ReadDiskItem` class is defined in :py:mod:`brainvisa.data.readdiskitem`.

**Syntax**

::

  ReadDiskItem(file_type_name, formats [, required_attributes, enableConversion=1, ignoreAttributes=0])
  formats <- format_name
  formats <- [format_name, ...]
  required_attributes <- {name: value, ...}

The value of this parameter is a readable **DiskItem**. This parameter type uses *BrainVisa* data organization (see :ref:`data`) to select possible files.

*file_type_name* enables to select files of a specific type, that is to say **DiskItem** objects whose type is either ``file_name_type`` or a derived type.

The *formats* list gives the exhaustive list of accepted formats for this parameter. But if there are some converters (see :ref:`roles`) from other formats to one of the accepted formats, they will be accepted too because *BrainVisa* can automatically convert the parameter (if *enableConversion* value is *1*, which is the default).

*required_attributes* enables to add some conditions on the parameter value: it will have to match the given attributes value.

.. warning::

  The type and formats given in parameters of :py:class:`ReadDiskItem` constructor must have been defined in *BrainVisa* types and hierarchies files.

This method eases file selection by showing the user only files that matches type and format required for this parameter. It also enables *BrainVisa* to automatically fill some parameters values. The :py:class:`ReadDiskItem` class has methods to search matching diskitems in *BrainVisa* databases:

* :py:meth:`ReadDiskItem.findItems(\<database directory diskitem\>, \<attributes\>) <ReadDiskItem.findItems>`: this method returns a list of diskitems that exist in that database and match type, format and required attributes of the parameter. It is possible to specify additional attributes in the method parameters. Found items will have the selected value for these attributes if they have the attribute, but these attributes are not mandatory. That's the difference with the required attributes set in the constructor.

* :py:meth:`ReadDiskItem.findValues(\<value\>) <ReadDiskItem.findValues>`: this method searches diskitems matching the value in parameter. This value can be a diskitem, a filename, a dictionary of attributes.

* :py:meth:`ReadDiskItem.findValue(\<value\>) <ReadDiskItem.findValue>`:  this method returns the best among possible value, that is to say with the more common attributes, highest priority. If there is an ambiguity, it returns *None*.

**Examples:**

::

  ReadDiskItem('Volume 3D', ['GIS Image', 'NIFTI-1 image'])
  ReadDiskItem('Cortical folds graph', 'Graph', requiredAttributes={'labelled': 'No', 'side': 'left'})

In the first example, the parameter will accept only a file whose type is 3D Volume and format is either *GIS image* or *NIFTI-1 image*, or a format that can be converted to *GIS* or *NIFTI-1 image*. These types and formats must have been defined first.

In the second example, the parameter value type must be *"Cortical folds graph"*, its format must be *"Graph"*. The required attributes add some conditions: the graph is not labelled and represents the left hemisphere.


.. _writeDiskItem:

WriteDiskItem
#############

::

  WriteDiskItem(file_type_name, formats [, required_attributes={}, exactType=0, ignoreAttributes=0])
  formats <- format_name
  formats <- [format_name, ...]

This parameter type is very close to <classname>ReadDiskItem</classname> (<classname>WriteDiskItem</classname> derives from <classname>ReadDiskItem</classname>), but it accepts writable files. That is to say, it accepts not only files that are accepted by a <classname>ReadDiskItem</classname> but also files that doesn't exist yet.
It has the same search methods as the <classname>ReadDiskItem</classname> class but these methods generate diskitems that may not exist yet, using data ontology information.
</para>
</sect3>
</sect2>
</sect1>

      <sect1>
        <title>Functions</title>
        <para>
          Some process functions can be defined in the script: validation, initialization and execution functions.
        </para>
        <sect2>
          <title>Validation</title>
          <para>
            <programlisting>
def validation():
  <emphasis>function_body</emphasis>
  if &lt;condition&gt;:
    raise ValidationError( "error message" )
            </programlisting>
            This function is executed at *BrainVisa* startup when the process is loaded. It checks some conditions for the process to be available. For example, the presence of modules, programs needed by the process. If the process is not available in the current context, the validation function should raise an exception.
            When the validation fails, the process is not available, it is shown disabled in *BrainVisa* interface. Each validation error is reported in *BrainVisa* log.
          </para>
        </sect2>
        <sect2>
          <title>Initialization</title>
          <para>
          <programlisting>
def initialization( self ):
  <emphasis>function_body</emphasis>
          </programlisting>
          This method is called when a new instance of the process is created. It is used to initialize parameters, set some parameters as optional and define links between parameters.
          The self parameter represents the process (and is an instance of <classname>Process</classname> class).
          </para>
          <para>
            **To  initialize parameters values**:
          <programlisting>
self.<emphasis>parameter_name</emphasis> = <emphasis>value</emphasis>
          </programlisting>
          Each parameter defined in the signature correspond to an attribute of the process object.
        </para>
        <para>
          **To set one or several parameters as optional**:
        <programlisting>
self.setOptional( <emphasis>parameter_name</emphasis> )
        </programlisting>
        The user does not need to fill these parameters. Other parameters are mandatory, if the user doesn't fill them, *BrainVisa* will not execute the process and will show an error message.
        </para>
        <para>
          **To link a parameter value to another parameter**:
        <programlisting>
self.linkParameters( destination, sources [, function] )
self.addLink( destination, sources [, function] )
        </programlisting>

        The function <function>linkParameters</function> is used for the links inside a process. To define links between steps of a pipeline, the function <function>addLink</function> must be used.
      </para>
      <sect3><title>linkParameters</title>
      <para>
        The parameter <emphasis>destination</emphasis> value is linked to <emphasis>sources</emphasis>, which can be either one parameter or a list of parameters. If a value changes in <emphasis>sources</emphasis>, *BrainVisa* updates <emphasis>destination</emphasis>, if it still has its default value. If the destination parameter has been modified by the user, it has no more a default value and is not modified by such a link.
      </para>
      <para>
        The optional argument <emphasis>function</emphasis> is a function that is called when the link is activated. The value returned by this function is used to set the destination parameter value. If there is no function, the source parameter is used directly. Anyway, the value of <emphasis>destination</emphasis> is evaluated with <function>ReadDiskItem.findValue(value)</function>. The signature of the function is: <function>function(process, process) -&gt; value</function>.
      </para>
      </sect3>
      <sect3><title>addLink</title>
      <para>
        This function do quite the same thing that the <function>linkParameters</function> function except that the link is always activated when the sources change, even if destination has no more a default value. That's why this link can be used as an equality link between parameters of two different steps of a pipeline. For example, this function is used to define a link between the output of one step and the input of the next step.
      </para>
      <para>
        Using the <function>addLink</function> method, the argument <emphasis>function</emphasis> is mandatory if there are several sources parameters: it takes as arguments the sources parameters and returns the value that must be used to find the destination parameter value: <function>addLink(process, **sources) -&gt; value</function>.
      </para>
    </sect3>
        <para>This is very useful to help the user fill in the process parameters. With the links correctly defined, the user will enter the first input parameter and BrainVISA will try to complete all other parameters automatically, trying to find values in the database for the other parameters using attributes of the first parameter. The default *BrainVisa* link mechanism assumes that parameters have common attributes, for example the protocol, subject, acquisition, which is generally the case.
        </para>
        </sect2>
        <sect2>
          <title>Execution</title>
          <para>
            This function is called when the process is started. All mandatory parameters must be set. This function is written in Python.
            <programlisting>
def execution(self, context):
  <emphasis>function_body</emphasis>
            </programlisting>
          </para>
          <para>
            The <emphasis>self</emphasis> parameter of this function represents the process. It is mainly used to access parameters values:  <emphasis>self.&lt;parameter_name&gt;</emphasis>.
          </para>
          <para>The <emphasis>context</emphasis> object given as argument reprensents the execution context of the process. </para>
          <para>Indeed, a process can be started in different contexts:
          <itemizedlist>
            <listitem>The user starts the process by clicking on the <emphasis>Run</emphasis> button in the graphical interface.</listitem>
            <listitem>The process is started via a script. It is possible to run brainvisa in batch mode (without any graphical interface) and to run a process via a python function: <emphasis>brainvisa.processes.defaultContext().runProcess(...)</emphasis>.</listitem>
            <listitem>The process is a converter, so it can be run automatically by *BrainVisa* when a conversion is needed for another process parameters.</listitem>
            <listitem>The process is a viewer or an editor, it is run when the user clicks on the corresponding icon to view &eye; or edit &pencil; another process parameter. </listitem>
          </itemizedlist>
        </para>
        <sect3><title>Execution context</title>
          <para>
            The <emphasis>context</emphasis> object offers several useful functions to interact with BrainVISA and to call system commands. Here are these functions:
          <itemizedlist>
          <listitem>write, warning, error: prints a message, either in the graphical process window (in GUI mode) or in the terminal (in batch mode).</listitem>
          <listitem>log: writes a message in the *BrainVisa* log file.</listitem>
          <listitem>ask, dialog: asks a question to the user.</listitem>
          <listitem>temporary: creates a temporary file.</listitem>
          <listitem>system: calls a system command.</listitem>
          <listitem>runProcess: runs a *BrainVisa* process.</listitem>
          <listitem>checkInterruption: defines a breakpoint.</listitem>
          </itemizedlist>
          </para>
          <sect4 id="context_write"><title>write</title>
          <para>
            <programlisting>
context.write(message [, message, ..., linebreak=1])
example: context.write("Computing threshold of &lt;i&gt;", self.input.name, "&lt;/i&gt;..." )
</programlisting>
            This method is used to print information messages during the process execution. All arguments are converted into strings and joined to form the message. This message may contain HTML tags for an improved display. The result vary according to the context. If the process is run via its graphical interface, the message is displayed in the process window. If the process is run via a script, the message is displayed in the terminal. The message can also be ignored if the process is called automatically by brainvisa or another process.
          </para>
        </sect4>
        <sect4><title>warning</title>
          <para>
            <programlisting>
context.warning(message [, message, ...])
            </programlisting>
            This method is used to print a warning message. This function adds some HTML tags to change the appearance of the message and calls the <link linkend="context_write">write</link> function.
          </para>
        </sect4>
        <sect4><title>error</title>
          <para>
            <programlisting>context.error(message [, message, ...])</programlisting>
            This method is used to print an error message. Like the above function, it adds some HTML tags to change the appearance of the message and calls <link linkend="context_write">write</link> function.
          </para>
        </sect4>
        <sect4><title>log</title>
          <para>
            <programlisting>context.log(what, when=None, html='', children=[], icon=None)</programlisting>
            This method is used to add a message to *BrainVisa* log. The first parameter <emphasis>what</emphasis> is the name of the entry in the log, the message to write is in the <emphasis>html</emphasis> parameter.
          </para>
        </sect4>
        <sect4><title>ask</title>
          <para>
            <programlisting>
context.ask( message, choices [, modal=1] )
choices &lt;- value, ...</programlisting>
This method asks a question to the user. The message is displayed and the user is invited to choose a value among the propositions. The method returns the index of the chosen value, beginning by 0. If the answer is not valid, the returned value is -1. Sometimes, when the process is called automatically (in batch mode), these calls to context.ask are ignored and return directly -1 without asking question.
</para>
<para>
<emphasis>Example</emphasis>
<programlisting>
if context.ask( 'Is the result ok ?', 'yes', 'no') == 1:
  try_again()
</programlisting>
</para>
        </sect4>
        <sect4><title>dialog</title>
          <para>
            <programlisting>
dialog=context.dialog( parentOrModal, message, signature, *buttons )
              </programlisting>
            This method is available only in a graphical context. Like ask, it is used to ask a question to the user, but the dialog interface is customisable. It is possible to add a signature to the dialog: fields that the user has to fill in.
          </para>
          <para>
            <emphasis>Example</emphasis>
            <programlisting>
dial = context.dialog( 1, 'Enter a value', Signature( 'param', Number() ), _t_( 'OK' ), _t_( 'Cancel' ) )
dial.setValue( 'param', 0 )
r = dial.call()
if r == 0:
v=dial.getValue( 'param' )
            </programlisting>
          </para>
        </sect4>
        <sect4><title>temporary</title>
          <para>
            <programlisting>
context.temporary( format )
context.temporary( format, type )
            </programlisting>
            This method enables to get a temporary DiskItem. The argument format is the temporary data format. The optional argument type is the data type. It generates one or several unique filenames (according to the format) in the temporary directory of *BrainVisa* (it can be changed in *BrainVisa* configuration). No file is created by this function. The process has to create it. The temporary files are deleted automatically when the temporary diskitem returned by the function is no later used.
          </para>
          <para>
            <emphasis>Example</emphasis>
            <programlisting>
tmp = context.temporary( 'GIS image' )
context.runProcess( 'threshold', self.input, tmp, self.threshold )
tmp2 = context.temporary( 'GIS image' )
context.system( 'erosion', '-i', tmp.fullPath(), '-o', tmp2.fullPath(), '-s', self.size )
del tmp
            </programlisting>
            In this example, a temporary data in GIS format is created and it is used to store the output of the process threshold. Then a new temporary data is created to store the output of a command line. At the end, the variable tmp is deleted, so the temporary data is no more referenced and the corresponding files are deleted.
          </para>
        </sect4>
        <sect4><title>system</title>
          <para>
            <programlisting>
context.system( command )
context.system(commandName, parameter [, parameter, ...])
            </programlisting>
            This function is used to call system commands. It is very similar to functions like os.system in Python and system in C. The main difference is the management of messages sent on standard output. These messages are intercepted and reported in *BrainVisa* interface according to the current execution context.
            Moreover, a command  started using this function can be interrupted via the <emphasis>Interrupt</emphasis> button in the interface which is not the case if the python os.system function is used directly.
          </para>
          <para>
            If the command is given as one argument, it is converted to a string and passed to the system. If there are several arguments, each argument is converted to a string, surrounded by simple quotes and all elements are joined, separated by spaces. The resulting command is passed to the system. The second method is recommended because the usage of quotes enables to pass arguments that contain spaces.
            The function returns the value returned by the system command.
          </para>
          <para>
            <emphasis>Example</emphasis>
            <programlisting>
arg1 = 'x'
arg2 = 'y z'
context.system( 'command ' + arg1 + ' ' + arg2 )
context.system( 'command', arg1, arg2 )
            </programlisting>
            The first call generates the command <command>command x y z</command> which calls the commands with 3 parameters. The second call generates the command <command>'command' 'x' 'y z'</command> which calls the command with two parameters.
          </para>
        </sect4>
        <sect4><title>runProcess</title>
          <para>
            <programlisting>
context.runProcess( process, value_list, named_value_list )
value_list &lt;- value, ...
named_value_list &lt;- argument_name = value, ...
            </programlisting>
          It is possible to call a sub-process in the current process by calling context.runProcess. The first argument is the process identifier, which is either the filename wihtout extension of the process or its english name. The other arguments are the values of the process parameters. All mandatory argument must have a value. The function returns the value returned by the sub-process execution method.

          </para>
          <para>
            <emphasis>Example</emphasis>
            <programlisting>
context.runProcess( 'do_something', self.input, self.output, value = 3.14 )
            </programlisting>In this example, the process do_something is called with self.input as the first paramter value, self.ouput as the second parameter value and 3.14 to the parameter named value.
          </para>
        </sect4>

        <sect4><title>checkInterruption</title>
          <para>
            <programlisting>
context.checkInterruption( )
            </programlisting>
            This function is used to define breakpoints. When the process execution reach a breakpoint, the user can interrupt the process. There are 4 types of breakpoints automatically added:
            <itemizedlist>
              <listitem>before each system call (context.system)</listitem>
              <listitem>after each system call (context.system)</listitem>
              <listitem>before each sub-process call (context.runProcess)</listitem>
              <listitem>after each sub-process call (context.runProcess)</listitem>
            </itemizedlist>
            To allow the user to interrupt the process at another place, you have to use the function context.checkInterruption. If the user has clicked on the <emphasis>Interrupt</emphasis> button while the process runs, it will stop when reaching the checkInterruption point.
          </para>
        </sect4>
       </sect3>
        </sect2>
      </sect1>

      <sect1>
        <title>Pipeline</title>
        <para>
          A pipeline is a particular process that is a combination of several other processes. It describes through a sort of graph the processes that it contains and the links between them. Pipelines are convenient for users because they use the parameters link system over several processes and chain their execution, so it requires less user interaction and is quicker to run.
        </para>
          <sect1><title>Writing a pipeline</title>
            <sect2><title>Execution graph</title>
            <para>
              A pipeline file is very similar to a process file, except in the initialization function where you have to define the execution graph of the pipeline. This is done by calling:
              <programlisting>self.setExecutionNode( eNode )
eNode &lt;- SerialExecutionNode | ProcessExecutionNode | ParallelExecutionNode | SelectionExecutionNode</programlisting>
              The different types of execution nodes are detailled below.
            </para>
            <sect3><title>SerialExecutionNode</title>
              <para>It represents a series of processes that will be executed serially. It is generally the main node of a pipeline. It is used when the results of one step are needed to go on with next step.</para>
              <para><programlisting>SerialExecutionNode(name='', optional = False, selected = True, guiOnly = False, parameterized = None, stopOnError=True)
Example (first node of a pipeline):  eNode = SerialExecutionNode( self.name, parameterized=self )</programlisting></para>
<para>
To add the different steps, use the method: <programlisting>&lt;serial execution node&gt;.addChild(&lt;name&gt;, &lt;execution node&gt;)</programlisting>
              </para>
            </sect3>
            <sect3><title>ParallelExecutionNode</title>
              <para>As SerialExecutionNode, it has children, but they may be executed in parallel.</para>
              <para><programlisting>ParallelExecutionNode(name='', optional = False, selected = True, guiOnly = False, parameterized = None, stopOnError=True)
Example:    eNode = ParallelExecutionNode( 'SulciRecognition', optional = 1, selected=0  )
                </programlisting>
              </para>
            </sect3>
            <sect3><title>ProcessExecutionNode</title>
              <para>It represents a leaf of the execution graph, this node cannot have children. It only calls one process, but obviously this process can be itself a pipeline. Any simple process has this type of execution node.</para>
              <para><programlisting>ProcessExecutionNode( self, process,, optional = False, selected = True, guiOnly = False )
Example:    eNode.addChild( 'ConvertDatabase', ProcessExecutionNode( 'convertDatabase', optional = 1 ) )
                </programlisting>
              </para>
            </sect3>
            <sect3><title>SelectionExecutionNode</title>
              <para>It reprensents a choice between several alternative paths. The user will select the process he wants to execute. </para>
              <para><programlisting>SelectionExecutionNode(name='', optional = False, selected = True, guiOnly = False, parameterized = None, stopOnError=True)
Example:      eNode = SelectionExecutionNode( self.name, parameterized = self )
eNode.addChild( 'BrainSegmentation05',
ProcessExecutionNode( 'BrainSegmentation', selected = 0 ) )
eNode.addChild( 'BrainSegmentation04',
ProcessExecutionNode( 'VipGetBrain', selected = 1 ) )
                </programlisting>
              </para>
            </sect3>
            <sect3><title>Example of serial pipeline composed of 3 processes</title>
            <para>
              <programlisting> eNode = SerialExecutionNode( self.name, parameterized=self )

eNode.addChild( 'ConvertDatabase',
ProcessExecutionNode( 'convertDatabase', optional = 1 ) )

eNode.addChild( 'CheckDatabase',
ProcessExecutionNode( 'checkDatabase',
optional = 1 ) )

eNode.addChild( 'CleanDatabase',
ProcessExecutionNode( 'cleanDatabase',
optional = 1 ) )
</programlisting>
            </para>
            </sect3>
          </sect2>
          <sect2><title>Links between steps</title>
            <para>Generally, the different steps of a pipeline are linked. For example, the output of the first process is the input of the second process. These links must be explicitely defined. So *BrainVisa* can automatically fill in parameters of the different processes that composed the pipeline. </para>
            <para><programlisting>&lt;execution node&gt;.addLink( &lt;destination parameter&gt;, &lt;source parameter&gt; )
#Example:
eNode.addLink( 'ConvertDatabase.database', 'database' )
eNode.addLink( 'database', 'ConvertDatabase.database' )
# This is equivalent to:
eNode.addDoubleLink('ConvertDatabase.database', 'database')
</programlisting>
</para><para>
In this example, the parameter database in the pipeline and in the sub-process ConvertDatabase are linked in the 2 directions. So if the user changes the parameter value in the main process interface or in the sub-process interface, the value will be reported in the linked parameter.</para>
<warning>Sometimes, it can be necessary to remove existing links in a process when it is included in a pipeline to avoid having two incompatible links towards the same parameter.</warning>
 <figure>
   <title>Example of a pipeline where links should be removed</title>
   <mediaobject>
     <imageobject><imagedata width="200" align="center" fileref="&DIR_IMG;/pipeline_links.png"/></imageobject>
   </mediaobject>
 </figure>
 <para>In this example, when including the process A and the process B in a pipeline, new links are created to assess that A.Output1 is equal to B.Input1 and A.Output2 is equal to B.Input2. With these pipeline links, B.Input2 becomes linked to 2 parameters: A.Output2 and B.Input1. So, if the link between Input1 and Input2 in process B is not removed, the value of Input2 will be computed 2 times. But the second time (with the link in process B), the value of Input2 cannot be found because the file does not exist yet as it is an output of the pipeline. WriteDiskItems can generate new filenames for none existing files but not ReadDiskItems.</para>
 <para>In this case, this link should be remove in process B when creating the pipeline:</para>
<programlisting>
eNode.addChild("processA", ProcessExecutionNode("processA"))
eNode.addChild("processB", ProcessExecutionNode("processB"))
eNode.addDoubleLink("processA.Output1", "processB.Input1")
eNode.addDoubleLink("processA.Output2", "processB.Input1")
eNode.processB.removeLink("Input2", "Input1")
</programlisting>
          </sect2>

          </sect1>
      </sect1>
      <sect1><title>Graphical user interface</title>
        <para>A graphical user interface is automatically generated by *BrainVisa* for each process. It allows the user to fill in the process's parameters via a form, to run and iterate the process via buttons and to see output log via a text panel. This default interface can be customized in several ways to better fit the user needs. This section will give an overview of the available GUI customizations.</para>
            <sect2><title>Replacing the buttons</title>
              <para>By default, two buttons are displayed in a process window: <emphasis>Execute</emphasis> to run the process and <emphasis>Iterate</emphasis> to repeat the process on a set of data. It is possible to replace these default buttons with a custom interface by redefining the method <emphasis>inlineGUI</emphasis>. </para>
              <para><programlisting>def inlineGUI( self, values, context, parent ):
  widget=<emphasis>Code to create the Qt widget that will replace the buttons</emphasis>
  return widget
</programlisting>The widget must have the parent widget given in parameters as a parent.</para>
<para>**Example** (from <emphasis>ROI drawing</emphasis> process in toolbox <emphasis>Tools -&gt; roi</emphasis>)
  <programlisting>def inlineGUI( self, values, context, parent, externalRunButton=False ):
    btn = QPushButton( _t_( 'Show' ), parent )
    btn.connect( btn, SIGNAL( 'clicked()' ), context._runButton )
    return btn
 </programlisting>
 <figure>
   <title>ROI drawing process</title>
   <mediaobject>
     <imageobject><imagedata width="400" align="center" fileref="&DIR_IMG;/roi_drawing.png"/></imageobject>
   </mediaobject>
 </figure>

 The default buttons are replaced with one button labelled "Show". This button has the same role as the <emphasis>Execute</emphasis> button because its <emphasis>clicked</emphasis> signal is connected to the <emphasis>_runButton</emphasis> callback function, that is connected to <emphasis>Execute</emphasis> button by default.
</para>
<para>The default GUI contains:
  <itemizedlist>
    <listitem>An <emphasis>Execute/Interrupt</emphasis> button whose click event is linked to the <emphasis>_runButton</emphasis> callback</listitem>
    <listitem>An <emphasis>Iterate</emphasis> button whose click event is linked to the <emphasis>_iterateButton</emphasis> callback</listitem>
    <listitem>If the process is an iteration, an <emphasis>Iterrupt current step</emphasis> button whose click event is linked to the <emphasis>_iterruptStepButton</emphasis> callback</listitem>
    <listitem>If parrallel execution is available, a <emphasis>Distribute</emphasis> button whose click event is linked to the <emphasis>_distributedButton</emphasis> callback</listitem>
  </itemizedlist>
  </para>
            </sect2>
            <sect2><title>Calling GUI functions</title>
        <para>Sometimes, you don't need to customize the process parameter interface but you want to
          use custom windows during process execution to interact with the user. Of course, it is
          possible to do so but you'll need to use a specific object to call GUI functions: the
          object returned by <emphasis role="italic"
            >brainvisa.processing.qt4gui.neuroProcessesGUI.mainThreadActions()</emphasis>. Indeed, the process execution
          function is always started in a new thread to avoid blocking the whole application during
          process execution. But graphical interface functions have to be called in the main thread
          where Qt event loop is running. The role of the mainThreadActions object is to enable
          passing actions to the main thread. </para>
        <para>The mainThreadActions object has two methods:
            <itemizedlist>
              <listitem>
                <para><emphasis role="italic">push( self, function, *args, **kwargs )</emphasis>:
                  adds a function with its parameters to the actions list. It will be executed as
                  soon as possible.</para>
              </listitem>
              <listitem>
                <para><emphasis role="italic">call( self, function, *args, **kwargs ) -&gt;
                    function call's result</emphasis>: sends the function call to be executed in the
                  Qt thread and wait for the result.</para>
              </listitem>
            </itemizedlist>
          </para>
        <para>**Example** (from <emphasis role="italic">Show Scalar
            Features</emphasis> process in toolbox <emphasis role="italic">Tools -&gt;
            viewers</emphasis>):
          <programlisting>from brainvisa.processing.qt4gui.neuroProcessesGUI import mainThreadActions
import brainvisa.data.qtgui.scalarFeaturesViewer as sfv

def execution( self, context ):
  data = readData( self.features.fullPath() )
  view = mainThreadActions().call( sfv.ScalarFeaturesViewer )
  mainThreadActions().push( view.setData, data )
  mainThreadActions().push( view.show )
  return view
          </programlisting>
          First, the <emphasis role="italic">call</emphasis> method of <emphasis role="italic"
            >mainThreadActions</emphasis> is called to create an instance of <emphasis role="italic"
            >sfv.ScalarFeaturesViewer</emphasis> widget. The <emphasis role="italic">call</emphasis>
          method waits for the call to be executed and returns the result: <emphasis role="italic"
            >view</emphasis>. The result can then be used in the rest of the execution function. As
          we don't need the result of the next functions, the <emphasis role="italic"
            >push</emphasis> method of the <emphasis role="italic">mainThreadActions</emphasis> can
          be used. </para>
              <figure>
                <title>Show scalar features process</title>
                <mediaobject>
                  <imageobject><imagedata width="800" align="center" fileref="&DIR_IMG;/show_scalar_features.png"/></imageobject>
                </mediaobject>
              </figure>

            </sect2>
            <sect2><title>Changing the whole process window</title>
        <para>In some case, you may need to customize the whole process interface and not use at all
          the default interface generated from the process's signature. It is possible to replace
          this default interface with a custom interface by redefining the method
            <emphasis>overrideGUI</emphasis>.</para>
        <para>
          <programlisting>def overrideGUI( self ):
  widget=<emphasis>Code to create the Qt widget that will replace the default interface of the process</emphasis>
  return widget</programlisting>
        </para>
            </sect2>
      <para>**Example** (from the <emphasis role="italic">Database
          browser</emphasis> process in <emphasis role="italic">Data Management</emphasis> toolbox
        ):<programlisting>from brainvisa.data.qtgui.hierarchyBrowser import HierarchyBrowser

def overrideGUI( self ):
  return HierarchyBrowser()</programlisting></para>
      <para>The HierarchyBrowser widget will be displayed when the process is opened instead of the
        default process window.</para>
        <figure>
          <title>Database browser process</title>
          <mediaobject>
            <imageobject><imagedata width="600" align="center" fileref="&DIR_IMG;/database_browser.png"/></imageobject>
          </mediaobject>
        </figure>

            <sect2><title>Creating a viewer</title>
        <para>Another way to add graphical features to *BrainVisa* is the creation of a viewer
          specialized for a type of data. A viewer is a special process that displays a view of the
          data given in parameters. At initialization, *BrainVisa* indexes all the viewers by type of
          data in order to call the appropriate viewer when a visualization of data is requested. </para>
        <para>The &eye; button in process parameters interface is linked to the viewer
          associated to the data type of the parameter. In <emphasis role="italic">Database
            browser</emphasis> process, the view command in contextual menu also calls the viewer
          associated to the data type of the current item.</para>
        <para>A lot of *BrainVisa* viewers use <emphasis role="italic">Anatomist</emphasis> to display
          neuroimaging data. These viewers uses the <emphasis role="italic">Pyanatomist</emphasis>
          API, a python API that enables to drive <emphasis role="italic">Anatomist</emphasis>
          application through python scripts. Refer to the <ulink url="#ana_training%pyanatomist"
            >programming part of Anatomist training</ulink>  to learn how to use it.</para>
        <para>**Example: Anatomist Show Volume**:
          <programlisting>from brainvisa.processes import *
from brainvisa.tools import aimsGlobals
from brainvisa import anatomist

name = 'Anatomist Show Volume'
roles = ('viewer',)
userLevel = 0

def validation():
  anatomist.validation()

signature = Signature( 'read', ReadDiskItem( '4D Volume', aimsGlobals.anatomistVolumeFormats ), )

def execution( self, context ):
  a = anatomist.Anatomist()
  return a.viewObject( self.read )
          </programlisting>
          </para>
          <para>
          This process will be used every time an item of type <emphasis role="italic">4D volume
          </emphasis>needs to be visualized. The process is considered as a viewer because
          it has the role viewer in roles attribute and because it has only one mandatory input
          parameter.</para>
          <warning>All <emphasis role="italic"
            >Anatomist</emphasis> objects and window that should not be deleted at the end of the
          process must be returned by the execution function. Indeed, by default any python object
          is deleted when there are not references on it anymore. If the objects are returned, they
          will remain visible until the viewer process is closed. </warning>
            </sect2>

      </sect1>
    </chapter>

---------------

.. _toolboxes:

.. _translation:

.. _writeDiskItem:

.. _data:

