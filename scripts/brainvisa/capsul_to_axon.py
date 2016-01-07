#!/usr/bin/env python

from brainvisa.axon import processes
from capsul import process, pipeline
from brainvisa import processes as procbv
from brainvisa.data import neuroData
from brainvisa.data.readdiskitem import ReadDiskItem
from brainvisa.data.writediskitem import WriteDiskItem
from traits import api as traits
from traits import trait_types
import importlib

from optparse import OptionParser


def fileOptions(filep):
    if hasattr(filep, 'output') and filep.output:
        return (WriteDiskItem, ['\'Any Type\'', 'getAllFormats()'])
    return (ReadDiskItem, ['\'Any Type\'', 'getAllFormats()'])


def choiceOptions(choice):
    return [repr(x) for x in choice.trait_type.values]


def listOptions(listp):
    item_type = listp.inner_traits[0]
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
    return '%s(%s)' % (newtype.__name__, ', '.join(paramoptions))


parser = OptionParser(
    'Convert a Capsul process into an Axon '
    'process.\nDoesn\'t work yet for pipelines.\nParameters links are not '
    'preserved (yet).')
parser.add_option(
    '-p', '--process', dest='process', action='append',
    help='input process ID, module+class. '
    'Ex: morphologist.process.morphologist.Morphologist. '
    'Several -p options are allowed and should each correspond to a '
    '-o option.')
parser.add_option('-o', '--output', dest='output', metavar='FILE',
                  action='append',
                  help='output .py file for the converted process code')

options, args = parser.parse_args()
if len(args) != 0:
    parser.print_help()
    sys.exit(1)


for procid, outfile in zip(options.process, options.output):

    modname = procid[: procid.rfind('.')]
    procname = procid[procid.rfind('.') + 1:]
    module = importlib.import_module(modname)

    p = getattr(module, procname)()
    print 'process:', p

    out = open(outfile, 'w')
    out.write( '''# -*- coding: utf-8 -*-

from brainvisa.processes import *

name = '%s'

signature = Signature(
''' % procname )

    excluded_traits = set(('nodes_activation', 'pipeline_steps'))
    for name, param in p.user_traits().iteritems():
        if name in excluded_traits:
            continue
        parameter = make_parameter(param, name)
        out.write('    \'%s\', %s,\n' % (name, parameter))

    out.write( ''')

def initialization(self):
''')
    init_empty = True
    for name in p.user_traits():
        if name in excluded_traits:
            continue
        value = getattr(p, name)
        if value not in (traits.Undefined, ''):
            out.write('    self.%s = %s\n' % (name, repr(value)))
            init_empty = False
    if init_empty:
        out.write('    pass\n')
    out.write('''
def execution(self, context):
    import %s
    proc = %s()
    for name in self.signature.keys():
        value = getattr(self, name)
        if isinstance(value, DiskItem):
            value = value.fullPath()
        setattr(proc, name, value)
    proc()
''' % ( modname, procid ) )
