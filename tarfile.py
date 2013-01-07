'''
 (C)opyright 2001 Jason Petrone <jp_py@jsnp.net>
  All Rights Reserved

Access tar and tar.gz files using the same interface as zipinfo from the
standard library.

Requires Python >= 2.2.

Read-only for now

'''

#
# TODO: - links
#       - write/append
#
# 0.2:
#   o bail out if using GzipFile without tell()
#   o command line help
#
# 0.1: 
#   o initial release

__version__ = '0.2'

from cStringIO import *
import struct, os
import gzip

if not dir(gzip.GzipFile).count('tell'):
  raise Exception, 'tarfile.py requires Python >= 2.2'

_BLOCKSIZE = 512
_NAMESIZE = 100
_TUNMLEN = 32
_TGNMLEN = 32

# Values used in typeflag field
REGTYPE  = '0'            # regular file 
AREGTYPE = '\0'           # regular file 
LNKTYPE  = '1'            # link 
SYMTYPE  = '2'            # reserved 
CHRTYPE  = '3'            # character special 
BLKTYPE  = '4'            # block special 
DIRTYPE  = '5'            # directory 
FIFOTYPE = '6'            # FIFO special 
CONTTYPE = '7'            # reserved 


def octToInt(s):
  s = s.replace('\0', '').strip()
  i = 0
  s = list(s)
  s.reverse()
  for c in range(len(s)):
    i += int(s[c]) * pow(8, c)
  return i

class TarInfo:
  def __init__(self, hdr, offset):
    self.hdr = hdr
    f = StringIO(hdr)
    self.name = f.read(_NAMESIZE).replace('\0', '')
    self.mode = octToInt(f.read(8))
    self.uid = octToInt(f.read(8))
    self.gid = octToInt(f.read(8))
    self.size = octToInt(f.read(12))
    self.mtime = octToInt(f.read(12))
    self.cksum = octToInt(f.read(8))
    self.typeflag = f.read(1)
    if len(self.name) > 0 and list(self.name).pop() == '/': 
      # some tar implementations use a trailing / to indicate a directory
      self.typeflag = DIRTYPE
    self.linkname = f.read(_NAMESIZE)
    self.magic = f.read(8)
    self.uname = f.read(_TUNMLEN)
    self.gname = f.read(_TGNMLEN)
    self.dev = f.read(16)
    self.file_offset = offset
  def check(self):
    sum = 0
    # Adjust checksum to count the "chksum" field as blanks.
    tail = self.hdr[156:]
    self.hdr = self.hdr[:148] + 8*' ' + tail
    for c in self.hdr: sum += 0xff & ord(c)
    return self.cksum == sum

class TarFile:
  def __init__(self, filename, mode='r'):
    self.entries = {}  # quick hashing for single lookups
    self.names = []  # keep a list of names to maintain ordering
    self.mode = mode
    self.filename = filename
    self.open(filename, mode)
  def open(self, filename, mode):
    self.f = open(filename, mode+'b')
    head = self.f.read(4)
    if head[:2] == '\037\213':  # check for gzip header
      self.f = gzip.open(filename)
    else:
      self.f.seek(0)

  def close(self):
    """Close the file, and for mode "w" and "a" write the ending
    records."""
    self.f.close()

  def _load(self):
    while 1:
      hdr = self.f.read(_BLOCKSIZE)
      if hdr.count('\0') == _BLOCKSIZE: break
      elif len(hdr) == 0: break
      entry = TarInfo(hdr, self.f.tell())
      self.entries[entry.name] = entry
      self.names.append(entry.name)
      rem = entry.size % _BLOCKSIZE
      if rem: size = entry.size - rem + _BLOCKSIZE
      else: size = entry.size
      if isinstance(self.f, gzip.GzipFile): self.f.read(size)
      else: self.f.seek(self.f.tell() + size)
  
  def namelist(self):
    """Return a list of file names in the archive."""
    if not self.names: self._load()
    return self.names

  def infolist(self):
    """Return a list of class TarInfo instances for files in the
       archive."""
    if not self.names: self._load()
    info = []
    for n in self.names: 
      info.append(self.entries[n])
    return info

  def getinfo(self, name):
    """Return the instance of TarInfo given 'name'."""
    if not self.entries: self._load()
    return self.entries[name]

  def testcrc(self):
    """Read all the files and check the CRC."""
    pass

  def write(self, filename):
    """Put the bytes from filename into the archive under the name
       arcname."""
    pass

  def writestr(self, tinfo, bytes):
    """Write a file into the archive.  The contents is the string
       'bytes'."""
    pass

  def read(self, name):
    '''
    Return the bytes of the file in the archive.  The archive must be open for
    read of append.
    '''
    if not self.entries: self._load()
    entry = self.entries[name] 
    if not entry.typeflag in [REGTYPE, AREGTYPE]: return None
    if isinstance(self.f, gzip.GzipFile):
      # GzipFile doesn't support seeking
      if self.f.tell() > entry.file_offset:
        self.close()
        self.open(self.filename, self.mode)
      self.f.read(entry.file_offset - self.f.tell())
    else:
      self.f.seek(entry.file_offset)
    return self.f.read(entry.size)

  def untar(self, path):
    import os
    oldcwd = os.getcwd()
    os.chdir(path)
    for n in self.namelist():
      i = self.getinfo(n)
      if i.typeflag == DIRTYPE:
        if not os.path.exists(i.name): os.mkdir(i.name)
      elif i.typeflag in [REGTYPE, AREGTYPE]:
        f = open(i.name, 'wb')
        f.write(self.read(i.name))
        f.close()
        os.chmod(i.name, i.mode)
      # elif i.typeflag == LNKTYPE:
      #
    os.chdir(oldcwd)
  
def istar(filename):
  head = open(filename, 'rb').read(4)
  if head[:2] == '\037\213':
    # gzip'd
    import gzip
    f = gzip.open(filename)
  else:
    f = open(filename, 'rb')
  hdr = f.read(_BLOCKSIZE)
  try: info = TarInfo(hdr, 0)
  except Exception, e: return None
  return info.check() 

if __name__ == '__main__':
  import sys, os
  if len(sys.argv) != 2:
    sys.stderr.write('\nusage: '+sys.argv[0]+' <file.gz>\n\n')
    sys.exit(-1)
  t = TarFile(sys.argv[1])
  for i in t.infolist():
    print i.name
    if i.typeflag == DIRTYPE:
      if not os.path.exists(i.name): os.mkdir(i.name)
    elif i.typeflag in [REGTYPE, AREGTYPE]:
      f = open(i.name, 'wb')
      f.write(t.read(i.name))
      f.close()
      os.chmod(i.name, i.mode)
    # elif i.typeflag == LNKTYPE:
    #
  
