#!/usr/bin/env python

from brainvisa.axon import processes
from capsul.process import process
from capsul.pipeline import pipeline
from brainvisa import processes as procbv
from brainvisa.data import neuroData
from brainvisa.data.readdiskitem import ReadDiskItem
from brainvisa.data.writediskitem import WriteDiskItem
from traits import api as traits
import weakref
import sys
import re

from optparse import OptionParser


def write_diskitem_options(wdiskitem):
    return ['output=True']


def choice_options(choice):
    return [repr(x[0]) for x in choice.values]


def open_choice_options(choice):
    if len(choice.values) != 0:
        print choice.values
        return ['default_value=' + repr(choice.values[0][0])]
    else:
        return []


def point3d_options(point):
    # note: not using traits.ListFloat because its constructor doesn't seem
    # to take parmeters into account (minlen, maxlen, value)
    return ['trait=Float()', 'minlen=3', 'maxlen=3', 'value=[0, 0, 0]']


def write_process_signature(p, out, buffered_lines, get_all_values=False):
    # write signature
    for name, param in p.signature.iteritems():
        newtype = param_types_table.get(type(param))
        paramoptions = []
        if newtype is None:
            print 'write_process_signature: type', type(param), 'not found'
            newtype = traits.Str
        if isinstance(newtype, tuple):
            paramoptions = newtype[1](param)
            newtype = newtype[0]
        if not param.mandatory:
            paramoptions.append('optional=True')
        if hasattr(newtype, '__name__'):
            # take name of a type class
            newtype = newtype.__name__
        out.write('        self.add_trait(\'%s\', %s(%s))\n' \
            % (name, newtype, ', '.join(paramoptions)))
        if get_all_values or not p.isDefault(name):
            value = getattr(p, name)
            if value is not None:
                buffered_lines['initialization'].append(
                    '        self.%s = %s\n' % (name, repr(value)))
                # print 'non-default value for %s in %s' % (name, p.name)
    out.write('\n\n')


def write_process_execution(p, out):
    out.write('''    def _run_process(self):
        from brainvisa import axon
        from brainvisa.configuration import neuroConfig
        import brainvisa.processes

        neuroConfig.gui = False
        neuroConfig.fastStart = True
        neuroConfig.logFileName = ''

        axon.initializeProcesses()

        kwargs = {name : getattr(self,name) for name in self.user_traits()}

        context = brainvisa.processes.defaultContext()
        context.runProcess(self.id.split('.')[-1], **kwargs)
''')


def write_process_definition(p, out, get_all_values=False):
    buffered_lines = {'initialization': []}
    write_process_signature(p, out, buffered_lines,
        get_all_values=get_all_values)
    write_buffered_lines(out, buffered_lines, sections=('initialization', ))
    write_process_execution(p, out)


def str_to_name(s):
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


def capsul_process_name(procid):
    return procid  # TODO


def use_weak_ref(obj):
    if obj is None:
        return None
    if type(obj) is weakref.ProxyType:
        return obj.__weakref__
    if type(obj) is weakref.ReferenceType:
        return obj
    return weakref.ref(obj)


