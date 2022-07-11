#!/usr/bin/env python

from __future__ import print_function
from __future__ import absolute_import
import os
from brainvisa.axon import processes
from brainvisa import processes as procbv
# from brainvisa.data import neuroData
# from brainvisa.data import neuroDiskItems
from brainvisa.data.readdiskitem import ReadDiskItem
from brainvisa.data.writediskitem import WriteDiskItem
# from traits import api as traits
from brainvisa.data import neuroHierarchy
import sys
from argparse import ArgumentParser
import yaml
import json
from six.moves import range
from collections import OrderedDict
from . import axon_to_capsul
import six


class AxonFsoToFom(object):

    '''
    Converter for Axon hierarchies (File System Ontologies) to CAPSUL/Soma-Base
    FOM (File Organization Model).

    Converts parameters for a given process according to rules taken from
    actual data: a main input data is used for Axon completion, then all
    parameters are analyzed and converted to FOM entries.
    '''

    def __init__(self, init_fom_def=OrderedDict(), formats_fom={}):
        '''
        Parameters
        ----------
        init_fom_def: dict or (preferably) collections.OrderedDict
            FOM to be completed. An existing one may be used, otherwise a new
            FOM dictionary is created.
        formats_fom: dict or collections.OrderedDict
            Formats and formats lists definitions to be used. They are expected
            to match Axon formats and formats lists definitions.
        '''
        self.current_fom_def = init_fom_def
        self.formats_fom = formats_fom

    def _find_rule(self, item):
        '''
        Find Axon FSO rule for a given distitem
        '''
        database_name = item.get('_database')
        if not database_name:
            print(item, 'not in any database.')
            return (None, {})
        name_in_db = item.name[len(database_name) + 1:]
        database = neuroHierarchy.databases.database(database_name)
        rules = database.fso.typeToPatterns.get(item.type, None)
        attribs = item.hierarchyAttributes()
        for rule in rules:
            m = rule.pattern.match(name_in_db, attribs)
            if m:
                return (rule, m)
        return (None, {})

    def _get_fom_formats(self, formats):
        '''
        Get FOM format definiton name in format FOM, adding it in format FOM
        it it is not found in it. Formats lists are handled.
        '''
        formats_lists = self.formats_fom.get('format_lists', {})
        fnames = set([f.name for f in formats])
        # special case of Directory format
        if len(fnames) >= 2 and 'Directory' in fnames:
            fnames.remove('Directory')
        for flist_name, flist in six.iteritems(formats_lists):
            if set(flist) == fnames:
                return flist_name
        all_formats = self.formats_fom.setdefault('formats', {})
        # complete global formats list
        for format in formats:
            if format.name == 'Directory' and format.name not in fnames:
                continue
            if format.name not in all_formats:
                all_formats[format.name] \
                    = self._extensions_from_format(format)[0]
        return list(fnames)

    def _extensions_from_format(self, format):
        '''
        File extensions for a given Axon Format
        '''
        exts = []
        for pattern in format.patterns.patterns:
            sp = pattern.pattern.split('|')
            if len(sp) != 2:
                print('malformed pattern for format:', format, ':', pattern)
                continue
            t, p = sp
            x = p.split('*.')
            if len(x) == 1:
                exts.append('')
            else:
                exts.append(x[-1])
        return exts

    def _translate_param_name(self, process, name):
        '''
        Translate a parameter name for a given process into the resulting one
        in Capsul pipeline.
        By default, just output the input name.
        '''
        return name

    def _transform_rule(self, rule, matched_attr, input_attr):
        '''
        Generates the FOM rule frol FSO rule and attributes

        Parameters
        ----------
        rule: FSO rule
        matched_attr: dict
            FSO attributes that made the rule match
        input_attr: dict
            input attributes and values

        Returns
        -------
        fom_pattern: string
        fom_added_attr: dict
            new attributes used in the rule, not in input_attr
        defaults: dict
            default attribute values used in the rule
        '''

        rule_attribs = dict([(k, '<%s>' % k) for k in matched_attr.keys()])
        non_transformed = ['filename_variable', ]
        # such attributes are not considered attributes: take their real value
        for k in non_transformed:
            value = matched_attr.get(k)
            if value is not None:
                rule_attribs[k] = value
        fom_pattern = rule.pattern.unmatch(rule_attribs, {})
        fom_added_attr = {}
        defaults = {}
        for k, value in six.iteritems(matched_attr):
            if k not in input_attr and k not in non_transformed:
                if k in rule.defaultAttributesValues:
                    defaults[k] = {'default_value':
                                   rule.defaultAttributesValues[k]}
                else:
                    fom_added_attr[k] = value
        return fom_pattern, fom_added_attr, defaults

    def fso_to_fom(self, proc_name, node_name, data):
        '''
        Transform a process or pipeline parameters into FOM rules. This is the
        main function in the class.

        Subprocesses of a pipeline will be added to the FOM too.

        Parameters
        ----------
        proc_name: string
            identifier of the Axon process
        node_name: string
            name to be used in the FOM
        data: string
            input data (file name) for the first input param opf the process.
            It will be used to perform Axon completion, then to get values
            and patterns for all parameters. Thus it must be a valid input
            data, existing in an Axon database.

        Returns
        -------
        new_fom_def: collections.OrderedDict
            new FOM definition (also found in self.current_fom_def)
        default_atts: dict
            attributes which have default values. Also adde in the FOM, in
            the "attribute_definitions" section.
        '''

        # print(proc_name, node_name, data)
        process = procbv.getProcessInstance(proc_name)
        signature = process.signature
        for name, param in six.iteritems(signature):
            if isinstance(param, ReadDiskItem):
                break
        else:
            raise ValueError('No ReadDiskItem in signature of process %s'
                             % proc_name)
        # print('process %s, set param: %s' % (proc_name, name))
        setattr(process, name, data)
        value = getattr(process, name)
        if value is None:
            raise ValueError(
                'The input value for param %s.%s could not be set (using: %s)'
                % (node_name, name, data))
        input_rule, input_attr = self._find_rule(value)
        self._done_params = set()
        self.current_fom_def, default_atts = self._fso_to_fom_parse(
            process, node_name, input_attr)
        node_names = {}
        self._process_nodes_fso_to_fom(process, node_name, default_atts,
                                       input_attr, node_names)
        del self._done_params
        return self.current_fom_def, default_atts

    def _fso_to_fom_parse(self, process, node_name, input_attr,
                          current_fom_def=None):
        '''
        Parse a single Axon process parameters and generate FOM rules for them.
        Parameters must all be already set.
        Doesn't handle children of a pipeline.
        '''

        if current_fom_def is None:
            current_fom_def = self.current_fom_def
        proc_fom = current_fom_def.setdefault(node_name, OrderedDict())
        signature = process.signature
        default_atts = OrderedDict()

        for name, param in six.iteritems(signature):
            if not isinstance(param, ReadDiskItem):
                # skip this param
                continue
            param_name = self._translate_param_name(process, name)
            value = getattr(process, name)
            # print('    %s.%s: %s' % (node_name, name, value))
            if value is None:
                continue
            if self._check_and_mark_done(process, name):
                # print('already done:', process, name)
                continue
            database_name = value.get('_database')
            rule, matched_attr = self._find_rule(value)
            if rule is None:
                continue
            database = neuroHierarchy.databases.database(database_name)
            if database.fso.name == 'shared':
                fom_type = 'shared'
            elif self._is_output(process, name, param):
                fom_type = 'output'
            else:
                fom_type = 'input'
            fom_rule, fom_added_attr, added_defaults \
                = self._transform_rule(rule, matched_attr, input_attr)
            default_atts.update(added_defaults)
            fom_format = self._get_fom_formats(param.formats)
            fom_pattern = [['%s:%s' % (fom_type, fom_rule), fom_format]]
            if fom_added_attr:
                fom_pattern[0].append(fom_added_attr)
            proc_fom[param_name] = fom_pattern

        if len(proc_fom) == 0:
            del current_fom_def[node_name]

        return current_fom_def, default_atts

    def _is_output(self, process, param_name, param):
        '''
        Checks if a given Axon process parameter is an output.
        '''
        if isinstance(param, WriteDiskItem):
            return True
        # check if this input is connected to an upstream output
        linkdefs = process._links.get(param_name)
        if linkdefs is not None:
            for linkdef in linkdefs:
                other_proc, other_param_name = linkdef[:2]
                if other_proc is None \
                        or other_proc == axon_to_capsul.use_weak_ref(process):
                    # internal link, doesn't count
                    continue
                other_param = other_proc.signature[other_param_name]
                if isinstance(other_param, WriteDiskItem) \
                        and getattr(process, param_name) \
                        == getattr(other_proc, other_param_name):
                    return True
        return False

    def _check_and_mark_done(self, process, param_name):
        '''
        Set param_name parameter of process process into processed list. Links
        are followed recursively to avoid having another parameter duplicating
        the current one.

        Returns
        -------
        True if the parameter was already in the done list, False otherwise
        '''
        proc_ref = axon_to_capsul.use_weak_ref(process)
        if (proc_ref, param_name) in self._done_params:
            return True
        stack = [(proc_ref, param_name)]
        value = getattr(process, param_name)
        while stack:
            cprocess, cparam_name = stack.pop(0)
            self._done_params.add((cprocess, cparam_name))
            # propagate through links
            links = cprocess()._links.get(cparam_name, [])
            for link in links:
                other_end = (axon_to_capsul.use_weak_ref(link[0]), link[1])
                if other_end[0] is not None \
                        and getattr(other_end[0](), link[1]) == value \
                        and other_end not in self._done_params:
                    stack.append(other_end)
        return False

    def _process_nodes_fso_to_fom(self, process, node_name, default_atts,
                                  input_attr, node_names):
        '''
        Walks a pipeline tree structure and adds all its children to the FOM
        '''

        if not hasattr(process, 'executionNode') \
                or process.executionNode() is None:
            return  # not a pipeline

        a_to_c = axon_to_capsul.AxonToCapsul()

        nodes = [(process.executionNode(), node_name, self.current_fom_def)]
        while nodes:
            node, current_node_name, current_fom_def = nodes.pop(0)
            if isinstance(node, procbv.ProcessExecutionNode):
                new_def, added_default_atts = self._fso_to_fom_parse(
                    node._process, current_node_name, input_attr,
                    current_fom_def)
                default_atts.update(added_default_atts)
            else:
                for child_name in node.childrenNames():
                    child = node.child(child_name)
                    if isinstance(child, procbv.ProcessExecutionNode):
                        new_node_name = a_to_c.make_node_name(
                            '.'.join([current_node_name, child_name]),
                            node_names,
                            None)
                    else:
                        new_node_name = current_node_name
                    nodes.append((child, new_node_name, current_fom_def))


