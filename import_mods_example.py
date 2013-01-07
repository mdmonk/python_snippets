#!/usr/bin/python

# Demonstrates various methods of importing modules.

from socket import *
import string
import time

# create a socket of the basic type.
s = socket(AF_INET, SOCK_STREAM)
# define our banner.
senddata1 = "220 desktop Microsoft ESMTP MAIL Service, Version 6.0.2600.1106 ready at" + time.strftime("%a, %d %b %Y %H:%M:%S %Z")
# Query the user for their IP Address and set that and the port
HOST = raw_input("Enter IP Address to bind socket to: ")
PORT = 25 s.bind((HOST, PORT))
# Bind the socket to an IP Address and Port
s.listen(1)
# Have the socket listen for a connection
(incomingsocket, address) = s.accept()
# Accept an incoming connection
incomingsocket.send(senddata1)
# Send our banner
straddress = str(address)
# Convert incoming address to a string
testlist = string.split(straddress, ",")
# Split the tuple into lists
gethost = string.split(testlist[0], "'")
# Split the host portion of the list
getaddr = string.split(testlist[1], ")")
# Split the port portion of the list
host = gethost[1]
# Remove just the address from the list
incomingport = int(getaddr[0])
# Remove just the port from the list
# define our Warning
senddata2 = "Illegal Access of this server, your IP [" + host +"] has been logged."
# Print connection information to the stdout
print "Connection attempt on port", PORT, "from", host, ":", incomingport
# Listen for incoming data
data = incomingsocket.recv(1024)
# Send the Warning
incomingsocket.send(senddata2)
# Close the socket 
incomingsocket.close

