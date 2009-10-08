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