#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: iphonebackupdb.py,v 1.2 2010/05/28 08:30:38 mstenber Exp $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
#  Copyright (c) 2009 Markus Stenberg
#       All rights reserved
#
# Created:       Tue Mar 31 13:44:03 2009 mstenber
# Last modified: Thu Aug  5 21:51:34 2010 mstenber
# Edit time:     150 min
#
"""

This is a minimalist module which abstracts the iPhone backup
directory's contents (in the Library/Applicatuon
Support/MobileSync/backup) as a filesystem. Only supported operation
is right now copying a file for read-only use, but in theory some
other things might be also diable later on (listdir etc).

XXX - turn this to a FUSE module?

On the other hand, why bother.. Currently this is like 3rd version of
iTunes backup DB that I'm supporting;

- pre-8.1 (.mdbackup files, plists with binary content)
- 8.2+ (.mdinfo files, readable plists with nested plists)
- 9.2+ (.mbdb, .mbdx index files + files as-is)

Disclaimer: This module is published for information purposes, and
it's usefulness for anyone else except me may be highly
questionable. However, it might serve some useful purpose to other
people too, so I keep it on my web site.. ;-)

(I know quite a bit more about the un-decoded fields in the .mbdb, but
as my application only needs this stuff, I can't be arsed to decode
them anytime soon.. basic UNIX backup stuff like permissions, uid/gid,
and so forth.)

"""
import os, os.path
import ms.debug, ms.util
import ms.hexdump
import ms.cstruct

#ms.debug.setModuleLevel('.*', 3)
(error, log, debug) = ms.debug.getCalls('iphonebackupdb')

BACKUPPATH=os.path.join(os.environ['HOME'], 'Library',
                        'Application Support',
                        'MobileSync', 'backup')

# Test data - not really used for anything if system works correctly,
# but they were useful when debugging the format
KNOWN = {'documents/rahat.pdb' : 'b07ac15b5c745a287d3ecdc60bb6f6b955c0f229',
         'documents/untitled.pdb': '27fe99e8746b43a9db00c332966d028998bc3a03',
         'Documents/Py%F6r%E4ily.PDB'.lower(): '95ef4154eedac2fcc458cf21ec93c8c3895d9fcb'}

mbdx_struct = ms.cstruct.CStruct('''
byte sha[20];
__u32 ofs;
__u16 junk;
''', formatPrefix="!")

def getMTime():
    mtime = None
    for iphone in os.listdir(BACKUPPATH):
        ipath = os.path.join(BACKUPPATH, iphone)
        imtime = ms.util.file_mtime(ipath)
        if mtime is None or mtime < imtime:
            mtime = imtime
    return imtime

def getS(data, ofs, defaultFF=False):
    if defaultFF:
        if data[ofs] == chr(0xFF):
            assert data[ofs+1] == chr(0xFF)
            return ofs+2, ''
    # Assume first digit is zero.. smirk. Seems to be a short.
    assert data[ofs] == chr(0)
    ofs += 1
    l = ord(data[ofs])
    ofs += 1
    return ofs+l, data[ofs:ofs+l]

def getN(data, ofs, count):
    return ofs+count, data[ofs:ofs+count]

def decodeMBDB(data):
    ofs = 6
    lofs = -1
    filenames = []
    while (ofs+20) < len(data):
        #debug('iter %r', ofs)
        assert ofs != lofs
        #print ms.hexdump.hexdump(data[ofs:ofs+150])
        lofs = ofs
        ofs, vendor = getS(data, ofs)
        ofs, filename = getS(data, ofs)
        #print vendor, filename
        ofs, bonus1 = getS(data, ofs, True)
        ofs, bonus2 = getS(data, ofs, True)
        ofs, bonus3 = getS(data, ofs, True)
        #print ms.hexdump.hexdump(data[ofs:ofs+100])
        ofs, garbage = getN(data, ofs, 39)
        ofs, cnt = getN(data, ofs, 1)
        filenames.append([lofs, vendor, filename, bonus1])
        bonuscount = ord(cnt)
        assert bonuscount <= 6, bonuscount
        bonus = []
        if bonuscount:
            for i in range(bonuscount):
                ofs, xxx = getS(data, ofs)
                ofs, yyy = getS(data, ofs)
                bonus.append((xxx, yyy))
        debug('idx#%d ofs#%d->%d %r %r (%d bonus %s)', len(filenames), lofs, ofs, vendor, filename, bonuscount, bonus)
    return filenames

