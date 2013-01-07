#!/usr/bin/env python

import unittest
import socket
import time

class EchoTest(unittest.TestCase):
    def setUp(self):
        self.s = socket.socket()
        self.s.settimeout(1)
        self.bufsize = 4096 # match Connection.hh value
        #self.rcvbuf = 810
        self.s.connect(('127.0.0.1', 50007))
        self.rcvbuf = self.s.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        self.sndbuf = self.s.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
        #self.rcvbuf = 81660
        #self.sndbuf = 81660
        self.sent = 0
        print self.sndbuf

    def _sendJunk(self, n):
        """Send n bytes of junk"""
        junk = ''.join(['x' for i in range(n)])
        written = 0
        while written < n:
            retval = self.s.send(junk[written:])
            self.sent += retval
            written += retval
        self.assertEquals(n, written)

    def _testWriteRead(self):
        expected = '12345'
        sentlen = self.s.send(expected)
        self.assertEquals(len(expected), sentlen)
        actual = self.s.recv(len(expected) + 1)
        self.assertEquals(expected, actual)

    def _testClose(self):
        self._sendJunk(self.sndbuf + self.rcvbuf + self.bufsize//2)
        self.s.shutdown(socket.SHUT_WR)
        time.sleep(5)
        received = 0
        while received < self.sent:
            received += len(self.s.recv(self.sent - received))
        self.assertEquals('', self.s.recv(1))

    def testFull(self):
        # Fill the buffers.
        #self._sendJunk(2*self.sndbuf + 2*self.rcvbuf + self.bufsize)
        self._sendJunk(2*self.sndbuf + self.rcvbuf + self.bufsize)

        # Try a write that blocks because the buffers are full.
        self.assertRaises(socket.timeout, self._sendJunk, self.sndbuf)
        #self.assertRaises(socket.timeout, self._sendJunk, 1)

        # Give it a chance to empty them.
        received = 0
        while received < self.sent:
            received += len(self.s.recv(self.sent - received))

        # It shouldn't have sent anything more.
        self.assertRaises(socket.timeout, self.s.recv, 1)

        # Now the write should go through.
        self._sendJunk(self.sndbuf)

        # And we should get the right amount of data back.
        received = 0
        while received < self.sndbuf:
            received += len(self.s.recv(self.sent - received))
        self.assertRaises(socket.timeout, self.s.recv, 1)

if __name__ == '__main__':
    unittest.main()
