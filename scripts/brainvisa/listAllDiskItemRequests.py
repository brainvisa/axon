from neuroProcesses import *

requests = {}
requestsAccess = {}
for pi in allProcessesInfo():
  process = getProcess( pi.id, ignoreValidation=True )
  if process is None:
    print >> sys.stderr, 'WARNING: Cannot instanciate process', repr( pi.id )
    continue
  for attrName, attrType in process.signature.items():
    if isinstance( attrType, ReadDiskItem ):
      rdi = attrType
    elif isinstance( attrType, ListOf ) and isinstance( attrType.contentType, ReadDiskItem ):
      rdi = attrType.contentType
    else:
      rdi is None
    if rdi is not None:
      write = isinstance( rdi, WriteDiskItem )
      type = rdi.type.name
      formats = tuple( sorted( i.name for i in getFormats( rdi.formats ) ) )
      required = tuple( sorted( ( i, j ) for i, j in  rdi.requiredAttributes.iteritems() if i not in ( '_format', '_type' ) ) )
      request = ( type, formats, required )
      requests.setdefault( request, set() ).add( pi )
      requestsAccess.setdefault( request, [ None, None ] )[ 1 if write else 0 ] = True

destDir='diskItemRequests'
if not os.path.exists( destDir ):
  os.makedirs( destDir )
index = open( os.path.join( destDir, 'index.html' ), 'w' )
print >> index, '''<html>
<head>
<title>Database requests embedded in BrainVISA ''' + versionString() + ''' processes</title>
</head>
<body>
<h1>Database requests embedded in BrainVISA ''' + versionString() + ''' processes</h1>
<a href="allRequests.html">All requests (''' + str( len( requests ) ) + ''')</a><p/>
</body>
</html>
'''
index.close()


allRequests = open( os.path.join( destDir, 'allRequests.html' ), 'w' )
print >> allRequests, '''<html>
<head>
<title>All requests embedded in BrainVISA ''' + versionString() + ''' processes</title>
</head>
<body>
<h1>All requests embedded in BrainVISA ''' + versionString() + ''' processes</h1>
'''
count = 1
requestsOrder = {}
for request in sorted( requests.iterkeys() ):
  type, formats, required = request
  requestsOrder[ request ] = count
  read, write = requestsAccess[ request ]
  if read:
    if write:
      access = 'read/write'
    else:
      access = 'read'
  else:
    access = 'write'
  print >> allRequests, '<h2>Request ' + str( count ) + '</h2>'
  print >> allRequests, '<b>Type:</b> ' + htmlEscape( type ) + '<br/>'
  print >> allRequests, '<b>Access:</b> ' + access + '<br/>'
  print >> allRequests, '<b>Formats:</b><blockquote>'
  for format in formats:
    formatName = htmlEscape( format )
    print >> allRequests, '<a href="format_' + formatName + '">' + formatName + '</a><br/>'
  print >> allRequests, '</blockquote>'
  if required:
    print >> allRequests, '<b>Attributes:</b><blockquote>'
    for n, v in required:
      print >> allRequests, n + ' = ' + htmlEscape( repr( v ) ) + '<br/>'
    print >> allRequests, '</blockquote>'
  
  print >> allRequests, '<b>Used in the following processes:</b><blockquote>'
  for pi in requests[ request ]:
    print >> allRequests, '<a href="process_' + pi.id + '">' + htmlEscape( pi.name ) + '</a><br/>'
  print >> allRequests, '</blockquote><hr/>'
  count += 1
print >> allRequests, '''</body>
</html>
'''
allRequests.close()
print 'Total:', len( requests )