# Copyright CEA and IFR 49 (2000-2005)
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

import glob
from neuroProcesses import *
import shfjGlobals
import math, time, shutil
from brainvisa import quaternion
from brainvisa import mpegConfig
from brainvisa import anatomist

name = 'Anatomist View Animation'
userLevel = 1


signature = Signature(
    'anim', ReadDiskItem( 'BrainVISA/Anatomist animation',
                          'BrainVISA/Anatomist animation' ),
    'window', anatomist.AWindowChoice(),
    'use_recorded_objects', Boolean(), 
    'keep_images', Boolean(),
    'images_basename', WriteDiskItem( '2D Image',
                                      shfjGlobals.aimsImageFormats ),
    'animation', WriteDiskItem( 'MPEG film', mpegConfig.mpegFormats ),
    )

def validation():
    anatomist.validation()

def initialization( self ):
    self.keep_images = 0
    self.setOptional( 'animation' )
    self.setOptional( 'images_basename' )

    if len( mpegConfig.findEncoders() ) != 0:
        eNode = SerialExecutionNode( self.name, parameterized=self )
        eNode.addChild( 'mpegEncode',
                        ProcessExecutionNode( 'mpegEncode', selected = True,
                                              optional=True ) )
        eNode.mpegEncode.signature[ 'images' ].userLevel = 3
        eNode.addLink( 'mpegEncode.animation', 'animation' )
        eNode.addLink( 'animation', 'mpegEncode.animation' )
        self.setExecutionNode( eNode )


def preloadfiles( self, anim ):
    """Preload all files needed for the animation and return a dictionary with
    ID in .banim file as KEY and object file as value"""
    a = anatomist.Anatomist()
    preloadedfiles = {}
    for iter in anim: # for each step of the animation
        objectsDict = iter.get( "objects" )
        for objID, obj in objectsDict.items():
            if objID not in preloadedfiles.keys():
                tmpfilename = obj.get( "filename" )
                if tmpfilename:
                    preloadedfiles[ objID ] = a.loadObject( tmpfilename )
    return preloadedfiles


