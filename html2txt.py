#!/usr/bin/env python
#####################
import re
import sys

def main():
    if len(sys.argv) - 1 < 1:
        print "Usage: %s <html file> <text file>" % sys.argv[0]
        sys.exit(1)

    print "Reading: %s" % sys.argv[1]
    print "Writing: %s" % sys.argv[2]

    p = re.compile('(<p.*?>)|(<tr.*?>)', re.I)
    t = re.compile('<td.*?>', re.I)
    comm = re.compile('<!--.*?-->', re.M)
    tags = re.compile('<.*?>', re.M)
    result = html2txt(sys.argv[1])
    f = open(sys.argv[2], mode='w')
    if (f):
        f.write(result)
        f.close()
    else:
        print "Unable to open file for writing! file name: %s" % sys.argv[2]
        sys.exit(1)

def html2txt(s, hint = 'entity', code = 'ISO-8859-1'):
    """Convert the html to raw txt
    - suppress all return
    - <p>, <tr> to return
    - <td> to tab
    Need the foolwing regex:
    p = re.compile('(<p.*?>)|(<tr.*?>)', re.I)
    t = re.compile('<td.*?>', re.I)
    comm = re.compile('<!--.*?-->', re.M)
    tags = re.compile('<.*?>', re.M)
    version 0.0.1 20020930
    """
    s = s.replace('\n', '') # remove returns time this compare to split filter join
    s = p.sub('\n', s) # replace p and tr by \n
    s = t.sub('\t', s) # replace td by \t
    s = comm.sub('', s) # remove comments
    s = tags.sub('', s) # remove all remaining tags
    s = re.sub(' +', ' ', s) # remove running spaces this remove the \n and \t
    # handling of entities
    """ result = s 
    pass
    return result """
    return s

if __name__ == "__main__":
	main()
