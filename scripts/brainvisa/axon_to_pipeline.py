#!/usr/bin/env python

from brainvisa.axon import processes
from soma.pipeline import process, pipeline
from brainvisa import processes as procbv
from brainvisa.data import neuroData
from brainvisa.data.readdiskitem import ReadDiskItem
from brainvisa.data.writediskitem import WriteDiskItem
from traits import api as traits
import weakref

from optparse import OptionParser


def write_diskitem_options( wdiskitem ):
    return [ 'output=True' ]


def choice_options( choice ):
    return [ repr(x[0]) for x in choice.values ]


def point3d_options( point ):
    return [ 'minlen=3', 'maxlen=3' ]


def write_process_signature( p, out ):
    # write signature
    for name, param in p.signature.iteritems():
        newtype = param_types_table.get( type( param ) )
        paramoptions = []
        if newtype is None:
            print 'type', type( param ), 'not found'
            newtype = traits.String
        if isinstance( newtype, tuple ):
            paramoptions = newtype[1]( param )
            newtype = newtype[0]
        if not param.mandatory:
            paramoptions.append( 'optional=True' )
        if hasattr( newtype, '__name__' ):
            # take name of a type class
            newtype = newtype.__name__
        out.write( '        self.add_trait(\'%s\', %s(%s))\n' \
            % ( name, newtype, ', '.join( paramoptions ) ) )
    out.write( '\n\n' )


def write_process_execution( p, out ):
    out.write( '''    def __call__(self):
        from brainvisa import axon
        from brainvisa.configuration import neuroConfig
        import brainvisa.processes

        neuroConfig.gui = False
        neuroConfig.fastStart = True
        neuroConfig.logFileName = ''

        axon.initializeProcesses()

        kwargs = {name : getattr(self,name) for name in self.user_traits()}

        context = brainvisa.processes.defaultContext()
        context.runProcess( self.name_process, **kwargs )
''' )


def write_process_definition( p, out ):
      write_process_signature( p, out )
      write_process_execution( p, out )


def str_to_name( s ):
    s = s.replace( ' ', '_' )
    s = s.replace( '(', '_' )
    s = s.replace( ')', '_' )
    s = s.replace( '\'', '_' )
    s = s.replace( '"', '_' )
    s = s.replace( ',', '_' )
    return s


def soma_process_name( procid ):
    return procid # TODO

def use_weak_ref( obj ):
    if obj is None:
        return None
    if type( obj ) is weakref.ProxyType:
        return obj.__weakref__
    if type( obj ) is weakref.ReferenceType:
        return obj
    return weakref.ref( obj )


def parse_links( pipeline, proc ):
    links = []
    proc = use_weak_ref( proc )
    for param, linkdefs in proc()._links.iteritems():
        for dstproc, dstparam, mlink, unknown in linkdefs:
            dstproc = use_weak_ref( dstproc )
            # check if link is compatible
            if dstproc is None or dstparam is None or dstproc is proc:
                # intra-process links are dropped.
                continue
            srcsign = proc().signature[ param ]
            dstsign = dstproc().signature[ dstparam ]
            if type( srcsign ) is not type( dstsign ) \
                    and ( not isinstance( srcsign, ReadDiskItem ) \
                        or not isinstance( dstsign, ReadDiskItem ) ):
                # incompatible parameters types
                continue
            if isinstance( srcsign, ReadDiskItem ):
                if srcsign.type.isA( dstsign.type.name ) \
                        or dstsign.type.isA( srcsign.type.name ):
                    # compatible type
                    if isinstance( dstsign, WriteDiskItem ) \
                            or ( not isinstance( srcsign, WriteDiskItem ) \
                                and dstproc is use_weak_ref( pipeline ) ):
                        # swap input/output
                        links.append( ( dstproc, dstparam, proc, param ) )
                    else:
                        links.append( ( proc, param, dstproc, dstparam ) )
            else:
                # not DiskItems
                links.append( ( proc, param, dstproc, dstparam ) )
    return links


def is_output( proc, param ):
    signp = proc().signature.get( param )
    return isinstance( signp, WriteDiskItem )


