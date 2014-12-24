
=====================
BrainVISA Axon manual
=====================

Introduction to *BrainVISA*
===========================

.. image:: images/brainvisa_large.png
  :width: 150

The purpose of this handbook is to provide the basic knowledge needed to start using *BrainVISA*. Practical aspects such as installation and hardware recommendations will be discussed, as well as the setup of *BrainVISA*.

What is *BrainVISA*
-------------------

*BrainVISA* results from collaborative work of methodologists in neuroimaging. The goal was to provide to potential users of the methodological results a unifying environment. This environment has been designed to address the following issues:

* Facilitate development, sharing and diffusion of heterogeneous neuroimaging software. The system takes into account that each software is developped independently and, therefore, can be implemented with its own programming language and can use its own data types and formats.

* Provide a system to organize, share and fusion multimodal data (e.g. aMRI, fMRI, dMRI, EEG/MEG, PET, etc.).

* Allow a unified and simplified usage of neuroimaging tools through a common graphical interface.

* Allow anyone to use and/or extend *BrainVISA* with his own tools. Therefore, *BrainVISA* is an open source project: http://brainvisa.info.


.. _fig_brainvisa_management:

.. figure:: images/brainvisa_management.png
  :align: center

  *BrainVISA* management of software and data

  (a) Classical Software and data management without *BrainVISA*. Each user is responsible of all the interactions between programs and data.

  (b) *BrainVISA* organization. Programs and data are organized by *BrainVISA* and can be accessed through a unified user interface.

In the neuroscience domain, there is no standard way to organize and manage various programs and heterogenuous data. Therefore, this work is done at the user level (`figure 1a <fig_brainvisa_management_>`_). As a result, each institute, each group or even each person can have a personal unique organization stategy (when they have one). It is therefore very difficult to share data between people using different organizations. Moreover, it is often a hard work to use different programs on the same data because it is necessary to manage several incompatibilities (unit conversion, file format, 3D referential, etc...). This work has to be done for each data and it can be a fastidious repetitive task.

*BrainVISA* has been designed not only to provide an organization system for programs and data, but also to free users from all the technical work required to combine different programs and data. *BrainVISA* architecture organizes programs through a set of modules and data through a database system. A unifiying graphical interface is provided to access programs and data (`figure 1b <fig_brainvisa_management_>`_).


Who developped BrainVISA
------------------------

*BrainVISA* was developed by a group of methodologists at the *IFR 49* (Institut Fédératif de Recherche). Their aim was to provide for potential users a range of methodological tools, via a relatively user-friendly unifying interface. In addition, this interface facilitates communication between the different groups of methodologists working in the various laboratories. This project was financed by the french ministry of Research, within the framework of an ACI (Action Concertée Incitative) in the telemedicine field. The first prototype was
developed by Yann Cointepas in 2000/2001. See:

  *Y. Cointepas, J.-F. Mangin, L. Garnero, J.-B. Poline, and H. Benali. BrainVISA: Software platform for visualization and analysis of multi-modality brain data. In Proc. 7th HBM, Brighton, United Kingdom, pages S98, 2001*.


What is provided with the *BrainVISA* package
---------------------------------------------

*BrainVISA* is a software platform that provides access to various analysis tools and enables to run one or more sequences of processes on a series of images. These processes are called up from specific libraries, or via command lines provided by different laboratories. These command lines therefore act as building blocks, which are used to create the tools assembly lines. *BrainVISA* comes with a range of different modules, for use in anatomical image processing, morphometry.

