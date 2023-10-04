''' Specialized Process class to link with :capsul:`CAPSUL <index.html>` processes and pipelines.

the aim is to allow using a Capsul process/pipeline as an Axon process (or at least, ease it). Such a process would look like the following:

::

    from brainvisa.processes import *
    from brainvisa.processing import capsul_process

    name = 'A Capusl process ported to Axon'
    userLevel = 0
    base_class = capsul_process.CapsulProcess
    capsul_process = 'morphologist.capsul.morphologist.Morphologist'

**Explanation:**

The process should inherit the CapsulProcess class (itself inheriting the standard Process). To do so, it declares the "base_class" variable to this CapsulProcess class type.

Then it should instantiate the appropriate Capsul process. This is done simlply by setting the variable ``capsul_process`` (or alternately by overloading the setup_capsul_process() method, which should instantiate the Capsul process and set it into the Axon proxy process).

The underlying Capsul process fields will be exported to the Axon signature automatically. This behaviour can be avoided or altered by overloading the initialize() method, which we did not define in the above example.

The process also does not have an :meth:`~brainvisa.processes.Process.execution` function. This is normal: :class:`CapsulProcess` already defines an :meth:`~CapsulProcess.executionWorkflow` method which will generate a :somaworkflow:`Soma-Workflow <index.html>` workflow which will integrate in the process or parent pipeline (or iteration) workflow.

**nipype interfaces**

As Capsul processes can be built directly from nipype interfaces, any nipype interface can be used in Axon wrappings here.


Pipeline design directly using Capsul nodes
-------------------------------------------

In an Axon pipeline, it is now also possible (since Axon 4.6.2) to use directly a Capsul process in an Axon pipeline. In the pieline initialization() method, the pipeline definition code can add nodes which are actually Capsul processes (or pipelines). Capsul processes identifier should start with ``capsul://``::

    from brainvisa.processes import *

    name = 'An Axon pipeline'
    userLevel = 0

    signature = Signature(
        'skeleton', ReadDiskItem('Raw T1 MRI', 'aims readable volume formats')
    )

    def initialization(self):
        eNode = SerialExecutionNode(self.name, parameterized=self)

        # add an Axon process node
        eNode.addChild('SulciSkeleton',
                       ProcessExecutionNode('sulciskeleton', optional=1)
        # add a Capsul process node
        eNode.addChild(
            'SulciLabeling',
            ProcessExecutionNode(
                'capsul://deepsulci.sulci_labeling.capsul.labeling',
                optional=1))
        # link parameters
        eNode.addDoubleLink('skeleton', 'SulciSkeleton.skeleton')
        eNode.addDoubleLink('SulciSkeleton.skeleton', 'SulciLabeling.skeleton')
        # ...
        self.setExecutionNode(eNode)

Note that using this syntax, a Capsul process wihch does not have an explicit Axon wraping will be automatically wraped in a new CapsulProcess subclass. This way any Capsul process can be used on-the-fly without needing to define their correspondance in Axon.

However if a wrapper process is already defined in Axon (either to make it visible in Axon interface, or because it needs some customization), then the wrapper process will be found, and used. In this situation the pipeline developer thus can either use the Axon wrapper (``ProcessExecutionNode('sulci_deep_labeling')`` here) or the Capsul process identifier (``ProcessExecutionNode('capsul://deepsulci.sulci_labeling.capsul.labeling')`` here). The result will be the same.

Note that **nipype interfaces** can also be used directly, the exact same way::

    eNode.addChild(
        'Smoothing',
        ProcessExecutionNode(
            'capsul://nipype.interfaces.spm.smooth', optional=1))


Process / pipeline parameters completion
----------------------------------------

Capsul and Axon are using parameters completions systems with very different designs (actually Capsul was written partly to overcome Axon's completion limitaions) and thus are difficult to completely integrate. However some things could be done.

A Capsul process will get completion using Capsul's completion system. Thus it should have a completion defined (throug a :capsul:`File Organization Model <user_guide_tree/advanced_usage.html#file-organization-model-fom>` typically). The completion system in Capsul defines some attributes.

The attributes defined in Capsul will be parsed in an Axon process, and using attributes and file format extensions of process parameters, Axon will try to guess matching DiskItem types in Axon (Capsul has no types).

For this to work, matching :ref:`DiskItem types <data>` must be also defined in Axon, and they should be described in a :ref:`files hierarchy <hierarchies>`. Thus, some things must be defined more or less twice...

**What to do when it does not work**

In some situations a matching type in Axon will not be found, either because it does not exist in Axon, or because it is declared in a different, complex way. And sometimes a type will be found but is not the one which should be picked, when several possible types are available.

It is possible to force the parameters types on Axon side, by overloading them in the axon process. To do this, it is possible to define a signature (as in a regular Axon process) which only declares the parameters that need to have their type forced.

For instance if a capsul process has 3 parameters, *param_a*, *param_b*, *param_c*, and we need to assign manually a type to *param_b*, we would write:

::

    from brainvisa.processes import *
    from brainvisa.processing import capsul_process

    name = 'A Capusl process ported to Axon'
    userLevel = 0
    base_class = capsul_process.CapsulProcess
    capsul_process = 'my_processes.MyProcess'

    signature = Signature(
        'param_b', ReadDiskItem('Raw T1 MRI', 'aims readable volume formats'),
    )

In this situation the types of *param_a* and *param_c* will be guessed, and *param_b* will be the one from the declared signature. This signature declaration is optional in a wraped Capsul process, of course, when all types can be guessed.


Iterations
----------

Capsul has its own iteration system, using iteration nodes in pipelines. Thus Capsul processes are iterated in the Capsul way. For the user it looks differently: parameters are replaced by lists, istead of duplicating the process to be iterated. The GUI is thus more concise and more efficient, and parameters completion is done in Capsul, which is also much more efficient than the Axon way (Capsul completion time is linear with the number of parameters to be completed, where Axon also slows down with the size of the database).


Completion time and bottlenecks
-------------------------------

The first time a Capsul process is opened, the :capsul:`completion system <user_guide_tree/advanced_usage.html#>` is initialized, which takes a few seconds. Later uses will not have this overhead.

Capsul completion system, although not providing immeditate answers, is much more efficient than Axon's. Typically to perform completion on **1000 iterations over a process of about 5-6 parameters**,

* Pure Capsul: about 2-3 seconds.
* Axon: about  1 minute
* Capsul process in Axon: about the same (1 minute) as Axon, because the long part here is the validation of file parameters (checking that files exist, are valid etc), which is always done in Axon whatever the process type.

For a complex pipeline, for instance the **Morphologist pipeline, 50 iterations** over it will take

* Pure Capsul: about 6 seconds
* Axon: about 3 minutes and 30 seconds
* Capsul process in Axon: about 35 seconds. This is faster than the Axon one because all pipeline internals (nodes parameters) are not exported in Axon.
* The specialized "Morphologist Capsul iteration", which hides the Capsul process inside and does not expose its parameters in Axon, will merely show any completion latency, because completion is delayed to runtime workflow preparation. It will run as fast as the Capsul version.


Process documentation
---------------------

Capsul processes have their documentation conventions: docs are normally in the process docstrings, and are normally written in `Sphinx <http://www.sphinx-doc.org>`_ / `RestructuredText <http://docutils.sourceforge.net/rst.html>`_ markup language. A Capsul process in Axon will be able to automatically retreive its Capsul documentation, and convert it into HTML as expected in Axon. The conversion will use `pandoc <https://pandoc.org/>`_ if available to convert the RST markup of Capsul into HTML (which is still not complete `Sphinx <http://www.sphinx-doc.org>`_ but easier to use), and the result will be used to generate the process documentation when the ``generateDocumentation`` process is used. Process developpers should not edit the process documentation is Axon though, because then a ``.procdoc`` file would be written and would be used afterwards, therefore the docs will be duplicated and may get out of sync when updated.

See also :doc:`capsul`

'''

