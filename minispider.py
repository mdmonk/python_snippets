#!/usr/bin/python

import httplib
import sys
import re
from HTMLParser import HTMLParser


class miniHTMLParser( HTMLParser ):

  viewedQueue = []
  instQueue = []

  def get_next_link( self ):
    if self.instQueue == []:
      return ''
    else:
      return self.instQueue.pop(0)


  def gethtmlfile( self, site, page ):
    try:
      httpconn = httplib.HTTPConnection(site)
      httpconn.request("GET", page)
      resp = httpconn.getresponse()
      resppage = resp.read()
    except:
      resppage = ""

    return resppage


  def handle_starttag( self, tag, attrs ):
    if tag == 'a':
      newstr = str(attrs[0][1])
      if re.search('http', newstr) == None:
        if re.search('mailto', newstr) == None:
          if re.search('htm', newstr) != None:
            if (newstr in self.viewedQueue) == False:
              print "  adding", newstr
              self.instQueue.append( newstr )
              self.viewedQueue.append( newstr )
          else:
            print "  ignoring", newstr
        else:
          print "  ignoring", newstr
      else:
        print "  ignoring", newstr


def main():

  if sys.argv[1] == '':
    print "usage is ./minispider.py site link"
    sys.exit(2)

  mySpider = miniHTMLParser()

  link = sys.argv[2]

  while link != '':

    print "\nChecking link ", link

    # Get the file from the site and link
    retfile = mySpider.gethtmlfile( sys.argv[1], link )

    # Feed the file into the HTML parser
    mySpider.feed(retfile)

    # Search the retfile here

    # Get the next link in level traversal order
    link = mySpider.get_next_link()

  mySpider.close()

  print "\ndone\n"

if __name__ == "__main__":
  main()
