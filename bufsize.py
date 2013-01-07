#!/usr/bin/env python

import socket
import errno
import time

# Create an AF_INET socket pair.
ss = socket.socket()
ss.listen(1)
s1 = socket.socket()
s1.connect(ss.getsockname())
s2 = ss.accept()[0]
ss = None

# Examine the buffers.
s1.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 32)
sndbuf = s1.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
print 'send buffer: %d' % sndbuf
s2.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF,  8)
rcvbuf = s2.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
print 'receive buffer: %d' % rcvbuf

# See how much we can send without blocking.
s1.setblocking(0)
bigdata = ''.join(['x' for i in range(16 * (sndbuf + rcvbuf))])
sent = 0
try:
    while True:
        sent += s1.send(bigdata)
        print 'sent %d bytes now' % sent
        time.sleep(.1)
except socket.error, (err, errstr):
    assert err == errno.EWOULDBLOCK
print 'Sent %d bytes' % sent

# Read a byte, then try again.
print 'Read %d bytes' % len(s2.recv(128))
sent = 0
try:
    while True:
        sent += s1.send(bigdata)
except socket.error, (err, errstr):
    assert err == errno.EWOULDBLOCK
print 'Sent %d bytes' % sent
