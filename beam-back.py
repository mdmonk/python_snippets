#!/usr/bin/python
import urllib, string, getopt, os, time, sys, tempfile, re, mimetools, socket

Version = "1.45"

#
# beam-back.py  
#
# Copyright GNU GENERAL PUBLIC LICENSE Version 2
# http://www.gnu.org/copyleft/gpl.html
#
# Homepage: http://beam-back.sourceforge.net
# Author  : Kal <kal@users.sourceforge.net>
#
# Acknowledgements
# ================
# 
# SourceForge crew -hosting this project
# my.mp3.com       -providing such a great service
# Robert A. Seace  -m3u playlist idea and code
# Tim Carroll      -infinite streaming suggestions
# Jake Kauth       -filename cleaning, logging class and rename code
# Jiva Devoe       -pls patch for direct http server handling
# Nathan Shafer    -mp3 filename fix and logging tweak patch
#
#

def Usage():
  print
  print "Usage: beam-back.py [options] m3u_file"
  print
  print "       -c       clobber files instead of appending -# "
  print "       -d dir   top directory to create files/subdirs in "
  print "       -f       enable framing and discard non-mp3 data "
  print "       -i       use ICY title data from a shoutcast stream "
  print "                (this option is much improved) "
  print "       -l       log output to beam-back.log file "
  print "       -m       create a local .m3u playlist (in top dir) "
  print "       -n 1     name as \"artist - title.mp3\" (default) "
  print "       -n 2     name as \"title.mp3\" "
  print "       -n 3     name as \"title.mp3\" in subdir \"artist\" "
  print "       -n 4     name as \"artist - title.mp3\" in subdir \"artist\" "
  print "       -n #u    same as -n 1 to 4 except sub underscores for spaces "
  print "       -p       persistent re-open pls until keyboard interrupt"
  print "       -t msec  trim msec milliseconds off the end of ICY files "
  print "       -u file  name for unfinished streams (unfinished-stream.mp3)"
  print "       -v       verbose mode "
  print "       -z size  download size limit in megabytes"
  print
  print "Set your netscape application for m3u suffixes to something like:"
  print "xterm -e beam-back.py -v -n 3 %s"
  print
  sys.exit()


class FilenameFactory:
  #
  # generates filenames that won't overwrite an
  # an existing file if clobber == 0 by appending a -#
  #
  def __init__(self, clobber = 0):
    self.clobber = clobber
    self.cleaner  = re.compile(r'[\000\\/:*?"<>|()]')

  def set_clobber(self, clobber):
    self.clobber = clobber

  def clean(self, text):
    return self.cleaner.sub('', text)

  def spacer(self, text):
    textlist = string.split(text)
    return string.joinfields(textlist, "_")

  def make(self, filename):
    newfilename = filename
    if self.clobber == 0:
      dirname = os.path.dirname(newfilename)
      basename = os.path.basename(newfilename)
      (root, ext) = os.path.splitext(basename)
      copycnt = 0
      while os.path.isfile(newfilename):
        copycnt = copycnt + 1
        newfilename = dirname + '/' + root + "-" + `copycnt` + ext
    return newfilename
  
  def makeindir(self, dirname, filename):
    basename = self.clean(filename)
    newfilename = dirname + "/" + basename
    if self.clobber == 0:
      (root, ext) = os.path.splitext(basename)
      copycnt = 0
      while os.path.isfile(newfilename):
        copycnt = copycnt + 1
        newfilename = dirname + '/' + root + "-" + `copycnt` + ext
    return newfilename
  
  
class Logger:
  #
  # open a new log file in the target dir if logging
  # a race condition if there are tons of beam-back scripts
  # starting at the same time and should really use locking
  # but that would be overkill for this app
  #
  def __init__(self, logname = "beam-back.log", verbose = 0, logging = 0):
    self.logname = logname
    self.verbose = verbose
    self.logging = logging
    self.prefix = "beam-back: "
    if self.logging:
      self.logfp = open(self.logname, "w")
      self.logfp.write("beam-back v" + Version + "\n")
      self.logfp.write(self.prefix + "logging to " + self.logname + "\n")
      self.logfp.close()
      print (self.prefix + "logging to "+self.logname)

  def logit(self, logline):
    if self.verbose:
      print self.prefix + logline
    if self.logging:
      self.logfp = open(self.logname, "a")
      self.logfp.write(self.prefix + logline + "\n")
      self.logfp.close()


