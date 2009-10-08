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

from neuroProcesses import *
import shfjGlobals
from brainvisa import anatomist

name = 'Label volume editor'
roles = ('editor',)
userLevel = 0

def validation():
    anatomist.validation()

signature = Signature(
  'label_volume', WriteDiskItem( 'Label volume',
                                 shfjGlobals.aimsVolumeFormats ),
  'support_volume', ReadDiskItem( 'Raw T1 MRI',
                                  shfjGlobals.anatomistVolumeFormats ),
  'pipeline_mask_nomenclature', ReadDiskItem( 'Nomenclature', 'Hierarchy' ),
  'background_label', OpenChoice( 'minimum' ),
)

def initialization( self ):
  self.linkParameters( 'support_volume', 'label_volume' )
  self.pipeline_mask_nomenclature = self.signature[ 'pipeline_mask_nomenclature' ].findValue( {"filename_variable" : "pipeline_masks"}, requiredAttributes = { "filename_variable" : "pipeline_masks" } )
  self.setOptional('pipeline_mask_nomenclature')
  self.setOptional('support_volume')
  
def execution( self, context ):
  a = anatomist.Anatomist()
  hie = a.loadObject( self.pipeline_mask_nomenclature )

  context.write( 'background:', self.background_label )
  if self.background_label != 'minimum':
    mask = context.temporary( 'GIS image', 'Label Volume' )
    context.write( 'not min' )
    context.system( 'AimsReplaceLevel', '-i', self.label_volume, '-o', mask,
      '-g', int( self.background_label ), '-g', -32767, '-n', -32767, '-n',
      -32766 )
  else:
    mask = self.label_volume
  if self.support_volume:
    vol = self.support_volume
  else:
    vol = mask
  tmpdir = context.temporary( 'directory' )
  voi = os.path.join( tmpdir.fullPath(), 'voi.ima' )
  voigraph = os.path.join( tmpdir.fullPath(), 'voigraph.arg' )
  fgraphbase = os.path.join( tmpdir.fullPath(), 'finalgraph' )
  finalgraph = fgraphbase + '.arg'

  context.system( 'AimsGraphConvert', 
                  '-i', mask.fullPath(), 
                  '-o', voigraph, 
                  '--bucket' )

  imagenum = a.loadObject( vol )
  voigraphnum = a.loadObject( voigraph )
  ref=imagenum.referential
  if ref != a.centralRef:
    voigraphnum.assignReferential( ref )
    windownum = a.createWindow( 'Axial' )
    windownum.assignReferential( ref )
  else:
    windownum = a.createWindow( 'Axial' )
  a.addObjects( objects=[voigraphnum,imagenum], windows=[windownum] )

  voigraphnum.setMaterial( a.Material( diffuse=[ 0.8, 0.8, 0.8, 0.5 ] ) )
  #selects the graph
  children = voigraphnum.children
  windownum.group.addToSelection( children )
  windownum.group.unSelect( children[1:] )
  del children

  a.execute( 'SetControl', windows=[windownum], control='PaintControl' )
  windownum.showToolbox(True)
  
  rep = context.ask( "Click here when finished","OK", "Cancel", modal=0 )
  if rep != 1:
    voigraphnum.save(voigraph)
    a.sync() # make sure that anatomist has finished to process previous commands
    #a.getInfo()
    context.system( 'AimsGraphConvert', 
                    '-i', voigraph, 
                    '-o', finalgraph, 
                    '--volume' )
    if self.background_label != 'minimum':
      val = self.background_label
    else:
      val = 0
    context.system( 'AimsReplaceLevel', '-i',
      os.path.join( fgraphbase + '.data' , 'roi_Volume' ), '-o',
      self.label_volume, '-g', -1, '-n', val )
    #context.system( 'VipMerge',
                    #'-i', os.path.join( fgraphbase + '.data' , 'roi_Volume' ),
                    #'-m', os.path.join( fgraphbase + '.data' , 'roi_Volume' ),
                    #'-o', self.label_volume.fullPath(),
                    #'-c', 'l', '-l', '-1', '-v', '0' )
  #return ( imagenum, voigraphnum, windownum )
