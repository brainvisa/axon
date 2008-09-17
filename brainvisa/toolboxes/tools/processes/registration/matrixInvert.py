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
#  $Id: //depot/brainvisa/main/processes/converters/automatic/transformInverter.py#2 $
#

from neuroProcesses import *
import shfjGlobals

name = 'Transformation inverter'
userLevel=1

signature = Signature(
  'transformation', ReadDiskItem( 'Transformation matrix', 'Transformation matrix' ),
  'inverted_transformation', WriteDiskItem( 'Transformation matrix', 'Transformation matrix' ),
)

def initialization( self ):
    def reverseTrans( self, proc ):
      if self.transformation is not None:
        return WriteDiskItem( 'Transformation matrix',
                                'Transformation matrix',
                                requiredAttributes = \
                                { 'from': self.transformation.get( 'to' ),
                                  'to': self.transformation.get( 'from' ) }
                                ).findValue( self.transformation )
      else:
        return None                              
    self.linkParameters( 'inverted_transformation', 'transformation', reverseTrans )

def execution( self, context ):
    context.system( 'AimsInvertTransformation', '-i', self.transformation.fullPath(),
                    '-o', self.inverted_transformation.fullPath() )