import brainvisa.processes as processes
from brainvisa.data import neuroData
from brainvisa.data.readdiskitem import ReadDiskItem
from brainvisa.data.writediskitem import WriteDiskItem
from brainvisa.processes import getAllFormats
from brainvisa.data.neuroData import Signature, ListOf
from brainvisa.data.neuroDiskItems import DiskItem, getAllDiskItemTypes
from brainvisa.data import neuroHierarchy
from brainvisa.configuration import neuroConfig
from brainvisa.configuration import axon_capsul_config_link
from soma.functiontools import SomaPartial
from capsul.pipeline.pipeline import Pipeline
from soma.controller import File, Directory, Literal, undefined
import distutils.spawn
import sys
import subprocess
import re
import tempfile


def fileOptions(filep, name, process, attributes=None):
    if hasattr(filep, 'output') and filep.output:
        return (WriteDiskItem, get_best_type(process, name, attributes))
    return (ReadDiskItem, get_best_type(process, name, attributes))


def choiceOptions(choice, name, process, attributes=None):
    return list(choice.subtypes())


def listOptions(param, name, process, attributes=None):
    item_type = param.subtypes()[0]
    return [make_parameter(item_type, name, process, attributes)]


param_types_table = \
    {
        bool: neuroData.Boolean,
        str: neuroData.String,
        float: neuroData.Number,
        int: neuroData.Integer,
        # Any: neuroData.String,
        File: fileOptions,
        Directory: fileOptions,
        Literal: (neuroData.Choice, choiceOptions),
        list: (neuroData.ListOf, listOptions),
        list[float]: (neuroData.ListOf, listOptions),
        set: (neuroData.ListOf, listOptions),
    }

try:
    import nipype.interfaces.base.traits_extension

    param_types_table.update({
        nipype.interfaces.base.traits_extension.Str: neuroData.String,
    })
except ImportError:
    pass  # no nipype


def make_parameter(param, name, process, attributes=None):
    newtype = param_types_table.get(param.type)
    paramoptions = []
    kwoptions = {}
    if newtype is None:
        print('no known converted type for', name, ':', param.type)
        newtype = neuroData.String
    if isinstance(newtype, tuple):
        paramoptions = newtype[1](param, name, process, attributes)
        newtype = newtype[0]
    elif hasattr(newtype, '__code__'):  # function
        newtype, paramoptions = newtype(param, name, process, attributes)
    if param.metadata('groups'):
        section = param.groups[0]
        kwoptions['section'] = section
    return newtype(*paramoptions, **kwoptions)


def convert_capsul_value(value):
    if isinstance(value, (list, set)):
        value = [convert_capsul_value(x) for x in value]
    elif value is undefined or value in ("<undefined>", "None"):
        # FIXME: "<undefined>" or "None" is a bug in the Controller GUI
        value = None
    return value


def convert_to_capsul_value(value, item_type=None, field=None):
    if isinstance(value, DiskItem):
        value = value.fullPath()
    elif isinstance(value, list):
        value = [convert_to_capsul_value(x, item_type.contentType)
                 for x in value]
        if field is not None and field.type is set:
            value = set(value)
    elif isinstance(value, set):
        value = set([convert_to_capsul_value(x, item_type.contentType)
                     for x in value])
    elif value is None and isinstance(item_type, ReadDiskItem):
        value = undefined
    return value


def get_initial_capsul():
    init_config = {
        'builtin': {
            'config_modules': [
                'spm',
                'axon',
            ],
        }
    }

    return init_config


def match_ext(capsul_exts, axon_formats):
    if not capsul_exts:
        return True
    for format in axon_formats:
        if not hasattr(format, 'patterns'):
            continue  # probably a group
        for pattern in format.patterns.patterns:
            f0 = pattern.pattern.split('|')[-1]
            f1 = f0.split('*')[-1]
            if f1 in capsul_exts:
                return True
    return False


def get_axon_formats(capsul_exts):
    if capsul_exts is None:
        capsul_exts = []
    formats = []
    used_exts = set()
    for f in getAllFormats():
        if match_ext(capsul_exts, [f]):
            formats.append(f)
            # get used exts
            if hasattr(f, 'patterns'):
                for pattern in f.patterns.patterns:
                    f0 = pattern.pattern.split('|')[-1]
                    f1 = f0.split('*')[-1]
                    if f1 in capsul_exts:
                        used_exts.add(f1)

    remaining = [e for e in capsul_exts if e not in used_exts]
    if remaining:
        # create format
        from brainvisa.data.neuroDiskItems import Format
        from brainvisa.data import fileformats
        for ext in remaining:
            # TODO: name it properly
            f_name = '%s file' % ext[1:]
            # create format
            f = Format(f_name, 'f|*%s' % ext)
            formats.append(f)
            # also in fileformats...
            fileformats.addNewFileFormat(f)
    return formats


