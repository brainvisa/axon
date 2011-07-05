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

import traceback, threading, pickle, formatter, htmllib, operator
import inspect, signal, shutil, imp, StringIO, types, copy, weakref
import cPickle, atexit
import string
import distutils.spawn
import os, errno, time, calendar

from soma.sorted_dictionary import SortedDictionary
from soma.functiontools import numberOfParameterRange, hasParameter
from soma.minf.api import readMinf, writeMinf, createMinfWriter, iterateMinf, minfFormat
from soma.minf.xhtml import XHTML
from soma.minf.xml_tags import xhtmlTag
from soma.notification import EditableTree, ObservableSortedDictionary, \
                              ObservableAttributes, Notifier
from soma.minf.api import createMinfWriter, iterateMinf, minfFormat
from soma.html import htmlEscape
from soma.somatime import timeDifferenceToString

from neuroData import *
from neuroDiskItems import *
import neuroConfig
import neuroLog
from neuroException import *
import Scheduler
from brainvisa import matlab
from brainvisa.validation import ValidationError
from brainvisa.debug import debugHere
from brainvisa.data.sqlFSODatabase import Database, NotInDatabaseError
import neuroPopen2

try:
  from remoteProcesses import *
  _neuroDistributedProcesses = True
except Exception, e:
  _neuroDistributedProcesses = False
  neuroDistribException = e

try:
  from backwardCompatibleQt import QProcess
  qprocess = True
except:
  qprocess = False


def neuroDistributedProcesses():
  return _neuroDistributedProcesses and \
  neuroConfig.app.configuration.distributed_execution.\
    allowDistributedExecution \
  and neuroConfig.userLevel >= 2

#----------------------------------------------------------------------------
def pathsplit( path ):
  '''Returns a tuple corresponding to a recursive call to os.path.split
  for example on Unix:
     pathsplit( 'toto/titi/tata' ) == ( 'toto', 'titi', 'tata' )
     pathsplit( '/toto/titi/tata' ) == ( '/', 'toto', 'titi', 'tata' )'''
  if isinstance( path, basestring ):
    if path:
      return pathsplit( ( path, ) )
    else:
      return ()
  else:
    if path[0]:
      d,b = os.path.split( path[0] )
      if b:
        if d:
          return pathsplit( d ) + (b,) + path[1:]
        else:
          return (b,) + path[1:]
      else:
          return (d,) + path[1:]

#----------------------------------------------------------------------------
def getProcdocFileName( processId ):
  processInfo = getProcessInfo( processId )
  fileName = getattr( processInfo, 'fileName', None )
  if fileName is None:
    return None

  newFileName = os.path.join( os.path.dirname( fileName ),
                              processInfo.id + ".procdoc" )
  return newFileName



#----------------------------------------------------------------------------
def readProcdoc( processId ):
  processInfo = getProcessInfo( processId )
  if processInfo is not None:
    procdoc = processInfo.procdoc
    if procdoc is None:
      fileName = getProcdocFileName( processInfo )
      if fileName and os.path.exists( fileName ):
        try:
          procdoc = readMinf( fileName )[ 0 ]
        except:
          print '!Error in!', fileName
          raise
      else:
        procdoc = {}
      processInfo.procdoc = procdoc
  else:
    procdoc = {}
  return procdoc


#----------------------------------------------------------------------------
def writeProcdoc( processId, documentation ):
  fileName = getProcdocFileName( processId )
  if not os.path.exists( fileName ):
    processInfo = getProcessInfo( processId )
    procFileName = getattr( processInfo, 'fileName', None )
    procSourceFileName = os.path.realpath( procFileName )
    # take care of keeping the .procdoc in the same location as the .py,
    # whatever symlinks
    if os.path.islink( procFileName ) and procFileName != procSourceFileName:
      sourceFileName = os.path.join( os.path.dirname( procSourceFileName ),
        os.path.basename( fileName ) )
      os.symlink( sourceFileName, fileName )
      fileName = sourceFileName
  writeMinf( fileName, ( documentation, ) )


#----------------------------------------------------------------------------
def procdocToXHTML( procdoc ):
  stack = [ (procdoc, key, key ) for key in procdoc.iterkeys() ]
  while stack:
    d, k, h = stack.pop()
    value = d[ k ]
    if isinstance( value, types.StringTypes ):
      # Convert HTML tags to XML valid tags

      # Put all tags in lower-case because <TAG> ... </tag> is illegal XML
      def lowerTag( x ):
        result = '<' + x.group(1).lower() + x.group(2)
        return result
      value = re.sub( '<(/?[A-Za-z_][a-zA-Z_0-9]*)(>|[^a-zA-Z_0-9][^>]*>)',
                        lowerTag, value )

      # Add a '/' at the end of non closed tags
      for l in ( 'img', 'br', 'hr' ):
        expr = '<(' + l + '(([^A-Za-z_0-9>/]?)|([^A-Za-z_0-9][^>]*[^/>])))>(?!\s*</' + l + '>)'
        value = re.sub( expr, '<\\1/>', value )

      # convert <s> tag to <xhtml> tag
      value = re.sub( '<(/?)s(>|[^a-zA-Z_0-9][^>]*>)', '<\\1' + xhtmlTag + '\\2', value )

      goOn = True
      while goOn:
        goOn = False
        try:
          newValue = XHTML.buildFromHTML( value )
        except Exception, e:
          # Build a text editor
          editor = QWidgetFactory.create( os.path.join( mainPath, '..', 'python', 'brainvisa', 'textEditor.ui' ), None, None )
          def f( l, c ):
            editor.cursorPosition.setText( str( l+2 ) + ' : ' + str( c ) )
          for x in editor.queryList( None, 'BV_.*' ):
            setattr( editor, x.name()[ 3:], x )
          editor.info.setText( '<h2><font color="red">Error in ' + h + ':<br>  ' + str(e) + '</font></h1>' )
          editor.content.setTextFormat( editor.content.PlainText )
          editor.content.setText( value )
          editor.connect( editor.content, SIGNAL( 'cursorPositionChanged(int,int)' ), f )
          editor.btnOk.setText( 'Check and save as XHTML' )
          editor.btnCancel.setText( 'Save as simple text' )
          line = getattr( e, 'getLineNumber', None )
          if line is not None:
            line = line() - 2
          else:
            line = 0
          column = getattr( e, 'getColumnNumber', None )
          if column is not None:
            column = column()
          else:
            column = 0
          editor.content.setCursorPosition( line, column )
          if editor.exec_loop() == QDialog.Accepted:
            value = unicode( editor.content.text() )
            goOn = True
          else:
            newValue = unicode( editor.content.text() )
            goOn = False
      d[ k ] = newValue
    elif type( value ) is types.DictType:
      stack += [ ( value, key, h + '.' + key ) for key in value.iterkeys() ]


#----------------------------------------------------------------------------
def getHTMLFileName( processId, documentation=None, language=None ):
  processInfo = getProcessInfo( processId )
  if documentation is None:
    documentation = readProcdoc( processId )
  if language is None:
    language = neuroConfig.language
  htmlPath=XHTML.html(documentation.get( 'htmlPath', ''))
  if htmlPath:
    defaultPath=htmlPath
  else:
    defaultPath = os.path.dirname( neuroConfig.docPath )
  return os.path.join( defaultPath, language, 'processes',
                       string.replace( processInfo.id, ' ', '_' ) + '.html' )

#----------------------------------------------------------------------------
def convertSpecialLinks( msg, language, baseForLinks, translator ):
  stack = [ msg ]
  while stack:
    item = stack.pop()
    if isinstance( item, XHTML ):# and \
      stack += item.content
      tag = item.tag
      if not tag: continue
      tag = tag.lower()
      if tag == 'a':
        href = item.attributes.get( 'href' )
        if href is not None:
          i = href.find( '#' )
          if i >= 0:
            postHref = href[ i: ]
            href = href[ :i ]
          else:
            postHref = ''
          if not href: continue
          if href.startswith( 'bvcategory://' ):
            href = href[ 13: ]
            if href.startswith( '/' ):
              href = href[ 1: ]
            if baseForLinks:
              base = baseForLinks + '/categories/'
            else:
              base = 'categories/'
            href = base + href.lower() + '/category_documentation.html'
            item.attributes[ 'href' ] = href + postHref
          elif href.startswith( 'bvprocess://' ):
            href = href[ 12: ]
            if href.startswith( '/' ):
              href = href[ 1: ]
            if baseForLinks:
              href = baseForLinks + '/' + href
            href += '.html'
            item.attributes[ 'href' ] = href + postHref
          elif href.startswith( 'bvimage://' ):
            href = href[ 10: ]
            if href.startswith( '/' ):
              href = href[ 1: ]
            if baseForLinks:
              href = baseForLinks + '/../../images/' + href
            else:
              href = '../../images/' + href
            item.attributes[ 'href' ] = href
      elif tag == 'img':
        src = item.attributes.get( 'src', '' )
        if not src: continue
        elif src.startswith( 'bvimage://' ):
          src = src[ 10: ]
          if src.startswith( '/' ):
            src = src[ 1: ]
          if baseForLinks:
            src = baseForLinks + '/../../images/' + src
          else:
            src = '../../images/' + src
          item.attributes[ 'src' ] = src
      elif tag == '_t_':
        item.tag = None
        item.content = ( translator.translate( item.content[0] ), )
      elif tag == 'bvprocessname':
        item.tag = None
        try:
          n = getProcessInfo( item.attributes[ 'name' ] ).name
        except:
          n = item.attributes[ 'name' ]
        item.content = ( translator.translate( n, ) )
  return msg



#----------------------------------------------------------------------------
def generateHTMLProcessesDocumentation( procId = None ):
  if procId is None:
    defaultContext().runProcess("generateDocumentation")
  else:
    docproc = getProcessInstance( 'generateDocumentation' )
    translators = {}
    for l in neuroConfig._languages:
      translators[ l ] = neuroConfig.Translator( l )
    ontology = docproc.ontology
    docproc.generateHTMLDocumentation( procId, translators, defaultContext(),
      ontology )

#----------------------------------------------------------------------------
class Parameterized( object ):

  def __init__( self, signature ):
    self.__dict__[ 'signature' ] = signature
    self._convertedValues = {}
    self._links = {}
    self._isParameterSet = {}
    self._isDefault = {}
    self._warn = {}
    self.signatureChangeNotifier = Notifier( 1 )
    self.deleteCallbacks = []

    for i, p in self.signature.items():
      np = copy.copy( p )
      self.signature[ i ] = np
      np.copyPostprocessing()
      np.setNameAndParameterized( i, self )

    # Values initialization
    for i, p in self.signature.items():
      self.setValue( i, p.defaultValue() )

    self.initialization()

    # Take into account links set during self.initialization() :
    # call parameterHasChanged for the parameters that have not their default value anymore or that have a not None value
    for name in [n for n, v in self.signature.items() if ( (self.__dict__[n] != v.defaultValue()) or (self.__dict__[n] != None) ) ]:
        self._parameterHasChanged( name, getattr( self, name ) )

  def __del__( self ):
    debugHere()
    for x in self.deleteCallbacks:
      x( self )

  def _parameterHasChanged( self, name, newValue ):
    debug = neuroConfig.debugParametersLinks
    if debug: print >> debug, 'parameter', name, 'changed in', self, 'with value', newValue
    for function in self._warn.get( name, [] ):
      if debug: print >> debug, '  call', function, '(', name, ',', newValue, ')'
      function( self, name, newValue )
    for parameterized, attribute, function, force in self._links.get( name, [] ):
      if parameterized is None:
        if debug: print >> debug, '  call', function, '(', self, ',', self, ')'
        function( self, self )
      else:
        if debug: print >> debug, ' ', name, 'is linked to parameter', attribute, 'of', parameterized
        linkParamType = parameterized.signature[ attribute ]
        if force or parameterized.parameterLinkable( attribute, debug=debug ):
          linkParamDebug = getattr( linkParamType, '_debug', None )
          if linkParamDebug is not None:
            print >> linkParamDebug, 'parameter', name, 'changed in', self, 'with value', newValue
          if force:
            parameterized.setDefault( attribute, self.isDefault( name ) )
          if function is None:
            if debug: print >> debug, '  ' + str(parameterized) + '.setValue(', repr(attribute), ',', newValue,')'
            if linkParamDebug is not None:
              print >> linkParamDebug, '  ==> ' + str(parameterized) + '.setValue(', repr(attribute), ',', newValue,')'
            valueSet = newValue
            parameterized.setValue( attribute, newValue )
          else:
            if debug: print >> debug, '  call', function, '(', self, ',', self, ')'
            if linkParamDebug is not None:
              print >> linkParamDebug, '  ==> call', function, '(', self, ',', self, ')'
            v = function( self, self )
            valueSet=v
            if debug: print >> debug, '  ' + str(parameterized) + '.setValue(', repr(attribute), ',', v,')'
            if linkParamDebug is not None:
              print >> linkParamDebug, '      ' + str(parameterized) + '.setValue(', repr(attribute), ',', v,')'
            parameterized.setValue( attribute, v )
          # activate the notifier with the parameter that receive a linked value and with the new value after evaluation of a link function.
          parameterized.signature[ attribute ].valueLinkedNotifier(
            parameterized, attribute, valueSet )

  def isDefault( self, key ):
    return self._isDefault.get( key, True )

  def setDefault( self, key, value ):
    debug = neuroConfig.debugParametersLinks
    if debug: print >> debug, '    setDefault(', key, ',', value, ')'
    self._isDefault[ key ] = value

  def parameterLinkable( self, key, debug=None ):
    if debug is None:
      debug = neuroConfig.debugParametersLinks
    result= bool( self.signature[ key ].linkParameterWithNonDefaultValue or \
                  self.isDefault( key ) )
    if debug: print >> debug, '    parameterLinkable =', result
    return result

  def initialization( self ):
    pass

  def checkArguments( self ):
    for p, o in self.signature.items():
      o.checkValue( p, getattr( self, p, None ) )

  def findValue( self, attributeName, value ):
    self.setValue( attributeName, value )

  def __setattr__( self, name, value ):
    if self.signature.has_key( name ):
      self.setValue( name, value )
    else:
      self.__dict__[ name ] = value

  def setValue( self, name, value, default=None ):
    debug = neuroConfig.debugParametersLinks
    if debug:
      print >> debug, str(self) + '.setValue(', repr(name), ',', repr(value), ',', repr(default), ')'
    changed = False
    if default is not None:
      changed = self.isDefault( name ) != default
      self.setDefault( name, default )
    if self._isParameterSet.get( name, False ):
      oldValue = getattr( self, name, None )
      newValue = self.signature[ name ].findValue( value )
      changed = changed or newValue != oldValue
    else:
      self._isParameterSet[ name ] = True
      newValue = self.signature[ name ].findValue( value )
      changed = True
    self.__dict__[ name ] =  newValue
    if changed:
      self._parameterHasChanged( name, newValue )

  def linkParameters( self, destName, sources, function = None ):
    if type( sources ) is types.StringType:
      sourcesList = [ sources ]
    else:
      sourcesList = sources
    for p in [ destName ] + list( sourcesList ):
      if not self.signature.has_key( p ):
        raise ValueError( HTMLMessage(_t_( '<em>%s</em> is not a valid parameter name' ) % p) )
    if function is None:
      function = getattr( self.signature[ destName ], 'defaultLinkParametersFunction', None )
    for p in sourcesList:
      self._links.setdefault( p, [] ).append( ( weakref.proxy( self ), destName, function, False ) )

  def addParameterObserver( self, parameterName, function ):
    minimum, maximum = numberOfParameterRange( function )
    if maximum == 0:
      tmp = lambda x, y, z, f=function: f()
      tmp._save_function = function
      function = tmp
    self._warn.setdefault( parameterName, [] ).append( function )

  def removeParameterObserver( self, parameterName, function ):
    l = self._warn.get( parameterName, None )
    if l is not None:
      l.remove( function )
      if not l:
        del self._warn[ parameterName ]

  def setOptional( self, *args ):
    for k in args:
      self.signature[ k ].mandatory = False

  def setConvertedValue( self, name, value ):
    self._convertedValues[ name ] = getattr( self, name )
    self.__dict__[ name ] = value

  def restoreConvertedValues( self ):
    self.__dict__.update( self._convertedValues )
    self._convertedValues.clear()

  def addLink( self, destination, source, function=None ):
    # Parse source
    sources = []
    if type( source ) in ( types.ListType, types.TupleType ):
      for i in source:
        if type( i ) in ( types.ListType, types.TupleType ):
          sources.append( i )
        else:
          sources.append( ( self, i ) )
    else:
      sources.append( ( self, source ) )

    if destination is None:
      destObject, destParameter = ( None, None )
    else:
      destObject, destParameter = ( self, destination )
    # Check if a default function can be provided
    if function is None:
      if len( sources ) == 1:
        function = lambda x: x
      else:
        raise RuntimeError( HTMLMessage(_t_( 'No function provided in <em>addLink</em>' )) )
    multiLink = ExecutionNode.MultiParameterLink( sources, function )
    for sourceObject, sourceParameter in sources:
      sourceObject._links.setdefault( sourceParameter, [] ).append (
        ( destObject, destParameter, multiLink, True ) )



  def removeLink( self, destination, source ):
    # print 'removeLink', self, destination, source
    # Parse source
    sources = []
    if type( source ) in ( types.ListType, types.TupleType ):
      for i in source:
        sources.append( ( self, i ) )
    else:
      sources.append( ( self, source ) )

    if destination is None:
      destObject, destParameter = ( None, None )
    else:
      destObject, destParameter = ( self, destination )

    removed = False
    for sourceObject, sourceParameter in sources:
      l = sourceObject._links.get( sourceParameter, [] )
      if l:
        lbis = l
        l = [i for i in l if ( i[0] is not destObject and i[0] is not weakref.proxy( destObject ) ) or i[1] != destParameter]
        if len( lbis ) != len( l ):
          removed = True
          if l:
            sourceObject._links[ sourceParameter ] = l
          else:
            del sourceObject._links[ sourceParameter ]
        else:
          print 'warning: link not removed:', self, destination, 'from:', source
    return removed


  def changeSignature( self, signature ):
    # Change signature
    self.signature = signature
    for n in self.signature.keys():
      setattr( self, n, getattr( self, n, None ) )

    # Remove unused links
    for n in self._links.keys():
      if not self.signature.has_key( n ):
        del self._links[ n ]
    for n in self._warn.keys():
      if not self.signature.has_key( n ):
        del self._warn[ n ]

    # Notify listeners
    self.signatureChangeNotifier.notify( self )

  def clearLinksTo( self, *args ):
    for i in args:
      if isinstance( i, basestring ):
        destObject,  destParameter = None, i
      else:
        destObject,  destParameter = i
      if destObject:
        do=destObject
      else:
        do= self
      #do = (self if destObject is None else destObject) # not work in python 2.4
      if not do.signature.has_key( destParameter ):
        raise KeyError( _t_( 'Object %(object)s has not parameter "%(param)s"' ) % { 'object': unicode( do ), 'param': destParameter } )
      for k, l in self._links.items():
        i = 0
        while i < len( l ):
          do, dp, ml, f = l[ i ]
          if ( destObject is None or destObject is do ) and \
             destParameter == dp:
            del l[ i ]
          else:
            i += 1

  def clearLinksFrom( self, *args ):
    for k in args:
      if self._links.has_key( k ):
        del self._links[ k ]


  def cleanup( self ):
    debugHere()
    self._convertedValues = {}
    self._links = {}
    self._warn = {}
    self.signatureChangeNotifier = Notifier( 1 )


  def convertStateValue( self, value ):

    if value is not None and not isinstance( value, ( int, float, basestring, list, dict, tuple ) ):
      result = unicode( value )
    elif isinstance( value, list ):
      result = [ self.convertStateValue( itervalue ) for itervalue in value ]
    elif isinstance( value, tuple ):
      result = tuple( self.convertStateValue( itervalue ) for itervalue in value )
    elif isinstance( value, dict ) :
      result = dict( (key, self.convertStateValue( itervalue ) ) for key, itervalue in value.iteritems() )
    else :
      result = value

    return result

  def saveStateInDictionary( self, result=None ):
    if result is None:
      result = {}
    selected = {}
    default = {}
    for n in self.signature.iterkeys():
      value = getattr( self, n, None )
      value = self.convertStateValue( value )

      if self.isDefault( n ):
        default[ n ] = value
      else:
        selected[ n ] = value
    result[ 'parameters' ] =  {
      'selected': selected,
      'default': default,
    }
    return result


