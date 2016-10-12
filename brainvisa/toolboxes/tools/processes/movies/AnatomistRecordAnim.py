#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
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

from brainvisa.processes import *
import math
from brainvisa import quaternion
import copy
from brainvisa import anatomist

name = 'Anatomist record animation'
userLevel = 1

def validation():
    anatomist.validation()

signature = Signature(
    'output_anim', WriteDiskItem( 'BrainVISA/Anatomist animation',
                                  'BrainVISA/Anatomist animation' ),
    'window', anatomist.AWindowChoice(),
    )

def initialization( self ):
    self.setOptional( 'output_anim' )

def execution( self, context ):
    selfdestroy = []
    a = anatomist.Anatomist()
    #a.eventFilter( default_filtering = 0 )
    win = self.window()

    context.write( _t_( 'Now setup the window (add objects in the window and ' \
                      'set its starting point of view)' ) )

    group = win.group

    positions = []
    steps = 100
    
    while 1:
        #r = context.ask( 'Set next point of view', 'OK', 'Stop' )
        # dialog box
        dial = context.dialog( 1, 'Set next point of view',
                               Signature( 'steps', Number() ),
                               _t_( 'OK' ), _t_( 'Stop' ) )
        dial.setValue( 'steps', steps )
        r = dial.call()
        if r != 0:
            break
        steps = dial.getValue( 'steps' )
        info = win.getInfos()
        quat = info[ 'view_quaternion' ]
        pos = info[ 'observer_position' ]
        cpos = info[ 'position' ]
        zoom = info[ 'zoom' ]
        slicequat = info[ 'slice_quaternion' ]
        a.importObjects()
        objects = win.objects
        objectsInfos={}
        for o in objects:
          infos=o.getInfos()
          sel=infos.get( 'selected_in_groups' )
          if sel and group in sel:
            infos['selected'] = 1
          objectsInfos[o.name] = infos
        positions.append( { 'view_quaternion' : quat,
                            'observer_position' : pos,
                            'cursor_position' : cpos,
                            'zoom' : zoom,
                            'slice_quaternion' : slicequat,
                            'steps' : steps,
                            'objects' : objectsInfos } )
        if len( positions ) >= 2:
            v0 = quat0
            v1 = quat
            s0 = slicequat0
            s1 = slicequat
            incr = 1. / ( steps - 1 )
            for i in xrange( steps ):
                win.camera(
                    zoom = zoom0*(1-incr*i) + zoom*incr*i, 
                    view_quaternion = \
                    quaternion.Quaternion( (
                    v0[0]*(1-incr*i) + v1[0]*incr*i,
                    v0[1]*(1-incr*i) + v1[1]*incr*i,
                    v0[2]*(1-incr*i) + v1[2]*incr*i,
                    v0[3]*(1-incr*i) + v1[3]*incr*i )
                                           ).normalized().vector(), 
                    observer_position = (
                    pos0[0]*(1-incr*i) + pos[0]*incr*i,
                    pos0[1]*(1-incr*i) + pos[1]*incr*i,
                    pos0[2]*(1-incr*i) + pos[2]*incr*i ), 
                    cursor_position = (
                    cpos0[0]*(1-incr*i) + cpos[0]*incr*i,
                    cpos0[1]*(1-incr*i) + cpos[1]*incr*i,
                    cpos0[2]*(1-incr*i) + cpos[2]*incr*i ), 
                    slice_quaternion = \
                    quaternion.Quaternion( (
                    s0[0]*(1-incr*i) + s1[0]*incr*i, 
                    s0[1]*(1-incr*i) + s1[1]*incr*i, 
                    s0[2]*(1-incr*i) + s1[2]*incr*i, 
                    s0[3]*(1-incr*i) + s1[3]*incr*i
                    ) ).normalized().vector(), 
                    )
        quat0 = copy.copy( quat )
        pos0 = copy.copy( pos )
        cpos0 = copy.copy( cpos )
        zoom0 = zoom
        slicequat0 = copy.copy( slicequat )
        objects0 = copy.copy( objectsInfos )

    # context.write( self.output_anim )
    if self.output_anim is not None:
        f = open( self.output_anim.fullPath(), 'w' )
        f.write( 'brainvisaAnim = ' )
        f.write( repr( positions ) )
        f.close()
    return selfdestroy
