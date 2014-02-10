#!/usr/bin/env python

from brainvisa.axon import processes
from soma.process import process
from soma.pipeline import pipeline
from brainvisa import processes as procbv
from brainvisa.data import neuroData
from brainvisa.data.readdiskitem import ReadDiskItem
from brainvisa.data.writediskitem import WriteDiskItem
from traits import api as traits
import weakref
import sys

from optparse import OptionParser


def write_diskitem_options(wdiskitem):
    return ['output=True']


def choice_options(choice):
    return [repr(x[0]) for x in choice.values]


def point3d_options(point):
    return ['minlen=3', 'maxlen=3']


def write_process_signature(p, out):
    # write signature
    for name, param in p.signature.iteritems():
        newtype = param_types_table.get(type(param))
        paramoptions = []
        if newtype is None:
            print 'write_process_signature: type', type(param), 'not found'
            newtype = traits.String
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
    out.write('\n\n')


def write_process_execution(p, out):
    out.write('''    def __call__(self):
        from brainvisa import axon
        from brainvisa.configuration import neuroConfig
        import brainvisa.processes

        neuroConfig.gui = False
        neuroConfig.fastStart = True
        neuroConfig.logFileName = ''

        axon.initializeProcesses()

        kwargs = {name : getattr(self,name) for name in self.user_traits()}

        context = brainvisa.processes.defaultContext()
        context.runProcess(self.name_process, **kwargs)
''')


def write_process_definition(p, out):
    write_process_signature(p, out)
    write_process_execution(p, out)


def str_to_name(s):
    s = s.replace(' ', '_')
    s = s.replace('(', '_')
    s = s.replace(')', '_')
    s = s.replace('\'', '_')
    s = s.replace('"', '_')
    s = s.replace(',', '_')
    return s


def soma_process_name(procid):
    return procid  # TODO


def use_weak_ref(obj):
    if obj is None:
        return None
    if type(obj) is weakref.ProxyType:
        return obj.__weakref__
    if type(obj) is weakref.ReferenceType:
        return obj
    return weakref.ref(obj)


def parse_links(pipeline, proc):
    links = []
    proc = use_weak_ref(proc)
    for param, linkdefs in proc()._links.iteritems():
        for dstproc, dstparam, mlink, unknown in linkdefs:
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
                        if (dstproc, dstparam, proc, param) not in links:
                            links.append((dstproc, dstparam, proc, param))
                    else:
                        if (proc, param, dstproc, dstparam) not in links:
                            links.append((proc, param, dstproc, dstparam))
            else:
                # not DiskItems
                if (proc, param, dstproc, dstparam) not in links:
                    links.append((proc, param, dstproc, dstparam))
    return links


def is_output(proc, param):
    if isinstance(proc(), procbv.SelectionExecutionNode):
        # SelectionExecutionNode nodes may be used for switch nodes.
        # They do not have parameters in the Axon API since they are not
        # processes. But the soma-pipeline side (Switch node) has input
        # parameters which should be connected to children outputs to swith.
        return False  # switch are used for inputs only
    signp = proc().signature.get(param)
    return isinstance(signp, WriteDiskItem)


def converted_link(linkdef, links, pipeline, selfinparams, revinparams,
        selfoutparams, revoutparams):
    pipeline = use_weak_ref(pipeline)
    if linkdef[2] is pipeline and linkdef[3] in selfinparams:
        # output in pipeline inputs: invert link
        linkdef = (linkdef[2], linkdef[3], linkdef[0], linkdef[1])
    if linkdef in links:
        return None
    if linkdef[0] is pipeline and linkdef[1] in selfoutparams:
        # source in pipeline outputs: either needs translation, or inversion
        if is_output(linkdef[2], linkdef[3]):
            # dest is an output: needs inversion
            linkdef = (linkdef[2], linkdef[3], linkdef[0], linkdef[1])
        else:
            altp = selfoutparams.get(linkdef[1])
            if altp is None:
                print '** warning, probably bad link:', linkdef[0]().name, \
                    ',', linkdef[1], ' ->', linkdef[2]().name, ',', linkdef[3]
                print revoutparams
                return None
            linkdef = (altp[0], altp[1], linkdef[2], linkdef[3])
    if linkdef in links:
        return None
    if linkdef[0] is not pipeline \
            and (linkdef[0], linkdef[1]) in revinparams:
        # source has an equivalent in exported inputs
        altp = revinparams[(linkdef[0], linkdef[1])]
        linkdef = (pipeline, altp, linkdef[2], linkdef[3])
    if linkdef[2] is not pipeline \
            and (linkdef[2], linkdef[3]) in revoutparams:
        # dest has an equivalent in exported outputs
        altp = revoutparams[(linkdef[2], linkdef[3])]
        linkdef = (linkdef[0], linkdef[1], pipeline, altp)
    if linkdef in links:
        return None
    if linkdef[2] is not pipeline \
            and (linkdef[2], linkdef[3]) in revinparams:
        # dest has an equivalent in exported inputs
        altp = revinparams[(linkdef[2], linkdef[3])]
        linkdef = (pipeline, altp, linkdef[0], linkdef[1])
    if linkdef in links:
        return None
    return linkdef


