#! /usr/bin/env python
# Script written to launch proper daemon, and gui nessus v2.2.8 or v3.0.3
# The script expects the default install directories to have been used.
# v2.2.8 is /usr/local
# v3.0.3 is /opt/nessus
# 6/19/2006

import sys, os

def usage():
	print """Usage: launch_nessus.py [OPTIONS]
  With no options version 2 is default.
  2	Use version 2 (/usr/local/sbin/nessusd)
  3	Use version 3 (/opt/nessus/sbin/nessusd)
	"""

nargs=len(sys.argv)
if nargs <= 1:
	print "Using Nessus version 2."
	ver='2'
else:
	ver=sys.argv[1]

if ver == '2':
		daemon='sudo /usr/local/sbin/nessusd -D'
		gui='/usr/local/bin/nessus&'
		#print "-- daemon: ", daemon
		#print "-- gui: ", gui
elif ver == '3':
		daemon='sudo /opt/nessus/sbin/nessusd -D'
		gui='/usr/X11R6/bin/NessusClient&'
		#print "-- daemon: ", daemon
		#print "-- gui: ", gui
else: 
		#print 'That version is unsupported'
		usage()
		sys.exit(2)

print "Stopping currently running nessusd."
os.popen("sudo pkill nessusd")
print "Starting ", daemon
os.popen(daemon)
print "Starting ", gui
os.popen(gui)