#----------------------------------------------------------------------------
class Process( Parameterized ):
  signature = Signature()
  category = 'BrainVISA'
  userLevel = 2

  def __init__( self ):
    # The following attributes can be set in user defined initialization()
    # mathod which is called by Parameterized constructor. Therefore, it
    # must be set before or never.
    self._executionNode = None

    # Copy signature because there is only one instance of each Parameter
    # object in signature for each Process class. This is an old mistake in
    # BrainVISA design, there should be one Signature instance by Process
    # instance.
    Parameterized.__init__( self, self.signature.shallowCopy())

    self._log = None
    self._outputLog = None
    self._outputLogFile = None
    #Main processes are opposed to subprocessed. There is more information
    # displayed to the user on main processes. For example, start/stop
    # notification and time elapsed in process are only displayed on main
    # processes. By default all processes called by another process are not
    # main process. It can be changed by setting isMainProcess to True.
    self.isMainProcess = False
    if hasattr( self.__class__, '_instance' ):
      self.__class__._instance += 1
    else:
      self.__class__._instance = 1
    self.instance = self.__class__._instance

  def __del__( self ):
    Parameterized.__del__( self )

  def _iterate( self, **kwargs ):
    # Find iteration size
    requiredLength = 0
    for values in kwargs.itervalues():
      length = len( values )
      if length > 1:
        if requiredLength > 0 and length > 1 and requiredLength != length:
          raise Exception( _t_( 'all lists of arguments with more than one values must have the same size' ) )
        else:
          requiredLength = length

    # Set lists of values
    finalValues = {}
    for key, values in kwargs.iteritems():
      if values:
        if len( values ) == 1:
          finalValues[ key ] = [ self.signature[ key ].findValue( values[0] ) ] * requiredLength
        else:
          finalValues[ key ] = [ self.signature[ key ].findValue( v ) for v in values ]

    result = []
    for i in xrange( requiredLength ):
      p = self._copy()
      for argumentName, values in finalValues.iteritems():
        p.setValue( argumentName, values[ i ], default=0 )
      result.append( p )
    return result


  def _copy( self ):
    result = self.__class__()
    for ( n, p ) in self.signature.items():
      if not self.isDefault( n ):
#        result.setDefault( n, 0 )
#        setattr( result, n, getattr( self, n ) )
        result.setValue( n, getattr( self, n, None ), default=False )
    if self._executionNode:
      self._executionNode._copy(result.executionNode())
    return result


  def inlineGUI( self, values, context, parent, externalRunButton=False ):
    return None


  def validation( self ):
    return 1

  def id( self ):
    return self._id

  def sourceFile( self ):
    return self._fileName

  def sourcePath( self ):
    return os.path.dirname( self._fileName )

  def __str__( self ):
    instance = getattr( self, '_instance', None )
    if instance is None:
      return self.id()
    else:
      return self.id() + '_' + unicode( instance )

  def addLink( self, destination, source, function=None ):
    eNode = getattr( self, '_executionNode', None )
    if eNode is None:
      Parameterized.addLink( self, destination, source, function )
    else:
      eNode.addLink( destination, source, function )

  def setExecutionNode( self, eNode ):
    self._executionNode = eNode

  def execution( self, context ):
    if self._executionNode is not None:
      return self._executionNode.run( context )
    else:
      raise RuntimeError( HTMLMessage(_t_( 'No <em>execution</em> method provided' )) )

  def executionNode( self ):
    return self._executionNode


  def pipelineStructure( self ):
    return self.id()


  def allProcesses( self ):
    yield self
    if self._executionNode is not None:
      stack = [ self._executionNode ]
      while stack:
        eNode = stack.pop( 0 )
        if isinstance( eNode, ProcessExecutionNode ):
          yield eNode._process
        stack.extend( eNode.children() )


  def saveStateInDictionary( self, result=None ):
    if result is None:
      result = {}
    result[ 'pipelineStructure' ] = self.pipelineStructure()
    if self._executionNode is not None:
      if self._executionNode._parameterized is not None:
        Parameterized.saveStateInDictionary( self._executionNode._parameterized(), result )
      eNodesState = {}
      for eNodeKey in self._executionNode.childrenNames():
        eNode = self._executionNode.child( eNodeKey )
        eNodeDict = {}
        eNode.saveStateInDictionary( eNodeDict )
        eNodesState[ eNodeKey ] = eNodeDict
      result[ 'executionNodes' ] = eNodesState
    else:
      Parameterized.saveStateInDictionary( self, result )
    return result


  def getAllParameters( self ):
    stack = [ self ]
    while stack:
      node = stack.pop( 0 )
      if isinstance( node, Process ):
        parameterized = node
        node = node.executionNode()
        if node is not None:
          stack += [node.child( i ) for i in node.childrenNames()]
      else:
        parameterized = node._parameterized
        if parameterized is not None: parameterized = parameterized()
        stack += [node.child( i ) for i in node.childrenNames()]
      if parameterized is not None:
        for attribute, type in parameterized.signature.iteritems():
          yield ( parameterized, attribute, type )



#----------------------------------------------------------------------------
class IterationProcess( Process ):
  def __init__( self, name, processes ):
    self._id = name + 'Iteration'
    self.name = name
    self.instance = 1
    self._processes = [getProcessInstance( p ) for p in processes]
    Process.__init__( self )
    for sp, p in zip( self._executionNode._children.values(), processes ):
      if isinstance( p, ExecutionNode ):
        sp._optional = p._optional
        sp._selected = p._selected

  def pipelineStructure( self ):
    return { 'type': 'iteration', 'name' : self.name, 'children':[p.pipelineStructure() for p in self._processes] }

  def initialization( self ):
    eNode = ParallelExecutionNode( self.name, stopOnError=False )
    for i in xrange( len( self._processes ) ):
      self._processes[ i ].isMainProcess = True
      eNode.addChild( str( i ), ProcessExecutionNode( self._processes[ i ],
                        optional=True, selected = True ) )
    self._executionNode = eNode


#----------------------------------------------------------------------------
class ListOfIterationProcess( IterationProcess ):
  '''An IterationProcess which has on its main signature a list of the first
  element of each sub-process.
  Used for viewers and editors of ListOf()'''
  class linkP( object ):
    def __init__( self, proc, i ):
      self.proc = proc
      self.num = i
    def __call__( self, par ):
      if len( self.proc.param ) > self.num:
        return self.proc.param[self.num]

  def __init__( self, name, processes ):
    IterationProcess.__init__( self, name, processes )
    chs = list( self.executionNode().children() )[0]._process.signature
    self.changeSignature( Signature( 'param', ListOf( chs.values()[0] ) ) )
    en = self.executionNode()
    en._parameterized = weakref.ref( self )
    for i, p in enumerate( en.children() ):
      s = p._process.signature
      en.addLink( str(i) + '.' + s.keys()[0], 'param', self.linkP( self, i ) )


#----------------------------------------------------------------------------
class DistributedProcess( Process ):
  def __init__( self, name, processes ):
    self._id = name + 'DistributedIteration'
    self.name = name
    self.instance = 1
    self._processes = [getProcessInstance( p ) for p in processes]
    Process.__init__( self )
    for sp, p in zip( self._executionNode._children.values(), processes ):
      if isinstance( p, ExecutionNode ):
        sp._optional = p._optional
        sp._selected = p._selected

  def pipelineStructure( self ):
    return { 'type': 'distributed', 'name' : self.name, 'children':[p.pipelineStructure() for p in self._processes] }

  def initialization( self ):
    eNode = ParallelExecutionNode( self.name )
    for i in xrange( len( self._processes ) ):
      self._processes[ i ].isMainProcess = True
      subENode = self._processes[ i ]._executionNode
      eNode.addChild( str( i ), ProcessExecutionNode( self._processes[ i ],
                      optional=True, selected = True ) )
    self._executionNode = eNode


#----------------------------------------------------------------------------
class SelectionProcess( Process ):
  def __init__( self, name, processes ):
    self._id = name + 'Selection'
    self.name = name
    self.instance = 1
    self._processes = [getProcessInstance( p ) for p in processes]
    Process.__init__( self )
    for sp, p in zip( self._executionNode._children.values(), processes ):
      if isinstance( p, ExecutionNode ):
        sp._optional = p._optional
        sp._selected = p._selected

  def pipelineStructure( self ):
    return { 'type': 'selection', 'name' : self.name, 'children':[p.pipelineStructure() for p in self._processes] }

  def initialization( self ):
    eNode = SelectionExecutionNode( self.name )
    for i in xrange( len( self._processes ) ):
      self._processes[ i ].isMainProcess = True
      eNode.addChild( str( i ), ProcessExecutionNode( self._processes[ i ],
                        optional=True, selected = True ) )
    self._executionNode = eNode

#----------------------------------------------------------------------------
class TimeoutCall( object ):
  def __init__( self, function, *args, **kwargs ):
    self.function = function
    self.args = args
    self.kwargs = kwargs
    self.event = threading.Event()
    self.callFunction = 0
    self.functionLock =threading.RLock()

  def __del__( self ):
    self.stop()

  def _thread( self ):
    self.event.wait( self.timeout )
    self.functionLock.acquire()
    try:
      if self.callFunction:
        apply( self.function, self.args, self.kwargs )
    finally:
      self.functionLock.release()

  def start( self, timeout ):
    self.stop() # Just in case of multiple start() call during timeout
    self.functionLock.acquire()
    try:
      self.callFunction = 1
      self.event.clear()
      self.timeout = timeout
      threading.Thread( target = self._thread )
    finally:
      self.functionLock.release()

  def stop( self ):
    self.functionLock.acquire()
    try:
      self.callFunction = 0
      self.event.set()
    finally:
      self.functionLock.release()


#----------------------------------------------------------------------------
def signalName( signalNumber ):
  for key, value in signal.__dict__.items():
    if key[ :3 ] == 'SIG' and value == signalNumber:
      return key
  return str( signalNumber )


#----------------------------------------------------------------------------
def escapeQuoteForShell( s ):
  return string.replace( s, "'",  "'\"'\"'" )


if qprocess:
  # If QProcess is available, provide an implementation of system calls
  # based on this class. This implementation is called CommandWithQProcess
  # and is also named Command (with Command = CommandWithQProcess) for
  # backward compatibility with old implementation (see CommandWithPopen
  # below).

  from qtgui.command import CommandWithQProcess as Command

