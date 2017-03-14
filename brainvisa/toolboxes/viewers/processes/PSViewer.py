# -*- coding: iso-8859-1 -*-

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

from __future__ import print_function
from brainvisa.processes import *
import string, types, os
from brainvisa import shelltools

name = 'Show PS or PSGZ files'
roles = ('viewer',)
userLevel = 0

def findPSviewer():
  psviewer = []
  if findInPath( 'gv' ):
    psviewer.append( 'gv' )
  if findInPath( 'kghostview' ):
    psviewer.append( 'kghostview' )
  if findInPath( 'okular' ):
    psviewer.append( 'okular' )
  if findInPath( 'evince' ):
    psviewer.append( 'evince' )
  return psviewer

psviewers = findPSviewer()

signature = Signature(
        'psfile', ReadDiskItem( 'Postscript file', [ 'PS file', 'gz compressed PS file'] ),
        'PSviewer', Choice( *psviewers ),
        'waitFor_userFileClose', Boolean(), 
)      

def validation():
  if len( psviewers ) == 0:
    raise ValidationError( _t_( 'no PostScript viewer available' ) )

def initialization( self ):
  self.waitFor_userFileClose = True
  if 'evince' in psviewers:
    self.PSviewer = 'evince'
  elif 'kghostview' in psviewers:
    self.PSviewer = 'kghostview'
  elif 'gv' in psviewers:
    self.PSviewer = 'gv'
  elif 'okular' in psviewers:
    self.PSviewer = 'okular'
  else:
    context.write( 'unknown PostScript Viewer')

def execution( self, context ):
  PSExtension = os.path.splitext( self.psfile.fullPath( ) )
  print('ps extension: ', str( PSExtension ))
  if PSExtension[1]=='.gz':
    
    if self.PSviewer == 'kghostview' or self.PSviewer == 'evince' or self.PSviewer == 'okular': 
      PSTmpFile = self.unzip(context, os)
      if(self.waitFor_userFileClose):
        cmd = [self.PSviewer,  PSTmpFile]
        context.system(*cmd)
      else:
        os.system(self.PSviewer+' "'+PSGZTmpFile+'" &')# & so dont waitFor_userFileClose 
    
    elif self.PSviewer == 'gv':
      cmd = ['gv', self.psfile.fullPath( ) ]
      context.system( *cmd )
    
  else:
    if(self.waitFor_userFileClose):
      cmd = [self.PSviewer,self.psfile.fullPath( )]
      context.system( *cmd )
    else:
      cmd = self.PSviewer+' "'+self.psfile.fullPath( )+'"'
      os.system(cmd+' &')# & so dont waitFor_userFileClose

def unzip(self, context, os):
  tmpDir = context.temporary('Directory')
  if os.path.exists(tmpDir.fullPath()) is None:
    os.mkdir(tmpDir.fullPath())
  shelltools.cp(self.psfile.fullPath(), tmpDir.fullPath())
  PSGZTmpFile = os.path.join(tmpDir.fullPath(), os.path.basename(self.psfile.fullPath()))
  PSTmpFile = os.path.splitext(PSGZTmpFile)
  cmd = ['gunzip', PSGZTmpFile ]
  context.system(*cmd)
  return PSTmpFile[0]
