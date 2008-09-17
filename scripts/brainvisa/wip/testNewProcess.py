from brainvisa.wip.newProcess import NewProcess
from soma.signature.api import Signature, Unicode, Number

class TestProcess( NewProcess ):
  name = '/tests/new signature/test'
  signature = Signature(
    's', Unicode,
    'n', Number,
  )
  
  def __init__( self ):
    super( TestProcess, self ).__init__()
    self.s = 'test'
    self.n = 42
  
  
  def run( self ):
    for n in self.signature.keys()[1:]:
      print >> self.userContext.stdout, repr(n), '=', repr( getattr( self, n ) )


class TestProcess2( TestProcess ):
  name = '/tests/new signature/test2'


class TestProcess3( TestProcess ):
  name = '/tests2/new signature/test3'

class TestProcess4( TestProcess ):
  name = '/tests2/new signature2/test4'


TestProcess.registerInBrainVISA()
TestProcess2.registerInBrainVISA()
TestProcess3.registerInBrainVISA()
TestProcess4.registerInBrainVISA()

#mainWindow = neuroProcessesGUI._mainWindow

#testTree = neuroProcesses.ProcessTree( name='tests', editable=False, user=False )
#signatureTree = testTree.Branch( name='new signature', editable=False )
#testTree.append( signatureTree )
#processLeaf = testTree.Leaf( processId=TestProcess, icon='icon_process_3.png', name='test', editable=False )
#signatureTree.append( processLeaf )
#mainWindow.processTrees.model.append( testTree )