class ICY:
  #
  # ICY protocol class 
  #
  def __init__(self, host = '', port = 80):
    self.metaint = 0
    self.myport = port
    self.mydir = "/"

    # strip leading and trailing whitespace
    host = string.lstrip(host)
    host = string.rstrip(host)

    # strip leading http:// if any
    if string.lower(host[:4]) == "http":
      self.myhost = host[7:]
    else:
      self.myhost = host

    # strip trailing / if any
    if self.myhost[-1] == '/':
      self.myhost = self.myhost[:-1]

    # strip out dir if any
    p1 = string.find(self.myhost, "/")
    if p1 != -1:
      self.mydir = self.myhost[p1:]
      self.myhost = self.myhost[:p1]

    # handle port number in myhost, if any
    p1 = string.find(self.myhost, ':')
    if p1 != -1:
      portstr = self.myhost[p1+1:]
      self.myhost = self.myhost[:p1]
      try:
        self.myport = string.atoi(portstr)
      except:
        raise socket.error, "bad port in URL"


  def icyopen(self, icydata = 0):
    #
    # try to connect and request icy meta data if icydata == 1
    #
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.connect((self.myhost, self.myport))
    self.sock.send("GET " + self.mydir + " HTTP/1.0\r\n")
    if icydata == 1:
      self.sock.send("Icy-Metadata: 1\r\n")
    self.sock.send('\r\n')

    # convert the socket to a file handle
    self.file = self.sock.makefile('rb')

    # grab the statusline
    self.statusline = self.file.readline()
    try:
      statuslist = string.split(self.statusline)
    except ValueError:
      # assume it is okay since so many servers are badly configured
      statuslist = ["ICY", "200"]

    if statuslist[1] == "302":
      # moved temporarily status, look for location header
      while 1:
        line = self.file.readline()
        if not line:
          return -1
        if string.find(line, "Location") == 0:
          self.location = line[10:]
          
          # strip leading and trailing whitespace
          self.location = string.lstrip(self.location)
          self.location = string.rstrip(self.location)

          return -2

    if statuslist[1] != "200":
      return -1

    # grab any headers for a max of 10 lines
    icyline = "" 
    linecnt = 0
    while linecnt < 10:
      icyline = self.file.readline()
      linecnt = linecnt + 1
      # break on short line (ie. really should be a blank line)
      if len(icyline) < 4:
        break

      # strip leading and trailing whitespace
      icyline = string.lstrip(icyline)
      icyline = string.rstrip(icyline)

      # strip out icy headers
      if string.find(icyline, "icy-notice1") != -1:
        self.icynotice1 = icyline
      if string.find(icyline, "icy-notice2") != -1:
        self.icynotice2 = icyline
      if string.find(icyline, "icy-name") != -1:
        self.icyname = icyline
      if string.find(icyline, "icy-genre") != -1:
        self.icygenre = icyline
      if string.find(icyline, "icy-url") != -1:
        self.icyurl = icyline
      if string.find(icyline, "icy-pub") != -1:
        self.icypub = icyline
      if string.find(icyline, "icy-br") != -1:
        self.icybr = icyline
        self.bitrate = string.atoi(self.icybr[7:])
      if string.find(icyline, "icy-metaint") != -1:
        self.icymetaint = icyline
        self.metaint = string.atoi(self.icymetaint[12:])

    return self.file

  def getmetaint(self):
    return self.metaint

  def getbitrate(self):
    return self.bitrate

  def getstatusline(self):
    return self.statusline

  def getlocation(self):
    return self.location


  def icyclose(self):
    if self.file:
        self.file.close()
    self.file = None
    if self.sock:
        self.sock.close()
    self.sock = None