def converted_link( linkdef, links, pipeline, selfinparams, revinparams,
        selfoutparams, revoutparams ):
    pipeline = use_weak_ref( pipeline )
    if linkdef[2] is pipeline and linkdef[3] in selfinparams:
        # output in pipeline inputs: invert link
        linkdef = ( linkdef[2], linkdef[3], linkdef[0], linkdef[1] )
    if linkdef in links:
        return None
    if linkdef[0] is pipeline and linkdef[1] in selfoutparams:
        # source in pipeline outputs: either needs translation, or inversion
        if is_output( linkdef[2], linkdef[3] ):
            # dest is an output: needs inversion
            linkdef = ( linkdef[2], linkdef[3], linkdef[0], linkdef[1] )
        else:
            altp = selfoutparams.get( linkdef[1] )
            if altp is None:
                print '** warning, probably bad link:', linkdef[0]().name, \
                    ',', linkdef[1], ' ->', linkdef[2]().name, ',', linkdef[3]
                print revoutparams
                return None
            linkdef = ( altp[0], altp[1], linkdef[2], linkdef[3] )
    if linkdef in links:
        return None
    if linkdef[0] is not pipeline \
            and ( linkdef[0], linkdef[1] ) in revinparams:
        # source has an equivalent in exported inputs
        altp = revinparams[ ( linkdef[0], linkdef[1] ) ]
        linkdef = ( pipeline, altp, linkdef[2], linkdef[3] )
    if linkdef[2] is not pipeline \
            and ( linkdef[2], linkdef[3] ) in revoutparams:
        # dest has an equivalent in exported outputs
        altp = revoutparams[ ( linkdef[2], linkdef[3] ) ]
        linkdef = ( linkdef[0], linkdef[1], pipeline, altp )
    if linkdef in links:
        return None
    if linkdef[2] is not pipeline \
            and ( linkdef[2], linkdef[3] ) in revinparams:
        # dest has an equivalent in exported inputs
        altp = revinparams[ ( linkdef[2], linkdef[3] ) ]
        linkdef = ( pipeline, altp, linkdef[0], linkdef[1] )
    if linkdef in links:
        return None
    return linkdef


def export_output( out, src, sname, sparam, p, dparam, selfoutparams, 
        revoutparams, processedlinks ):
    # global output param in pipeline signature
    out.write( '        # export output parameter\n' )
    out.write(
        '        self.export_parameter(\'%s\', \'%s\', \'%s\')\n' \
        % ( sname, sparam, dparam ) )
    selfoutparams[ dparam ] = ( src, sparam )
    revoutparams[ ( src, sparam ) ] = dparam
    processedlinks.add( ( src, sparam, use_weak_ref( p ), dparam ) )
    processedlinks.add( ( use_weak_ref( p ), dparam, src, sparam ) )


def export_input( out, dst, dname, dparam, p, sparam, selfinparams, 
        revinparams, processedlinks ):
    # global input param in pipeline signature
    out.write( '        # export input parameter\n' )
    out.write(
        '        self.export_parameter(\'%s\', \'%s\', \'%s\')\n' \
        % ( dname, dparam, sparam ) )
    selfinparams[ sparam ] = ( dst, dparam )
    revinparams[ ( dst, dparam ) ] = sparam
    processedlinks.add( ( use_weak_ref( p ), sparam, dst, dparam ) )
    processedlinks.add( ( dst, dparam, use_weak_ref( p ), sparam ) )


def make_node_name( name, nodenames ):
    if name in nodenames:
        nodenames[ name ] += 1
        return '%s_%d' % ( name, nodenames[ name ] )
    else:
        nodenames[ name ] = 0
        return name


def write_pipeline_links( p, out, procmap, links ):
    # parse and set pipeline links
    selfinparams = {}
    revinparams = {}
    selfoutparams = {}
    revoutparams = {}
    processedlinks = set()
    for link in links:
        link = converted_link( link, processedlinks, p, selfinparams, 
            revinparams, selfoutparams, revoutparams )
        if link is None:
            continue
        src, sparam, dst, dparam = link
        sname = procmap.get( src, None )
        if sname is None:
            print 'warning, src process', src().name, 'not found in pipeline.'
            print 'procmap:', [ k().name for k in procmap ]
            continue # skip this one
        dname = procmap.get( dst, None )
        if dname is None:
            print 'warning, dst process', dst().name, 'not found in pipeline.'
            continue # skip this one
        spname = sparam
        if sname:
            spname = '%s.%s' % ( sname, sparam )
        dpname = dparam
        if dname:
            dpname = '%s.%s' % ( dname, dparam )
        if sname == '' and sparam not in selfinparams:
            export_input( out, dst, dname, dparam, p, sparam, selfinparams, 
                revinparams, processedlinks )
        elif dname == '' and dparam not in selfoutparams:
            export_output( out, src, sname, sparam, p, dparam, selfoutparams, 
                revoutparams, processedlinks )
        else:
          if dname == '' and dparam in selfinparams:
              # swap input/output
              tmp = spname
              spname = dpname
              dpname = tmp
          if sname == '' and sparam in selfoutparams:
              spname = selfoutparams[ sparam ][1]
          if dname != '' and ( dst, dpname ) in revoutparams:
              dpname = revoutparams[ ( dst, dpname ) ]
          if spname == dpname:
              continue
          # check for non-exported links with same IO status
          if sname != '' and dname != '' \
                  and is_output( src, sparam ) == is_output( dst, dparam ):
              if is_output( src, sparam ):
                  # both outputs: export 1st
                  sparam2 = sname + '_' + sparam
                  if sparam2 in selfoutparams or sparam2 in selfinparams:
                      # avoid duplicate name
                      sparam2 = sparam2 + '2'
                  export_output( out, src, sname, sparam, p, sparam2, 
                      selfoutparams, revoutparams, processedlinks )
                  # and link 2nd to this exported output (and switch link)
                  src = dst
                  sparam = dparam
                  spname = dpname
                  dst = use_weak_ref( p )
                  dparam = srcparam2
                  dpname = srcparam2
              else:
                  # both inputs: export 1st
                  sparam2 = sname + '_' + sparam
                  if sparam2 in selfinparams or sparam2 in selfoutparams:
                      # duplicate name
                      sparam2 = sparam + '2'
                  export_input( out, src, sname, sparam, p, sparam2, 
                      selfinparams, revinparams, processedlinks )
                  # and link 2nd to this exported input
                  sparam = sparam2
                  spname = sparam2
                  print '   ', src().name, sparam, '->', dst().name, dparam
          out.write(
              '        self.add_link(\'%s->%s\')\n' % ( spname, dpname ) )
        processedlinks.add( ( src, sparam, dst, dparam ) )
        processedlinks.add( ( dst, dparam, src, sparam ) )


