#!/usr/bin/env python
#####################
# skeleton.py - template for python src files.
# 7/29/2007 - CL
#####################

import SocketServer 

def main():
	class MyHandler(SocketServer.BaseRequestHandler): 
		def handle(self): 
			while 1: 
				dataReceived = self.request.recv(1024) 
				if not dataReceived: break 
				self.request.send(dataReceived) 
 
	myServer = SocketServer.TCPServer(('',8881), MyHandler) 
	myServer.serve_forever(  ) 

if __name__ == "__main__":
	main()

