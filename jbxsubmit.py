####
# 02/2006 Will Holcomb <wholcomb@gmail.com>
# 11/2010 Stefan Buehlmann <stefan.buehlmann@joebox.org>
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# JOEBOX SUBMIT SCRIPT
#
# GLOBAL SETTINGS
# ------------------------------
# Change to your requirements!!!

usexp = True
usevista = False
usew7 = False
getpcap = False
getshoots = False
email = "mdmonk@gmail.com"

# ------------------------------

import urllib
import urllib2
import mimetools, mimetypes
import os, stat, sys, time, platform

def main():

	print ""
	print "--- Joebox upload script ---"
	print ""
	
	if len(sys.argv) == 3 and sys.argv[1] == "sendtoinstall":
		if sys.platform[0:3] != "win":
			print "Sendto installation only available on windows"
		elif platform.version()[0:1] == "6":
			ct = open(sys.argv[0], "r").read()
			open("C:\\Users\\" + os.getenv("USERNAME") + "\\AppData\\Roaming\\Microsoft\\Windows\\SendTo\\jbxsubmit.py", "w").write(ct.replace("email = \"youremail", "email = \"" + sys.argv[2]))
			print "Successfully installed to jbxsubmit to sendto"
		elif platform.version()[0:1] == "5":
			ct = open(sys.argv[0], "r").read()
			open(os.getenv("USERPROFILE") + "\\SendTo\\jbxsubmit.py", "w").write(ct.replace("youremail", sys.argv[2]))
			print "Successfully installed to jbxsubmit to sendto"
	elif len(sys.argv) == 2 and email != "youremail":
		submit(sys.argv[1], email)
	elif len(sys.argv) == 3:
		submit(sys.argv[1], sys.argv[2])
	else:
		print "Usage: jbxsubmit <filetosend or directorywithfilestosend> <emailaddr>"
		print "Usage: jbxsubmit sendtoinstall <emailaddr> (will install jbxsubmit to the windows sendto menu)"
		
	print ""
	raw_input("Press ENTER to continue ...")
	
def submit(path, mail):

	if os.path.isdir(path):
		files = os.listdir(path)
		for file in files:
			file = path + "\\" + file
			if not os.path.isdir(file):
				post(file, mail)
	else:
		post(path, mail)
		

def post(file, mail):
    	
	submitUrl = "http://analysis.joebox.org/joeboxservlet/submit"
	opener = urllib2.build_opener(MultipartPostHandler)

	params = { "email" : mail,	 
			   "upfile" : open(file, "rb") }

	if(usexp):
		print "-> Using system: xp"
		params["xp"] = "1"
			
	if(usevista):
		print "-> Using system: vista"
		params["vista"] = "1"
			
	if(usew7):
		print "-> Using system: w7"
		params["w7"] = "1"
		
	if(getpcap):
		print "-> Adding PCAPs to results"
		params["pcap"] = "1"
			
	if(getshoots):
		print "-> Adding screenshots to results"
		params["shoots"] = "1"
			
	print ""
	
	ret = opener.open(submitUrl, params).read()
	pos = ret.find("Queue size:")
		
	if pos != -1:
		print "-> Successfully submited file: " + os.path.basename(file) + ", queue size: " + ret[pos + 12:ret.find("\n", pos)]
	else:
		print "-> Unable to upload file: " + ret[ret.find("error") + 9: ret.find("/div") - 2].strip()

class Callable:
	def __init__(self, anycallable):
		self.__call__ = anycallable

# Controls how sequences are uncoded. If true, elements may be given multiple values by
#  assigning a sequence.
doseq = 1

class MultipartPostHandler(urllib2.BaseHandler):
	handler_order = urllib2.HTTPHandler.handler_order - 10 # needs to run first

	def http_request(self, request):
		data = request.get_data()
		if data is not None and type(data) != str:
			v_files = []
			v_vars = []
			try:
				 for(key, value) in data.items():
					 if type(value) == file:
						 v_files.append((key, value))
					 else:
						 v_vars.append((key, value))
			except TypeError:
				systype, value, traceback = sys.exc_info()
				raise TypeError, "not a valid non-string sequence or mapping object", traceback

			if len(v_files) == 0:
				data = urllib.urlencode(v_vars, doseq)
			else:
				boundary, data = self.multipart_encode(v_vars, v_files)
				contenttype = 'multipart/form-data; boundary=%s' % boundary
				if(request.has_header('Content-Type')
				   and request.get_header('Content-Type').find('multipart/form-data') != 0):
					print "Replacing %s with %s" % (request.get_header('content-type'), 'multipart/form-data')
				request.add_unredirected_header('Content-Type', contenttype)

			request.add_data(data)
		return request

	def multipart_encode(vars, files, boundary = None, buffer = None):
		if boundary is None:
			boundary = mimetools.choose_boundary()
		if buffer is None:
			buffer = ''
		for(key, value) in vars:
			buffer += '--%s\r\n' % boundary
			buffer += 'Content-Disposition: form-data; name="%s"' % key
			buffer += '\r\n\r\n' + value + '\r\n'
		for(key, fd) in files:
			file_size = os.fstat(fd.fileno())[stat.ST_SIZE]
			filename = os.path.basename(fd.name)
			contenttype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
			buffer += '--%s\r\n' % boundary
			buffer += 'Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (key, filename)
			buffer += 'Content-Type: %s\r\n' % contenttype
			# buffer += 'Content-Length: %s\r\n' % file_size
			fd.seek(0)
			buffer += '\r\n' + fd.read() + '\r\n'
		buffer += '--%s--\r\n\r\n' % boundary
		return boundary, buffer
	multipart_encode = Callable(multipart_encode)

	https_request = http_request
		
if __name__=="__main__":
	main()