else:
  # Here, QProcess is not available. Therefore we provide an implementation
  # of system calls based on os.popen3 and threading. This implementation is
  #called CommandWithQProcess and is also named Command (with Command =
  # CommandWithPopen) for backward compatibility. This implementation may
  # disapear since QProcess should always be available.

  #--------------------------------------------------------------------------
  class CommandWithPopen( object ):
    class SignalException( Exception ):
      pass

    def _buildCommand( args ):
      if neuroConfig.platform == 'windows':
        # don't give priority to .bat scripts if both .bat and .exe are available
        x = distutils.spawn.find_executable( args[0] )
        if x is None:
          x = args[0]
        # take care of space characters in command path
        x = string.join( x.split(), '" "' )
        args = ( x, ) + tuple( args[1:] )
      if len( args ) == 1:
        return str( args[ 0 ] )
      else:
        if neuroConfig.platform == 'windows':
          return string.join( [args[0]] + map( lambda x: '"'+str(x)+'"', args[1:] ) )
        else:
          return string.join( map( lambda x: "'" + escapeQuoteForShell( str(x) ) \
                  + "'", args ) )
    _buildCommand = staticmethod( _buildCommand )

    def __init__( self, *command ):
      self.command = self._buildCommand( command )
      self.stdoutAction = ( sys.stdout.write, (), {})
      self.stderrAction = ( sys.stderr.write, (), {})
      self.endAction = None
      self.popen3 = None

    def setEnvironment(self, env):
      """
      Set a map of environment variables that have to be change at starting the process.
      @type env: map string -> string
      @param env: map variable -> value
      """
      pass

    def _parsecommand( self ):
      '''recreate an args list from the commandline (string) to run'''
      c = []
      p = 0
      q = 0
      l = len( self.command )
      line = ''
      # print self.command
      while q < l:
        if self.command[q] in ( '"', "'" ):
          ch = self.command[p]
          p += 1
          q = self.command.find( ch, p )
          if q == -1:
            c.append( line + self.command[ p: ] )
            return c
          line += self.command[ p:q ]
          q += 1
          p = q
        elif self.command[q] not in ( ' ', '\t' ):
          q += 1
        else:
          if q > p:
            line += self.command[ p:q ]
          if line:
            c.append( line )
            line = ''
          q += 1
          while q < l and self.command[q] in ( ' ', '\t' ):
            q += 1
          p = q
      if q > p:
        line += self.command[ p:q ]
      if line:
        c.append( line )
      return c

    def start( self ):
      result = None
      self.readThread = threading.Thread( target = self.read )
      self.errorThread = threading.Thread( target = self.readError )
      if sys.platform[:3] == 'win':
        self.popen3 = None
        self.stdout, self.stdin, self.stderr = neuroPopen2.popen3( self.command )
      else:
        self.popen3 = neuroPopen2.Popen3( self.command, 1 )
        self.stdout, self.stdin, self.stderr = self.popen3.fromchild, \
                                              self.popen3.tochild, \
                                              self.popen3.childerr
      self.readThread.start()
      self.errorThread.start()

    def wait( self ):
      # print 'wait', self
      # sys.stdout.flush()
      if self.readThread is not None:
        self.readThread.join()
      # print 'readThread joined', self
      # sys.stdout.flush()
      if self.errorThread is not None:
        self.errorThread.join()
      # print 'errorThread joined', self
      # sys.stdout.flush()
      self.stdin.close()
      self.stdout.close()
      result = self.stderr.close()
      self.readThread = None
      self.errorThread = None
      if self.popen3 is not None:
        try:
          #print '/wait pid ', str( self.popen3.pid ), ', state', \
          #      str( self.popen3.poll() ), '/'
          self.popen3.wait()
        except:
          pass
        status = self.popen3.poll()
        sig = None
        if os.WIFEXITED( status ):
          result = os.WEXITSTATUS( status )
        elif os.WIFSTOPPED( status ):
          sig = os.WSTOPSIG( status )
        elif os.WIFSIGNALED( status ):
          sig = os.WTERMSIG( status )
        self.popen3 = None
        if sig:
          raise self.SignalException( HTMLMessage(_t_( 'System call interrupted with signal <em>%s</em>') % signalName( sig )) )
      #print '/wait end/'
      #print '/system result:', result, '/'
      return result

    def error(self):
      return None

    def read( self ):
      l = '-'
      # print '/read/'
      # sys.stdout.flush()

      while l:
        l = ''
        c = '-'
        while c not in ( '', '\r', '\n', '\b' ):
          if neuroConfig.platform == 'windowsxx':
            import win32file
            #print '.'
            c = ''
            while not c:
              res, c = win32file.ReadFile( self.popen3.stdout[0], 1, None )
              #print 'read:', res, c
              #sys.stdout.flush()
              if res != 0:
                c = ''
                break
              if not c:
                time.sleep( 0.02 )
          else:
            c = self.stdout.read( 1 )
          if c != '\x0b':
            l += c
        ( function, args, kwargs ) = self.stdoutAction
        apply( function, ( l, ) + args, kwargs )
      # print '/read end ' + str( self.popen3.poll() ) + ', pid ' \
      #       + str( self.popen3.pid ) + '/'
      # sys.stdout.flush()

    def readError( self ):
      l = '-'
      while l:
        #try:
        #  x = os.waitpid( self.popen3.pid, os.WNOHANG )
        #print x
        #if x[0] == 0:
        #  print '/readError aborting/'
        #return
        #except:
        #  pass
        l = self.stderr.readline()
        #print '/readError ' + str( self.popen3.poll() ) + ', pid ' \
        #      + str( self.popen3.pid ) + '/'
        ( function, args, kwargs ) = self.stderrAction
        apply( function, ( l, ) + args, kwargs )
      #print '/readError end ' + str( self.popen3.poll() ) + ', pid ' \
      #      + str( self.popen3.pid ) + '/'

    def setStdoutAction( self, function, *args, **kwargs ):
      self.stdoutAction = ( function, args, kwargs )

    def setStderrAction( self, function, *args, **kwargs ):
      self.stderrAction = ( function, args, kwargs )

    def stop( self ):
  ##    # Try to nicely abort the command
  ##    os.kill( self.popen3.pid, signal.SIGINT )
  ##    # If the command is not finished in 30 seconds, kill it
  ##    killer = TimeoutCall( os.kill, self.popen3.pid, signal.SIGKILL )
  ##    killer.start( 30 )
  ##    self.wait()
  ##    killer.stop()
      # Just kill the process merciless
      if neuroConfig.platform == 'windows':
        import win32api
        try:
          win32api.TerminateProcess( self.popen3.pid[0], 1 )
        except:
          pass
        self.stdin.close()
        self.stdout.close()
        self.stderr.close()
      else:
        os.kill( self.popen3.pid, signal.SIGKILL )

    def commandName( self ):
      return self._parsecommand()[0]
      # older stuff
      first = self.command[ 0 ]
      if first in ( '"', "'" ):
        i = 1
        while i < len( self.command ):
          c = self.command[ i ]
          if c == first: break
          if c == '\\': i += 1
          i += 1
        return os.path.basename( self.command[ 1 : i ] )
      elif sys.platform[:3] == 'win':
        c = ''
        i = 0
        j = 0
        n = len( self.command )
        while i != -1:
          j = self.command.find( ' ', i )
          if j != -1:
            c += self.command[i:j-1]
            if self.command[j-1] in ( '"', "'" ) \
              and j < n-1 and self.command[j+1] == self.command[j-1]:
              c += self.command[i:j-1] + ' '
              i = j+2
            else:
              c += self.command[i:j]
              i = -1
          else:
            c += self.command[i:-1]
        return os.path.basename( c )
      else:
        return os.path.basename( string.split( self.command )[ 0 ] )

    def __str__( self ):
      return self.command

  Command = CommandWithPopen



#-------------------------------------------------------------------------------
class ExecutionNode( object ):
  class MultiParameterLink:
    def __init__( self, sources, function ):
      self.sources = []
      for p, n in sources:
        if type(p) is weakref.ReferenceType:
          self.sources.append( ( p, n ) )
        else:
          self.sources.append( ( weakref.ref( p ), n ) )
      self.function = function
      self.hasParameterized = hasParameter( function, 'parameterized' )
      self.hasNames = hasParameter( function, 'names' )

    def __call__( self, dummy1, dummy2 ):
      kwargs = {}
      if self.hasParameterized:
        kwargs[ 'parameterized' ] = [i[0]() for i in self.sources]
      if self.hasNames:
        kwargs[ 'names' ] = [i[1] for i in self.sources]
      return self.function( *[getattr( i[0](), i[1], None ) for i in self.sources],
                           **kwargs )

  def __init__( self, name='', optional = False, selected = True,
                guiOnly = False, parameterized = None ):
    # Initialize an empty execution node
    self.__dict__[ '_children' ] = SortedDictionary()
    if parameterized is not None:
      parameterized = weakref.ref( parameterized )
    self.__dict__[ '_parameterized' ] = parameterized
    self.__dict__[ '_name' ] = str( name )
    self.__dict__[ '_optional' ] = optional
    self.__dict__[ '_selected' ] = selected
    self.__dict__[ '_guiOnly' ] = guiOnly
    self.__dict__[ '_selectionChange' ] = Notifier( 1 )

  def __del__( self ):
    debugHere()

  def _copy(self, node):
    """
    Uses non default parameters values to initialize the parameters of the node given in argument.
    """
    # if execution node contains a process, copy the process parameters and copy its execution node parameters if any
    process=getattr(self, "_process", None)
    if process:
      processCopy=node._process
      for ( n, v ) in process.signature.items():
        if not self.isDefault( n ):
          processCopy.setValue( n, getattr( process, n, None ), default=False )
      processNode=process.executionNode()
      if processNode:
        processNode._copy(processCopy.executionNode())
    node.setSelected(self._selected)
    # if execution node have children nodes, copy the parameters of these nodes
    for name in self.childrenNames():
      child=self.child(name)
      child._copy(node.child(name))

  def addChild( self, name, node ):
    'Add a new child execution node'
    if self._children.has_key( name ):
      raise KeyError( HTMLMessage(_t_( '<em>%s</em> already defined' ) % ( name, )) )
    if not isinstance( node, ExecutionNode ):
      raise RuntimeError( HTMLMessage('<em>node</em> argument must be an ececution node') )
    self._children[ name ] = node


  def childrenNames( self ):
    return self._children.keys()


  def children( self ):
    return self._children.itervalues()

  def hasChildren( self ):
    return bool( self._children )


  def setSelected( self, selected ):
    if selected != self._selected:
      self._selected = selected
      self._selectionChange.notify( self )

  def isSelected( self ):
    return self._selected

  def __setattr__( self, attribute, value ):
    if self._parameterized is not None and \
       self._parameterized().signature.has_key( attribute ):
      setattr( self._parameterized(), attribute, value )
    elif self._children.has_key( attribute ):
      raise RuntimeError( HTMLMessage(_t_( 'Direct modification of execution node <em>%s</em> is not allowed.' ) % ( attribute, )) )
    else:
      self.__dict__[ attribute ] = value

  def __getattr__( self, attribute ):
    p = self.__dict__.get( '_parameterized' )
    if p is not None: p = p()
    if p is not None and hasattr( p, attribute ):
      return getattr( p, attribute )
    children = self.__dict__[ '_children' ]
    if children.has_key( attribute ):
      return children[ attribute ]
    raise AttributeError( attribute )

  def child( self, name, default = None ):
    return self._children.get( name, default )

  def run( self, context ):
    if self._optional and ( not self._selected ):
      context.write( '<font color=orange>Skip unselected node: ' + str(self.name()) + '</font>' )
      return
    if self._guiOnly and not neuroConfig.gui:
      context.write( '<font color=orange>Skip GUI-only node: ' + str(self.name()) + '</font>' )
      return
    return self._run( context )

  def _run( self, context ):
    pass

  def name( self ):
    return self._name

  def gui( self, parent, processView = None ):
    from qtgui.neuroProcessesGUI import ExecutionNodeGUI
    if self._parameterized is not None:
      return ExecutionNodeGUI(parent, self._parameterized())
    return None

  def addLink( self, destination, source, function=None ):
    # Parse source
    sources = []
    if type( source ) in ( types.ListType, types.TupleType ):
      for i in source:
        sources.append( self.parseParameterString( i ) )
    else:
      sources.append( self.parseParameterString( source ) )

    destObject, destParameter = self.parseParameterString( destination )
    # Check if a default function can be provided
    if function is None:
      if len( sources ) == 1:
        function = lambda x: x
      else:
        raise RuntimeError( HTMLMessage(_t_( 'No function provided in <em>addLink</em>' )) )
    multiLink = self.MultiParameterLink( sources, function )
    for sourceObject, sourceParameter in sources:
      sourceObject._links.setdefault( sourceParameter, [] ).append (
        ( destObject, destParameter, multiLink, True ) )


  def addDoubleLink( self, destination, source, function=None ):
    self.addLink( destination, source, function )
    self.addLink( source, destination, function )


  def removeLink( self, destination, source, function=None ):
    # Parse sourceExecutionContext
    sources = []
    if type( source ) in ( types.ListType, types.TupleType ):
      for i in source:
        sources.append( self.parseParameterString( i ) )
    else:
      sources.append( self.parseParameterString( source ) )

    destObject, destParameter = self.parseParameterString( destination )

    removed = 0
    for sourceObject, sourceParameter in sources:
      l = sourceObject._links.get( sourceParameter, [] )
      if l:
        lbis = l
        l = [i for i in l if ( i[0] is not destObject and i[0] is not weakref.proxy( destObject ) ) or i[1] != destParameter]
        if len(l) != len(lbis):
          removed = 1
        if l:
          sourceObject._links[ sourceParameter ] = l
        else:
          del sourceObject._links[ sourceParameter ]
          removed=1
    if removed == 0:
      print 'warning: enode link not removed:', self, destination, 'from:', source, ', function:', function


  def parseParameterString( self, parameterString ):
    if parameterString is None: return ( None, None )
    l = parameterString.split( '.' )
    node = self
    for nodeName in l[ : -1 ]:
      node = node.child( nodeName )
    parameterized = node._parameterized
    if parameterized is not None: parameterized = parameterized()
    name = l[ -1 ]
    if parameterized is None or not parameterized.signature.has_key( name ):
      raise KeyError( name )
    return ( parameterized, name )


  def saveStateInDictionary( self, result=None ):
    if result is None:
      result = {}
    result[ 'name' ] = self._name
    result[ 'selected' ] = self._selected
    if self._parameterized is not None:
      Parameterized.saveStateInDictionary( self._parameterized(), result )
    eNodesState = {}
    for eNodeKey in self.childrenNames():
      eNode = self.child( eNodeKey )
      eNodesState[ eNodeKey ] = eNode.saveStateInDictionary()
    result[ 'executionNodes' ] = eNodesState
    return result

#-------------------------------------------------------------------------------
class ProcessExecutionNode( ExecutionNode ):
  'An execution node that has no children and run one process'

  def __init__( self, process, optional = False, selected = True,
                guiOnly = False ):
    process = getProcessInstance( process )
    ExecutionNode.__init__( self, process.name,
                            optional = optional,
                            selected = selected,
                            guiOnly = guiOnly,
                            parameterized = process )
    self.__dict__[ '_process' ] = process
    reloadNotifier = getattr( process, 'processReloadNotifier', None )
    if reloadNotifier is not None:
      reloadNotifier.add( self.processReloaded )


  def addChild( self, name, node ):
    raise RuntimeError( _t_( 'A ProcessExecutionNode cannot have children' ) )

  def _run( self, context ):
    return context.runProcess( self._process )

  def gui( self, parent, processView = None ):
    if processView is not None:
      return ProcessView( self._process, parent,
                          externalInfo = processView.info )
    else:
      return ProcessView( self._process, parent )

  def name( self ):
    return _t_(self._process.name)

  def children( self ):
    eNode = getattr( self._process, '_executionNode', None )
    if eNode is not None:
      return eNode._children.itervalues()
    else:
      return []

  def childrenNames( self ):
    eNode = getattr( self._process, '_executionNode', None )
    if eNode is not None:
      return eNode._children.keys()
    else:
      return []

  def __setattr__( self, attribute, value ):
    if self._parameterized is not None and \
       self._parameterized().signature.has_key( attribute ):
      setattr( self._parameterized(), attribute, value )
    else:
      eNode = getattr( self._process, '_executionNode', None )
      if eNode is not None and eNode._children.has_key( attribute ):
        raise RuntimeError( HTMLMessage(_t_( 'Direct modification of execution node <em>%s</em> is not allowed.' ) % ( attribute, )) )
      self.__dict__[ attribute ] = value

  def __getattr__( self, attribute ):
    p = self.__dict__.get( '_parameterized' )()
    if p is not None and hasattr( p, attribute ):
      return getattr( p, attribute )
    eNode = getattr( self._process, '_executionNode', None )
    if eNode is not None:
      c = eNode.child( attribute )
      if c is not None:
        return c
    raise AttributeError( attribute )

  def child( self, name, default=None ):
    eNode = getattr( self._process, '_executionNode', None )
    if eNode is not None:
      return eNode.child( name, default )
    return default

  def processReloaded( self, newProcess ):
    event = ProcessExecutionEvent()
    event.setProcess( self._process )
    self._process.processReloadNotifier.remove( self.processReloaded )
    self.__dict__[ '_process' ] = getProcessInstanceFromProcessEvent( event )
    self._process.processReloadNotifier.add( self.processReloaded )



