#!/usr/bin/env python

from __future__ import print_function
from __future__ import absolute_import
from brainvisa.axon import processes
from capsul.api import Process
from capsul.api import Pipeline
from brainvisa import processes as procbv
from brainvisa.data import neuroData
from brainvisa.data.readdiskitem import ReadDiskItem
from brainvisa.data.writediskitem import WriteDiskItem
from brainvisa.data import neuroDiskItems
from brainvisa.processing.capsul_process import CapsulProcess
from traits import api as traits
import weakref
import sys
import re
import io
import inspect
import six

from optparse import OptionParser
from six.moves import zip


def AxonToCapsulInstance(ver='2'):
    ''' factory
    '''

    ver = str(ver)
    mod = sys.modules[__name__]
    cname = 'AxonToCapsul_v%s' % ver
    cclass = getattr(mod, cname, AxonToCapsul)
    print("CLASS:", cclass)
    return cclass(ver=ver)


def choice_options(choice):
    return [repr(x[min(1, len(x) - 1)]) for x in choice.values]


def use_weak_ref(obj):
    if obj is None:
        return None
    if type(obj) is weakref.ProxyType:
        return obj.__weakref__
    if type(obj) is weakref.ReferenceType:
        return obj
    return weakref.ref(obj)


# ----

class AxonToCapsul(object):

    Any = traits.Any
    Undefined = traits.Undefined

    def __init__(self, ver='2'):
        self.ver = ver


    def get_choice_type(self, choice):
        if len(choice.values) == 0:
            return None
        element_types = {
            bool: traits.Bool,
            int: traits.Int,
            float: traits.Float,
            str: traits.Str,
            six.text_type: traits.Str,
            list: traits.List,
            tuple: traits.List,
        }
        choice_types = [element_types[type(t[min(1, len(t) - 1)])]
                        for t in choice.values]
        choice0 = choice_types[0]
        if all([elem is choice0 for elem in choice_types[1:]]):
            return choice0
        # test compatible types, ie (int, float) -> float
        if all([elem in (traits.Int, traits.Float) for elem in choice_types]):
            return traits.Float
        return None


    def open_choice_options(self, choice):
        if len(choice.values) != 0:
            options = []
            trait_type = self.get_choice_type(choice)
            if trait_type is not None:
                options.append('trait=%s()' % trait_type.__name__)
            value = choice.values[0][min(1, len(choice.values[0]) - 1)]
            return options + ['default_value=' + repr(value)]
        else:
            return []


    def get_openchoice_type(self, choice):
        trait_type = self.get_choice_type(choice)
        if trait_type is None:
            trait_type = traits.Str  # default to string
        return trait_type


    def point3d_options(self, point):
        # note: not using traits.ListFloat because its constructor doesn't seem
        # to take parmeters into account (minlen, maxlen, value)
        return ['trait=Float()', 'minlen=3', 'maxlen=3', 'value=[0, 0, 0]']


    def matrix_options(self, list_trait):
        return ['trait=List()']


    def diskitem_type(self, diskitem):
        otype = None
        for format in diskitem.formats:
            f = neuroDiskItems.getFormat(format)
            if otype is None \
                    and f.fileOrDirectory() is neuroDiskItems.Directory:
                otype = traits.Directory
            elif f.fileOrDirectory() is not neuroDiskItems.Directory:
                otype = traits.File
                break
        if otype is None:
            otype = traits.File
        return otype


    def diskitem_options(self, diskitem):
        extre = re.compile('^.*\|[^*]*\*(.*)$')
        exts = []
        options = []
        #formats = sorted(diskitem.formats)
        formats = diskitem.formats
        for format in formats:
            f = neuroDiskItems.getFormat(format)
            for pat in f.patterns.patterns:
                m = extre.match(pat.pattern)
                if m is not None and m.group(1) not in exts:
                    exts.append(m.group(1))
        if len(exts) != 0:
            options.append('allowed_extensions=%s' % repr(exts))
        if isinstance(diskitem, WriteDiskItem):
            options.append('output=True')
        return options


    _param_types_table = None

    @property
    def param_types_table(self):
        if self._param_types_table is not None:
            return self._param_types_table
        self._param_types_table= \
        {
            neuroData.Boolean: traits.Bool,
            neuroData.String: traits.Str,
            neuroData.Number: traits.Float,
            neuroData.Float: traits.Float,
            neuroData.Integer: traits.Int,
            ReadDiskItem: (self.diskitem_type, self.diskitem_options),
            WriteDiskItem: (self.diskitem_type, self.diskitem_options),
            neuroData.Choice: (traits.Enum, choice_options),
            neuroData.OpenChoice: (self.get_openchoice_type,
                                   self.open_choice_options),
            neuroData.ListOf: traits.List,
            neuroData.Point3D: (traits.List, self.point3d_options),
            neuroData.Matrix: (traits.List, self.matrix_options),
        }
        return self._param_types_table


    def capsul_param_type(self, axon_param):
        newtype = self.param_types_table.get(type(axon_param))
        paramoptions = []
        if newtype is None:
            print('write_process_signature: type', type(axon_param), 'not found')
            newtype = traits.Str
        if isinstance(newtype, tuple):
            paramoptions = newtype[1](axon_param)
            newtype = newtype[0]
        if not axon_param.mandatory:
            paramoptions.append('optional=True')
        if inspect.isfunction(newtype) or inspect.ismethod(newtype):
            # newtype is a function: call it to get the actual type
            newtype = newtype(axon_param)
        if hasattr(newtype, '__name__'):
            # take name of a type class
            newtype = newtype.__name__
        section = axon_param.getSectionTitleIfDefined()
        if section is not None:
            paramoptions.append('groups=("%s",)' % section)
        return newtype, paramoptions


    def capsul_merged_param_type(self, axon_params):
        ''' get a "common" capsul parameter type for a list of axon parameters,
            typically to form a swith output from its possible inputs. the
            output allowed_extensions will be the union of input extensions
            (which may not always be OK).
        '''
        ctype = None
        coptions = []
        allowed_extensions = []
        for axon_param in axon_params:
            newtype, paramoptions = self.capsul_param_type(axon_param)
            if ctype is None:
                ctype = newtype
            else:
                if ctype != newtype:
                    print('warning: unmatching input types (for switch) %s and %s'
                          % (ctype, newtype))
            for opt in paramoptions:
                oname, oval = opt.split('=')
                oname = oname.strip()
                if oname == 'allowed_extensions':
                    oval = eval(oval)
                    for ext in oval:
                        if ext not in allowed_extensions:
                            allowed_extensions.append(ext)
                elif opt not in coptions:
                    coptions.append(opt)
        if len(allowed_extensions) != 0:
            coptions.append('allowed_extensions=%s' % repr(allowed_extensions))
        return ctype, coptions


    def write_process_signature(self, p, out, buffered_lines,
                                get_all_values=True):
        # write signature
        for name, param in six.iteritems(p.signature):
            newtype, paramoptions = self.capsul_param_type(param)
            out.write(u'        self.add_trait(\'%s\', %s(%s))\n'
                      % (name, newtype, ', '.join(paramoptions)))
            if get_all_values or not p.isDefault(name):
                value = getattr(p, name)
                if value is not None:
                    buffered_lines['initialization'].append(
                        '        self.%s = %s\n' % (name, repr(value)))
                    # print('non-default value for %s in %s' % (name, p.name))
                elif type(param) in (neuroData.Boolean, neuroData.Number,
                                    neuroData.Float, neuroData.Integer):
                    # None as number is a forced optional value
                    buffered_lines['initialization'].append(
                        '        self.%s = %s\n' % (name, 'Undefined'))
        out.write(u'\n\n')


    def write_process_execution(self, p, out):
        axon_name = p.id()
        out.write(u'''    def _run_process(self):
        from brainvisa import axon
        from brainvisa.configuration import neuroConfig
        import brainvisa.processes

        neuroConfig.gui = False
        neuroConfig.fastStart = True
        neuroConfig.logFileName = ''

        axon.initializeProcesses()

        kwargs = {}
        for name in self.user_traits():
            value = getattr(self, name)
            if value is Undefined:
                continue
            if isinstance(self.trait(name).trait_type, File) and value != '':
                kwargs[name] = value
            elif isinstance(self.trait(name).trait_type, List):
                kwargs[name] = list(value)
            else:
                kwargs[name] = value

        context = brainvisa.processes.defaultContext()
        context.runProcess('%s', **kwargs)
''' % axon_name)


    def write_process_definition(self, p, out, get_all_values=True):
        buffered_lines = {'initialization': []}
        print('write_process_definition ver:', self.ver)
        self.write_process_signature(p, out, buffered_lines,
                                     get_all_values=get_all_values)
        self.write_buffered_lines(out, buffered_lines,
                                  sections=('initialization', ))
        self.write_process_execution(p, out)


    def str_to_name(self, s):
        s = s.replace(' ', '_')
        s = s.replace('(', '_')
        s = s.replace(')', '_')
        s = s.replace('\'', '_')
        s = s.replace('"', '_')
        s = s.replace(',', '_')
        s = s.replace('-', '_')
        s = s.replace('/', '_')
        s = s.replace('+', '_')
        s = s.replace('*', '_')
        return s


    def make_module_name(self, procid, module_name_prefix=None,
                         use_process_names={}, lowercase_modules=True):
        '''module + process class name, ex: morpho.morphologist.morphologist.

        Parameters
        ----------
        procid: string
            Axon process id
        module_name_prefix: string (optional)
            base module name (ex: morpho). If not specified, no base module
        use_process_names: dict (optional)
            If specified, override some complete process names. Key is the axon ID,
            value is the full name.
            Ex: {'morphologist': 'morpho.morphologist.Morphologist'}
        '''
        altname = use_process_names.get(procid)
        if altname:
            return altname
        if module_name_prefix is None:
            return '%s.%s' % (fix_case(procid, lowercase_modules), procid)
        else:
            return '%s.%s.%s' % (module_name_prefix,
                                fix_case(procid, lowercase_modules), procid)


    def parse_param_link(self, pipeline, proc, param, linkdefs,
                         weak_outputs=False):
        links = []
        for dstproc, dstparam, mlink, unknown, force in linkdefs:
            dstproc = use_weak_ref(dstproc)
            # check if link is compatible
            if dstproc is None or dstparam is None or dstproc is proc:
                # intra-process links are dropped.
                continue
            srcsign = proc().signature[param]
            dstsign = dstproc().signature[dstparam]
            if type(srcsign) is not type(dstsign) \
                    and (not isinstance(srcsign, ReadDiskItem)
                        or not isinstance(dstsign, ReadDiskItem)):
                # incompatible parameters types
                continue
            if isinstance(srcsign, ReadDiskItem):
                if srcsign.type.isA(dstsign.type.name) \
                        or dstsign.type.isA(srcsign.type.name):
                    # compatible type
                    if isinstance(dstsign, WriteDiskItem) \
                            or (not isinstance(srcsign, WriteDiskItem)
                                and dstproc is use_weak_ref(pipeline)):
                        # swap input/output
                        this_weak_output = False
                        if weak_outputs and proc is use_weak_ref(pipeline):
                            this_weak_output = True
                        if (dstproc, dstparam, proc, param) not in links:
                            links.append((dstproc, dstparam, proc, param,
                                          this_weak_output))
                    else:
                        this_weak_output = False
                        if weak_outputs and dstproc is use_weak_ref(pipeline):
                            this_weak_output = True
                        if (proc, param, dstproc, dstparam) not in links:
                            links.append((proc, param, dstproc, dstparam,
                                          this_weak_output))
            else:
                # not DiskItems
                this_weak_output = False
                if weak_outputs and dstproc is use_weak_ref(pipeline):
                    this_weak_output = True
                if (proc, param, dstproc, dstparam) not in links:
                    links.append((proc, param, dstproc, dstparam,
                                  this_weak_output))
        return links


    def parse_links(self, pipeline, proc, weak_outputs=False):
        links = []
        proc = use_weak_ref(proc)
        for param, linkdefs in six.iteritems(proc()._links):
            links += self.parse_param_link(
                pipeline, proc, param, linkdefs, weak_outputs)
        return links


    def is_output(self, proc, param, verbose=False):
        if verbose:
            print('is_output', proc().name, param)
            print('selection?:', isinstance(proc(),
                                            procbv.SelectionExecutionNode))
        if isinstance(proc(), procbv.SelectionExecutionNode):
            # SelectionExecutionNode nodes may be used for switch nodes.
            # They do not have parameters in the Axon API since they are not
            # processes. But the Capsul pipeline side (Switch node) has input
            # parameters which should be connected from children outputs, and
            # output parameters which should be exported.
            if (hasattr(proc(), 'switch_output')
              and proc().switch_output == param) \
                    or (not hasattr(proc(), 'switch_output')
                        and param == 'switch_out'):
                return True
            else:
                return False
        signp = proc().signature.get(param)
        if signp is None:  # non-exported parameter
            # print('internal')
            # parse sub_nodes
            if hasattr(proc(), 'executionNode'):
                en = proc().executionNode()
                for cn in en.childrenNames():
                    if param.startswith(cn + '_'):
                        node = getattr(en, cn)
                        sub_param = param[len(cn) + 1:]
                        if hasattr(node, 'signature') \
                                and sub_param in node.signature:
                            return isinstance(node.signature[sub_param],
                                              WriteDiskItem)
            # not found: guess it's an output (may be wrong)
            print('Warning: internal param %s.%s not foud. Assuming output'
                  % (proc().name, param))
            return True
        return isinstance(signp, WriteDiskItem)


    def converted_link(self, linkdef, links, pipeline, selfinparams,
                       revinparams, selfoutparams, revoutparams, procmap):
        # selfinparams: outputs which are in self (pipeline) and are thus inputs
        # selfoutparams: inputs which are in self (pipeline) and are thus outpupts
        # revinparams: input params which should be translated to pipeline
        # revoutparams: dest params which should be translated to pipeline
        # find exported source/dest
        weak_link = linkdef[4]
        real_source = self.find_param_in_parent(linkdef[0], linkdef[1],
                                                procmap)
        real_dest = self.find_param_in_parent(linkdef[2], linkdef[3], procmap)
        if real_source[0] is None or real_dest[0] is None:
            print('Warning, missing link info for:', linkdef[0]().name,
                  ',', linkdef[1], ' ->', linkdef[2]().name, ',', linkdef[3])
            return None
        linkdef = (real_source[0], real_source[2], real_dest[0], real_dest[2],
                  weak_link)
        pipeline = use_weak_ref(pipeline)
        if linkdef[2] is pipeline and linkdef[3] in selfinparams:
            # output in pipeline inputs: invert link
            linkdef = (linkdef[2], linkdef[3], linkdef[0], linkdef[1], weak_link)
        if linkdef[:4] in links:
            return None
        if linkdef[0] is pipeline and linkdef[1] in selfoutparams:
            # source in pipeline outputs: either needs translation, or inversion
            if self.is_output(linkdef[2], linkdef[3]):
                # dest is an output: needs inversion
                linkdef = (linkdef[2], linkdef[3], linkdef[0], linkdef[1],
                          weak_link)
            else:
                altp = selfoutparams.get(linkdef[1])
                if altp is None:
                    print('** warning, probably bad link:', linkdef[0]().name,
                          ',', linkdef[1], ' ->', linkdef[2]().name, ',',
                          linkdef[3])
                    print(revoutparams)
                    return None
                linkdef = (altp[0], altp[1], linkdef[2], linkdef[3], weak_link)
            if linkdef[:4] in links:
                return None
        if linkdef[0] is not pipeline \
                and (linkdef[0], linkdef[1]) in revinparams:
            # source has an equivalent in exported inputs
            altp = revinparams[(linkdef[0], linkdef[1])]
            linkdef = (pipeline, altp, linkdef[2], linkdef[3], weak_link)
        if linkdef[2] is not pipeline \
                and (linkdef[2], linkdef[3]) in revoutparams:
            # dest has an equivalent in exported outputs
            altp = revoutparams[(linkdef[2], linkdef[3])]
            linkdef = (linkdef[0], linkdef[1], pipeline, altp, weak_link)
        if linkdef[:4] in links:
            return None
        if linkdef[2] is not pipeline \
                and (linkdef[2], linkdef[3]) in revinparams:
            # dest has an equivalent in exported inputs
            altp = revinparams[(linkdef[2], linkdef[3])]
            linkdef = (pipeline, altp, linkdef[0], linkdef[1], weak_link)
        if linkdef[:4] in links:
            return None
        return linkdef


    def export_output(self, buffered_lines, src, sname, sparam, p, dparam,
                      selfoutparams, revoutparams, processed_links,
                      selfouttraits, weak_outputs=False):
        if dparam in selfouttraits:
            # a trait has been manually declared
            self.declare_output_trait(buffered_lines, src, sname, sparam, p,
                                      dparam, selfoutparams, revoutparams,
                                      processed_links)
        else:
            # global output param in pipeline signature
            buffered_lines['exports'].append('        # export output parameter\n')
            if weak_outputs:
                buffered_lines['exports'].append(
                    '        self.export_parameter(\'%s\', \'%s\', \'%s\', '
                    'weak_link=True)\n'
                    % (sname, sparam, dparam))
            else:
                buffered_lines['exports'].append(
                    '        self.export_parameter(\'%s\', \'%s\', \'%s\')\n'
                    % (sname, sparam, dparam))
            selfoutparams[dparam] = (src, sparam)
            revoutparams[(src, sparam)] = dparam
            processed_links.add((src, sparam, use_weak_ref(p), dparam))
            processed_links.add((use_weak_ref(p), dparam, src, sparam))


    def declare_output_trait(self, buffered_lines, src, sname, sparam, p,
                             dparam, selfoutparams, revoutparams,
                             processed_links):
        # global output param in pipeline signature, as a trait
        selfoutparams[dparam] = (src, sparam)
        revoutparams[(src, sparam)] = dparam
        processed_links.add((src, sparam, use_weak_ref(p), dparam))
        processed_links.add((use_weak_ref(p), dparam, src, sparam))


    def export_input(self, buffered_lines, dst, dname, dparam, p, sparam,
                     selfinparams, revinparams, processed_links):
        # global input param in pipeline signature
        buffered_lines['exports'].append('        # export input parameter\n')
        buffered_lines['exports'].append(
            '        self.export_parameter(\'%s\', \'%s\', \'%s\')\n'
            % (dname, dparam, sparam))
        selfinparams[sparam] = (dst, dparam)
        revinparams[(dst, dparam)] = sparam
        processed_links.add((use_weak_ref(p), sparam, dst, dparam))
        processed_links.add((dst, dparam, use_weak_ref(p), sparam))


    def make_node_name(self, name, nodenames, parents):
        name = self.str_to_name(name)
        full_name = '.'.join((parents or []) + [name])
        if full_name in nodenames:
            nodenames[full_name] += 1
            return '%s_%d' % (name, nodenames[full_name])
        else:
            nodenames[full_name] = 0
            return name


    def is_linked_to_parent(self, proc, param, parent):
        # get links from proc.param
        if isinstance(proc(), procbv.Process):
            linkdefs = proc()._links.get(param)
            if linkdefs:
                for dstproc, dstparam, mlink, unknown, force in linkdefs:
                    if use_weak_ref(dstproc) == parent:
                        return dstparam
            # get links to parent
            for pparam, linkdefs in six.iteritems(parent()._links):
                for srcproc, srcparam, mlink, unknown, force in linkdefs:
                    if use_weak_ref(srcproc) == proc and srcparam == param:
                        return pparam
        return None


    def find_param_in_parent(self, proc, param, procmap):
        # parse all nodes since there is no notion of parent
        verbose = False  # debug flag - TODO: remove it when all is OK
        pname, exported = procmap.get(proc, (None, None))
        if exported:  # exported node: direct, OK
            if verbose:
                print('    find_param_in_parent:', proc().name, '/', param,
                      ': direct export')
            return (proc, pname, param)
        last = (proc, param)
        allnotfound = False
        if verbose:
            print('    find_param_in_parent:', proc().name, '/', param, ':',
                  pname)
        while not allnotfound:
            if verbose:
                print('    try as child:', last[0]().name, '/', last[1])
            if last[0] not in procmap:
                # probably an external link to a parent pipeline
                if verbose:
                    print('    Warning: link to external node in "parent" '
                          'pipeline:', last[0]().name)
                return (None, None, None)
            child_name = procmap[last[0]][0]
            # look for parent enode
            for new_proc, (new_node_name, exported) in six.iteritems(procmap):
                if isinstance(new_proc(), procbv.Process):
                    new_node = use_weak_ref(new_proc().executionNode())
                    if new_node is None:  # leaf: not a possible parent
                        continue
                else:
                    new_node = new_proc
                children = set()
                for n in new_node().children():
                    if isinstance(n, procbv.ProcessExecutionNode):
                        children.add(n._process)
                    else:
                        children.add(n)
                if last[0]() in children:
                    if verbose:
                        print('    test parent:', new_node_name)
                    new_pname = '_'.join((child_name, last[1]))
                    if exported:
                        parent_pname = last[1]
                        if verbose:
                            print('    find_param_in_parent:', proc().name,
                                  '/', param)
                            print('    ** found:', new_proc().name, '/',
                                  new_pname)
                        # now check if it is an exported param in the
                        # sub-pipeline
                        opname = self.is_linked_to_parent(proc, param,
                                                          new_proc)
                        if opname is not None:
                            # then return the exported parent one
                            # parent_pname = opname
                            new_pname = opname
                            if verbose:
                                print('    parent param translated:',
                                      new_pname)
                        elif verbose:
                            print('    not linked to parent: take:', new_pname)
                        return (new_proc, new_node_name, new_pname)
                    last = (new_proc, new_pname)
                    break
            else:  # loop through the end of procmap
                allnotfound = True
        # not found
        print('Warning: find_param_in_parent: NOT FOUND')
        print('    was:', proc().name, '/', param)
        return (None, None, None)


    def write_pipeline_links(self, p, buffered_lines, procmap, links,
                             processed_links, selfoutparams, revoutparams,
                             selfouttraits):
        # parse and set pipeline links
        selfinparams = {}
        revinparams = {}
        for link in links:
            link = self.converted_link(link, processed_links, p, selfinparams,
                                       revinparams, selfoutparams,
                                       revoutparams, procmap)
            if link is None:
                continue
            src, sparam, dst, dparam, weak_link = link
            sname, sexported = procmap.get(src, (None, None))
            if sname is None:
                print('warning, src process', src().name, 'not found in pipeline.')
                # print('procmap:', [ k[0]().name for k in procmap ])
                continue  # skip this one
            dname, dexported = procmap.get(dst, (None, None))
            if dname is None:
                print('warning, dst process', dst().name, 'not found in pipeline.')
                continue  # skip this one
            spname = sparam
            if sname:
                spname = '%s.%s' % (sname, sparam)
            dpname = dparam
            if dname:
                dpname = '%s.%s' % (dname, dparam)
            if sname == '' and sparam not in selfinparams:
                self.export_input(buffered_lines, dst, dname, dparam, p,
                                  sparam, selfinparams, revinparams,
                                  processed_links)
            elif dname == '' and dparam not in selfoutparams:
                self.export_output(buffered_lines, src, sname, sparam, p,
                                   dparam, selfoutparams, revoutparams,
                                   processed_links, selfouttraits)
            else:
                if dname == '' and dparam in selfinparams:
                    # swap input/output
                    tmp = spname
                    spname = dpname
                    dpname = tmp
                if sname == '' and sparam in selfoutparams:
                    spname = selfoutparams[sparam][1]
                if dname != '' and (dst, dpname) in revoutparams:
                    dpname = revoutparams[(dst, dpname)]
                if spname == dpname:
                    continue
                # check for non-exported links with same IO status
                if sname != '' and dname != '' \
                        and self.is_output(src, sparam) \
                            == self.is_output(dst, dparam):
                    print('Warning: write_pipeline_links, sname: %s, '
                          'sparam: %s, dname: %s, dparam: %s: both same IO type:'
                          % (sname, sparam, dname, dparam),
                          self.is_output(src, sparam))
                    if self.is_output(src, sparam):
                        # both outputs: export 1st
                        sparam2 = sname + '_' + sparam
                        if sparam2 in selfoutparams or sparam2 in selfinparams:
                            # avoid duplicate name
                            sparam2 = sparam2 + '2'
                        self.export_output(buffered_lines, src, sname, sparam,
                                           p, sparam2, selfoutparams,
                                           revoutparams, processed_links,
                                           selfouttraits)
                        # and link 2nd to this exported output
                        # (and switch link)
                        src = dst
                        sparam = dparam
                        spname = dpname
                        dst = use_weak_ref(p)
                        dparam = sparam2
                        dpname = sparam2
                    else:
                        # both inputs: export 1st
                        sparam2 = sname + '_' + sparam
                        if sparam2 in selfinparams or sparam2 in selfoutparams:
                            # duplicate name
                            sparam2 = sparam + '2'
                        self.export_input(buffered_lines, src, sname, sparam,
                                          p, sparam2, selfinparams,
                                          revinparams, processed_links)
                        # and link 2nd to this exported input
                        sparam = sparam2
                        spname = sparam2
                if weak_link:
                    buffered_lines['links'].append(
                        '        self.add_link(\'%s->%s\', weak_link=True)\n'
                        % (spname, dpname))
                else:
                    buffered_lines['links'].append(
                        '        self.add_link(\'%s->%s\')\n' % (spname, dpname))
            processed_links.add((src, sparam, dst, dparam))
            processed_links.add((dst, dparam, src, sparam))


    def write_switch(self, enode, buffered_lines, nodenames, links, p,
                     processed_links, selfoutparams, revoutparams,
                     self_out_traits, exported, parent_names, enode_name=None,
                     weak_outputs=False):
        if enode_name is None:
            enode_name = 'select_' + enode.name()
        nodename = self.make_node_name(enode_name, nodenames, parent_names)
        input_names = [input_name for input_name in enode.childrenNames()]
        have_optional = any([getattr(enode.child(x), 'skip_invalid', False)
                            for x in input_names])
        output_names = ['switch_out']
        if hasattr(enode, 'switch_output'):
            output_names = enode.switch_output
            if isinstance(output_names, str) \
                    or isinstance(output_names, six.text_type):
                output_names = [output_names]  # have a list
        elif exported:
            buffered_lines['switches'].append(
                '        # warning, the switch output trait should be '
                'renamed to a more comprehensive name\n')
        if exported and not hasattr(enode, 'selection_outputs'):
            buffered_lines['switches'].append(
                '        # warning, input items should be connected to '
                'adequate output items in each subprocess in the switch.\n')
        if exported:
            # postpone add_switch line after we have determined its params types
            for output_name in output_names:
                self.export_output(buffered_lines, use_weak_ref(enode),
                                   nodename, output_name,
                                   use_weak_ref(p), output_name, selfoutparams,
                                   revoutparams, processed_links,
                                   self_out_traits, weak_outputs)
        out_types = {}
        if hasattr(enode, 'selection_outputs'):
            # connect children outputs to the switch
            sel_out = enode.selection_outputs
            sw_options = ''
            for link_src, link_pars in zip(input_names, sel_out):
                if not isinstance(link_pars, list) \
                        and not isinstance(link_pars, tuple):
                    link_pars = [link_pars]
                for link_par, output_name in zip(link_pars, output_names):
                    if link_par is None:  # not connected
                        input_name = '_switch_'.join((link_src, output_name))
                        buffered_lines['exports'].append(
                            '        self.do_not_export.add((\'%s\', \'%s\'))\n'
                            % (nodename, input_name))
                        continue
                    if link_par.startswith('/'):  # absolute name, not in child
                        src = enode
                        link_par = link_par[1:]
                    else:
                        src = enode.child(link_src)
                    link_par_split = link_par.split('.')
                    if len(link_par_split) == 1:
                        src = use_weak_ref(src._parameterized)
                    else:
                        while len(link_par_split) > 1:
                            srcname_short = link_par_split.pop(0)
                            src = src.child(srcname_short)
                        src = use_weak_ref(src._parameterized)
                        link_par = link_par_split[-1]
                    # in switches, input params are the concatenation of declared
                    # input params and the output "group" name
                    input_name = '_switch_'.join((link_src, output_name))
                    src_par = src().signature[link_par]
                    out_types.setdefault(output_name, []).append(src_par)
                    # input_name = link_src  # has changed again in Switch...
                    links.append((src, link_par, use_weak_ref(enode), input_name,
                                  weak_outputs))
                    processed_links.add(
                        (src, link_par, use_weak_ref(p), output_name))
                    processed_links.add(
                        (use_weak_ref(p), output_name, src, link_par))
                    processed_links.add(
                        (src, link_par, use_weak_ref(p), input_name))
                    processed_links.add(
                        (use_weak_ref(p), input_name, src, link_par))
            if exported:
                for out_name in out_types.keys():
                    src = out_types[out_name]
                    out_types[out_name] = self.capsul_merged_param_type(src)
                out_types_list = []
                for out in output_names:
                    if out in out_types:
                        ptype, options = out_types[out]
                        todel = None
                        for opt in options:
                            if opt.startswith('output='):
                                todel = opt
                                break
                        if todel:
                            options.remove(todel)
                        out_types_list.append(
                            self.param_type_decl_string(ptype, options,
                                                        as_instance=True))
                    else:
                        out_types[output_name] = (self.Any, [])
                        out_types_list.append('Any()')
                if have_optional:
                    sw_options += ', opt_nodes=True'
                input_names = repr(input_names)
                buffered_lines['switches'].append(
                    '        self.add_switch(\'%s\', %s, %s, output_types=[%s]%s)\n'
                    % (nodename, input_names, repr(output_names),
                      ', '.join(out_types_list), sw_options))

        # select the right child
        for sub_node_name in enode.childrenNames():
            node = enode.child(sub_node_name)
            if node.isSelected():
                buffered_lines['initialization'].append(
                    '        if \'%s\' in self.nodes:\n' % sub_node_name)
                buffered_lines['initialization'].append(
                    '            self.nodes[\'%s\'].switch = \'%s\'\n'
                    % (nodename, sub_node_name))
        return nodename


    def param_type_decl_string(self, ptype, options, as_instance=False):
        return '%s(%s)' % (ptype, ', '.join(options))


    def reorder_exports(szlf, buffered_lines, p):
        old_lines = buffered_lines['exports']
        reordered = [0] * len(old_lines)
        delayed = False
        linkre = re.compile(
            '^ *self.export_parameter\(\'([^,]+)\', \'([^\']+)\'(, \''
            '([^\']+)\')(, weak_link=True)?\)$')
        omax = 0
        for i, line in enumerate(old_lines):
            if line.startswith('        #'):
                delayed = True
                reordered[i] = -1
            else:
                m = linkre.match(line)
                if not m:
                    reordered[i] = -1
                else:
                    if len(m.groups()) >= 4:
                        out_name = m.group(4)
                    else:
                        out_name = m.group(2)
                    if out_name in p.signature:
                        sign_ind = p.signature.sortedKeys.index(out_name)
                        reordered[i] = sign_ind * 2 + 1
                        if reordered[i] > omax:
                            omax = reordered[i]
                        if delayed:
                            # move comment line just before its command line
                            reordered[i - 1] = reordered[i] - 1
                    else:
                        reordered[i] = -1
                delayed = False
        omax += 1
        revorder = {}
        for i in six.moves.xrange(len(reordered)):
            # move non-recognized lines at the end
            if reordered[i] < 0:
                reordered[i] = omax
                omax += 1
            # inverse map
            revorder[reordered[i]] = i
        new_lines = []
        for i in sorted(revorder.keys()):
            j = revorder[i]
            new_lines.append(old_lines[j])
        buffered_lines['exports'] = new_lines


    def write_buffered_lines(self, out, buffered_lines, sections=None):
        if sections is None:
            sections = ('nodes', 'switches', 'exports', 'links',
                        'initialization')
        for section in sections:
            if buffered_lines.get(section):
                out.write(u'        # %s section\n' % section)
                for line in buffered_lines[section]:
                    out.write(six.ensure_text(line))
                out.write(u'\n')


    def write_pipeline_definition(self, p, out, parse_subpipelines=False,
                                  get_all_values=False, module_name_prefix=None,
                                  use_process_names={},
                                  lowercase_modules=True):
        '''Write a pipeline structure in the out file, and links between pipeline
        nodes.
        If parse_subpipelines is set, the pipeline structure inside sub-pipelines
        which are already Axon processes is also parsed (this is generally
        unneeded).
        '''

        # writing will be buffered so as to allow reordering
        buffered_lines = {'nodes': [], 'switches': [], 'exports': [], 'links': [],
                          'initialization': []}
        out.write(u'\n\n')
        out.write(u'    def pipeline_definition(self):\n')
        # enodes list: each element is a 6-tuple:
        # axon_node, name, exported, weak_outputs, parents, parentnode
        enodes = [(p.executionNode(), None, True, False, None, None)]
        links = self.parse_links(p, p)
        processed_links = set()
        # procmap: weak_ref(process) -> (node_name, exported)
        # non-exported nodes are not built as nodes, but may be used by links
        procmap = {weakref.ref(p): ('', True)}
        nodenames = {}
        selfoutparams = {}
        revoutparams = {}
        self_out_traits = []
        while enodes:
            enode, enode_name, exported, weak_outputs, parents, parentnode \
                = enodes.pop(0)
            nodename = None
            if isinstance(enode, procbv.ProcessExecutionNode) \
                    and (len(list(enode.children())) == 0
                        or not parse_subpipelines):
                if enode_name is None:
                    enode_name = enode.name()
                nodename = self.make_node_name(enode_name, nodenames, parents)
                proc = enode._process
                if isinstance(proc, CapsulProcess):
                    # we have actually a wrapped Capsul process: remove the
                    # wrapping layer and use it directly
                    moduleprocid = '.'.join(
                        [proc.get_capsul_process().__module__,
                        proc.get_capsul_process().__class__.__name__])
                else:
                    procid = proc.id()
                    moduleprocid = self.make_module_name(procid,
                                                         module_name_prefix,
                                                         use_process_names,
                                                         lowercase_modules)
                procmap[use_weak_ref(proc)] = (nodename, exported)
                if exported:
                    skip_invalid = getattr(enode, 'skip_invalid', False)
                    if skip_invalid:
                        opt = ', skip_invalid=True'
                    else:
                        opt = ''
                    buffered_lines['nodes'].append(
                        '        self.add_process(\'%s\', \'%s\'%s)\n'
                        % (nodename, moduleprocid, opt))
                    if weak_outputs:
                        ind = ''
                        if skip_invalid:
                            buffered_lines['nodes'].append(
                                '        if \'%s\' in self.nodes:\n' % nodename)
                            ind = '    '
                        buffered_lines['nodes'].append(
                            '        %sself.nodes[\'%s\']._weak_outputs = True\n'
                            % (ind, nodename))
                    links += self.parse_links(p, proc, weak_outputs)
                    for param_name in six.iterkeys(proc.signature):
                        if not proc.isDefault(param_name):
                            value = getattr(proc, param_name)
                            buffered_lines['initialization'].append(
                                '        self.nodes[\'%s\'].%s = %s\n'
                                % (nodename, param_name, repr(value)))
                new_parents = (parents or []) + [nodename]
                enodes += [(enode.child(name), name, False, weak_outputs,
                            new_parents, enode) for name in enode.childrenNames()]
                # parse process signature, look for non-default values
            else:
                if isinstance(enode, procbv.SelectionExecutionNode) and exported:
                    # FIXME: BUG: if not exported, should we rebuild switch params
                    # list, and doing this, export again internal params ?
                    nodename = self.write_switch(enode, buffered_lines,
                                                 nodenames, links, p,
                                                 processed_links,
                                                 selfoutparams, revoutparams,
                                                 self_out_traits, exported,
                                                 parents, enode_name,
                                                 weak_outputs)
                    procmap[use_weak_ref(enode)] = (nodename, exported)
                    # children should have weak outputs so that they can be
                    # deactivated by the switch
                    weak_outputs = True
                new_parents = parents
                enodes += [(enode.child(name), name, exported, weak_outputs,
                            new_parents, enode) for name in enode.childrenNames()]
            if nodename and not enode.isSelected() and exported:
                # FIXME: the exported flag filters out sub-nodes of sub-pipelines
                # so it is not possible this way to unselect a node inside a
                # sub-pipeline.
                # To do so we would have to remove the exported test here,
                # but it would cause other problems, such as sub-nodes naming,
                # which should not follow the "global" rule make_node_name().
                if parentnode \
                        and isinstance(parentnode, procbv.SelectionExecutionNode):
                    continue  # switches have already their selection activation
                if parents:
                    sub_node_address = '.'.join(
                        ['nodes[\'%s\'].process' % sub_name
                            for sub_name in parents])
                    buffered_lines['initialization'].append(
                        '        self.%s.nodes_activation.%s = False\n'
                        % (sub_node_address, nodename))
                else:
                    buffered_lines['initialization'].append(
                        '        self.nodes_activation.%s = False\n' % nodename)

        self.write_pipeline_links(p, buffered_lines, procmap, links,
                                  processed_links, selfoutparams, revoutparams,
                                  self_out_traits)

        do_not_export = getattr(p, 'capsul_do_not_export', set())
        if do_not_export:
            buffered_lines['exports'].append(
                '        self.do_not_export.update(%s)\n' % repr(do_not_export))
        # try to respect pipeline main parameters ordering
        self.reorder_exports(buffered_lines, p)
        # flush the write buffer
        self.write_buffered_lines(out, buffered_lines,
                                  sections=('nodes', 'switches', 'exports',
                                            'links'))

        # remove this when there is a more convenient method in Pipeline
        # out.write(
    # '''        # export orphan output parameters
            # self.export_internal_parameters()

    #''')
        #
        buffered_lines['initialization'] += [
            "        # export orphan parameters\n",
            "        if not hasattr(self, '_autoexport_nodes_parameters') \\\n",
            "                or self._autoexport_nodes_parameters:\n",
            "            self.autoexport_nodes_parameters()\n"]
        # flush the init section buffer
        self.write_buffered_lines(out, buffered_lines,
                                  sections=('initialization', ))
        if all([not buffered_lines.get(section)
                for section in ('nodes', 'exports', 'links', 'initialization')]):
            out.write(u'        pass\n')

        out.write(
            u'''
    def autoexport_nodes_parameters(self):
        \'\'\'export orphan and internal output parameters\'\'\'
        for node_name, node in self.nodes.items():
            if node_name == '':
                continue # skip main node
            if hasattr(node, '_weak_outputs'):
                weak_outputs = node._weak_outputs
            else:
                weak_outputs = False
            for parameter_name, plug in node.plugs.items():
                if parameter_name in ('nodes_activation', 'selection_changed'):
                    continue
                if (node_name, parameter_name) not in self.do_not_export:
                    if not plug.output and plug.links_from:
                        continue
                    weak_link = False
                    if plug.output:
                        if plug.links_to: # or plug.links_from:
                            # some links exist
                            if [True for x in plug.links_to \\
                                    if x[0]=='' or isinstance(x[2], Switch)] \\
                                    or \\
                                    [True for x in plug.links_from \\
                                    if x[0]=='' or isinstance(x[2], Switch)]:
                                # a link to the main pipeline or to a switch
                                # already exists
                                continue
                            # links exist but not to the pipeline: export
                            # weak_link = True
                    if weak_outputs and plug.output:
                        weak_link = True
                    self.export_parameter(node_name, parameter_name,
                        '_'.join((node_name, parameter_name)),
                        weak_link=weak_link, is_optional=True)

''')


