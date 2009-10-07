#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL-B license under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the 
# terms of the CeCILL-B license as circulated by CEA, CNRS
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
# knowledge of the CeCILL-B license and that you accept its terms.
from neuroProcesses import *
import shfjGlobals
from brainvisa import anatomist

name = 'ROI drawing'
userLevel = 1

signature = Signature(
  'image', ReadDiskItem( '4D Volume', shfjGlobals.anatomistVolumeFormats ),
  'ROI', WriteDiskItem( 'ROI', 'Graph and data' ),
)

def validation():
    anatomist.validation()

def initialize( self ):
  self.linkParameters( 'ROI', 'image' )

def inlineGUI( self, values, context, parent ):
  btn = QPushButton( _t_( 'Show' ), parent )
  btn.connect( btn, SIGNAL( 'clicked()' ), context._runButton )
  return btn

def execution( self, context ):
  sourceUuid = self.image.uuid( saveMinf=False )
  self.ROI.setMinf( 'source_volume', str( sourceUuid ) )

  a = anatomist.Anatomist()
  imageObject = a.loadObject( self.image )

  nodesObjects = []
  if not self.ROI.isReadable():
    regionsObject = a.createGraph( object=imageObject,
                                   name=self.ROI.fullPath(),
                                   filename=self.ROI.fullPath() )
    # Create a region
    nodesObjects.append( regionsObject.createNode( name='region',
                                                   duplicate=False ) )
  else:
    regionsObject = a.loadObject( self.ROI.fullPath() )

  # Show regions and linked image
  block = a.createWindowsBlock()
  windowC = a.createWindow( 'Coronal', block=block )
  windowS = a.createWindow( 'Sagittal', block=block )
  windowA = a.createWindow( 'Axial', block=block )
  a.addObjects( [ imageObject, regionsObject ], [windowC, windowS, windowA] )
  a.setWindowsControl( windows=[windowC, windowS, windowA], control="PaintControl" )
  window3 = a.createWindow( '3D', block=block )
  window3.addObjects( [regionsObject] )
  
  return ( imageObject, regionsObject, windowC, windowS, windowA, window3,
           nodesObjects )
