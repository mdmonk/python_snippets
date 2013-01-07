#!/usr/bin/python
import sys
import MySQLdb
try:
	conn = MySQLdb.connect (host = "localhost",
						    user = "testuser",
                            passwd = "r34d0nly",
                            db = "test")
except MySQLdb.Error, e:
  print "Error %d: %s" % (e.args[0], e.args[1])
  sys.exit (1)

cursor = conn.cursor ()
cursor.execute ("SELECT VERSION()")
row = cursor.fetchone ()
print "MySQL server version:", row[0]
cursor.close ()
conn.close ()