# ----

    def __call__(self, proc, outfile, module_name_prefix=None,
                 parse_subpipelines=False, get_all_values=True,
                 capsul_process_name=None, use_process_names={},
                 lowercase_modules=True):
        '''Converts an Axon process or pipeline into a CAPSUL process or
        pipeline.
        The output is a file, named with the outfile parameter.

        Parameters
        ----------
        proc: axon process ID (string) or instance
            process to be converted
        outfile: filename
            output file name for the converted process in CAPSUL API
        module_name_prefix: module path (string) (optional)
            if specified, this prefix will be prepended to processes module names
        parse_subpipelines: bool (optional)
            if True, sub-pipelines internals will be extracted in the current one
            Experimental. Expect strange effects when you use it.
            Default is False.
        get_all_values: bool (optional)
            if True, the current values of the input process instance will all be
            reported to the output process.
            Default is True.
        capsul_process_name: string (optional)
            if specified, name of the converted Capsul process. Otherwise use the
            same name as the Axon process ID.
        use_process_names: dict string:string (optional)
            names mapping table between Axon process IDs and Capsul process names
            when used as pipeline nodes. Default: same as Axon IDs.
        '''

        # try using autopep8
        try:
            import autopep8
        except ImportError:
            autopep8 = None

        if isinstance(proc, procbv.Process):
            procid = proc.id()
            p = proc
        else:
            procid = proc
            p = procbv.getProcessInstance(procid, ignoreValidation=True)

        if capsul_process_name is None:
            capsul_process_name = procid

        if p.executionNode():
            proctype = Pipeline
        else:
            proctype = Process

        if autopep8 is not None:
            # write in a string buffer
            out = six.StringIO()
        else:
            out = io.open(outfile, 'w', encoding='utf-8')

        if self.ver == '2':
            out.write(u'''# -*- coding: utf-8 -*-
try:
    from traits.api import File, Directory, Float, Int, Bool, Enum, Str, \\
        List, Any, Undefined
except ImportError:
    from enthought.traits.api import File, Directory, Float, Int, Bool, Enum, \\
        Str, List, Any, Undefined

from capsul.api import Process
import six
''')
        else:
            out.write(u'''# -*- coding: utf-8 -*-
from soma.controller import File, Directory, undefined, Any, \\
    Literal, field
from pydantic import conlist
from capsul.api import Process
''')

        if proctype is Pipeline:
            out.write(u'''from capsul.api import Pipeline
from capsul.api import Switch
''')
        out.write(u'''

class ''')
        out.write(six.ensure_text(capsul_process_name) + u'(%s):\n' % proctype.__name__)

        if proctype is Pipeline:
            out.write(u'''    def __init__(self, autoexport_nodes_parameters=True, **kwargs):
        self._autoexport_nodes_parameters = autoexport_nodes_parameters
        super(%s, self).__init__(False, **kwargs)
        del self._autoexport_nodes_parameters
#        if autoexport_nodes_parameters:
#            self.autoexport_nodes_parameters()\n''' % capsul_process_name)
            self.write_pipeline_definition(
                p, out, parse_subpipelines=parse_subpipelines,
                get_all_values=get_all_values,
                module_name_prefix=module_name_prefix,
                use_process_names=use_process_names,
                lowercase_modules=lowercase_modules)
        else:
            out.write(u'    def __init__(self, **kwargs):\n')
            out.write(u'        super(%s, self).__init__(**kwargs)\n' % capsul_process_name)
            self.write_process_definition(p, out,
                                          get_all_values=get_all_values)

        if autopep8 is not None:
            # use autopep8 and save to an actual file
            if [int(x) for x in autopep8.__version__.split('.')] >= [1, 0, 0]:
                pretty_code = autopep8.fix_code(out.getvalue())
            else:  # old versions of autopep8
                pretty_code = autopep8.fix_string(out.getvalue())
            out = io.open(outfile, 'w', encoding='utf-8')
            out.write(pretty_code)