def get_best_type(process, param, metadata=None):

    from capsul.dataset import ProcessMetadata

    cext = process.field(param).metadata('extensions')
    if metadata is None:
        metadata = process.metadata

    is_list = process.field(param).is_list()

    if metadata is None:
        # look if it's a pipeline with iterations inside
        # iterations are not handled in a regular way in Capsul, because
        # they are virtual links (a single process instance is used to
        # complete parameters iteratively with attributes values from a
        # list). So here we have to get inside this system. Too bad.
        if isinstance(process, Pipeline):
            plug = process.plugs[param]
            if process.field(param).is_output():
                links = plug.links_from
            else:
                links = plug.links_to
            for to in links:
                if hasattr(to[2], 'iterative_parameters'):
                    metadata = ProcessMetadata(
                        to[2], metadata.execution_context,
                        datasets=metadata.datasets)
                    process = to[2].process
                    param = to[1]
                    cext = process.field(param).metadata('extensions')
                    is_list = True
                    break
        if metadata is None:
            return ('Any Type', get_axon_formats(cext))

    # merge field extensions and completion system extensions
    compl_ext = None  # FIXME allowed extensions for param
    if not cext:
        cext = compl_ext
    elif compl_ext:
        cext = [e for e in cext if e in compl_ext]

    orig_values = None
    # TODO
    #if is_list:
        ## print('** list !**')
        ## keep 1st value. We must instantiate a new attrubutex controller,
        ## using the underlying completion engine
        #orig_values = metadata.asdict()
        #for field in metadata.fields():
            #attr = field.name
            #if field.is_list() and issubclass(field.subtypes()[0], str):
                #setattr(metadata, attr,
                        #getattr(metadata, attr)[0])
            #else:
                #setattr(metadata, attr, getattr(metadata, attr))

    orig_values = metadata.asdict()
    tr = CapsulToAxonSchemaTranslation()
    tr.translate_metadata(metadata, in_place=True)

    try:
        # print('metadata:', metadata.asdict())

        path = metadata.path_for_parameter(process, param)
        # remove dataset
        if path is not None and path is not undefined:
            m = re.match('!{[^}]*}/(.*)', path)
            if m:
                path = m.group(1)
            # print('path:', path)
            if path is None:
                # fallback to the completed value
                path = getattr(process, param)
                # print('new path:', path)
            if path in (None, undefined, []):
                # print('Any 2')
                return ('Any Type', get_axon_formats(cext))

            for db in neuroHierarchy.databases.iterDatabases():
                # print('look in db:', db.directory)
                for typeitem in getAllDiskItemTypes():
                    rules = db.fso.typeToPatterns.get(typeitem)
                    if rules:
                        for rule in rules:
                            pattern = rule.pattern.pattern
                            cpattern = pattern.replace('{', '<')
                            cpattern = cpattern.replace('}', '>')
                            # print('cpattern:', cpattern)
                            if path.startswith(cpattern):
                                if len(cpattern) < len(path):
                                    if path[len(cpattern)] != '.':
                                        continue
                                    if not match_ext(cext, rule.formats):
                                        continue
                                # print('found:', typeitem.name, rule.formats)
                                return (typeitem.name, rule.formats)
    finally:
        if orig_values is not None:
            metadata.import_dict(orig_values)

    # print('Any end')
    return ('Any Type', get_axon_formats(cext))


