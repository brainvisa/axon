# -*- coding: utf-8 -*-
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
from brainvisa.configuration import neuroConfig
from brainvisa.data.sqlFSODatabase import SQLDatabase
from soma.path import relative_path
from brainvisa.toolboxes import getToolbox
from brainvisa.data.fileSystemOntology import FileSystemOntology
import subprocess
import six

signature = Signature(
  'write_graphs', Boolean(),
  #'htmlDirectory', WriteDiskItem( 'Any type', 'Directory' ),
)

def initialization( self ):
  self.setOptional("write_graphs")
  self.write_graphs=True
  #self.addLink( 'htmlDirectory', 'ontology', lambda ontology: os.path.join( neuroConfig.mainDocPath, 'ontology-' + ontology ) )

#----------------------------------------------------------------------------
def generateHTMLDocumentation( processInfoOrId, translators, context, ontology ):
  processInfo = getProcessInfo( processInfoOrId )
  documentation = readProcdoc( processInfo.id )
  
  if context is not None:
    # this <font></font> thing is a trick to allow text to be considered as
    # HTML, and the <br/> not escaped, otherwise either "<br/>" appears in
    # the process view window, or the log has no line breaks
    context.write( '<font></font>Generate HTML for process "' + processInfo.name + '"<br/>' )
  # english translation is the default
  den = documentation.get( 'en', {} )
  pen = den.get( 'parameters', {} )
  # Generate HTML documentations
  for l in neuroConfig._languages:
    tr = translators.get( l, None )
    if not tr:
      tr=neuroConfig.Translator(l)
    d = documentation.get( l, {} )
    htmlFileName = getHTMLFileName( processInfo.id, documentation, l )
    p = os.path.dirname( htmlFileName )
    if not os.path.isdir( p ):
      os.makedirs( p )
    # Main page
    f = open( htmlFileName, 'w' )
    print('<html>', file=f)
    print('<head>', file=f)
    print('<title>' + tr.translate( processInfo.name ) + '</title>', file=f)
    # unicode strings written in this file are encoded using default encoding
    # to choose a different encoding, unicode_string.encode("encoding") should be used
    # in Brainvisa, the default encoding is set at initilization using sys.setdefaultencoding in neuro.py
    print('<meta http-equiv="Content-Type" content="text/html; charset='+sys.getdefaultencoding()+'">', file=f)
    print('<meta content="BrainVISA ' + neuroConfig.shortVersion + '" name="generator">', file=f)
    print('<link rel="stylesheet" href="../../axon.css" media="screen" />', file=f)
    print('</head>', file=f)
    print('<body>', file=f)
    print('<h1><a href="bvshowprocess://' + processInfo.id
          + '"><img src="../../images/icons/icon_process.png" border="0"></a>',
          file=f)
    print('<a name="bv_process%' + processInfo.id + '">'
          + tr.translate(processInfo.name) + '</a></h1>', file=f)
    print('<blockquote>', file=f)
    short = d.get('short')
    if short:
      short = convertSpecialLinks( short, l, '', tr )
      short = XHTML.html( short )
    if not short and l != 'en':
      short = den.get( 'short' )
      if short:
        short = convertSpecialLinks( short, l, '', tr )
        short = XHTML.html( short )
    print(short, file=f)
    print('</blockquote>', file=f)

    # Description
    long = d.get( 'long' )
    if long:
      long = convertSpecialLinks( long, l, '', tr )
      long = XHTML.html( long )
    if not long and l != 'en':
      long = den.get( 'long' )
      if long:
        long = convertSpecialLinks( long, l, '', tr )
        long = XHTML.html( long )
    if long:
      print('<h2>' + tr.translate( 'Description' ) + '</h2><blockquote>', file=f)
      print(long, file=f)
      print('</blockquote>', file=f)

    try:
      signature = getProcessInstance( processInfo.id ).signature
    except ValidationError:
      signature = getProcess(processInfo.id, ignoreValidation=True).signature
    signature = signature.items()

    def param_type_descr(param_type):
      ti = param_type.typeInfo( tr )
      descr = ti[0][1]
      if isinstance( param_type, ReadDiskItem ):
        if param_type.type is None:
          type = 'Any type'
        else:
          type = param_type.type.name
        typeFileName = type.replace( '/', '_' )
        typeHTML = os.path.join( neuroConfig.mainDocPath, 'ontology-' + ontology, l, 'types', typeFileName + '.html' )
        descr = '<a href="' + htmlEscape( relative_path( typeHTML, os.path.dirname( f.name ) ) ) + '">' + descr + '</a>'
      elif isinstance(param_type, ListOf):
        subtype = param_type.contentType
        descr = _t_('ListOf') + '( ' + param_type_descr(subtype) + ' )'
      return descr

    supportedFormats = []
    if signature:
      # Parameters
      p = d.get( 'parameters', {} )
      print('<h2>' + tr.translate('Parameters') + '</h2>', file=f)
      for i, j in signature:
        ti = j.typeInfo( tr )
        descr = p.get( i, '' )
        descr = convertSpecialLinks( descr, l , '', tr )
        descr = XHTML.html( descr )
        if not descr and l != 'en':
          descr = XHTML.html( pen.get( i, '' ) )
        type_descr = param_type_descr(j)
        print('<blockquote><b>' + i + '</b>: ' + type_descr, file=f)
        f.write( '<i> ( ' )
        if not j.mandatory:
          f.write( _t_( 'optional, ' ) )
        try:
          if len( ti ) > 1:
            k, access = ti[ 1 ]
          else:
            access = _t_( 'input' )
          f.write( access )
        except context.UserInterruption:
          raise
        except Exception as e:
          print(e)
        f.write( ' )</i>' )
        print('<blockquote>', file=f)
        print(descr, file=f)
        print('</blockquote></blockquote>', file=f)

        try:
          if len( ti ) > 2:
            supportedFormats.append( ( i, ti[2][1] ) )
        except context.UserInterruption:
          raise
        except Exception as e:
          print(e)

    # Technical information
    print('<h2>' + tr.translate( 'Technical information' )
          + '</h2><blockquote>', file=f)
    print('<p><em>' + tr.translate( 'Toolbox' ) + ' : </em>'
          + unicode(tr.translate(get_toolbox_name(processInfo.toolbox)))
          + '</p>', file=f)
    print('<p><em>' + tr.translate( 'User level' ) + ' : </em>'
          + unicode(processInfo.userLevel) + '</p>', file=f)
    print('<p><em>' + tr.translate( 'Identifier' ) + ' : </em><code>'
          + processInfo.id + '</code></p>', file=f)
    processFileRef=relative_path(processInfo.fileName, os.path.dirname(htmlFileName))
    processFileName=relative_path(processInfo.fileName, os.path.dirname(neuroConfig.mainPath))
    print('<p><em>' + tr.translate( 'File name' )
          + ' : </em><nobr><code><a href="'+processFileRef+'">'
          + processFileName + '</a></code></nobr></p>', file=f)

    if supportedFormats:
      print('<p><em>' + tr.translate( 'Supported file formats' ) + ' : </em>',
            file=f)
      try:
        for parameter, formats in supportedFormats:
          print('<blockquote>', parameter, ':<blockquote>', formats,
                '</blockquote>', '</blockquote>', file=f)
      except context.UserInterruption:
        raise
      except Exception as e:
        print(e)
      print('</p>', file=f)
    print('</blockquote>', file=f)

    print('</body></html>', file=f)
    f.close()

