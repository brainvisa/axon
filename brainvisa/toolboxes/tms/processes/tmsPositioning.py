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

from neuroProcesses import *
import shfjGlobals
from brainvisa import anatomist

name = 'TMS positioning'
userLevel = 2

def validation():
    if neuroConfig.platform != 'darwin':
        raise ValidationError( 'This process is useless on other platforms '
                               'than MacOS X because it runs with BrainSight' )
    anatomist.validation()

signature = Signature(
    'BrainSight_output', ReadDiskItem( 'TMS position file',
                                       'TMS position file' ),
    'T1_mri', ReadDiskItem( 'T1 MRI', shfjGlobals.aimsVolumeFormats ),
    'window', anatomist.AWindowChoice(),
    'update_frequency', Float(), 
    'TMS_mesh', ReadDiskItem( 'Mesh', shfjGlobals.aimsMeshFormats ), 
    'pointer_type', Choice( 'Coil', 'Pointer' ), 
    )

def initialization( self ):
    self.setOptional( 'T1_mri' )
    self.update_frequency = 10
    self.setOptional( 'TMS_mesh' )
    self.TMS_mesh = self.signature[ 'TMS_mesh' ].findValue( \
      { 'category': 'tms_template', 'filename_variable': 'tms_coil' },
      requiredAttributes = { 'category': 'tms_template',
                             'filename_variable': 'tms_coil' } )

def readPos( self, tms ):
    try:
        #print 'readPos'
        msg = os.read( tms, 10000 )
        if len( msg ) == 0:
            time.sleep( 1/self.update_frequency )
        self._rawmsg += msg
        #print 'msg:', self._rawmsg
        x = 0
        y = 0
        while x >= 0:
            x = self._rawmsg.find( '\n', y )
            if x >= 0:
                self._msg.append( self._rawmsg[y:x] )
                y = x + 1
        self._rawmsg = self._rawmsg[y:]
        #print 'linedmsg:', self._rawmsg


        l = len( self._msg )
        if l >= 10:
            del self._msg[:int(l/5-1)*5]
        while len( self._msg ) >= 5:
            self.processMessage( self._msg )
        #print 'readPos end'
    except:
        self.removeTMSreader()
        raise

def processMessage( self, msg ):
    try:
        if len( msg ) < 5:
            return
        if msg[0][:14] != 'Trajectory at ':
            if len( msg ) != 0:
                print 'Unable to understand message:', msg[0]
            del msg[0]
            return
        timestamp = int( msg[0][14:] )
        #print 'timestamp:', timestamp
        matrix = map( lambda x: float(x), msg[1].split()[:3] )
        matrix += map( lambda x: float(x), msg[2].split()[:3] )
        matrix += map( lambda x: float(x), msg[3].split()[:3] )
        matrix = map( lambda x: float(x), msg[4].split()[:3] ) + matrix
        # transpose the matrix: BrainSight uses it in the form
        # [ x y z 1 ] M
        # and we need the (more common) form:
        # M [ x y z 1 ]
        a = matrix[4]
        matrix[4] = matrix[6]
        matrix[6] = a
        a = matrix[5]
        matrix[5] = matrix[9]
        matrix[9] = a
        a = matrix[8]
        matrix[8] = matrix[10]
        matrix[10] = a
        #print matrix
        #a = anatomist.Anatomist()
        self._trans.update( matrix=matrix )
        # consume message (5 lines)
        del msg[:5]
    except:
        self.removeTMSreader()
        raise

def installTMSreader( self, tms ):
    snot = QSocketNotifier( tms, QSocketNotifier.Read, None, 'TMS listener' )
    self._notifier = snot
    self._msg = []
    snot.connect( snot, SIGNAL( 'activated( int )' ), self.readPos )

def removeTMSreader( self ):
    if self._notifier:
        del self._notifier
        self._notifier = None

