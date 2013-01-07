#!/usr/bin/env python
"""
getcreationdate.py.

Accepts a filename as a command-line option. Prints the Unix creation date
and the OS X creation date of the file given.

Copyright (c) 2009 John Mark Schofield
root@sudosu.net
http://www.sudosu.net

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import os.path
import time
import commands
import sys
import os

def get_osx_creation_time(filename):
    """Accepts a filename as a string. Gets the OS X creation date/time by parsing "mdls" output.

    Returns file creation date as a float; float is creation date as seconds-since-epoch.
    """
    status, output = commands.getstatusoutput('/usr/bin/mdls -name kMDItemFSCreationDate "%s"' % (filename))
    if status != 0:
        print('Error getting OS X metadata for %s. Error was %d. Error text was: <%s>.' %
              (filename, status, output))
        sys.exit(3)
    datestring = output.split('=')[1].strip()
    datestring_split = datestring.split(' ')
    datestr = datestring_split[0]
    timestr = datestring_split[1]
    # At present, we're ignoring timezone.
    tzstr = datestring_split[2]

    date_split = datestr.split('-')
    year = int(date_split[0])
    month = int(date_split[1])
    day = int(date_split[2])

    time_split = timestr.split(':')
    hour = int(time_split[0])
    minute = int(time_split[1])
    second = int(time_split[2])

    # convert to "seconds since epoch" to be compatible with os.path.getctime and os.path.getmtime.
    return time.mktime([year, month, day, hour, minute, second, 0, 0, -1])
    
                                       

if __name__ == '__main__':
    testfile = sys.argv[1]
    if os.access(testfile, os.R_OK):
        print('Unix Creation Time for file %s: %s' % (testfile, time.ctime(os.path.getctime(testfile))))
        print('OS X Creation Time for file %s: %s' % (testfile, time.ctime(get_osx_creation_time(testfile))))
    else:
        print('Unable to access file: %s' % testfile)
        sys.exit(2)
