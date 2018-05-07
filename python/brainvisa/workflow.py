# -*- coding: utf-8 -*-
from __future__ import print_function
import collections
import os
import sys
import pickle
import types
import six

from brainvisa.processes import ProcessExecutionNode, SerialExecutionNode, ParallelExecutionNode, defaultContext
from brainvisa.data.readdiskitem import ReadDiskItem
from brainvisa.data.writediskitem import WriteDiskItem
from brainvisa.data.neuroData import ListOf
from brainvisa.data import neuroHierarchy
from brainvisa.data.neuroDiskItems import DiskItem

from soma_workflow.constants import *
from soma_workflow.client import Job, FileTransfer, SharedResourcePath, Group, Workflow, Helper, OptionPath


class ProcessToWorkflow(object):
    JOB = 'j'
    NATIVE_JOB = 'n'
    PARALLEL_GROUP = 'p'
    SERIAL_GROUP = 's'
    FILE = 'f'

    def __init__(self, process):
        self.process = process
        self._identifiers = {}
        # self._groups = groupId -> ( label, content )
        self._groups = {None: (None, [])}
        self._inGroup = {}
        self._jobs = {}
        # self._files = fileId -> (fileName, fullPaths)
        self._files = {}
        # self._filesNames = fileName -> fileId
        self._fileNames = {}
        # self._iofiles = fileId -> (list of job for which the file is an
        # input, list of job for which the file is an output)
        self._iofiles = {}
        # list of history boook directories to transfer back after wf execution
        self._historyBooks = {}
        # execution node to group ID map
        self._nodeToId = {}
        self._nodeHistoryBooks = set()

        self.brainvisa_cmd = [os.path.basename(sys.executable),
                              '-m', 'brainvisa.axon.runprocess']

    def escape(self):
        return None

    def _createIdentifier(self, type):
        count = self._identifiers.get(type, 0) + 1
        self._identifiers[type] = count
        return type + str(count)

    def flatten(self, l):
        return (sum(map(self.flatten, l), []) if isinstance(l, list) else [l])

    def parameterToString(self, process, name):
        def toString(value, useHierarchy, escape=None, level=0):
            # This function converts values to string
            # also converting lists recursively
            if isinstance(value, DiskItem):
                hierarchyAttributes = value.hierarchyAttributes()
                hierarchyAttributes.pop('_database', None)
                if hierarchyAttributes and useHierarchy:
                    value = repr(hierarchyAttributes)
            else:
                if isinstance(value, list) \
                        or isinstance(value, tuple):
                    new_value = []
                    for element in value:
                        new_value.append(
                            toString(element, useHierarchy, escape, level + 1))
                    if isinstance(value, tuple):
                        value = tuple(new_value)
                    else:
                        value = new_value

            if level == 0:
                if isinstance(value, basestring) and (value.startswith('"')
                                                      or value.startswith("'") or value == "None"):
                    value = '"' + str(value) + '"'
                else:
                    value = str(value)
                if escape is not None:
                    for e, r in escape:
                        value = value.replace(e, r)

            return value

        value = getattr(process, name)
        useHierarchy = name in getattr(
            process, 'workflow_transmit_by_attributes', ())
        value = toString(value, useHierarchy, escape=self.escape())

        return value

    def _processExecutionNode(self, eNode, inGroup, priority=None):
        if eNode is not None and eNode.isSelected():
            if isinstance(eNode, ProcessExecutionNode):
                pENode = eNode._process._executionNode
                # print('==>eNode.name() :', eNode.name(), ', pENode : ',
                # pENode)
                if pENode is None:
                    if hasattr(eNode._process, 'executionWorkflow'):
                        # Register native jobs from the process
                        jobId = self._registerJob(
                            self.NATIVE_JOB, eNode._process, priority, inGroup)

                    else:
                        # Create job
                        jobId = self._registerJob(
                            self.JOB, eNode._process, priority, inGroup)
                    return
            else:
                pENode = eNode

            if isinstance(pENode, ParallelExecutionNode):
                process = getattr(eNode, '_process', None)
                if process is None:
                    label = eNode.name()
                else:
                    label = process.name
                # Create parallel group
                groupId = self._registerGroup(
                    self.PARALLEL_GROUP, label, inGroup)
                self._nodeToId[eNode] = groupId
                children_count = len(eNode.childrenNames())
                cmpt = 0
                for i in eNode.children():
                    if priority == None:
                        self._processExecutionNode(i,
                                                   groupId,
                                                   priority=children_count - cmpt)
                        cmpt = cmpt + 1
                    else:
                        self._processExecutionNode(i, groupId, priority)

            elif isinstance(pENode, SerialExecutionNode):
                process = getattr(eNode, '_process', None)
                if process is None:
                    label = eNode.name()
                else:
                    label = process.name
                # Create serial group
                groupId = self._registerGroup(
                    self.SERIAL_GROUP, label, inGroup)
                self._nodeToId[eNode] = groupId

                if priority == None:
                    for i in eNode.children():
                        self._processExecutionNode(i, groupId, 0)
                else:
                    for i in eNode.children():
                        self._processExecutionNode(i, groupId, priority)
            else:
                if priority == None:
                    for i in eNode.children():
                        self._processExecutionNode(i, inGroup, 0)
                else:
                    for i in eNode.children():
                        self._processExecutionNode(i, inGroup, priority)

    def doIt(self):
        self._historyBooks = {}
        # set the priority 0 to all jobs
        # self._processExecutionNode( self.process._executionNode, None, priority=0 )
        # if the root node is a parallel node, its children will have a decreasing
        # priorities
        if self.process._executionNode:
            self._processExecutionNode(self.process._executionNode, None)
            self._processNodes(
                0, self._groups[None][1], None, set(), set(), False, None)
        else:
            groupId = self._registerGroup(self.SERIAL_GROUP, self.process.name)

            if hasattr(self.process, 'executionWorkflow'):
                # Create a native job
                jobId = self._registerJob(
                    self.NATIVE_JOB, self.process, 0, groupId)

            else:
                jobId = self._registerJob(self.JOB, self.process, 0, groupId)

            self._processNodes(0, [groupId], None, set(), set(), False, None)

        self._processExtraDependencies()

        # import pprint
        # pprint.pprint( self._groups )
        for fid, input_output in six.iteritems(self._iofiles):
            input, output = input_output
            # if len( output ) > 1:
                # print('!!!', 'File "%s" is created by several processes: %s' % ( self._files[fid][0], ', '.join( self._jobs[ i ][0].name for i in output ) ))
            # fileId = self._createIdentifier( self.FILE )
            # print("------------")
            # print(repr(fid) + " " + repr(input) + " " + repr(output))
            if output:
                self.create_output_file(fid, self._files[fid][0], self._files[
                                        fid][1], self._files[fid][2], self._files[fid][3])
            else:
                self.create_input_file(fid, self._files[fid][0], self._files[
                                       fid][1], self._files[fid][2], self._files[fid][3])
            # for i in input:
                # self.create_link( fileId, i )
            # for o in output:
                # self.create_link( o, fileId )

    def _handleHistoryBook(self, inputFileName, id):
        '''Appends the history_book directory as an output file transfer, for a
        given disk item, if it belongs to a database with history handling.
        '''

        # initialize the dict, because a directory history can have only one value, at less than ?
        #?: in fact, self._historyBooks may be a string not a dict
