#!/usr/bin/env python
import time as t
import sys

if __name__ == "__main__":

    while 1 == 1:
        print "\x1B[H\x1B[J"
        xtmp = t.localtime(t.time())
        # xstr = '%d-%d-%d 16:30' % (xtmp[0], xtmp[1], xtmp[2])
        xstr = '2011-04-01 16:00'
	print "xstr = %s" % xstr
        end = t.mktime(t.strptime(xstr, '%Y-%m-%d %H:%M'))

        if end < t.time():
            print "after %s, your dnoe." % xstr
            sys.exit(0)

        diff = end - t.time()
        hours = int(diff / 3600)
        if hours != 0:
            diff = diff - (hours * 3600)
        minutes = int(diff / 60)
        if minutes != 0:
            diff = diff - (minutes * 60)
    
        print "%.02d hour[s] %.02d minute[s] %.02d second[s] left" % \
                ( hours, minutes, diff)
        t.sleep(1)