#-------------------------------------------------------------------------------
class SerialExecutionNode( ExecutionNode ):
  'An execution node that run all its children sequentially'

  def __init__(self, name='', optional = False, selected = True,
                guiOnly = False, parameterized = None, stopOnError=True ):
    ExecutionNode.__init__(self, name, optional, selected, guiOnly, parameterized)
    self.stopOnError=stopOnError

  def _run( self, context ):
    result = []
    pi, p = context.getProgressInfo( self )
    pi.children = [ None ] * len( self._children )
    if self.stopOnError:
      for node in self._children.values():
        npi, proc = context.getProgressInfo( node, parent=pi )
        context.progress()
        result.append( node.run( context ) )
        del npi
    else:
      for node in self._children.values():
        npi, proc = context.getProgressInfo( node, parent=pi )
        context.progress()
        try:
          result.append( node.run( context ) )
          del npi
        except ExecutionContext.UserInterruptionStep, e:
          context.error(unicode(e))
        except ExecutionContext.UserInterruption:
          raise
        except Exception, e:
          context.error("Error in execution node : "+unicode(e))
    context.progress()
    return result


#-------------------------------------------------------------------------------
class ParallelExecutionNode( SerialExecutionNode ):
  """
  An execution node that run all its children in any order (and in parallel
  if possible)
  """

  def _run( self, context ):
    pi, p = context.getProgressInfo( self )
    if not neuroDistributedProcesses() or len( self._children ) < 2:
      # do as for serial node
      return super( ParallelExecutionNode, self )._run( context )
    else:
      errorCount = 0
      result = []

      rp_t = []
      rpid = 0

      try:
        print 'ParallelExecutionNode._run'
        user = UserInfosBV(context, Signature('Password', Password()) )
        print 'user:', user

        if not user.isAccepted():
          context.error('Password needed to launch process remotely. Running locally and sequencially...')
          raise RuntimeError( _t_( 'distributed execution failure' ) )

        print 'user accepted'
        if not hasattr( context, 'remote' ) or context.remote is None:
          # no remote context has been setup yet - no GUI
          print 'creating remote context'
          context.remote = RemoteContext()
          context.remote.write = context.write
        remoteContext = context.remote
        remoteContext.clearGUI()
        cluster, isServer = getClusterInstance(context)
        print 'cluster:', cluster, isServer

        context.write('Dispatching processes on cluster...\n')
      except Exception, e:
        # distribution failure: run locally
        # do as for serial node
        print 'distributed execution has failed:', e
        print 'running sequentially.'
        result = []
        for node in self._children.values():
          npi, proc = context.getProgressInfo( node, parent=pi )
          context.progress()
          result.append( node.run( context ) )
          del npi
        context.progress()
        return result

      context.progress()
      pis = []
      for node in self._children.values():
        npi, proc = context.getProgressInfo( node, parent=pi )
        pis.append( npi )
        try:

          rp_t.append( RemoteProcessCall(rpid, cluster, context, node) )
          rp_t[rpid].start()
          rpid += 1

        except ExecutionContext.UserInterruption:
          raise
        except:
          errorCount += 1
          result.append( sys.exc_info()[ 1 ] )
          try:
            self._showException()
          except SystemExit:
            raise
          except:
            import traceback
            info = sys.exc_info()
            sys.stderr.write('\n%s: %s\n' % (info[0].__name__, info[1].message))
            traceback.print_tb(info[2], None, sys.stderr)
          logException( context=context )

      if errorCount:
        raise RuntimeError( _t_( '%d execution nodes on %d have produced an error' ) % ( errorCount, len( result ) ) )

      context.write('Processes are running...\n')

      print 'waiting...'
      for i in range(len(self._children.values())):
        rp_t[i].join()
        del pis[0]
        context.progress()
        print 'thread [%d] finished'%i
        if isinstance(rp_t[i].exception, Exception):
          if isinstance(rp_t[i].exception, RemoteConnectionError):
            context.write(_t_('Remote execution failed on process %s. Running locally.') % (str(i),) )
            # distribution failure: run locally
            # do as for serial node
            result.append( self._children.values()[i].run( context ) )
          else:
            raise rp_t[i].exception
      del pis

      if not isServer:
        cluster.closeSessions()

      print 'All finished'

      context.progress()
      return result

#-------------------------------------------------------------------------------
class SelectionExecutionNode( ExecutionNode ):
  '''An execution node that run one of its children'''

  def __init__( self, *args, **kwargs ):
    ExecutionNode.__init__( self, *args, **kwargs )
    self._selection = None


  def _run( self, context ):
    'Run the selected child'
    if self._selected is None:
      raise RuntimeError( _t_( 'No children selected' ) )
    pi, p = context.getProgressInfo( self )
    pi.children = [ None ]
    for node in self._children.values():
      if node._selected:
        npi, proc = context.getProgressInfo( node, parent=pi )
        context.progress()
        res =  node.run( context )
        del npi
        context.progress()
        return res
    context.progress()

  def addChild( self, name, node ):
    'Add a new child execution node'
    ExecutionNode.addChild(self, name, node)
    node._selectionChange.add(self.childSelectionChange)

  def childSelectionChange(self, node):
    '''This callback is called when the selection state of a child has changed.
    If the child is selected, all the other children must be unselected
    because this node is a selectionNode.'''
    if node._selected:
      for child in self.children():
        if child != node:
          child.setSelected(False)

#-------------------------------------------------------------------------------
class ExecutionContext:
  remote = None

  class UserInterruption( Exception ):
    def __init__( self ):
      Exception.__init__( self, _t_( 'user interruption' ) )

  class UserInterruptionStep( Exception ):
    def __init__( self ):
      Exception.__init__( self, _t_( 'user interruption of current step' ) )

  class StackInfo:
    def __init__( self, process ):
      self.process = process
      self.processCount = {}
      self.thread = None
      self.debug = None
      self.log = None
      self.time = time.localtime()

  def __init__( self, userLevel = None, debug = None ):
    if userLevel is None:
      self.userLevel = neuroConfig.userLevel
    else:
      self.userLevel = userLevel
    #self._processStack = []
    self._lock = threading.RLock()
    self._processStackThread = {}
    self._processStackHead = None
    self.manageExceptions = 1
    self._systemOutputLevel = 0
    self._systemLog = None
    self._systemLogFile = None

    self._interruptionRequest = None
    self._interruptionActions = {}
    self._interruptionActionsId = 0
    self._interruptionLock = threading.RLock()
    self._allowHistory = False

  def _processStack( self ):
    self._lock.acquire()
    try:
      stack = self._processStackThread[ threading.currentThread() ]
    except:
      stack = []
      self._processStackThread[ threading.currentThread() ] = stack
    self._lock.release()
    return stack

  def _popStack( self ):
    self._lock.acquire()
    stack = self._processStackThread[ threading.currentThread() ]
    stackinfo = stack.pop()
    if len( stack ) == 0:
      del self._processStackThread[ threading.currentThread() ]
    if stackinfo is self._processStackHead:
      self._processStackHead = None
    self._lock.release()
    return stackinfo

  def _pushStack( self, stackinfo ):
    self._lock.acquire()
    stack = self._processStack()
    stack.append( stackinfo )
    if self._processStackHead is None:
      self._processStackHead = stackinfo
    self._lock.release()

  def _stackTop( self ):
    stack = self._processStack()
    if len( stack ) == 0:
      return None
    return stack[-1]

  def _processStackParent( self ):
    stack = self._processStack()
    if len( stack ) == 0:
      return self._processStackHead
    return stack[-1]

  def _setArguments( self, _process, *args, **kwargs ):
    # Set arguments
    i = 0
    for v in args:
      n = _process.signature.keys()[ i ]
      _process.setDefault( n, 0 )
      if v is not None:
        _process.setValue( n, v )
      else:
        setattr( _process, n, None )
      i += 1
    for ( n, v ) in kwargs.items():
      _process.setDefault( n, 0 )
      if v is not None:
        _process.setValue( n, v )
      else:
        setattr( _process, n, None )
    _process.checkArguments()

  def _startProcess( self, _process, executionFunction, *args, **kwargs ):
    if not isinstance( _process, Process ):
      _process = getProcessInstance( _process )
    apply( self._setArguments, (_process,)+args, kwargs )
    # Launch process
    t = threading.Thread( target = self._processExecutionThread,
                          args = ( _process, executionFunction ) )
    t.start()
    return _process

  def runProcess( self, _process, *args, **kwargs ):
    _process = getProcessInstance( _process )
    self.checkInterruption()
    apply( self._setArguments, (_process,)+args, kwargs )
    result = self._processExecution( _process, None )
    self.checkInterruption()
    return result


  @staticmethod
  def createContext():
    return ExecutionContext()


  def runInteractiveProcess( self, callMeAtTheEnd, process, *args, **kwargs ):
    context = self.createContext()
    process = getProcessInstance( process )
    self.checkInterruption()
    apply( self._setArguments, (process,)+args, kwargs )
    thread = threading.Thread( target = self._runInteractiveProcessThread,
      args = ( context, process, callMeAtTheEnd ) )
    thread.start()


  def _runInteractiveProcessThread( self, context, process, callMeAtTheEnd ):
    try:
      result = context.runProcess( process )
    except Exception, e:
      result = e
    callMeAtTheEnd( result )


  def _processExecutionThread( self, *args, **kwargs ):
    self._processExecution( *args, **kwargs )
    neuroHierarchy.databases.currentThreadCleanup()


  def _processExecution( self, process, executionFunction=None ):

    '''Execute the process "process". The value return is stored to avoid
    the garbage-collection of some of the objects created by the process
    itself (GUI for example).
    '''
    result = None
    stackTop = None
    process = getProcessInstance( process )
    stack = self._processStack()
    stackTop = self._processStackParent()

    if stackTop:
