#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from brainvisa import axon
import sys
import time
import traceback
from optparse import OptionParser

parser = OptionParser(
    description='Parse BV history items and inserts outputs of processes that have run into the database. Databases need to be already setup in BrainVisa.')
parser.add_option('-i', '--input', dest='infile',
                  help='input history file (.bvproc)', action='append', default=[])
parser.add_option('-d', '--dir', dest='dir',
                  help='input history_book directory')
parser.add_option('-n', '--newer', dest='newer',
                  help='read only items newer than <date> in a history_book directory. format: 2012/11/15 or 2012/11/15 18:41:00')
parser.add_option('-r', '--remove', dest='remove', action='store_true',
                  help='remove obsolete history files (referencing only output files that have been rewritten by newer histoty files)')
parser.add_option('-s', '--simulation', dest='simulation', action='store_true',
                  help='Simulation mode (dry run). Don\'t insert elements in the databases nor remove obsolete history files. Just parse files and look at what should have to be done.')


options, args = parser.parse_args()
infiles = options.infile
newdate = options.newer
directory = options.dir
removeold = options.remove
simulation = options.simulation
if simulation:
    removeold = False

if (not infiles and not directory) or len(args) != 0:
    parser.print_help()
    sys.exit(1)

if newdate:
    try:
        t = time.mktime(time.strptime(newdate, "%Y/%m/%d"))
    except:
        t = time.mktime(time.strptime(newdate, "%Y/%m/%d %H:%M:%S"))
    print('date:', t)

axon.initializeProcesses()

from brainvisa.processes import *

if directory:
    print('reading history book directory...')
    for f in os.listdir(directory):
        if f.endswith('.bvproc'):
            ff = os.path.join(directory, f)
            if newdate:
                s = os.stat(ff)
                if s.st_mtime >= t:
                    infiles.append(ff)
            else:
                infiles.append(ff)
    print('done.')

print('parsing %d history files...' % len(infiles))
toadd = set()
deadhistories = set()
livehistories = set()
scanned = 0
for bvprocfile in infiles:
    try:
        p = readMinf(bvprocfile)[0]  # ProcessExecutionEvent object
    except Exception as e:
        print('error reading', bvprocfile)
        traceback.print_exc()
        continue
    idf = os.path.basename(bvprocfile)
    idf = idf[: idf.rfind('.')]
    halive = False

    for par in p.content.get('modified_data', []):
        addit = False
        try:
            item = neuroHierarchy.databases.getDiskItemFromFileName(par)
            # already exists in DB: no need to add it
        except:
            try:
                item = neuroHierarchy.databases.createDiskItemFromFileName(
                    par)
                addit = True
            except:
                print(
                    'Warning: file', par, 'cannot be inserted in any database.')
                continue
        scanned += 1
        if item is not None and isinstance( item, DiskItem ) \
            and item.isReadable() and item.get("_database", None) and \
                (not hasattr(item, '_isTemporary') or not item._isTemporary):
            if addit:
                toadd.add(item)
            lasth = item.get('lastHistoricalEvent', None)
            if lasth is not None and lasth == idf:
                halive = True
    if not halive:
        # print('history file', bvprocfile, 'is obsolete')
        deadhistories.add(bvprocfile)
    else:
        livehistories.add(bvprocfile)
print('parsing done. Scanned %d files/items.' % scanned)
print()
print('living history files:', len(livehistories))
print('dead history files:', len(deadhistories))
print()

if removeold:
    print('removing dead histories...')
    for bvprocfile in deadhistories:
        os.unlink(bvprocfile)
    print('done.')

print('adding %d disk items...' % len(toadd))
if simulation:
    print('Nothing changed: we are in simulation mode.')
else:
    for item in toadd:
        try:
            # print('adding', item)
            neuroHierarchy.databases.insertDiskItem(item, update=True)
        except NotInDatabaseError:
            pass
        except:
            showException()
    print('done.')
