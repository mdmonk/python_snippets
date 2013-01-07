#!/usr/bin/env python

import MySQLdb
import time

eTime = time.time()
print "Current seconds since the epoch is:"
print "Floating point: ", eTime
print "as an Integer: ", int(eTime)

#mycon = MySQLdb.connect(host="140.215.9.7", port=3306, user="readonly", passwd="re@d0nly", db="vainternal")
#cursor = mycon.cursor()
#basicStuff()
#cursor.close()
#mycon.close()

def basicStuff():
	# Execute SQL query
	sqlqry = "SELECT * FROM DEVICES"
	cursor.execute(sqlqry)

	numrows = int(cursor.rowcount)
	print "Number of rows: ", numrows

	for x in range(0,numrows):
		row = cursor.fetchone()
		print row[0] , "-->", row[1] , "-->", row[2] , "-->", row[3] , "-->", row[4] , "-->", row[5]

# end def basicStuff

def getThoseStats():
	return
# end def getThoseStats

def calcDevs():
	return
# end def calcDevs

def printStats():
	return
# end def printStats

def printDevs():
	return
# end def printDevs

