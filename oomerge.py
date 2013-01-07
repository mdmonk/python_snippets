import getopt, sys
import uno
import os 

from os.path import isfile, join
from os import getcwd
from unohelper import systemPathToFileUrl, absolutize
from com.sun.star.beans import PropertyValue
from com.sun.star.style.BreakType import PAGE_BEFORE, PAGE_AFTER
from com.sun.star.uno import Exception as UnoException, RuntimeException
from com.sun.star.connection import NoConnectException
from com.sun.star.lang import IllegalArgumentException
from com.sun.star.io import IOException

def usage():
    sys.stderr.write( "usage: oomerge.py --help |\n"+
                  "       [-c <connection-string> | --connection-string=<connection-string>]\n"+
		  "       [-o <outputfile> | --outfile=<outputfile>] \n"+
                  "       file1 file2 ...\n"+
                  "\n" +
                  "Merges two or more documents into a single file, called 'output.swx' unless\n" +
                  "otherwise specified. It requires an OpenOffice.org instance to be running.\n" +
		  "The script and the running OpenOffice.org instance must be able to access the file with\n"+
                  "by the same system path.\n"
		  "[ To have a listening OpenOffice.org instance, just run:\n"+
		  "openoffice \"-accept=socket,host=localhost,port=2002;urp;\" ] \n"
		  "\n"+
                  "\n"+
                  "-c <connection-string> | --connection-string=<connection-string>\n" +
                  "        The connection-string part of a uno url to where the\n" +
                  "        the script should connect to in order to do the conversion.\n" +
                  "        The strings defaults to socket,host=localhost,port=2002\n"
                  "-o <outputfile> | --outfile=<outputfile>\n" +
                  "        The name of the output filename. \"output.swx\" if not specified\n"
                  )

def main():
    retVal = 0
    outputfile = "output.swx"

    opts, args = getopt.getopt(sys.argv[1:], "hco:", ["help", "connection-string=", "outfile" ])
    url = "uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext"

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-c", "--connection-string" ):
            url = "uno:" + a + ";urp;StarOffice.ComponentContext"
        if o in ("-o", "--outfile"):
            outputfile = a
        
    if not len( args ):
        usage()
        sys.exit()
    
    try:
        ctxLocal = uno.getComponentContext()
        smgrLocal = ctxLocal.ServiceManager

        resolver = smgrLocal.createInstanceWithContext(
                   "com.sun.star.bridge.UnoUrlResolver", ctxLocal )
        ctx = resolver.resolve( url )
        smgr = ctx.ServiceManager
        desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx )
    except NoConnectException, e:
        sys.stderr.write("OpenOffice process not found or not listening (" + e.Message + ")\n")
        sys.exit(1)
    except IllegalArgumentException, e:
        sys.stderr.write("The url is invalid ( " + e.Message + ")\n")
        sys.exit(1)
    except RuntimeException, e:
        sys.stderr.write("An unknown error occured: " + e.Message + "\n")

    cwd = systemPathToFileUrl( getcwd() )
    destFile = absolutize( cwd, systemPathToFileUrl(outputfile) )
    inProps = PropertyValue( "Hidden" , 0 , True, 0 ),

    newdoc = desktop.loadComponentFromURL( "private:factory/swriter", "_blank", 0, inProps )
    text   = newdoc.Text
    cursor = text.createTextCursor()

    for i in args:
        if isfile(os.path.join(getcwd(), i)):
            try:
                fileUrl = absolutize( cwd, systemPathToFileUrl(i) )

                print "Appending %s" % fileUrl
                try:
                    cursor.gotoEnd(False)
                    cursor.BreakType = PAGE_BEFORE
                    cursor.insertDocumentFromURL(fileUrl, ())
                except IOException, e:
                    sys.stderr.write("Error during opening ( " + e.Message + ")\n")
                except IllegalArgumentException, e:
                    sys.stderr.write("The url is invalid ( " + e.Message + ")\n")

            except IOException, e:
                sys.stderr.write( "Error during opening: " + e.Message + "\n" )
            except UnoException, e:
                sys.stderr.write( "Error ("+repr(e.__class__)+") during conversion:" + 
                    e.Message + "\n" )
        else:
            raise IOException

    print "%s merged into %s" % (args, destFile)
    newdoc.storeAsURL(destFile, ())
    newdoc.dispose()
	
main()
