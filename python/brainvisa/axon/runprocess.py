#!/usr/bin/env python2
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

from brainvisa import axon
from brainvisa.configuration import neuroConfig
import brainvisa.processes
from brainvisa.axon import processinfo
import sys, re, types
from optparse import OptionParser, OptionGroup

usage = '''Usage: %prog [options] processname [arg1] [arg2] ... [argx=valuex] [argy=valuey] ...

Example:
%prog --enabledb threshold ~/data/irm.ima /tmp/th.nii threshold1=80

Named arguments (in the shape argx=valuex) may address sub-processes of a pipeline, using the dot separator:

PrepareSubject.t1mri=/home/myself/mymri.nii
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
#group1.add_option('--enablegui', dest='enablegui', action='store_true',
    #default=False,
    #help='enable graphical user interface for interactive processes')
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
                  default=None, help='Input files processing: local_path, '
                  'transfer, translate, or translate_shared. The default is '
                  'local_path if the computing resource is the localhost, or '
                  'translate_shared otherwise.')
group2.add_option('--keep-workflow', dest='keep_workflow', action='store_true',
                  help='keep the workflow in the computing resource database '
                  'after execution. By default it is removed.')
group2.add_option('--keep-failed-workflow', dest='keep_failed_workflow',
                  action='store_true',
                  help='keep the workflow in the computing resource database '
                  'after execution, if it has failed. By default it is '
                  'removed.')
parser.add_option_group(group2)
group3 = OptionGroup(parser, 'Help',
                     description='Help and documentation options')
group3.add_option('--list-processes', dest='list_processes',
    action='store_true',
    help='List processes and exit. sorting / filtering are controlled by the '
    'following options.')
group3.add_option('--sort-by', dest='sort_by',
    help='List processed by: id, name, toolbox, or role')
group3.add_option('--proc-filter', dest='proc_filter', action='append',
    help='filter processes list. Several filters may be used to setup several '
    'rules. Rules have the shape: attribute="filter_expr", filter_expr is a '
    'regex.\n'
    'Ex: id=".*[Ss]ulci.*"')
group3.add_option('--hide-proc-attrib', dest='hide_proc_attrib',
    action='append', default=[],
    help='in processes list, hide selected attribute (several values allowed)')
group3.add_option('--process-help', dest='process_help',
    action='append',
    help='display specified process help')
parser.add_option_group(group3)

parser.disable_interspersed_args()
(options, args) = parser.parse_args()

#if options.enablegui:
    #neuroConfig.gui = True
    #from PyQt4 import QtGui
    #qapp = QtGui.QApplication([])
#else:
neuroConfig.gui = False
if not options.enabledb:
    neuroConfig.fastStart = True
if options.historyBook:
    neuroConfig.historyBookDirectory = options.historyBook
if not options.enabledb and not options.historyBook:
    neuroConfig.logFileName = ''

axon.initializeProcesses()

if options.list_processes:
    sort_by = options.sort_by
    if not sort_by:
        sort_by = 'id'
    else: print('sort-by:', sort_by)
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
    if type(arg) in types.StringTypes:
        m = kwre.match(arg)
        if m is not None:
            kwargs[m.group(1)] = \
                neuroConfig.convertCommandLineParameter(m.group(3))
            todel.append(arg)
args = [arg for arg in args if arg not in todel]

if options.soma_workflow:

    from brainvisa import workflow
    from soma_workflow import client as swclient
    from soma_workflow import constants as swconstants
    import socket

    resource_id = options.resource_id
    login = options.login
    password = options.password
    config = None #options.config
    rsa_key_pass = options.rsa_key_pass
    queue = options.queue
    file_processing = []

    for opt in (options.input_file_processing, options.output_file_processing):
        if opt is None:
            if resource_id in ('localhost', None, socket.gethostname()):
                file_proc = workflow.ProcessToSomaWorkflow.NO_FILE_PROCESSING
            else:
                file_proc = workflow.ProcessToSomaWorkflow.BV_DB_SHARED_PATH
        elif opt == 'local_path':
            file_proc = workflow.ProcessToSomaWorkflow.NO_FILE_PROCESSING
        elif opt == 'transfer':
            file_proc = workflow.ProcessToSomaWorkflow.FILE_TRANSFER
        elif opt == 'translate':
            file_proc = workflow.ProcessToSomaWorkflow.SHARED_RESOURCE_PATH
        elif opt == 'translate_shared':
            file_proc = workflow.ProcessToSomaWorkflow.BV_DB_SHARED_PATH
        else:
            raise ValueError('unrecognized file processing option')
        file_processing.append(file_proc)

    process = brainvisa.processes.getProcessInstance(args[0])
    context = brainvisa.processes.defaultContext()
    context._setArguments(*(process,) + tuple(args[1:]), **kwargs)
    wf = workflow.process_to_workflow(
        process, None,
        input_file_processing=file_processing[0],
        output_file_processing=file_processing[1],
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
    if file_processing[0] == workflow.ProcessToSomaWorkflow.FILE_TRANSFER:
        print('transfering input files...')
        swclient.Helper.transfer_input_files(wid, wc)
        print('input transfers done.')
    swclient.Helper.wait_workflow(wid, wc)
    print('finished.')
    workflow_status = wc.workflow_status(wid)
    elements_status = wc.workflow_elements_status(wid)
    failed_jobs = [element for element in elements_status[0] \
        if element[1] != swconstants.DONE \
            or element[3][0] != swconstants.FINISHED_REGULARLY]

    if file_processing[1] == workflow.ProcessToSomaWorkflow.FILE_TRANSFER:
        print('transfering output files...')
        swclient.Helper.transfer_output_files(wid, wc)
        print('output transfers done.')

    if not options.keep_failed_workflow and not options.keep_workflow:
        wc.delete_workflow(wid)

    if workflow_status != swconstants.WORKFLOW_DONE:
        raise RuntimeError('Workflow did not finish regularly: %s'
                           % workflow_status)
    print('workflow status OK')
    if len(failed_jobs) != 0:
        raise RuntimeError('Morphologist jobs failed:', failed_jobs)

    if not options.keep_workflow and options.keep_failed_workflow:
        wc.delete_workflow(wid)

else:
    brainvisa.processes.defaultContext().runProcess(*args, **kwargs)

sys.exit(neuroConfig.exitValue)


