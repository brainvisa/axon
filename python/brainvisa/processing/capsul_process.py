''' Specialized Process class to link with CAPSUL processes and pipelines.

the aim is to allow using a Capsul process/pipeline as an Axon process (or at least, ease it). Such a process would like the following:

::

    from brainvisa.processes import *
    from brainvisa.processing import capsul_process

    name = 'A Capusl process ported to Axon'
    userLevel = 0
    base_class = capsul_process.CapsulProcess
    capsul_process = 'morphologist.capsul.morphologist.Morphologist'

Explanation:

The process should inherit the CapsulProcess class (itself inheriting the standard Process). To do so, it declares the "base_class" variable to this CapsulProcess class type.

The it should instantiate the appropriate Capsul process. This is done by overloading the setup_capsul_process() method, which will instantiate the Capsul process and set it into the Axon proxy process.

The underlying Capsul process traits will be exported to the Axon signature automatically. This behaviour can be avoided or altered by overloading the initialize() method, which we did not define in the above example.

The process also does not have an execution() function. This is normal: CapsulProcess already defines an executionWorkflow() method which will generate a Soma-Workflow workflow which will integrate in the process or parent pipeline (or iteration) workflow.

See also :doc:`capsul`

'''

from __future__ import print_function

import brainvisa.processes as processes
from brainvisa.data import neuroData
from brainvisa.data.readdiskitem import ReadDiskItem
from brainvisa.data.writediskitem import WriteDiskItem
from brainvisa.processes import getAllFormats
from brainvisa.data.neuroData import Signature
from brainvisa.data.neuroDiskItems import DiskItem
from brainvisa.data import neuroHierarchy
from traits import trait_types
import traits.api as traits
import six


def fileOptions(filep):
    if hasattr(filep, 'output') and filep.output:
        return (WriteDiskItem, ['Any Type', getAllFormats()])
    return (ReadDiskItem, ['Any Type', getAllFormats()])


def choiceOptions(choice):
    return [x for x in choice.trait_type.values]


def listOptions(param):
    item_type = param.inner_traits[0]
    return [make_parameter(item_type)]


param_types_table = \
    {
        trait_types.Bool: neuroData.Boolean,
        trait_types.String: neuroData.String,
        trait_types.Str: neuroData.String,
        trait_types.Float: neuroData.Number,
        trait_types.Int: neuroData.Integer,
        trait_types.File: fileOptions,
        trait_types.File: fileOptions,
        trait_types.Enum: (neuroData.Choice, choiceOptions),
        trait_types.List: (neuroData.ListOf, listOptions),
        trait_types.ListFloat: (neuroData.ListOf, listOptions),
    }


def make_parameter(param, name='<unnamed>'):
    newtype = param_types_table.get(type(param.trait_type))
    paramoptions = []
    if newtype is None:
        print('no known converted type for', name, ':',
              type(param.trait_type))
        newtype = neuroData.String
    if isinstance(newtype, tuple):
        paramoptions = newtype[1](param)
        newtype = newtype[0]
    elif hasattr(newtype, 'func_name'):
        newtype, paramoptions = newtype(param)
    return newtype(*paramoptions)


def convert_capsul_value(value):
    if isinstance(value, traits.TraitListObject):
        value = [convert_capsul_value(x) for x in value]
    return value


def convert_to_capsul_value(value):
    if isinstance(value, DiskItem):
        value = value.fullPath()
    return value


class CapsulProcess(processes.Process):
    ''' Specialized Process to link with a CAPSUL process or pipeline.

    See the :py:mod:`brainvisa.processing.capsul_process` doc for details.
    '''

    def __init__(self):
        self._capsul_process = None
        self.setup_capsul_process()
        super(CapsulProcess, self).__init__()


    def set_capsul_process(self, process):
        ''' Sets a CAPSUL process into the Axon (proxy) process
        '''
        self._capsul_process = process


    def setup_capsul_process(self):
        ''' This method is in charge of instantiating the appropriate CAPSUL process or pipeline, and setting it into the Axon process (self), using the set_capsul_process() method.

        It may be overloaded by children processes, but the default implementation looks for a variable "capsul_process" in the process source file which provides the Capsul module/process name (as a string), for instance:

        ::

          capsul_process = "morphologist.capsul.axon.t1biascorrection.T1BiasCorrection"

        This is basically the only thing the process must do.
        '''
        module = processes._processModules[self._id]
        capsul_process = getattr(module, 'capsul_process')
        if capsul_process:
            from capsul.api import get_process_instance
            process = get_process_instance(capsul_process)
            self.set_capsul_process(process)


    def get_capsul_process(self):
        ''' Get the underlying CAPSUL process '''
        return self._capsul_process


    def initialization(self):
        ''' This specialized initialization() method sets up a default signature for the process, duplicating every user trait of the underlying CAPSUL process.

        As some parameter types and links will not be correctly translated, it is possible to prevent this automatic behaviour, and to setup manually
        a new signature, by overloading the initialization() method.

        In such a case, the process designer will also probably have to overload the propagate_parameters_to_capsul() method to setup the underlying Capsul process parameters from the Axon one, since there will not be a direct correspondance any longer.
        '''
        process = self.get_capsul_process()
        signature_args = []
        excluded_traits = set(('nodes_activation', 'pipeline_steps'))
        optional = []
        for name, param in process.user_traits().iteritems():
            if name in excluded_traits:
                continue
            parameter = make_parameter(param, name)
            signature_args += [name, parameter]
            if param.optional:
                optional.append(name)
        signature = Signature(*signature_args)
        signature['edit_pipeline'] = neuroData.Boolean()
        self.__class__.signature = signature
        self.changeSignature(signature)

        if optional:
            self.setOptional(*optional)
        self.edit_pipeline = False
        for name in process.user_traits():
            if name in excluded_traits:
                continue
            value = getattr(process, name)
            if value not in (traits.Undefined, ''):
                setattr(self, name, convert_capsul_value(value))

        self.linkParameters(None, 'edit_pipeline', self._on_edit_pipeline)


    def propagate_parameters_to_capsul(self):
        ''' Set the underlying Capsul process parameters values from the Axon process (self) parameters values.

        This method will be called before execution to build the workflow.

        By default, it assumes a direct correspondance between Axon and Capsul processes parameters, so it will just copy all parameters values. If the initialization() method has been specialized in a particular process, this direct correspondance will likely be broken, so this method should also be overloaded.
        '''
        process = self.get_capsul_process()
        for name in six.iterkeys(self.signature):
            setattr(process, name,
                    convert_to_capsul_value(getattr(self, name)))


    def executionWorkflow(self, context=processes.defaultContext()):
        ''' Build the workflow for execution. The workflow will be integrated in the parent pipeline workflow, if any.

        StudyConfig options are handled to support local or remote execution, file transfers / translations and other specific stuff.

        FOM completion is not performed yet.
        '''

        from capsul.process import process_with_fom
        from capsul.pipeline import pipeline_workflow

        study_config = self.init_study_config(context)

        self.propagate_parameters_to_capsul()
        process = self.get_capsul_process()

        #capsul_pwf = process_with_fom.ProcessWithFom(process, study_config)
        #capsul_pwf.create_completion()

        wf = pipeline_workflow.workflow_from_pipeline(
            process, study_config=study_config)  #, jobs_priority=priority)
        jobs = wf.jobs
        dependencies = wf.dependencies
        groups = wf.groups

        return jobs, dependencies, groups


    def init_study_config(self, context=processes.defaultContext()):
        ''' Build a Capsul StudyConfig object if not present in the context,
        set it up, and return it
        '''
        from capsul.study_config.study_config import StudyConfig
        from soma.wip.application.api import Application as Appli2

        study_config = getattr(context, 'study_config', None)

        #axon_to_capsul_formats = {
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

        ditems = [(name, item) for name, item in six.iteritems(self.signature)
                  if isinstance(item, DiskItem)]
        database = ''
        #format = ''
        for item in ditems:
            #format = axon_to_capsul_formats.get(
                #item[1].format.name, item[1].format.name)
            database = getattr(self, item[0]).get('_database', '')
            if database and \
                    not neuroHierarchy.databases.database(database).builtin:
                break
            database = ''

        if study_config:
            study_config.input_directory = database
            study_config.output_directory = database
        else:
            configuration = Appli2().configuration
            initial_study_config = {
                "input_directory" : database,
                "output_directory" : database,
                "input_fom" : "morphologist-auto-1.0",
                "output_fom" : "morphologist-auto-1.0",
                "shared_fom" : "shared-brainvisa-1.0",
                "spm_directory" : configuration.SPM.spm8_standalone_path,
                "use_soma_workflow" : True,
                "use_fom" : True,
                "volumes_format" : "NIFTI gz",
                "meshes_format" : "GIFTI",
            }

            study_config = StudyConfig(
                init_config=initial_study_config,
                modules=StudyConfig.default_modules + ['BrainVISAConfig',
                                                       'FomConfig'])

        # soma-workflow execution settings
        soma_workflow_config = getattr(context, 'soma_workflow_config', {})
        study_config.somaworkflow_computing_resource = 'localhost'
        study_config.somaworkflow_computing_resources_config.localhost \
            = soma_workflow_config

        return study_config


    def _on_edit_pipeline(self, process, dummy):
        from brainvisa.configuration import neuroConfig
        if not neuroConfig.gui:
            return
        if process.edit_pipeline:
            processes.mainThreadActions().push(self._open_pipeline)
        else:
            self._pipeline_view = None

    def _open_pipeline(self):
        from capsul.qt_gui.widgets import PipelineDevelopperView
        from capsul.pipeline import Pipeline
        from brainvisa.tools.mainthreadlife import MainThreadLife
        Pipeline.hide_nodes_activation = False
        mpv = PipelineDevelopperView(
          self.get_capsul_process(), allow_open_controller=True,
          show_sub_pipelines=True)
        mpv.show()
        self._pipeline_view = MainThreadLife(mpv)


