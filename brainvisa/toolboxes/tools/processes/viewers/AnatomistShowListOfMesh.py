#
#  Copyright (C) 2000-2001 INSERM
#  Copyright (C) 2000-2002 CEA
#  Copyright (C) 2000-2001 CNRS
#
#  This software and supporting documentation were developed by
#  	INSERM U494
#  	Hopital Pitie Salpetriere
#  	91 boulevard de l'Hopital
#  	75634 Paris cedex 13
#  	France
#  	--
#  	CEA/DSV/SHFJ
#  	4 place du General Leclerc
#  	91401 Orsay cedex
#  	France
#  	--
#  	CNRS UPR640-LENA
#  	Hopital Pitie Salpetriere
#  	47 boulevard de l'Hopital
#  	75651 Paris cedex 13
#  	France
#
#  $Id$
#

from neuroProcesses import *
import shfjGlobals
from brainvisa import anatomist

name = 'Show in anatomist a list of mesh'
userLevel = 2

signature = Signature(
    'mesh',      ListOf(ReadDiskItem('Any Type','MESH mesh' )),
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