def execution( self, context ):
    selfdestroy = []
    try:
        f = open( self.anim.fullPath(), 'r' )
        exec( f.read() )
        anim = brainvisaAnim
        f.close()
    except:
        raise IOError( self.anim.fullPath() \
                       + _t_( ' is not a brainvisa/Antomist animation file' ) )

    a = anatomist.Anatomist()
    win = self.window()

    context.ask( _t_( 'Now setup the window (add objects in the window)' ),
                 _t_( 'OK' ) )

    group = win.group
    
    if not group:
        group = 0

    if self.animation is not None:
        # force window size to multiples of 16
        info=win.getInfos()
        geom = info[ 'view_size' ]
        if geom is not None and \
           ( int(geom[0]/16)*16 != geom[0] or int(geom[1]/16)*16 != geom[1] ):
            w = int(geom[0]/16+1)*16
            h = int(geom[1]/16+1)*16
            #dw = w - geom[0]
            #dh = h - geom[1]
            #g = info[ 'geometry' ]
            #g[2] += dw
            #g[3] += dh
            a.execute("WindowConfig", windows=[win], view_size = [ w, h ])
            # check again
            time.sleep(1)	# let anatomist time to finish resize
            info = win.getInfos()
            geom = info[ 'view_size' ]
            if geom[0] != w or geom[1] != h:
                context.write( 'warning: Anatomist refuses to resize its ' \
                               'window as requested (Qt-3?) - using trick...' )
                context.write( 'target size: ', [w, h] )
                context.write( 'current size: ', geom )
                w1 = w*2 - geom[0]
                h1 = h*2 - geom[1]
                context.write( 'asked size: ', [w1, h1] )
                a.execute("WindowConfig", windows=[win],
                  view_size = [ w1, h1 ])
                # last checking...
                time.sleep(1)	# let anatomist time to finish resize
                info = win.getInfos()
                geom = info[ 'view_size' ]
                if geom[0] != w or geom[1] != h:
                    context.write( 'Sorry, Anatomist windows are too ' \
                                   'undisciplined, I can\'t correctly ' \
                                   'set their size' )
                    context.write( 'current size: ', geom )
                    return

    # temp directory to store images
    tmpdir = context.temporary( 'Directory' )
    tmp = tmpdir.fullPath()
    if self.images_basename is None:
        self.keep_images = 0
        context.write( '<font color="#e00000"> <i><b>' + _t_( 'Warning' )
                       + ':</b></i> '
                       + _t_( 'images_basename field is not filled: I won\'t '
                            'keep generated images' ) + '</font>' )
    if self.keep_images == 0:
        imgbase = os.path.join( tmp, 'anim.jpg' )
    else:
        imgbase = os.path.join( tmp, self.images_basename.fileName() )

    objects = []
    translationtable = {}
    n = len( anim )


    preloadedFiles = self.preloadfiles( anim )

    # Loop over scenes
    for j in xrange( n - 1 ):
        x0 = anim[j]
        x1 = anim[j+1]
        obj0 = x0.get( 'objects' )
        obj1 = x1.get( 'objects' )
        v0 = x0[ 'view_quaternion' ]
        v1 = x1[ 'view_quaternion' ]
        pos0 = x0[ 'observer_position' ]
        pos = x1[ 'observer_position' ]
        cpos0 = x0.get( 'cursor_position' )
        cpos = x1.get( 'cursor_position' )
        zoom0 = x0[ 'zoom' ]
        zoom = x1[ 'zoom' ]
        s0 = x0[ 'slice_quaternion' ]
        s1 = x1[ 'slice_quaternion' ]
        steps = x1[ 'steps' ]
        incr = 1. / steps
        params = {}

        # manage objects
        if self.use_recorded_objects and obj1:
            # Find files that are to add/remove/select/deselect to the window
            # (check the differences between the new image and the previous
            # one)
            toadd = []
            for o in obj1:
                if not o in objects and o in preloadedFiles:
                    toadd.append( preloadedFiles[ o ] )
                    objects.append( o )
                    mat1 = obj1[ o ].get( "material" )
                    if mat1:
                        preloadedFiles[ o ].setMaterial( a.Material(**mat1),
                          refresh = False  )

            toremove = []
            for o in objects:
                if o not in obj1:
                    toremove.append( preloadedFiles[ o ] )
                    objects.remove( o )

            tosel = []
            tounsel = []
            for o in obj1:
                if o in preloadedFiles:
                    if o in obj0:
                        sel0 = obj0[ o ].get( "selected", 0 )
                    sel1 = obj1[ o ].get( "selected", 0 )
                    # Check if the selected state has changed
                    if sel0 != sel1 and sel1:
                        # The object has been selected
                        tosel.append( preloadedFiles[ o ] )
                    else:
                        # else it has been deselected
                        tounsel.append( preloadedFiles[ o ] )

            if toremove:
                win.removeObjects( toremove )
            if toadd:
                win.addObjects( toadd )
            if tosel:
                group.addToSelection(tosel)
            if tounsel:
                group.unSelect(tounsel)

        # play anim
        for i in xrange( steps ):
            if self.use_recorded_objects and obj0 and obj1:
                for o in obj1:
                    if o in obj0 and o in preloadedFiles:
                        no = preloadedFiles[ o ]
                        # material
                        mat0 = obj0[o].get( 'material' )
                        mat1 = obj1[o].get( 'material' )
                        if mat0 and mat1:
                            amb0 = mat0[ 'ambient' ]
                            amb1 = mat1[ 'ambient' ]
                            dif0 = mat0[ 'diffuse' ]
                            dif1 = mat1[ 'diffuse' ]
                            emi0 = mat0[ 'emission' ]
                            emi1 = mat1[ 'emission' ]
                            spe0 = mat0[ 'specular' ]
                            spe1 = mat1[ 'specular' ]
                            shi0 = mat0[ 'shininess' ]
                            shi1 = mat1[ 'shininess' ]

                        if mat0 and mat1:
                            no.setMaterial( a.Material(
                                       ambient = [ \
                                       amb0[0]*(1-incr*i) + amb1[0]*incr*i,
                                       amb0[1]*(1-incr*i) + amb1[1]*incr*i,
                                       amb0[2]*(1-incr*i) + amb1[2]*incr*i,
                                       amb0[3]*(1-incr*i) + amb1[3]*incr*i ],
                                       diffuse = [ \
                                       dif0[0]*(1-incr*i) + dif1[0]*incr*i,
                                       dif0[1]*(1-incr*i) + dif1[1]*incr*i,
                                       dif0[2]*(1-incr*i) + dif1[2]*incr*i,
                                       dif0[3]*(1-incr*i) + dif1[3]*incr*i ],
                                       emission = [ \
                                       emi0[0]*(1-incr*i) + emi1[0]*incr*i,
                                       emi0[1]*(1-incr*i) + emi1[1]*incr*i,
                                       emi0[2]*(1-incr*i) + emi1[2]*incr*i,
                                       emi0[3]*(1-incr*i) + emi1[3]*incr*i ],
                                       specular = [ \
                                       spe0[0]*(1-incr*i) + spe1[0]*incr*i,
                                       spe0[1]*(1-incr*i) + spe1[1]*incr*i,
                                       spe0[2]*(1-incr*i) + spe1[2]*incr*i,
                                       spe0[3]*(1-incr*i) + spe1[3]*incr*i ],
                                       shininess = \
                                       shi0*(1-incr*i) + shi1*incr*i),
                                       refresh=False
                                       )
                        # palette


            params = {
                'zoom' : zoom0*(1-incr*i) + zoom*incr*i, 
                'view_quaternion' : \
                quaternion.Quaternion( (
                v0[0]*(1-incr*i) + v1[0]*incr*i,
                v0[1]*(1-incr*i) + v1[1]*incr*i,
                v0[2]*(1-incr*i) + v1[2]*incr*i,
                v0[3]*(1-incr*i) + v1[3]*incr*i
                ) ).normalized().vector(), 
                'observer_position' : (
                pos0[0]*(1-incr*i) + pos[0]*incr*i,
                pos0[1]*(1-incr*i) + pos[1]*incr*i,
                pos0[2]*(1-incr*i) + pos[2]*incr*i ), 
                'slice_quaternion' : \
                quaternion.Quaternion( (
                s0[0]*(1-incr*i) + s1[0]*incr*i, 
                s0[1]*(1-incr*i) + s1[1]*incr*i, 
                s0[2]*(1-incr*i) + s1[2]*incr*i, 
                s0[3]*(1-incr*i) + s1[3]*incr*i
                ) ).normalized().vector(), 
                'force_redraw' : 1,
                }
            if cpos and cpos0:
                params[ 'cursor_position' ] = (
                    cpos0[0]*(1-incr*i) + cpos[0]*incr*i, 
                    cpos0[1]*(1-incr*i) + cpos[1]*incr*i, 
                    cpos0[2]*(1-incr*i) + cpos[2]*incr*i, 
                    cpos0[3]*(1-incr*i) + cpos[3]*incr*i )
            win.camera( **params )
            if i == 0 and j == 0 and \
              ( self.animation is not None or self.keep_images ):
                # get anatomist to record mode
                a.execute("WindowConfig", windows=[win], record_mode='1',
                  record_basename=imgbase )
        # last step
        params = {
            'zoom' : zoom, 
            'view_quaternion' : \
            quaternion.Quaternion( ( v1[0], v1[1], v1[2], v1[3] \
                                          ) ).normalized().vector(), 
            'observer_position' : ( pos[0], pos[1], pos[2] ), 
            'slice_quaternion' : \
            quaternion.Quaternion( ( s1[0], s1[1], s1[2], s1[3] \
                                          ) ).normalized().vector(),
            'force_redraw' : 1
            }
        if cpos and cpos0:
            params[ 'cursor_position' ] = cpos
        win.camera( **params )

    if self.animation is not None or self.keep_images:
        a.execute("WindowConfig", windows=[win], record_mode = "0" )
        # This is needed to wait for Anatomist to finish what it is doing
        a.sync()
        #a.getInfo()

    if self.animation is not None:
        if len( mpegConfig.findEncoders() ) != 0:
            # make sure anatomist has finished its work
            a.sync()
            #a.getInfo()
            context.write( 'temp dir: ', tmp )
            context.write( 'imgbase: ', imgbase )
            inputs = os.listdir( tmp )
            inputs.sort()
            for i in xrange( len( inputs ) ):
                inputs[i] = os.path.join( tmp, inputs[i] )
            context.write( 'num images: ', len( inputs ) )
            #context.ask( 'check ' + tmp, 'OK' )
            #context.write( 'encoder:', self.encoder )
            #context.write( 'encoding:', self.encoding )
            self._executionNode.mpegEncode.images = inputs
            self._executionNode.run( context )
        else:
            context.warning( 'No animation encorder available - ' \
                             'skipping the encoding step' )
    if self.keep_images:
        context.write( 'Moving images...' )
        inputs = os.listdir( tmp )
        context.write( 'images:', len( inputs ) )
        dst = os.path.dirname( self.images_basename.fullPath() )
        for i in xrange( len( inputs ) ):
            s = os.path.join( tmp, inputs[i] )
            d = os.path.join( dst, inputs[i] )
            #context.write( 'move: ', s, ' -> ', d )
            try:
                os.rename( s, d )
            except:
                #context.write( 'move failed, trying to copy' )
                try:
                    shutil.copy( s, d )
                except:
                    context.write( 'can\'t copy' )
                os.unlink( s )

    return( selfdestroy )