def parse_links(pipeline, proc, weak_outputs=False):
    links = []
    proc = use_weak_ref(proc)
    for param, linkdefs in proc()._links.iteritems():
        for dstproc, dstparam, mlink, unknown, force in linkdefs:
            dstproc = use_weak_ref(dstproc)
            # check if link is compatible
            if dstproc is None or dstparam is None or dstproc is proc:
                # intra-process links are dropped.
                continue
            srcsign = proc().signature[param]
            dstsign = dstproc().signature[dstparam]
            if type(srcsign) is not type(dstsign) \
                    and (not isinstance(srcsign, ReadDiskItem) \
                        or not isinstance(dstsign, ReadDiskItem)):
                # incompatible parameters types
                continue
            if isinstance(srcsign, ReadDiskItem):
                if srcsign.type.isA(dstsign.type.name) \
                        or dstsign.type.isA(srcsign.type.name):
                    # compatible type
                    if isinstance(dstsign, WriteDiskItem) \
                            or (not isinstance(srcsign, WriteDiskItem) \
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


def is_output(proc, param):
    if isinstance(proc(), procbv.SelectionExecutionNode):
        # SelectionExecutionNode nodes may be used for switch nodes.
        # They do not have parameters in the Axon API since they are not
        # processes. But the Capsul pipeline side (Switch node) has input
        # parameters which should be connected from children outputs, and
        # output parameters which should be exported.
        if (hasattr(proc(), 'switch_output') \
                    and proc().switch_output == param) \
                or (not hasattr(proc(), 'switch_output') \
                    and param=='switch_out'):
            return True
        else:
            return False
    signp = proc().signature.get(param)
    return isinstance(signp, WriteDiskItem)


def converted_link(linkdef, links, pipeline, selfinparams, revinparams,
        selfoutparams, revoutparams, procmap):
    # find exported source/dest
    weak_link = linkdef[4]
    real_source = find_param_in_parent(linkdef[0], linkdef[1], procmap)
    real_dest = find_param_in_parent(linkdef[2], linkdef[3], procmap)
    if real_source[0] is None or real_dest[0] is None:
        print 'Warning, missing link info for:', linkdef[0]().name, \
            ',', linkdef[1], ' ->', linkdef[2]().name, ',', linkdef[3]
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
        if is_output(linkdef[2], linkdef[3]):
            # dest is an output: needs inversion
            linkdef = (linkdef[2], linkdef[3], linkdef[0], linkdef[1],
                weak_link)
        else:
            altp = selfoutparams.get(linkdef[1])
            if altp is None:
                print '** warning, probably bad link:', linkdef[0]().name, \
                    ',', linkdef[1], ' ->', linkdef[2]().name, ',', linkdef[3]
                print revoutparams
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


def export_output(buffered_lines, src, sname, sparam, p, dparam, selfoutparams,
        revoutparams, processed_links, selfouttraits, weak_outputs=False):
    if dparam in selfouttraits:
        # a trait has been manually declared
        declare_output_trait(buffered_lines, src, sname, sparam, p, dparam,
            selfoutparams, revoutparams, processed_links)
    else:
        # global output param in pipeline signature
        buffered_lines['exports'].append('        # export output parameter\n')
        if weak_outputs:
            buffered_lines['exports'].append(
                '        self.export_parameter(\'%s\', \'%s\', \'%s\', ' \
                'weak_link=True)\n' \
                % (sname, sparam, dparam))
        else:
            buffered_lines['exports'].append(
                '        self.export_parameter(\'%s\', \'%s\', \'%s\')\n' \
                % (sname, sparam, dparam))
        selfoutparams[dparam] = (src, sparam)
        revoutparams[(src, sparam)] = dparam
        processed_links.add((src, sparam, use_weak_ref(p), dparam))
        processed_links.add((use_weak_ref(p), dparam, src, sparam))


def declare_output_trait(buffered_lines, src, sname, sparam, p, dparam,
        selfoutparams, revoutparams, processed_links):
    # global output param in pipeline signature, as a trait
    selfoutparams[dparam] = (src, sparam)
    revoutparams[(src, sparam)] = dparam
    processed_links.add((src, sparam, use_weak_ref(p), dparam))
    processed_links.add((use_weak_ref(p), dparam, src, sparam))


def export_input(buffered_lines, dst, dname, dparam, p, sparam, selfinparams,
        revinparams, processed_links):
    # global input param in pipeline signature
    buffered_lines['exports'].append('        # export input parameter\n')
    buffered_lines['exports'].append(
        '        self.export_parameter(\'%s\', \'%s\', \'%s\')\n' \
        % (dname, dparam, sparam))
    selfinparams[sparam] = (dst, dparam)
    revinparams[(dst, dparam)] = sparam
    processed_links.add((use_weak_ref(p), sparam, dst, dparam))
    processed_links.add((dst, dparam, use_weak_ref(p), sparam))


def make_node_name(name, nodenames):
    name = str_to_name(name)
    if name in nodenames:
        nodenames[name] += 1
        return '%s_%d' % (name, nodenames[name])
    else:
        nodenames[name] = 0
        return name


def is_linked_to_parent(proc, param, parent):
    # get links from proc.param
    if isinstance(proc(), procbv.Process):
        linkdefs = proc()._links.get( param )
        for dstproc, dstparam, mlink, unknown, force in linkdefs:
            if use_weak_ref(dstproc) == parent:
                return dstparam
        # get links to parent
        for pparam, linkdefs in parent()._links.iteritems():
            for srcproc, srcparam, mlink, unknown, force in linkdefs:
                if use_weak_ref(srcproc) == proc and srcparam == param:
                    return pparam
    return None


def find_param_in_parent(proc, param, procmap):
    # parse all nodes since there is no notion of parent
    verbose = False  # debug flag - TODO: remove it when all is OK
    pname, exported = procmap.get(proc, (None, None))
    if exported:  # exported node: direct, OK
        if verbose:
            print '    direct export'
        return (proc, pname, param)
    last = (proc, param)
    allnotfound = False
    if verbose:
        print '    find_param_in_parent:', proc().name, param, ':', pname
    while not allnotfound:
        if verbose:
            print '    try as child:', last[0]().name, '/', last[1]
        child_name = procmap[last[0]][0]
        # look for parent enode
        for new_proc, (new_node_name, exported) in procmap.iteritems():
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
                    print '    test parent:', new_node_name
                new_pname = '_'.join((child_name, last[1]))
                if exported:
                    parent_pname = last[1]
                    if verbose:
                        print '    find_param_in_parent:', proc().name, param
                        print '    ** found:', new_proc().name, new_pname
                    # now check if it is an exported param in the sub-pipeline
                    opname = is_linked_to_parent(proc, param, new_proc)
                    if opname is not None:
                        # then return the exported parent one
                        #parent_pname = opname
                        new_pname = opname
                        if verbose:
                            print '    parent param translated:', new_pname
                    return (new_proc, new_node_name, new_pname)
                last = (new_proc, new_pname)
                break
        else: # loop through the end of procmap
            allnotfound = True
    # not found
    print 'Warning: find_param_in_parent: NOT FOUND'
    print '    was:', proc().name, '/', param
    return (None, None, None)


# is this function useful ?
#def find_param_in_children(proc, param, procmap):
    #print 'find_param_in_children:', proc().name, param
    #node_name, exported = procmap[proc]
    #if exported:  # exported node
        #return proc, node_name, param
    #if isinstance(proc, procbv.Process):
        #node = proc.executionNode()
    #else:
        #node = proc
    #nodes = [(node, param)]
    #while nodes:
        #node, pname = nodes.pop(0)
        #for child_name in node.childrenNames():
            #child = node.child(child_name)
            #if isinstance(child, procbv.Process):
                #new_node = child._process
            #else:
                #new_node = child
            #new_node_name, exported = procmap.get(use_weak_ref(new_node),
                #(None,None))
            #if new_node_name is not None \
                    #and pname.startswith(new_node_name + '_'):
                #new_pname = pname[len(new_node_name) + 1:]
                #if isinstance(new_node, procbv.Process) \
                        #and new_node.signature.has_key(new_pname):
                    ## found
                    #return (new_node, new_node_name, new_pname)
                #nodes.append((child, new_pname))
    #return (None, None, None)


def write_pipeline_links(p, buffered_lines, procmap, links, processed_links,
        selfoutparams, revoutparams, selfouttraits):
    # parse and set pipeline links
    selfinparams = {}
    revinparams = {}
    for link in links:
        link = converted_link(link, processed_links, p, selfinparams,
            revinparams, selfoutparams, revoutparams, procmap)
        if link is None:
            continue
        src, sparam, dst, dparam, weak_link = link
        sname, sexported = procmap.get(src, (None, None))
        if sname is None:
            print 'warning, src process', src().name, 'not found in pipeline.'
            # print 'procmap:', [ k[0]().name for k in procmap ]
            continue  # skip this one
        dname, dexported = procmap.get(dst, (None, None))
        if dname is None:
            print 'warning, dst process', dst().name, 'not found in pipeline.'
            continue  # skip this one
        spname = sparam
        if sname:
            spname = '%s.%s' % (sname, sparam)
        dpname = dparam
        if dname:
            dpname = '%s.%s' % (dname, dparam)
        if sname == '' and sparam not in selfinparams:
            export_input(buffered_lines, dst, dname, dparam, p, sparam,
                selfinparams, revinparams, processed_links)
        elif dname == '' and dparam not in selfoutparams:
            export_output(buffered_lines, src, sname, sparam, p, dparam,
                selfoutparams, revoutparams, processed_links, selfouttraits)
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
                    and is_output(src, sparam) == is_output(dst, dparam):
                if is_output(src, sparam):
                    # both outputs: export 1st
                    sparam2 = sname + '_' + sparam
                    if sparam2 in selfoutparams or sparam2 in selfinparams:
                        # avoid duplicate name
                        sparam2 = sparam2 + '2'
                    export_output(buffered_lines, src, sname, sparam, p,
                        sparam2, selfoutparams, revoutparams, processed_links,
                        selfouttraits)
                    # and link 2nd to this exported output (and switch link)
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
                    export_input(buffered_lines, src, sname, sparam, p,
                        sparam2, selfinparams, revinparams, processed_links)
                    # and link 2nd to this exported input
                    sparam = sparam2
                    spname = sparam2
            if weak_link:
                buffered_lines['links'].append(
                    '        self.add_link(\'%s->%s\', weak_link=True)\n' \
                    % (spname, dpname))
            else:
                buffered_lines['links'].append(
                    '        self.add_link(\'%s->%s\')\n' % (spname, dpname))
        processed_links.add((src, sparam, dst, dparam))
        processed_links.add((dst, dparam, src, sparam))


def write_switch(enode, buffered_lines, nodenames, links, p, processed_links,
        selfoutparams, revoutparams, self_out_traits, exported,
        enode_name=None, weak_outputs=False):
    if enode_name is None:
        enode_name = 'select_' + enode.name()
    nodename = make_node_name(enode_name, nodenames)
    output_name = 'switch_out'
    if hasattr(enode, 'switch_output'):
        output_name = enode.switch_output
    elif exported:
        buffered_lines['nodes'].append(
            '        # warning, the switch output trait should be ' \
            'renamed to a more comprehensive name\n')
    if exported and not hasattr(enode, 'selection_outputs'):
        buffered_lines['nodes'].append(
            '        # warning, input items should be connected to ' \
            'adequate output items in each subprocess in the switch.\n')
    if exported:
        buffered_lines['nodes'].append(
            '        self.add_switch(\'%s\', %s, \'%s\')\n' \
            % (nodename, repr(enode.childrenNames()), output_name))
        export_output(buffered_lines, use_weak_ref(enode), nodename,
            output_name, p, output_name, selfoutparams, revoutparams,
            processed_links, self_out_traits, weak_outputs)
    if hasattr(enode, 'selection_outputs'):
        # connect children outputs to the switch
        sel_out = enode.selection_outputs
        for link_src, link_par in zip(enode.childrenNames(), sel_out):
            link_par_split = link_par.split('.')
            if len(link_par_split) == 1:
                src = use_weak_ref(enode.child(link_src)._process)
            else:
                src = enode.child(link_src)
                while len(link_par_split) > 1:
                    srcname_short = link_par_split.pop(0)
                    src = src.child(srcname_short)
                src = use_weak_ref(src._process)
                link_par = link_par_split[-1]
            # in switches, input params are the concatenation of declared
            # input params and the output "group" name
            input_name = '_switch_'.join((link_src, output_name))
            # input_name = link_src  # has changed again in Switch...
            links.append((src, link_par, use_weak_ref(enode), input_name,
                weak_outputs))
            processed_links.add((src, link_par, use_weak_ref(p), output_name))
            processed_links.add((use_weak_ref(p), output_name, src, link_par))

    # select the right child
    for sub_node_name in enode.childrenNames():
        node = enode.child(sub_node_name)
        if node.isSelected():
            buffered_lines['initialization'].append(
                '        self.nodes[\'%s\'].switch = \'%s\'\n' \
                % (nodename, sub_node_name))
    return nodename


def reorder_exports(buffered_lines, p):
    old_lines = buffered_lines['exports']
    reordered = [0] * len(old_lines)
    delayed = False
    linkre = re.compile(
        '^ *self.export_parameter\(\'([^,]+)\', \'([^\']+)\'(, \'' \
        '([^\']+)\')(, weak_link=True)?\)$')
    omax = 0
    for i, line in enumerate(old_lines):
        if line.startswith('        #'):
            delayed = True
            reordered[i] = -1
        else:
            m = linkre.match(line)
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
                    reordered[i-1] = reordered[i] - 1
            else:
                reordered[i] = -1
            delayed = False
    omax += 1
    revorder = {}
    for i in xrange(len(reordered)):
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


def write_buffered_lines(out, buffered_lines, sections=None):
    if sections is None:
        sections = ('nodes', 'exports', 'links', 'initialization')
    for section in sections:
        if buffered_lines.get(section):
            out.write('        # %s section\n' % section)
            for line in buffered_lines[section]:
                out.write(line)
            out.write('\n')


def make_module_name(procid, module_name_prefix=None):
    if module_name_prefix is None:
        return '%s.%s' % (procid, procid)
    else:
        return '%s.%s.%s' % (module_name_prefix, procid, procid)


def write_pipeline_definition(p, out, parse_subpipelines=False,
        get_all_values=False, module_name_prefix=None):
    '''Write a pipeline structure in the out file, and links between pipeline
    nodes.
    If parse_subpipelines is set, the pipeline structure inside sub-pipelines
    which are already Axon processes is also parsed (this is generally
    unneeded).
    '''

    # writing will be buffered so as to allow reordering
    buffered_lines = {'nodes': [], 'exports': [], 'links': [],
        'initialization': []}
    out.write('\n\n')
    out.write('    def pipeline_definition(self):\n')
    # enodes list: each element is a 4-tuple:
    # axon_node, name, exported, weak_outputs
    enodes = [(p.executionNode(), None, True, False, None, None)]
    links = parse_links(p, p)
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
                and (len(list(enode.children())) == 0 \
                    or not parse_subpipelines):
            if enode_name is None:
                enode_name = enode.name()
            nodename = make_node_name(enode_name, nodenames)
            proc = enode._process
            procid = proc.id()
            capsulproc = capsul_process_name(procid)
            moduleprocid = make_module_name(procid, module_name_prefix)
            procmap[use_weak_ref(proc)] = (nodename, exported)
            if exported:
                buffered_lines['nodes'].append(
                    '        self.add_process(\'%s\', \'%s\')\n' \
                    % (nodename, moduleprocid))
                if weak_outputs:
                    buffered_lines['nodes'].append(
                        '        self.nodes[\'%s\']._weak_outputs = True\n' \
                        % nodename)
                links += parse_links(p, proc, weak_outputs)
                for param_name in proc.signature.iterkeys():
                    if not proc.isDefault(param_name):
                        value = getattr(proc, param_name)
                        buffered_lines['initialization'].append(
                            '        self.nodes[\'%s\'].%s = %s\n' \
                            % (nodename, param_name, repr(value)))
            new_parents = (parents or []) + [nodename]
            enodes += [(enode.child(name), name, False, weak_outputs,
                new_parents, enode) for name in enode.childrenNames()]
            # parse process signature, look for non-default values
        else:
            if isinstance(enode, procbv.SelectionExecutionNode) and exported:
                # FIXME: BUG: if not exported, should we rebuild switch params
                # list, and doing this, export again internal params ?
                nodename = write_switch(enode, buffered_lines, nodenames,
                    links, p, processed_links, selfoutparams, revoutparams,
                    self_out_traits, exported, enode_name, weak_outputs)
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
                continue # switches have already their selection activation
            if parents:
                sub_node_address = '.'.join(
                    ['nodes[\'%s\'].process' % sub_name \
                        for sub_name in parents])
                buffered_lines['initialization'].append(
                    '        self.%s.nodes_activation.%s = False\n' \
                    % (sub_node_address, nodename))
            else:
                buffered_lines['initialization'].append(
                    '        self.nodes_activation.%s = False\n' % nodename)

    write_pipeline_links(p, buffered_lines, procmap, links, processed_links,
        selfoutparams, revoutparams, self_out_traits)

    # try to respect pipeline main parameters ordering
    reorder_exports(buffered_lines, p)
    # flush the write buffer
    write_buffered_lines(out, buffered_lines,
        sections=('nodes', 'exports', 'links'))

    # remove this when there is a more convenient method in Pipeline
    out.write(
'''        # export orphan output parameters
        for node_name, node in self.nodes.iteritems():
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
                    if not plug.output and (plug.links_to or plug.links_from):
                        continue
                    weak_link = False
                    if plug.output:
                        if plug.links_to or plug.links_from:
                            # some links exist
                            if [True for x in plug.links_to if x[0]==''] \\
                                    or \\
                                    [True for x in plug.links_from \\
                                        if x[0]=='']:
                                # a link to the main pipeline already exists
                                continue
                            # links exist but not to the pipeline: export
                            # weak_link = True
                    if weak_outputs and plug.output:
                        weak_link = True
                    self.export_parameter(node_name, parameter_name,
                        '_'.join((node_name, parameter_name)),
                        weak_link=weak_link)

''')

    # flush the init section buffer
    write_buffered_lines(out, buffered_lines, sections=('initialization', ))


# ----

param_types_table = \
{
    neuroData.Boolean: traits.Bool,
    neuroData.String: traits.Str,
    neuroData.Number: traits.Float,
    neuroData.Float: traits.Float,
    neuroData.Integer: traits.Int,
    ReadDiskItem: traits.File,
    WriteDiskItem: (traits.File, write_diskitem_options),
    neuroData.Choice: (traits.Enum, choice_options),
    neuroData.OpenChoice: (traits.Str, open_choice_options),
    neuroData.ListOf: traits.List,
    neuroData.Point3D: (traits.List, point3d_options),
}


def axon_to_capsul(proc, outfile, module_name_prefix=None,
        parse_subpipelines=False, get_all_values=False):
    '''Converts an Axon process or pipeline into a CAPSUL process or pipeline.
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
        Default is False.
    '''

    if isinstance(proc, procbv.Process):
        procid = proc.id()
        p = proc
    else:
        procid = proc
        p = procbv.getProcessInstance(procid)
    # print 'process:', p

    if p.executionNode():
        proctype = pipeline.Pipeline
    else:
        proctype = process.Process

    out = open(outfile, 'w')
    out.write('''# -*- coding: utf-8 -*-
try:
    from traits.api import File, Float, Int, Bool, Enum, Str, List
except ImportError:
    from enthought.traits.api import File, Float, Int, Bool, Enum, Str, List

from capsul.process.process import Process
from capsul.pipeline.pipeline import Pipeline

class ''')
    out.write(procid + '(%s):\n' % proctype.__name__)
    out.write('''    def __init__(self, **kwargs):
        super(%s, self).__init__(**kwargs)\n''' % procid)

    if proctype is pipeline.Pipeline:
        write_pipeline_definition(p, out,
            parse_subpipelines=parse_subpipelines,
            get_all_values=get_all_values,
            module_name_prefix=module_name_prefix)
    else:
        write_process_definition(p, out, get_all_values=get_all_values)


def axon_to_capsul_main(argv):

    parser = OptionParser('Convert an Axon process into a Capsul ' \
        'process.\nAlso works for pipeline structures.\n' \
        'Parameters links for completion are not preserved (yet), but ' \
        'inter-process links in pipelines are (normally) rebuilt.')
    parser.add_option('-p', '--process', dest='process', action='append',
        help='input process ID. Ex: NobiasHistoAnalysis. Several -p options ' \
        'are allowed and should each correspond to a -o option.')
    parser.add_option('-o', '--output', dest='output', metavar='FILE',
        action='append',
        help='output .py file for the converted process code')
    parser.add_option('-m', '--module', dest='module',
        help='module name used as namespace to get the sub-processes in a ' \
        'pipeline')
    parser.add_option('-r', '--recursive_sub', dest='parse_subpipelines',
        action='store_true', default=False,
        help='recursively parse sub-pipelines of a pipeline. This is mostly ' \
        'a debugging feature, since it is generally not needed because ' \
        'sub-pipelines are processes and can be converted and used ' \
        'directly. Moreover with this option, pipeline processes are not ' \
        'exported as themselves, but may contain parameters which will not ' \
        'be exported and may cause missing or broken links.')

    options, args = parser.parse_args(argv)
    if len(args) != 0:
        parser.print_help()
        sys.exit(1)

    processes.fastStart = True
    processes.initializeProcesses()

    for procid, outfile in zip(options.process, options.output):
        proc = axon_to_capsul(procid, outfile,
        module_name_prefix=options.module,
        parse_subpipelines=options.parse_subpipelines)


if __name__ == '__main__':
    axon_to_capsul_main(sys.argv[1:])

