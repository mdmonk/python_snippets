#!/usr/bin/env python
import sys
import os
import re
from optparse import OptionParser




#debug output.
global debug
debug = None

#Some silly constants for further optimization
PIPE = 1
FILE = 0

#this sets up file associations for extracting text
#from a variety of file types.  Each entry should be 
#a tuple with everything before the filepath 
#in cell 0, and everything after the filepath in cell 1.

fileAssoc = {
       
    #yes, this is probably an unnecessary use of cat,
    #but you might want to use fmt for text or tidy for 
    #html.
    
    #On second thought, throw in a switch to read from a file.
    #the third argument here can be either FILE or PIPE.  So if you 
    #want to use tidy:
    #"html" : ("tidy -iw, "",PIPE),
    "txt" : ("cat", "",FILE),
    "html" : ("cat", "",FILE),
    "htm" : ("cat", "",FILE)
    }
    
#the default file action. use mdiport and pull 
#information from stderr. This takes advantage of 
#file indexing plugins.
defaultFileAction=("mdimport -nfd2", "2>&1",PIPE)


#parse options
parser = OptionParser()
parser.add_option("-i", "--ignore-case", dest="ignoreCase", action="store_true",
    help="""Use case-insensitive searches.  ('Foo' matches 'foo')""")
parser.add_option("-r", "--regex", dest="regex", action="store",
    help="""Use regular expression instead of phrase.""")
parser.add_option("-s", "--spotlight-expression", dest="spotlightExpression",
    action="store", help="""An extra expression used to seach the spotlight index
    for example mdgrep "Frank Zappa" -s "utopia" finds all items in the spotlight
    index matching "utopia" with the phrase "Frank Zappa".""")
parser.add_option("-o", "--only-in", dest="directory",
    action="store", help="""Search only in this directory.""")
parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
    help="Print out some debug messages.")


parser.set_usage("%prog seachPhrase [options]")

(options, args) = parser.parse_args()

if debug:
    print "Options:" + options
    print "Args" + args



class textExtractor:
    """Extracts the text contents of file at filepath and then
    performs a case-insensive seach on searchPhrase"""
    def __init__(self,filepath):
        self.filepath = filepath
        self.status = None
        #self.text = None
        #self.searchPhrase=searchPhrase.lower()
    def searchString(self,searchPhrase,ignoreCase=True):
        """Convert a file to text and search for a match,
        if a match is found, set status to true."""
        #threadPool.acquire()
        
        #this is just used for debugging
        command = buildCommand(self.filepath)
        
        #get a reader from the 
        reader = buildReader(self.filepath)
        
        #provide some helpful information 
        #about what process is running.
        global debug
        if debug:
            print "Running: " + command
        #reader = os.popen(command, "r")
        while 1:
            text = reader.readline()
            #print text
            if not text: break
            if ignoreCase:
                text = text.lower()
            if text.find(searchPhrase) > -1:
                self.status = True
                break
        #close our resources.
        reader.close()
        #threadPool.release()

    def searchRegex(self,expression):
        """Search a parsed file using a regular expression 
        object. expression must be an re object."""
        #threadPool.acquire()
        
        #this is just used for debugging
        command = buildCommand(self.filepath)
        
        #get a reader from the 
        reader = buildReader(self.filepath)
        
        #provide some helpful information 
        #about what process is running.
        if debug:
            print "Running: " + command
        #reader = os.popen(command, "r")
        while 1:
            text = reader.readline()
            #print text
            if not text: break
            if expression.search(text):
                self.status = True
                break
        #close our resources.
        reader.close()
        #threadPool.release()

        
def spacesToAnd(text):
    """This function converts a phrase query to an and query"""
    return(text.replace(r" ",r"&"))
    
def buildCommand(filepath):
    """Build a command for parsing filepath."""
    extension = filepath.split('.')[-1]
    action = fileAssoc.get(extension,defaultFileAction)
    return "".join([action[0], ' "' , filepath, '" ', action[1]]) 
    