#----------------------------------------------------------------------------
def generateHTMLProcessesDocumentation( context, ontology ):
  import sys
  
  #--------------------------------------
  # Generate translators
  #--------------------------------------
  translators = {}
  for l in neuroConfig._languages:
    translators[ l ] = neuroConfig.Translator( l )
  #--------------------------------------
  # Generate documentation for processes
  #--------------------------------------
  for pi in allProcessesInfo():
    try:
      generateHTMLDocumentation( pi, translators, context, ontology )
    except context.UserInterruption:
      raise
    except ValidationError:
      pass
    except:
      context.showException( beforeError=_t_('Cannot generate documentation for <em>%s</em>') % (pi.fileName,) )

  #---------------------------------------
  # Generate documentation for categories
  #---------------------------------------
  # Find all category_documentation.minf files in
  # the order of neuroConfig.processesPath
  categoryDocFiles = {}
  for procPath in neuroConfig.processesPath:
    stack = [ '' ]
    while stack:
      r = stack.pop()
      f = os.path.join( procPath, r )
      if os.path.basename( r ) == 'category_documentation.minf':
        category = os.path.dirname(r).lower()
        if category:
          categoryDocFiles.setdefault( category, f )
      elif os.path.isdir( f ):
        stack += [ os.path.join( r, c ) for c in os.listdir( f ) ]
  
  # Find documentation files in toolboxes
  # processes are in toolboxesDir/toolboxName/processes by default. anyway they are in toolbox.processesDir
  # each relative directory dir in processes, matches a category named toolboxName/dir
  # a documentation for the toolbox may be in toolboxesDir/toolboxId
  
  from brainvisa.toolboxes import allToolboxes
  for toolbox in allToolboxes():
    # search for a file category_documentation.minf in toolboxesDir/toolboxId, otherwise it can be in processesDir
    # It is usefull for my processes toolbox because the toolbox and the processes are not in the same place and the documentation of the toolbox cannot be in the processes directory. 
    toolboxDoc=os.path.join( neuroConfig.toolboxesDir, toolbox.id, "category_documentation.minf")
    if os.path.exists(toolboxDoc): # if it exists, add it to the doc file for which we have to generate an html file
        categoryDocFiles.setdefault( toolbox.id, toolboxDoc )
    # search for category documentation files in processes directory
    stack = [('', toolbox.id)] # relative directory, category name
    while stack:
      r, cat = stack.pop() # get current relative path and associated category
      f=os.path.join(toolbox.processesDir, r)
      currentItem=os.path.basename( r )
      if currentItem == 'category_documentation.minf':
          categoryDocFiles.setdefault( cat, f )
      elif os.path.isdir( f ):
        if currentItem:
          cat=os.path.join(cat, currentItem.lower())
        stack += [ (os.path.join( r, c ), cat) for c in os.listdir( f ) ]

  # Create category HTML files
  
  baseDocDir = os.path.dirname( neuroConfig.docPath )
  for category, f in six.iteritems(categoryDocFiles):
    categoryPath=category.split("/")
    minfContent = readMinf( f )[ 0 ]
    enContent=minfContent['en']
    for l in neuroConfig._languages:
      #for l, c in six.iteritems(minfContent):
      if l=='en':
        c=enContent
      else:
        c=minfContent.get(l, enContent)
        
      tr = translators.get( l )
      
      c = convertSpecialLinks( c, l , '/'.join( ( '..', ) * (len( categoryPath )+1) ), tr ) # base dir for links : processes
      p = os.path.join( baseDocDir, l, 'processes', 'categories', category )
      if not os.path.isdir( p ):
        os.makedirs( p )
      nsubdirs = len(category.split('/')) + 3
      f = open( os.path.join( p, 'category_documentation.html' ), 'w' )
      print('<html>', file=f)
      print('<head>', file=f)
      print('  <meta http-equiv="Content-Type" content="text/html; charset='
            + sys.getdefaultencoding()+'">', file=f)
      print('  <meta content="BrainVISA ' + neuroConfig.shortVersion
            + '" name="generator">', file=f)
      print('  <link rel="stylesheet" href="' + ('../' * nsubdirs)
            + 'axon.css" media="screen" />', file=f)
      print('</head>', file=f)
      print('<body>', file=f)
      print(XHTML.html( c ), file=f)
      print('</body></html>', file=f)
      f.close()