##      if neuroConfig.userLevel > 0:
##        self.write( '<img alt="" src="' + os.path.join( neuroConfig.iconPath, 'icon_process.png' ) + '" border="0">' \
##                    + _t_(process.name) + ' '\
##                    + str(process.instance) + '<p>' )
      # Count process execution
      count = stackTop.processCount.get( process._id, 0 )
      stackTop.processCount[ process._id ] = count + 1


    newStackTop = self.StackInfo( process )
    self._pushStack( newStackTop )
    ishead = not stackTop

    # Logging process start
    if not stackTop:
      process.isMainProcess = True

    try: # finally -> processFinished
      try: # show exception

        # check write parameters if the process is the main process (check all parameters in child nodes if it is a pipeline)
        # or if it has a parent which is not a pipeline that is to say, the current process is run throught context.runProcess
        if ishead:
          self._allWriteDiskItems = {}
        if ishead or (stackTop and stackTop.process._executionNode is None):
          writeParameters = []
          #try: # an exception could occur if the user has not write permission on the database directory
          for parameterized, attribute, type in process.getAllParameters():
            if isinstance( type, WriteDiskItem ):
              item = getattr( parameterized, attribute )
              if item is not None:
                writeParameters.append(item)
            elif isinstance( type, ListOf ) and isinstance( type.contentType, WriteDiskItem ):
              itemList = getattr( parameterized, attribute )
              if itemList:
                writeParameters.extend(itemList)
          for item in writeParameters:
            dirs=[]
            dirname = os.path.dirname( item.fullPath() )
            dir=dirname
            while not os.path.exists( dir ):
              dirs.append(dir)
              dir=os.path.dirname(dir)
            if dirs:
              try:
                os.makedirs( dirname )
              except OSError, e:
                if not e.errno == os.errno.EEXIST:
                  # filter out 'File exists' exception, if the same dir has
                  # been created concurrently by another instance of BrainVisa
                  # or another thread
                  raise
              for d in dirs:
                dirItem=neuroHierarchy.databases.createDiskItemFromFileName(d, None)
                if dirItem:
                  uuid=dirItem.uuid()
                  self._allWriteDiskItems[uuid] = [ dirItem, None ]
            uuid=item.uuid()
            self._allWriteDiskItems[uuid] = [ item, item.modificationHash() ]
          #except:
            #showException()
        if ishead:
          log = neuroConfig.mainLog
          if self._allowHistory:
            self._historyBookEvent, self._historyBooksContext = HistoryBook.storeProcessStart( self, process )
        else:
          if len( stack ) >= 2:
            log = stack[ -2 ].log
          else:
            # FIXME:
            # attaching to head log is not always the right solution
            # if a sub-process has parallel sub-nodes, then a new thread
            # and a new stack will be created, but the logs will not be
            # appended to the correct parent
            log = self._processStackHead.log
        if log is not None:
          #print "Create subLog for process ", process.name
          newStackTop.log = log.subLog()
          process._log = newStackTop.log
          content= '<html><body><h1>' + _t_(process.name) + '</h1><h2>' + _t_('Process identifier') + '</h2>' + process._id + '<h2>' + _t_('Parameters') +'</h2>'
          for n in process.signature.keys():
            content += '<em>' + n + '</em> = ' + htmlEscape( str( getattr( process, n, None ) ) ) + '<p>'
          content += '<h2>' + _t_( 'Output' ) + '</h2>'
          try:
            #print "Create subTextLog for process ", process.name
            process._outputLog = log.subTextLog()
            process._outputLogFile = open( process._outputLog.fileName, 'w' )
            print >> process._outputLogFile, content
            process._outputLogFile.flush()
            content = process._outputLog
          except:
            content += '<font color=red>' + _t_('Unabled to open log file') + '</font></html></body>'
            process._outputLog = None
            process._outputLogFile = None
          self._lastStartProcessLogItem = log.append( _t_(process.name) + ' ' + str(process.instance), html=content,
                      children=newStackTop.log, icon='icon_process.png' )
        else:
          newStackTop.log = None

        self._processStarted()
        newStackTop.thread = threading.currentThread()

        self._lastProcessRaisedException = False
        # Check arguments and conversions
        def _getConvertedValue( v, p ):
          # v: value
          # p: parameter (Read/WriteDiskItem)
          if v and getattr(v, "type", None) and ( ( not isSameDiskItemType( v.type, p.type ) ) or v.format not in p.formats ):
            c = None
            formats = [ p.preferredFormat ] \
              + [ f for f in p.formats if f is not p.preferredFormat ]
            for destinationFormat in formats:
              converter = getConverter( (v.type, v.format), (p.type, destinationFormat), checkUpdate=False )
              if converter:
                tmp = self.temporary( destinationFormat )
                tmp.type = v.type
                tmp.copyAttributes( v )
                convargs = { 'read' : v, 'write' : tmp }
                c = getProcessInstance( converter.name )
                if c is not None:
                  try:
                    apply( self._setArguments, (c,), convargs )
                    if c.write is not None:
                      break
                  except:
                    pass
            ##              if not converter: raise Exception( _t_('Cannot convert format <em>%s</em> to format <em>%s</em> for parameter <em>%s</em>') % ( _t_( v.format.name ), _t_( destinationFormat.name ), n ) )
            ##              tmp = self.temporary( destinationFormat )
            ##              tmp.type = v.type
            ##              tmp.copyAttributes( v )
            ##              self.runProcess( converter.name, read = v, write = tmp )
            if not c: raise Exception( HTMLMessage(_t_('Cannot convert format <em>%s</em> to format <em>%s</em> for parameter <em>%s</em>') % ( _t_( v.format.name ), _t_( destinationFormat.name ), n )) )
            self.runProcess( c )
            return tmp

        converter = None
        for ( n, p ) in process.signature.items():
          if isinstance( p, ReadDiskItem ) and p.enableConversion:
            v = getattr( process, n )
            tmp = _getConvertedValue( v, p )
            if tmp is not None:
              process.setConvertedValue( n, tmp )
          elif isinstance( p, WriteDiskItem ):
            v = getattr( process, n )
            if v is not None:
              v.createParentDirectory()
          elif isinstance( p, ListOf ):
            needsconv = False
            converted = []
            lv = getattr( process, n )
            for v in lv:
              tmp = _getConvertedValue( v, p.contentType )
              if tmp is not None:
                converted.append( tmp )
                needsconv = True
              else:
                converted.append( v )
            if needsconv:
              process.setConvertedValue( n, converted )
        if executionFunction is None:
          result = process.execution( self )
        else:
          result = executionFunction( self )
      except:
        self._lastProcessRaisedException = True
        try:
          self._showException()
        except SystemExit, e:
          neuroConfig.exitValue = e.args[0]
        except:
          import traceback
          info = sys.exc_info()
          sys.stderr.write('\n%s: %s\n' % (info[0].__name__, info[1].message))
          traceback.print_tb(info[2], None, sys.stderr)
        logException( context=self )
        if self._depth() != 1 or not self.manageExceptions:
          raise
    finally:
      self._processFinished( result )
      process.restoreConvertedValues()
      for item_hash in self._allWriteDiskItems.values():
        item, hash = item_hash
        if item.isReadable():
          if item.modificationHash() != hash:
            try:
              # do not try to insert in the database an item that doesn't have any reference to a database
              # or which is temporary
              if item.get("_database", None) and \
                ( not hasattr( item, '_isTemporary' ) \
                  or not item._isTemporary ):
                neuroHierarchy.databases.insertDiskItem( item, update=True )
            except NotInDatabaseError:
              pass
            except:
              showException()
            item_hash[ 1 ] = item.modificationHash()
        elif (process.isMainProcess): # clear unused minfs only when the main process is finished to avoid clearing minf that will be used in next steps
          item.clearMinf()

      # Close output log file
      if process._outputLogFile is not None:
        print >> process._outputLogFile, '</body></html>'
        process._outputLogFile.close()
        process.outputLogFile = None
      if process._outputLog is not None:
        process._outputLog.close()
        process._outputLog = None
      if process._log is not None:
        process._log.close()
        process._log = None
      # Expand log to put sublogs inline
      log = self._stackTop().log
      if log is not None:
        if process.isMainProcess and neuroConfig.mainLog:
          neuroConfig.mainLog.expand()
        if self._depth() == 1:
          if self._allowHistory:
            if self._historyBookEvent is not None:
              HistoryBook.storeProcessFinished( self, process, self._historyBookEvent, self._historyBooksContext )
              self._historyBookEvent = None
              self._historyBooksContext = None
          self._lastStartProcessLogItem = None
      self._popStack().thread = None ##### WARNING !!! not pop()
    return result

  def _currentProcess( self ):
    stackTop = self._stackTop()
    if stackTop is None:
      return None
    else:
      return stackTop.process

  def _depth( self ):
    return len( self._processStack() )

  def _showSystemOutput( self ):
    return self._systemOutputLevel >= 0 and self.userLevel >= self._systemOutputLevel

  def _processStarted( self ):
    if self._currentProcess().isMainProcess:
      msg = '<p><img alt="" src="' + \
            os.path.join( neuroConfig.iconPath, 'process_start.png' ) + \
            '" border="0"><em>' + _t_( 'Process <b>%s</b> started on %s') % \
            ( _t_(self._currentProcess().name ) + ' ' + \
              str( self._currentProcess().instance ),
              time.strftime( _t_( '%Y/%m/%d %H:%M' ),
                             self._stackTop().time ) ) + \
            '</em></p>'
      self.write( msg )

  def _processFinished( self, result ):
    if self._currentProcess().isMainProcess:
      finalTime = time.localtime()
      elapsed = calendar.timegm( finalTime ) - calendar.timegm( self._stackTop().time )
      msg = '<br><img alt="" src="' + \
            os.path.join( neuroConfig.iconPath, 'process_end.png' ) + \
            '" border="0"><em>' + _t_( 'Process <b>%s</b> finished on %s (%s)' ) % \
        ( _t_(self._currentProcess().name) + ' ' + str( self._currentProcess().instance ),
          time.strftime( _t_( '%Y/%m/%d %H:%M' ), finalTime), timeDifferenceToString( elapsed ) ) + \
        '</em>'
      self.write( msg )

  def system( self, *args, **kwargs ):
    self._systemOutputLevel = kwargs.get( 'outputLevel', 0 )
    ignoreReturnValue = kwargs.get( 'ignoreReturnValue', 0 )
    command = [str(i) for i in args]

    ret = self._system( command, self._systemStdout, self._systemStderr )
    if ret and not ignoreReturnValue:
      raise RuntimeError( _t_( 'System command exited with non null value : %s' ) % str( ret ) )
    return ret

  def _systemStdout( self, line, logFile=None ):
    if logFile is None:
      logFile = self._systemLogFile
    if line and logFile is not None and self._showSystemOutput():
      if line[ -1 ] not in ( '\b', '\r' ):
        logFile.write( htmlEscape(line))
        logFile.flush()

  def _systemStderr( self, line, logFile=None ):
    if logFile is None:
      logFile = self._systemLogFile
    if line:
      lineInHTML = '<font color=red>' + htmlEscape(line) + '</font>'
      self.write( lineInHTML )
    if logFile is not None and line:
      logFile.write( lineInHTML )
      logFile.flush()

  def _system( self, command, stdoutAction = None, stderrAction = None ):
    self.checkInterruption()
    stackTop = self._stackTop()

    if type( command ) in types.StringTypes:
      c = Command( command )
    else:
      c = Command( *command )

    # Logging system call start
    if stackTop:
      log = stackTop.log
    else:
      log = neuroConfig.mainLog
    systemLogFile = None
    systemLog = None
    if log is not None:
      #print "Create subTextLog for command ", command[0]
      systemLog = log.subTextLog()
      self._systemLog = systemLog
      systemLogFile = open( systemLog.fileName, 'w' )
      self._systemLogFile = systemLogFile
      log.append( c.commandName(),
                  html=systemLog,
                  icon='icon_system.png' )
    try:
      commandName = distutils.spawn.find_executable( c.commandName() )
      if not commandName:
        commandName = c.commandName()
      if systemLogFile:
        print >> systemLogFile, '<html><body><h1>' + commandName +' </h1><h2>' +_t_('Command line') + \
          '</h2><code>' + htmlEscape( str( c ) ) + '</code></h2><h2>' + _t_('Output') + '</h2><pre>'
        systemLogFile.flush()

  ##    if self._showSystemOutput() > 0:
  ##      self.write( '<img alt="" src="' + os.path.join( neuroConfig.iconPath, 'icon_system.png' ) + '">' + c.commandName() + '<p>' )

      # Set environment for the command
      if (not commandName.startswith(os.path.dirname(neuroConfig.mainPath))): # external command
        if neuroConfig.brainvisaSysEnv:
          c.setEnvironment(neuroConfig.brainvisaSysEnv.getVariables())

      if stdoutAction is not None:
        if stdoutAction is self._systemStdout:
          c.setStdoutAction( lambda line: stdoutAction( line,
            logFile=systemLogFile ) )
        else:
          c.setStdoutAction( stdoutAction )
      if stderrAction is not None:
        if stderrAction is self._systemStderr:
          c.setStderrAction( lambda line: stderrAction( line,
            logFile=systemLogFile ) )
        else:
          c.setStderrAction( stderrAction )

      retry = 1
      first=True
      while (retry > 0):
        try:
          c.start()
          retry=0
        except RuntimeError, e:
          if c.error() == QProcess.FailedToStart:
            if first:
              retry = 2
              first=False
            else:
              retry=retry-1
            self._systemStderr(e.message+"\n", systemLogFile)
            if (retry != 0):
               self._systemStderr("Try to restart the command...\n", systemLogFile)
            else:
              raise e
          else:
            raise e

      intActionId = self._addInterruptionAction( c.stop )
      try:
        result = c.wait()
      finally:
        self._removeInterruptionAction( intActionId )
      self.checkInterruption()
      if systemLogFile is not None:
        print >> systemLogFile, '</pre><h2>' + _t_('Result') + '</h2>' + _t_('Value returned') + ' = ' + str( result ) + '</body></html>'
    finally:
      if systemLogFile is not None:
        systemLogFile.close()
        self._systemLogFile = None
      if systemLog is not None:
        systemLog.close()
        # no need to expand the log associated to the command as it is the log of the parent process,
        # it will be expanded at the end of the process
#      if log is not None and log is not neuroConfig.mainLog:
#        log.expand()
    return result

  def temporary( self, format, diskItemType = None ):
    result = getTemporary( format, diskItemType )
    return result

  def matlab( self, *commands ):
    self.checkInterruption()
    if matlab.valid and commands:
      m = matlab.matlab()
      for c in commands[:-1]:
        m.eval( c )
      return m.eval( commands[ -1 ] )
    self.checkInterruption()


  def write( self, *messages, **kwargs ):
    self.checkInterruption()
    if messages:
      msg = u' '.join( unicode( i ) for i in messages )
      stackTop = self._stackTop()
      if stackTop:
        outputLogFile = stackTop.process._outputLogFile
        if outputLogFile:
          print >> outputLogFile, msg
          outputLogFile.flush()
      self._write( msg )

  def _write( self, html ):
    if not hasattr( self, '_writeHTMLParser' ):
      self._writeHTMLParser = htmllib.HTMLParser( formatter.AbstractFormatter(
        formatter.DumbWriter( sys.stdout, 80 ) ) )
    self._writeHTMLParser.feed( html + '<br>\n' )

  def warning( self, *messages ):
    self.checkInterruption()
    bmsg = '<table width=100% border=1><tr><td><font color=orange><img alt="WARNING: " src="' \
      + os.path.join( neuroConfig.iconPath, 'warning.png' ) + '">'
    emsg = '</font></td></tr></table>'
    apply( self.write, (bmsg, ) + messages + ( emsg, ) )

  def error( self, *messages ):
    self.checkInterruption()
    bmsg = '<table width=100% border=1><tr><td><font color=red><img alt="ERROR: " src="' \
      + os.path.join( neuroConfig.iconPath, 'error.png' ) + '">'
    emsg = '</font></td></tr></table>'
    apply( self.write, (bmsg, ) + messages + ( emsg, ) )

  def ask( self, message, *buttons, **kwargs):
    self.checkInterruption()
    self.write( '<pre>' + message )
    i = 0
    for b in buttons:
      self.write( '  %d: %s' % ( i, str(b) ) )
      i += 1
    sys.stdout.write( 'Choice: ' )
    sys.stdout.flush()
    line = sys.stdin.readline()[:-1]
    self.write( '</pre>' )
    try:
      result = int( line )
    except:
      result = None
    return result


  def dialog( self, *args ):
    self.checkInterruption()
    return None


  def _showException( self ):
    stackTop = self._stackTop()
    msg = exceptionHTML(
      beforeError=_t_( 'in <em>%s</em>' ) % ( _t_(stackTop.process.name) + ' ' + str( stackTop.process.instance ) ) )
    try:
      self.checkInterruption()
    except:
      pass
    self.write( '<table width=100% border=1><tr><td>'+ msg + '</td></tr></table>' )
    if neuroConfig.fastStart and not neuroConfig.gui:
      sys.exit( 1 )


  def checkInterruption( self ):
    self._interruptionLock.acquire()
    try:
      self._checkInterruption()
      exception = self._interruptionRequest
      if exception is not None:
        self._interruptionRequest = None
        raise exception
    finally:
      self._interruptionLock.release()


  def _checkInterruption( self ):
    self._interruptionLock.acquire()
    try:
      if self._interruptionRequest is not None:
        for function, args, kwargs in self._interruptionActions.values():
          function( *args, **kwargs )
        self._interruptionActions.clear()
    finally:
      self._interruptionLock.release()
    return None

  def _addInterruptionAction( self, function, *args, **kwargs ):
    self._interruptionLock.acquire()
    try:
      result = self._interruptionActionsId
      self._interruptionActionsId += 1
      self._interruptionActions[ result ] = ( function, args, kwargs )
    finally:
      self._interruptionLock.release()
    return result

  def _removeInterruptionAction( self, number ):
    self._interruptionLock.acquire()
    try:
      if self._interruptionActions.has_key( number ):
        del self._interruptionActions[ number ]
    finally:
      self._interruptionLock.release()

  def _setInterruptionRequest( self, interruptionRequest ):
    self._interruptionLock.acquire()
    try:
      self._interruptionRequest = interruptionRequest
      self._checkInterruption()
    finally:
      self._interruptionLock.release()


  def log( self, *args, **kwargs ):
    stackTop = self._stackTop()
    if stackTop:
      logFile = stackTop.log
    else:
      logFile = neuroConfig.mainLog
    if logFile is not None:
      logFile.append( *args, **kwargs )


  def getConverter( self, source, dest, checkUpdate=True ):
    # Check and convert source type
    if isinstance( source, DiskItem ):
      source = ( source.type, source.format )
    elif isinstance( source, ReadDiskItem ):
      if source.formats:
        source = ( source.type, source.formats[ 0 ] )
      else:
        source = ( source.type, None )

    # Check and convert dest type
    if isinstance( dest, DiskItem ):
      dest = ( dest.type, dest.format )
    elif isinstance( dest, ReadDiskItem ):
      if dest.formats:
        dest = ( dest.type, dest.formats[ 0 ] )
      else:
        dest = ( dest.type, None )
    st, sf = source
    dt, df = dest
    return getConverter( ( getDiskItemType( st ), getFormat( sf ) ),
                         ( getDiskItemType( dt ), getFormat( df ) ), checkUpdate=checkUpdate )

  def createProcessExecutionEvent( self ):
    from brainvisa.history import ProcessExecutionEvent
    event = ProcessExecutionEvent()
    event.setProcess( self.process )
    stack = self._processStack()
    if stack:
      log = stack[0].log
      if log is not None:
        event.setLog( log )
    return event

  def _attachProgress( self, parent, count=None, process=None ):
    '''Create a new ProgressInfo object.
    If parent is provided, it is the parent ProgressInfo, or the parent
    process. If not specified, the new ProgressInfo will be attached to the
    top-level ProgressInfo in the context.
    count is the number of children that the new ProgressInfo will hold. It is
    not the maximum value of a numeric progress value (see progress() method).
    process is the current (child) process which will be attached with the new
    ProgressInfo.

    This method is called internally in pipeline execution nodes. Regular
    processes need not to call it directly. They should call getProcessInfo()
    instead.
    '''
    if parent is not None:
      parent, parentproc = self._findProgressInfo( parent )
    if parent is None:
      parent = self._topProgressinfo()
      #if parent is not None and len( parent.children ) == 0:
        #parent.childrendone = 0 # reset
    if parent is None:
      parent = ProgressInfo()
      self._progressinfo = weakref.ref( parent )
      if process is None:
        pi = parent
        pi.children = [ None ] * count
      else:
        pi = ProgressInfo( parent, count, process=process )
    else:
      pi = ProgressInfo( parent, count, process=process )
    pig = self._topProgressinfo()
    if process is not None:
      plist = getattr( pig, 'processes', None )
      if plist is None:
        plist = weakref.WeakKeyDictionary()
        pig.processes = plist
      plist[ process ] = weakref.ref( pi )
    return pi

  def getProgressInfo( self, process, childrencount=None, parent=None ):
    '''Get the progress info for a given process or execution node, or create
    one if none already exists.
    A regular process may call it.
    The output is a tuple containing the ProgressInfo and the process itself,
    just in case the input process is in fact a ProgressInfo instance.
    A ProgressInfo has no hard reference in BrainVISA: when you don't need
    it anymore, it is destroyed via Python reference counting, and is
    considered done 100% for its parent.
    childrencount is the number of children that the process will have, and is
    not the same as the own count of the process in itself, which is in
    addition to children (and independent), and specified when using the
    progress() method.
    '''
    pinfo, process = self._findProgressInfo( process )
    if pinfo is None:
      if process is None:
        pinfo = self._topProgressinfo()
      if pinfo is None:
        pinfo = self._attachProgress( parent=parent, process=process,
          count=childrencount )
    return pinfo, process

  def _topProgressinfo( self ):
    '''internal.'''
    if hasattr( self, '_progressinfo' ):
      return self._progressinfo()
    return None

  def _findProgressInfo( self, processOrProgress ):
    '''internal.'''
    if processOrProgress is None:
      return None, None
    if isinstance( processOrProgress, ProgressInfo ):
      return processOrProgress, getattr( processOrProgress, 'process', None )
    # in case it is a ProcessExecutionNode
    down = True
    while down:
      down = False
      if isinstance( processOrProgress, ExecutionNode ) and \
        hasattr( processOrProgress, '_process' ):
          processOrProgress = processOrProgress._process
          down = True
      if not isinstance( processOrProgress, ExecutionNode ) and \
        hasattr( processOrProgress, '_executionNode' ):
          p = processOrProgress._executionNode
          if p is not None:
            processOrProgress = p
            down = True
    if hasattr( processOrProgress, '_progressinfo' ):
      return processOrProgress._progressinfo, processOrProgress
    pinfo = getattr( self, '_progressinfo', None )
    if pinfo is None:
      return None, processOrProgress
    procs = getattr( self._topProgressinfo(), 'processes', None )
    if procs is None:
      return None, processOrProgress
    pi = procs.get( processOrProgress, None )
    if pi is not None:
      pi = pi()
    return pi, processOrProgress

  def progress( self, value=None, count=None, process=None ):
    '''Set the progress information for the parent process or ProgressInfo
    instance, and output it using the context output mechanisms.
    value is the progress value to set. If none, the value will not be changed,
    but the current status will be shown.
    count is the maximum value for the process own progress value (not taking
    children into account).
    process is either the calling process, or the ProgressInfo.
    '''
    if value is not None:
      pinfo, process = self.getProgressInfo( process )
      pinfo.setValue( value, count )
    tpi = self._topProgressinfo()
    if tpi is not None:
      self.showProgress( tpi.value() * 100 )

  def showProgress( self, value, count=None ):
    '''Output the given progress value. This is just the output method which
    is overriden in subclassed contexts.
    Users should normally not call it directory, but use progress() instead.
    '''
    if count is None:
      self.write( 'progress:', value, '% ...' )
    else:
      self.write( 'progress:', value, '/', count, '...' )

