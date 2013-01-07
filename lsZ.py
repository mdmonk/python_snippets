#!/usr/bin/env python
# Evan 2007/11/16
# list SElinux attributes with color inspired by this:
# http://blog.gnist.org/article.php?story=RHEL5-SELinux-Benchmark
import os, curses, re, sys

def chomp(line):
     if line[-1:] == '\n':
         line = line[:-1]
     line = re.sub('\s', '', line)
     return line

if __name__ == "__main__":
     xuser = re.compile('([\w]+):')
     xrole = re.compile(':([\w]+_[\w]+):')
     xtype = re.compile(':([\w]+_[\w]+)')

     # curses!
     curses.setupterm()
     cap = curses.tigetstr('setf')
     GREEN = curses.tparm(cap, 2)
     CYAN = curses.tparm(cap, 3)
     MAG = curses.tparm(cap, 5)
     YELL= curses.tparm(cap, 6)
     RESET = curses.tparm(cap, 9)

     print len(sys.argv)
         
     if not sys.stdin.isatty():
         arg = []
         for i in sys.stdin.readlines():
             arg.append(chomp(i))
         xlist = os.popen('/bin/ls -Zd %s' % " ".join(arg))
     elif not len(sys.argv) > 1:
         xlist = os.popen('/bin/ls -Z')
     else:
         xlist = os.popen('/bin/ls -Zd %s' % " ".join(sys.argv[1:]))

     for i in xlist:
         xa = re.sub(xuser, ("%s%s%s:" % (MAG, r'\1', RESET)), i, count=1)
         xa = re.sub(xrole, (":%s%s%s:" % (YELL, r'\1', RESET)) , xa, count=1)
         xa = re.sub(xtype, (":%s%s%s" % (CYAN, r'\1', RESET)) , xa, count=1)
         print xa,