def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    '''
    http://stackoverflow.com/questions/5121931/in-python-how-can-you-load-yaml-mappings-as-ordereddicts
    '''
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)

# usage example:
# ordered_load(stream, yaml.SafeLoader)


def ordered_dump(data, stream=None, Dumper=yaml.Dumper, **kwds):
    '''
    http://stackoverflow.com/questions/5121931/in-python-how-can-you-load-yaml-mappings-as-ordereddicts
    '''
    class OrderedDumper(Dumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            list(data.items()))
    OrderedDumper.add_representer(OrderedDict, _dict_representer)
    return yaml.dump(data, stream, OrderedDumper, **kwds)

# usage:
# ordered_dump(data, Dumper=yaml.SafeDumper)


def fso_to_fom_main(argv):
    '''
    Main FSO hierarchy to FOM conversion for one or several processes.
    Contains an argument parser for the __main__ function.
    '''

    basedir = os.path.dirname(__file__)
    for i in range(3):
        basedir = os.path.dirname(basedir)
    foms_dir = os.path.join(basedir, 'share', 'foms')
    def_formats_fom = os.path.join(foms_dir, 'brainvisa-formats-3.2.0.json')

    parser = ArgumentParser(
        description='Convert an Axon FSO hierarchy into FOM entries, for '
        'given Axon processes.')
    parser.add_argument('-p', '--process', dest='process', action='append',
                        help='input process ID. Ex: NobiasHistoAnalysis. Several -p options '
                        'are allowed. Processes may be specified as id,name (no space) to '
                        'force a new name')
    parser.add_argument('-o', '--output', dest='output',
                        help='output FOM rules files')
    parser.add_argument('-a', '--append', action='store_true',
                        help='append output to the end of an existing FOM file')
    parser.add_argument('-d', '--data', dest='data',
                        help='input data file for process 1st arg (ex: '
                        '/home/bob/bvdata/center/subject01/t1mri/default_acquisition/subject01.nii')
    parser.add_argument('-f', '--formats', dest='formats',
                        help='formats FOM file [default: %s]' % def_formats_fom)
    parser.add_argument('-n', '--name', dest='fom_name',
                        help='set this FOM name [default: output file name]')
    parser.add_argument('-F', '--Formats', dest='output_formats',
                        help='output file name for updated formats FOM')
    args = parser.parse_args(argv)

    # from brainvisa.configuration import neuroConfig
    # neuroConfig.ignoreValidation = True
    processes.initializeProcesses()

    append = args.append
    fom_def = OrderedDict()
    if args.append:
        fom_def = ordered_load(open(args.output))

    if args.formats:
        formats = args.formats
    else:
        formats = None
        fom_imports = fom_def.get('fom_import')
        if fom_imports:
            formats_list = [x for x in fom_imports if x.find('formats') >= 0]
            if len(formats_list) >= 1:
                formats = os.path.join(foms_dir, formats_list[0] + '.json')
    if not formats:
        formats = def_formats_fom
    if formats:
        print('using formats FOM:', formats)
        formats_fom = ordered_load(open(formats))
    else:
        print('NO formats FOM !')
        # raise RuntimeError('No formats FOM')
        formats_fom = {}

    fom_name = args.fom_name
    if 'fom_name' not in fom_def or fom_name is not None:
        if fom_name is None:
            fom_name = os.path.basename(args.output)
            p = fom_name.rfind('.')
            if p >= 0:
                fom_name = fom_name[: p]
        fom_def['fom_name'] = fom_name

    fom_imports = fom_def.setdefault('fom_import', [])
    if formats_fom:
        formats_bname = os.path.basename(formats)
        formats_bname = formats_bname[: formats_bname.rfind('.')]
        if formats_bname not in fom_imports:
            fom_imports.append(formats_bname)
    if 'shared-brainvisa-1.0' not in fom_imports:
        fom_imports.append('shared-brainvisa-1.0')

    default_atts = fom_def.setdefault("attribute_definitions", OrderedDict())
    current_fom_def = fom_def.setdefault('processes', OrderedDict())

    fso_to_fom = AxonFsoToFom(current_fom_def, formats_fom)

    for proc_spec in args.process:
        proc_spec_list = proc_spec.split(',')
        proc_name = proc_spec_list[0]
        node_name = proc_spec_list[-1]
        new_def, added_default_atts = fso_to_fom.fso_to_fom(
            proc_name, node_name, args.data)
        default_atts.update(added_default_atts)

    # ordered_dump(fom_def, open(args.output, 'w'))
    json.dump(fom_def, open(args.output, 'w'), indent=4)
    if args.output_formats:
        json.dump(fso_to_fom.formats_fom, open(args.output_formats, 'w'),
                  indent=4)


if __name__ == '__main__':
    fso_to_fom_main(sys.argv[1:])