#----------------------------------------------------------------------------
class ProgressInfo( object ):
  '''ProgressInfo is a tree-like structure for progression information in a
  process or a pipeline. The final goal is to provide feedback to the user via
  a progress bar. ProgressInfo has children for sub-processes (when used in a
  pipeline), or a local value for its own progression.
  A ProgressInfo normally registers itself in the calling Process, and is
  destroyed when the process is destroyed, or when the process _progressinfo
  variable is deleted.
  '''
  def __init__( self, parent=None, count=None, process=None ):
    '''parent is a ProgressInfo instance.
    count is a number of children which will be attached.
    process is the calling process.
    '''
    if count is None:
      self.children = []
    else:
      self.children = [ None ] * count
    self.done = False
    self.childrendone = 0
    if parent is not None:
      parent.attach( self )
      self.parent = parent # prevent parent from deleting
    self._localvalue = 0.
    self._localcount = None
    if process is not None:
      self.process = weakref.ref( process )
      #process._progressinfo = self
    else:
      self.process = None

  def __del__( self ):
    if self.process is not None:
      proc = self.process()
      if proc is not None and hasattr( proc, '_progressinfo' ):
        del proc._progressinfo

  def value( self ):
    '''Calculate the progress value including those of children.
    '''
    if self.done:
      return 1.
    n = self.childrendone + len( self.children )
    if self._localcount is not None:
      n += 1 # self._localcount
    if n == 0:
      return self._localvalue
    done = float( self.childrendone )
    for c in self.children:
      if c is not None:
        done += c().value()
        if c().done:
          self._delchild( c )
    done += self._localvalue
    return done / n

  def setValue( self, value, count=None ):
    '''Set the ProgressInfo own progress value (not its children)
    '''
    if count is None:
      count = self._localcount
    else:
      self._localcount = count
    if self.done:
      if ( count is not None and value != count ) \
        or ( count is None and value != 1. ):
        self.done = False
    if count:
      value = float( value ) / count
    self._localvalue = value

  def setdone( self ):
    '''Marks the ProgressInfo as done 100%, the children are detached.
    '''
    self.done = True
    del self.children

  def _delchild( self, child ):
    if child in self.children:
      del self.children[ self.children.index( child ) ]
      self.childrendone += 1
    if len( self.children ) == 0:
      self.done = True

  def attach( self, pinfo ):
    '''Don't use this method directly, it is part of the internal mechanism,
    called by the constructor.
    '''
    wr = weakref.ref( pinfo, self._delchild )
    if None in self.children:
      i = self.children.index( None )
      self.children[i] = wr
    else:
      self.children.append( wr )
    self.done = False

  def debugDump( self ):
    print 'ProgressInfo:', self
    if hasattr( self, 'process' ):
      print '  process:', self.process
    print '  local value:', self._localvalue, '/', self._localcount
    print '  value:', self.value()
    print '  children:', len( self.children ) + self.childrendone
    print '  done:', self.childrendone
    print '  not started:', len( [ x for x in self.children if x is None ] )
    print '  running:'
    todo = [ ( x(), 1 ) for x in self.children if x is not None ]
    while len( todo ) != 0:
      pi, indent = todo[0]
      del todo[0]
      print '  ' * indent, pi, pi.childrendone,
      if hasattr( pi, 'process' ):
        print pi.process()
      else:
        print
      todo = [ ( x(), indent+1 ) for x in pi.children if x is not None ] + todo


#----------------------------------------------------------------------------
class ProcessInfo:
  def __init__( self, id, name, signature, userLevel, category, fileName, roles, toolbox, module=None ):
    self.id = id
    self.name = name
    #TODO: Signature cannot be pickeled
    self.signature = None
    self. userLevel = userLevel
    self.category = category
    self.fileName = fileName
    self.roles = tuple( roles )
    self.valid=True # set to False if process' validation method fails
    self.procdoc = None
    self.toolbox = toolbox

    if module is None:
      for p in ( neuroConfig.mainPath, neuroConfig.homeBrainVISADir ):
        if self.fileName.startswith( p ):
          module = split_path( self.fileName[ len( p ) + 1: ] )
      if module:
        if module[0] == 'toolboxes':
          module = module[ 2: ]
        module = '.'.join( module )
        if module.endswith( '.py' ):
          module = module[ :-3 ]
    self.module = module


  def html( self ):
    return '\n'.join( ['<b>' + n + ': </b>' + unicode( getattr( self, n ) ) + \
                        '<br>\n' for n in ( 'id', 'name', 'toolbox', 'signature',
                                            'userLevel', 'category',
                                            'fileName', 'roles' )] )

#----------------------------------------------------------------------------
def getProcessInfo( processId ):
  if isinstance( processId, ProcessInfo ):
    result = processId
  else:
    if type(processId) in types.StringTypes:
      processId = processId.lower()
    result = _processesInfo.get( processId )
    if result is None:
      process = getProcess( processId, checkUpdate=False )
      if process is not None:
        result = _processesInfo.get( process._id.lower() )
  return result

#----------------------------------------------------------------------------
def addProcessInfo( processId, processInfo ):
  _processesInfo[ processId.lower() ] = processInfo

#----------------------------------------------------------------------------
def getProcess( processId, ignoreValidation=False, checkUpdate=True ):
  global _askUpdateProcess
  if processId is None: return None
  if isinstance( processId, Process ) or ( type(processId) in (types.ClassType, types.TypeType) and issubclass( processId, Process ) ):
    result = processId
    id = getattr( processId, '_id', None )
    if id is not None:
      process = getProcess( id, checkUpdate=False )
      if process is not None:
        result=process
  elif isinstance( processId, dict ):
    if processId[ 'type' ] == 'iteration':
      return IterationProcess( processId.get('name', 'Iteration'), [ getProcessInstance(i) for i in processId[ 'children' ] ] )
    elif processId[ 'type' ] == 'distributed':
      return DistributedProcess( processId.get('name', 'Distributed iteration'), [ getProcessInstance(i) for i in processId[ 'children' ] ] )
    elif processId['type'] == 'selection' :
      return SelectionProcess( processId.get('name', 'Selection'), [ getProcessInstance(i) for i in processId[ 'children' ] ] )
    else:
      raise TypeError( _t_( 'Unknown process type: %s' ) % ( unicode( processId['type'] ) ) )
  else:
    if type(processId) in types.StringTypes:
      processId=processId.lower()
    result = _processes.get( processId )
  if result is None:
    info = _processesInfo.get( processId )
    if info is None:
      info = _processesInfoByName.get( processId )
    if info is not None:
      result = _processes.get( info.id.lower() )
      if result is None:
        result = readProcess( info.fileName, ignoreValidation=ignoreValidation )
        checkUpdate=False
  if result is not None:
    # Check if process source file have changed
    if checkUpdate:
      fileName = getattr( result, '_fileName', None )
      if fileName is not None:
        ask = _askUpdateProcess.get( result._id, 0 )
        # if the user choosed never updating the process, no need to check if it needs update
        if (ask != 2):
          ntime = os.path.getmtime( fileName )
          if ntime > result._fileTime:
            update = 0
            if ask == 0:
              #if neuroConfig.userLevel > 0:
              r = defaultContext().ask( _t_( '%s has been modified, would you like to update the process <em>%s</em> processes ? You should close all processes windows before reloading a process.' ) % \
                ( result._fileName, _t_(result.name) ), _t_('Yes'), _t_('No'), _t_('Always'), _t_('Never') )
              if r == 0:
                update = 1
              elif r == 2:
                update = 1
                _askUpdateProcess[ result._id ] = 1
              elif r == 3:
                update = 0
                _askUpdateProcess[ result._id ] = 2
            elif ask == 1:
              update = 1
            if update:
              result = readProcess( fileName )
  return result

#----------------------------------------------------------------------------
def getProcessInstanceFromProcessEvent( event ):
  pipelineStructure = event.content.get( 'id' )
  if pipelineStructure is None:
    pipelineStructure = event.content.get( 'pipelineStructure' )
  result = getProcessInstance( pipelineStructure )
  if result is not None:
    for n, v in event.content.get( 'parameters', {} ).get( 'selected', {} ).iteritems():
      try:
        result.setValue( n, v, default=False )
      except KeyError:
        pass
    for n, v in event.content.get( 'parameters', {} ).get( 'default', {} ).iteritems():
      try:
        result.setValue( n, v, default=True )
      except KeyError:
        pass
    stack = [ ( result.executionNode(), k, e.get( 'parameters' ), e[ 'selected' ],
                e.get( 'executionNodes', {} ) ) for k, e in
                event.content.get( 'executionNodes', {} ).iteritems() ]
    while stack:
      eNodeParent, eNodeName, eNodeParameters, eNodeSelected, eNodeChildren = stack.pop( 0 )
      eNode = eNodeParent.child( eNodeName )
      eNode.setSelected( eNodeSelected )
      if eNodeParameters:
        for n, v in eNodeParameters[ 'selected' ].iteritems():
          try:
            eNode.setValue( n, v, default=False )
          except KeyError:
            pass
        for n, v in eNodeParameters[ 'default' ].iteritems():
          try:
            eNode.setValue( n, v, default=True )
          except KeyError:
            pass
      stack += [ ( eNode, k, e.get( 'parameters' ), e[ 'selected' ],
                e.get( 'executionNodes', {} ) ) for k, e in eNodeChildren.iteritems() ]
    windowGeometry = event.content.get( 'window' )
    if windowGeometry is not None:
      result._windowGeometry = windowGeometry
  return result


#----------------------------------------------------------------------------
def getProcessFromExecutionNode( node ):
  nt = type( node )
  if nt is ProcessExecutionNode:
    return node._process
  elif nt is SerialExecutionNode:
    return IterationProcess( node.name(), node.children() )
  elif nt is ParallelExecutionNode:
    return DistributedProcess( node.name(), node._children.values() )
  elif nt is SelectionExecutionNode:
    return SelectionProcess( node.name(), node.children() )

#----------------------------------------------------------------------------
def getProcessInstance( processIdClassOrInstance ):
  result = getProcess( processIdClassOrInstance )
  if isinstance( processIdClassOrInstance, Process ):
    if result is processIdClassOrInstance or result is processIdClassOrInstance.__class__:
      result = processIdClassOrInstance
    else:
      event = ProcessExecutionEvent()
      event.setProcess( processIdClassOrInstance )
      result = getProcessInstanceFromProcessEvent( event )
  elif result is None:
    if isinstance( processIdClassOrInstance, ExecutionNode ):
      result = getProcessFromExecutionNode( processIdClassOrInstance )
    else:
      try:
        if isinstance( processIdClassOrInstance, basestring ) and minfFormat( processIdClassOrInstance )[ 1 ] == minfHistory:
          event = readMinf( processIdClassOrInstance )[0]
          result = getProcessInstanceFromProcessEvent( event )
          if result is not None:
            result._savedAs = processIdClassOrInstance
      except IOError:
        raise KeyError( 'Could not get process "' + processIdClassOrInstance \
            + '": invalid identifier or process file' )
  elif not isinstance( result, Process ):
    result = result()
  return result


#----------------------------------------------------------------------------
def allProcessesInfo():
  return _processesInfo.values()


#----------------------------------------------------------------------------
def getConverter( source, destination, checkUpdate=True ):
  global _processes
  result = _converters.get( destination, {} ).get( source )
  if result is None:
    dt, df = destination
    st, sf = source
    if isSameDiskItemType( st, dt ):
      while result is None and st:
        st = st.parent
        result = _converters.get( ( st, df ), {} ).get( ( st, sf ) )
  return getProcess( result, checkUpdate=checkUpdate )


#----------------------------------------------------------------------------
def getConvertersTo( destination, keepType=1, checkUpdate=True ):
  global _converters
  t, f = destination
  c = _converters.get( ( t, f ), {} )
  if keepType: return c
  while not c and t:
    t = t.parent
    c = _converters.get( ( t, f ), {} )
  return dict([(n,getProcess(p, checkUpdate=checkUpdate)) for n,p in c.items()])


#----------------------------------------------------------------------------
def getConvertersFrom( source, checkUpdate=True ):
  global _converters
  result = {}
  for destination, i in _converters.items():
    c = i.get( source )
    t,f = source
    while not c and t:
      t = t.parent
      c = i.get( ( t, f ) )
    if c:
      result[ destination ] = getProcess( c, checkUpdate=checkUpdate )
  return result