class CapsulProcess(processes.Process):

    ''' Specialized Process to link with a CAPSUL process or pipeline.

    See the :py:mod:`brainvisa.processing.capsul_process` doc for details.
    '''

    capsul_to_axon_process_map = {}
    # possibly costomize FSO->FOM names translations
    fso_to_schema_map = {
        'brainvisa-3.2.0': 'brainvisa',
        'morphologist-bids-1.0': 'morphologist_bids',
    }

    def __init__(self):
        self._capsul_process = None
        self.setup_capsul_process()
        super().__init__()

    def set_capsul_process(self, process):
        ''' Sets a CAPSUL process into the Axon (proxy) process
        '''
        from capsul.dataset import ProcessMetadata

        capsul = self.get_capsul()
        execution_context = capsul.engine().execution_context(process)

        metadata = ProcessMetadata(process, execution_context)

        self._capsul_process = process

    def setup_capsul_process(self):
        ''' This method is in charge of instantiating the appropriate CAPSUL process or pipeline, and setting it into the Axon process (self), using the set_capsul_process() method.

        It may be overloaded by children processes, but the default implementation looks for a variable "capsul_process" in the process source file which provides the Capsul module/process name (as a string), for instance:

        ::

          capsul_process = "morphologist.capsul.axon.t1biascorrection.T1BiasCorrection"

        This is basically the only thing the process must do.
        '''
        capsul_process = getattr(self, 'capsul_process', None)
        if capsul_process is None:
            if not hasattr(self, '_id'):
                return  # no associated module, may be built on-the-fly
            module = processes._processModules.get(self._id)
            if module is None:
                return  # no associated module, may be built on-the-fly
            capsul_process = getattr(module, 'capsul_process')
        if capsul_process:
            capsul = self.get_capsul()
            process = capsul.executable(capsul_process)
            self.set_capsul_process(process)

    def get_capsul_process(self):
        ''' Get the underlying CAPSUL process '''
        return self._capsul_process

    def initialization(self):
        ''' This specialized initialization() method sets up a default
        signature for the process, duplicating every user field of the
        underlying CAPSUL process.

        As some parameter types and links will not be correctly translated, it
        is possible to prevent this automatic behaviour, and to setup manually
        a new signature, by overloading the initialization() method.

        In such a case, the process designer will also probably have to
        overload the propagate_parameters_to_capsul() method to setup the
        underlying Capsul process parameters from the Axon one, since there
        will not be a direct correspondance any longer.
        '''
        process = self.get_capsul_process()
        if process is None:
            return  # no process defined, probably too early to do this.

        from capsul.dataset import ProcessMetadata
        from soma.qt_gui.qtThread import gui_thread_function

        capsul = self.get_capsul()
        execution_context = capsul.engine().execution_context(process)
        metadata = ProcessMetadata(process, execution_context)

        # save parameters values
        orig_params = process.asdict()

        orig_attributes = metadata.asdict()
        for field in metadata.fields():
            attr = field.name
            if issubclass(field.type, str):
                setattr(metadata, attr, '<%s>' % attr)
            elif field.is_list() \
                    and issubclass(field.subtypes()[0], str):
                setattr(metadata, attr, ['<%s>' % attr])

        metadata.generate_paths()

        signature = getattr(self, 'signature', Signature())
        excluded_fields = set(('nodes_activation', 'visible_groups',
                               'pipeline_steps'))
        optional = []
        for param in process.user_fields():
            name = param.name
            if name in excluded_fields:
                continue
            if name in signature:
                # the param was explicitely declared in axon process: keep it,
                # but place it at the same position as in capsul process
                parameter = signature[name]
                del signature[name]
            else:
                # FIXME
                parameter = make_parameter(param, name, process, metadata)
            signature[name] = parameter
            if param.optional:
                optional.append(name)

        # restore attributes
        metadata.import_dict(orig_attributes)

        for name in ('use_capsul_completion', 'edit_pipeline', 'capsul_gui',
                     'edit_pipeline_steps', 'edit_capsul_config'):
            if name in signature:
                del signature[name]
        signature['use_capsul_completion'] = neuroData.Boolean()
        signature['edit_pipeline'] = neuroData.Boolean()
        signature['capsul_gui'] = neuroData.Boolean()
        has_steps = False
        if getattr(process, 'pipeline_steps', None):
            has_steps = True
            signature['edit_pipeline_steps'] = neuroData.Boolean()
        signature['edit_capsul_config'] = neuroData.Boolean()
        self.__class__.signature = signature
        self.changeSignature(signature)

        # restore parameters
        for param, value in orig_params.items():
            if param not in ('pipeline_steps', 'nodes_activation'):
                setattr(process, param, value)

        # setup callbacks to sync capsul and axon parameters values
        dispatch = gui_thread_function(neuroConfig.gui)

        self._capsul_process.on_attribute_change.add(
            dispatch(self._process_field_changed))
        import inspect
        pcallback = dispatch(self._process_field_changed)
        signature = inspect.signature(pcallback)

        if optional:
            self.setOptional(*optional)
        use_capsul_completion = getattr(self.__class__,
                                        'use_capsul_completion',
                                        True)

        self.setValue('use_capsul_completion', use_capsul_completion,
                      default=True)
        self.setValue('edit_pipeline', False, default=True)
        self.setValue('capsul_gui', False, default=True)
        if getattr(process, 'pipeline_steps', None):
            self.setValue('edit_pipeline_steps', False, default=True)
        self.setValue('edit_capsul_config', False, default=True)
        for field in process.user_fields():
            name = field.name
            if name in excluded_fields:
                continue
            value = getattr(process, name)
            if value not in (undefined, ''):
                self.setValue(name, convert_capsul_value(value), default=True)
            else:
                self.setValue(name, None, default=True)
            self.linkParameters(None, name,
                                SomaPartial(self._on_axon_parameter_changed,
                                            name))

        self.linkParameters(None, 'edit_pipeline', self._on_edit_pipeline)
        self.linkParameters(None, 'capsul_gui', self._on_capsul_gui)
        if has_steps:
            self.linkParameters(None, 'edit_pipeline_steps',
                                self._on_edit_pipeline_steps)
        self.linkParameters(None, 'edit_capsul_config',
                            self._on_edit_capsul_config)
        self.linkParameters(None, 'use_capsul_completion',
                            self._on_change_use_completion)
        if hasattr(process, 'visible_groups'):
            self.visible_sections = process.visible_groups

    def propagate_parameters_to_capsul(self):
        ''' Set the underlying Capsul process parameters values from the Axon process (self) parameters values.

        This method will be called before execution to build the workflow.

        By default, it assumes a direct correspondance between Axon and Capsul processes parameters, so it will just copy all parameters values. If the initialization() method has been specialized in a particular process, this direct correspondance will likely be broken, so this method should also be overloaded.
        '''
        process = self.get_capsul_process()
        for name, itype in self.signature.items():
            converted_value = convert_to_capsul_value(getattr(self, name),
                                                      itype,
                                                      process.field(name))
            try:
                setattr(process, name, converted_value)
            except AttributeError:
                pass

            # enable / forbid completion in capsul when it's forbidden in axon
            forbid_completion = not self.parameterLinkable(name)
            if hasattr(process, 'propagate_metadata'):
                if name in process.pipeline_node.plugs:
                    process.propagate_metadata(
                        '', name, {'forbid_completion': forbid_completion})
            else:
                field = process.field(name)
                if field is not None:
                    field.forbid_completion = forbid_completion

    def forbid_completion(self, params, forbid=True):
        ''' Forbids (blocks) Capsul completion system for the selected
        parameters. This allows to replace Capsul completion by Axon links
        when needed (this is more or less the equivalent of unplugging internal
        links in Axon processes when inserting them in pipelines).

        Parameters
        ----------
        params: str or list
            parameters to block
        forbid: bool
            True blocks completion, False allows it again
        '''
        if isinstance(params, str):
            params = [params]
        process = self.get_capsul_process()
        for param in params:
            f = process.field(param)
            f.forbid_completion = forbid

    @staticmethod
    def capsul_workflow_to_somaworkflow(wf_name, cwf):
        ''' Convert a CapsulWorkflow (Capsul3) to Soma-Workflow
        '''
        import soma_workflow.client as swc
        import json

        def resolve_tmp(value, temps, ref_param, param_dict, pname):
            if isinstance(value, list):
                return [resolve_tmp(v, temps, ref_param, param_dict,
                                    '%s_%d' % (pname, i))
                        for i, v in enumerate(value)]
            if isinstance(value, str) \
                    and value.startswith('!{dataset.tmp.path}'):
                tvalue = temps.get(value)
                if tvalue is not None:
                    ref_param.append(tvalue)
                    param_dict[pname] = tvalue
                    return tvalue
                if len(value) == 19:  # exactly temp dir
                    tvalue = tempfile.gettempdir()  # FIXME
                else:
                    tvalue = swc.TemporaryPath(suffix=value[20:])
                    ref_param.append(tvalue)
                temps[value] = tvalue
                param_dict[pname] = tvalue
                return tvalue
            return value

        deps = []
        job_map = {}
        temps = {}
        for job_id, cjob in cwf.jobs.items():
            cmd = [
                'python', '-m', 'capsul', 'run', '--non-persistent',
                cjob['process']['definition'],
            ]
            ref_inputs = []
            ref_outputs = []
            param_dict = {}
            for param, index in cjob.get('parameters_index', {}).items():
                value = cwf.parameters_values[index]
                while isinstance(value, list) and len(value) == 2 \
                        and value[0] == '&':
                    value = value[1]
                if param in cjob.get('write_parameters', []):
                    ref_param = ref_outputs
                else:
                    ref_param = ref_inputs
                value = resolve_tmp(value, temps, ref_param, param_dict, param)
                try:
                    value = json.dumps(value)
                except TypeError:  # TemporaryPath are not jsonisable
                    pass
                if isinstance(value, str):
                    cmd.append(f'{param}={value}')
                else:
                    cmd.append(['<join>', f'{param}=', value])
            job = swc.Job(command=cmd,
                          name=cjob['process']['definition'],
                          param_dict=param_dict,
                          referenced_input_files=ref_inputs,
                          referenced_output_files=ref_outputs)
            job_map[job_id] = job
            priority = cjob.get('priority')
            if priority is not None:
                job.priority = priority
            # TODO param links

        for job_id, cjob in cwf.jobs.items():
            for dep in cjob.get('wait_for', []):
                deps.append((job_map[dep], job_map[job_id]))

        wf = swc.Workflow(name=wf_name, jobs=job_map.values(),
                          dependencies=deps)
        return wf

    def executionWorkflow(self, context=processes.defaultContext()):
        ''' Build the workflow for execution. The workflow will be integrated
        in the parent pipeline workflow, if any.
        '''

        from capsul.execution_context import CapsulWorkflow

        self.propagate_parameters_to_capsul()
        process = self.get_capsul_process()

        metadata = getattr(process, 'metadata', None)
        if metadata is not None and self.use_capsul_completion:
            self._on_axon_parameter_changed(self.signature.keys()[0],
                                            self, None)
            #metadata.generate_paths(process)
            #execution_context \
                #= self.get_capsul().engine().execution_context(process)
            #process.resolve_paths(execution_context)

        cwf = CapsulWorkflow(process)

        wf = self.capsul_workflow_to_somaworkflow(process.name, cwf)
        jobs = wf.jobs
        dependencies = wf.dependencies
        root_group = wf.root_group

        return jobs, dependencies, root_group

    def init_capsul(self, context=processes.defaultContext()):
        ''' Build a Capsul / config object if not present in the context,
        set it up, and return it
        '''
        from capsul.api import Capsul
        from capsul.schemas.brainvisa import declare_morpho_schemas
        import sys
        import os.path as osp

        # morphologist may be imported as a toolbox. Here we need the regular
        # module
        old_morpho = None
        if 'morphologist' in sys.modules \
                and sys.modules['morphologist'].__file__.endswith(
                    osp.join('brainvisa', 'toolboxes', 'morphologist',
                             'processes', 'morphologist.py')):
            # print('change morphologist module')
            old_morpho = sys.modules['morphologist']
            del sys.modules['morphologist']
        declare_morpho_schemas('morphologist.capsul')
        if old_morpho is not None:
            # restore toolbox module
            sys.modules['morphologist'] = old_morpho

        capsul = getattr(context, 'capsul', None)

        # axon_to_capsul_formats = {
            #'NIFTI-1 image': "NIFTI",
            #'gz compressed NIFTI-1 image': "NIFTI gz",
            #'GIS image': "GIS",
            #'MINC image': "MINC",
            #'SPM image': "SPM",
            #'GIFTI file': "GIFTI",
            #'MESH mesh': "MESH",
            #'PLY mesh': "PLY",
            #'siRelax Fold Energy': "Energy",
        #}

        ditems = [(name, item) for name, item in self.signature.items()
                  if isinstance(item, DiskItem)]
        idatabase = ''
        odatabase = ''
        ischema = None
        oschema = None
        for item in ditems:
            # format = axon_to_capsul_formats.get(
                # item[1].format.name, item[1].format.name)
            database = getattr(self, item[0]).get('_database', '')
            schema = self.get_capsul_schema(database)
            if database and \
                    not neuroHierarchy.databases.database(database).builtin:
                if isinstance(item, WriteDiskItem):
                    if odatabase == '':
                        odatabase = database
                        oschema = schema
                elif idatabase == '':
                    idatabase = database
                    ischema = schema
                if idatabase != '' and odatabase != '':
                    break

        if capsul is None:
            initial_config = get_initial_capsul()
            capsul = Capsul()
            capsul.config.import_dict(initial_config)
        capsul.axon_link = \
            axon_capsul_config_link.AxonCapsulConfSynchronizer(capsul)
        capsul.axon_link.sync_axon_to_capsul()
        capsul.config.builtin.on_attribute_change.add(
            capsul.axon_link.sync_capsul_to_axon)

        if ischema:
            capsul.config.builtin.dataset.input.path = idatabase
            capsul.config.builtin.dataset.input.metadata_schema = ischema
        if oschema:
            capsul.config.builtin.dataset.output.path = odatabase
            capsul.config.builtin.dataset.output.metadata_schema = oschema

        # TODO
        ## soma-workflow execution settings
        #soma_workflow_config = getattr(context, 'soma_workflow_config', {})
        #study_config.somaworkflow_computing_resource = 'localhost'
        #study_config.somaworkflow_computing_resources_config.localhost \
            #= soma_workflow_config

        return capsul

    def get_capsul(self, context=processes.defaultContext()):
        capsul = None
        if self._capsul_process is not None:
            capsul = getattr(self._capsul_process, 'capsul', None)
        if capsul is None:
            capsul = self.init_capsul(context)
            if self._capsul_process is not None:
                self._capsul_process.capsul = capsul
        if context is not None:  # may be None during axon_to_capsul conversion
            context.capsul = capsul
        return capsul

    @classmethod
    def build_from_instance(cls, process, name=None, category=None,
                            pre_signature=None, cache=True):
        '''
        Build an Axon process instance from a Capsul process instance,
        on-the-fly, without an associated module file
        '''
        class NewProcess(CapsulProcess):
            _instance = 0
            _id = None

        if name is None:
            name = process.name
        NewProcess._id = name
        NewProcess.name = name
        NewProcess.category = category
        NewProcess.dataDirectory = None
        NewProcess.toolbox = None
        if process.definition == 'capsul.pipeline.pipeline.Pipeline':
            # special case of a pipeline built on-the-fly
            NewProcess.capsul_process = None
            # anyway it will miss things, hope setup_capsul_process()
            # will be called with a real instance later.
        else:
            NewProcess.capsul_process = process.definition
        if pre_signature:
            NewProcess.signature = pre_signature

        axon_process = NewProcess()
        axon_process.set_capsul_process(process)
        axon_process.initialization()

        if cache:
            # register the capsul / axon correspondance
            cls.capsul_to_axon_process_map[NewProcess.capsul_process] \
                = NewProcess

        return axon_process

    @classmethod
    def axon_process_from_capsul_module(cls, process,
                                        context=processes.defaultContext(),
                                        pre_signature=None):
        '''
        Create an Axon process from a capsul process instance, class, or module
        definition ('morphologist.capsul.morphologist').

        A registry of capsul:axon process classes is maintained

        May use build_from_instanc() at lower-level. The main differences
        with build_from_instance() are:

        * build_from_instance creates a new process class unconditionally
          each time it is used
        * build_from_instance will not check if a process wraping class is
          defined in axon processes
        * it will not reuse a cache of process classes
        '''
        capsul = None
        if isinstance(process, capsul.Process):
            capsul = getattr(process, 'capsul', None)
        if capsul is None:
            capsul = getattr(context, 'capsul', None)
            if capsul is None:
                capsul = cls().get_capsul(context)
        capsul_proc = capsul.executable(process)
        capsul_def = capsul_proc.definition
        axon_process = cls.capsul_to_axon_process_map.get(capsul_def)
        if axon_process is not None:
            return processes.getProcessInstance(axon_process)
        else:
            # check if an existing process class matches
            for pid, proc_class in processes._processes.items():
                if not issubclass(proc_class, CapsulProcess):
                    continue
                module = processes._processModules.get(pid)
                if module is None:
                    continue  # no associated module, may be built on-the-fly
                cid = getattr(module, 'capsul_process')
                if cid is None:
                    continue
                try:
                    cins = capsul.executable(cid)
                    # cache it anyway
                    cid_def = cins.definition
                    cls.capsul_to_axon_process_map[cid_def] = proc_class
                    if cins.__class__ is capsul_proc.__class__:
                        axon_process = processes.getProcessInstance(pid)
                        use_capsul_completion = getattr(
                            module, 'use_capsul_completion', None)
                        if use_capsul_completion is not None:
                            axon_process.__class__.use_capsul_completion \
                                = use_capsul_completion
                            axon_process.use_capsul_completion \
                                = use_capsul_completion
                        return axon_process
                except Exception:
                    # print('cannot instantiate')
                    continue
            axon_process = cls.build_from_instance(capsul_proc,
                                                   pre_signature=pre_signature)
            return axon_process

    def custom_iteration(self):
        '''
        Build a pipeline iterating over this process
        '''
        from capsul.api import Pipeline

        pipeline = Pipeline()
        pipeline.name = '%s_iteration' % self.get_capsul_process().name
        capsul = self.get_capsul()
        pipeline.capsul = capsul
        # duplicate the process
        process = capsul.executabme(self.get_capsul_process().__class__)
        # do we need to iterate over all (non-file) parameters, or let the
        # default completion system determine it ?
        # rather iterate over all
        plugs = [field.name for field in process.fields()
                 if field.name in self.signature]
        pipeline.add_iterative_process(
            pipeline.name, process, iterative_plugs=plugs)
        pipeline.autoexport_nodes_parameters(include_optional=True)
        # TODO: keep current values as 1st element in lists

        # force signature types when we know them on the iterated process
        # (optional but sometimes helps, especially when types are manually
        # defined in the process signature)
        pre_signature = Signature()
        piter = pipeline.nodes[pipeline.name]
        for field in process.fields():
            param = field.name
            if param not in self.signature:
                continue  # control field such as "nodes_activation"
            if param in piter.iterative_parameters:
                pre_signature[param] = ListOf(self.signature[param])
            else:
                pre_signature[param] = self.signature[param]

        axon_process = self.build_from_instance(
            pipeline, pre_signature=pre_signature, cache=False)

        return axon_process

    def _on_change_use_completion(self, process, dummy):
        if process.use_capsul_completion:
            cprocess = self.get_capsul_process()
            metadata = getattr(cprocess, 'metadata')

            if metadata is not None \
                    and sys._getframe(2).f_code.co_name \
                        != 'linksInitialization':
                # we don't want to complete when called from Process
                # initialization, because attributes are still empty and this
                # will result in non-empty but incomplete filenames, which is
                # rather dirty.
                metadata.generate_paths(cprocess)

    def _on_edit_pipeline(self, process, dummy):
        from brainvisa.configuration import neuroConfig
        if not neuroConfig.gui:
            return
        if process.edit_pipeline:
            processes.mainThreadActions().push(self._open_pipeline)
        else:
            self._pipeline_view = None

    def _on_capsul_gui(self, process, dummy):
        from brainvisa.configuration import neuroConfig
        if not neuroConfig.gui:
            return
        if process.capsul_gui:
            processes.mainThreadActions().push(self._open_capsul_gui)
        else:
            self._capsul_gui = None

    def _on_edit_pipeline_steps(self, process, dummy):
        from brainvisa.configuration import neuroConfig
        if not neuroConfig.gui:
            return
        steps = getattr(self._capsul_process, 'pipeline_steps', None)
        if not self.edit_pipeline_steps or not steps:
            steps_view = getattr(self, '_steps_view', None)
            if steps_view is not None:
                steps_view.ref().close()
                del steps_view
                del self._steps_view
            return
        from soma.qt_gui.controller import ControllerWidget
        from soma.qt_gui.qtThread import MainThreadLife
        steps_view = ControllerWidget(steps, live=True)
        steps_view.show()
        self._steps_view = MainThreadLife(steps_view)

    def _open_pipeline(self):
        from brainvisa.configuration import neuroConfig
        if not neuroConfig.gui:
            return
        from capsul.qt_gui.widgets import PipelineDeveloperView
        from capsul.pipeline.pipeline import Pipeline
        from soma.qt_gui.qtThread import MainThreadLife

        Pipeline.hide_nodes_activation = False
        self.propagate_parameters_to_capsul()
        mpv = PipelineDeveloperView(
            self.get_capsul_process(), allow_open_controller=True,
            show_sub_pipelines=True)
        mpv.show()
        self._pipeline_view = MainThreadLife(mpv)

    def _open_capsul_gui(self):
        from brainvisa.configuration import neuroConfig
        if not neuroConfig.gui:
            return
        from capsul.qt_gui.widgets.attributed_process_widget \
            import AttributedProcessWidget
        from soma.qt_gui.qtThread import MainThreadLife
        self.propagate_parameters_to_capsul()
        pv = AttributedProcessWidget(
            self.get_capsul_process(), enable_attr_from_filename=True,
            enable_load_buttons=True)
        if not self.use_capsul_completion:
            pv.checkbox_fom.setChecked(False)
        pv.show()
        self._capsul_gui = MainThreadLife(pv)

    def _process_field_changed(self, new_value, old_value, name):
        if name not in [f.name for f in self._capsul_process.user_fields()]:
            return
        if self.isDefault(name):
            try:
                self.setValue(name, convert_capsul_value(new_value))
            except Exception as e:
                print('exception in _process_field_changed:', e)
                print('param:', name, ', value:', new_value, 'of type:',
                      type(new_value))
                import traceback
                traceback.print_exc()
        else:
            # non-default value in axon, we cannot change it
            # and must force it back into capsul
            value = getattr(self, name, None)
            itype = self.signature.get(name)
            field = self._capsul_process.field(name)
            capsul_value = convert_to_capsul_value(value, itype, field)
            if capsul_value == getattr(self._capsul_process, name):
                return  # not changed
            setattr(self._capsul_process, name, capsul_value)

    def _on_edit_capsul_config(self, process, dummy):
        from brainvisa.configuration import neuroConfig
        if not neuroConfig.gui:
            return
        if process.edit_capsul_config:
            processes.mainThreadActions().push(self._open_capsul_config_editor)
        else:
            self._capsul_capsul_editor = None

    def _open_capsul_config_editor(self):
        from soma.qt_gui.controller import ControllerWidget
        from soma.qt_gui.qtThread import MainThreadLife
        capsul = self.get_capsul()
        scv = ControllerWidget(capsul.config, live=True)
        scv.show()
        self._capsul_config_editor = MainThreadLife(scv)

    def _get_capsul_attributes(self, param, value, itype, item=None):
        '''
        Get Axon attributes (from axon FSO/database hierarchy) of a diskitem
        and convert it into Capsul attributes system.

        If item is not None, then we must get attributes for this item number
        in a list

        Returns:
            capsul_attr: dict
            modified: bool
        '''

        if not isinstance(value, DiskItem):
            return {}, False

        cprocess = self.get_capsul_process()
        metadata = getattr(cprocess, 'metadata', None)
        if metadata is None:
            return {}, False

        schema = metadata.schema_per_parameter[param]
        meta_attr = getattr(metadata, schema)
        attributes = value.hierarchyAttributes()
        attributes = AxonToCapsulAttributesTranslation(
            meta_attr).translate(attributes)
        param_attr = [f.name for f in meta_attr.fields()]
        # we must start with current attributes values in order to keep those
        # not used with the current parameter
        capsul_attr = meta_attr.asdict()
        if item is not None:
            # get item-th element in lists
            for k, v in capsul_attr.items():
                if isinstance(v, list):
                    i = min(item, len(v) - 1)
                    if i >= 0:
                        capsul_attr[k] = v[i]
                    else:  # empty list
                        capsul_attr[k] = undefined

        modified = False
        for attribute, avalue in attributes.items():
            if avalue is not None and attribute in param_attr:
                if capsul_attr.get(attribute) != avalue:
                    capsul_attr[attribute] = avalue
                    modified = True

        database = attributes.get('_database', None)
        if database:
            if isinstance(itype, WriteDiskItem):
                db = ['output', 'input']
            else:
                allowed_db = [h.name
                                for h in neuroHierarchy.hierarchies()
                                if h.fso.name
                                not in ("shared", "spm", "fsl")]
                if database in allowed_db:
                    db = ['input', 'output']
                else:
                    db = None
            if db is not None:
                capsul = self.get_capsul()
                for idb in db:
                    ds = getattr(capsul.config.builtin.dataset, idb)
                    if ds.path != database:
                        modified = True
                        ds.path = database

            # convert FSO to FOM name
            db = neuroHierarchy.databases.database(database)
            fso = db.fso.name
            schema = self.fso_to_schema_map.get(fso, fso)
            # print('FSO:', fso, ', schema:', schema, 'for param:', param, ':', value)

            if capsul.config.builtin.dataset.input.metadata_schema \
                    != schema \
                    or capsul.config.builtin.dataset.output.schema \
                        != schema:
                capsul.config.builtin.dataset.input.metadata_schema \
                    = schema
                capsul.config.builtin.dataset.output.metadata_schema \
                    = schema

        return capsul_attr, modified

    def _on_axon_parameter_changed(self, param, process, dummy):

        from capsul.dataset import ProcessMetadata

        if getattr(self, '_capsul_process', None) is None:
            return
        if getattr(self, '_ongoing_completion', False):
            return

        # print('Process:', process.id())
        self._ongoing_completion = True
        # print('_on_axon_parameter_changed', param, process)
        try:
            value = getattr(self, param, None)
            itype = self.signature.get(param)
            field = self._capsul_process.field(param)
            capsul_value = convert_to_capsul_value(value, itype, field)
            if capsul_value == getattr(self._capsul_process, param):
                return  # not changed
            setattr(self._capsul_process, param, capsul_value)
            #if not isinstance(itype, ReadDiskItem):
                ## not a DiskItem: nothing else to do.
                #return

            capsul = self.get_capsul()
            metadata = ProcessMetadata(
                self._capsul_process,
                capsul.engine().execution_context(self._capsul_process))
            if metadata is None:
                return
            schema = metadata.schema_per_parameter[param]
            meta_attr = getattr(metadata, schema)
            modified = False
            if isinstance(value, list) and len(value) != 0:
                # if value is a list (of diskitems), then use get attributes
                # for each list item, and append the values to the list
                # attributes (which should be lists)
                capsul_attr = {}
                for i, item in enumerate(value):
                    capsul_attr_item, modified_item \
                        = self._get_capsul_attributes(param, item,
                                                      meta_attr,
                                                      itype.contentType,
                                                      item=i)
                    modified |= modified_item
                    for k, v in capsul_attr_item.items():
                        f = meta_attr.field(k)
                        if f.is_list():
                            if k not in capsul_attr:
                                li = f.default_value()
                                if len(li) > 0:
                                    if len(li) < i:
                                        li += [li[-1]] * (i - len(li))
                                else:
                                    li += [None] * i
                                capsul_attr[k] = li
                            else:
                                li = capsul_attr[k]
                            li.append(v)
                        else:
                            capsul_attr[k] = v
                    for k, v in capsul_attr.items():
                        f = meta_attr.field(k)
                        if f.is_list() and len(v) != i + 1:
                            li = f.default_value()
                            if len(li) == 0:
                                li = [None] * (i + 1 - len(v))
                            else:
                                li += [li[-1]] * (i + 1 - len(v) - len(li))
                            v += li
            else:
                capsul_attr, modified \
                    = self._get_capsul_attributes(param, value, itype)

            if modified:
                meta_attr.import_dict(capsul_attr)
                if self.use_capsul_completion:
                    metadata.generate_paths()
                    self._capsul_process.resolve_paths(
                        capsul.engine().execution_context(
                            self._capsul_process))

        finally:
            self._ongoing_completion = False

    @staticmethod
    def sphinx_to_xhtml(doc):
        if isinstance(doc, str):
            doc_utf8 = doc.encode('utf-8')
        else:
            doc_utf8 = doc
        pandoc = distutils.spawn.find_executable('pandoc')
        if pandoc:
            cmd = ['pandoc', '-r', 'rst', '-t', 'html', '--']
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE)
            out = proc.communicate(input=doc_utf8)
            out_txt = out[0]
            if not isinstance(out_txt, str):
                out_txt = out_txt.decode()
            return out_txt
        else:
            from soma.html import htmlEscape
            return htmlEscape(doc).replace('\n', '<br/>\n')

    def procdoc_from_capsul(self):
        from soma.minf import xhtml
        process = self.get_capsul_process()
        doc = process.__doc__
        # remove note added by capsul
        i = doc.rfind('\n    .. note::')
        if i >= 0:
            doc = doc[:i]

        param = {}
        procdoc = {'en': {
            'long': xhtml.XHTML.buildFromHTML(self.sphinx_to_xhtml(doc)),
            'short': '',
            'parameters': param,
        }}
        for field in process.fields():
            name = field.name
            if getattr(field, 'doc', None):
                param[name] = xhtml.XHTML.buildFromHTML(
                    self.sphinx_to_xhtml(field.doc))
        return procdoc