def buildReader(filepath):
    """Return the proper reader for filepath, this will be a 
    basic file handle for text-based objects, and a popen 
    handle for other objects."""
    extension = filepath.split('.')[-1]
    action = fileAssoc.get(extension,defaultFileAction)
    if action[2] == FILE:
        return open(filepath,"r")
    else:
        return os.popen("".join([action[0], ' "' , filepath, '" ', action[1]]),"r")
        

    
    


def searchSpotlight(searchPhrase,spotlightQuery=None,onlyin=None,regexObject=None,
                    case=False):
    """Run a spotlightQuery with our parameters and then pass the results to 
    our file reader function"""
    if not spotlightQuery:
        spotlightQuery = spacesToAnd(searchPhrase)
    if onlyin:
        onlyinText = ' -onlyin "' + onlyin + '" '
    else:
        onlyinText = ""
        
    #extractorList = []
    queryCommand = 'mdfind ' + onlyinText + '"' + spotlightQuery + '"'
    if debug:
        print queryCommand
        
    #open mdfind as a pipe.    
    mdQueryObj = os.popen(queryCommand)
    
    #iterate over the results of mdfind.
    #mdfind can be a bit slow, so parse the results
    #as soon as we get it, rather than wait for readlines()
    #to exit.
    while 1:
        text = mdQueryObj.readline()
        if not text: break
        current = textExtractor(text.strip())
        #extractorList.append(current)
        if regexObject:
            current.searchRegex(regexObject)
        else:    
            current.searchString(searchPhrase,ignoreCase=case)
        if current.status:
            print current.filepath

def main():
    """process args and pass on control to the searchSpotlight function"""

    #parse options
    parser = OptionParser()
    parser.add_option("-i", "--ignore-case", dest="ignoreCase", action="store_true",
        help="""Use case-insensitive searches.  ('Foo' matches 'foo')""")
    parser.add_option("-r", "--regex", dest="regex", action="store",
        help="""Use regular expression instead of phrase.""")
    parser.add_option("-s", "--spotlight-expression", dest="spotlightExpression",
        action="store", help="""An extra expression used to seach the spotlight index
        for example mdgrep "Frank Zappa" -s "utopia" finds all items in the spotlight
        index matching "utopia" with the phrase "Frank Zappa".""")
    parser.add_option("-o", "--only-in", dest="directory",
        action="store", help="""Search only in this directory.""")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
        help="Print out some debug messages.")
    
    
    parser.set_usage("%prog seachPhrase [options]")
    
    (options, args) = parser.parse_args()
    
  
    

    #set our debug level
    global debug
    debug = options.verbose

    if debug:
        print "Options:" 
        print options
        print "Args:"
        print args
  

    #get the search phrase from the args
    searchPhrase = None
    if len(args):
        searchPhrase = args[0]
        
        
        
    #error checking. We need either a search phrase or a spotLight expression.
    #for any query.
    if  not (searchPhrase or options.spotlightExpression):
        print """You must supply either a search phrase, or a spotlight expression."""
        parser.print_help()
        sys.exit()
    
    #set options for ignoreCase
    if options.ignoreCase:
        ignoreCase = True
        regexFlags = re.I
    else:
        ignoreCase = None
        regexFlags = 0
        
    #if there is a regular expression specified, do the "phrase" search using that.    
    if options.regex:
        reObject = re.compile(options.regex,regexFlags)
        searchSpotlight(searchPhrase,
            spotlightQuery=options.spotlightExpression,
            onlyin=options.directory,
            regexObject=reObject)
            
    #run a normal text search.        
    else:
        searchSpotlight(searchPhrase,
            spotlightQuery = options.spotlightExpression,
            onlyin=options.directory,
            case=ignoreCase)
        
        
        
        
    
            

if __name__ == "__main__":   
    main()