#    self._historyBooks = {}

        database = inputFileName.get('_database')
        if not database:
            return  # will not record history for this.
        db = neuroHierarchy.databases.database(database)
        if db is None or not db.activate_history:
            return  # will not record history for this.
        databaseUuid = neuroHierarchy.databases.database(database).uuid
        fileName = os.path.join(database, 'history_book')
        self._nodeHistoryBooks.add(fileName)
        if fileName in self._fileNames:
            fileId = self._historyBooks[fileName]
            if id not in self._iofiles[fileId][1]:
                self._iofiles[fileId][1].append(id)
            return  # already done
        fileId = self._createIdentifier(self.FILE)
        # print("file => " + repr(fileName.fullPath()))
        # print("database => " + repr(database))
        # print("databaseUuid => " + repr(databaseUuid))
        full_paths = [fileName]
        self._files[fileId] = (fileName, full_paths, databaseUuid, database)
        self._fileNames[fileName] = fileId
        self._iofiles.setdefault(fileId, ([], []))[1].append(id)

        self._historyBooks[fileName] = fileId

    def _registerJob(self, type, process, priority=None, inGroup=None):
        # Create job
        jobId = self._createIdentifier(type)
        # print('Create job:', jobId, '(', inGroup, ')', process.name)
        if priority == None:
            self._jobs[jobId] = (process, 0)
        else:
            self._jobs[jobId] = (process, priority)
        self._groups[inGroup][1].append(jobId)

        if not inGroup is None:
            self._inGroup[jobId] = inGroup

        return jobId

    def _registerGroup(self, type, label, inGroup=None):
        groupId = self._createIdentifier(type)
        # print('Create group (', type, '):', groupId, '(', inGroup, ')',
        # label)
        self._groups[groupId] = (label, [])
        self._groups[inGroup][1].append(groupId)
        self._inGroup[groupId] = inGroup

        return groupId

    def _processNodes(self, depth, nodes, inGroup, begin, end, serial, previous):
        first = None
        last = previous
        for id in nodes:
            if id[0] in (self.JOB, self.NATIVE_JOB):
                self._nodeHistoryBooks = set()
                (process, priority) = self._jobs[id]
                for name, type in six.iteritems(process.signature):
                    if isinstance(type, WriteDiskItem):
                        fileName = getattr(process, name, None)
                        if fileName is not None:
                            if not fileName.fullPath() in self._fileNames:
                                fileId = self._createIdentifier(self.FILE)
                                database = fileName.get('_database')
                                databaseUuid = None
                                if database:
                                    databaseUuid = neuroHierarchy.databases.database(
                                        database).uuid
                                # print("file => " + repr(fileName.fullPath()))
                                # print("database => " + repr(database))
                                # print("databaseUuid => " +
                                # repr(databaseUuid))
                                full_paths = [fileName.fullPath() + ".minf"]
                                if fileName.fullPaths():
                                    full_paths.extend(fileName.fullPaths())
                                else:
                                    full_paths.append(fileName.fullPath())
                                self._files[fileId] = (
                                    fileName.fullPath(), full_paths, databaseUuid, database)
                                self._fileNames[fileName.fullPath()] = fileId
                            else:
                                fileId = self._fileNames[fileName.fullPath()]
                            self._iofiles.setdefault(
                                fileId, ([], []))[1].append(id)
                            self._handleHistoryBook(fileName, id)

                    elif isinstance(type, ReadDiskItem):
                        fileName = getattr(process, name, None)
                        if name in getattr(process, 'workflow_transmit_by_attributes', ()):
                            hierarchyAttributes = fileName.hierarchyAttributes(
                            )
                            hierarchyAttributes.pop('_database', None)
                            if hierarchyAttributes:
                                continue
                        if fileName is not None:
                            if fileName.fullPath() not in self._fileNames:
                                fileId = self._createIdentifier(self.FILE)
                                database = fileName.get('_database')
                                databaseUuid = None
                                if database:
                                    databaseUuid = neuroHierarchy.databases.database(
                                        database).uuid
                                full_paths = [fileName.fullPath() + ".minf"]
                                if fileName.fullPaths():
                                    full_paths.extend(fileName.fullPaths())
                                else:
                                    full_paths.append(fileName.fullPath())
                                self._files[fileId] = (
                                    fileName.fullPath(), full_paths, databaseUuid, database)
                                self._fileNames[fileName.fullPath()] = fileId
                            else:
                                fileId = self._fileNames[fileName.fullPath()]
                            self._iofiles.setdefault(
                                fileId, ([], []))[0].append(id)

                    elif isinstance(type, ListOf) and \
                            isinstance(type.contentType, WriteDiskItem):
                        file_list = getattr(process, name, None)
                        # print("list of WriteDiskItem")
                        # print("file_list " + repr(file_list))
                        if file_list is not None:
                            for fileName in file_list:
                                if not fileName.fullPath() in self._fileNames:
                                    fileId = self._createIdentifier(self.FILE)
                                    database = fileName.get('_database')
                                    databaseUuid = None
                                    if database:
                                        databaseUuid = neuroHierarchy.databases.database(
                                            database).uuid
                                    full_paths = [
                                        fileName.fullPath() + ".minf"]
                                    if fileName.fullPaths():
                                        full_paths.extend(fileName.fullPaths())
                                    else:
                                        full_paths.append(fileName.fullPath())
                                    self._files[fileId] = (
                                        fileName.fullPath(), full_paths, databaseUuid, database)
                                    self._fileNames[
                                        fileName.fullPath()] = fileId
                                else:
                                    fileId = self._fileNames[
                                        fileName.fullPath()]
                                self._iofiles.setdefault(
                                    fileId, ([], []))[1].append(id)
                                self._handleHistoryBook(fileName, id)

                    elif isinstance(type, ListOf) and \
                            isinstance(type.contentType, ReadDiskItem):
                        file_list = getattr(process, name, None)
                        # print("list of ReadDiskItem")
                        # print("file_list " + repr(file_list))
                        if file_list is not None:
                            for fileName in file_list:
                                if name in getattr(process, 'workflow_transmit_by_attributes', ()):
                                    hierarchyAttributes = fileName.hierarchyAttributes(
                                    )
                                    hierarchyAttributes.pop('_database', None)
                                    if hierarchyAttributes:
                                        continue
                                if fileName is not None:
                                    if fileName.fullPath() not in self._fileNames:
                                        fileId = self._createIdentifier(
                                            self.FILE)
                                        database = fileName.get('_database')
                                        databaseUuid = None
                                        if database:
                                            databaseUuid = neuroHierarchy.databases.database(
                                                database).uuid
                                        full_paths = [
                                            fileName.fullPath() + ".minf"]
                                        if fileName.fullPaths():
                                            full_paths.extend(
                                                fileName.fullPaths())
                                        else:
                                            full_paths.append(
                                                fileName.fullPath())
                                        self._files[fileId] = (
                                            fileName.fullPath(), full_paths, databaseUuid, database)
                                        self._fileNames[
                                            fileName.fullPath()] = fileId
                                    else:
                                        fileId = self._fileNames[
                                            fileName.fullPath()]
                                    self._iofiles.setdefault(
                                        fileId, ([], []))[0].append(id)

                if (id[0] == self.NATIVE_JOB):
                    self._append_native_jobs(
                        depth, id, process, inGroup, priority)

                else:
                    self._create_job(depth, id, process, inGroup, priority)

                if serial:
                    if first is None:
                        first = [id]
                    previous = last
                    last = [id]
                else:
                    begin.add(id)
                    end.add(id)
                    if previous:
                        for source in previous:
                            if source != id:
                                self.create_link(source, id)

            elif id[0] == self.PARALLEL_GROUP:
                label, content = self._groups[id]
                self.open_group(depth, id, label, inGroup)
                b = set()
                e = set()
                self._processNodes(depth + 1, content, id, b, e, False, last)
                if serial:
                    if first is None:
                        first = b
                    previous = None
                    last = e
                else:
                    begin.update(b)
                    end.update(e)
                self.close_group(depth, id)
            elif id[0] == self.SERIAL_GROUP:
                label, content = self._groups[id]
                self.open_group(depth, id, label, inGroup)
                b = set()
                e = set()
                self._processNodes(depth + 1, content, id, b, e, True, last)
                if serial:
                    if first is None:
                        first = b
                    previous = None
                    last = e
                else:
                    begin.update(b)
                    end.update(e)
                self.close_group(depth, id)

            if serial and previous is not None:
                for source in previous:
                    for destination in last:
                        if source != destination:
                            self.create_link(source, destination)

        if serial and first:
            begin.update(first)
            end.update(last)

    def _create_job(self, depth, jobId, process, inGroup, priority):

        command = list(self.brainvisa_cmd)
        for hb in self._nodeHistoryBooks:
            command += ['--historyBook', hb]
        command.append(process.id())
        for name in process.signature.keys():
            value = self.parameterToString(process, name)
            command.append(value)
        # print("==> command " + repr(command))
        self.create_job(
            depth, jobId, command, inGroup, label=process.name, priority=priority)

    def _processExtraDependencies(self):
        jobtoid = {}
        for id, job in six.iteritems(self._jobs):
            jobtoid[job[0]] = id
        idtogroup = {}
        for node, id in six.iteritems(self._nodeToId):
            idtogroup[id] = node
        for id, job in six.iteritems(self._jobs):
            node = job[0].executionNode()
            if hasattr(node, '_dependencies'):
                deps = node._dependencies
                self._processExtraDependenciesFor(id, deps, jobtoid)
        for id, group in six.iteritems(self._groups):
            if id is not None:  # None group has no deps.
                node = idtogroup.get(id)
                if hasattr(node, '_dependencies'):
                    deps = node._dependencies
                    self._processExtraDependenciesFor(id, deps, jobtoid)

    def _processExtraDependenciesFor(self, id, deps, jobtoid):
        if id[0] == self.SERIAL_GROUP:
            group = self._groups[id]
            self._processExtraDependenciesFor(group[1][0], deps, jobtoid)
        elif id[0] == self.PARALLEL_GROUP:
            # add deps for each job of the parallel
            group = self._groups[id]
            for jid in group[1]:
                self._processExtraDependenciesFor(jid, deps, jobtoid)
        elif id[0] in (self.JOB, self.NATIVE_JOB):
            # add source dependencies deps to a single job id
            for dep in deps:
                if type(dep) not in (str, unicode):
                    dep = dep()  # dereference weakref
                    if dep in jobtoid or (hasattr(dep, '_process') and
                                          dep._process in jobtoid):  # dep is a single job
                        if hasattr(dep, '_process'):
                            destid = jobtoid[dep._process]
                        else:
                            destid = jobtoid[dep]
                        print('create_link( ', destid, ',', id, ')')
                        self.create_link(destid, id)
                    elif dep in self._nodeToId:  # dep is a group
                        gid = self._nodeToId[dep]
                        group = self._groups[gid][1]
                        if gid[0] == self.SERIAL_GROUP:
                            # depend only on last task in serial group
                            self._processExtraDependenciesFor(
                                id, [group[-1]], jobtoid)
                        elif gid[0] == self.PARALLEL_GROUP:
                            # depend on all jobs in the parallel group
                            self._processExtraDependenciesFor(
                                id, group, jobtoid)
                else:  # dep as job/group id
                    if dep[0] == (self.JOB, self.NATIVE_JOB):
                        print('create_link( ', dep, ',', id, ')')
                        self.create_link(dep, id)
                    elif dep[0] == self.SERIAL_GROUP:
                        # depend only on last task in serial group
                        group = self._groups[dep][1]
                        self._processExtraDependenciesFor(
                            id, [group[-1]], jobtoid)
                    elif dep[0] == self.PARALLEL_GROUP:
                        group = self._groups[dep][1]
                        # depend on all jobs in the parallel group
                        self._processExtraDependenciesFor(id, group, jobtoid)

    def _append_native_jobs(self, depth, jobId, process, inGroup, priority):
        pass


