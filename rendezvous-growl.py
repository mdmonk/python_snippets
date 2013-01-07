#!/usr/bin/env python
#####################
# rendezvous-growl.py
#####################

from Rendezvous import *
import socket, time, sys, os

PIPE="/tmp/alert"

def loop():
	r = Rendezvous()
	while 1:
		f = open(PIPE, 'r')
		line = f.readline()
		f.close() # we only want the one line - avoid buffering issues
		# pack line into mDNS record
		desc = { 'source':'pipe', 'text':line }
		# use MDNS as notifier with short TTL. Note that the socket calls
		# might send the wrong IP address on a multihomed machine
		info = ServiceInfo( "_alerter._udp.local.", "Alert" +
			str(int(time.time())) + "._alerter._udp.local.",
			socket.inet_aton(socket.gethostbyname(socket.gethostname())),
			0, 0, 0, desc )
		# we'll need to unregister this later
		r.registerService(info, 15)

if __name__ == '__main__':
	if not os.access(PIPE, os.F_OK):
		os.mkfifo(PIPE)
	loop()
