#!/usr/bin/env python

import os
import pyid3lib

for root, dirs, files in os.walk('/home/jonojono/Desktop/Music'):
    for f in files:
        if f.endswith('.MP3') or f.endswith('.mp3'):
            song = os.path.join(root, f)
            dir = os.path.dirname(song)
            dirlist = dir.split('/')

            id3info = pyid3lib.tag(song)
            if dirlist[-2] == "Music":
                id3info.artist = dirlist[-2]
            else:
                id3info.album = dirlist[-1]
                id3info.artist = dirlist[-2]
            id3info.update()	
