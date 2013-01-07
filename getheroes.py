#!/usr/bin/env python

#Description: Attempt to download all Heroes Graphic Novels
#Author: Tyler Reguly (ht@computerdefense.org)

import urllib

def pad(count) : 
	count = str(count)
	while ( len ( count ) < 3 ) :
		count = "0" + count
	return count

def get(issue) : 
	URL = "http://www.nbc.com/Heroes/novels/downloads/Heroes_novel_" + issue + ".pdf"
	contentType = urllib.urlopen(URL).info().getsubtype()
	if ( contentType == 'pdf' ) :
		print "Downloading Issue #" + issue + "."
		urllib.urlretrieve(URL, issue + '.pdf')
		print "Issue #" + issue + " download complete."
		return True
	else : return False  

counter = 1
try : 
	while ( get(pad(counter)) == True ) : 
		counter += 1
except KeyboardInterrupt :
	print "\nProgram Execution Terminated\n"




