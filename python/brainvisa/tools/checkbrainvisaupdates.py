#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import re
from brainvisa.configuration import neuroConfig

import six
import six.moves.urllib.request
from six.moves.urllib.error import URLError

filesaddress = 'https://brainvisa.info/neuro-forge/linux-64'


def checkUpdates():
    '''Checks on the BrainVisa servers if there is a newer version than the
    current one. If so, a tuple is returned, containing 3 elements:
    ( version, file, exact_arch )

    * version is the highest version found on the server
    * file is the URL of the latest binary package
    * exact_arch is True if the latest package is found for the same exact
    achitecture, False if it is a compatible, but different architecture (i686
    on a x86_64). In Singularity/apptainer releases it is always True.
    '''
    refversion = [int(x) for x in neuroConfig.versionString().split('.')]

    try:
        lines = six.moves.urllib.request.urlopen(filesaddress,
                                                 timeout=5).readlines()
    except URLError:  # the network may be not available
        lines = []
    rexp = re.compile('^.*(axon-([0-9\.]+)-.*\.conda).*$')
    bvrexp = re.compile('^.*(brainvisa-([0-9\.]+)-.*\.conda).*$')
    upgrade = False
    highest_ver = None
    highest = None
    bv_highest_ver = None
    for l in lines:
        l = six.ensure_str(l)
        m = rexp.match(l)
        if m:
            version = [int(x) for x in m.group(2).split('.')]
            if version > refversion:
                upgrade = True
                if highest_ver is None or version > highest_ver:
                    highest_ver = version
                    highest = m.group(1)
        else:
            m = bvrexp.match(l)
            if not m:
                continue
            version = [int(x) for x in m.group(2).split('.')]
            if bv_highest_ver is None:
                bv_highest_ver = version
            elif version > bv_highest_ver:
                bv_highest_ver = version
    if upgrade:
        highest = (highest_ver,
                   filesaddress + '/' + highest, True, bv_highest_ver)

    return highest
