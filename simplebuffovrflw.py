#!/usr/bin/python
# simple buffer brute force tool
# syndrowm 2007-03-16

import sys
import os

def usage():
        print 'Usage: %s <program> [lower] [higher]' % sys.argv[0]
        sys.exit(0)

if len(sys.argv) - 1 < 1:
        usage()

try:
        program = sys.argv[1]
        lower = int(sys.argv[2])
        higher = int(sys.argv[3])
        higher = higher + 1
except:
        print 'Using default range 1 100'
        lower = 1
        higher = 101

if (os.access(program, os.X_OK)) != 1:
        print '%s does not exist' % program
        usage()

n = range(lower,higher)

for x in n:
        b = "A"*x
        #print x, b
        e = os.system('%s %s' % (program, b))
        if e != 0:
                if e == 139:
                        print x, e, "Segmentation fault \m/:(|)\m/"
                else:
                        print x, e, "Unknown"
