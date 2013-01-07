# scancode.py - Web application source code scanning tool for .Net
# Author: Shreeraj shah

# Importing required libraries

import sys
import os
import re

# Function: scanfile
# purpose: Scan entire file for various important information

def scanfile(file):
   infile = open(file,"r")
   s = infile.readlines()
   linenum = 0
   for line in s:               
         # Look for entry point
         linenum += 1
         p = re.compile(".*.[Rr]equest.*[^\n]\n")
         m = p.match(line)
         if m:                          
            print 'Request Object Entry:'
            print linenum,":",m.group()
                
         # Look for sql injection points
         p = re.compile(".*.select .*?[^\n]\n|.*.SqlCommand.*?[^\n]\n")
         m = p.match(line)
         if m:
            print 'SQL Object Entry:'
            print linenum,":",m.group()
                
         # Look for file reader
         p = re.compile(".*.FileStream .*?[^\n]\n|.*.StreamReader.*?[^\n]\n")
         m = p.match(line)
         if m:
            print 'File System Entry:'
            print linenum,":",m.group()
                
         # Look for cookie and session management
         p = re.compile(".*.HttpCookie.*?[^\n]\n|.*.session.*?[^\n]\n")
         m = p.match(line)
         if m:
            print 'Session Object Entry:'
            print linenum,":",m.group()
                
         # Look for dependencies
         p = re.compile("<!--.*?#include.*?-->")
         m = p.match(line)
         if m:
            print 'Dependencies:'
            print linenum,":",m.group()
        
         # Look for response object
         p = re.compile(".*.[Rr]esponse.*[^\n]\n")
         m = p.match(line)
         if m:
            print 'Response Object Entry:'
            print linenum,":",m.group()
                
         # Look for XSS attack point
         p = re.compile(".*.write.*[^\n]\n")
         m = p.match(line)
         if m:                          
            print 'XSS Check:'
            print linenum,":",m.group()
                
         # Look for exception handling
         p = re.compile(".*catch.*[^\n]\n")
         m = p.match(line)
         if m:                          
            print 'Exception handling:'
            print linenum,":",m.group()
                
     return

# Function: scan4request
# Purpose: Look for entry points

def scan4request(file):
    infile = open(file,"r")
    s = infile.readlines()
    linenum = 0
    print 'Request Object Entry:'
    for line in s:                      
          linenum += 1
          p = re.compile(".*.[Rr]equest.*[^\n]\n")
          m = p.match(line)
          if m:                                 
             print linenum,":",m.group()
# Function: scan4trace
# Purpose: Help in tracing variable

def scan4trace(file,var):
    infile = open(file,"r")
    s = infile.readlines()
    print 'Tracing variable:'+var
    for line in s:                      
          p = re.compile(".*"+var+".*")
          m = p.match(line)
          if m:                                 
             print m.group()

# Main scripting portion

try:
        flag = sys.argv[1]
        file = sys.argv[2]
        if flag=="-sR":
           scan4request(file)
        
        if flag=="-t":
           var = sys.argv[3]
           scan4trace(file,var)
                
        if flag=="-sG":
           scanfile(file)

except (IndexError,ValueError):
       print "Cannot parse the option string correctly"
       print "Usage:\n"
       print "scancode -<flag> <file> <variable>"
       print "flag -sG : Global match"
       print "flag -sR : Entry points"
       print "flag -t  : Variable tracing"
       print "            Variable is only needed for -t option\n"
       print "Examples:\n"
       print "scancode.py -sG details.aspx"
       print "scancode.py -sR details.aspx"
       print "scancode.py -t details.aspx pro_id"