def write_pipeline_definition( p, out ):
    out.write( '\n\n' )
    out.write( '    def pipeline_definition(self):\n' )
    enodes = [ ( p.executionNode(), None ) ]
    links = parse_links( p, p )
    procmap = { weakref.ref(p) : '' }
    nodenames = {}
    while enodes:
      enode, enode_name = enodes.pop( 0 )
      if isinstance( enode, procbv.ProcessExecutionNode ):
          if enode_name is None:
              enode_name = enode.name()
          nodename = make_node_name( enode_name, nodenames )
          proc = enode._process
          procid = proc.id()
          somaproc = soma_process_name( procid )
          moduleprocid = '%s.%s' % ( procid, procid )
          out.write( '        self.add_process( \'%s\', \'%s\' )\n' \
              % ( str_to_name( nodename ), moduleprocid ) )
          procmap[ use_weak_ref( proc ) ] = str_to_name( nodename )
          links += parse_links( p, proc )
      else:
          if isinstance( enode, procbv.SelectionExecutionNode ):
              if enode_name is None:
                  enode_name = 'switch'
              nodename = make_node_name( enode_name, nodenames )
              out.write( '        # warning, the switch output trait should be renamed to a more comprehensive name\n' )
              out.write( '        # moreover, input items should be connected to adequate output items in each subprocess in the switch.\n')
              out.write( '        self.add_trait(\'switch_out\', File())\n' )
              out.write( '        self.add_switch(\'%s\', %s, \'%s\')\n' \
                  % ( nodename, repr( enode.childrenNames() ), 'switch_out' ) )
              out.write( 
                  '        self.add_link(\'%s.switch_out->switch_out\')\n' \
                      % nodename )
          enodes += [ ( enode.child( name ), name ) \
              for name in enode.childrenNames() ]
    out.write( '\n' )

    write_pipeline_links( p, out, procmap, links )


# ----

param_types_table = \
{
    neuroData.Boolean : traits.Bool,
    neuroData.String : traits.String,
    neuroData.Number : traits.Float,
    neuroData.Float : traits.Float,
    neuroData.Integer : traits.Int,
    ReadDiskItem : traits.File,
    WriteDiskItem : ( traits.File, write_diskitem_options ),
    neuroData.Choice : ( traits.Enum, choice_options ),
    neuroData.ListOf : traits.List,
    neuroData.Point3D : ( 'ListFloat', point3d_options ),
}


parser = OptionParser( 'Convert an Axon process into a Soma-pipeline ' \
    'process.\nAlso works for pipeline structures.\n' \
    'Parameters links are not preserved (yet).' )
parser.add_option( '-p', '--process', dest='process', action='append',
    help='input process ID. Ex: NobiasHistoAnalysis. Several -p options are ' \
    'allowed and should each correspond to a -o option.' )
parser.add_option( '-o', '--output', dest='output', metavar='FILE', 
    action='append',
    help='output .py file for the converted process code' )

options, args = parser.parse_args()
if len( args ) != 0:
    parser.print_help()
    sys.exit(1)

processes.initializeProcesses()


for procid, outfile in zip( options.process, options.output ):

    p = procbv.getProcessInstance( procid )
    print 'process:', p

    if p.executionNode():
        proctype = pipeline.Pipeline
    else:
        proctype = process.Process

    out = open( outfile, 'w' )
    out.write( '''# -*- coding: utf-8 -*-
try:
    from traits.api import File, Float, Int, Bool, Enum, String, List, \\
        ListFloat
except ImportError:
    from enthought.traits.api import File, Float, Int, Bool, Enum, String, \\
        List, ListFloat

from soma.pipeline.process import Process
from soma.pipeline.pipeline import Pipeline

class ''' )
    out.write( procid + '(%s):\n' % proctype.__name__ )
    out.write( '''    def __init__(self, **kwargs):
        super(%s, self).__init__(**kwargs)
        self.name_process = '%s\'\n''' % ( procid, procid ) )


    if proctype is pipeline.Pipeline:
        write_pipeline_definition( p, out )
    else:
        write_process_definition( p, out )
