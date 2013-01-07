#!/usr/bin/python
import os,sys,pickle,re,stat

MAP_DIR = "C:\\ADS\\"
FRAG_DIR = "C:\\ADS\\testdir\\"

frag_map = []

def usage():
	print "ads.py <-e|-f> <file>"
	
def welcome():
	print "*" * 35
	print "\tADS Fragment Program"
	print "*" * 35		

def fragment(file):
	fName = file
	name = fName.split('\\')[-1]
	if os.path.exists("%s%s.map" % (MAP_DIR, name)):
		print "[*] Map File already exists"
		sys.exit(1)
	if not os.path.exists(file):
		print "[*] Input file does not exist"
		sys.exit(1)
	
	inFile = open(file, 'rb')
	data = inFile.read()
	inFile.close()
	data_size = len(data)
	
	frag_files = []
	
	for file in os.listdir(FRAG_DIR):
		frag = os.path.join(FRAG_DIR, file)
		attrib = os.stat(frag)[0]
		if attrib & stat.S_IWRITE:
			frag_files.append(frag)
			#print frag
		
	user_frags = -1
	min = 1
	max = ""
	if len(frag_files) > data_size:
		print "[*] Length of frag_files is greater than size of file"
		max = data_size
	else:
		max = len(frag_files)
		
	#max = len(frag_files)
		
	while user_frags < min or user_frags > max:
		user_frags = raw_input("Number of Fragments min[1] max[%d]: " % max)
		if re.search('^[0-9].*',user_frags) == None:
			print "[*] Not a valid number"
			continue
		user_frags = int(user_frags)
		if user_frags < 1 or user_frags > len(frag_files):
			print "[*] Invalid choice"
			continue
		
	block_size = data_size / user_frags
	data_splits = []
	
	print "Data Size: %d" % data_size
	
	count = 0
	for i in range(0,data_size,block_size):
		current = data[i:i+block_size]
		if len(data_splits) == len(frag_files):
			data_splits[count-1] += data[i:]
			break
		current = data[i:i+block_size]
		data_splits.append(current)
		count += 1
	
	count = 0
	
	#Alright so we need to make a defined structure for the end of the new file
	#We should create a general padded footer for the file that contains
	#the location of the next file, and 0s padding the remainder
	#That way we can extact the set amount of data, find where the next file is
	#and disregard the remaining 0s
	
	#Lets get the first file and write it out to the map
	first_file = frag_files[0]
	map_file = "%s%s.map" % (MAP_DIR, name)
	map_out = open(map_file, 'w')
	map_out.write(first_file)
	map_out.close()
	
	for frag in data_splits:
		#We need to make sure data size is 250
		#Starting with the next file location and padded with 0s to 250
		outfile = frag_files[count]
		
		print count
		
		data = ""
		
		if count == (len(data_splits) -1):
			#print "Last fragment"
			#This is the last fragment, there will be no linked list
			#We do want to pad it with 250 0's though
			pad = "0" * 250
			data += pad
		else:
			nextfile = frag_files[count+1]
		
			data = nextfile
			frag_length = len(data)
			pad = 250 - len(data)
			for i in range(pad):
				data += "0"
				
			
		#Append the pointer to the next file to the end of the fragment
		frag += data

		#print "Inserting Fragment %d in file %s" % (count, outfile)
		file_name = ""
		if name.find("\\") != -1:
			file_name = name.split("\\")[-1]
		else:
			file_name = name
		
		ads_file = open("%s:%s" % (outfile, name), 'wb')
		ads_file.write(frag)
		ads_file.close()

		count += 1
		
	
	os.remove(fName)
	
def extract():
	map_files = []
	for file in os.listdir(MAP_DIR):
		if file.endswith(".map"):
			map_files.append(file)
			
	if len(map_files) == 0:
		print "[*] No Map files found"
		sys.exit(1)
			
	for file in map_files:
		print file[:-4]
		
	user = raw_input("Extract what stream: ")
	user_file = "%s%s.map" % (MAP_DIR, user)
	inFile = ""
	data = ""
	if os.path.exists(user_file):
		inFile = open(user_file, 'r')
		data = inFile.read().strip()
		inFile.close()
	else:
		print "Not a valid choice"
		sys.exit(1)
		
	#Lets extract data from the fragments
	#Start with the first file
	print "Reading: %s:%s" % (data,user)
	frag_file = open("%s:%s" % (data, user), 'rb')
	frag_data = frag_file.read()
	frag_file.close()
	
	current_data = ""
	#Pull off the first next file
	next_file = frag_data[-250:]
	#print frag_data
	#sys.exit(0)
	next_file = next_file[:next_file.find("0000")]
	#Get rid of 250 pad
	frag_data = frag_data[:-250]
	#Apped first data to current data
	current_data += frag_data
	
	#Lets go through a loop!
	count = 0
	while next_file != "":
		print "Reading: %s:%s" % (next_file,user)
		frag_file = open("%s:%s" % (next_file,user), 'rb')
		frag_data = frag_file.read()
		frag_file.close()
		
		next_file = frag_data[-250:]
		next_file = next_file[0:next_file.find("0000")]
		
		frag_data = frag_data[:-250]
		current_data += frag_data
		frag_file.close()
		count += 1
		

	os.remove(user_file)
	print "Done"
	print "*" * 30
	
	extracted_size = len(current_data)
	print "Extracted Size: %d" % extracted_size
	
	extracted_file = open(user, 'wb')
	extracted_file.write(current_data)
	extracted_file.close()
	
	
def main():
	welcome()
	args = sys.argv[1:]
	if len(args) > 2 or len(args) < 1:
		usage()
		sys.exit(1)
	if args[0] == "-f":
		fragment(args[1])
	elif args[0] == "-e":
		extract()
	else:
		usage()
		sys.exit(1)
	
if __name__ == "__main__":
	main()