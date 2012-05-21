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
from brainvisa.processes import *
from brainvisa.configuration import neuroConfig
from brainvisa.data.sqlFSODatabase import SQLDatabase
from soma.path import relative_path
from brainvisa.toolboxes import getToolbox
from brainvisa.data.fileSystemOntology import FileSystemOntology
import subprocess

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
    print >> f, '<html>'
    print >> f, '<head>'
    print >> f, '<title>' + tr.translate( processInfo.name ) + '</title>'
    # unicode strings written in this file are encoded using default encoding
    # to choose a different encoding, unicode_string.encode("encoding") should be used
    # in Brainvisa, the default encoding is set at initilization using sys.setdefaultencoding in neuro.py
    print >> f, '<meta http-equiv="Content-Type" content="text/html; charset='+sys.getdefaultencoding()+'">'
    print >> f, '<meta content="BrainVISA ' + neuroConfig.shortVersion + '" name="generator">'
    print >> f, '</head>'
    print >> f, '<body>'
    print >> f, '<h1><a href="bvshowprocess://' + processInfo.id \
      + '"><img src="../../images/icons/icon_process.png" border="0"></a>'
    print >> f, '<a name="bv_process%' + processInfo.id + '">' + tr.translate( processInfo.name ) + '</a></h1>'
    print >> f, '<blockquote>'
    short = d.get( 'short' )
    if short:
      short = convertSpecialLinks( short, l, '', tr )
      short = XHTML.html( short )
    if not short and l != 'en':
      short = den.get( 'short' )
      if short:
        short = convertSpecialLinks( short, l, '', tr )
        short = XHTML.html( short )
    print >> f, short
    print >> f, '</blockquote>'

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
      print >> f, '<h2>' + tr.translate( 'Description' ) + '</h2><blockquote>'
      print >> f, long
      print >> f, '</blockquote>'

    signature = getProcessInstance( processInfo.id ).signature
    signature = signature.items()

    supportedFormats = []
    if signature:
      # Parameters
      p = d.get( 'parameters', {} )
      print >> f, '<h2>' + tr.translate('Parameters') + '</h2>'
      for i, j in signature:
        ti = j.typeInfo( tr )
        descr = p.get( i, '' )
        descr = convertSpecialLinks( descr, l , '', tr )
        descr = XHTML.html( descr )
        if not descr and l != 'en':
          descr = XHTML.html( pen.get( i, '' ) )
        if isinstance( j, ReadDiskItem ):
          if j.type is None:
            type = 'Any type'
          else:
            type = j.type.name
          typeFileName = type.replace( '/', '_' )
          typeHTML = os.path.join( neuroConfig.mainDocPath, 'ontology-' + ontology, l, 'types', typeFileName + '.html' )
          #context.write( repr(typeHTML), repr(f.name), repr( relative_path( typeHTML, os.path.dirname( f.name ) ) ) )
          a_prefix = '<a href="' + htmlEscape( relative_path( typeHTML, os.path.dirname( f.name ) ) ) + '">'
          a_suffix = '</a>'
        else:
          a_prefix = ''
          a_suffix = ''
        print >> f, '<blockquote><b>' + i + '</b>: ' + a_prefix + ti[0][1] + a_suffix
        f.write( '<i> ( ' )
        if not j.mandatory:
          f.write( _t_( 'optional, ' ) )
        try:
          if len( ti ) > 1:
            k, access = ti[ 1 ]
          else:
            access = _t_( 'input' )
          f.write( access )
        except Exception, e:
          print e
        f.write( ' )</i>' )
        print >> f, '<blockquote>'
        print >> f, descr
        print >> f, '</blockquote></blockquote>'

        try:
          if len( ti ) > 2:
            supportedFormats.append( ( i, ti[2][1] ) )
        except Exception, e:
          print e

    # Technical information
    print >> f, '<h2>' + tr.translate( 'Technical information' ) + '</h2><blockquote>'
    print >> f, '<p><em>' + tr.translate( 'Toolbox' ) + ' : </em>' + unicode( tr.translate(get_toolbox_name(processInfo.toolbox) )) + '</p>'
    print >> f, '<p><em>' + tr.translate( 'User level' ) + ' : </em>' + unicode( processInfo.userLevel ) + '</p>'
    print >> f, '<p><em>' + tr.translate( 'Identifier' ) + ' : </em><code>' + processInfo.id + '</code></p>'
    processFileRef=relative_path(processInfo.fileName, os.path.dirname(htmlFileName))
    processFileName=relative_path(processInfo.fileName, os.path.dirname(neuroConfig.mainPath))
    print >> f, '<p><em>' + tr.translate( 'File name' ) + ' : </em><nobr><code><a href="'+processFileRef+'">' + processFileName + '</a></code></nobr></p>'

    if supportedFormats:
      print >> f, '<p><em>' + tr.translate( 'Supported file formats' ) + ' : </em>'
      try:
        for parameter, formats in supportedFormats:
          print >> f, '<blockquote>', parameter, ':<blockquote>', formats, '</blockquote>', '</blockquote>'
      except Exception, e:
        print e
      print >> f, '</p>'
    print >> f, '</blockquote>'

    print >> f, '</body></html>'
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
    except ValidationError:
      pass
    except:
      showException( beforeError=_t_('Cannot generate documentation for <em>%s</em>') % (pi.fileName,) )

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
  for category, f in categoryDocFiles.iteritems():
    categoryPath=category.split("/")
    minfContent = readMinf( f )[ 0 ]
    enContent=minfContent['en']
    for l in neuroConfig._languages:
      #for l, c in minfContent.iteritems():
      if l=='en':
        c=enContent
      else:
        c=minfContent.get(l, enContent)
        
      tr = translators.get( l )
      
      c = convertSpecialLinks( c, l , '/'.join( ( '..', ) * (len( categoryPath )+1) ), tr ) # base dir for links : processes
      p = os.path.join( baseDocDir, l, 'processes', 'categories', category )
      if not os.path.isdir( p ):
        os.makedirs( p )
      f = open( os.path.join( p, 'category_documentation.html' ), 'w' )
      print >> f, '<html>'
      print >> f, '<head>'
      print >> f, '<meta http-equiv="Content-Type" content="text/html; charset='+sys.getdefaultencoding()+'">'
      print >> f, '<meta content="BrainVISA ' + neuroConfig.shortVersion + '" name="generator">'
      print >> f, '</head>'
      print >> f, '<body>'
      print >> f, XHTML.html( c )
      print >> f, '</html></body>'
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
    formatsByToolboxes.setdefault(f.toolbox, []).append(f)
      
  # get information about links between processes, types and formats
  for pi in allProcessesInfo():
    try:
      process = getProcessInstance(pi.id)
    except ValidationError:
      continue
    except:
      showException()
      #context.error( exceptionHTML() )
      continue
    processTypes = set()
    processId=process.id()
    for param in process.signature.itervalues():
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
  
      print >> dot, 'digraph "' + typeFileName + ' inheritance" {'
      print >> dot, '  node [style=filled,shape=box];'
      print >> dot, '  "' + type  + '" [color=orange];'
      previous = type
      parent = typeParent.get( type )
      while parent:
        print >> dot, '  "' + parent  + '" [URL="' + htmlEscape( parent.replace( '/', '_' ) ) + '.html"];'
        print >> dot, '  "' + parent + '" -> "' + previous + '";'
        previous = parent
        parent = typeParent.get( parent )
      stack = [ ( type, typeChildren.get( type, () ) ) ]
      while stack:
        t, children = stack.pop( 0 )
        for c in children:
          print >> dot, '  "' + c  + '" [URL="' + htmlEscape( c.replace( '/', '_' ) ) + '.html"];'
          print >> dot, '  "' + t + '" -> "' + c + '";'
          stack.append( ( c, typeChildren.get( c, () ) ) )
      print >> dot, '}'
      dot.close()
      try:
        context.system( 'dot', '-Tpng', '-o' + os.path.join( imagesDirectory, typeFileName + '_inheritance.png' ), '-Tcmapx', '-o' + tmpMap, tmpDot )
      except:
        context.warning("Cannot generate inheritance graph, the dot command failed.")
  
  # Create documentation files for types and formats and index files
  # LANGUAGES
  for l in neuroConfig._languages:
    context.write( '<p><b>Generate HTML for language ', l, "</b></p>" )
    # INDEX.HTML
    htmlDirectory=os.path.join( ontologyDirectory, l )
    index = open( os.path.join( htmlDirectory, 'index.html' ), 'w' )
    print >> index, '<html>\n<body>\n<center><h1>Data types and formats in BrainVISA ontologies</h1></center>'
    print >> index, '<a href="types/index.html">All Data types</a><br>'
    print >> index, '<a href="types/index_toolboxes.html">Data types per toolbox</a><br>'
    print >> index, '<a href="types/index_ontologies.html">Data types per ontology</a><br><br>'
    print >> index, '<a href="formats/index.html">All Formats</a><br>'
    print >> index, '<a href="formats/index_toolboxes.html">Formats per toolbox</a>'
    print >> index, "</body></html>"
    index.close()
    
    # TYPES
    typesDirectory=os.path.join( htmlDirectory, 'types' )
    formatsDirectory=os.path.join( htmlDirectory, 'formats' )
    if not os.path.exists( typesDirectory ):
      os.mkdir( typesDirectory )
      
    return_to_index=htmlEscape( relative_path( index.name,  typesDirectory) )

    # types per toolbox index
    types_toolboxes = open( os.path.join( typesDirectory, 'index_toolboxes.html' ), 'w' )  
    print >> types_toolboxes, '<html>\n<body>\n<center><h1>Data types per toolbox</h1></center>'
    print >> types_toolboxes, '<p><a href="'+return_to_index+'">Return to index</a></p>'
    for toolbox in sorted(typesByToolboxes.keys()):
      print >> types_toolboxes, '<a href=\'#toolbox_'+toolbox+'\'>', get_toolbox_name(toolbox), '</a><br/>'
    for toolbox in sorted(typesByToolboxes.keys()):
      print >> types_toolboxes, '<a name=\'toolbox_'+toolbox+'\'/><h2>', get_toolbox_name(toolbox), '</h2>'
      for diskItemType in typesByToolboxes.get(toolbox, []):
        print >> types_toolboxes, get_link_to_documentation(diskItemType)
    print >> types_toolboxes, '</body></html>'
    types_toolboxes.close()

      
    # types per ontology index
    types_ontologies = open( os.path.join( typesDirectory, 'index_ontologies.html' ), 'w' )  
    print >> types_ontologies, '<html>\n<body>\n<center><h1>Data types per ontology</h1></center>'
    print >> types_ontologies, '<p><a href="'+return_to_index+'">Return to index</a></p>'
    ontologies.insert(0, "")
    for ont in ontologies:
      if ont == "":
        print >> types_ontologies, "<a href='#ont'>Common types</a><br/>"
      else:
        print >> types_ontologies, '<a href=\'#ont_'+ont+'\'>', ont, 'ontology</a><br/>'
    for ontology in ontologies:
      if ontology == "":
        print >> types_ontologies, "<a name='ont'/><h2>Common types</h2>"
      else:
        print >> types_ontologies, '<a name=\'ont_'+ontology+'\'/><h2>', ontology, ' ontology</h2>'
      for diskItemType in allTypes:
         if ( ((ontology == "") and (typeRules.get( diskItemType.name ) == {})) or
              (typeRules.get(diskItemType.name).get(ontology, None) is not None) ) :
          print >> types_ontologies, get_link_to_documentation(diskItemType)
    print >> types_ontologies, '</body></html>'
    types_ontologies.close()

    # All types index + documentation file for each type
    types = open( os.path.join( typesDirectory, 'index.html' ), 'w' )
    print >> types, '<html>\n<body>\n<center><h1>Data types in BrainVISA</h1></center>'
    print >> types, '<p><a href="'+return_to_index+'">Return to index</a></p>'
    count = 0
    for diskItemType in allTypes :
      type=diskItemType.name
      count += 1
      typeFileName = type.replace( '/', '_' )
      htmlFileName = os.path.join( typesDirectory, typeFileName + '.html' )
      typeHTML = open( htmlFileName, 'w' )
      typeEscaped = htmlEscape( type )
      context.write( '<font></font>Generate HTML for type', typeEscaped, '( ' + str( count ) + ' / ' + str( len( allTypes ) ) + ' )<br/>' )
      print >> types, '<a href="' + htmlEscape( typeFileName ) + '.html">' + typeEscaped + '</a><br/>'
      
      # documentation file for the type
      print >> typeHTML, '<html>\n<body>\n<center><h1>' + typeEscaped +'</h1></center>'
      href=htmlEscape( relative_path( index.name, os.path.dirname( typeHTML.name ) ) )
      print >> typeHTML, '<p><a href="'+href+'">Return to index</a></p>'

      if self.write_graphs:
        print >> typeHTML, '<h2>Inheritance graph</h2>'
        src=htmlEscape( relative_path( os.path.join( imagesDirectory, typeFileName + '_inheritance.png'), os.path.dirname( typeHTML.name ) ) )
        print >> typeHTML, '<center><img src="' +src + '" usemap="#' + htmlEscape(typeFileName) + ' inheritance"/></center>'
        graphmap = os.path.join( tmpDatabase.fullPath(),
          typeFileName+'_map.html' )
        if os.path.exists( graphmap ):
          print >> typeHTML, open( graphmap ).read()
        else:
          print >> typeHTML, '<em>(no documentation for type', typeHTML.name, \
            ')</em>'

      typeFileRef=relative_path(diskItemType.fileName, os.path.dirname(htmlFileName))
      typeFileName=relative_path(diskItemType.fileName, os.path.dirname(neuroConfig.mainPath))
      print >> typeHTML, '<p><em>Defined in file : </em><nobr><code><a href="'+typeFileRef+'">' + typeFileName + '</a></code></nobr></p>'

      print >> typeHTML, '<h2>Used in the following processes</h2><blockquote>'
      processes=sorted(processesByTypes.get( type, () ), key=nameKey)
      for pi in processes:
        href = htmlEscape( relative_path( getHTMLFileName( pi.id, language=l ), os.path.dirname( typeHTML.name ) ) )
        print >> typeHTML, '<a href="' + href + '">' + htmlEscape( pi.name ) + '</a><br/>'
      print >> typeHTML, '</blockquote>'
      
      print >> typeHTML, '<h2>Associated formats</h2><blockquote>'
      for f in sorted(formatsByTypes.get( type, () ), key=str.lower ):
        formatFileName = f.replace( '/', '_' )
        href = htmlEscape( relative_path( os.path.join( formatsDirectory, formatFileName + '.html' ), os.path.dirname( typeHTML.name ) ) )
        print >> typeHTML, '<a href="' + href + '">' + htmlEscape( f ) + '</a><br/>'
      print >> typeHTML, '</blockquote>'
      
      print >> typeHTML, '<h2>Associated ontology rules</h2>'
      ontRules = typeRules.get( type, {} )
      for ont, rules in ontRules.items():  
        print >> typeHTML, "<li><b>", ont, "</b>:</li><blockquote>"
        for rule in rules:
          print >> typeHTML, htmlEscape(rule.pattern.pattern), "<br/>"
        print >> typeHTML, '</blockquote>'
      
      print >> typeHTML, '<h2>Keys attributes</h2>'
      ontKeys=typeKeys.get( type, {} )
      for ont, keys in ontKeys.items():
        if keys:
          print >> typeHTML, "<li><b>", ont, "</b>:</li><blockquote>"
          print >> typeHTML, htmlEscape(keys[0])
          for key in keys[1:]:
            print >> typeHTML, ",&nbsp;", htmlEscape(key)
          print >> typeHTML, '</blockquote>'

      print >> typeHTML, '</body></html>'
      typeHTML.close()
      
  
    # FORMATS
    if not os.path.exists( formatsDirectory ):
      os.mkdir( formatsDirectory )
    
    formats_toolboxes=open(os.path.join( formatsDirectory, 'index_toolboxes.html' ), 'w')
    print >> formats_toolboxes, '<html>\n<body>\n<center><h1> Formats per toolbox </h1></center>'
    print >> formats_toolboxes, '<p><a href="'+return_to_index+'">Return to index</a></p>'
    for toolbox in sorted(formatsByToolboxes.keys()):
      print >> formats_toolboxes, '<a href=\'#toolbox_'+toolbox+'\'>', get_toolbox_name(toolbox), '</a><br/>'
    for toolbox in sorted(formatsByToolboxes.keys()):
      print >> formats_toolboxes, '<a name=\'toolbox_'+toolbox+'\'/><h2>', get_toolbox_name(toolbox), '</h2>'
      for diskItemFormat in formatsByToolboxes.get(toolbox, []):
        print >> formats_toolboxes, get_link_to_documentation(diskItemFormat)
    print >> formats_toolboxes, '</body></html>'
    formats_toolboxes.close()

    
    formatsFileName=os.path.join( formatsDirectory, 'index.html' )
    formats = open( formatsFileName, 'w' )
    print >> formats, '<html>\n<body>\n<center><h1> Formats in BrainVISA </h1></center>'
    print >> formats, '<p><a href="'+return_to_index+'">Return to index</a></p>'
    print >> formats, '<a href="#all_formats">All formats</a><br>'
    print >> formats, '<a href="#formats_lists">Formats lists</a><br>'
    print >> formats, '<a name=\'all_formats\'/><h2>All formats</h2>'
    for format in allFormats :
      formatFileName = format.name.replace( '/', '_' )
      htmlFileName = os.path.join( formatsDirectory, formatFileName + '.html' )
      formatHTML = open( htmlFileName, 'w' )
      formatEscaped = htmlEscape( format.name )
      context.write( '<font></font>Generate HTML for format ', formatEscaped, '<br/>' )
      print >> formats, '<a href="' + htmlEscape( formatFileName ) + '.html">' + formatEscaped + '</a><br/>'
      print >> formatHTML, '<html>\n<body>\n<center><h1>' + formatEscaped +'</h1></center>'
      href=htmlEscape( relative_path( index.name, os.path.dirname( formatHTML.name ) ) )
      print >> formatHTML, '<p><a href="'+href+'">Return to index</a></p>'

      print >> formatHTML, '<h2>Files patterns</h2><blockquote>'
      patterns=""
      for p in format.getPatterns().patterns:
        if patterns:
          patterns+=", "+p.pattern
        else:
          patterns="<b>"+p.pattern+"</b>"
      print >> formatHTML, patterns, "</blockquote>"

      formatFileRef=relative_path(format.fileName, os.path.dirname(htmlFileName))
      formatFileName=relative_path(format.fileName, os.path.dirname(neuroConfig.mainPath))
      print >> formatHTML, '<p><em>Defined in file: </em><nobr><code><a href="'+formatFileRef+'">' + formatFileName + '</a></code></nobr></p>'

      print >> formatHTML, '<h2>Used in the following processes</h2><blockquote>'
      processes=sorted(processesByFormats.get( format.name, () ), key=nameKey)
      for pi in processes:
        href = htmlEscape( relative_path( getHTMLFileName( pi.id, language=l  ), os.path.dirname( formatHTML.name ) ) )
        print >> formatHTML, '<a href="' + href + '">' + htmlEscape( pi.name ) + '</a><br/>'
      print >> formatHTML, '</blockquote>'
      
      print >> formatHTML, '<h2>Associated types</h2><blockquote>'
      for t in sorted(typesByFormats.get( format.name, () ), key=str.lower):
        typeFileName = t.replace( '/', '_' )
        href = htmlEscape( relative_path( os.path.join( typesDirectory, typeFileName + '.html' ), os.path.dirname( formatHTML.name ) ) )
        print >> formatHTML, '<a href="' + href + '">' + htmlEscape( t ) + '</a><br/>'
      print >> formatHTML, '</blockquote>'

      print >> formatHTML, '</body></html>'
      formatHTML.close()

  
    # FORMATS LISTS
    print >> formats, '<h2><a name="formats_lists"/>Formats Lists in BrainVISA</h2>'
    
    for listName, format in sorted( formatLists.items() ):
      formatFileName = format.name.replace( '/', '_' )
      htmlFileName = os.path.join( formatsDirectory, formatFileName + '.html' )
      formatHTML = open( htmlFileName, 'w' )
      formatEscaped = htmlEscape( format.name )
      context.write( '<font></font>Generate HTML for format', formatEscaped, '<br/>' )
      print >> formats, '<a href="' + htmlEscape( formatFileName ) + '.html">' + formatEscaped + '</a><br/>'
      print >> formatHTML, '<html>\n<body>\n<center><h1>' + formatEscaped +'</h1></center>'
      href=htmlEscape( relative_path( index.name, os.path.dirname( formatHTML.name ) ) )
      print >> formatHTML, '<p><a href="'+href+'">Return to index</a></p>'

      print >> formatHTML, '<h2>Formats</h2><blockquote>'
      for f in format:
        fname=f.name.replace( "/", "_" )
        print >> formatHTML, "<a href='" + htmlEscape(fname) + ".html'>", f.name, "</a><br/>"
      print >> formatHTML, "</blockquote>"

      formatFileRef=relative_path(format.fileName, os.path.dirname(htmlFileName))
      formatFileName=relative_path(format.fileName, os.path.dirname(neuroConfig.mainPath))
      print >> formatHTML, '<p><em>Defined in file: </em><nobr><code><a href="'+formatFileRef+'">' + formatFileName + '</a></code></nobr></p>'

      print >> formatHTML, '<h2>Used in the following processes</h2><blockquote>'
      processes=sorted(processesByFormats.get( format.name, () ), key=nameKey)
      for pi in processes:
        href = htmlEscape( relative_path( getHTMLFileName( pi.id, language=l  ), os.path.dirname( formatHTML.name ) ) )
        print >> formatHTML, '<a href="' + href + '">' + htmlEscape( pi.name ) + '</a><br/>'
      print >> formatHTML, '</blockquote>'
      
      print >> formatHTML, '<h2>Associated types</h2><blockquote>'
      for t in sorted(typesByFormats.get( format.name, () ), key=str.lower):
        typeFileName = t.replace( '/', '_' )
        href = htmlEscape( relative_path( os.path.join( typesDirectory, typeFileName + '.html' ), os.path.dirname( formatHTML.name ) ) )
        print >> formatHTML, '<a href="' + href + '">' + htmlEscape( t ) + '</a><br/>'
      print >> formatHTML, '</blockquote>'

      print >> formatHTML, '</body></html>'
      formatHTML.close()
  
    print >> formats, '</body></html>'
    formats.close()

  for database in databases:
    database.currentThreadCleanup()