class GraphvizProcessToWorkflow(ProcessToWorkflow):

    def __init__(self, process, output, clusters=True, files=True):
        super(GraphvizProcessToWorkflow, self).__init__(process)
        self.out = output
        self.links = set()
        self.clusters = clusters
        self.files = files

    def doIt(self):
        print('digraph "' + self.process.name + '" {', file=self.out)
        super(GraphvizProcessToWorkflow, self).doIt()
        for source, destination in self.links:
            print('  ', source, '->', destination, file=self.out)
        print('}'.edit(options), file=self.out)

        self.out.close()

    def create_job(self, depth, jobId, command, inGroup, label, priority):
        print('create_job' + repr((depth, jobId, command, inGroup)))
        print('  ' * depth, jobId, '[ shape=ellipse, label="' + label + '" ]',
              file=self.out)

    def open_group(self, depth, groupId, label, inGroup):
        print('open_group' + repr((depth, groupId, label, inGroup)))
        if self.clusters:
            print('  ' * depth, 'subgraph cluster_' + str(groupId), '{',
                  file=self.out)
            if label:
                print(
                    '  ' * (depth + 1), 'label = "' + label + '"', file=self.out)

    def close_group(self, depth, groupId):
        print('close_group' + repr((depth, groupId)))
        if self.clusters:
            print('  ' * depth, '}', file=self.out)

    def create_input_file(self, fileId, fileName, fullPaths, databaseUuid, database_dir):
        print('create_input_file' + repr((fileId, fileName)))
        if self.files:
            print(
                '  ', fileId, '[ shape=diamond, label="' + os.path.basename(fileName) + '" ]', file=self.out)

    def create_output_file(self, fileId, fileName, fullPaths, databaseUuid, database_dir):
        print('create_output_file' + repr((fileId, fileName)))
        if self.files:
            print(
                '  ', fileId, '[ shape=diamond, label="' + os.path.basename(fileName) + '" ]', file=self.out)

    def create_link(self, source, destination):
        print('create_link' + repr((source, destination)))
        if self.files or (source[0] != self.FILE and destination[0] != self.FILE):
            self.links.add((source, destination))