#----------------------------------------------------------------------------
def getViewer( source, enableConversion = 1, checkUpdate=True, listof=False ):
  global _viewers
  global _listViewers
  if listof:
    viewers = _listViewers
  else:
    viewers = _viewers

  if isinstance( source, DiskItem ):
    t0 = source.type
    f = source.format
  elif isinstance( source, list):
    if source != [] and isinstance(source[0], DiskItem):
      t0 = source[0].type
      f=source[0].format
  else:
    t0, f = source
  t = t0
  v = viewers.get( ( t, f ) )
  # if the diskitem has no type, get the more generic viewer that accept the format of the diskitem
  if not v and t is None:
    for k in viewers.keys():
      t0b, fb = k
      if fb == f:
        if t is None or t.isA(t0b):
          t=t0b
          v=viewers.get((t, f))
          if t.parent is None:
            break
  while not v and t:
    t = t.parent
    v = viewers.get( ( t, f ) )
  if not v and enableConversion:
    converters = getConvertersFrom( (t0, f), checkUpdate=checkUpdate )
    t = t0
    while not v and t:
      for tc, fc in converters.keys():
        if ( tc, fc ) != ( t0, f ):
          v = viewers.get( ( t, fc ) )
          if v: break
      t = t.parent
  p =  getProcess( v, checkUpdate=checkUpdate )
  if p and p.userLevel <= neuroConfig.userLevel:
    return p
  if listof:
    if isinstance( source, tuple ) and len( source ) == 2:
      vrs = [ getViewer( source, enableConversion=enableConversion,
                        checkUpdate=checkUpdate ) ]
    else:
      vrs = [ getViewer( s, enableConversion=enableConversion,
                        checkUpdate=checkUpdate ) for s in source ]
    if None not in vrs and len( vrs ) != 0:
      class iterproc( object ):
        def __init__( self, name, procs ):
          self.name = name
          self.procs = procs
        def __call__( self ):
          ip = ListOfIterationProcess( self.name, self.procs )
          return ip
      return iterproc( _t_( 'Viewer for list of ' ) + t0.name, vrs )
  return None


#----------------------------------------------------------------------------
def runViewer( source, context=None ):
  if not isinstance( source, DiskItem ):
    source = ReadDiskItem( 'Any Type', formats.keys() ).findValue( source )
  if context is None:
    context = defaultContext()
  viewer = getViewer( source, checkUpdate=False )
  return context.runProcess( viewer, source )


#----------------------------------------------------------------------------
def getDataEditor( source, enableConversion = 0, checkUpdate=True, listof=False ):
  global _dataEditors
  global _listDataEditors
  if listof:
    dataEditors = _listDataEditors
  else:
    dataEditors = _dataEditors

  if isinstance( source, DiskItem ):
    t0 = source.type
    f = source.format
  elif isinstance( source, list):
    if source != [] and isinstance(source[0], DiskItem):
      t0 = source[0].type
      f=source[0].format
  else:
    t0, f = source
  t = t0
  v = dataEditors.get( ( t, f ) )
  while not v and t:
    t = t.parent
    v = dataEditors.get( ( t, f ) )
  if not v and enableConversion:
    converters = getConvertersFrom( (t0, f), checkUpdate=checkUpdate )
    t = t0
    while not v and t:
      for tc, fc in converters.keys():
        if ( tc, fc ) != ( t0, f ):
          v = dataEditors.get( ( t, fc ) )
          if v: break
      t = t.parent
  p =  getProcess( v, checkUpdate=checkUpdate )
  if p and p.userLevel <= neuroConfig.userLevel:
    return p
  if listof:
    if isinstance( source, tuple ) and len( source ) == 2:
      vrs = [ getDataEditor( source, enableConversion=enableConversion,
                             checkUpdate=checkUpdate ) ]
    else:
      vrs = [ getDataEditor( s, enableConversion=enableConversion,
                             checkUpdate=checkUpdate ) for s in source ]
    if None not in vrs and len( vrs ) != 0:
      class iterproc( object ):
        def __init__( self, name, procs ):
          self.name = name
          self.procs = procs
        def __call__( self ):
          ip = ListOfIterationProcess( self.name, self.procs )
          return ip
      return iterproc( _t_( 'Editor for list of ' ) + t0.name, vrs )
  return None

#----------------------------------------------------------------------------
def getImporter( source, checkUpdate=True ):
  global _processes
  if isinstance( source, DiskItem ):
    t0 = source.type
    f = source.format
  else:
    t0, f = source
  t = t0
  v = _importers.get( ( t, f ) )
  while not v and t:
    t = t.parent
    v = _importers.get( ( t, f ) )
  p =  getProcess( v, checkUpdate=checkUpdate )
  if p:
    return p
  return None


#----------------------------------------------------------------------------
_extToModuleDescription ={
  'py': ('.py', 'r', imp.PY_SOURCE),
  'pyo': ('.py', 'r', imp.PY_COMPILED),
  'pyc': ('.py', 'r', imp.PY_COMPILED),
  'so': ('.so', 'rb', imp.C_EXTENSION),
}

#----------------------------------------------------------------------------
def readProcess( fileName, category=None, ignoreValidation=False, toolbox='brainvisa' ):
  result = None
  try:
    global _processModules, _processes, _processesInfo, _processesInfoByName, _readProcessLog, _askUpdateProcess
    # If we do not remove user level here, default userLevel for process
    # will be this one.
    g = globals()
    try:
      del g[ 'userLevel' ]
    except KeyError:
      pass

    extPos = fileName.rfind('.')
    fileExtension = fileName[ extPos+1: ]
    moduleName = os.path.basename( fileName[ : extPos ] )
    dataDirectory = fileName[ : extPos ] + '.data'
    if not os.path.exists( dataDirectory ):
      dataDirectory = None

    # Load module
    moduleDescription = _extToModuleDescription.get( fileExtension )
    if moduleDescription is None:
      raise RuntimeError( HTMLMessage(_t_( 'Cannot load a process from file <em>%s</em>' ) % (fileName,)) )
    currentDirectory = os.getcwdu()
    fileIn = open( fileName, moduleDescription[ 1 ] )
    try:
      if dataDirectory:
        os.chdir( dataDirectory )
      try:
        processModule = imp.load_module( moduleName, fileIn, fileName, moduleDescription )
      except NameError, e:
        showException(beforeError=( _t_('In <em>%s</em>') ) % ( fileName, ), afterError=_t_(' (perharps you need to add the line <tt>"from neuroProcesses import *"</tt> at the begining of the process)'))
        return
        #raise RuntimeError( HTMLMessage( _t_('In <em>%s</em>')  % ( fileName, ) + " <b>"+str(e)+"</b> "+_t_(' (perharps you need to add the line <tt>"from neuroProcesses import *"</tt> at the begining of the process)') ))
    finally:
      fileIn.close()
      if dataDirectory:
        os.chdir( currentDirectory )

    _processModules[ moduleName ] = processModule

    if category is None:
      category = os.path.basename( os.path.dirname( fileName ) )
    class NewProcess( Process ):
      _instance = 0

    NewProcess._id = moduleName
    NewProcess.name = moduleName
    NewProcess.category = category
    NewProcess.dataDirectory = dataDirectory
    NewProcess.toolbox = toolbox
    # The callback registered in processReloadNotifier are called whenever
    # a change in the process source file lead to a reload of the process.
    # The argument is the new process.
    NewProcess.processReloadNotifier = Notifier( 1 )

    # Optional attributes
    for n in ( 'signature', 'execution', 'name', 'userLevel', 'roles' ):
      v = getattr( processModule, n, None )
      if v is not None:
        setattr( NewProcess, n, v )
    v = getattr( processModule, 'category', None )
    if v is not None:
      NewProcess.category = v

    # Other attributes
    for n, v in processModule.__dict__.items():
      if type( v ) is types.FunctionType and \
        g.get( n ) is not v:
        args = inspect.getargs( v.func_code )[ 0 ]
        if args and args[ 0 ] == 'self':
          setattr( NewProcess, n, v )
          delattr( processModule, n )
        else:
          setattr( NewProcess, n, staticmethod( v ) )


    NewProcess._fileName = fileName
    NewProcess._fileTime = os.path.getmtime( fileName )

    processInfo = ProcessInfo( id = NewProcess._id,
      name = NewProcess.name,
      signature = NewProcess.signature,
      userLevel = NewProcess.userLevel,
      category = NewProcess.category,
      fileName = NewProcess._fileName,
      roles = getattr( NewProcess, 'roles', () ),
      toolbox = toolbox
    )
    _processesInfo[ processInfo.id.lower() ] = processInfo
    _processesInfoByName[ NewProcess.name.lower() ] = processInfo

    NewProcess.module = processInfo.module

    # Process validation
    if not ignoreValidation:
      v = getattr( processModule, 'validation', None )
      if v is not None:
        try:
          v()
        except Exception, e:
          processInfo.valid=False
          if _readProcessLog is not None:
            _readProcessLog.append( NewProcess._id, html=exceptionHTML(), icon='warning.png' )
          raise ValidationError( HTMLMessage(_t_('In <em>%s</em>') % ( fileName, ) + ': ' + str( e )) )

    oldProcess = _processes.get( NewProcess._id.lower() )
    if oldProcess is not None:
      if fileName != oldProcess._fileName:
        defaultContext().warning("Two processes have the same id : "+NewProcess._id.lower()+".", fileName, " process will override ", oldProcess._fileName)
      NewProcess.toolbox = oldProcess.toolbox
      processInfo.toolbox = oldProcess.toolbox
      for n in ( 'execution', 'initialization', 'checkArguments' ):
        setattr( oldProcess, n, getattr( NewProcess, n ).im_func )
      oldProcess._fileTime = NewProcess._fileTime

    _processes[ processInfo.id.lower() ] = NewProcess
    result = NewProcess

    def warnRole( processInfo, role ):
      print >> sys.stderr, 'WARNING: process', processInfo.name, '(' + processInfo.fileName + ') is not a valid', role + '. Add the following line in the process to make it a', role + ':\nroles =', ( role, )
    roles = getattr( processModule, 'roles', () )
#    if NewProcess.category.lower() == 'converters/automatic':
    def _setConverter( source, dest, proc ):
      d = _converters.setdefault( dest, {} )
      oldc = d.get( source )
      if oldc:
        oldproc = getProcess( oldc )
        oldpriority = 0
        if oldproc:
          oldpriority = getattr( oldproc, 'rolePriority', 0 )
        newpriority = getattr( proc, 'rolePriority', 0 )
        if oldpriority > newpriority:
          return # don't register because prioriry is not sufficient
      d[ source ] = proc._id
    if 'converter' in roles:
      global _converters
      possibleConversions = getattr( NewProcess, 'possibleConversions', None )
      if possibleConversions is None:
        sourceArg, destArg = NewProcess.signature.values()[ : 2 ]
        for destFormat in destArg.formats:
          for sourceFormat in sourceArg.formats:
            _setConverter( ( sourceArg.type, sourceFormat ),
              ( destArg.type, destFormat ), NewProcess )
      else:
        for source, dest in possibleConversions():
          source = ( getDiskItemType( source[0] ), getFormat( source[1] ) )
          dest = ( getDiskItemType( dest[0] ), getFormat( dest[1] ) )
          _setConverter( source, dest, NewProcess )

    elif NewProcess.category.lower() == 'converters/automatic':
      warnRole( processInfo, 'converter' )
    if 'viewer' in roles:
#    elif NewProcess.category.lower() == 'viewers/automatic':
      global _viewers
      global _listViewers
      arg = NewProcess.signature.values()[ 0 ]
      if isinstance(arg, ListOf):
        arg=arg.contentType
        if hasattr( arg, 'formats' ):
          for format in arg.formats:
            _listViewers[ ( arg.type, format ) ] = NewProcess._id
      elif hasattr( arg, 'formats' ):
        for format in arg.formats:
          _viewers[ ( arg.type, format ) ] = NewProcess._id
    elif NewProcess.category.lower() == 'viewers/automatic':
      warnRole( processInfo, 'viewer' )
    if 'editor' in roles:
#    elif NewProcess.category.lower() == 'editors/automatic':
      global _dataEditors
      global _listDataEditors
      arg = NewProcess.signature.values()[ 0 ]
      if isinstance(arg, ListOf):
        arg=arg.contentType
        if hasattr( arg, 'formats' ):
          for format in arg.formats:
            _listDataEditors[ ( arg.type, format ) ] = NewProcess._id
      elif hasattr( arg, 'formats' ):
        for format in arg.formats:
          _dataEditors[ ( arg.type, format ) ] = NewProcess._id
    elif NewProcess.category.lower() == 'editors/automatic':
      warnRole( processInfo.fileName, 'editor' )
    if 'importer' in roles:
      global _importers
      sourceArg, destArg = NewProcess.signature.values()[ : 2 ]
      if hasattr( destArg, 'formats' ):
        for format in destArg.formats:
          _importers[ ( destArg.type, format ) ] = NewProcess._id

    if _readProcessLog is not None:
      _readProcessLog.append( processInfo.id,
        html='<h1>' + processInfo.id + '</h1>' + processInfo.html(),
        icon = 'icon_process.png' )

    if oldProcess is not None:
      oldProcess.processReloadNotifier.notify( result )

  except ValidationError:
    raise
  except:
    if _readProcessLog is not None:
      _readProcessLog.append( os.path.basename( fileName ), html=exceptionHTML(), icon='error.png' )
    raise
  return result

#----------------------------------------------------------------------------
def readProcesses( processesPath ):
  # New style processes initialization
  global _processesInfo
  global _allProcessesTree
  processesCacheFile = os.path.join( neuroConfig.homeBrainVISADir, 'processCache-' + neuroConfig.shortVersion )
  processesCache = {}
  if neuroConfig.fastStart and os.path.exists( processesCacheFile ):
    try:
      _processesInfo = cPickle.load( open( processesCacheFile, 'r' ) )
    except:
      raise
      if neuroConfig.mainLog is not None:
        neuroConfig.mainLog.append( 'Cannot read processes cache',
          html=exceptionHTML( beforeError=_t_( 'Cannot read processes cache file <em>%s</em>' ) % ( processCacheFile, ) ),
          icon='warning.png' )

  if neuroConfig.gui or not neuroConfig.fastStart:
    # create all processes tree while reading processes in processesPath
    _allProcessesTree=ProcessTree("Various processes", "all processes",editable=False, user=False)
    for processesDir in processesPath:
      _allProcessesTree.addDir(processesDir, "", processesCache)
    for toolbox in neuroConfig.allToolboxes():
      toolbox.getProcessTree()

    # save processes cache
    try:
      cPickle.dump( _processesInfo, open( processesCacheFile, 'wb' ) )
    except:
      if neuroConfig.mainLog is not None:
        neuroConfig.mainLog.append( 'Cannot write processes cache',
          html=exceptionHTML( beforeError=_t_( 'Cannot write processes cache file <em>%s</em>' ) % ( processesCacheFile, ) ),
          icon='warning.png' )

