

#!/usr/bin/python

import os
import sys
import re
from subprocess import Popen
import time

HANDBRAKE = '/usr/local/bin/HandBrakeCLI'

def usage():
    print 'rip.py [dvd_name output_dir]'

def get_dvd_file():
    vols = os.listdir('/Volumes')
    candidates = list()
    for vol in vols:
        if vol.startswith('.'):
            continue
        candidates.append(vol)
    if len(candidates) > 0:
        for vol in candidates:
            dirs = os.listdir('/Volumes/' + vol)
            if 'VIDEO_TS' in dirs:
                return vol
    else:
        sys.exit()

def prettify_filename(filename):
    """
    LITTLE_MISS_SUNSHINE => Little Miss Sunshine
    """
    pretty = ''
    l = None
    for i in xrange(len(filename)):
        c = filename[i]
        if not l or l == '_':
            pretty += c.upper()
        else:
            pretty += c.lower()
        l = c
    return pretty

start = time.time()
dvd_file = None
out_dir = None

#really ugly comand line parsing, should you opt
if len(sys.argv) > 3:
    print sys.argv
    usage()
    sys.exit()
if len(sys.argv) == 3:
    dvd_file, out_dir = sys.argv[1:]
elif len(sys.argv) == 2:
    dvd_file = get_dvd_file()
    out_dir = sys.argv[1]
else:
    dvd_file = get_dvd_file()
    out_dir = '.'
if out_dir.endswith('/'):
    out_dir = out_dir[:-1]

#input and output options for handbrake
infile = '/Volumes/%s' % (dvd_file)
dvd_file = prettify_filename(dvd_file)
outfile = '%s/%s.m4v' % (out_dir, dvd_file)

#lets verify the paths
if not os.path.exists(infile) or not os.path.exists(out_dir):
    print 'bad paths: input file (%s) output directory (%s)' % (infile, out_dir)
    sys.exit()

#scan the dvd for the titles
tmp = os.tmpfile()
po = Popen((HANDBRAKE, '-i%s' % (infile), '-t0'), stderr=tmp) 
while po.poll() == None:
    time.sleep(1)
    sys.stdout.write('.')
    sys.stdout.flush()
tmp.seek(0)
sys.stdout.write('n')

#read the output from the scan to get all the titles and their length
title = re.compile('title (d+):')
duration = re.compile('duration: (d+):(d+):(d+)')
chapters = list()
t = d = None
for line in tmp.readlines():
    tm = title.search(line)
    dm = duration.search(line)
    if tm != None:
        t = tm.groups()[0]
    elif dm != None:
        d = dm.groups()
        d = [ int(x) for x in d ]
        h, m, s = d
        secs = h * 3600 + m * 60 + s
        chapters.append((t, secs))
        t = d = None

#determine the longest title
max_secs = title = 0
for chapter in chapters:
    if chapter[1] > max_secs:
        title = chapter[0]
        max_secs = chapter[1]

print 'ripping: chapter %s (%ds)' % (title, max_secs)

#start the ripping process, redirect stderr to tmp
tmp = os.tmpfile()
po = Popen((HANDBRAKE, '-i%s' % (infile), '-t%s' % (title), '-o%s' % (outfile), 
            '-effmpeg', '-m', '-b2048', '-p',         #video options
            '-B256', '-R48', '-66ch') , stderr=tmp)   #audio options
while po.poll() == None:
    time.sleep(60)
    sys.stdout.write('.')
    sys.stdout.flush()
sys.stdout.write('n')

#get total time
secs = time.time() - start
hrs = int(secs) / 3600
min = int(secs) % 3600 / 60
sec = int(secs) % 60

print 'you totally ripped! (%d:%d:%d total time)' % (hrs, min, sec)

# notify via growl
os.popen('growlnotify -m "Completed encoding %s" -p 2' % (dvd_file))