class MPEG:
  #
  # routines to analyze MPEG frame headers
  #

  def __init__(self):
    self.mpeg = ""
    self.layer = ""
    self.bitrate = 0
    self.samplerate = 0
    self.genretable = ["Blues", "Classic Rock", "Country", "Dance", "Disco", 
      "Funk", "Grunge", "Hip-Hop", "Jazz", "Metal", 
      "New Age", "Oldies", "Other", "Pop", "R&B", 
      "Rap", "Reggae", "Rock", "Techno", "Industrial",
      "Alternative", "Ska", "Death Metal", "Pranks", "Soundtrack",
      "Euro-Techno", "Ambient", "Trip-Hop", "Vocal", "Jazz+Funk",
      "Fusion", "Trance", "Classical", "Instrumental", "Acid",
      "House", "Game", "Sound Clip", "Gospel", "Noise",
      "AlternRock", "Bass", "Soul", "Punk", "Space",
      "Meditative", "Instrumental Pop", "Instrumental Rock", "Ethnic", "Gothic",
      "Darkwave", "Techno-Industrial", "Electronic", "Pop-Folk", "Eurodance",
      "Dream", "Southern Rock", "Comedy", "Cult", "Gangsta",
      "Top 40", "Christian Rap", "Pop/Funk", "Jungle", "Native American",
      "Cabaret", "New Wave", "Psychadelic", "Rave", "Showtunes",
      "Trailer", "Lo-Fi", "Tribal", "Acid Punk", "Acid Jazz",
      "Polka", "Retro", "Musical", "Rock & Roll", "Hard Rock",
      "Unknown"]

  def getmpeg(self):
    return self.mpeg

  def getlayer(self):
    return self.layer

  def getbitrate(self):
    return self.bitrate

  def getsamplerate(self):
    return self.samplerate

  #
  # calculate the mp3 frame length given a mp3 header
  # returns None or the frame length
  #
  def FrameLen(self, header):

    # get the 4 bytes of the header into integers
    h1 = ord(header[0])
    h2 = ord(header[1])
    h3 = ord(header[2])
    h4 = ord(header[3])
  
    # MPEG Version ID
    vID = (h2 & 24) >> 3   # 0 = V2.5, 1 = reserved, 2 = v2, 3 = v1
    if vID == 0:
      vName = "2.5"
    elif vID == 2:
      vName = "2"
    elif vID == 3:
      vName = "1"
    else:
      return None
    self.mpeg = vName

    # MPEG Layer
    layerID = (h2 & 6) >> 1     # 1=layerIII, 2=layerII, 3=layerI
    if layerID == 1:
      layerName = "III"
    elif layerID == 2:
      layerName = "II"
    elif layerID == 3:
      layerName = "I"
    else:
      return None
    self.layer = layerName
  
    # determine the bitrate
    rateID = (h3 & 240) >> 4
    
    if vName == "1" and layerName == "III":  
      ratetable = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, -1]
    elif vName == "1" and layerName == "II": 
      ratetable = [0, 32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384, -1]
    elif vName == "1" and layerName == "I": 
      ratetable = [0, 32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448, -1]
    elif vName == "2" and layerName == "III": 
      ratetable = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, -1]
    elif vName == "2" and layerName == "II": 
      ratetable = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, -1]
    elif vName == "2" and layerName == "I":  
      ratetable = [0, 32, 48, 56, 64, 80, 96, 112, 128, 144, 160, 176, 192, 224, 256, -1]
    elif vName == "2.5" and layerName == "III": 
      ratetable = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, -1]
    elif vName == "2.5" and layerName == "II": 
      ratetable = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, -1]
    elif vName == "2.5" and layerName == "I":  
      ratetable = [0, 32, 48, 56, 64, 80, 96, 112, 128, 144, 160, 176, 192, 224, 256, -1]
    else:
      ratetable = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
  
    br = ratetable[rateID] * 1000
    self.bitrate = br
  
    if br <= 0:
      return None
  
    # determine the sr
    sampleID = (h3 & 12) >> 2
  
    if vName == "1": 
      sampletable = [44100, 48000, 32000, -1]
    elif vName == "2": 
      sampletable = [22050, 24000, 16000, -1]
    elif vName == "2.5": 
      sampletable = [11025, 12000, 8000, -1]
    else:
      sampletable = [-1, -1, -1, -1]
  
    sr = sampletable[sampleID]
    self.samplerate = sr
    
    if sr <= 0:
      return None
  
    # grab the padding size in bytes 
    padbit = (h3 & 2) >> 1
    if padbit == 1 and layerName == "III":  
      padsize = 1
    elif padbit == 1 and layerName == "II":
      padsize = 1
    elif padbit == 1 and layerName == "I":
      padsize = 4
    else:
      padsize = 0

    # calculate frame length



    if vName == "1": 
      if layerName == "I":
        framelen = ((48 * br) / sr) + padbit
      else:
        framelen = ((144 * br) / sr) + padbit
    else:
      if layerName == "I":
        framelen = ((24 * br) / sr) + padbit
      else:
        framelen = ((72 * br) / sr) + padbit

    #if layerName == "I":
    #  framelen = (12 * br / sr + padsize) * 4
    #else:
    #  framelen = 144 * br / sr + padsize
  
    # channel mode
    channel = (h4 & 192) >> 6

    return framelen
  
  #
  # find the mp3 frame start index given a chunk of data
  # by checking for sync at the start of several headers
  # returns None or the frame start index
  #
  def FrameStart(self, data):
    f1 = -1
    dlen = len(data) - 100
    # find a possible frame sync
    while 1:
      f1 = f1 + 1
      if f1 >= dlen:
        break
      if ord(data[f1]) == 255 and ord(data[f1+1]) >= 224:
        flen1 = self.FrameLen(data[f1:f1+4])
        if flen1 == None:
          continue
        if f1 + flen1 >= dlen:
          return None
        if ord(data[f1+flen1]) == 255 and ord(data[f1+flen1+1]) >= 224:
          flen2 = self.FrameLen(data[f1 + flen1:f1 + flen1 + 4])
          if flen2 == None:
            continue
          if f1 + flen1 + flen2 >= dlen:
            return None
          if ord(data[f1 + flen1 + flen2]) == 255 and ord(data[f1 + flen1 + flen2+1]) >= 224:
            break
          else:
            continue
          
        else:
          continue
      
    if f1 >= dlen:
      return None
    else:
      return f1
      
  #
  # parse the ID3 V1 tag given the 128 bytes starting with tag
  # returns None or a tuple with the id3 info
  #
  def ID3v1(self, data):
    if data[0:3] == "TAG":
      title = string.rstrip(data[3:33])
      artist = string.rstrip(data[33:63])
      album = string.rstrip(data[63:93])
      year = string.rstrip(data[93:97])
      comment = string.rstrip(data[97:127])
      genre = string.rstrip(data[127:128])
      gid = ord(genre)
      if gid <= 80:
        return [title, artist, album, year, comment, self.genretable[gid]]
      else:
        return [title, artist, album, year, comment, `gid`]
    else:
      return None
    
  #
  # parse the ID3 V2 tag given mp3 data 
  # returns None or a tuple with the id3 info
  # INCOMPLETE
  #
  def ID3v2len(self, data):
    if data[0:3] == "ID3" and ord(data[3]) == 3:
      # get the 4 bytes of the header for frame size
      s1 = ord(data[5]) & 127
      s2 = ord(data[6]) & 127
      s3 = ord(data[7]) & 127
      s4 = ord(data[8]) & 127
      size = (s1 << 21) + (s2 << 14) + (s3 << 7) + (s4) + 10
      print size
      return None
    elif data[0:3] == "ID3" and ord(data[3]) == 4:
      # NOT FINISHED
      # get the 4 bytes of the header for frame size
      s1 = ord(data[6]) & 127
      s2 = ord(data[7]) & 127
      s3 = ord(data[8]) & 127
      s4 = ord(data[9]) & 127
      size = (s1 << 21) + (s2 << 14) + (s3 << 7) + (s4)
      print size + 10
      return None
    else:
      return None


