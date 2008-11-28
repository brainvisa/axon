from neuroProcesses import *

signature = Signature('number', Number())

def buildNewSignature( self, number ):
  # Create a new Signature object
  paramSignature = ['number', Number()]
  for i in xrange( number ):
	  paramSignature += [ 'n' + str( i ), Number() ]
  signature = Signature( *paramSignature )
  # Set optional parameters
  for i in xrange( number ):
	  signature[ 'n' + str( i ) ].mandatory = False

  # Change the signature
  self.changeSignature( signature )


def initialization( self ):
  self.number = 0
  # Call self.buildNewSignature each time number is changed
  self.addLink( None, 'number', self.buildNewSignature )


def execution( self, context ):
  # Print all parameters values
  for n in self.signature.keys():
	  context.write( n, '=', getattr( self, n ) )
  if self.number == 0:
    # Try dynamic signature in batch mode
	  context.runProcess("DynamicSignature",4,1.2,3.4,5.6,7.8)
  context.system( 'sleep', '2s' )
  raise Exception( 'Arrgh !' )
