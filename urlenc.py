#!/usr/bin/env python
# Evan 08/14/2007
# simple script to url encode/decode a passed string.
# 
import sys
import urllib
import optparse
import re

def usage():
	print "Usage: %s <url>" % sys.argv[0]
	sys.exit(1)

def encodeit(urlarg):
	print urllib.quote(urlarg)

def decodeit(urlarg):
	print urllib.unquote(urlarg)

if __name__ == "__main__":

	#if len(sys.argv) - 1 < 1:
	#	usage()
	
	parser = optparse.OptionParser()
	parser.set_usage("%s [options] <url>" % parser.get_prog_name())
	parser.add_option("-e", "--encode", dest="encode", help="Force URL encoding", metavar="URL")
	parser.add_option("-d", "--decode", dest="decode", help="Force URL decoding", metavar="URL")
	
	(options, args) = parser.parse_args()
	if options.encode:
		encodeit(options.encode)

	elif options.decode:
		decodeit(options.decode)
	else:
		if len(sys.argv) - 1 < 1:
			parser.print_help()
			parser.exit()
	
		r = re.compile('[%]')
		if r.search(sys.argv[1]):
			decodeit(sys.argv[1])
		else:
			encodeit(sys.argv[1])
