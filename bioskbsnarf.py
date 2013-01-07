#!/usr/bin/python
# Parses the realmode keyboard buffer out of the bios data area
# Metlstorm 2k6 <metlstorm@storm.net.nz>
#

import struct
import binascii
import sys
import string

BASE = 0x400
OFFSET= 0x17
BUFOFFSET = 0x1e
LEN = 39

fp=open(sys.argv[1], "r")
fp.seek(BASE + OFFSET)
data = fp.read(LEN)
fp.close()

def decodeRealModeKbdBiosDataArea(bda):
	fmt = "<BBBHH32s"
	shifta, shiftb, alt, readp, writep, buf = struct.unpack(fmt, bda)
	unringed = buf[readp - BUFOFFSET:]
	unringed += buf[:readp - BUFOFFSET]
	pressed = []
	for i in range(0,len(unringed)-2,2):
		if ord(unringed[i]) != 0:
			pressed.append((unringed[i], ord(unringed[i+1])))
	
	return pressed


def formatC(c):
	if c in string.printable and c not in string.whitespace:
		return c
	else:
		return "."

def displayKeyPresses(presses):
	for c,s in presses:
		print "Ascii: %c (0x%02x)\tScancode: 0x%02x" % (formatC(c),ord(c),s)

displayKeyPresses(decodeRealModeKbdBiosDataArea(data))