class ProcessToFastExecution(ProcessToWorkflow):

    def __init__(self, process, output, clusters=True, files=True):
        super(ProcessToFastExecution, self).__init__(process)
        self.out = output

    def doIt(self):
        super(ProcessToFastExecution, self).doIt()
        self.out.close()

    def create_job(self, depth, jobId, command, inGroup, label, priority):
        print('echo', ' '.join(repr(i) for i in command), file=self.out)
        print(' '.join(repr(i) for i in command), file=self.out)

    def open_group(self, depth, groupId, label, inGroup):
        pass

    def close_group(self, depth, groupId):
        pass

    def create_input_file(self, fileId, fileName, fullPaths, databaseUuid, database_dir):
        pass

    def create_output_file(self, fileId, fileName, fullPaths, databaseUuid, database_dir):
        pass

    def create_link(self, source, destination):
        pass


class ProcessToSomaWorkflow(ProcessToWorkflow):

    NO_FILE_PROCESSING = "use local path"
    FILE_TRANSFER = "transfer files"
    SHARED_RESOURCE_PATH = "use path translation"
    BV_DB_SHARED_PATH = "path translation for BrainVISA db"

    def __init__(self,
                 process,
                 output=None,
                 input_file_processing="use local path",
                 output_file_processing="use local path",
                 brainvisa_cmd=[os.path.basename(sys.executable),
                                "-m", "brainvisa.axon.runprocess"],
                 brainvisa_db=None, context=None):
        '''
        brainvisa_db: list of the brainvisa db uuid which will be used in the case
        of the option: BV_DB_SHARED_PATH
        '''

        super(ProcessToSomaWorkflow, self).__init__(process)
        self.__out = output

        self.__jobs = {}
        self.__file_transfers = {}
        self.__groups = {}
        self.__mainGroupId = None
        self.__dependencies = []

        self.__input_file_processing = input_file_processing
        self.__output_file_processing = output_file_processing
        self.context = context

        self.brainvisa_cmd = brainvisa_cmd
        if isinstance(self.brainvisa_cmd, in six.string_types):
            self.brainvisa_cmd = [brainvisa_cmd]
        if brainvisa_db == None:
            self.brainvisa_db = []
        else:
            self.brainvisa_db = brainvisa_db

        # setup soma-workflow context config (for executionWorkflow() process
        # methods and links with Capsul
        self.setup_workflow_context()

    def escape(self):
        return [('\'', '"')]

    def setup_workflow_context(self):
        context = self.context
        if context is None:
            context = defaultContext()
            self.context = context
        path_translations = {}
        transfer_paths = []
        if self.__input_file_processing in (self.BV_DB_SHARED_PATH,
                                            self.SHARED_RESOURCE_PATH):
            shared_db = [db
                         for db in neuroHierarchy.databases.iterDatabases()
                         if db.fso.name == 'share']
            path_translations = dict(
                [(db.directory, ['brainvisa', db.uuid]) for db in shared_db])
        if self.__input_file_processing == self.FILE_TRANSFER \
                or self.__output_file_processing == self.FILE_TRANSFER:
            for db in neuroHierarchy.databases.iterDatabases():
                if db.fso.name != 'share' \
                    or self.__input_file_processing not in (
                        self.BV_DB_SHARED_PATH,
                                                            self.SHARED_RESOURCE_PATH):
                    transfer_paths.append(db.directory)
        elif self.__input_file_processing == self.SHARED_RESOURCE_PATH \
                or self.__output_file_processing == self.SHARED_RESOURCE_PATH:
            for db in neuroHierarchy.databases.iterDatabases():
                path_translations[db.directory] = ['brainvisa', db.uuid]

        context.soma_workflow_config = {'path_translations': path_translations,
                                        'transfer_paths': transfer_paths}

    def doIt(self):

        self.__jobs = {}
        self.__file_transfers = {}
        self.__groups = {}
        self.__mainGroupId = None
        self.__dependencies = []

        # self.linkcnt = {}
        # self.linkcnt[(self.JOB, self.JOB)] = 0
        # self.linkcnt[(self.FILE, self.JOB)] = 0
        # self.linkcnt[(self.JOB, self.FILE)] = 0
        # self.linkcnt[(self.FILE, self.FILE)] = 0

        super(ProcessToSomaWorkflow, self).doIt()

        # Due to native jobs, it is necessary to flatten jobs list
        jobs = self.flatten(self.__jobs.values())
        dependencies = self.__dependencies
        root_group = self.__groups[self.__mainGroupId]

        workflow = Workflow(
            jobs, dependencies, root_group, name=self.process.name)
        if self.__out:
            Helper.serialize(self.__out, workflow)
        return workflow

        #
        # print(">>> referenced input and output")
        # for n in workflow.jobs:
            # if isinstance(n, Job):
                # print("-------------")
                # print("    " + n.name)
                # print("referenced inputs : " + repr(len(n.referenced_input_files)))
                # for r in n.referenced_input_files:
                    # print("   %30s                              %s" %(r.name,r.client_path))
                # print("referenced outputs :" + repr(len(n.referenced_output_files)))
                # for r in n.referenced_output_files:
                    # print("   %30s                              %s" %(r.name,r.client_path))
        # print("<<< referenced input and output")
        # print(" ")
        # print(">>> jobs")
        # for n in workflow.jobs:
            # print(" " + n.name)
        # print("<<< jobs")
        # print(" ")
        # print(">>> dependencies ")
        # for d in workflow.dependencies:
            # print("   ( " + d[0].name + " , " + d[1].name + " ) ")
        # print("<<< dependencies ")
        # print(" ")
        # print(">>> root group ")
        # for el in workflow.root_group:
            # print(" " + el.name)
        # print("<<< root group ")
        # print("  ")
        # print(">>> groups ")
        # for g in workflow.groups:
            # print("--------")
            # print(" " + g.name)
            # for el in g.elements: print("      " + el.name)
        # print("<<< groups ")
        #

    def parameterToString(self, process, name):
        def toString(value, useHierarchy, escape=None, level=0):
            # This function converts values to string
            # also converting lists recursively
            if isinstance(value, DiskItem):
                hierarchyAttributes = value.hierarchyAttributes()
                hierarchyAttributes.pop('_database', None)
                if hierarchyAttributes and useHierarchy:
                    value = repr(hierarchyAttributes)
            else:
                if isinstance(value, list) \
                        or isinstance(value, tuple):
                    new_value = []
                    for element in value:
                        new_value.append(
                            toString(element, useHierarchy, escape, level + 1))
                    if isinstance(value, tuple):
                        value = tuple(new_value)
                    else:
                        value = new_value
            if not isinstance(value, list) and not isinstance(value, tuple):
                if isinstance(value, basestring) and (value.startswith('"')
                                                      or value.startswith("'") or value == "None"):
                    value = '"' + str(value) + '"'
                else:
                    value = str(value)
                if escape is not None:
                    for e, r in escape:
                        value = value.replace(e, r)

            return value

        value = getattr(process, name)
        useHierarchy = name in getattr(
            process, 'workflow_transmit_by_attributes', ())
        value = toString(value, useHierarchy, escape=self.escape())

        return value

    def create_job(self, depth, jobId, command, inGroup, label, priority):
        # print('create_job' + repr( ( depth, jobId, command, inGroup ) ))
        self.__jobs[jobId] = Job(
            command=command, name=label, priority=priority)  # jobId)#
        self.__groups[inGroup].elements.append(self.__jobs[jobId])

    def _append_native_jobs(self, depth, jobId, process, inGroup, priority):
        jobs, dependencies, groups \
            = process.executionWorkflow(context=self.context)
        self.__jobs[jobId] = jobs
        self.__groups[inGroup].elements += groups
        self.__dependencies += dependencies

    def open_group(self, depth, groupId, label, inGroup):
        # print('open_group' + repr( ( depth, groupId, label, inGroup ) ))
        self.__groups[groupId] = Group(name=label,
                                       elements=[])  # groupId)#
        if not inGroup:
            self.__mainGroupId = groupId
        else:
            self.__groups[inGroup].elements.append(self.__groups[groupId])

    def close_group(self, depth, groupId):
        # print('close_group' + repr( ( depth, groupId ) ))
        pass

    def create_input_file(self, fileId, fileName, fullPaths=None,
                          databaseUuid=None, database_dir=None):
        if not self.__input_file_processing == self.NO_FILE_PROCESSING:
            # print('create_input_file' + repr( ( fileId, os.path.basename(
            # fileName ), fullPaths, databaseUuid, database_dir ) ))
            if self.__input_file_processing == self.FILE_TRANSFER:
                global_in_file = FileTransfer(is_input=True,
                                              client_path=fileName,
                                              name=os.path.basename(fileName),
                                              client_paths=fullPaths)
                self.__file_transfers[fileId] = global_in_file

            elif self.__input_file_processing == self.SHARED_RESOURCE_PATH:
                if databaseUuid and database_dir:
                    global_in_file = SharedResourcePath(
                        relative_path=fileName[(len(database_dir) + 1):],
                      namespace="brainvisa",
                      uuid=databaseUuid)
                else:
                    print("Cannot find database uuid for file " + repr(
                        fileName) + " => the file will be transfered.")
                    global_in_file = FileTransfer(is_input=True,
                                                  client_path=fileName,
                                                  name=os.path.basename(
                                                      fileName),
                                                  client_paths=fullPaths)
                    self.__file_transfers[fileId] = global_in_file

            elif self.__input_file_processing == self.BV_DB_SHARED_PATH:
                if databaseUuid and databaseUuid in self.brainvisa_db:
                    global_in_file = SharedResourcePath(relative_path=fileName[
                                                        (len(database_dir) + 1):], namespace="brainvisa", uuid=databaseUuid)
                else:
                    return

            if global_in_file:
                jobs_to_inspect = []
                for job_id in self._iofiles[fileId][0]:
                    if isinstance(global_in_file, FileTransfer):
                        self.create_link((self.FILE, global_in_file), job_id)
                    jobs_to_inspect += self.flatten(self.__jobs[job_id])
                for job_id in self._iofiles[fileId][1]:
                    if isinstance(global_in_file, FileTransfer):
                        self.create_link(job_id, (self.FILE, global_in_file))
                    jobs_to_inspect += self.flatten(self.__jobs[job_id])

                # print("job inspection: " + repr(len(jobs_to_inspect)) + "
                # jobs.")
                for job in jobs_to_inspect:
                    new_command = []
                    for command_el in job.command:
                        if command_el == fileName:
                            if isinstance(global_in_file, FileTransfer):
                                new_command.append(
                                    (global_in_file, os.path.basename(fileName).encode('utf-8')))
                            else:
                                new_command.append(global_in_file)
                        elif isinstance(command_el, OptionPath) and command_el.parent_path == fileName:
                            new_option_path = OptionPath(
                                parent_path=global_in_file,
                                                         uri=command_el.uri,
                                                         name=command_el.name)
                            new_command.append(new_option_path)
                        elif isinstance(command_el, list):
                            new_command_el = []
                            for list_el in command_el:
                                if list_el == fileName:
                                    if isinstance(global_in_file, FileTransfer):
                                        new_command_el.append(
                                            (global_in_file, os.path.basename(fileName).encode('utf-8')))
                                    else:
                                        new_command_el.append(global_in_file)
                                elif isinstance(list_el, OptionPath) and list_el.parent_path == fileName:
                                    new_option_path = OptionPath(
                                        parent_path=global_in_file,
                                                                 uri=list_el.uri,
                                                                 name=list_el.name)
                                    new_command.append(new_option_path)
                                else:
                                    new_command_el.append(list_el)
                            new_command.append(new_command_el)
                        else:
                            new_command.append(command_el)
                    job.command = new_command
                    if job.stdin == fileName:
                        job.stdin = global_in_file
                    elif isinstance(job.stdin, OptionPath) and job.stdin.parent_path == fileName:
                        new_option_path = OptionPath(
                            parent_path=global_in_file,
                                                     uri=job.stdin.uri,
                                                     name=job.stdin.name)
                        job.stdin = new_option_path
                    if job.stdout_file == fileName:
                        job.stdout_file = global_in_file
                    elif isinstance(job.stdout_file, OptionPath) and job.stdout_file.parent_path == fileName:
                        new_option_path = OptionPath(
                            parent_path=global_in_file,
                                                     uri=job.stdout_file.uri,
                                                     name=job.stdout_file.name)
                        job.stdout_file = new_option_path
                    if job.stderr_file == fileName:
                        job.stderr_file = global_in_file
                    elif isinstance(job.stderr_file, OptionPath) and job.stderr_file.parent_path == fileName:
                        new_option_path = OptionPath(
                            parent_path=global_in_file,
                                                     uri=job.stderr_file.uri,
                                                     name=job.stderr_file.name)
                        job.stderr_file = new_option_path

    def create_output_file(self, fileId, fileName, fullPaths=None,
                           databaseUuid=None, database_dir=None):
        if not self.__output_file_processing == self.NO_FILE_PROCESSING:
            # print('create_output_file' + repr( ( fileId, os.path.basename(
            # fileName ), fullPaths, databaseUuid, database_dir ) ))
            if self.__output_file_processing == self.FILE_TRANSFER:
                global_out_file = FileTransfer(is_input=False,
                                               client_path=fileName,
                                               name=os.path.basename(fileName),
                                               client_paths=fullPaths)
                self.__file_transfers[fileId] = global_out_file

            elif self.__output_file_processing == self.SHARED_RESOURCE_PATH:
                if databaseUuid and database_dir:
                    global_out_file = SharedResourcePath(
                        relative_path=fileName[(len(database_dir) + 1):],
                                                         namespace="brainvisa",
                                                         uuid=databaseUuid)
                else:
                    print("Cannot find database uuid for file " + repr(
                        fileName) + " => the file will be transfered.")
                    global_out_file = FileTransfer(is_input=False,
                                                   client_path=fileName,
                                                   name=os.path.basename(
                                                   fileName),
                                                   client_paths=fullPaths)
                    self.__file_transfers[fileId] = global_out_file
            else:
                raise ValueError('Unsupported output file processing mode: %s'
                                 % self.__output_file_processing)

            if global_out_file:
                jobs_to_inspect = []
                for job_id in self._iofiles[fileId][0]:
                    if isinstance(global_out_file, FileTransfer):
                        self.create_link((self.FILE, global_out_file), job_id)
                    jobs_to_inspect += self.flatten(self.__jobs[job_id])
                for job_id in self._iofiles[fileId][1]:
                    if isinstance(global_out_file, FileTransfer):
                        self.create_link(job_id, (self.FILE, global_out_file))
                    jobs_to_inspect += self.flatten(self.__jobs[job_id])

                # print("job inspection: " + repr(len(jobs_to_inspect)) + "
                # jobs.")
                for job in jobs_to_inspect:
                    new_command = []
                    for command_el in job.command:
                        if command_el == fileName:
                            if isinstance(global_out_file, FileTransfer):
                                new_command.append(
                                    (global_out_file, os.path.basename(fileName).encode('utf-8')))
                            else:
                                new_command.append(global_out_file)
                        elif isinstance(command_el, OptionPath) and command_el.parent_path == fileName:
                            new_option_path = OptionPath(
                                parent_path=global_out_file,
                                                         uri=command_el.uri,
                                                         name=command_el.name)
                            new_command.append(new_option_path)
                        elif isinstance(command_el, list):
                            new_command_el = []
                            for list_el in command_el:
                                if list_el == fileName:
                                    if isinstance(global_out_file, FileTransfer):
                                        new_command_el.append(
                                            (global_out_file, os.path.basename(fileName).encode('utf-8')))
                                    else:
                                        new_command_el.append(global_out_file)
                                elif isinstance(list_el, OptionPath) and list_el.parent_path == fileName:
                                    new_option_path = OptionPath(
                                        parent_path=global_out_file,
                                                                 uri=list_el.uri,
                                                                 name=list_el.name)
                                    new_command.append(new_option_path)
                                else:
                                    new_command_el.append(list_el)
                            new_command.append(new_command_el)
                        else:
                            new_command.append(command_el)
                    job.command = new_command
                    if job.stdin == fileName:
                        job.stdin = global_out_file
                    elif isinstance(job.stdin, OptionPath) and job.stdin.parent_path == fileName:
                        new_option_path = OptionPath(
                            parent_path=global_out_file,
                                                     uri=job.stdin.uri,
                                                     name=job.stdin.name)
                        job.stdin = new_option_path
                    if job.stdout_file == fileName:
                        job.stdout_file = global_out_file
                    elif isinstance(job.stdout_file, OptionPath) and job.stdout_file.parent_path == fileName:
                        new_option_path = OptionPath(
                            parent_path=global_out_file,
                                                     uri=job.stdout_file.uri,
                                                     name=job.stdout_file.name)
                        job.stdout_file = new_option_path
                    if job.stderr_file == fileName:
                        job.stderr_file = global_out_file
                    elif isinstance(job.stderr_file, OptionPath) and job.stderr_file.parent_path == fileName:
                        new_option_path = OptionPath(
                            parent_path=global_out_file,
                                                     uri=job.stderr_file.uri,
                                                     name=job.stderr_file.name)
                        job.stderr_file = new_option_path

    def resolve_objects(self, k):

        r = []
        t = k[0]

        if (type(k) is tuple):
            o = k[1]

        elif (t in (self.NATIVE_JOB, self.JOB)):
            o = self.__jobs[k]

        elif (t == self.FILE):
            o = self.__file_transfers[k]

        if type(o) is list:
            for c in o:
                r += self.resolve_objects((t, c))

        elif not o is None:
            r += [(t, o)]

        return r

    def create_link(self, source, destination):
        # print('==>create_link' + repr( ( source, destination ) ))

        s = self.resolve_objects(source)
        d = self.resolve_objects(destination)

        for srctype, src in s:
            for dsttype, dst in d:
                if srctype in (self.JOB, self.NATIVE_JOB) \
                        and dsttype in (self.JOB, self.NATIVE_JOB):

                    self.__dependencies.append((src, dst))
                    # self.linkcnt[(self.JOB, self.JOB)] = self.linkcnt[(self.JOB, self.JOB)] +1
                    # print(repr(self.linkcnt[(self.JOB, self.JOB)]) +'     JOB
                    # -> JOB  ' + repr( ( self.__jobs[source].name,
                    # self.__jobs[destination].name ) ))
                elif self.__file_transfers:
                    if srctype == self.FILE and dsttype in (self.JOB, self.NATIVE_JOB):
                        dst.referenced_input_files.append(src)
                        # self.linkcnt[(self.FILE, self.JOB)] = self.linkcnt[(self.FILE, self.JOB)] +1
                        # print(repr(self.linkcnt[(self.FILE, self.JOB)]) +'
                        # FILE -> JOB  ' + repr( (file.name, job.name ) ) + '
                        # len(job.referenced_input_files) = ' +
                        # repr(len(job.referenced_input_files)))
                    elif srctype in (self.JOB, self.NATIVE_JOB) and dsttype == self.FILE:
                        src.referenced_output_files.append(dst)
                        # self.linkcnt[(self.JOB, self.FILE)] = self.linkcnt[(self.JOB, self.FILE)] +1
                        # print(repr(self.linkcnt[(self.JOB, self.FILE)]) +'
                        # JOB  -> FILE ' + repr( (job.name, file.name ) ) + '
                        # len(job.referenced_output_files) = ' +
                        # repr(len(job.referenced_output_files)))
                    elif srctype == self.FILE and dsttype == self.FILE:
                        self.__dependencies.append((src, dst))
                        # self.linkcnt[(self.FILE, self.FILE)] = self.linkcnt[(self.FILE, self.FILE)] +1
                        # print(repr(self.linkcnt[(self.FILE, self.FILE)]) +'
                        # FILE -> FILE ' + repr( (
                        # self.__file_transfers[source].name,
                        # self.__file_transfers[destination].name ) ))


def process_to_workflow(
    process, output,
    input_file_processing=ProcessToSomaWorkflow.NO_FILE_PROCESSING,
    output_file_processing=ProcessToSomaWorkflow.NO_FILE_PROCESSING,
        context=None):
    # ptwf = GraphvizProcessToWorkflow( process, output, clusters=clusters, files=files )
    # ptwf = ProcessToFastExecution( process, output )
    ptwf = ProcessToSomaWorkflow(process, output, input_file_processing,
                                 output_file_processing, context=None)
    return ptwf.doIt()


if __name__ == '__main__':
    try:
        theProcess
    except NameError:
        from brainvisa.processes import *
        theProcess = getProcessInstance(sys.argv[1])
    # process_to_workflow(theProcess, open( 'test.dot', 'w' ), clusters = True, files = False)
    # process_to_workflow( theProcess, open( 'test.sh', 'w' ) )
    # process_to_workflow(theProcess, 'test.workflow')
    workflow = process_to_workflow(process=theProcess, output=sys.argv[2],
                                   input_file_processing=sys.argv[3],
                                   output_file_processing=sys.argv[4])