if __name__=="__main__":

  #
  # check the os we are running on and print the version
  #
  if sys.platform == "win32":
    print "beam-back v" + Version + " win32"
  else:
    print "beam-back v" + Version + " linux"

  #
  # default options
  #
  opt_verbose = 0
  opt_logging = 0
  opt_topdir = "."
  opt_naming = "1"
  opt_playlist = 0
  opt_clobber = 0
  opt_icydata = 0
  opt_persistent = 0
  opt_unfinished = "unfinished-stream.mp3"
  opt_size = 0
  opt_trim = 0
  opt_framing = 0

  #
  # parse the command line options
  #
  if len(sys.argv) == 1:
    Usage()

  try:
    opts, args = getopt.getopt(sys.argv[1:], "cd:ilmn:pu:vz:t:f")
  except getopt.error, reason:
    print reason
    sys.exit(-1)

  if len(args) == 0:
    Usage()

  #
  # check clobber, verbose, logging and topdir options first
  #
  for opt in opts:
    (lopt, ropt) = opt
    if lopt == "-c":
      opt_clobber = 1
    elif lopt == "-l":
      opt_logging = 1
    elif lopt == "-v":
      opt_verbose = 1
    elif lopt == "-d":
      if os.path.isdir(ropt):
        opt_topdir = ropt
      else:
        print "bad top directory"
        sys.exit()

  # fix the top dir name to not end in slash
  if opt_topdir[-1:] == "/":
    opt_topdir = opt_topdir [:-1]

  # create the filename factory object
  fnfactory = FilenameFactory(opt_clobber)

  # create the logger object
  logname = fnfactory.makeindir(opt_topdir, "beam-back.log")
  logger = Logger(logname, opt_verbose, opt_logging)

  # log the options set before log object created
  if opt_clobber == 1:
    logger.logit("clobber option set")
  if opt_logging == 1:
    logger.logit("logging option set")
  if opt_verbose == 1:
    logger.logit("verbose option set")
  logger.logit("storing files in " + opt_topdir)

  #
  # handle other options and log as needed
  #
  for opt in opts:
    (lopt, ropt) = opt
    if lopt == "-i":
      opt_icydata = 1
      logger.logit("icydata option set")
    elif lopt == "-m":
      # opt_playlist = 1 means create a new playlist
      # opt_playlist = 2 means playlist created add mp3 file name
      opt_playlist = 1
      logger.logit("playlist option set")
    elif lopt == "-n":
      if ropt == "1" or ropt == "2" or ropt == "3" or ropt == "4" or ropt == "1u" or ropt == "2u" or ropt == "3u" or ropt == "4u":
        opt_naming = ropt
        logger.logit("naming option set to " + ropt)
      else:
        print "bad naming option"
        sys.exit()
    elif lopt == "-p":
      opt_persistent = 1
      logger.logit("persistent option set")
    elif lopt == "-u":
      opt_unfinished = ropt
      logger.logit("unfinished option set to " + ropt)
    elif lopt == "-z":
      try:
        opt_size = string.atoi(ropt)
        logger.logit("size limit option set to " + ropt + "M")
      except:
        opt_size = 0
        logger.logit("bad size limit option")
    elif lopt == "-t":
      try:
        opt_trim = string.atoi(ropt)
        logger.logit("trim option set to " + ropt)
      except:
        opt_trim = 0
        logger.logit("bad trim option")
    elif lopt == "-f":
      opt_framing = 1
      logger.logit("framing option set")

  inputfile = args[0] # name of the m3u file
  taggedcnt = 0 # number of mp3 files downloaded
  notagcnt = 0 # number of files that look bad (no ID3 tags)
  failedcnt = 0 # number of files that failed the transfer
  plname = "" # the playlist name

  #
  # get the input file
  #
  lines = []
  if(inputfile[:7] == "http://"):
    fTmp = urllib.urlopen(inputfile)
    fTmpWrite = open("/tmp/beam-back.pls", 'w')
    plsLines = fTmp.readlines()
    for line in plsLines:
      fTmpWrite.write(line)
    inputfile = "/tmp/beam-back.pls"
    fTmpWrite.close()

  logline = "inputfile " + inputfile
  logger.logit(logline)
  
  inputfp = open(inputfile, "r")
  while (1):
    line = inputfp.readline()
    if not line:
      break    
    lines.append(line)
  inputfp.close()

  urls = []
  opt_plsfile = 0
  if inputfile[-4:] == ".pls":
    newurl = ""
    for plsfile in lines:
      if string.find(plsfile, "File") == 0:
        p1 = string.find(plsfile, "=")
        newurl = plsfile[p1+1:]

        # strip leading and trailing whitespace
        newurl = string.lstrip(newurl)
        newurl = string.rstrip(newurl)

        if opt_verbose:
          logline = "server url " + newurl
          logger.logit(logline)
        urls.append(newurl)
        opt_plsfile = 1
    if not newurl:
      logline = "playlist handling file error"
      logger.logit(logline)
      sys.exit()
  else:
    # m3u file
    urls = lines
    if opt_verbose:
      logline = "transferring " + `len(urls)` + " URL(s)."
      logger.logit(logline)


  # now go thru the urls
  #
  for url in urls:

    # pause before starting song to give my.mp3.com 
    # a chance at authorizing the url before we access it
    time.sleep(1)

    # strip leading and trailing whitespace
    url = string.lstrip(url)
    url = string.rstrip(url)

    # if the url consists only of a host treat it like
    # a playlist (ie. icecast m3u playlists)
    p1 = string.rfind(url, "/")
    if p1 == -1 or p1 > len(url) - 5 or opt_plsfile == 1:
      opt_plsfile = 1

      if url[-1] == "/":
        url = url[:-1]
      logline = "Trying stream " + url
      logger.logit(logline)
    else:
      logline = "Getting file " + url[p1+1:]
      logger.logit(logline)

    #
    # Open the URL using urllib for m3u and icy for pls
    #
    bytesread = 0
    kilobytes = 0
    blocksize = 4*1024
    if opt_plsfile:
      if opt_verbose:
        logline = "ICY " + url[7:]
        logger.logit(logline)
      icy = ICY(url[7:])
      urlfp = icy.icyopen(opt_icydata)

      if urlfp == -2:
        logline = "\"" + url + "\" moved to " + icy.getlocation()
        logger.logit(logline)

        url = icy.getlocation()
        logline = "Trying new location " + url
        logger.logit(logline)
        icy = ICY(url)
        urlfp = icy.icyopen(opt_icydata)

      if urlfp < 0:
        logline = icy.getstatusline()
        logger.logit(logline)
        continue

    else:
      urlfp = urllib.urlopen(url)

    #
    # create a temp file for the data
    #
    tempfile.tempdir = opt_topdir
    tmpfilename = tempfile.mktemp(".mp3")
    tmpfp = open(tmpfilename, "wb")


    mpeg = MPEG()
    icyfilename = ""
    icycount = 1
    icychunk = ""
    
    try:
      blockread = urlfp.read(blocksize)

      # discard the beginning junk that doesn't look like a mp3 frame
      #if opt_framing == 1 and opt_plsfile == 0:
      if opt_framing == 1:
        fstart = mpeg.FrameStart(blockread)
        floop = 0
        while fstart == None and floop < 7:
          if opt_verbose:
            logger.logit("NO Frame " + `fstart` + " MPEG v" + mpeg.getmpeg() + " Layer " + mpeg.getlayer())
          moreread = urlfp.read(blocksize)
          blockread = blockread + moreread
          fstart = mpeg.FrameStart(blockread)
          floop = floop + 1

        if fstart != None:
          if opt_verbose:
            logger.logit("Frame " + `fstart` + " MPEG v" + mpeg.getmpeg() + " Layer " + mpeg.getlayer())
          blockread = blockread[fstart:]
        else:
          logger.logit("Could not find the frame start.  Framing disabled.")
          opt_framing = 0


      while 1:
        if len(blockread) == 0 and opt_persistent == 0:
          break

        bytesread = bytesread + len(blockread)
        if bytesread > 100000:
          # track bytesread with two variables
          kilobytes = kilobytes + 100
          bytesread = bytesread - 102400
        mesgbytes = kilobytes + (bytesread / 1000)
        print "Data read: " + `mesgbytes` + "K     CTRL-C to stop\r",

        sys.stdout.flush()

        if opt_icydata == 0:
          # write the block, non icy data
          if len(blockread) > 0:
            tmpfp.write(blockread)

        else:
          # we really want to compute the following expression 
          # (bytesread + (kilobytes * 1024)) <= icycount * icy.getmetaint():
          # but this will overflow after 2G of capturing (~30hrs)
          #
          # so we use lhs to icyread and rhs to icynext
          # and reduce the counters
          icyread = 0
          icynext = 0
          if (bytesread + (kilobytes * 1024)) <= icycount * icy.getmetaint():
            # save a block that doesn't need icy processing
            icychunk = icychunk + blockread

          else:
            # handle a block with ICY metadata
            icycount = icycount + 1

            # write a warning if the beginning looks messed up
            if ord(blockread[0]) > 20:
              logger.logit("VERY Suspicious beginning of meta data.   ")

            # determine the length via the length byte
            metalen = ord(blockread[0]) * 16

            # read some more data to maintain chunk boundaries
            if metalen == 0:
              metadata = blockread[:1]
              moreread = urlfp.read(1)
              blockread = blockread[1:] + moreread

              # write the icy chunk previous to this block
              tmpfp.write(icychunk)

              # save this chunk for writing 
              icychunk = blockread

            else:
              if blockread[metalen] != "\0":
                logger.logit("VERY Suspicious ending of meta data.   ")

              metadata = blockread[:metalen]
              moreread = urlfp.read(metalen + 1)
              blockread = blockread[metalen+1:] + moreread

              # analyze the metadata for the stream title
              # before writing the block
              p1 = string.find(metadata, "StreamTitle") 
              if p1 == -1:
                # couldn't find the StreamTitle heading
                logger.logit("Couldn't find StreamTitle in metadata.   ")

                # write the icy chunk previous to this block
                tmpfp.write(icychunk)

                # save this block for writing later as a chunk
                icychunk = blockread

              else:

                p2 = string.find(metadata, "'", p1);
                p3 = string.find(metadata, "';", p2+1)
                mp3name = icyfilename
                if p2+1 == p3:
                  icyfilename = "notitle.mp3"
                else:
                  icyfilename = metadata[p2+1:p3] + ".mp3"

                logline = "%-40s" % icyfilename
                logger.logit(logline)

                if opt_icydata == 1:
                  # first stream title encountered
                  # set the flag to use this title as name of file
                  # at the end of the song
                  opt_icydata = 2

                  # write the icy chunk previous to this block
                  tmpfp.write(icychunk)

                  # save this block for writing later as a chunk
                  icychunk = blockread

                elif opt_icydata == 2:

                  # close the file and rename it correctly
                  tmpfp.close()
                  newmp3name = fnfactory.makeindir(opt_topdir, mp3name)

                  # trim the end if needed
                  if opt_trim > 0:
                    trimsize = opt_trim * icy.getbitrate() 
                    tmpfp = open(tmpfilename, "rb")
                    tmpdata = tmpfp.read()
                    tmpfp.close()
                    tmpfp = open(newmp3name, "wb")
                    if len(tmpdata) <= trimsize:
                      tmpfp.write(tmpdata)
                    else:
                      # find a frame to trim at
                      fstart = mpeg.FrameStart(tmpdata[:-trimsize])
                      if fstart == None:
                        tmpfp.write(tmpdata[:-trimsize])
                      else:
                        tmpfp.write(tmpdata[:-(trimsize - fstart)])

                    tmpfp.close()
                    os.unlink(tmpfilename)
                  else:
                    os.rename(tmpfilename, newmp3name)
                  
                  # open a new file
                  tempfile.tempdir = opt_topdir
                  tmpfilename = tempfile.mktemp(".mp3")
                  tmpfp = open(tmpfilename, "wb")

                  # write out the icychunk to the new file
                  tmpfp.write(icychunk)
                  
                  # save this block for writing later as a chunk
                  icychunk = blockread


        # read a new block for processing
        blockread = urlfp.read(blocksize)

        # check the size limit, only compare kilo vs mega
        if opt_size > 0:
          if (kilobytes * 1024) > opt_size:
            urlfp.close() 
            tmpfp.close()
            if opt_icydata == 2:
              newmp3name = fnfactory.makeindir(opt_topdir, icyfilename)
              os.rename(tmpfilename, newmp3name)
              logline = "size limit reached saved to " + newmp3name
            else: 
              newmp3name = fnfactory.makeindir(opt_topdir, opt_unfinished)
              os.rename(tmpfilename, newmp3name)
              logline = "size limit reached saved to " + newmp3name
            logger.logit(logline)
            sys.exit()

        # possibly reopen if persistent
        if len(blockread) == 0 and opt_persistent == 1:
          # close and reopen
          if opt_plsfile:
            logline = "Reopening PLS " + url[7:]
            logger.logit(logline)
            icy.icyclose()
            urlfp = icy.icyopen(opt_icydata)
          else:
            logline = "Reopening M3U " + url
            logger.logit(logline)
            urlfp.close() 
            urlfp = urllib.urlopen(url)


      urlfp.close() 
      tmpfp.close()
    except KeyboardInterrupt:
      # rename the temp file to the interrupted name
      urlfp.close() 
      tmpfp.close()
      if opt_icydata == 2:
        newmp3name = fnfactory.makeindir(opt_topdir, icyfilename)
        os.rename(tmpfilename, newmp3name)
        logline = "keyboard interrupt, saved to " + newmp3name
      else: 
        newmp3name = fnfactory.makeindir(opt_topdir, opt_unfinished)
        os.rename(tmpfilename, newmp3name)
        logline = "keyboard interrupt, saved to " + newmp3name
      logger.logit(logline)
      sys.exit()

    #
    # non-icy data streams from here on
    #

    #
    # need to check if the size of returned data is suspiciously small
    #
    if bytesread < 2048 and kilobytes <= 0:
      datafp = open(tmpfilename, "rb")
      data = datafp.read()
      datafp.close()

      logline = "FAILED \"" + url + "\" "
      logger.logit(logline)
      failedcnt = failedcnt + 1
      continue

    # grab the id3 info
    tmpfp = open(tmpfilename, "rb")
    tmpfp.seek(-128, 2)
    id3 = tmpfp.read(128)
    tmpfp.close()

    if id3[0:3] == "TAG":
      taggedcnt = taggedcnt + 1
      title = string.rstrip(id3[3:33])
      artist = string.rstrip(id3[33:63])
      album = string.rstrip(id3[63:93])
    else:
      notagcnt = notagcnt + 1
      title = "notitle"
      artist = "noartist"
      album = "noalbum"

    # clean up id3 strings before using them for filename creation
    title = fnfactory.clean(title)
    artist = fnfactory.clean(artist)
    album = fnfactory.clean(album)

    # fix up the spaces to underscores if specified
    divider = " - "
    if len(opt_naming) > 1:
       if opt_naming[1] == "u":
         title = fnfactory.spacer(title)
         artist = fnfactory.spacer(artist)
         album = fnfactory.spacer(album)
         divider = "-"

    # compute a playlist name if necessary
    if opt_playlist == 1:
      plcnt = 1
      if not album:
        plname = artist + ".m3u"
      else:
        plname = artist + divider + album + ".m3u"

      newplname = fnfactory.makeindir(opt_topdir, plname)
      playfp = open(newplname, "w")
      playfp.close()
      opt_playlist = 2

    #
    # compute the output mp3 filename
    #
    mp3name = ""
    mp3dir = ""
    if opt_naming[0] == "1":
      mp3dir = opt_topdir 
      mp3name = artist + divider + title + ".mp3"
    elif opt_naming[0] == "2":
      mp3dir = opt_topdir 
      mp3name = title + ".mp3"
    elif opt_naming[0] == "3":
      mp3dir = opt_topdir + "/" + artist
      if not os.path.isdir(mp3dir):
        os.mkdir(mp3dir) 
      mp3name = title + ".mp3"
    elif opt_naming[0] == "4":
      mp3dir = opt_topdir + "/" + artist
      if not os.path.isdir(mp3dir):
        os.mkdir(mp3dir) 
      mp3name = artist + divider + title + ".mp3"
    else:
      # should never be here but just in case have a default
      mp3dir = opt_topdir 
      mp3name = artist + divider + title + ".mp3"

    # if the mp3name already exists create a copy count name
    newmp3name = fnfactory.makeindir(mp3dir, mp3name)
    os.rename(tmpfilename, newmp3name)

    if bytesread < 2048 and kilobytes <= 0:
      logline = "SUSPICIOUSLY SMALL " + newmp3name 
      logger.logit(logline)
    else:
      logline = "creating " + newmp3name
      logger.logit(logline)

    # write the playlist
    if opt_playlist == 2:
      playfp = open(plname, "a")
      playfp.write(newmp3name + "\n")
      playfp.close()

  # show the summary
  logline = "=========="
  logger.logit(logline)

  logline = "success on " + `taggedcnt` + " file(s)."
  logger.logit(logline)

  if (notagcnt > 0):
    logline = "no ID3 tags on " + `notagcnt` + " file(s)."
    logger.logit(logline)
  
  if (failedcnt > 0):
    logline = "failed transfers on " + `failedcnt` + " file(s)."
    logger.logit(logline)

  print "Done."

  if (failedcnt > 0) or (notagcnt > 0):
    time.sleep(10)
  else:
    time.sleep(5)