def export_output(out, src, sname, sparam, p, dparam, selfoutparams,
        revoutparams, processed_links, selfouttraits):
    if dparam in selfouttraits:
        # a trait has been manually declared
        declare_output_trait(out, src, sname, sparam, p, dparam, selfoutparams,
            revoutparams, processed_links)
    else:
        # global output param in pipeline signature
        out.write('        # export output parameter\n')
        out.write(
            '        self.export_parameter(\'%s\', \'%s\', \'%s\')\n' \
            % (sname, sparam, dparam))
        selfoutparams[dparam] = (src, sparam)
        revoutparams[(src, sparam)] = dparam
        processed_links.add((src, sparam, use_weak_ref(p), dparam))
        processed_links.add((use_weak_ref(p), dparam, src, sparam))


def declare_output_trait(out, src, sname, sparam, p, dparam, selfoutparams,
        revoutparams, processed_links):
    # global output param in pipeline signature, as a trait
    selfoutparams[dparam] = (src, sparam)
    revoutparams[(src, sparam)] = dparam
    processed_links.add((src, sparam, use_weak_ref(p), dparam))
    processed_links.add((use_weak_ref(p), dparam, src, sparam))


def export_input(out, dst, dname, dparam, p, sparam, selfinparams,
        revinparams, processed_links):
    # global input param in pipeline signature
    out.write('        # export input parameter\n')
    out.write(
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


def write_pipeline_links(p, out, procmap, links, processed_links,
        selfouttraits):
    # parse and set pipeline links
    selfinparams = {}
    revinparams = {}
    selfoutparams = {}
    revoutparams = {}
    for link in links:
        link = converted_link(link, processed_links, p, selfinparams,
            revinparams, selfoutparams, revoutparams)
        if link is None:
            continue
        src, sparam, dst, dparam = link
        sname = procmap.get(src, None)
        if sname is None:
            print 'warning, src process', src().name, 'not found in pipeline.'
            # print 'procmap:', [ k().name for k in procmap ]
            continue  # skip this one
        dname = procmap.get(dst, None)
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
            export_input(out, dst, dname, dparam, p, sparam, selfinparams,
                revinparams, processed_links)
        elif dname == '' and dparam not in selfoutparams:
            export_output(out, src, sname, sparam, p, dparam, selfoutparams,
                revoutparams, processed_links, selfouttraits)
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
                    export_output(out, src, sname, sparam, p, sparam2,
                        selfoutparams, revoutparams, processed_links,
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
                    export_input(out, src, sname, sparam, p, sparam2,
                        selfinparams, revinparams, processed_links)
                    # and link 2nd to this exported input
                    sparam = sparam2
                    spname = sparam2
            out.write(
                '        self.add_link(\'%s->%s\')\n' % (spname, dpname))
        processed_links.add((src, sparam, dst, dparam))
        processed_links.add((dst, dparam, src, sparam))


def write_switch(enode, out, nodenames, links, p, processed_links,
        enode_name=None):
    self_out_traits = []
    if enode_name is None:
        enode_name = enode.name()
    nodename = make_node_name(enode_name, nodenames)
    output_name = 'switch_out'
    if hasattr(enode, 'switch_output'):
        output_name = enode.switch_output
    else:
        out.write('        # warning, the switch output trait should be ' \
            'renamed to a more comprehensive name\n')
    if not hasattr(enode, 'selection_outputs'):
        out.write('        # warning, input items should be connected to ' \
            'adequate output items in each subprocess in the switch.\n')
    #out.write('        self.add_switch(\'%s\', %s, \'%s\', ' \
        #'output_type=File(output=True))\n' \
        #% (nodename, repr(enode.childrenNames()), output_name))
    out.write('        self.add_switch(\'%s\', %s, \'%s\')\n' \
        % (nodename, repr(enode.childrenNames()), output_name))
    out.write('        self.export_parameter(\'%s\', \'%s\', \'%s\' )\n' \
        % (nodename, output_name, output_name))
    self_out_traits.append(output_name)
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
            links.append((src, link_par, use_weak_ref(enode), link_src))
            processed_links.add((src, link_par,
                use_weak_ref(p), output_name))
            processed_links.add((use_weak_ref(p), output_name, src, link_par))
    return nodename, self_out_traits


def write_pipeline_definition(p, out, parse_subpipelines=False):
    '''Write a pipeline structure in the out file, and links between pipeline
    nodes.
    If parse_subpipelines is set, the pipeline structure inside sub-pipelines
    which are already Axon processes is also parsed (this is generally
    unneeded).
    '''

    out.write('\n\n')
    out.write('    def pipeline_definition(self):\n')
    enodes = [(p.executionNode(), None)]
    links = parse_links(p, p)
    processed_links = set()
    procmap = {weakref.ref(p): ''}
    nodenames = {}
    self_out_traits = []
    while enodes:
        enode, enode_name = enodes.pop(0)
        if isinstance(enode, procbv.ProcessExecutionNode) \
                and (len(list(enode.children())) == 0 \
                    or not parse_subpipelines):
            if enode_name is None:
                enode_name = enode.name()
            nodename = make_node_name(enode_name, nodenames)
            proc = enode._process
            procid = proc.id()
            somaproc = soma_process_name(procid)
            moduleprocid = '%s.%s' % (procid, procid)
            out.write('        self.add_process(\'%s\', \'%s\')\n' \
                % (nodename, moduleprocid))
            procmap[use_weak_ref(proc)] = nodename
            links += parse_links(p, proc)
            #if parse_subpipelines:
                #enodes += [(enode.child(name), name) \
                    #for name in enode.childrenNames()]
        else:
            if isinstance(enode, procbv.SelectionExecutionNode):
                nodename, out_traits = write_switch(enode, out, nodenames,
                    links, p, processed_links, enode_name)
                self_out_traits += out_traits
                procmap[use_weak_ref(enode)] = nodename
            enodes += [(enode.child(name), name) \
                for name in enode.childrenNames()]
    out.write('\n')

    write_pipeline_links(p, out, procmap, links, processed_links,
        self_out_traits)

    # remove this when there is a more convenient method in Pipeline
    out.write('''
        for node_name, node in self.nodes.iteritems():
          for parameter_name, plug in node.plugs.iteritems():
            if parameter_name in ('nodes_activation', 'selection_changed'):
              continue
            if ((node_name, parameter_name) not in self.do_not_export and
                not plug.links_to and not plug.links_from):
              self.export_parameter(node_name, parameter_name,
                  '_'.join((node_name, parameter_name)))
''')


# ----

param_types_table = \
{
    neuroData.Boolean: traits.Bool,
    neuroData.String: traits.String,
    neuroData.Number: traits.Float,
    neuroData.Float: traits.Float,
    neuroData.Integer: traits.Int,
    ReadDiskItem: traits.File,
    WriteDiskItem: (traits.File, write_diskitem_options),
    neuroData.Choice: (traits.Enum, choice_options),
    neuroData.ListOf: traits.List,
    neuroData.Point3D: ('ListFloat', point3d_options),
}


parser = OptionParser('Convert an Axon process into a Soma-pipeline ' \
    'process.\nAlso works for pipeline structures.\n' \
    'Parameters links for completion are not preserved (yet), but ' \
    'inter-process links in pipelines are (normally) rebuilt.')
parser.add_option('-p', '--process', dest='process', action='append',
    help='input process ID. Ex: NobiasHistoAnalysis. Several -p options are ' \
    'allowed and should each correspond to a -o option.')
parser.add_option('-o', '--output', dest='output', metavar='FILE',
    action='append',
    help='output .py file for the converted process code')
parser.add_option('-r', '--recursive_sub', dest='parse_subpipelines',
    action='store_true', default=False,
    help='recursively parse sub-pipelines of a pipeline. This is mostly a ' \
    'debugging feature, since it is generally not needed because ' \
    'sub-pipelines are processes and can be converted and used directly. ' \
    'Moreover with this option, pipeline processes are not exported as ' \
    'themselves, but may contain parameters which will not be exported and ' \
    'may cause missing or broken links.')

options, args = parser.parse_args()
if len(args) != 0:
    parser.print_help()
    sys.exit(1)

processes.initializeProcesses()


for procid, outfile in zip(options.process, options.output):

    p = procbv.getProcessInstance(procid)
    print 'process:', p

    if p.executionNode():
        proctype = pipeline.Pipeline
    else:
        proctype = process.Process

    out = open(outfile, 'w')
    out.write('''# -*- coding: utf-8 -*-
try:
    from traits.api import File, Float, Int, Bool, Enum, String, List, \\
        ListFloat
except ImportError:
    from enthought.traits.api import File, Float, Int, Bool, Enum, String, \\
        List, ListFloat

from soma.process.process import Process
from soma.pipeline.pipeline import Pipeline

class ''')
    out.write(procid + '(%s):\n' % proctype.__name__)
    out.write('''    def __init__(self, **kwargs):
        super(%s, self).__init__(**kwargs)
        self.name_process = '%s\'\n''' % (procid, procid))

    if proctype is pipeline.Pipeline:
        write_pipeline_definition(p, out,
            parse_subpipelines=options.parse_subpipelines)
    else:
        write_process_definition(p, out)