def execution( self, context ):
    a = anatomist.Anatomist()
    win = self.window()
    if self.TMS_mesh is not None:
      # load an existing mesh representing the TMS coal
      cf = self.TMS_mesh
    else:
      # no mesh provided, create a new one
      cp = context.temporary( 'Config file' )
      f = open( cp.fullPath(), 'w' )
      orient = 1
      if self.pointer_type == 'Pointer':
        orient = 0
      print >> f, 'attributes = {'
      print >> f, "  'type' : 'arrow',"
      print >> f, "  'point1' : [ 0, 0, 0  ],"
      if orient == 0:
        print >> f, "  'point2' : [ 0, 0, 100 ],"
      else:
        print >> f, "  'point2' : [ 100, 0, 0 ],"
      print >> f, "  'radius' : 2,"
      print >> f, "  'facets' : 6,"
      print >> f, "  'arrow_radius' : 4,"
      print >> f, "  'arrow_length_factor' : 0.3,"
      print >> f, "}"
      f.close()
      cf = context.temporary( 'Mesh mesh' )
      context.system( 'AimsMeshGenerate', '-i', cp.fullPath(), '-o',
                      cf.fullPath() )

      f = open( cp.fullPath(), 'w' )
      print >> f, 'attributes = {'
      print >> f, "  'type' : 'cylinder',"
      if orient == 0:
        print >> f, "  'point1' : [ -25, 0, 40  ],"
        print >> f, "  'point2' : [ -25, 0, 60 ],"
      else:
        print >> f, "  'point1' : [ 40, -25, 0  ],"
        print >> f, "  'point2' : [ 60, -25, 0 ],"
      print >> f, "  'radius' : 25,"
      print >> f, "  'facets' : 20,"
      print >> f, "  'closed' : 1,"
      print >> f, "}"
      f.close()
      cf1 = context.temporary( 'Mesh mesh' )
      context.system( 'AimsMeshGenerate', '-i', cp.fullPath(), '-o',
                      cf1.fullPath() )

      f = open( cp.fullPath(), 'w' )
      print >> f, 'attributes = {'
      print >> f, "  'type' : 'cylinder',"
      if orient == 0:
        print >> f, "  'point1' : [ 25, 0, 40  ],"
        print >> f, "  'point2' : [ 25, 0, 60 ],"
      else:
        print >> f, "  'point1' : [ 25, 40, 0  ],"
        print >> f, "  'point2' : [ 25, 60, 0 ],"
      print >> f, "  'radius' : 25,"
      print >> f, "  'facets' : 20,"
      print >> f, "  'closed' : 1,"
      print >> f, "}"
      f.close()
      cf2 = context.temporary( 'Mesh mesh' )
      context.system( 'AimsMeshGenerate', '-i', cp.fullPath(), '-o',
                      cf2.fullPath() )
      context.system( 'AimsZCat', '-o', cf.fullPath(), '-i', cf.fullPath(), '-i', cf1.fullPath(), 
                      '-i', cf2.fullPath() )


    cyl = a.loadObject( cf.fullPath() )
    self._refbase = a.createReferential()
    #cyl.assignReferential(self._refbase)
    self._ref = a.createReferential()
    cyl.assignReferential(self._ref)
    cyl.setMaterial( a.Material(diffuse=[ 1, 0, 0, 1 ]) )

    transl = [ 0, 0, 0 ]
    if self.T1_mri:
        atts = shfjGlobals.aimsVolumeAttributes( self.T1_mri )
        dims = atts[ 'volume_dimension' ]
        vs = atts[ 'voxel_size' ]
        transl[0] = 0.5 * vs[0]
        transl[1] = 0.5 * vs[1]
        transl[2] = (dims[2]-0.5) * vs[2]
    self._transbase = a.createTransformation( transl + [ 1, 0, 0,
                                                                0, 1, 0,
                                                                0, 0, -1 ], 
                                            a.centralRef,
                                            self._refbase)
    self._trans = a.createTransformation( [ 0, 0, 0, 1, 0, 0, 
                                                   0, 1, 0, 0, 0, 1 ], 
                                          self._ref, self._refbase)
    win.addObjects( [cyl] )
    # open TMS file
    tms = os.open( self.BrainSight_output.fullPath(), os.O_RDONLY )
    # skip strange 'header'
    #os.read( tms, 0x80 )
    self._rawmsg = ''
    # install handler
    context.mainThreadActions().call( self.installTMSreader, tms )

    # wait for end
    a.waitEndProcessing()
    context.ask( _t_( 'Click here to stop' ), _t_( 'Stop' ) )
    context.mainThreadActions().call( self.removeTMSreader )
