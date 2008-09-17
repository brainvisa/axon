#
#  Copyright (C) 2000-2001 INSERM
#  Copyright (C) 2000-2002 CEA
#  Copyright (C) 2000-2001 CNRS
#
#  This software and supporting documentation were developed by
#    INSERM U494
#    Hopital Pitie Salpetriere
#    91 boulevard de l'Hopital
#    75634 Paris cedex 13
#    France
#    --
#    CEA/DSV/SHFJ
#    4 place du General Leclerc
#    91401 Orsay cedex
#    France
#    --
#    CNRS UPR640-LENA
#    Hopital Pitie Salpetriere
#    47 boulevard de l'Hopital
#    75651 Paris cedex 13
#    France
#
#  $Id$
#

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



