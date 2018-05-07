#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, platform, sys
from brainvisa.configuration import neuroConfig
try:
    import six.moves.urllib.request as urllib2
except ImportError:
    # some six versions do not provide six.moves.urllib (Ubuntu 12.04)
    import urllib2
import six

filesaddress = 'ftp://ftp.cea.fr/pub/dsv/anatomist/binary'

def checkUpdates():
    '''Checks on the BrainVisa servers if there is a newer version than the
    current one. If so, a tuple is returned, containing 3 elements:
    ( version, file, exact_arch )

    * version is the highest version found on the server
    * file is the URL of the latest binary package
    * exact_arch is True if the latest package is found for the same exact
    achitecture, False if it is a compatible, but different architecture (i686
    on a x86_64)
    '''
    refversion = [ int(x) for x in neuroConfig.versionString().split( '.' ) ]

    sysnames = { 'Fedora' : 'linux2', 'Mandriva' : 'linux2',
        'Ubuntu' : 'linux2', 'MacOS' : 'darwin', 'Windows' : 'win32' }
    archs = { 'i686' : '32bit', 'x86_64' : '64bit' }

    # timeout parameter does not exists in python 2.5
    #lines = urllib2.urlopen( filesaddress, timeout=3 ).readlines()
    try:
      lines = urllib2.urlopen(filesaddress, timeout=5).readlines()
    except: # the network may be not available
      lines = []
    rexp = re.compile( \
        '^.*(brainvisa-(.*)-(i686|x86_64).*-([^-]+)-.*)\.README.*$' )
    upgrade = False
    exactarch = None
    compatiblearch = None
    if sys.version_info[0] >= 3:
        decode = True
    else:
        decode = False
    for l in lines:
        if decode:
            l = l.decode()
        m = rexp.match( l )
        if not m:
            continue
        system = m.group(2)
        osid = None
        for s, sid in six.iteritems(sysnames):
            if system.startswith( s ) and sys.platform == sid:
                osid = sid
                break
        if not osid:
            continue
        arch = m.group(3)
        if archs[ arch ] != platform.architecture()[0] \
            and ( arch != 'i686' or platform.architecture()[0] != '64bit' ):
            continue
        version = [ int(x) for x in m.group(4).split('.') ]
        if version > refversion:
            upgrade = True
            if archs[ arch ] == platform.architecture()[0]:
                if not exactarch or version > exactarch[0]:
                    exactarch = [ version, m.group(1) ]
            else:
                if not compatiblearch or version > compatiblearch[0]:
                    compatiblearch = [ version, m.group(1) ]
    highest = None
    if upgrade:
        if exactarch:
            #print 'can upgrade to:', exactarch
            highest = ( exactarch[0], filesaddress + '/' + exactarch[1], True )
        if compatiblearch and \
            ( not exactarch or compatiblearch[0] > exactarch[0] ):
            #print 'higher compatible version:', compatiblearch
            highest = ( compatiblearch[0],
                filesaddress + '/' + compatiblearch[1], False )

    if highest:
        if sys.platform == 'win32':
            highest = ( highest[0], highest[1] + '.zip', highest[2] )
        else:
            highest = ( highest[0], highest[1] + '.tar.gz', highest[2] )
    return highest