class AxonToCapsulAttributesTranslation:
    def __init__(self, schema_meta):
        # hard-coded for now...
        self._translations = {
            'side': AxonToCapsulAttributesTranslation._translate_side,
            'graph_version':
                AxonToCapsulAttributesTranslation._translate_graph_version,
            'labelled':
                AxonToCapsulAttributesTranslation._translate_labeling_type,
            'manually_labelled':
                AxonToCapsulAttributesTranslation._translate_labeling_type,
            'automatically_labelled':
                AxonToCapsulAttributesTranslation._translate_labeling_type,
        }

    def translate(self, attributes):
        translated = {}
        for attr, value in attributes.items():
            translator = self._translations.get(attr)
            if translator is not None:
                new_attr_dict = translator(attr, value, attributes)
                translated.update(new_attr_dict)
            else:
                translated[attr] = value
        return translated

    @staticmethod
    def _translate_side(attr, value, attributes):
        if value == 'left':
            return {attr: 'L'}
        elif value == 'right':
            return {attr: 'R'}
        else:
            return {attr: value}

    @staticmethod
    def _translate_graph_version(attr, value, attributes):
        return {'sulci_graph_version': value}

    @staticmethod
    def _translate_labeling_type(attr, value, attributes):
        if attributes.get('manually_labelled') == 'Yes':
            return {'sulci_recognition_type': 'manual'}
        elif attributes.get('automatically_labelled') == 'Yes':
            return {'sulci_recognition_type': 'auto'}
        elif attributes.get('labelled') == 'No':
            return {'sulci_recognition_type': undefined}
        return {}


