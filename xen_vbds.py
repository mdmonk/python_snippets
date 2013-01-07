#!/usr/bin/env python
import sys
sys.path.append('/usr/lib/xen-3.0.3-1/lib/python/')

from xen.xend.XendClient import server
from xen.xend import sxp


def get_vbd_paths(domain):
    info = server.xend.domain(domain)
    devices = [x[1] for x in sxp.children(info,'device')]
    vbds = sxp.children(devices,'vbd')
    for vbd in vbds:
        path = sxp.child_value(vbd,'uname')
        if path.startswith("phy:"):
            path = path.replace("phy:", "/dev/")
        elif path.startswith("file:"):
            path = path.replace("file:", "")
        else :
            raise 'not handled'
        yield path

if __name__ == "__main__":
    paths = get_vbd_paths(sys.argv[1])
    for p in paths:
        print p