#----------------------------------------------------------------------------
class ProcessTree( EditableTree ):
  """
  Represents a hierarchy of processes.
  It contains branches : category/directory, and leaves: processes.
  """
  defaultName = "New"

  def __init__( self, name=None, id=None, icon=None, tooltip=None, editable=True, user=True,  content=[]):
    """
    Represents a process tree. It can be a user profile or a default tree.
    This object can be saved in a minf file (in userProcessTree.minf for user profiles). That's why it defines __getinitkwargs__ method.  this method's result is stored in the file and passed to the constructor to restore the object.
    Some changes to the constructor attributes must be reflected in getinitkwargs method, but changes can affect the reading of existing minf files.
    """
    if id is None and name is not None:
      id=string.lower(name)
    super(ProcessTree, self).__init__(_t_(name), id, editable, content)
    self.initName=name
    self.onAttributeChange("name", self.updateName)
    self.user = bool( user )
    if icon is not None:
      self.icon=icon
    elif self.user:
      self.icon = 'folder_home.png'
    else:
      self.icon = 'list.png'
    if tooltip!=None:
      self.tooltip=_t_(tooltip)
    else: self.tooltip=self.name
    self.setValid() # tag the tree as valid or not : it is valid if it contains at least one valid child (or no child)

  def __getinitargs__(self):
    content=self.values()
    return ( self.initName, self.id, self.icon, self.tooltip, self.modifiable, self.user, content )

  def __getinitkwargs__(self):
    content=self.values()
    return ( (), {'name' : self.initName, 'id': self.id, 'icon' : self.icon, 'editable' : self.modifiable, 'user' : self.user, 'content' : content} )

  def addDir(self, processesDir, category="", processesCache={}, toolbox='brainvisa' ):
    """
    @type processesDir: string
    @param processesDir: directory where processes are recursively searched.
    @type category: string
    @param category: category prefix for all processes found in this directory (usefull for toolboxes : all processes category begins with toolbox's name.
    @processesCache: dictionary
    @param processesCache: a dictionary containing previously saved processes info stored by id. Processes that are in this cache are not reread.
    """
    if os.path.isdir( processesDir ):
      stack = [ ( self, processesDir, category ) ]
      while stack:
        parent, dir, category = stack.pop( 0 )
        p = []
        try:
          listdir = os.listdir( dir )
        except:
          showException()
          listdir=[]
        for f in sorted( listdir ):
          ff = os.path.join( dir, f )
          if os.path.isdir( ff ):
            if not ff.endswith( '.data' ):
              if category:
                c = category + '/' + f
              else:
                c = f
              b = ProcessTree.Branch( name=f, id=c.lower(), editable=False )
              parent.add( b )
              stack.append( ( b, ff, c ) )
            else:
              continue
          elif ff.endswith( '.py' ) or ff.endswith('.so'):
            p.append( ( f, ff ) )
        for f, ff in p:
          if not os.path.exists( ff ): continue
          id = f[:-3]
          try:
            processInfo = processesCache.get( id )
            if processInfo is None:
              readProcess( ff, category=category,
                ignoreValidation=neuroConfig.ignoreValidation,
                toolbox=toolbox ) # two arguments : process fullpath and category (directories separated by /)
            else:
              addProcessInfo( id, processInfo )
          except ValidationError:# it may occur a validation error on reading process
            pass
          except:
            showException()
          processInfo = getProcessInfo( id )
          if processInfo is not None:
            l = ProcessTree.Leaf( id=processInfo.id, editable=False)
            parent.add( l )

  def setEditable(self, bool):
    """
    Makes the tree editable. All its children becomes modifiable and deletable.
    """
    self.modifiable=bool
    for item in self.values():
      item.setAllModificationsEnabled(bool)

  def setName(self, n):
    """Renames item. The notifier notifies the change."""
    if self.name==self.tooltip:
      self.tooltip=n # change also the tooltip if it is equal to the name
    EditableTree.setName(self, n)

  def setValid(self):
    """
    Sets the tree as valid if it has no child and it is a user tree or if it has at least one valid child.
    Empty user tree is valid because it can be a newly created user tree and the user may want to fill it later.
    """
    valid=False
    if len(self)==0 and self.user:
      valid=True
    else:
      for item in self.values():
        if item.valid:
          valid=True
          break
    self.valid=valid

  def update(self):
    """
    Updates recursively valid attribute for each item in the tree. This method must be called when the validity may have change. For exemple when the userLevel has changed, some process must become visibles.
    """
    if len(self)==0 and self.user:
      self.valid=True
    else:
      validChild=False
      for item in self.values():
        item.update(self.user)
        if item.valid:
          validChild=True
      self.valid=validChild

  def updateName(self):
    """
    When the tree name is changed after construction. The new name must be saved if the tree is saved in minf file. So change the initName.
    """
    self.initName=self.name

  #----------------------------------------------------------------------------
  class Branch( EditableTree.Branch ):
    """
    A directory that contains processes and/or another branches. Enables to organise processes by category.
    """
    _defaultIcon = 'folder.png'
    defaultName = "New category"

    def __init__( self, name=None, id=None, editable=True, icon=None, content=[] ):
      if icon is None:
        icon = self._defaultIcon
      defaultName = _t_( self.defaultName )
      if id is None or id == defaultName:
        if name is not None and name != defaultName:
          id=string.lower(name)
        else:
          id=None
      #from brainvisa.toolboxes import getToolbox
      #toolbox=getToolbox(id)
      #if toolbox is not None:
         #name=toolbox.name
      # even if the tree isn't editable, copy of elements is enabled
      # (that  doesn't change the tree but enable to  copy elements in another tree)
      super(ProcessTree.Branch, self).__init__(_t_(name), id, icon, _t_("category"), True, editable, editable, content)
      self.initName=name # store the name given in parameters to return in getinitkwargs, so save in minf format will store init name before potential traduction
      self.onAttributeChange("name", self.updateName)
      #EditableTree.Branch.__init__(self, unicode(name), unicode(icon), _t_("category"), True, editable, editable, content)
      self.setValid() # set the validity of the branch relatively to its content. As the branch can be constructed with a content (when it is restored from minf file for example), it is usefull to do so.

    def __getinitargs__(self):
      content=self.values()
      return ( self.initName, self.id, self.modifiable, self.icon, content)

    def __getinitkwargs__(self):
      content=self.values()
      return ( (), {'name' : self.initName, 'id' : self.id, 'editable' : self.modifiable, 'content' : content})

    def __reduce__( self ):
      """This method is redefined for enable deepcopy of this object (and potentially pickle).
      It gives the arguments to pass to the init method of the object when creating a copy
      """
      return ( self.__class__, self.__getinitargs__(), None, None, None )

    def setValid(self):
      """
      Sets the branch as valid if it has no child or if it has at least one valid child.
      Empty branch is valid because it can be a newly created user branch and the user may want to fill it later.
      """
      valid=False
      if len(self)==0:
        valid=True
      else:
        for item in self.values():
          if item.valid:
            valid=True
            break
      self.valid=valid

    def update(self, userTree=False):
      """
      Updates recursively valid attribute for each item in the branch. This method must be called when the validity may have change. For exemple when the userLevel has changed, some processes must become visibles.
      """
      if len(self)==0:
        self.valid=True
      else:
        validChild=False
        for item in self.values():
          item.update(userTree)
          if item.valid:
            validChild=True
        self.valid=validChild

    def updateName(self):
      self.initName=self.name
  #----------------------------------------------------------------------------
  class Leaf( EditableTree.Leaf ):
    """
    A ProcessTree.Leaf represents a process.
    """
    def __init__( self, id, name=None, editable=True, icon=None, *args, **kwargs ):
      processInfo=getProcessInfo(id)
      pname=name
      if name is None:
        pname=id
      if processInfo is not None:
        if name is None:
          pname=processInfo.name
        if icon is None: # set icon according to process role and user level
          if 'viewer' in processInfo.roles:
            icon = 'viewer.png'
          elif 'editor' in processInfo.roles:
            icon = 'editor.png'
          elif 'converter' in processInfo.roles:
            icon = 'converter.png'
          else:
            icon = 'icon_process_' + str( min( processInfo.userLevel, 3 ) ) + '.png'
      super(ProcessTree.Leaf, self).__init__(_t_(pname), id, icon, _t_("process"), True, editable, editable)
      self.initName=name
      self.onAttributeChange("name", self.updateName)
      self.setValid(processInfo)

    def __getinitargs__(self):
      return (self.id, self.initName, self.modifiable, self.icon)

    def __getinitkwargs__(self):
      return ( (), {'id' : self.id, 'name' : self.initName, 'editable' :  self.modifiable}) # do not save icon in minf file for processes because it is determined by its role and user level

    def __reduce__( self ):
      """This method is redefined for enable deepcopy of this object (and potentially pickle).
      It gives the arguments to pass to the init method of the object when creating a copy
      """
      return ( self.__class__,  self.__getinitargs__(), None, None, None )

    def setValid(self, processInfo):
      """
      A ProcessTree.Leaf is valid if the id references a process in _processesInfo and if the process' userLevel is lower or equal than global userLevel and the related process is valid (validation function succeeded).
      """
      valid=False
      if processInfo is not None:
        if (processInfo.userLevel <= neuroConfig.userLevel) and processInfo.valid:
          valid=True
      self.valid=valid

    def update(self, userTree=False):
      """
      Called when the parent tree is updated because some validity conditions have changed.
      Evaluates the validity of the reprensented process.
      """
      processInfo=getProcessInfo(self.id)
      self.setValid(processInfo)

    def updateName(self):
      self.initName=self.name

#----------------------------------------------------------------------------
class ProcessTrees(ObservableAttributes, ObservableSortedDictionary):
  """
  Model for the list of process trees in brainvisa.
  It is a dictionary which maps each tree with its id.
  It contains several process trees :
    - default process trees : all processes in brainvisa/processes (that are not in a toolbox). Not modifiable by user.
    - toolboxes : processes grouped by theme. Not modifiable by user.
    - user process trees : lists created by the user and saved in a minf file.
  A tree can be set as default. It becomes the current tree at Brainvisa start.
  """

  def __init__(self, name=None):
    if name is None:
      name = _t_('Toolboxes')
    # set the selected tree
    super(ProcessTrees, self).__init__()
    self.name=name
    self.userProcessTreeMinfFile=os.path.join( neuroConfig.homeBrainVISADir, 'userProcessTrees.minf' )
    self.selectedTree=None
    self.load()

  def add(self, processTree):
    """
    Add an item in the dictionary. If this item's id is already present in the dictionary as a key, add the item's content in the corresponding key.
    recursive method
    """
    key=processTree.id
    if self.has_key(key):
        for v in processTree.values(): # item is also a dictionary and contains several elements, add each value in the tree item
          self[key].add(v)
    else: # new item
      self[key]=processTree

  def load(self):
    """
    Loads process trees :
      - a tree containing all processes that are not in toolboxes: allProcessesTree;
      - toolboxes as new trees.
      - user trees that are saved in a minf file in user's .brainvisa directory.
    """
    allTree=allProcessesTree()
    self.add(allTree)
    # append toolboxes process trees
    from brainvisa.toolboxes import allToolboxes
    for toolbox in allToolboxes(): # add each toolbox's process tree
      self.add(toolbox.getProcessTree())
      # no longer add toolboxes in allProcessesTree, it was redundant
      # and add the toolbox as a branch in all processes tree
      #allTree.add(ProcessTree.Branch(toolbox.processTree.name, toolbox.processTree.id, False, toolbox.processTree.icon, toolbox.processTree.values()))
    for toolbox in allToolboxes(): # when all toolbox are created, add links from each toolbox to others
      for processTree in toolbox.links():
        self.add(processTree) # if a toolbox with the same id already exists, it doesn't create a new tree but update the existing one
        # report the links in the toolbox that are in all processes tree
        #if processTree.id != allTree.id: # except if the links points directly to all processes tree, in that case, there's nothing else to do
        #  allTree.add(ProcessTree.Branch(processTree.name, processTree.id, False, processTree.icon, processTree.values()))
    # sort processes in alphabetical order in toolboxes and in all processes tree
    for toolbox in allToolboxes():
      toolbox.processTree.sort()
    allTree.sort()
    # append other trees here if necessary
    # ....
    # load user trees from minf file
    userTrees=None
    currentTree=None
    if os.access(self.userProcessTreeMinfFile, os.F_OK): # if the file exists, read it
      try:
        format, reduction=minfFormat( self.userProcessTreeMinfFile )
        if (format=="XML") and (reduction=="brainvisa-tree_2.0"):
          userTrees, currentTree=iterateMinf( self.userProcessTreeMinfFile )
      except:
        print "Error while reading", self.userProcessTreeMinfFile
    if userTrees != None:
      for userTree in userTrees:
        self.add(userTree)
    # search selected tree.
    if currentTree is not None:
      # The id of the selected tree is stored in the minf file. But before, the name was stored, so if the value is not a key, search by names
      if self.has_key(currentTree):
        self.selectedTree=self[currentTree]
      else:
        for tree in self.values():
          if tree.name==currentTree:
            self.selectedTree=tree
            break
    else:
      self.selectedTree=None
    # update items validity it depends on processes validity and user level : must update to invalid branches that only contain invalid items
    self.update()

  def save(self):
    """
    Write trees created by the user in a minf file to restore them next time Brainvisa starts.
    """
    writer = createMinfWriter( self.userProcessTreeMinfFile, reducer='brainvisa-tree_2.0' )
    # save trees created by user
    writer.write( [ i for i in self.values() if i.user] )
    # save selected tree name
    if self.selectedTree is not None:
      writer.write(self.selectedTree.id)
    else:
      writer.write(None)
    writer.close()

  def update(self):
    """
    Updates all trees (evaluates validity of each items).
    """
    for item in self.values():
      item.update()
#----------------------------------------------------------------------------
_mainProcessTree = None
def updatedMainProcessTree():
  """
  @rtype: ProcessTrees
  @return: Brainvisa list of trees :  all processes tree, toolboxes, user trees
  """
  global _mainProcessTree
  if _mainProcessTree is None:
    _mainProcessTree = ProcessTrees()
  return _mainProcessTree

#----------------------------------------------------------------------------
def allProcessesTree():
  """
  Get the tree that contains all processes. It is created when processes in processesPath are first read.
  Toolboxes processes are also added in this tree.
  @rtype: ProcessTree
  @return: the tree that contains all processes.
  """
  global _allProcessesTree
  return _allProcessesTree

#----------------------------------------------------------------------------
def updateProcesses():
  """
  Called when option userLevel has changed (neuroConfigGUI.validateOptions()).
  Associated widgets will be updated automatically because they listens for changes.
  """
  _mainProcessTree.update()

#----------------------------------------------------------------------------
def mainThread():
  return _mainThread

#----------------------------------------------------------------------------
def defaultContext():
  return _defaultContext


#----------------------------------------------------------------------------
def initializeProcesses():
  #TODO: A class would be more clean instead of all these global variables
  global _processModules, _processes, _processesInfo, _processesInfoByName, \
         _converters, _viewers, _listViewers, _mainThread, _defaultContext, _dataEditors, _listDataEditors, _importers,\
         _askUpdateProcess, _readProcessLog
  _mainThread = threading.currentThread()
  _processesInfo = {}
  _processesInfoByName = {}
  _processes = {}
  _processModules = {}
  _askUpdateProcess = {}
  _converters = {}
  _viewers = {}
  _listViewers = {}
  _dataEditors = {}
  _listDataEditors = {}
  _importers = {}
  _defaultContext = ExecutionContext()
  if neuroConfig.mainLog is not None:
    _readProcessLog = neuroConfig.mainLog.subLog()
    neuroConfig.mainLog.append( _t_('Read processes'),
      html='<em>processesPath</em> = ' + str( neuroConfig.processesPath ),
      children=_readProcessLog, icon='icon_process.png' )
  else:
    _readProcessLog = None
  atexit.register( cleanupProcesses )


#----------------------------------------------------------------------------
def cleanupProcesses():
  global _processModules, _processes, _processesInfo, _processesInfoByName, \
         _converters, _viewers, _listViewers, _mainThread, _defaultContext, _dataEditors, _listDataEditors, _importers, \
         _askUpdateProcess, _readProcessLog
  _converters = {}
  _viewers = {}
  _listViewers = {}
  _dataEditors = {}
  _listDataEditors = {}
  _importers = {}
  _processesInfo = {}
  _processesInfoByName = {}
  _processes = {}
  _processModules = {}
  _askUpdateProcess = {}
  _mainThread = None
  _defaultContext = None
  if _readProcessLog is not None:
    _readProcessLog.close()
    _readProcessLog = None

# ---

if not _neuroDistributedProcesses:
  # TODO: use log
  if globals().has_key( '_t_' ):
    logmsg = _t_( 'Distributed execution has been disabled due to the ' \
      'following error:<br>' )
  else: # in case _t_ has not been loaded yet
    logmsg = 'Distributed execution has been disabled due to the ' \
      'following error:<br>'
  logmsg += str( neuroDistribException )
  #defaultContext().log( \
    #_t_( 'Distributed execution' ), html=logmsg, icon='warning' )
  print logmsg
  del neuroDistribException, logmsg




import neuroHierarchy
from neuroHierarchy import *
from brainvisa.history import HistoryBook, minfHistory
