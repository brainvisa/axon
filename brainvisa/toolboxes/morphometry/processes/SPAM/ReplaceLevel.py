# -*- coding: iso-8859-1 -*-

#
#  Copyright (C) 2000-2001 INSERM
#  Copyright (C) 2000-2003 CEA
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

import shfjGlobals     
from brainvisa import shelltools

from neuroProcesses import *
name = 'Threshold and Normalize'
userLevel = 2

signature = Signature(
    'Image', ReadDiskItem( '3D Volume', 'GIS image' ),
    'Method', Choice('gt' ,'le', 'lt', 'ge', 'eq', 'di', 'be', 'ou'),
    'Normalize', Choice('yes' ,'no'),
    'Threshold', Float(),
 )

def initialization( self ):
     self.Thresholded = 0

def execution( self, context ):


     context.system('AimsThreshold', '-o', self.Image.fullPath(),'-m',
                    self.method, '-t', self.Threshold, '-b', '-i', self.Image.fullPath() )

     if self.Normalize == 'yes':
          context.system('AimsReplaceLevel', '-i',self.Image.fullPath(),
                         '-g','32767', '-n','1', '-o',self.Image.fullPath()  )
