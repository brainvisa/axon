from neuroProcesses import *
import neuroConfig
from brainvisa.data.sqlFSODatabase import SQLDatabase
from soma.path import relative_path
from brainvisa.toolboxes import getToolbox

signature = Signature(
  'ontology', Choice( 'brainvisa-3.1.0', 'brainvisa-3.0', 'shared' ),
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
    context.write( 'Generate HTML for process "' + processInfo.name + '"' )
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
    toolbox = getToolbox( processInfo.toolbox )
    if toolbox:
      toolbox = tr.translate( toolbox.name )
    else:
      toolbox = 'brainvisa'
    print >> f, '<p><em>' + tr.translate( 'Toolbox' ) + ' : </em>' + unicode( toolbox ) + '</p>'
    print >> f, '<p><em>' + tr.translate( 'User level' ) + ' : </em>' + unicode( processInfo.userLevel ) + '</p>'
    print >> f, '<p><em>' + tr.translate( 'Identifier' ) + ' : </em><code>' + processInfo.id + '</code></p>'
    print >> f, '<p><em>' + tr.translate( 'File name' ) + ' : </em><nobr><code>' + processInfo.fileName + '</code></nobr></p>'

    if supportedFormats:
      print >> f, '<p><em>' + tr.translate( 'Supported file formats' ) + ' : </em><blockquote>'
      try:
        for parameter, formats in supportedFormats:
          print >> f, parameter + ':<blockquote>', formats, '</blockquote>'
      except Exception, e:
        print e
      print >> f, '</blockquote></p>'
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


def nameKey(x):
  return x.name.lower()
  
def execution( self, context ):
  generateHTMLProcessesDocumentation( context, self.ontology )
  
  # Ontology documentation for each language
  ontologyDirectory=os.path.join( neuroConfig.mainDocPath, 'ontology-' + self.ontology)
  for l in neuroConfig._languages:
    htmlDirectory=os.path.join( ontologyDirectory, l )
    if not os.path.exists( htmlDirectory ):
      os.makedirs( htmlDirectory )
  
  allFormats=sorted(getAllFormats(), key=nameKey)
  allTypes=sorted(getAllDiskItemTypes(), key=nameKey)
  
  processesByTypes = {}
  typesByFormats = {}
  formatsByTypes = {}
  processesByFormats = {}
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
  

  tmpDatabase = context.temporary( 'Directory' )
  database = SQLDatabase( ':memory:', (tmpDatabase.fullPath(),), fso=self.ontology )
  
  # Create types inheritance graphs
  if self.write_graphs:
    imagesDirectory=os.path.join( ontologyDirectory, 'images' )
    if not os.path.exists( imagesDirectory ):
      os.mkdir( imagesDirectory )

    typeParent = {}
    typeChildren = {}
    typeRules = {}
    #stack = list( database.keysByType )
    stack = list( allTypes )
    #allTypes = set( stack )
    while stack:
      type = stack.pop( 0 )
      #allTypes.add( type )
      parentType = type.parent
      if parentType is not None:
        #if parentType not in allTypes:
          #allTypes.add( parentType )
          #stack.append( parentType )
        typeParent[ type.name ] = parentType.name
        typeChildren.setdefault( parentType.name, set() ).add( type.name )
      # get ontology rules
      rules=database.fso.typeToPatterns.get(type, None)
      if rules:
        typeRules[type.name]=rules
    tmpDot = os.path.join( tmpDatabase.fullPath(), 'tmp.dot' )
    for diskItemType in allTypes :
      type=diskItemType.name
      typeFileName = type.replace( '/', '_' )
      
      context.write( 'Generate inheritance graph for type ', htmlEscape(type) )
      
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
      context.system( 'dot', '-Tpng', '-o' + os.path.join( imagesDirectory, typeFileName + '_inheritance.png' ), '-Tcmapx', '-o' + tmpMap, tmpDot )
  
  # LANGUAGES
  for l in neuroConfig._languages:
    context.write( '\nGenerate HTML for language ', l, "\n" )
    # INDEX.HTML
    htmlDirectory=os.path.join( ontologyDirectory, l )
    index = open( os.path.join( htmlDirectory, 'index.html' ), 'w' )
    print >> index, '<html>\n<body>\n<center><h1>' + database.fso.name + '</h1></center><a href="types/index.html">Data types</a><br><a href="formats/index.html">Formats</a>'
  
    # TYPES
    typesDirectory=os.path.join( htmlDirectory, 'types' )
    formatsDirectory=os.path.join( htmlDirectory, 'formats' )
    if not os.path.exists( typesDirectory ):
      os.mkdir( typesDirectory )
    types = open( os.path.join( typesDirectory, 'index.html' ), 'w' )  
    print >> types, '<html>\n<body>\n<center><h1> Datatypes for ontology ' + database.fso.name + '</h1></center>'
    count = 0
    for diskItemType in allTypes :
      type=diskItemType.name
      count += 1
      typeFileName = type.replace( '/', '_' )
      typeHTML = open( os.path.join( typesDirectory, typeFileName + '.html' ), 'w' )
      typeEscaped = htmlEscape( type )
      context.write( 'Generate HTML for type', typeEscaped, '( ' + str( count ) + ' / ' + str( len( allTypes ) ) + ' )' )
      print >> types, '<a href="' + htmlEscape( typeFileName ) + '.html">' + typeEscaped + '</a><br/>'
      print >> typeHTML, '<html>\n<body>\n<center><h1>' + typeEscaped +' (' + database.fso.name + ')</h1></center>'

      if self.write_graphs:
        print >> typeHTML, '<h2>Inheritance graph</h2>'
        src=htmlEscape( relative_path( os.path.join( imagesDirectory, typeFileName + '_inheritance.png'), os.path.dirname( typeHTML.name ) ) )
        print >> typeHTML, '<center><img src="' +src + '" usemap="#' + htmlEscape(typeFileName) + ' inheritance"/></center>'
        print >> typeHTML, open( os.path.join( tmpDatabase.fullPath(), typeFileName+'_map.html' ) ).read()
    
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
      
      print >> typeHTML, '<h2>Associated ontology rules</h2><blockquote>'
      for rule in typeRules.get( type, () ):
        print >> typeHTML, htmlEscape(rule.pattern.pattern), "<br/>"
      print >> typeHTML, '</blockquote>'
      
    #dot = open( tmpDot, 'w' )
    #print >> dot, 'digraph "' + typeFileName + ' dataflow" {'
    #print >> dot, '  node [style=filled,shape=ellipse];'
    #for t in inputTypes:
      #if t in outputTypes:
        #color='orange'
      #else:
        #color='green'
      #print >> dot, '  "' + t  + '" [color=' + color + '];'
    #for t in outputTypes:
      #if t in inputTypes:
        #continue
      #print >> dot, '  "' + t + '" [color=red];'
    #for p in typesProcesses:
      #if p in inPipeline:
        #shape='ellipse'
      #else:
        #shape='box'
      #print >> dot, '  "' + p + '" [shape=' + shape + '];'
    #for i, p in typesInputLinks:
      #if p in inPipeline: continue
      #print >> dot, '  "' + i + '" -> "' + p + '" [color=green];'
    #for p, o in typesOutputLinks:
      #if p in inPipeline: continue
      #print >> dot, '  "' + p + '" -> "' + o + '" [color=red];'
    #print >> dot, '}'
    #dot.close()
    #context.system( 'dot', '-Tpng', '-o' + os.path.join( self.htmlDirectory.fullPath(), 'types', typeFileName + ' dataflow.png' ), '-Tcmapx', '-o' + tmpMap, tmpDot )
    #print >> typeHTML, '<h2>Data flow graph</h2>'
    #print >> typeHTML, '<center><img src="' + htmlEscape( typeFileName ) + ' dataflow.png" usemap="#' + htmlEscape(typeFileName) + ' inheritance"/></center>'
    #print >> typeHTML, open( tmpMap ).read()
      print >> typeHTML, '</body></html>'

    # FORMATS
    if not os.path.exists( formatsDirectory ):
      os.mkdir( formatsDirectory )
    formatsFileName=os.path.join( formatsDirectory, 'index.html' )
    formats = open( formatsFileName, 'w' )
    print >> formats, '<html>\n<body>\n<center><h1> Formats for ontology ' + database.fso.name + '</h1></center>'
    
    for format in allFormats :
      formatFileName = format.name.replace( '/', '_' )
      formatHTML = open( os.path.join( formatsDirectory, formatFileName + '.html' ), 'w' )
      formatEscaped = htmlEscape( format.name )
      context.write( 'Generate HTML for format ', formatEscaped )
      print >> formats, '<a href="' + htmlEscape( formatFileName ) + '.html">' + formatEscaped + '</a><br/>'
      print >> formatHTML, '<html>\n<body>\n<center><h1>' + formatEscaped +'</h1></center>'

      print >> formatHTML, '<h2>Files patterns</h2><blockquote>'
      patterns=""
      for p in format.getPatterns().patterns:
        if patterns:
          patterns+=", "+p.pattern
        else:
          patterns="<b>"+p.pattern+"</b>"
      print >> formatHTML, patterns, "</blockquote>"

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
      
    # FORMATS LISTS
    print >> formats, '<center><h1> Formats Lists for ontology ' + database.fso.name + '</h1></center>'
    
    for listName, format in sorted( formatLists.items() ):
      formatFileName = format.name.replace( '/', '_' )
      formatHTML = open( os.path.join( formatsDirectory, formatFileName + '.html' ), 'w' )
      formatEscaped = htmlEscape( format.name )
      context.write( 'Generate HTML for format', formatEscaped )
      print >> formats, '<a href="' + htmlEscape( formatFileName ) + '.html">' + formatEscaped + '</a><br/>'
      print >> formatHTML, '<html>\n<body>\n<center><h1>' + formatEscaped +'</h1></center>'

      print >> formatHTML, '<h2>Formats</h2><blockquote>'
      for f in format:
        fname=f.name.replace( "/", "_" )
        print >> formatHTML, "<a href='" + htmlEscape(fname) + ".html'>", f.name, "</a><br/>"
      print >> formatHTML, "</blockquote>"

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

  database.currentThreadCleanup()