class AxonToCapsul_v3(AxonToCapsul):

    Any = 'Any'
    Undefined = 'undefined'

    def get_choice_type(self, choice):
        if len(choice.values) == 0:
            return None
        element_types = {
            six.text_type: str,
            tuple: list,
        }
        choice_types = [element_types.get(type(t[min(1, len(t) - 1)]),
                                          type(t[min(1, len(t) - 1)]))
                        for t in choice.values]
        choice0 = choice_types[0]
        if all([elem is choice0 for elem in choice_types[1:]]):
            return choice0
        # test compatible types, ie (int, float) -> float
        if all([elem in (int, float) for elem in choice_types]):
            return float
        return None


    def get_openchoice_type(self, choice):
        trait_type = self.get_choice_type(choice)
        if trait_type is None:
            trait_type = str  # default to string
        return trait_type


    def point3d_options(self, point):
        return ['default_factory=lambda: [0, 0, 0]']


    def matrix_options(self, list_trait):
        return ['float']


    def diskitem_type(self, diskitem):
        otype = None
        for format in diskitem.formats:
            f = neuroDiskItems.getFormat(format)
            if otype is None \
                    and f.fileOrDirectory() is neuroDiskItems.Directory:
                otype = 'Directory'
            elif f.fileOrDirectory() is not neuroDiskItems.Directory:
                otype = 'File'
                break
        if otype is None:
            otype = 'File'
        return otype


    def diskitem_options(self, diskitem):
        extre = re.compile('^.*\|[^*]*\*(.*)$')
        exts = []
        options = []
        if isinstance(diskitem, WriteDiskItem):
            options.append('write=True')
        else:
            options.append('read=True')
        #formats = sorted(diskitem.formats)
        formats = diskitem.formats
        for format in formats:
            f = neuroDiskItems.getFormat(format)
            for pat in f.patterns.patterns:
                m = extre.match(pat.pattern)
                if m is not None and m.group(1) not in exts:
                    exts.append(m.group(1))
        if len(exts) != 0:
            options.append('allowed_extensions=%s' % repr(exts))
        return options


    @property
    def param_types_table(self):
        if self._param_types_table is not None:
            return self._param_types_table

        self._param_types_table= \
        {
            neuroData.Boolean: bool,
            neuroData.String: str,
            neuroData.Number: float,
            neuroData.Float: float,
            neuroData.Integer: int,
            ReadDiskItem: (self.diskitem_type, self.diskitem_options),
            WriteDiskItem: (self.diskitem_type, self.diskitem_options),
            neuroData.Choice: ('Literal[]', choice_options),
            neuroData.OpenChoice: (self.get_openchoice_type,
                                   self.open_choice_options),
            neuroData.ListOf: list,
            neuroData.Point3D: ('conlist(float, min_items=3, max_items=3)',
                                self.point3d_options),
            neuroData.Matrix: ('list[]', self.matrix_options),
        }
        return self._param_types_table


    def capsul_param_type(self, axon_param):
        newtype = self.param_types_table.get(type(axon_param))
        paramoptions = []
        if newtype is None:
            print('write_process_signature: type', type(axon_param), 'not found')
            newtype = str
        if isinstance(newtype, tuple):
            paramoptions = newtype[1](axon_param)
            newtype = newtype[0]
        if not axon_param.mandatory:
            paramoptions.append('optional=True')
        if inspect.isfunction(newtype) or inspect.ismethod(newtype):
            # newtype is a function: call it to get the actual type
            newtype = newtype(axon_param)
        if hasattr(newtype, '__name__'):
            # take name of a type class
            newtype = newtype.__name__
        section = axon_param.getSectionTitleIfDefined()
        if section is not None:
            paramoptions.append('groups=("%s",)' % section)
        return newtype, paramoptions


    def param_type_decl_string(self, ptype, options, as_instance=False):
        #if ptype.endswith('()'):
            #type_str = '%s(%s)' % (ptype[:-2], ', '.join(options))
        if isinstance(ptype, str) and ptype.endswith('[]'):
            type_opt = [p for p in options if '=' not in p]
            par_opt = [p for p in options if '=' in p]
            type_str = '%s[%s]' % (ptype[:-2], ', '.join(type_opt))
            type_str = ', '.join([type_str] + par_opt)
            if as_instance and par_opt:
                type_str = 'field(type_=%s)' % type_str
        else:
            type_str = ', '.join([ptype] + options)
            if as_instance and options:
                type_str = 'field(type_=%s)' % type_str
        return type_str


    def write_process_signature(self, p, out, buffered_lines,
                                get_all_values=True):
        # write signature
        for name, param in six.iteritems(p.signature):
            newtype, paramoptions = self.capsul_param_type(param)
            type_str = self.param_type_decl_string(newtype, paramoptions)

            out.write(u'        self.add_field(\'%s\', %s)\n'
                      % (name, type_str))
            if get_all_values or not p.isDefault(name):
                value = getattr(p, name)
                if value is not None:
                    buffered_lines['initialization'].append(
                        '        self.%s = %s\n' % (name, repr(value)))
                    # print('non-default value for %s in %s' % (name, p.name))
                elif type(param) in (neuroData.Boolean, neuroData.Number,
                                    neuroData.Float, neuroData.Integer):
                    # None as number is a forced optional value
                    buffered_lines['initialization'].append(
                        '        self.%s = %s\n' % (name, 'undefined'))
        out.write(u'\n\n')


    def write_process_execution(self, p, out):
        axon_name = p.id()
        out.write(u'''    def execution(self, context=None):
        from brainvisa import axon
        from brainvisa.configuration import neuroConfig
        import brainvisa.processes

        neuroConfig.gui = False
        neuroConfig.fastStart = True
        neuroConfig.logFileName = ''

        axon.initializeProcesses()

        kwargs = {}
        for field in self.fields():
            name = field.name
            value = getattr(self, name)
            if value is undefined:
                continue
            if is_path(field) and value != '':
                kwargs[name] = value
            elif is_list(field):
                kwargs[name] = list(value)
            else:
                kwargs[name] = value

        context = brainvisa.processes.defaultContext()
        context.runProcess('%s', **kwargs)
''' % axon_name)




