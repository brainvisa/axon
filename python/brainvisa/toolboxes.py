from neuroProcesses import ProcessTree
import os, traceback
from soma.minf.api import readMinf, minfFormat
from soma.sorted_dictionary import SortedDictionary
from soma.wip.application.api import findIconFile

class Toolbox( object ):
  """
  @type name: string 
  @ivar name: toolbox name. It can be the name given in the constructor, or the userName specified in the toolbox .py file.
  @type id: string
  @ivar id: identifier for the toolbox.
  @type processTree: ProcessTree
  @ivar processTree: content of the toolbox
  """
  def __init__( self, name, toolboxDirectory, icon=None, description=None ):
    """
    @type name: string
    @param name: toolbox name.
    @type toolboxDirectory: string
    @param toolboxDirectory: main directory for this toolbox.
    @type description: string
    @param description: short text describing the toolbox. It's optional, it can be set in init file. It will be printed in a tooltip.
    """
    if icon is None:
      icon = findIconFile( 'toolbox.png')
    d = {
      'userName': name,
      'icon': icon,
      'description' : description,
    }
    # options can be set in toolboxeDirectory/<name>.py
    initFile = os.path.join( toolboxDirectory, name + '.py' )
    if os.path.exists( initFile ):
      execfile( initFile, {}, d )
    
    self.name = d[ 'userName' ]
    self.id = name.lower()
    self.toolboxDirectory = toolboxDirectory
    self.processesDir = os.path.join( toolboxDirectory, 'processes' )
    self.initializationFile = os.path.join( toolboxDirectory, 'initialization.py' )
    self.startupFile = os.path.join( toolboxDirectory, 'startup.py' )
    self.fsoDir = os.path.join( toolboxDirectory, 'hierarchies' )
    self.typesDir = os.path.join( toolboxDirectory, 'types' )
    if ( d[ 'icon' ] != None ) :
      self.icon = os.path.join( toolboxDirectory, d[ 'icon' ] )
    self.processTree = None
    self.description = description
    
  
  def getProcessTree( self ):
    if self.processTree is None:
      self.processTree = ProcessTree(
        name=self.name,
        id=self.id,
        icon=self.icon,
        tooltip=self.description,
        editable=False, 
        user=False )
      # create a process tree parsing the processes directory, 
      # category associated to processes while going throught directories : toolboxName/rep1/rep2...
      if os.path.exists( self.processesDir ):
        self.processTree.addDir( self.processesDir, self.id )
      # Read minf file for processes to add in other toolboxes or in this toolbox
    return self.processTree
  
  def links( self ):
    """
    Gets the links between this toolbox and other toolboxes reading the minf file of the toolbox (if there is one).
    Must be called only after having loaded all toolboxes to be sure that all referenced processes are loaded.
    @rtype: list of ProcessTree
    @return : links to other toolboxes. each process tree represents another toolbox and contains part of current toolbox that must be added in the other toolbox. 
    """
    linkToolboxesFile=os.path.join( self.toolboxDirectory, self.id + ".minf" )
    otherToolboxes=None
    if os.access( linkToolboxesFile, os.F_OK ): # if the file exists, read it
      format, reduction = minfFormat( linkToolboxesFile )
      if reduction == "brainvisa-tree_2.0":
          otherToolboxes = readMinf( linkToolboxesFile )[ 0 ]
    if otherToolboxes is not None:
      for otherToolbox in otherToolboxes:
        otherToolbox.user = False
        otherToolbox.setEditable( False )
        # the id is the name in lower case (the initName before any translation)
        otherToolbox.id = otherToolbox.initName.lower() 
        otherToolbox.icon = findIconFile( 'toolbox.png' )
        yield otherToolbox
  
_toolboxes = {}
  

def readToolboxes( toolboxesDir, homeBrainVISADir ):
  """
  Search for toolboxes directory in neuroConfig.toolboxesDir (brainvisa/toolboxes) and in brainvisaHomeDir (.brainvisa).
  """
  global _toolboxes
  _toolboxes = SortedDictionary()
  if not os.path.exists( toolboxesDir ):
    return

  # always load toolboxes in the same order. (listdir doesn't give results always ordered the same way)
  for name in sorted( os.listdir( toolboxesDir ) ):
    try:
      print 'Loading toolbox', name
      _toolboxes[ name ] = Toolbox( name, os.path.join( toolboxesDir, name ) )
    except:
        traceback.print_exc()
  print 'Loading toolbox', 'My processes'
  _toolboxes[ 'My processes' ] = Toolbox( 'My processes', toolboxDirectory= homeBrainVISADir )
        

def allToolboxes():
  """
  @rtype: iterator of Toolbox
  @return: all loaded toolboxes. 
  """
  global _toolboxes
  return _toolboxes.itervalues()

def getToolbox(id):
  """
  @rtype: Toobox
  @return: the toolbox whose id is given. The id of a toolbox is its directory name (lowercase) or if it doesn't have a named directory, the toolbox's name in lowercase.
  """
  return _toolboxes.get(id)