def decodeMBDX(data):
    ofs = 4
    shas = []
    #print ms.hexdump.hexdump(data[ofs:ofs+150])
    assert data[ofs] == chr(2) # version check?
    assert data[ofs+1] == chr(0)
    ofs += 2
    assert data[ofs] == chr(0)
    assert data[ofs+1] == chr(0)
    ofs += 2 # more 0s
    # Then there's two bytes of .. something ..
    ofs, xxx = getN(data, ofs, 2)
    lofs = None
    while (ofs + 20) < len(data):
        #print 'iter', ofs
        assert ofs != lofs
        lofs = ofs
        #print ms.hexdump.hexdump(data[ofs:ofs+150])
        e = mbdx_struct.unpackOffset(data, ofs, 0)
        assert mbdx_struct.getSize() == 26 # sanity check
        ofs += mbdx_struct.getSize()
        sha = e.sha
        fofs = e.ofs
        assert len(sha) == 20
        sha = "".join(map(lambda x:'%02x' % x, sha))
        debug('idx#%d ofs#%d %r %r', len(shas), lofs, fofs, sha)
        assert fofs <= 10 * 65536 # sanity check - less than 650k Manifest.mbdb
        shas.append((sha, fofs))
    return shas

def getFileToFilename(backuppath, destfilename):
    """ iphone database format 4 reader/decoder - this is 'simplified'
    version which will hopefully eventually work correctly."""
    l = []
    for iphone in os.listdir(BACKUPPATH):
        ipath = os.path.join(BACKUPPATH, iphone)
        l.append((os.stat(ipath).st_mtime, iphone, ipath))
    l.sort()
    l.reverse()
    for _, iphone, ipath in l:
        debug('ipath:%r', ipath)
        filename = os.path.join(ipath, 'Manifest.mbdb')
        debug('opening %r', filename)
        data = open(filename).read()
        filenames = decodeMBDB(data)
        log('decoded %d filenames', len(filenames))
        # Ok. Then parse through the .mdbx file
        data = open(os.path.join(ipath, 'Manifest.mbdx')).read()
        shas = decodeMBDX(data)
        log('decoded %d sha hashes', len(shas))
        assert len(shas) == len(filenames)
        # Create
        # - convenience mapping of file-name => file-ofs from 'filenames'
        # - convenience mapping of file-ofs => hash-name from 'shas'
        fileMap = {}
        rFileMap = {}
        for lofs, vendor, filename, bonus1 in filenames:
            lofs -= 6 # 6 = start of mbdb
            filename = filename.lower()
            fileMap[filename] = lofs
            rFileMap[lofs] = filename
        for sha, fofs in shas:
            fileMap[rFileMap[fofs]] = sha

        # Test how many of the files really exists
        # Hardcoded check
        bpl = backuppath.lower()

        sha = fileMap.get(bpl, '')
        if sha:
            if KNOWN.has_key(bpl):
                if sha != KNOWN[bpl]:
                    log('!!! WRONG sha: %s <> %s', sha, KNOWN[bpl])
                    sha = KNOWN[bpl]
            path = os.path.join(ipath, sha)
            log('found potential sha candidate %r', path)
            if ms.util.file_exists(path):
                log('and it even existed! yay')
                open(destfilename, 'w').write(open(path).read())
                return True
            else:
                log('Path %r not found', path)
        else:
            log('No sha found for %r', bpl)
    return False

if __name__ == '__main__':
    tfilename = '/tmp/test-iphonebackupdb.dat'
    assert getFileToFilename('documents/rahat.pdb', tfilename)
    assert not getFileToFilename('documents/rahat.pdbxxx', tfilename)
    os.unlink(tfilename)


