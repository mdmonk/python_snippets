# Volatility
# Copyright (C) 2008 Volatile Systems
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#

from vutils import *
from forensics.win32.tasks import *
from forensics.win32.executable import rebuild_exe_mem
from forensics.win32.vad import *

import pydasm
import pefile

def get_vad_range(process_address_space, StartingVpn, EndingVpn):
    Range = EndingVpn - StartingVpn + 1
    NumberOfPages = Range >> 12
    range_data = '' 

    if (StartingVpn == 0) or (EndingVpn > 0x7FFFFFFF):
        return range_data

    for i in range(0, NumberOfPages):
        page_addr = StartingVpn+i*0x1000
        if not process_address_space.is_valid_address(page_addr):
            range_data + ('\0' * 0x1000)
            continue

        page_read = process_address_space.read(page_addr, 0x1000)
        if page_read == None:
            range_data = range_data + ('\0' * 0x1000)
        else:
            range_data = range_data + page_read

    return range_data
    
def rebuild_pe(addr_space, types, pe_base, pe_filename):
    try:
        f = open(pe_filename, 'wb')
        rebuild_exe_mem(addr_space, types, pe_base, f, True)
        f.close()
    except:
        print "[!] Error dumping PE file to %s" % pe_filename

def dump_to_file(name, data):
    f = open(name, "wb")
    f.write(data)
    f.close()

# hexdump formula from http://code.activestate.com/recipes/142812/ 

FILTER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])

def dump2(src, start=0, length=16):
    result=[]
    for i in xrange(0, len(src), length):
        s = src[i:i+length]
        hexa = ' '.join(["%02x"%ord(x) for x in s])
        printable = s.translate(FILTER)
        result.append("0x%08x   %-*s   %s\n" % (i+start, length*3, hexa, printable))
    return ''.join(result)

class malfind2(forensics.commands.command):

    # Declare meta information associated with this plugin

    meta_info = forensics.commands.command.meta_info
    meta_info['author'] = 'Michael Ligh'
    meta_info['copyright'] = 'Copyright (c) 2008,2009 Michael Ligh'
    meta_info['contact'] = 'michael.ligh@mnin.org'
    meta_info['license'] = 'GNU General Public License 2.0 or later'
    meta_info['url'] = 'http://www.mnin.org'
    meta_info['os'] = 'WIN_32_XP_SP2'
    meta_info['version'] = '1.0'

    def parser(self):

        forensics.commands.command.parser(self)

        self.op.add_option('-d', '--dir',
            help='Output directory for extracted data',
            action='store', type='string', dest='dir')

        self.op.add_option('-p', '--pid',
            help='Examine this pid only',
            action='store', type='string', dest='pid')

    def help(self):
        return "Detect hidden and injected code"

    def execute(self):

        op = self.op
        opts = self.opts

        if (opts.filename is None) or (not os.path.isfile(opts.filename)):
            op.error("File is required")
        else:
            filename = opts.filename

        if (opts.dir is None):
            op.error("Directory is required")
        else:
            if not os.path.isdir(opts.dir):
                os.mkdir(opts.dir)
            vaddir = opts.dir

        print "\n", '#' * 25, 'Malfind Report', '#' * 25, "\n"

        (addr_space, symtab, types) = load_and_identify_image(op, opts)
        all_tasks = process_list(addr_space, types, symtab)

        for task in all_tasks:
            if not addr_space.is_valid_address(task):
                continue

            directory_table_base = process_dtb(addr_space, types, task)
            process_id = process_pid(addr_space, types, task)
            
            image_file_name = process_imagename(addr_space, types, task)
            if image_file_name is None:
                image_file_name = "UNKNOWN"

            # by default, scan all processes - otherwise only scan the selected one
            if (opts.pid is None) or (int(opts.pid) == process_id):
                print "#\n# %s (Pid: %s)\n#\n" % (image_file_name, process_id)
                
                process_address_space = create_addr_space(addr_space, directory_table_base)
                if process_address_space is None:
                    print "[!] Error obtaining address space for process [%d]\n" % (process_id)
                    continue

                VadRoot = process_vadroot(process_address_space, types, task)
                if VadRoot == None or not process_address_space.is_valid_address(VadRoot):
                    print "[!] Error obtaining VAD root for process [%d]\n" % (process_id)
                    continue

                vadlist = []
                traverse_vad(None, process_address_space, types, VadRoot, append_entry, None, None, 0, vadlist)
                
                for vad_entry in vadlist: 
                    tag_addr = vad_entry - 0x4
                    if not process_address_space.is_valid_address(tag_addr):
                        continue

                    tag = process_address_space.read(tag_addr,4)
                    StartingVpn = read_obj(process_address_space, types, ['_MMVAD_LONG', 'StartingVpn'], vad_entry)
                    StartingVpn = StartingVpn << 12

                    EndingVpn = read_obj(process_address_space, types, ['_MMVAD_LONG', 'EndingVpn'], vad_entry)
                    EndingVpn = ((EndingVpn+1) << 12) - 1         

                    (u_offset, tmp) = get_obj_offset(types, ['_MMVAD_LONG', 'u'])
                    Flags = read_value(process_address_space, 'unsigned long', u_offset+vad_entry)
                    Protection = (Flags & get_mask_flag('_MMVAD_FLAGS', 'Protection')) >> 24
                    
                    range_data = ''
                    ofname = "%s/malfind.%d.%x-%x.dmp" % (vaddir, process_id, StartingVpn, EndingVpn) 
                    
                    if tag == "VadS":
                        
                        if (Protection == 0x2) or (Protection == 0x3) or \
                           (Protection == 0x6) or (Protection == 0x7) or (Protection == 0x18):
                          
                           range_data = get_vad_range(process_address_space, StartingVpn, EndingVpn) 
                           
                           if (range_data != None) and (len(range_data) > 2):
                               
                               print "[!] Range: 0x%08x - 0x%08x" % ( StartingVpn, EndingVpn)
                               print "Memory extracted to %s" % ofname

                               # Found a PE file
                               
                               if range_data[0:2] == 'MZ':
                                   rebuild_pe(process_address_space, types, StartingVpn, ofname)
                                   
                                   if os.path.isfile(ofname):
                                       try:
                                           pe = pefile.PE(data=open(ofname).read())
                                       except:
                                           print "[!] Cannot open %s with pefile\n" % ofname
                                           continue
                                           
                                       secinfo = ""
                                       for sec in pe.sections:
                                           secinfo += "%s, " % sec.Name.replace('\0', '')
                                           
                                       print "PE sections: {%s}" % secinfo
                                       
                                       # Fixup the ImageBase in case we plan to open in IDA
                                       
                                       pe.OPTIONAL_HEADER.ImageBase = StartingVpn
                                       pe.write(ofname)
                                      
                                   # If rebuild_exe_mem fails for any reason, just dump the memory range
                                   
                                   else: 
                                       dump_to_file(ofname, range_data)
                                      
                               else:
                                   
                                   dump_to_file(ofname, range_data)
                                   size = len(range_data) if len(range_data) < 64 else 64
                                   
                                   print "Hexdump:\n", dump2(range_data[0:size], StartingVpn)
                                   print "Disassembly:"
                                   offset = 0
                                   while (offset < size):
                                       k = pydasm.get_instruction(range_data[offset:], pydasm.MODE_32)
                                       print "0x%08x   %s" % (StartingVpn+offset, pydasm.get_instruction_string(k, pydasm.FORMAT_INTEL, StartingVpn))
                                       if not k:
                                           break
                                       offset += k.length
                                       
                               print ""

