#!/usr/bin/env python
#####################
# skeleton.py - template for python src files.
# 7/29/2007 - CL
#####################
"""A script to fetch and store XKCD comics
by Simon Rivada. You can reach me at
simon@brutalpenetration.org. Have fun!"""

import urllib, re

def main():
    xkcd         = urllib.urlopen("http://www.xckd.com")
    xkcd_content = xkcd.read()

    xkcd_pattern = re.compile("http://imgs.xkcd.com/comics/(.*?)\.png")

    xkcd_name  = xkcd_pattern.search(xkcd_content).group().replace("http://imgs.xkcd.com/comics/", "")
    xkcd_image = urllib.urlopen(xkcd_pattern.search(xkcd_content).group()).read()

    file = open("store/%s" % xkcd_name, "w")
    file.write(xkcd_image)
    file.close()

    print "Fetched %s" % xkcd_name


if __name__ == "__main__":
	main()