Other tools are provided by Anatomist, such as image viewing commands (fusion, display of graphs, etc.). Anatomist is a visualization and manipulation software used with images and structured objects such as sulci graphs (http://brainvisa.info). BrainVISA interacts with Anatomist in the management of a certain number of processes. Modules pertaining to functional image analysis or EEG-MEG analysis have also been implemented and are distributed as an additional toolbox (http://cogimage.dsi.cnrs.fr/logiciels/index.htm). It is perfectly possible to integrate your own processes or modules. All you need is a basic knowledge of computing and programming (Python language).


Quick start
-----------

.. |browse_write| image:: images/browse_write.png
.. |database_read| image:: images/database_read.png
.. |database_write| image:: images/database_write.png
.. |eye| image:: images/eye.png

Here is a summary of the main steps that you need to follow to start with BrainVISA:

* **Create a database** where all data written by BrainVISA will be stored: *BrainVISA menu -> Preferences -> Databases -> Add button*. It is strongly advisable to use a database to process data with BrainVISA. Indeed, some important features are not available when you are using data outside a database. More information about databases in the :ref:`Databases and ontology <database>` chapter.

* **Import raw data**: *Data Management toolbox -> import...* Choose the process according to the type of data. Select raw data with |browse_write|. Fill in database attributes using |database_write|. The process will copy data in BrainVISA database.

* **Process data**: Open a process, enter input parameters by selecting them in the database using |database_read|. BrainVISA automatically complete as many parameters as possible. Output data will be written in the database.

* **Visualize data** with |eye|

* **Iteration** of a process on several data with the iterate button in the process.


.. _installation:

Installation
============

Checking your computer
----------------------

Before installing *BrainVISA* on your computer, you need to check a few things:

* Your operating system and its version
* 1.5 Gb of free space
* 2 Gb of RAM. However, it should be noted that this depends on the size of the images you work with. 1 Gb is the minimum recommended value, and you may run into problems when dealing with large data such as diffusion-weighted images or MRI. If you are planning to buy a computer, we advise you to get one with at least 8 Go Mb of RAM.


The operating system
--------------------

BrainVISA has been developed as a cross-platform software, and thus can run on Linux, Windows and MacOS. For a more precise description of OS releases that have been tested, please refer to the web site: :web:`http://brainvisa.info/download.html <download.html>`

It is possible that your operating system and version are not mentioned in the supported systems table there. When you install a package, you may encounter a number of different problems. You can either update your system or compile the sources. To compile the sources, please refer to `the downoad section <download_>`_.


Recommended hardware
--------------------

The video card often comes up in questions about recommended hardware. Here are a few pointers:

* If you work with linux, 3D graphics generally have two sets of 3D drivers: open-source, community drivers, and proprietary drivers written by the company who build the hardware. Proprietary drivers do normally work better and are more optimized. But some open-source drivers now are OK in many situations. As of 2014 we generally use open-source drivers for AMD hardware, and proprietary drivers for NVidia hardware.

* If you encounter graphic display problems, please refer to http://brainvisa.info/forum.


.. download:

Downloads
---------

You can download ready-to-install binary packages. If the binary distribution does not work (for example, if your operating system is not compatible), you can download the sources for compilation via your working environment (see http://brainvisa.info/repository.html#use_brainvisa_sources for compilation instructions).

You can download the packages via the following link:

:web:`http://brainvisa.info/downloadpage.html <downloadpage.html>`


Installation
------------

Installation instructions are provided with the download instructions.


Using programs
--------------

Several programs are available: two important main software (BrainVISA and Anatomist), along with many command lines for the processing tools (Aims, Vip etc). All the programs are independent of each other. They are in the ``bin`` subfolder of the binary package.


Program: BrainVISA
++++++++++++++++++

To use BrainVISA, run the ``brainVISA`` (``brainvisa.bat`` on Windows) file by double clicking it via either a shortcut on the desktop or the ``bin`` folder.

Refer to this :ref:`appendix <helpcom>` to see the *brainvisa* command options, or enter one of the following command lines:

::

  brainvisa -h

or:

::

  brainvisa --help


Program: Anatomist
++++++++++++++++++

The Anatomist application is independent of BrainVISA. You can run Anatomist without running BrainVISA. Anatomist will be described in another handbook.

To use Anatomist, run the ``anatomist`` (``anatomist.bat`` on Windows) file by double clicking it via either a shortcut on the desktop or the ``bin`` folder.


Command lines
+++++++++++++

You can also launch ``Aims*.exe``, ``Vip*.exe`` or ``si*.exe`` command lines, such as ``AimsFileInfo``, independently of BrainVISA and Anatomist. To get information on a command, enter:

::

  <command_name> -h

You will find all the commands in the ``bin`` sub-directory or on the Web page: :documentation:`commands index <index_commands.html>`.

These commands are usable from a DOS terminal from the ``bin`` sub-directory of the BrainVISA package.

On Windows
##########

For instance, to use ``AimsFileInfo`` command via DOS terminal, follow the instrucions below:

#. Initiate a DOS terminal via the *Program -> Accessories -> Command prompt* menu.
#. Locate in ``bin`` sub-directory of the brainvisa package, and run the setu script ``bv_env.bat``

  ::

    C:\<brainvisa_dir>\bin\bv_env.bat

#. Launch the command:

  ::

    AimsFileInfo -i D:\data\image.ima

On Unix (Linux/Mac)
###################

* **Possibility 1:** To launch a program, for example ``anatomist``, enter the absolute pathname for the program:

  ::

    ~/<brainvisa_dir>/bin/anatomist

* **Possibility 2:** Source the setups script ``bv_env.sh`` in a bash terminal:

  ::

    . ~/<brainvisa_dir>/bin/bv_env.sh

(if you are using the csh or tcsh shell in your terminal, there is also a ``bv_env.csh`` script)

Then all the programs are available in the *PATH*: ``anatomist``, ``brainvisa``, ``AimsFileInfo`` and all others:

::

  anatomist


.. note::

  environment variables are initialized from each program. If you launch this line:

  ::

    ~/<brainvisa_dir>/bin/AimfileInfo

  all variables will be initialised and you can use them from any directory.


Uninstalling programs
+++++++++++++++++++++

The installation of the BrainVISA package does not modify the configuration of your system (no DLLs added, no changes to the registry, etc.).

To uninstall the BrainVISA package, delete the following items:

* The BrainVISA package folder.
* The folders ``.brainvisa`` and ``.anatomist`` are created when the programs are started.

  These folders contain user information, configuration files, template files, etc. ``.brainvisa`` and ``.anatomist`` folders are created for each user.

  These folders must therefore be deleted if you are sure you want to get rid of all the settings.

  On Windows, they are found in the user directory  (``C:\Documents and Settings\user_name``.

  On Unix, they are in the home directory ``*$HOME\user_name``.

.. warning::

  Sometimes users store their BrainVISA databases in the BrainVISA package folder. This is dangerous however, as, when you update your package (and therefore delete the previous one) you will also delete your database. Therefore, avoid storing your database in the installation package.


*BrainVISA* User interface
==========================

This chapter describes the various windows that can be found in BrainVISA graphical user interface.

General user interface
----------------------

The general user interface is BrainVISA main window that shows up when starting BrainVISA. It consists of four parts (cf. the figure below):

* A menu (1)
* A window providing access to processes (2) including a toolboxes/bookmarks panel (2.a) and a processes list (2.b)
* A window providing documentation about the selected item (3)
* A search box to search a process by name (4)

.. figure:: images/general_interface.png
  :align: center

  General user interface of BrainVISA


BrainVISA menu
++++++++++++++

Main menu
#########

The *BrainVISA* menu gives you the following choices:

* *Help*: Opens the help page in a web browser, which provides access to a manual, a tutorial, etc.
* *About*: Opens a window that shows the version of BrainVISA and the institutes and laboratories that contributes to the project.
* *Preferences*: Opens the configuration window which is used to choose options and to configure BrainVISA databases.
* *Show log*: Opens a window providing information about the current session of BrainVISA: configuration, loaded processes, run processes, errors...
* *Open process*: Opens a process which have been previously saved in a ``.bvproc`` file.
* *Reload toolboxes*: Reloads toolboxes, processes, ontologies, databases. It is useful for people who develop their own toolboxes to take into account new files without having to quit and start again Brainvisa. Useful when developing new processes.
* *Start shell*: Opens in a console a IPython shell.
* *Quit*: Closes the application.


Support menu
############

The *Support* menu gives you the following choices:

* *Bug report*: Send a bug report, either with or without the log file.

When you click on *Bug report:*, a new window opens to send the email. Here are some details about the parameters of this window:

* *From*: mandatory, sender e-mail address, i.e. the user who sends the bug report.

* *To*: mandatory, destination address, i.e. the address to which the bug report is sent. The default destination address is: support@brainvisa.info.

* *Cc*: optional, to send a carbon copy to someone.

* *Bcc*: optional, to send a blind carbon copy to someone.

* *Attach log file*: use this option to attach the :ref:`log file <log>`.

* *Send*: to validate the sending of the e-mail.

* *Cancel*: to cancel the sending of the e-mail.

.. figure:: images/support_3.png
  :align: center

  Example of bug report


View menu
#########

The *View* menu can be used to hide/show optional panels in the main window:

* *Documentation*: Hides/Shows the documentation panel (3).

* *Workflow execution*: Shows/hides a panel that shows the workflows that have been run via Soma-workflow on available computing resources. This panel is hidden by default and the parallel computing features are available only if you select a Advanced or higher user level in BrainVISA preferences. See the :ref:`chapter about parallel computing with Soma-Workflow <soma-workflow>` for more information about this feature.

* *Close all viewers*: Closes all windows opened by Brainvisa viewers whichever way they have been run: through an eye button, directly running the viewer process, or using the contextual menu of the :ref:`Database browser <db_browser>`.


.. _toolboxes:

Toolboxes panel
+++++++++++++++

The left panel of the main window contains the list of available toolboxes. A toolbox contains a set of processes related to a common theme. When you select a toolbox, its list of processes appear on the next panel.

Several toolboxes are included in BrainVISA package but some other toolboxes are available for download separately and have to be installed in addition to BrainVISA main package. More information about existing toolboxes on :documentation:`http://brainvisa.info/toolboxes.html <toolboxes.html>`.


.. _bookmarks:

Custom toolboxes
################

It is possible to create a custom toolbox by adding your own processes in the ``.brainvisa/processes`` directory in your personal folder. If this directory contains processes, they will be available in BrainVISA interface in a toolbox named *My Processes*.

It is also possible to define new toolbox containing links to existing processes, it can a sort of bookmarks toolbox. It can be useful to group in such a toolbox the processes you mostly use.

To create such a toolbox, select *New* in the contextual menu. The name of the new toolbox is editable, type whatever you want. The name will be modifiable later by double-click on the toolbox. Then you can open the empty toolbox in another window via the contextual menu then drag and drop in it the processes you want to put as shortcut in this toolbox. The shortcuts can be moved, renamed and deleted in the personal toolbox. You can also create category directories to sort the shortcuts.

The custom toolboxes are automatically saved in a file ``.brainvisa/userProcessTrees.minf`` in your personal folder. They will be reloaded from this file next time you start BrainVISA.

Example of custom toolbox
#########################

On the image below, a toolbox My Processes is visible, it means that there are valid processes defined in .brainvisa/processes in the user's personal folder. A custom toolbox named Bookmarks is also visible : it contains shortcuts to processes from various toolboxes (T1 MRI, Tools, Data Management). New directories (tools, data) have been created and some shortcuts have been moved in it. The T1 MRI toolbox is opened in a new window : this enables to drag and drop items from this toolbox to the custom toolbox.

.. figure:: images/custom_toolbox.png
  :align: center

  Custom toolbox "Bookmarks"


Actions available in a custom toolbox
#####################################

A custom toolbox is editable, so several actions are available on the content of such a toolbox:

* **Renaming the toolbox**: Double-click on the name of the toolbox, type the new name and press enter key.
* **Adding a shortcut**: Drag an element of another toolbox and drop it in the custom toolbox.
* **Renaming a shortcut**: Double-click on the shortcut, type the new name and press enter key.
* **Moving a shortcut**: Drag and drop the shortcut at its new place.
* **Creating a new category directory**: Use contextual menu *New*.


Contextual menu
###############

The contextual menu available in toolboxes panel contains the following options:

* **New**: creates a new custom toolbox to store shortcuts to processes you often use.
* **Delete**: deletes the current selected toolbox if it is a custom toolbox. Of course, BrainVISA toolboxes cannot be removed.
* **Open**: Opens the current toolbox in a new window, this enables to drag and drop elements from one toolbox to another. However only custom toolboxes are editable, you cannot drop elements in a BrainVISA toolbox.
* **Set as default list**: Sets the current selected toolbox as the default toolbox, that is to say the toolbox that is selected at BrainVISA startup. Indeed, it is practical to have the toolbox you use most of the time already selected when BrainVISA starts.


.. _processes:

Processes panel
+++++++++++++++

The processes panel contains the list of available processes, which are organized into toolboxes and categories. The list of available processes changes according to the user level selected in the preferences. In basic level, some advanced processes are hidden. The user level of a process is shown on its icon. Remember that level 1 and level 2 processes are either for advanced users (level 1) or evaluation purposes (level 2, for which no help is available).

For example, the *T1 MRI -> import* category provides access to the  *Import T1 MRI* process. To open the process, either double click on the process name, or right-click on it and select *Open* in the contextual menu.


Contextual menu
###############

The contextual menu available in processes panel when you right click on a process item contains the following options:

* **Open**: Opens the process window in order to run it.
* **Edit documentation**: Opens the documentation edition window that enables to write the documentation of the process. This feature is useful for users who develop their own processes.
* **Iterate**: Opens the iteration dialog window in order to run this process on a set of data. It is equivalent to clicking on the *Iterate* button in the process window.

There is no contextual menu available for categories directories.


.. _documentation:

Documentation panel
-------------------

This panel displays information to help you using BrainVISA in general, or a specific process. When BrainVISA is opened, this window automatically displays the main BrainVISA help page. When a process is selected, the related documentation is shown.

This panel is now a dock window so it can be hidden using the menu *View -> Documentation* or by clicking on the close button (cross) at the top right corner of the panel. It is also possible to get this panel out of the main window by clicking on the float button (squares) at the top right corner of the panel.


Editing process documentation
#############################

It is possible to edit and modify the documentation of your processes in BrainVISA interface. Click on the edit button or select Edit in the contextual menu of the process. The following window appears:

.. figure:: images/process_doc_edit.png
  :align: center

  Process documentation edition window

See the :axondev:`Process documentation <developer_manual.html#documentation>` in BrainVISA Programming manual for more information about this documentation edition interface.


BrainVISA user interface icons
------------------------------

Description of BrainVISA user interface icons:

.. raw:: html

  <table class="docutils">
    <thead>
      <tr class="row-odd">
        <th> Icon</th>
        <th> Description</th>
      </tr>
    </thead>

    <tbody>

      <tr class="row-even">
        <td><img src="_static/images/top.png" /></td>
        <td> This button takes you back to the first documentation page of BrainVISA, i.e. to the main BrainVISA help page.</td>
      </tr>
      <tr class="row-odd">
        <td><img src="_static/images/back.png" /></td>
        <td> This button takes you back to the previous documentation page. </td>
      </tr>
      <tr class="row-even">
        <td><img src="_static/images/forward.png" /></td>
        <td> This button takes you to the next documentation page (and, in iterative mode, it also indicates the process that is currently underway).</td>
      </tr>
      <tr class="row-odd">
        <td><img src="_static/images/reload.png" width="24" /></td>
        <td> This button reloads the current documentation page. </td>
      </tr>

      <tr class="row-even">
        <td><img src="_static/images/icon_process_0.png" width="24" /></td>
        <td> This icon represents user level 0 processes. Basic processes accessible to all users.</td>
      </tr>

      <tr class="row-odd">
        <td><img src="_static/images/icon_process_1.png" width="24" /></td>
        <td> This icon represents user level 1 processes. Advanced processes accessible to advanced users. </td>
      </tr>

      <tr class="row-even">
        <td><img src="_static/images/icon_process_2.png" width="24" /></td>
        <td> This icon represents user level 2 processes. Expert processes accessible to expert users. In fact, these processes
        consist of internal  BrainVISA processes (started up via level 0 or level 1 processes) or processes that are still being developed
        and do not, therefore, give reliable results.</td>
      </tr>
      <tr class="row-odd">
        <td><img src="_static/images/viewer.png" width="24" /></td>
        <td> This icon represents a viewer, that is to say a process dedicated to the visualization of certain type of data. This type of processes is automatically run when you click on the eye button next a parameter data in a process.</td>
      </tr>
      <tr class="row-even">
        <td><img src="_static/images/editor.png" width="24" /></td>
        <td> This icon represents an editor, that is to say a process dedicated to edition of certain type of data, for example the manual correction of a mask. This type of processes is automatically run when you click on the editor button next a parameter data in a process.</td>
      </tr>

    </tbody>
  </table>



</section>


<section id="bv_man%pref"><title>Preferences window</title>

<para>
The *Preferences* menu allows to customize user settings in several aspects of BrainVISA. Depending on the installed toolboxes, the preferences window may show a variable number of items. It is not necessary to complete all the fields to use BrainVISA, however they do allow you to optimally configure your user profile. The mandatory fields, such as *user level* or *language* contain a default value. Some fields become mandatory when you want to use processes that start up external programs such as Matlab (*matlabExecutable* field).

<figure><title>Preferences window</title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;preferences.png" format="PNG"  width="400"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;preferences.png" format="PNG"/></imageobject>
</mediaobject>
</figure>
</para>

<section id="bv_man%optg"><title>Configuring the main options</title>

<para>
The general *BrainVISA* sub-panel is used to configure several options for customizing your BrainVISA platform (see figure above).
</para>


<section><title>General parameters</title>
<itemizedlist>
<listitem> <para>*userLevel*: this field can contain any one of 3 values: *Basic* for a standard user (access to top-level processes) or *Advanced*/*Expert* for more experienced users (access to lower level processes or processes undergoing validation/implementation).</para></listitem>
<listitem> <para>* language*: this field can contain any one of 3 values: *System default* which is the default language in your operating system, *English* or *French*.</para></listitem>
<listitem>
*textEditor* is the external editor program used to show or edit text files when needed. It is used by several viewer or editor processes.
</listitem>
<listitem> <para>*HTMLBrowser*: list of browsers available on your workstation. you can specify the browser you wish to use.</para></listitem>
</itemizedlist>

<para>The following parameters are for an advanced use of BrainVISA:</para>
<itemizedlist>
<listitem> <para>*processesPath*: this optional field is used to configure the path to BrainVISA processes program files. It is for experienced users.</para></listitem>
<listitem> <para>*temporaryDirectory *: parameter is used to configure a path to temporary files.</para></listitem>
<listitem><para>
*removeTemporary* determines if temporary files created within BrainVISA should be deleted immediately to free disk space, or only when exiting BrainVISA. Such deletion delay is useful for processes developers when debugging processes.</para>
</listitem>
<listitem><para>
*gui_style* enables choosing the preferred style for the graphical interface.</para>
</listitem>
<listitem><para>
*databasesWarning:* unselect this option to disable the warning that is shown at startup when you have not created any database.
</para>
</listitem>
<listitem><para>
*databaseVersionSync:* Management of the database synchronization through BrainVISA versions. Possible options are:
<itemizedlist>
<listitem>Ask User : BrainVISA will ask what to do when a database need to be updated.</listitem>
<listitem>Automatic : BrainVISA will automatically update your database if you switch from one BrainVISA version to another.</listitem>
<listitem>Manual : If you modify a database and then switch from one BrainVISA version to another, you will have to update the database if you want BrainVISA take into account the modifications.</listitem>
</itemizedlist></para>
</listitem>

</itemizedlist>
</section>

<section><title>SPM parameters</title>
<itemizedlist>
<listitem><para>
*SPM99_compatibility* tells AIMS applications and Anatomist if it should read/write SPM/Analyze format images like SPM99 did, or rather like SPM2 does. See AIMS and SPM documentations for more details.</para>
</listitem>
<listitem><para>
*radiological_orientation*: for SPM format images, tells wheter they are considered to be in radiological (right to left) or neurological (left to right) convention when no further information is available in the image files.</para>
</listitem>
</itemizedlist>
</section>

<section><title>Support parameters</title>
<para>The *Support* settings section is used to configure the automatic electronic mail system for sending bug reports. This configuration is only relevant if you have access to the internet, and if you are familiar with all the mail transfer parameters. If in doubt, contact your network administrator.</para>
<itemizedlist>
<listitem><para>*userEmail*: e-mail address of the sender, i.e. the user who sends the bug report.</para></listitem>
<listitem><para>*supportEmail*: destination, i.e. the address to which the bug report is sent. The default destination address is: <computeroutput>support@brainvisa.info</computeroutput></para></listitem>
<listitem><para>*SMTP_server_name*: address/name of the server that manages the SMTP (Simple Mail Transfer Protocol). </para></listitem>
</itemizedlist>

</section>
</section>


<section id="bv_man%configdb"><title>Databases</title>

<section><title>Databases configuration panel</title>

<para>The *Databases* configuration item is used to configure one or more databases. Each database is associated with a directory and a database organization description (ontology).
</para>
<para>The database configuration window provides several functions (cf. figure below):</para>
<para>
<itemizedlist>
<listitem><para>*Edit*: Provides access to the parameters of a database, and allows the user to modify them.</para></listitem>
<listitem><para> *Add*: Used to configure a new database.</para></listitem>
<listitem><para>*Remove*: This removes the database entry in BrainVISA, but does not delete the database file and directory (no data is lost).</para></listitem>
</itemizedlist>
</para>
<para>
<figure><title>*Databases* configuration panel</title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;database_1.png" format="PNG"  width="300"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;database_1.png" format="PNG"/></imageobject>
</mediaobject>
</figure></para>

</section>

<section><title>Creating a database</title>

<para>We are now going to create a database. Please follow the instructions below:</para>
<orderedlist numeration="arabic">
<listitem><para>Open the *Preferences* window.</para> and select the *Databases* item.</listitem>
<listitem><para>Click the *Add* button.</para>
<figure><title>Adding a database</title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;database_2.png" format="PNG"  width="200"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;database_2.png" format="PNG"/></imageobject>
</mediaobject>
</figure></listitem>
<listitem><para>Complete the following fields (only *directory* is mandatory) :</para>
<itemizedlist>
<listitem><para>**directory**: mandatory field. Enter the path of the folder that will contain your database.</para></listitem>
<listitem>Expert settings
<itemizedlist>
<listitem><para>**ontology**: The ontology describes the database organization. The default organization, <emphasis>brainvisa-3.1.0</emphasis>, should be OK for most usage. However, custom organizations may be defined and used.</para></listitem>
<listitem><para>**sqliteFileName**: The database indexation is stored in a SQLite file. With this option, it is possible to choose the name of this file.</para>
</listitem>
<listitem><para>**activate_history**: When this option is checked history information will be recorded in the database directory: the log of the processes and brainvisa session which have been run to write data in the specified database. It is possible to view the history of data thanks to the <link linkend="bv_man%db_browser">Database browser</link>.</para>
</listitem>
</itemizedlist>
</listitem>
</itemizedlist>
<figure><title>Creating a database</title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;database_3.png" format="PNG"  width="150"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;database_3.png" format="PNG"/></imageobject>
</mediaobject>
</figure></listitem>
<listitem> <para>Click <emphasis>Ok</emphasis> when you have finished entering your parameters.</para>
<para><figure><title>List of database</title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;database_4.png" format="PNG"  width="200"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;database_4.png" format="PNG"/></imageobject>
</mediaobject>
</figure></para>
</listitem>
</orderedlist>

</section>

</section>

<section><title>Anatomist configuration panel</title>
<itemizedlist>
<listitem> <para><emphasis>executable</emphasis>: this parameter is used to configure the command for starting up Anatomist.</para></listitem>
</itemizedlist>
</section>

<section><title>R panel</title>
<itemizedlist>
<listitem> <para><emphasis>executable</emphasis>: command used for starting up the R program.</para></listitem>
<listitem> <para><emphasis>options</emphasis>: R software options passed to the R commandline.</para></listitem>
</itemizedlist>
</section>

<section><title>Matlab panel</title>
<itemizedlist>
<listitem> <para><emphasis>executable</emphasis>: this parameter is used to configure the command for starting up MatLab.</para></listitem>
<listitem>
<emphasis>version</emphasis>: Matlab release version, used to assume a specific version and avoid the automatic detection which may take a few seconds.
</listitem>
<listitem> <para><emphasis>options</emphasis>: used to configure options for MatLab.</para></listitem>
<listitem> <para><emphasis>path</emphasis>: used to configure the path from which matlab files will be loaded.</para></listitem>
<listitem> <para><emphasis>startup</emphasis>: run this matlab command when starting up matlab.</para></listitem>
</itemizedlist>
</section>


<section><title>SPM panel</title>
<para>It is possible to set the paths to 3 versions of SPM: SPM 5, SPM 8 (Matlab) and SPM 8 standalone.</para>
<itemizedlist>
<listitem><para><emphasis>spm8_path</emphasis>: Path to SPM 8 installation (Matlab version)</para></listitem>
<listitem> <para><emphasis>spm8_standalone_command</emphasis>: Location of the standalone version of SPM 8 run command (run_spm8.sh on linux).</para></listitem>
<listitem> <para><emphasis>spm8_standalone_mcr_path</emphasis>: Path to the Matlab Compiler Runtime (MCR) needed for a standalone version of SPM 8.</para></listitem>
<listitem> <para><emphasis>spm8_standalone_path</emphasis>: Path to SPM 8 files (where the templates for example are installed) in the standalone version.</para></listitem>
<listitem><para><emphasis>spm5_path</emphasis>: Path to SPM 5 installation (Matlab version).</para></listitem>
</itemizedlist>
<para>An <emphasis>Auto detect</emphasis> button is available at the bottom of the panel. It enables to try and find the spm paths automatically. Only one the 3 versions is needed to use the processes that need SPM (SPM normalization in Morphologist for example).</para>
</section>

<section><title>FSL panel</title>
<itemizedlist>
<listitem> <para><emphasis>fsl_commands_prefix</emphasis>: Needed if the fsl commands in your installation starts with a prefix, for example <emphasis>fsl4.1-flirt</emphasis>.</para></listitem>
</itemizedlist>
</section>

<section><title>Freesurfer panel</title>
<itemizedlist>
<listitem> <para><emphasis>freesurfer_home_path</emphasis>: Location of Freesurfer installation directory.</para></listitem>
<listitem> <para><emphasis>subjects_dir_path</emphasis>: Value of SUBJECTS_DIR variable.</para></listitem>
</itemizedlist>
</section>

<section><title>Sulci toolbox panel</title>
<itemizedlist>
<listitem> <para><emphasis>check_spam_models</emphasis>: Enable or Disable the checking of SPAM identification models installation for the automatic recognition of sulci.</para></listitem>
</itemizedlist>
</section>

<!-- dFR -->
<section><title>User configuration</title>
<para>When configuration is done, the configuration data is stored in the user <emphasis>.brainvisa</emphasis> folder.
There are actually 2 profile types: a general one (<emphasis>options.minf</emphasis>) and named profiles that can be used to store or use alternative configurations (<emphasis>options-&lt;userprofile&gt;.minf</emphasis>)</para>
<para>These different profiles are particularly useful when you must use a shared user connection.</para>

<section><title>Locating configuration files</title>
<para>If your user name is <emphasis>user</emphasis>, for instance the general configuration file will be placed in:</para>
<itemizedlist>
<listitem><para>**Unix / MacOS:</emphasis> <emphasis>$(HOME)/.brainvisa/options.minf</emphasis>, typically <emphasis>/home/user/.brainvisa/options.minf</emphasis></para>
</listitem>
<listitem><para>**Windows:</emphasis> generally something like <emphasis>C:\Documents and Settings\user\.brainvisa\options.minf</emphasis></para></listitem>
</itemizedlist>
<para></para>
<para>Customized configuration files for named profiles are placed in the same directory.</para>

<para>The general profile is automatically used when BrainVISA is launched. </para>
</section>

<section><title>Using / configuring a specific profile</title>
<para>To use and configure a specific profile, for example toto, follow the instructions below:</para>
<orderedlist numeration="arabic">
<listitem><para>Start BrainVISA with a profile name (even if it does not exist yet), for instance
<screen>brainvisa -u toto</screen></para></listitem>
<listitem><para>Customize this profile with the configuration interface: <emphasis>Preferences</emphasis> menu.</para></listitem>
<listitem><para>Validate them with the <emphasis>OK</emphasis> button</para></listitem>
<listitem><para>Exit BrainVISA.</para></listitem>
<listitem><para>To start BrainVISA with this profile:</para>
<screen>brainvisa -u toto </screen></listitem>
</orderedlist>
</section>
<!-- fFR -->
</section>

<para>
<figure><title>Example of a Linux configuration : here we have changed the <emphasis>temporaryDirectory</emphasis> and Matlab <emphasis>executable</emphasis> fields.
</title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;pref_2.png" format="PNG"  width="300"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;pref_2.png" format="PNG"/></imageobject>
</mediaobject>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;pref_2_matlab.png" format="PNG"  width="300"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;pref_2_matlab.png" format="PNG"/></imageobject>
</mediaobject>
</figure>
</para>

</section>

<section id="bv_man%log"><title>BrainVISA <emphasis>log</emphasis> window</title>
<para>The log window enables the user to monitor all the actions performed by BrainVISA. It shows information about the configuration, the processes that have been run during and their parameters, the errors that occured during the session.</para>
<para>The information displayed in this window is stored in a file which you should therefore keep if you wish to submit an execution error to the BrainVISA support. In many cases, if this file is not available, the information submitted is not specific enough to enable the error to be understood or reproduced.</para>

<para>The <emphasis>log</emphasis> window can be accessed via the <emphasis>BrainVISA -> Show Log</emphasis> menu.
If you open it just after starting the session (i.e. before running a process) you can see the list of read processes, and check if they were loaded successfully. If a dependency of a process is not installed on your workstation, the process cannot be loaded and a warning is displayed in the log window. Here is an example of the log interface:</para>
<figure><title><emphasis>Log</emphasis> interface.</title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;log_1.png" format="PNG"  width="600"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;log_1.png" format="PNG"/></imageobject>
</mediaobject>
</figure>

<table><title>Description of BrainVISA log user interface</title>
<tgroup cols="2" align="justify">
<thead>
<row>
<entry> Icon</entry>
<entry> Description</entry>
</row>
</thead>
<tbody>
<row>
<entry>&icon_process;</entry>
<entry> This icon represents a BrainVISA process run. </entry>
</row>
<row>
<entry>&anat;</entry>
<entry> Icon in the log interface, denoting communication with Anatomist.</entry>
</row>
<row>
<entry>&warning;</entry>
<entry> Icon in the log file, representing a warning.  When BrainVISA is loaded, all the processes are analyzed to make sure that all
the external programs required to run them are available. If not, the process is not loaded, and a warning is displayed in the log
interface. For example, if you wish to use a process that requires Matlab, and Matlab is not installed on your system or your object
program path is not properly configured, a warning will be displayed.</entry>
</row>
<row>
<entry>&icon_system;</entry>
<entry> This icon represents a system command call.</entry>
</row>
<row>
<entry>&error;</entry>
<entry> This icon represents an error.</entry>
</row>
</tbody></tgroup>
</table>

<section><title>Example of <emphasis>log</emphasis> window</title>

<para>You can see this windows at any time. In the example below, we can see the list of processes run, and the associated parameter
values and output. Here, we are looking at the <emphasis>Import T1 MRI</emphasis> process, but we can also see that the <emphasis>Anatomist Show Volume</emphasis> process has been run, and view the communication between BrainVISA and Anatomist via &anat;.</para>
<figure><title>Viewing the execution of a process via the  <emphasis>log</emphasis> interface.</title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;log_2.png" format="PNG"  width="600"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;log_2.png" format="PNG"/></imageobject>
</mediaobject>
</figure>

</section>

<section><title>Saving the <emphasis>log</emphasis> file</title>
<para>The <emphasis>log</emphasis> file is re-edited each time a new session is opened. So, if you want to save it, you must do so before opening a new session, otherwise the data will be lost.</para>
<para>To save the <emphasis>log</emphasis> file, follow the instructions below:</para>
<orderedlist numeration="arabic">
<listitem><para>Exit BrainVISA (and don't start it up again until you have saved the <emphasis>log</emphasis> file).</para></listitem>
<listitem><para>In Linux, go to the following folder:</para>
<screen>/home/user/.brainvisa</screen></listitem>
<listitem><para>In Windows, go to the following folder:</para>
<screen>C:\Documents and Settings\user\.brainvisa\</screen></listitem>
<listitem><para>Save the <emphasis>brainvisa.log</emphasis> file of this folder.</para></listitem>
</orderedlist>
<para>**NOTE 1:</emphasis> If you started up BrainVISA with a specific <emphasis>toto</emphasis> profile
(and there is therefore a specific <emphasis>options-toto.py</emphasis> configuration file), you should save the
<emphasis>brainvisa-toto.log</emphasis> file.</para>
<para>**NOTE 2:</emphasis> you musn't save it during a BrainVISA session otherwise log file won't be readable.</para>
<para>**NOTE 3:</emphasis> you may have several log files with numbers (eg. brainvisa2.log). It can occur when several instances of BrainVISA have been running at the same time or if a BrainVISA session didn't terminate correctly. To know which log file is associated to the current session, you can have a look at the console messages at BrainVISA starting, it says the name of the log file. The log interface also displays the name of the log file in the title of the window.</para>
</section>
<!-- fFR -->
</section>

<section><title>Errors window </title>
<para>When you work with BrainVISA, sometimes you obtain an error screen. The error window contains a list of error messages. You can click on the button <emphasis>More info</emphasis> to see the complete traceback of the errors.</para>
<para>In the example below, the error indicates that a mandatory parameter of the process has not been filled in before running the process.</para>

<figure>
<title>Error screen</title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;error.png" format="PNG"  width="300"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;error.png" format="PNG"/></imageobject>
</mediaobject>

</figure>
<figure>
<title>Error screen after a click on More info</title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;error_details.png" format="PNG"  width="400"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;error_details.png" format="PNG"/></imageobject>
</mediaobject>

</figure>

<section><title>Viewing errors </title>
<para>Even if you close the error screen, the errors are still available for consultation in BrainVISA <emphasis>Log</emphasis> file. See the paragraph on the <link linkend="bv_man%log"><emphasis>log window</emphasis></link>.</para>
</section>

<section><title>What to do in the event of an error</title>

<para>Here is a little advice on what to do if an error occurs while a process is running: </para>

<itemizedlist>
<listitem><para>Make sure that the error is not related to the management of the database or the type of data selected (wrong type of data, inexisting data, etc.).</para></listitem>

<listitem><para>Consult the process log via the <emphasis>BrainVISA</emphasis> -> <emphasis>Show log</emphasis> menu
(for more information, see the paragraph on the <link linkend="bv_man%log"><emphasis>log window</emphasis>
</link>).</para></listitem>

<listitem><para>Sign up to and consult the forum at <ulink url="http://brainvisa.info/forum">http://brainvisa.info/forum</ulink>.</para></listitem>

<listitem><para>Report the error to the BrainVISA team on the forum and attach the log file to your post.</para></listitem>
<!-- fFR -->
</itemizedlist>

</section>

</section>

<section><title>User interface of a process</title>

<section><title>Presentation</title>
<para>The graphical interface of the processes is generally automatically generated, that's why this interface is very similar from one process to the other.
We shall call the values that the user must enter to run a process "parameters". There are mandatory parameters (shown in bold type)
and optional parameters. The parameters are entered in various ways: selection of a file or a list item, entry of a value, etc. </para>

<!--<para>Some parameters have a **default value</emphasis> (not null) and so there are already filled in when you open the process. Other parameters are automatically filled in by BrainVISA when you fill in another parameter. Indeed, it is possible to define links between parameters in a process to indicate that the value of one parameter can be guessed from the value of another parameter. A lot of processes use this feature to speed up the parameters capture.</para>-->

<para>The table below describes process interface icons: </para>

<table><title>Description of process window icons: </title>
<tgroup cols="2" align="justify">
<thead>
<row>
<entry> Icon</entry>
<entry> Description</entry>
</row>
</thead>
<tbody>
<row>
<entry>&point;</entry>
<entry> This icon allows you to open a dialog window and select several values.</entry>
</row>
<row>
<entry>&browse_write;</entry>
<entry> This icon provides access to your files. It enables you to select an input or output file without using the BrainVISA database system.</entry>
</row>
<row>
<entry>&database_read;</entry>
<entry> This icon represents an input parameter. It provides access to existing data stored in a BrainVISA database. It shows all the data corresponding to the parameter type and allows selection by attribute value.</entry>
</row>
<row>
<entry>&database_write;</entry>
<entry> This icon represents an output parameter. It provides access to existing or non existing data in a BrainVISA database. It shows all the data corresponding to the parameter type and allows selection by attribute value.</entry>
</row>
<row>
<entry>&anat;</entry>
<entry> This icon represents a link with Anatomist. It is mainly used for parameters that are, in fact, 3D points. When this icon is clicked,
the current location of the 3D cursor (i.e. the red cross) in Anatomist is taken as the parameter value. It allows the user to select a value by clicking it in Anatomist.</entry>
</row>
<row>
<entry>&eye;</entry>
<entry> This icon tells you whether a data item can be visualized or not. If the button is enabled it means that BrainVISA has a viewer capable of displaying that type of data. If the icon is disabled (i.e. not clickable), it means that the corresponding file is not readable (usually because the file does not exist). If this button is not displayed, it means that BrainVISA doesn't have any viewer for this type of data.</entry>
</row>
<row>
<entry>&pencil;</entry>
<entry> This icon provides access an editor to manually correct data. For instance, the editor for label volume is ROIs toolbox in Anatomist.</entry>
</row>
<!--dFR-->
<row>
<entry>&modified;</entry>
<entry> This icon appears next to a parameter name to indicate that this parameter has been modified, it doesn't have its default value anymore.</entry>
<!--fFR-->
</row>
<row>
<entry>&lock;</entry>
<entry>This icon indicates if the data is locked. Only output files are concerned (files with &database_write;). It is not possible to execute a process when it has a locked file in its output parameters.</entry>
<!--fFR-->
</row>
<row>
<entry>&ok;</entry>
<entry> This icon indicates that a step has finished correctly in an iteration or a pipeline.</entry>
</row>
<row>
<entry>&abort;</entry>
<entry> This icon indicates that an error has occurred during a step of an iteration or a pipeline.</entry>
<!--fFR-->
</row>
</tbody></tgroup>
</table>
<para></para>

</section>


<section id="bv_man%parameter_menu"><title>Menu of a parameter</title>
<para>By right-click on a parameter, one or two options are available: </para>
<itemizedlist>

<listitem><para>**default value</emphasis>:
Always available. Some parameters have a **default value</emphasis> (not null) and so there are already filled in when you open the process. Other parameters are automatically filled in by BrainVISA when you fill in another parameter. Indeed, it is possible to define links between parameters in a process to indicate that the value of one parameter can be guessed from the value of another parameter. A lot of processes use this feature to speed up the parameters capture.</para></listitem>

<listitem><para>**lock</emphasis>: This option is available if the data is an output file and if the file exists. So that, the parameter can be locked. In fact, sometimes you would like to preserve the output file because you set/changed specific options. Once a file is locked, then a process can't rewrite this parameter. A message will be displayed to indicate that you must unlock data if you want to run the process. To unlock a parameter, just click on <emphasis>lock</emphasis> option in the menu to unselect this option.
When a parameter is locked, a <emphasis>&lt;filename&gt;.lock</emphasis> file is created. There is no link with the database or .minf file.</para>
</listitem>

</itemizedlist>
</section>

<section><title>Example of a process interface</title>
<para>We will take the following process as an example: <emphasis>Prepare subject for anatomical pipeline</emphasis>. This process is
located in <emphasis>T1 MRI -> Segmentation Pipeline -> components</emphasis>. It enables to locate the following points in a brain image: the posterior commissure (PC), the anterior commissure (AC), an interhemispheric point (IP) and a point on the left hemisphere. In fact, these reference points must be located before running the
<emphasis>Morphologist</emphasis> pipeline to determine whether or not the orientation is correct (axial, coronal, sagittal and radiologic convention) and to compute a common referential.</para>
<note>To do this example, first you must import data if you want to use a database as explained in <link linkend="bv_man%importT1">Data importation</link> paragraph.</note>
<para>Parameters are :</para>
<itemizedlist>

<listitem><para><emphasis>T1mri</emphasis>: Selecting the T1 weighted MRI, either using &database_read; (selection from your database of imported images), or via &browse_write; (selection from all the files on your disk).</para></listitem>

<listitem><para><emphasis>Commissure_coordinates</emphasis>: selecting the output file. This field is automatically completed when you
select a T1 weighted image using &database_read;. Otherwise, you must select the output file with &browse_write;.</para></listitem>

<listitem><para><emphasis>Normalized</emphasis>: you need to know if your image has already been normalized. If it has, choose the
procedure used to normalize it, and the AC, PC and IP will not have to be selected from an anatomical volume. You will however have
to run the process so that the type of normalization is taken into account and .APC file is created.
On the other hand, if your volume has not been normalized, you will have to select the AC, PC and IP from the
anatomical volume proposed by Anatomist.</para></listitem>

<listitem><para><emphasis>Anterior_Commissure</emphasis>: click &anat; to access your anatomical image via &anat; and to select the coordinates. When you click the first time, a new Anatomist session is
opened. Then, if the cursor is correctly located on the volume, click again to display the coordinates in the field.
</para></listitem>

<listitem><para><emphasis>Posterior_Commissure</emphasis>: cf. <emphasis>Anterior_Commissure</emphasis> <!--click &anat; to access your anatomical image via &anat;, and to select the
coordinates. When you click the first time, a new Anatomist session is opened. Then, if the cursor is correctly located on the volume, click again to display the coordinates in the field. -->
</para></listitem>

<listitem><para><emphasis>Interhemispheric_Point</emphasis>: cf. <emphasis>Anterior_Commissure</emphasis><!-- click &anat; to access your anatomical image via &anat;,
and to select the coordinates. When you click the first time, a new Anatomist session is opened. Then, if the cursor is correctly located on the volume, click again to display the coordinates in the field.-->
</para></listitem>

<listitem><para><emphasis>Left_Hemisphere_Point</emphasis>: cf. <emphasis>Anterior_Commissure</emphasis><!-- click &anat; to access your anatomical image via &anat;,
and to select the coordinates. When you click the first time, a new Anatomist session is
opened. Then, if the cursor is correctly located on the volume, click again to display the coordinates in the field.-->
</para></listitem>

<listitem><para><emphasis>Allow_flip_initial_MRI</emphasis>: two values are listed, <emphasis>True</emphasis>
or <emphasis>False</emphasis>. This option authorizes or forbids the user to rewrite the volume so that the orientations (axial, coronal and sagittal) and the convention (radiological) are correct.</para></listitem>
</itemizedlist>

<para>After running the process, you will be able to view the .APC file by clicking the &eye; in <emphasis>Commissure_coordinates</emphasis>.</para>

<figure><title>Process interface:  <emphasis>prepare subject for anatomical pipeline</emphasis></title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;prepare_subject.png" format="PNG"  width="400"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;prepare_subject.png" format="PNG"/></imageobject>
</mediaobject>
</figure>

</section>


<section><title>Running and interrupting a process</title>

<para>When you have completed all the fields required by the process (all fields in bold), you can launch the process by clicking the <emphasis>Run</emphasis>
button halfway up the left-hand side of the process window. You can then watch the progress of the process in the lower half of the
process window. You will be told explicitly when the process starts and ends.
<!-- dFR -->
While the process is running, the following icon (in the top right and corner) will be constantly animated. The duration of a process
varies according to the algorithms used by the process and performances of your workstation. In fact, a process such as a conversion is almost instantaneous, whereas a process such as the sulci recognition process may take anything from 1 to 2 hours depending on your workstation.</para>

<figure><title>Icon animated during a process run.</title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;rotatingBrainVISA.gif" format="GIF"  width="40"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;rotatingBrainVISA.gif" format="GIF" width="40"/></imageobject>
</mediaobject>
</figure>
<!-- fFR -->

<para>When the process begins, the <emphasis>Run</emphasis> button is replaced by an <emphasis>Interrupt</emphasis> button, which enables to stop the process when needed.</para>

</section>

<section><title>Save the state of a process</title>
<para>It is possible to save the state of a process (input and output parameters) in a file in order to reload it later. To do so, click on the <emphasis>Process -> Save</emphasis> menu and choose the place and name of the file which will store the state of the process. The file will have the extension <emphasis>.bvproc</emphasis>.</para>
<para>To reload a saved process, use the <emphasis>BrainVISA -> Open process</emphasis> menu and select the <emphasis>.bvproc</emphasis> file previously saved.</para>
</section>

</section>

<section id="bv_man%pipeline"><title>User interface of a pipeline</title>
<para>A pipeline is a special process that is composed of several other processes. A pipeline can chain a series of processes and offer a choice between different methods, each implemented in a different process. A pipeline can also contain other pipelines, so it can be a tree of processes.</para>
<para>This type of proceses have a special user interface that shows the composition of the pipeline and enables to choose between several methods and to unselect some optional steps.</para>
<para>In the example below, the structure of the pipeline is visible in the left part of the process window. When you select a step, you can see in the right part the parameters of the current step (process). A check box next the name of the step indicates that it is optional, you can click on the box to modify the selection. A radio button next the name of the step indicates that it is one of several choices, if you select one, the others are automatically deselected. Only the checked steps will be executed when the pipeline is started.</para>
<figure><title>Example: the T1 segmentation pipeline.</title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;morphologist_pipeline.png" format="PNG"  width="600"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;morphologist_pipeline.png" format="PNG" /></imageobject>
</mediaobject>
</figure>
<para>A contextual menu (right click) offers several features to ease the selection/deselection of the steps, to open a step in a new window or to show its documentation. Here are the different options of this menu : </para>
<itemizedlist>
<listitem>**Unselect before</emphasis>: Unselect all the steps before the current step at the same depth level.</listitem>
<listitem>**Unselect after</emphasis>: Unselect all the steps after the current step at the same depth level.</listitem>
<listitem>**Select before</emphasis>: Select all the steps before the current step at the same depth level.</listitem>
<listitem>**Select after</emphasis>: Select all the steps after the current step at the same depth level.</listitem>
<listitem>**Unselect steps writing lock files</emphasis>: Unselect the steps that have a locked file as output parameter. More information about locked files <link linkend="bv_man%parameter_menu">here</link>.</listitem>
<listitem>**Unselect steps upstream of locked files</emphasis>: Unselect the steps that have a locked file as output parameter and the steps before.</listitem>
<listitem>**Open this step separately</emphasis>: Open the process window of the current step.</listitem>
<listitem>**Show documentation</emphasis>: show the documentation of the current step in the BrainVISA documentation panel.</listitem>
</itemizedlist>
</section>

<section id="bv_man%iteration"><title>User interface of an iteration</title>
<para>The iterative mode enables you to sequentially run the same process on several input data. This is very similar to a
batch mode, with a user-friendly interface. This means that, for each input file selected, you can adjust the parameters
as required. For example, if you are converting several  DICOM volumes, some can be converted to GIS format (.ima and .dim),
and others can be converted to NIFTI format (.nii). This a very practical mode as it makes it possible to repeat
the same process using different parameters (or not), on a group of input files. For instance, you can apply exactly the same process to all
the brain images in a given protocol.
</para>

<para>To use the iterative mode, follow the instructions below:</para>
<orderedlist numeration="arabic">
<listitem><para>Open the process or if you don't need to change a parameter for all processes, you can use the contextual menu <emphasis>Iterate</emphasis> and go directly to step 4.</para></listitem>
<listitem><para>If necessary, modify a parameter, which will remain the same for all the repeated processes.</para></listitem>
<listitem><para>Press the <emphasis>Iterate</emphasis> button on the bottom right. A new window opens. </para></listitem>
<listitem><para>In the new window, select the input files with
&database_read;  or &browse_write;. When you select the files in the filesystem with &browse_write; an additionnal interface appears enabling to select the files in several steps wich is useful when the files are in different directories. This list editor is also available from the &database_read; icon through a right-click on the button. The list editor also enables to add, remove items and change their order in the list. </para></listitem>
<listitem><para>If necessary, modify the process parameters of each iteration using  &point;. Note that the number of iterations with a given parameter should be equal to the number of input files. But if you set only one value, BrainVISA will use this value for all iterations.</para></listitem>
<listitem><para>Once the input files and the parameters have been configured, press <emphasis>Ok</emphasis>.</para></listitem>
<listitem><para>A new window appear, it is a pipeline composed of <emphasis>n</emphasis> iterations of the process. Via this new interface, you can view each process individually. You can also check or modify parameters.</para>
<!--<para>Under Windows: via this new interface, you can view each process individually. You can also check or modify
parameters.</para>--></listitem>
<listitem><para>You can deselect processes if you do not want them to be run. See the paragraph about <link linkend="bv_man%pipeline">pipelines user interface</link> for more details about the possible actions.</para></listitem>
<listitem><para>All you have to do now is press <emphasis>Run</emphasis> to run all the processes. You can monitor the sequence of processes in the bottom part of the window. If an error occurs during a process, the iterative mode will go on to the next process. </para></listitem>
</orderedlist>
<note>If Soma-workflow is available in your version of Brainvisa, a new button <emphasis>Run in parallel</emphasis> may be available. This feature enables to execute the processes of the iteration faster than before using available computing resources. More information about this feature in the chapter <link linkend="bv_man%soma-workflow">Parallel computing with Soma-Workflow</link>.</note>


<section><title>Parameter values</title>
<para>Parameters can be modified at 3 levels:</para>
<itemizedlist>
<listitem><para>Via the general interface of the process that you wish to iterate: this modification will then be applied to
each instances. </para></listitem>
<listitem><para>Via the iteration dialog: use &point;. As mentioned above, the number of iterations for a parameter
must be equal to the number of input files, if you select only one value, this value will be used for each instances. Each parameter value will be applied to the process, depending on the input files order. </para></listitem>
<listitem><para>Via the iteration process window: you can modify the process parameters individually. The modification will only be applied to the current process.</para></listitem>
</itemizedlist>
</section>


<section><title>Example: converting several files</title>
<para>In this example, we wish to convert 6 GIS images (.ima and .dim) in a database to NIFTI format (.nii). </para>
<orderedlist numeration="arabic">
<listitem><para>Select the conversion process: <emphasis>Tools -> converters -> Aims Converter</emphasis>.</para></listitem>
<listitem><para>Select the <emphasis>preferredFormat</emphasis> parameter (<emphasis>NIFTI-1 image</emphasis>).</para>
<figure><title>Window 1: Process to be iterated</title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;iter_1.png" format="PNG"  width="300"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;iter_1.png" format="PNG"/></imageobject>
</mediaobject>
</figure></listitem>
<listitem><para>Start up the iterative mode by clicking <emphasis>Iterate</emphasis> button.</para></listitem>
<listitem><para>A new window is displayed: </para>
<figure><title>Window 2: Iteration dialog</title>

<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;iter_2.png" format="PNG"  width="200"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;iter_2.png" format="PNG"/></imageobject>
</mediaobject>
</figure></listitem>
<listitem><para>Select the volumes on which you want to run the process by clicking
&database_read;. A database file selector is displayed. Select  6 Raw T1 MRI (filter on the type). To select several files, use the
<emphasis>Ctrl</emphasis> + <emphasis>left click</emphasis> combination.</para>
<figure><title>Window 3: Selecting files to iterate</title>


<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;iter_3.png" format="PNG"  width="600"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;iter_3.png" format="PNG"/></imageobject>
</mediaobject>
</figure></listitem>
<listitem><para>Click the <emphasis>Ok</emphasis> buttons in windows 3 and 2. A new window, containing all the processes appears.</para>
<figure><title>Window 4: Iteration window</title>

<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;iter_4.png" format="PNG"  width="400"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;iter_4.png" format="PNG"/></imageobject>
</mediaobject>
</figure>
<!--<figure><title>Window 4: Processing the files to be iterated under Windows</title>
<mediaobject><imageobject><imagedata fileref="&DIR_IMG;iterw_4.png" format="PNG" scale="75"></imagedata>
</imageobject></mediaobject></figure>-->
</listitem>
<listitem><para>If you want, you can still modify the process parameters if necessary.</para></listitem>
<listitem><para>To start the iteration, click  <emphasis>Run</emphasis> </para></listitem>
<listitem><para>When the iteration is finished, the following window is displayed:</para>
<figure><title>Window 5: Iteration completed</title>

<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;iter_5.png" format="PNG"  width="400"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;iter_5.png" format="PNG"/></imageobject>
</mediaobject>
</figure>
<!--<figure><title> Window 5: Iteration completed under Windows</title>
<mediaobject><imageobject><imagedata fileref="&DIR_IMG;iterw_5.png" format="PNG" scale="75"></imagedata>
</imageobject></mediaobject></figure>-->
</listitem>
</orderedlist>


<section><title>Selecting a different value for each iteration</title>
<para>To select the value of a parameter in relation to the input values (i.e. value of <emphasis>preferredFormat</emphasis>
in relation to value of <emphasis>read</emphasis>), you can proceed this way :</para>
<orderedlist numeration="arabic">
<listitem>
<para>After the fifth step, click on <emphasis>Ok</emphasis> button to return to window 2 :
<figure>
<title>Window 3.1 : After selection of <emphasis>read</emphasis> parameters</title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;iter_note0.png" format="PNG"  width="200"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;iter_note0.png" format="PNG"/></imageobject>
</mediaobject>
</figure>
</para>
</listitem>

<listitem>
<para>Click on &point; of <emphasis>preferredFormat</emphasis> parameter <figure>
<title>Window 3.2 : Selection of <emphasis>preferredFormat</emphasis> parameters</title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;iter_note1.png" format="PNG"  width="200"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;iter_note1.png" format="PNG"/></imageobject>
</mediaobject>
</figure>
</para>
</listitem>

<listitem>
<para>Select the nth <emphasis>preferredFormat</emphasis> parameter in relation to nth <emphasis>read</emphasis> parameter with the menu:
<figure>
<title>Window 3.3 : Selection of <emphasis>preferredFormat</emphasis> parameter</title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;iter_note2.png" format="PNG"  width="200"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;iter_note2.png" format="PNG"/></imageobject>
</mediaobject>
</figure>
<figure>
<title>Window 3.4 : Selection of <emphasis>preferredFormat</emphasis> parameter</title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;iter_note3.png" format="PNG"  width="200"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;iter_note3.png" format="PNG"/></imageobject>
</mediaobject>
</figure>
</para>
</listitem>

<listitem>
<para>Click on <emphasis>Add</emphasis> (this selection of <emphasis>preferredFormat</emphasis> parameter corresponds to the first
<emphasis>read</emphasis> parameter) :

<figure>
<title>Window 3.5 : Validation of the first <emphasis>preferredFormat</emphasis> parameter</title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;iter_note3bis.png" format="PNG"  width="200"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;iter_note3bis.png" format="PNG"/></imageobject>
</mediaobject>
</figure>
</para>
</listitem>

<listitem>
<para>Do the same to select the value of the parameter in each iterations.
</para>
</listitem>

<listitem>
<para>Click on <emphasis>Ok</emphasis> button in windows 3.5 to return to the 6th steps :
<figure>
<title>Window 3.6 : <emphasis>preferredFormat</emphasis> parameters selection</title>
<mediaobject>
<imageobject role="fop"><imagedata fileref="&DIR_IMG;iter_note4.png" format="PNG"  width="500"/></imageobject>
<imageobject role="html"><imagedata fileref="&DIR_IMG;iter_note4.png" format="PNG"/></imageobject>
</mediaobject>
</figure>
</para>
</listitem>
<listitem>
<para>Click on <emphasis>Ok</emphasis> button in windows 3.6 to return to step 6</para>
</listitem>
</orderedlist>
</section>

<!-- fFR -->

</section>
</section>

</chapter>



---------------

.. _database:

.. _helpcom:

.. _log:

.. _soma-workflow:

.. _db_browser:

