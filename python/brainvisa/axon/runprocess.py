#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  This software and supporting documentation were developed by
#      CEA/DSV/SHFJ and IFR 49
#      4 place du General Leclerc
#      91401 Orsay cedex
#      France
#
# This software is governed by the CeCILL license version 2 under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the
# terms of the CeCILL license version 2 as circulated by CEA, CNRS
# and INRIA at the following URL "http://www.cecill.info".
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license version 2 and that you accept its terms.

"""
brainvisa.axon.runprocess is not a real python module, but rather an executable script with commandline arguments and options parsing. It is provided as a module just to be easily called via the python command in a portable way:
python -m brainvisa.axon.runprocess <process name> <process arguments>
"""

from __future__ import print_function

from __future__ import absolute_import
from brainvisa import axon
from brainvisa.configuration import neuroConfig
import brainvisa.processes
from brainvisa.axon import processinfo
import sys
import re
import types
from optparse import OptionParser, OptionGroup
import six
import os


def get_process_with_params(process_name, iterated_params=[], *args, **kwargs):
    ''' Instantiate a process, or an iteration over processes, and fill in its
    parameters.

    Parameters
    ----------
    process_name: string
        name (ID) of the process to instantiate
    iterated_params: list (optional)
        parameters names which should be iterated on. If this list is not
        empty, an iteration process is built. All parameters values
        corresponding to the selected names should be lists with the same size.
    *args:
        sequential parameters for the process. In iteration, "normal"
        parameters are set with the same value for all iterations, and iterated
        parameters dispatch their values to each iteration.
    **kwargs:
        named parameters for the process. Same as above for iterations.

    Returns
    -------
    process: Process instance
    '''
    process = brainvisa.processes.getProcessInstance(process_name)
    context = brainvisa.processes.defaultContext()

    # check for iterations
    if iterated_params:
        iterated_values = {}
        signature = process.signature
        params = list(signature.keys())
        iterated_args = []
        n_iter = 0
        for it_param in iterated:
            if it_param in kwargs:
                values = kwargs.pop(it_param)
                iterated_values[it_param] = values
                if n_iter == 0:
                    n_iter = len(values)
                elif len(values) != n_iter:
                    raise ValueError(
                        'unmatched iteration numbers for iterated parameters')
            else:
                if it_param not in signature:
                    raise KeyError(
                        'iterated parameter %s is not in the process parameters'
                        % it_param)
                i_par = params.index(it_param)
                if len(args) <= i_par:
                    raise ValueError(
                        'Iterated parameter %s has no specified value in process '
                        'parameters' % it_param)
                values = args[i_par]
                iterated_args.append(i_par)
                if n_iter == 0:
                    n_iter = len(values)
                elif len(values) != n_iter:
                    raise ValueError(
                        'unmatched iteration numbers for iterated parameters')

        # build list of processes for iteration
        processes = [process] \
            + [brainvisa.processes.getProcessInstance(process_name)
               for i in six.moves.xrange(n_iter - 1)]
        # fill in their parameters
        for i_proc, process in enumerate(processes):
            p_args = list(args)
            p_kwargs = dict(kwargs)
            for i in iterated_args:
                p_args[i] = args[i][i_proc]
            p_kwargs.update(dict([(k, value[i_proc])
                                  for k, value in six.iteritems(iterated_values)]))
            context._setArguments(*(process,) + tuple(p_args), **p_kwargs)
        iteration = brainvisa.processes.IterationProcess(
            '%s iteration' % process.name, processes)
        process = iteration

    else:
        # not iterated
        context._setArguments(*(process,) + tuple(args), **kwargs)

    return process


def run_process_with_distribution(
        process, use_soma_workflow=False, resource_id=None, login=None,
        password=None, config=None, rsa_key_pass=None, queue=None,
        input_file_processing=None, output_file_processing=None,
        keep_workflow=False, keep_failed_workflow=False):
    ''' Run the given process, either sequentially or distributed through
    Soma-Workflow.

    Parameters
    ----------
    process: Process instance
        the process to execute (or pipeline, or iteration...)
    use_soma_workflow: bool (default=False)
        if False, run sequentially, otherwise use Soma-Workflow. Its
        configuration has to be setup and valid for non-local execution, and
        additional login and file transfer options may be used.
    resource_id: string (default=None)
        soma-workflow resource ID, defaults to localhost
    login: string
        login to use on the remote computing resource
    password: string
        password to access the remote computing resource. Do not specify it if
        using a ssh key.
    config: dict (optional)
        Soma-Workflow config: Not used for now...
    rsa_key_pass: string
        RSA key password, for ssh key access
    queue: string
        Queue to use on the computing resource. If not specified, use the
        default queue.
    input_file_processing: brainvisa.workflow.ProcessToSomaWorkflow processing code
        Input files processing: local_path (NO_FILE_PROCESSING),
        transfer (FILE_TRANSFER), translate (SHARED_RESOURCE_PATH),
        or translate_shared (BV_DB_SHARED_PATH).
    output_file_processing: same as for input_file_processing
        Output files processing: local_path (NO_FILE_PROCESSING),
        transfer (FILE_TRANSFER), or translate (SHARED_RESOURCE_PATH).
        The default is local_path.
    keep_workflow: bool
        keep the workflow in the computing resource database after execution.
        By default it is removed.
    keep_failed_workflow: bool
        keep the workflow in the computing resource database after execution,
        if it has failed. By default it is removed.
    '''
    if use_soma_workflow:
        from brainvisa import workflow
        from soma_workflow import client as swclient
        from soma_workflow import constants as swconstants

        if input_file_processing is None:
            input_file_processing \
                = workflow.ProcessToSomaWorkflow.NO_FILE_PROCESSING
        if output_file_processing is None:
            output_file_processing \
                = workflow.ProcessToSomaWorkflow.NO_FILE_PROCESSING

        context = brainvisa.processes.defaultContext()
        wf = workflow.process_to_workflow(
            process, None,
            input_file_processing=input_file_processing,
            output_file_processing=output_file_processing,
            context=context)

        wc = swclient.WorkflowController(
            resource_id=resource_id,
            login=login,
            password=password,
            config=config,
            rsa_key_pass=rsa_key_pass)
        print('workflow controller init done.')
        wid = wc.submit_workflow(wf, name=process.name, queue=queue)
        print('running...')
        if input_file_processing \
                == workflow.ProcessToSomaWorkflow.FILE_TRANSFER:
            print('transfering input files...')
            swclient.Helper.transfer_input_files(wid, wc)
            print('input transfers done.')
        swclient.Helper.wait_workflow(wid, wc)
        print('finished.')
        workflow_status = wc.workflow_status(wid)
        elements_status = wc.workflow_elements_status(wid)
        failed_jobs = [element for element in elements_status[0]
                       if element[1] != swconstants.DONE
                       or element[3][0] != swconstants.FINISHED_REGULARLY]

        if output_file_processing \
                == workflow.ProcessToSomaWorkflow.FILE_TRANSFER:
            print('transfering output files...')
            swclient.Helper.transfer_output_files(wid, wc)
            print('output transfers done.')

        if not keep_failed_workflow and not keep_workflow:
            wc.delete_workflow(wid)

        if workflow_status != swconstants.WORKFLOW_DONE:
            raise RuntimeError('Workflow did not finish regularly: %s'
                               % workflow_status)
        print('workflow status OK')
        if len(failed_jobs) != 0:
            raise RuntimeError('Jobs failed, n=%d:' % len(failed_jobs),
                               failed_jobs)

        if not keep_workflow and keep_failed_workflow:
            wc.delete_workflow(wid)

    else:
        brainvisa.processes.defaultContext().runProcess(process)


# main

usage = '''Usage: %prog [options] processname [arg1] [arg2] ... [argx=valuex] [argy=valuey] ...

Example:
%prog --enabledb threshold ~/data/irm.ima /tmp/th.nii threshold1=80

Named arguments (in the shape argx=valuex) may address sub-processes of a pipeline, using the dot separator:

PrepareSubject.t1mri=/home/myself/mymri.nii

For a more precise description, please look at the web documentation:
https://brainvisa.info/axon/user_doc/axon_manual2.html#brainvisa-commandline
'''

parser = OptionParser(description='Run a single BrainVISA / Axon process',
                      usage=usage)
group1 = OptionGroup(parser, 'Config',
                     description='Processing configuration, database options')
group1.add_option('--enabledb', dest='enabledb', action='store_true',
                  default=False,
                  help='enable databasing (slower startup, but all features enabled)')
group1.add_option('--historyBook', dest='historyBook', action='append',
                  help='store history information files in this directory (otherwise '
                  'disabled unless dabasing is enabled)')
# group1.add_option('--enablegui', dest='enablegui', action='store_true',
    # default=False,
    # help='enable graphical user interface for interactive processes')
group1.add_option('--logFile', dest='logFile', default=None,
                  help='specify the log file to use. '
                  'Default is the usual brainvisa.log if databasing is enabled, else no log '
                  'file is used.')
parser.add_option_group(group1)

group2 = OptionGroup(parser, 'Processing',
                     description='Processing options, distributed execution')
group2.add_option('--swf', '--soma_workflow', dest='soma_workflow',
                  action='store_true', help='use soma_workflow. Soma-Workflow '
                  'configuration has to be setup and valid for non-local '
                  'execution, and additional login and file transfer options '
                  'may be used')
group2.add_option('-r', '--resource_id', dest='resource_id', default=None,
                  help='soma-workflow resource ID, defaults to localhost')
group2.add_option('-u', '--user', dest='login', default=None,
                  help='login to use on the remote computing resource')
group2.add_option('-p', '--password', dest='password', default=None,
                  help='password to access the remote computing resource. '
                  'Do not specify it if using a ssh key')
group2.add_option('--rsa-pass', dest='rsa_key_pass', default=None,
                  help='RSA key password, for ssh key access')
group2.add_option('--queue', dest='queue', default=None,
                  help='Queue to use on the computing resource. If not '
                  'specified, use the default queue.')
group2.add_option('--input-processing', dest='input_file_processing',
                  default=None, help='Input files processing: local_path, '
                  'transfer, translate, or translate_shared. The default is '
                  'local_path if the computing resource is the localhost, or '
                  'translate_shared otherwise.')
group2.add_option('--output-processing', dest='output_file_processing',
                  default=None, help='Output files processing: local_path, '
                  'transfer, or translate. The default is local_path.')
group2.add_option('--keep-workflow', dest='keep_workflow', action='store_true',
                  help='keep the workflow in the computing resource database '
                  'after execution. By default it is removed.')
group2.add_option('--keep-failed-workflow', dest='keep_failed_workflow',
                  action='store_true',
                  help='keep the workflow in the computing resource database '
                  'after execution, if it has failed. By default it is '
                  'removed.')
parser.add_option_group(group2)

group3 = OptionGroup(parser, 'Iteration',
                     description='Iteration')
group3.add_option('-i', '--iterate', dest='iterate_on', action='append',
                  help='Iterate the given process, iterating over the given '
                  'parameter(s). Multiple parameters may be iterated joinly '
                  'using several -i options. In the process parameters, '
                  'values are replaced by lists, all iterated lists should '
                  'have the same size.\n'
                  'Ex:\n'
                  'axon-runprocess -i par_a -i par_c a_process par_a="[1, 2]" '
                  'par_b="something" par_c="[\\"one\\", \\"two\\"]"')
parser.add_option_group(group3)

group4 = OptionGroup(parser, 'Help',
                     description='Help and documentation options')
group4.add_option('--list-processes', dest='list_processes',
                  action='store_true',
                  help='List processes and exit. sorting / filtering are controlled by the '
                  'following options.')
group4.add_option('--sort-by', dest='sort_by',
                  help='List processed by: id, name, toolbox, or role')
group4.add_option('--proc-filter', dest='proc_filter', action='append',
                  help='filter processes list. Several filters may be used to setup several '
                  'rules. Rules have the shape: attribute="filter_expr", filter_expr is a '
                  'regex.\n'
                  'Ex: id=".*[Ss]ulci.*"')
group4.add_option('--hide-proc-attrib', dest='hide_proc_attrib',
                  action='append', default=[],
                  help='in processes list, hide selected attribute (several values allowed)')
group4.add_option('--process-help', dest='process_help',
                  action='append',
                  help='display specified process help')
parser.add_option_group(group4)

parser.disable_interspersed_args()
(options, args) = parser.parse_args()

print('Initializing brainvisa... (takes a while)...')
sys.stdout.flush()

# if options.enablegui:
    # neuroConfig.gui = True
    # from soma.qt_gui.qt_backend import QtGui
    # qapp = QtGui.QApplication([])
# else:
neuroConfig.gui = False
if not options.enabledb:
    neuroConfig.fastStart = True
if options.historyBook:
    neuroConfig.historyBookDirectory = options.historyBook
if not options.logFile is None:
    neuroConfig.logFileName = options.logFile
else:
    if not options.enabledb and not options.historyBook:
        neuroConfig.logFileName = ''

# redirect stderr/stdout to avoid printing error messages from processes
stdout = sys.stdout
stderr = sys.stderr
tmp = []
if os.path.exists('/dev/null'):
    outfile = open('/dev/null', 'a')
else:
    import tempfile
    x = mkstemp()[0]
    os.close(x[0])
    outfile = open(x[1], 'a')
    tmp.append(x[1])
    del x
# print('--- disabling stdout/err ---')
sys.stdout = outfile
sys.stderr = outfile
# print('*** DISABLED. ***')
try:

    axon.initializeProcesses()

finally:
    sys.stderr = stderr
    sys.stdout = stdout
    outfile.close()
    del outfile
    x = None
    for x in tmp:
        os.unlink(x)
    del x, tmp
    # print('*** Re-enabling stdout/err ***')



if options.list_processes:
    sort_by = options.sort_by
    if not sort_by:
        sort_by = 'id'
    else:
        print('sort-by:', sort_by)
    processinfo.process_list_help(sort_by, sys.stdout,
                                  proc_filter=options.proc_filter,
                                  hide=options.hide_proc_attrib)
    sys.exit(0)

if options.process_help:
    for process in options.process_help:
        processinfo.process_help(process)
    sys.exit(0)

args = tuple((neuroConfig.convertCommandLineParameter(i) for i in args))
kwre = re.compile('([a-zA-Z_](\.?[a-zA-Z0-9_])*)\s*=\s*(.*)$')
kwargs = {}
todel = []
for arg in args:
    if isinstance(arg, six.string_types):
        m = kwre.match(arg)
        if m is not None:
            kwargs[m.group(1)] = \
                neuroConfig.convertCommandLineParameter(m.group(3))
            todel.append(arg)
args = [arg for arg in args if arg not in todel]

# get the main process
process_name = args[0]
args = args[1:]

iterated = options.iterate_on
process = get_process_with_params(process_name, iterated, *args, **kwargs)

resource_id = options.resource_id
login = options.login
password = options.password
config = None  # options.config
rsa_key_pass = options.rsa_key_pass
queue = options.queue
file_processing = []

if options.soma_workflow:

    from brainvisa import workflow
    import socket

    for io, opt in enumerate((options.input_file_processing,
                              options.output_file_processing)):
        if opt is None:
            if io == 0 and resource_id not in ('localhost', None,
                                               socket.gethostname()):
                file_proc = workflow.ProcessToSomaWorkflow.BV_DB_SHARED_PATH
            else:
                file_proc = workflow.ProcessToSomaWorkflow.NO_FILE_PROCESSING
        elif opt == 'local_path':
            file_proc = workflow.ProcessToSomaWorkflow.NO_FILE_PROCESSING
        elif opt == 'transfer':
            file_proc = workflow.ProcessToSomaWorkflow.FILE_TRANSFER
        elif opt == 'translate':
            file_proc = workflow.ProcessToSomaWorkflow.SHARED_RESOURCE_PATH
        elif opt == 'translate_shared' and io == 0:
            file_proc = workflow.ProcessToSomaWorkflow.BV_DB_SHARED_PATH
        else:
            raise ValueError('unrecognized file processing option')
        file_processing.append(file_proc)

else:
    file_processing = [None, None]

run_process_with_distribution(
    process, options.soma_workflow, resource_id=resource_id, login=login,
    password=password, config=config, rsa_key_pass=rsa_key_pass, queue=queue,
    input_file_processing=file_processing[0],
    output_file_processing=file_processing[1],
    keep_workflow=options.keep_workflow,
    keep_failed_workflow=options.keep_failed_workflow)


sys.exit(neuroConfig.exitValue)
