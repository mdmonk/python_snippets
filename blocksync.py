#!/usr/bin/env python
"""
blocksync.py

Sync block devices over the network
 Copyright 2006-2008 Justin Azoff <justin@bouncybouncy.net>

  License:
      GPL

"""
import sys
import md5
import os

SAME = "same\n"
DIFF = "diff\n"

def do_open(f, mode):
    f = open(f, mode)
    f.seek(0, 2)
    size = f.tell()
    f.seek(0)
    return f, size

def getblocks(f, blocksize):
    while 1:
        block = f.read(blocksize)
        if not block:
            break
        yield block


def server(dev, blocksize):
    print dev, blocksize
    f, size = do_open(dev, 'r+')
    print size
    sys.stdout.flush()

    for block in getblocks(f, blocksize):
        print md5.md5(block).hexdigest()
        sys.stdout.flush()
        res = sys.stdin.readline()
        if res != SAME:
            newblock=sys.stdin.read(blocksize)
            f.seek(-blocksize, 1)
            f.write(newblock) 

def sync(srcdev, dsthost, dstdev=None, blocksize=1024*1024):

    if not dstdev:
        dstdev = srcdev
    
    cmd = "ssh -c blowfish %s blocksync.py server %s -b %d" % (dsthost, dstdev, blocksize)
    print cmd
    p_in, p_out = os.popen2(cmd)#, bufsize=blocksize)

    line = p_out.readline()
    a, b = line.split()
    assert a==dstdev and int(b)==blocksize

    f, size = do_open(srcdev, 'r')

    remote_size  = int(p_out.readline())
    assert size == remote_size

    same_blocks = diff_blocks = 0

    for l_block in getblocks(f, blocksize):
        l_sum   = md5.md5(l_block).hexdigest()
        r_sum = p_out.readline().strip()

        #print l_sum, r_sum, l_sum==r_sum
        if l_sum == r_sum:
            p_in.write(SAME)
            p_in.flush()
            same_blocks += 1
        else :
            p_in.write(DIFF)
            p_in.flush()
            p_in.write(l_block)
            p_in.flush()
            diff_blocks += 1

        print "\rsame: %d, diff: %d, %d/%d" % (same_blocks, diff_blocks, same_blocks+diff_blocks, size / blocksize),
    print

    return same_blocks, diff_blocks

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser(usage="%prog [options] /dev/source host [/dev/dest]")
    parser.add_option("-b", "--blocksize", dest="blocksize", action="store", type="int", help="block size", default=1024*1024)
    (options, args) = parser.parse_args()

    if len(args) < 2:
        parser.print_help()
        sys.exit(1)

    if args[0] == 'server':
        dstdev = args[1]
        server(dstdev, options.blocksize)
    else :
        srcdev  = args[0]
        dsthost = args[1]
        if len(args) > 2:
            dstdev = args[2]
        else :
            dstdev = None
        sync(srcdev, dsthost, dstdev, options.blocksize)
