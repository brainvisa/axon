#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCIL license version 2 under
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
# knowledge of the CeCILL version 2 license and that you accept its terms.

from neuroProcesses import *
import shfjGlobals
from brainvisa import anatomist

name = 'Show in anatomist a list of mesh'
userLevel = 2

signature = Signature(
    'mesh',      ListOf(ReadDiskItem('Any Type','Anatomist mesh formats' )),
    'transformations',    ListOf(ReadDiskItem( 'Transformation matrix', 'Transformation matrix')),
    'color',          ListOf(Number())
  )

def validation():
    anatomist.validation()

def stringParameters( **kwargs ):
    return str( kwargs )

def initialization( self ):
    self.setOptional('color','transformations')
  
def execution( self, context ):

    nb=len(self.mesh)
    
    #Ouverture de Anatomist 
    a = anatomist.Anatomist()

    #Chargement des graphs
    mesh_object=[]
    for m in self.mesh:
        mesh_object.append(a.loadObject( m.fullPath() ))
    #Ouverture des fenetres
    window=[]
    for i in range(nb):
      window.append(a.createWindow( '3D' ))

    #Ajout des graph dans les fenetres avec modification des couleurs
    #def des coef de transparence:
    for i in range(nb):
      window[i].a.addObjects( [mesh_object[i]] )

    # creation et assignement des referentiels
    if self.transformations:
      ref=[]
      for i in range(nb):
        r=a.createReferential()
        mesh_object[i].assignReferential(r)
        ref.append(r)

      #Chargement de transformation Faisceaux_TO_refCommun.trm
      ref_commun=a.centralRef
      transfo=[]
      for i in range(nb):
        transfo.append(a.loadTransformation(filename = self.transformations[i].fullPath(), origin=ref[i], destination=ref_commun))

      return ( mesh_object, window, ref, transfo )
    else:
      return ( mesh_object, window)
