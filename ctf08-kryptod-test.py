#!/usr/bin/env python
# written by team Robot Mafia (mantis) for CTF'08
#
#import string
from socket import *

alph = "abcdefghijklmnopqrstuvwxyz"
hexlist = []
hexpw = []        

if __name__ == "__main__":
    for a in alph:
        for b in alph:
            for c in alph:
                for d in alph:

                    s = socket()
                    s.connect(('172.16.97.130', 20020))
                    ch = a + b + c + d
                    s.send(ch+"\n")
                    r = s.recv(1024)
                    if hexlist.count(r) == 0:
                        hexlist.append(r)
                        hexpw.append(ch)
                        for cm in r:
                            print hex(ord(cm)),
                        print "   - passphrase " + ch
                    s.close()