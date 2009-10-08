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
from brainvisa import anatomist

name = 'Anatomist Show Activations'
roles = ('viewer',)
userLevel = 0

def validation():
  anatomist.validation()

signature = Signature(
  'Zmap', ReadDiskItem( 'fMRI activations', [ 'GIS Image', 'VIDA Image' ] ),
  'view', Choice( ( 'Ask', None ), ( 'Activations', 0 ), ( 'Activations on MRI', 1 ), ( 'Both', 2 ) ),
  'dialog', Boolean(),
)

def initialization( self ):
  self.setOptional( 'view' )
  self.dialog = 0

def update( dialog ):
  try:
    a = anatomist.Anatomist()
    if dialog.view is None:
      mri = dialog.getValue( 'mri' )
      if mri is not None:
        print globals().keys()
        dialog.view = a.viewActivationsOnMRI( mri, dialog.Zmap,
                                                           dialog.getValue( 'matrix' ),
                                                           both = 0 )
    else:
      self.transformation=a.createTransformation(dialog.getValue( 'matrix' ), )
      dialog.view.updateTransformation( dialog.getValue( 'matrix' ), dialog.view["refFMRI"], dialog.view["refMRI"])
  except:
    neuroConfig.showLastException()

def execution( self, context ):
  print self.name
  
  a = anatomist.Anatomist()
  if self.view is None:
    tosee = context.ask( _t_('What would you like to see ?' ), 
      _t_( 'Activations' ), _t_( 'Activations on MRI' ), _t_( 'Both' ), _t_( 'Cancel' ) )
  else:
    tosee = self.view
  
  if tosee is None:
    alone = 1
    onMRI = 1    
  elif tosee == 0:
    alone = 1
    onMRI = 0
  elif tosee == 1:
    alone = 0
    onMRI = 1
  elif tosee == 2:
    alone = 1
    onMRI = 1
  else:
    return
  
  selfdestroy = []
  if alone and not onMRI:
      selfdestroy.append( a.viewObject( self.Zmap ) )
  if onMRI:
    mri = ReadDiskItem( 'T1 MRI', [ 'GIS Image', 'VIDA Image' ] ).findValue( self.Zmap )
    trm = ReadDiskItem( 'Transformation matrix', 'Transformation matrix' ).findValue( self.Zmap )
    if trm is None:
      trm = [ 0, 0, 0,
              1, 0, 0,
              0, 1, 0,
              0, 0, 1 ]
    else:
      f = open( trm.fullPath(), 'r' )
      trm = string.split( string.join( f.readlines() ) )
      f.close()
    view = None
    if mri is not None:
      view = a.viewActivationsOnMRI( mri, self.Zmap, trm, both = alone )
      selfdestroy.append( view )
    if self.dialog and neuroConfig.gui:
      d = context.dialog( 0, _t_( 'Co-registration options'),
        Signature(
          'mri', ReadDiskItem( 'T1 MRI', [ 'GIS Image', 'VIDA Image' ] ),
          'matrix', ListOf( Float() ),
        ),
        ( _t_('Update'), update )
      )
      d.setValue( 'mri', mri )
      d.setValue( 'matrix', trm )
      d.view = view
      d.Zmap = ( self.Zmap )
      context.mainThreadActions().push( d.show )
  return selfdestroy