def get_subprocesses(procid):
    '''Recursive list of children processes.

    Parameters
    ----------
    procid: str or brainvisa Process
        process (pipeline) to parse

    Returns
    -------
    set of processes found inside procid
    '''
    subprocs = set()
    if not isinstance(procid, procbv.Process):
        proc = procbv.getProcessInstance(procid, ignoreValidation=True)
    else:
        proc = procid
    enode = proc.executionNode()
    if enode is None:
        return subprocs
    nodes = list(enode.children())
    while nodes:
        node = nodes.pop(0)
        if isinstance(node, procbv.ProcessExecutionNode):
            subprocs.add(node._process)
        nodes += list(node.children())
    return subprocs


def get_process_id(proc):
    '''ID of a process or ID'''
    if isinstance(proc, procbv.Process):
        return proc.id()
    return proc


def fix_case(module_name, lowercase_modules):
    if lowercase_modules:
        return module_name.lower()
    return module_name


def module_filename(process_name, lowercase_modules, gen_process_names):
    return fix_case(gen_process_names.get(process_name, process_name),
                    lowercase_modules)


def axon_to_capsul_main(argv):

    parser = OptionParser('Convert an Axon process into a Capsul '
                          'process.\nAlso works for pipeline structures.\n'
                          'Parameters links for completion are not preserved (yet), but '
                          'inter-process links in pipelines are (normally) rebuilt.')
    parser.add_option('-c', '--capsul',
                      default='2',
                      help='Capsul lib version: 2 or 3')
    parser.add_option('-p', '--process', dest='process', action='append',
                      default=[],
                      help='input process ID. Ex: NobiasHistoAnalysis. Several -p options '
                      'are allowed and should each correspond to a -o option.')
    parser.add_option('-o', '--output', dest='output', metavar='FILE',
                      action='append', default=[],
                      help='output .py file for the converted process code')
    parser.add_option('-n', '--name', dest='name', action='append',
                      default=[],
                      help='name of converted Capsul processes. Default: same as Axon. '
                      'Individual processes may be renamed. The syntax is '
                      'axon_name:capsul_name, ex: "-n BiasCorrection:bias_correction". '
                      'Several -n options may be specified')
    parser.add_option('-m', '--module', dest='module',
                      help='module name used as namespace to get the sub-processes in a '
                      'pipeline')
    parser.add_option('-u', '--use', dest='use_proc', action='append',
                      default=[],
                      help='names of processes to use in pipeline nodes. As for -n '
                      'option, the syntax is axon_name:capsul_name. But this table is not '
                      'used when generating a Capsul process class name, but only when '
                      'using it to get a process inside a pipeline. The capsul name is '
                      'the full module + class name, ex: morpho.morphologist.Morphologist')
    parser.add_option('-r', '--recursive_sub', dest='parse_subpipelines',
                      action='store_true', default=False,
                      help='recursively parse sub-pipelines of a pipeline. This is mostly '
                      'a debugging feature, since it is generally not needed because '
                      'sub-pipelines are processes and can be converted and used '
                      'directly. Moreover with this option, pipeline processes are not '
                      'exported as themselves, but may contain parameters which will not '
                      'be exported and may cause missing or broken links.')
    parser.add_option('-s', '--subprocess', dest='subprocess',
                      action='store_true', default=False,
                      help='automatically convert sub-processes of a pipeline, using the '
                      'process IDs as both class name and output file names. Names '
                      'conversion through the -u option applies. This option mainly '
                      'avoids to specify all pipeline processes via series of -p/-o '
                      'parameters. Additional sub-processes specified through -p/-o may '
                      'replace them.')
    parser.add_option('-l', '--lowercase_modules', dest='lowercase_modules',
                      action='store_true', default=True,
                      help='convert process/pipeline classes modules names to lowercase. '
                      'Used with the -s option. Default=True')

    options, args = parser.parse_args(argv)
    if len(args) != 0:
        parser.print_help()
        sys.exit(1)

    if len(options.process) != len(options.output):
        raise ValueError(
            'There should be the same number of -p options and -o options')

    ver = options.capsul

    converter = AxonToCapsulInstance(ver=ver)

    # processes.fastStart = True
    from brainvisa.configuration import neuroConfig
    neuroConfig.ignoreValidation = True
    processes.initializeProcesses()
    lowercase_modules = options.lowercase_modules
    gen_process_names = dict([(axon, capsul)
                              for (axon, capsul) in [name.split(':') for name in options.name]])
    use_process_names = dict(
        [(axon,
          converter.make_module_name(capsul, options.module, {},
                                     lowercase_modules))
         for axon, capsul in six.iteritems(gen_process_names)])
    # print('converted proc names:', use_process_names)
    use_process_names.update(dict([(axon, capsul)
                                   for (axon, capsul) in [name.split(':') for name in options.use_proc]]))

    # print('use_process_names:', use_process_names)

    done_processes = set()
    todo = list(zip([procbv.getProcessInstance(p, ignoreValidation=True)
                for p in options.process],
               options.output))
    if options.subprocess:
        added_processes = []
        for proc, outfile in todo:
            added_processes += get_subprocesses(proc)
        todo += list(zip(list(added_processes),
                    [module_filename(p.id(), lowercase_modules,
                                     gen_process_names) + '.py'
                     for p in added_processes]))

    todo = set(todo)  # remove duplicates

    for proc, outfile in todo:
        if isinstance(proc, CapsulProcess):
            # already a capsul process
            continue
        procid = get_process_id(proc)
        # print('Process:', procid, '->', gen_process_names.get(procid), '\n')
        if procid in done_processes:
            continue
        done_processes.add(procid)
        proc = converter(proc, outfile,
                         module_name_prefix=options.module,
                         parse_subpipelines=options.parse_subpipelines,
                         get_all_values=True,
                         capsul_process_name=gen_process_names.get(
                             procid),
                         use_process_names=use_process_names,
                         lowercase_modules=lowercase_modules)


if __name__ == '__main__':
    axon_to_capsul_main(sys.argv[1:])
