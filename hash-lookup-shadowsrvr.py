#!/usr/bin/env python
#  Written by:  Jose Nazario (jose@arbor.net)
import os
import simplejson
import sys

def whitelisted(hashfile):
    p = os.popen('curl -s http://bin-test.shadowserver.org/api -F filename.1=@%s' % hashfile)
    data = p.read()
    p.close()
    res = {}
    for line in data.split('\n'):
        l = line.split(' ', 1)
        if len(l) == 2:
            try: res[l[0]] = simplejson.loads(l[1])
            except: pass
    return res

res = whitelisted(sys.argv[1])
print res.keys()
