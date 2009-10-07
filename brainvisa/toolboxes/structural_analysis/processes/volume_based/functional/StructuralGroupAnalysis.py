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
name = '3 - Structural Group Analysis'
userLevel = 2


signature = Signature(
#     'Lwhitemesh', ReadDiskItem( 'Left Hemisphere White Mesh' , shfjGlobals.aimsMeshFormats),
#     'Rwhitemesh', ReadDiskItem( 'Right Hemisphere White Mesh' , shfjGlobals.aimsMeshFormats),
    'primalsketches', ListOf(ReadDiskItem( 'Primalsketch graph', 'Graph' )),
    'model', ReadDiskItem( 'Model graph', 'Graph' ), 
    'temp', Float(),
    'rate', Float(),
    'gibbsChange', Integer()
  )

def initialization( self ):
     self.temp = 300.0
     self.rate = 0.98
     self.gibbsChange = 1
     self.model = "/home/grg/Perforce/shared-main/models/3.0/functionalsketchmodel/surfacebasedfunctionalsketchmodel.arg"

def execution ( self, context ):
     config=context.temporary( 'Tree' )
     #config=File( '/tmp/germaine' )
     fconfig=open(config.fullPath(), 'w')
     logf=context.temporary( 'Text file' )

     if (self.rate >= 1.0) or (self.rate <=0) :
          context.write( 'Sorry but the rate parameter must be in ]0;1[' )
     else :
          templist=''
          tempout=''
          for ps in self.primalsketches :
               templist += '|' + ps.fullPath()
               tempout += '|' + ps.fullPath() + '_auto.arg'
          sketchlist=templist[1:]
          sketchout=tempout[1:]
          context.write(sketchlist)
          context.write(sketchout)

          context.write(config.fullPath())

          fconfig.write('*BEGIN TREE siRelax\n')
          fconfig.write('modelFile ' + self.model.fullPath() + '\n')
          gf = 'graphFile ' + sketchlist + '\n'
          of = 'output ' + sketchlist + '\n'
          fconfig.write(gf)
          fconfig.write(of)
          fconfig.write('initflg 1\n')
          fconfig.write('save 1\n')
          s = str(self.temp)
          t='temp ' + s + '\n'
          fconfig.write(t)
          fconfig.write('mode gibbs\n')
          s=str(self.rate)
          t='rate ' + s + '\n'
          fconfig.write(t)
          fconfig.write('tempICM 0\n')
          s=str(self.gibbsChange)
          t='gibbsChange ' + s + '\n'
          fconfig.write(t)
          fconfig.write('verbose 1\n')
          t='plotfile ' + logf.fullPath() + '\n'
          fconfig.write(t)
          fconfig.write('voidMode NONE\n')
#           fconfig.write('voidLabel 0\n')
          fconfig.write('*END\n')
          fconfig.close()

          label=['siRelax', config.fullPath()]
          analyse=['siFunctionalGraphs', config.fullPath()]
          context.write('Labelling graphs')
          apply( context.system, label )
          context.write('Post-labelling analysis')
          apply( context.system, analyse)