#----------------------------------------------------------------------------
def get_link_to_documentation(item):
  item_name=item.name
  item_fileName = item_name.replace( '/', '_' )
  item_escaped = htmlEscape( item_name )
  return '<a href="' + htmlEscape( item_fileName ) + '.html">' + item_escaped + '</a><br/>'

def get_toolbox_name(toolbox_id):
  toolbox = getToolbox(toolbox_id)
  if toolbox:
    name= toolbox.name
  else:
    name = toolbox_id
  if name is None:
    name = '&lt;unnamed toolbox&gt;'
  return name
  
def nameKey(x):
  return x.name.lower()

#----------------------------------------------------------------------------
def execution( self, context ):
  generateHTMLProcessesDocumentation( context, "all" )
  # Ontology documentation for each language
  # directory ontology-all
  ontologyDirectory=os.path.join( neuroConfig.mainDocPath, 'ontology-all')
  # directory ontology-all/en and ontology-all/fr
  for l in neuroConfig._languages:
    htmlDirectory=os.path.join( ontologyDirectory, l )
    if not os.path.exists( htmlDirectory ):
      os.makedirs( htmlDirectory )
  
  # collect information about types and formats
  allFormats=sorted(getAllFormats(), key=nameKey)
  allTypes=sorted(getAllDiskItemTypes(), key=nameKey)
  processesByTypes = {}
  typesByFormats = {}
  formatsByTypes = {}
  processesByFormats = {}
  typesByToolboxes = {}
  formatsByToolboxes = {}
  for t in allTypes:
    typesByToolboxes.setdefault(t.toolbox, []).append(t)
    if isinstance(t.formats, NamedFormatList):
      f=t.formats.name
      formatsByTypes.setdefault( t.name, set() ).add( f )
      typesByFormats.setdefault( f, set() ).add( t.name )
    elif t.formats:
      for format in t.formats:
        f=format.name
        formatsByTypes.setdefault( t.name, set() ).add( f )
        typesByFormats.setdefault( f, set() ).add( t.name )
  for f in allFormats:
    if not isinstance(f.toolbox, basestring):
      context.warning('bad toolbox %s in format: %s'
        % (repr(f.toolbox), repr(f)))
      continue
    formatsByToolboxes.setdefault(f.toolbox, []).append(f)

  # get information about links between processes, types and formats
  for pi in allProcessesInfo():
    try:
      process = getProcessInstance(pi.id)
    except context.UserInterruption:
      raise
    except ValidationError:
      continue
    except:
      context.showException()
      #context.error( exceptionHTML() )
      continue
    processTypes = set()
    processId=process.id()
    for param in six.itervalues(process.signature):
      if isinstance( param, ReadDiskItem ):
        t=param.type.name
        processesByTypes.setdefault( t, set() ).add( pi )
        if isinstance(param.formats, NamedFormatList):
          f=param.formats.name
          formatsByTypes.setdefault( t, set() ).add( f )
          typesByFormats.setdefault( f, set() ).add( t )
          processesByFormats.setdefault( f, set() ).add( pi )
        elif param.formats:
          for format in param.formats:
            f=format.name
            formatsByTypes.setdefault( t, set() ).add( f )
            typesByFormats.setdefault( f, set() ).add( t )
            processesByFormats.setdefault( f, set() ).add( pi )
  
  # create a temporary database for each ontology to get ontology rules
  tmpDatabase = context.temporary( 'Directory' )
  ontologies=sorted(FileSystemOntology.getOntologiesNames())
  databases=[]
  for ontology in ontologies:  
    database = SQLDatabase( ':memory:', tmpDatabase.fullPath(), fso=ontology )
    databases.append(database)
  
  
  if distutils.spawn.find_executable('dot') is None:
    self.write_graphs=False
    context.warning('Cannot find dot executable. Inheritance graphs won\'t be written.' )

  # collect information about types inheritance, ontology rules and key attributes
  typeRules = {}
  typeParent = {}
  typeChildren = {}
  typeKeys = {}
  stack = list( allTypes )
  while stack:
    type = stack.pop( 0 )
    if self.write_graphs:
      parentType = type.parent
      if parentType is not None:
        typeParent[ type.name ] = parentType.name
        typeChildren.setdefault( parentType.name, set() ).add( type.name )
    # get ontology rules
    typeRules[type.name]={}
    typeKeys[type.name]={}
    for database in databases:
      rules=database.fso.typeToPatterns.get(type, None)
      if rules:
        typeRules[type.name][database.fso.name]=rules
      keys=database.getTypesKeysAttributes(type.name)
      if keys:
        typeKeys[type.name][database.fso.name]=keys
  
  # Create types inheritance graphs (dot format)
  if self.write_graphs:
    imagesDirectory=os.path.join( ontologyDirectory, 'images' )
    if not os.path.exists( imagesDirectory ):
      os.mkdir( imagesDirectory )
    tmpDot = os.path.join( tmpDatabase.fullPath(), 'tmp.dot' )
    for diskItemType in allTypes :
      type=diskItemType.name
      typeFileName = type.replace( '/', '_' )
      
      context.write( '<font></font>Generate inheritance graph for type ', htmlEscape(type) +
        '<br/>' )
      
      dot = open( tmpDot, 'w' )
      tmpMap = os.path.join( tmpDatabase.fullPath(), typeFileName+'_map.html' )
  
      print('digraph "' + typeFileName + ' inheritance" {', file=dot)
      print('  node [style=filled,shape=box];', file=dot)
      print('  "' + type  + '" [color=orange];', file=dot)
      previous = type
      parent = typeParent.get( type )
      while parent:
        print('  "' + parent  + '" [URL="'
              + htmlEscape(parent.replace('/', '_')) + '.html"];', file=dot)
        print('  "' + parent + '" -> "' + previous + '";', file=dot)
        previous = parent
        parent = typeParent.get( parent )
      stack = [ ( type, typeChildren.get( type, () ) ) ]
      while stack:
        t, children = stack.pop( 0 )
        for c in children:
          print('  "' + c  + '" [URL="' + htmlEscape( c.replace( '/', '_' ) )
                + '.html"];', file=dot)
          print('  "' + t + '" -> "' + c + '";', file=dot)
          stack.append( ( c, typeChildren.get( c, () ) ) )
      print('}', file=dot)
      dot.close()
      try:
        context.system( 'dot', '-Tpng', '-o' + os.path.join( imagesDirectory, typeFileName + '_inheritance.png' ), '-Tcmapx', '-o' + tmpMap, tmpDot )
      except context.UserInterruption:
        raise
      except:
        context.warning("Cannot generate inheritance graph, the dot command failed.")
  
  # Create documentation files for types and formats and index files
  # LANGUAGES
  for l in neuroConfig._languages:
    context.write( '<p><b>Generate HTML for language ', l, "</b></p>" )
    # INDEX.HTML
    htmlDirectory=os.path.join( ontologyDirectory, l )
    index = open( os.path.join( htmlDirectory, 'index.html' ), 'w' )
    print('''<html>
<head>
  <title>Data types and formats in BrainVISA ontologies</title>
  <link rel="stylesheet" href="../../axon.css" media="screen" />
</head>
<body>
  <center><h1>Data types and formats in BrainVISA ontologies</h1></center>''',
        file=index)
    print('<a href="types/index.html">All Data types</a><br>', file=index)
    print('<a href="types/index_toolboxes.html">Data types per toolbox</a><br>', file=index)
    print('<a href="types/index_ontologies.html">Data types per ontology</a><br><br>', file=index)
    print('<a href="formats/index.html">All Formats</a><br>', file=index)
    print('<a href="formats/index_toolboxes.html">Formats per toolbox</a>',
          file=index)
    print("</body></html>", file=index)
    index.close()
    
    # TYPES
    typesDirectory=os.path.join( htmlDirectory, 'types' )
    formatsDirectory=os.path.join( htmlDirectory, 'formats' )
    if not os.path.exists( typesDirectory ):
      os.mkdir( typesDirectory )
      
    return_to_index=htmlEscape( relative_path( index.name,  typesDirectory) )

    # types per toolbox index
    types_toolboxes = open( os.path.join( typesDirectory, 'index_toolboxes.html' ), 'w' )  
    print('''<html>
<head>
  <title>Data types per toolbox</title>
  <link rel="stylesheet" href="../../../axon.css" media="screen" />
</head>
<body>
  <center><h1>Data types per toolbox</h1></center>''', file=types_toolboxes)
    print('<p><a href="'+return_to_index+'">Return to index</a></p>',
          file=types_toolboxes)
    for toolbox in sorted(typesByToolboxes.keys()):
      if toolbox is not None:
        print('<a href=\'#toolbox_'+toolbox+'\'>', get_toolbox_name(toolbox),
              '</a><br/>', file=types_toolboxes)
    for toolbox in sorted(typesByToolboxes.keys()):
      if toolbox is not None:
        print('<a name=\'toolbox_'+toolbox+'\'/><h2>',
              get_toolbox_name(toolbox), '</h2>', file=types_toolboxes)
        for diskItemType in typesByToolboxes.get(toolbox, []):
          print(get_link_to_documentation(diskItemType), file=types_toolboxes)
    print('</body></html>', file=types_toolboxes)
    types_toolboxes.close()

      
    # types per ontology index
    types_ontologies = open( os.path.join( typesDirectory, 'index_ontologies.html' ), 'w' )  
    print('''<html>
<head>
  <title>Data types per ontology</title>
  <link rel="stylesheet" href="../../../axon.css" media="screen" />
</head>
<body>
  <center><h1>Data types per ontology</h1></center>''', file=types_ontologies)
    print('<p><a href="'+return_to_index+'">Return to index</a></p>',
          file=types_ontologies)
    ontologies.insert(0, "")
    for ont in ontologies:
      if ont == "":
        print(types_ontologies, "<a href='#ont'>Common types</a><br/>",
              file=types_ontologies)
      else:
        print(types_ontologies, '<a href=\'#ont_'+ont+'\'>', ont,
              'ontology</a><br/>', file=types_ontologies)
    for ontology in ontologies:
      if ontology == "":
        print(types_ontologies, "<a name='ont'/><h2>Common types</h2>",
              file=types_ontologies)
      else:
        print('<a name=\'ont_'+ontology+'\'/><h2>', ontology, ' ontology</h2>',
              file=types_ontologies)
      for diskItemType in allTypes:
         if ( ((ontology == "") and (typeRules.get( diskItemType.name ) == {})) or
              (typeRules.get(diskItemType.name).get(ontology, None) is not None) ) :
          print(get_link_to_documentation(diskItemType), file=types_ontologies)
    print('</body></html>', file=types_ontologies)
    types_ontologies.close()

    # All types index + documentation file for each type
    types = open( os.path.join( typesDirectory, 'index.html' ), 'w' )
    print('''<html>
<head>
  <title>Data types in BrainVISA</title>
  <link rel="stylesheet" href="../../../axon.css" media="screen" />
</head>
<body>
  <center><h1>Data types in BrainVISA</h1></center>''', file=types)
    print('<p><a href="'+return_to_index+'">Return to index</a></p>',
           file=types)
    count = 0
    for diskItemType in allTypes :
      type=diskItemType.name
      count += 1
      typeFileName = type.replace( '/', '_' )
      htmlFileName = os.path.join( typesDirectory, typeFileName + '.html' )
      typeHTML = open( htmlFileName, 'w' )
      typeEscaped = htmlEscape( type )
      context.write( '<font></font>Generate HTML for type', typeEscaped, '( ' + str( count ) + ' / ' + str( len( allTypes ) ) + ' )<br/>' )
      print('<a href="' + htmlEscape( typeFileName ) + '.html">'
            + typeEscaped + '</a><br/>', file=types)
      
      # documentation file for the type
      print('''<html>
<head>
  <title>''' + typeEscaped + '''</title>
  <link rel="stylesheet" href="../../../axon.css" media="screen" />
</head>
<body>
  <center><h1>''' + typeEscaped +'</h1></center>', file=typeHTML)
      href=htmlEscape( relative_path( index.name, os.path.dirname( typeHTML.name ) ) )
      print('<p><a href="'+href+'">Return to index</a></p>', file=typeHTML)

      if self.write_graphs:
        print('<h2>Inheritance graph</h2>', file=typeHTML)
        src=htmlEscape( relative_path( os.path.join( imagesDirectory, typeFileName + '_inheritance.png'), os.path.dirname( typeHTML.name ) ) )
        print('<center><img src="' +src + '" usemap="#'
              + htmlEscape(typeFileName) + ' inheritance"/></center>',
              file=typeHTML)
        graphmap = os.path.join( tmpDatabase.fullPath(),
          typeFileName+'_map.html' )
        if os.path.exists( graphmap ):
          print(open( graphmap ).read(), file=typeHTML)
        else:
          print('<em>(no documentation for type', typeHTML.name,
                ')</em>', file=typeHTML)

      typeFileRef=relative_path(diskItemType.fileName, os.path.dirname(htmlFileName))
      typeFileName=relative_path(diskItemType.fileName, os.path.dirname(neuroConfig.mainPath))
      print('<p><em>Defined in file : </em><nobr><code><a href="'
            + typeFileRef+'">' + typeFileName + '</a></code></nobr></p>',
            file=typeHTML)

      print('<h2>Used in the following processes</h2><blockquote>',
            file=typeHTML)
      processes=sorted(processesByTypes.get( type, () ), key=nameKey)
      for pi in processes:
        try:
          href = htmlEscape( relative_path( getHTMLFileName( pi.id, language=l ), os.path.dirname( typeHTML.name ) ) )
          print('<a href="' + href + '">' + htmlEscape( pi.name )
                + '</a><br/>', file=typeHTML)
        except context.UserInterruption:
          raise
        except Exception as e:
          context.showException(
            beforeError=_t_( 'error in process doc for: ' )+' <b>%s</b> (%s)' \
            % ( pi.id, pi.name ) )
      print('</blockquote>', file=typeHTML)

      print('<h2>Associated formats</h2><blockquote>', file=typeHTML)
      for f in sorted(formatsByTypes.get( type, () ), key=str.lower ):
        formatFileName = f.replace( '/', '_' )
        href = htmlEscape( relative_path( os.path.join( formatsDirectory, formatFileName + '.html' ), os.path.dirname( typeHTML.name ) ) )
        print('<a href="' + href + '">' + htmlEscape( f ) + '</a><br/>',
              file=typeHTML)
      print('</blockquote>', file=typeHTML)

      print('<h2>Associated ontology rules</h2>', file=typeHTML)
      ontRules = typeRules.get( type, {} )
      for ont, rules in ontRules.items():  
        print("<li><b>", ont, "</b>:</li><blockquote>", file=typeHTML)
        for rule in rules:
          print(htmlEscape(rule.pattern.pattern), "<br/>", file=typeHTML)
        print('</blockquote>', file=typeHTML)

      print('<h2>Key attributes</h2>', file=typeHTML)
      ontKeys=typeKeys.get( type, {} )
      for ont, keys in ontKeys.items():
        if keys:
          print("<li><b>", ont, "</b>:</li><blockquote>", file=typeHTML)
          print(htmlEscape(keys[0]), file=typeHTML)
          for key in keys[1:]:
            print(",&nbsp;", htmlEscape(key), file=typeHTML)
          print('</blockquote>', file=typeHTML)

      print('</body></html>', file=typeHTML)
      typeHTML.close()
      
  
    # FORMATS
    if not os.path.exists( formatsDirectory ):
      os.mkdir( formatsDirectory )
    
    formats_toolboxes=open(os.path.join( formatsDirectory, 'index_toolboxes.html' ), 'w')
    print('''<html>
<head>
  <title>Formats per toolbox</title>
  <link rel="stylesheet" href="../../../axon.css" media="screen" />
</head>
<body>
  <center><h1> Formats per toolbox </h1></center>''', file=formats_toolboxes)
    print('<p><a href="'+return_to_index+'">Return to index</a></p>',
          file=formats_toolboxes)
    for toolbox in sorted(formatsByToolboxes.keys()):
      context.write('toolbox: ', repr(toolbox))
      print('<a href=\'#toolbox_'+toolbox+'\'>', get_toolbox_name(toolbox),
            '</a><br/>', file=formats_toolboxes)
    for toolbox in sorted(formatsByToolboxes.keys()):
      print('<a name=\'toolbox_'+toolbox+'\'/><h2>', get_toolbox_name(toolbox),
            '</h2>', file=formats_toolboxes)
      for diskItemFormat in formatsByToolboxes.get(toolbox, []):
        print(get_link_to_documentation(diskItemFormat),
              file=formats_toolboxes)
    print('</body></html>', file=formats_toolboxes)
    formats_toolboxes.close()


    formatsFileName=os.path.join( formatsDirectory, 'index.html' )
    formats = open( formatsFileName, 'w' )
    print('''<html>
<head>
  <title>Formats in BrainVISA</title>
  <link rel="stylesheet" href="../../../axon.css" media="screen" />
</head>
<body>
  <center><h1> Formats in BrainVISA </h1></center>''', fileformats)
    print('<p><a href="'+return_to_index+'">Return to index</a></p>',
          file=formats)
    print('<a href="#all_formats">All formats</a><br>', file=formats)
    print('<a href="#formats_lists">Formats lists</a><br>', file=formats)
    print('<a name=\'all_formats\'/><h2>All formats</h2>', file=formats)
    for format in allFormats :
      formatFileName = format.name.replace( '/', '_' )
      htmlFileName = os.path.join( formatsDirectory, formatFileName + '.html' )
      formatHTML = open( htmlFileName, 'w' )
      formatEscaped = htmlEscape( format.name )
      context.write( '<font></font>Generate HTML for format ', formatEscaped, '<br/>' )
      print('<a href="' + htmlEscape( formatFileName ) + '.html">'
            + formatEscaped + '</a><br/>', file=formats)
      print('''<html>
<head>
  <title>''' + formatEscaped + '''</title>
  <link rel="stylesheet" href="../../../axon.css" media="screen" />
</head>
<body>
  <center><h1>''' + formatEscaped +'</h1></center>', file=formats)
      href=htmlEscape( relative_path( index.name, os.path.dirname( formatHTML.name ) ) )
      print('<p><a href="'+href+'">Return to index</a></p>', file=formatHTML)

      print('<h2>Files patterns</h2><blockquote>', file=formatHTML)
      patterns=""
      for p in format.getPatterns().patterns:
        if patterns:
          patterns+=", "+p.pattern
        else:
          patterns="<b>"+p.pattern+"</b>"
      print(patterns, "</blockquote>", file=formatHTML)

      formatFileRef=relative_path(format.fileName, os.path.dirname(htmlFileName))
      formatFileName=relative_path(format.fileName, os.path.dirname(neuroConfig.mainPath))
      print('<p><em>Defined in file: </em><nobr><code><a href="'
            + formatFileRef+'">' + formatFileName + '</a></code></nobr></p>',
            file=formatHTML)

      print('<h2>Used in the following processes</h2><blockquote>',
            file=formatHTML)
      processes=sorted(processesByFormats.get( format.name, () ), key=nameKey)
      for pi in processes:
        try:
          href = htmlEscape( relative_path( getHTMLFileName( pi.id, language=l  ), os.path.dirname( formatHTML.name ) ) )
          print('<a href="' + href + '">'
                + htmlEscape( pi.name ) + '</a><br/>', file=formatHTML)
        except context.UserInterruption:
          raise
        except Exception as e:
          context.showException(
            beforeError=_t_( 'error in process doc for:' )+' <b>%s</b> (%s)' \
            % ( pi.id, pi.name ) )
      print('</blockquote>', file=formatHTML)
      
      print('<h2>Associated types</h2><blockquote>', file=formatHTML)
      for t in sorted(typesByFormats.get( format.name, () ), key=str.lower):
        typeFileName = t.replace( '/', '_' )
        href = htmlEscape( relative_path( os.path.join( typesDirectory, typeFileName + '.html' ), os.path.dirname( formatHTML.name ) ) )
        print('<a href="' + href + '">' + htmlEscape( t ) + '</a><br/>',
              file=formatHTML)
      print('</blockquote>', file=formatHTML)

      print('</body></html>', file=formatHTML)
      formatHTML.close()

  
    # FORMATS LISTS
    print('<h2><a name="formats_lists"/>Formats Lists in BrainVISA</h2>',
          file=formats)
    
    for listName, format in sorted( formatLists.items() ):
      formatFileName = format.name.replace( '/', '_' )
      htmlFileName = os.path.join( formatsDirectory, formatFileName + '.html' )
      formatHTML = open( htmlFileName, 'w' )
      formatEscaped = htmlEscape( format.name )
      context.write( '<font></font>Generate HTML for format', formatEscaped, '<br/>' )
      print('<a href="' + htmlEscape( formatFileName ) + '.html">' + formatEscaped + '</a><br/>', file=formats)
      print('''<html>
<head>
  <title>''' + formatEscaped
        + '''</title>
  <link rel="stylesheet" href="../../../axon.css" media="screen" />
</head>
<body>
  <center><h1>''' + formatEscaped +'</h1></center>', file=formatHTML)
      href=htmlEscape( relative_path( index.name, os.path.dirname( formatHTML.name ) ) )
      print('<p><a href="'+href+'">Return to index</a></p>', file=formatHTML)

      print('<h2>Formats</h2><blockquote>', file=formatHTML)
      for f in format:
        fname=f.name.replace( "/", "_" )
        print("<a href='" + htmlEscape(fname) + ".html'>", f.name, "</a><br/>",
              file=formatHTML)
      print("</blockquote>", file=formatHTML)

      formatFileRef=relative_path(format.fileName, os.path.dirname(htmlFileName))
      formatFileName=relative_path(format.fileName, os.path.dirname(neuroConfig.mainPath))
      print('<p><em>Defined in file: </em><nobr><code><a href="'
        + formatFileRef + '">' + formatFileName + '</a></code></nobr></p>',
        file=formatHTML)

      print('<h2>Used in the following processes</h2><blockquote>',
            file=formatHTML)
      processes=sorted(processesByFormats.get( format.name, () ), key=nameKey)
      for pi in processes:
        href = htmlEscape( relative_path( getHTMLFileName( pi.id, language=l  ), os.path.dirname( formatHTML.name ) ) )
        print('<a href="' + href + '">' + htmlEscape( pi.name ) + '</a><br/>',
              file=formatHTML)
      print('</blockquote>', file=formatHTML)
      
      print('<h2>Associated types</h2><blockquote>', file=formatHTML)
      for t in sorted(typesByFormats.get( format.name, () ), key=str.lower):
        typeFileName = t.replace( '/', '_' )
        href = htmlEscape( relative_path( os.path.join( typesDirectory, typeFileName + '.html' ), os.path.dirname( formatHTML.name ) ) )
        print('<a href="' + href + '">' + htmlEscape( t ) + '</a><br/>',
              file=formatHTML)
      print('</blockquote>', file=formatHTML)

      print('</body></html>', file=formatHTML)
      formatHTML.close()
  
    print('</body></html>', file=formats)
    formats.close()

  for database in databases:
    database.currentThreadCleanup()