class CapsulToAxonSchemaTranslation:
    schemas = {
        'bids': {
            'sub': '<subject>',
            'ses': '<session>',
            'sub': '<subject>',
            'acq': '<acquisition>',
        },
        'brainvisa': {
            'center': '<center>',
            'subject': '<subject>',
            'modality': 't1mri',
            'acquisition': '<acquisition>',
            'analysis': '<analysis>',
            'sulci_graph_version': '<graph_version>',
            'sulci_recognition_session': '<sulci_recognition_session>',
            'side': 'L',
        },
        'shared': {
            'side': 'L',
            'graph_version': '<graph_version>',
        },
        'morphologist_bids': {
            'center': '<center>',
            'subject': '<subject>',
            'modality': 't1mri',
            'acquisition': '<acquisition>',
            'analysis': '<analysis>',
            'sulci_graph_version': '<graph_version>',
            'sulci_recognition_session': '<sulci_recognition_session>',
            'side': 'L',
        },
    }

    def __init__(self):
        pass

    def translate_metadata(self, metadata, in_place=False):
        result = {}
        for sfield in metadata.fields():
            sname = sfield.name
            schema = getattr(metadata, sname)
            axon_schema = self.schemas.get(sfield.name, {})
            amap = {}
            result[sname] = amap
            for field in schema.fields():
                afield = axon_schema.get(field.name)
                if afield is not None:
                    if hasattr(afield, '__call__'):
                        afield = afield(metadata, sname, field.name,
                                        getattr(schema, field.name))
                    amap[field.name] = afield
                    if in_place:
                        setattr(schema, field.name, afield)

        return result

    @staticmethod
    def identity(metadata, scheman, attribute, value):
        return value
