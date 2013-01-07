#!/usr/bin/env python

import commands

SENSORS = ['fofw', 'dmz', 'fw']

class SguilServerStatus:
    """ check the status of the sguild server and mysql processes. """

    def __init__(self):
        self.allprocs = commands.getoutput('/bin/ps -ef').split('\n')
        self.mysql_procs = {}
        self.sguild_procs = []
        for i in self.allprocs:
            if 'mysqld_safe' in i:
                a = i.split()
                self.mysql_procs['mysqld_safe']=a[1]
            elif 'mysqld' in i:
                a = i.split()
                self.mysql_procs['mysqld']=a[1]
            elif 'server/sguild' in i:
                a = i.split()
                self.sguild_procs.append(a[1])

    def check(self, xthing, xlen):
        """ return OK or FAIL """
        import curses
        curses.setupterm()
        cap = curses.tigetstr('setf')
        GREEN = curses.tparm(cap, 2)
        RED = curses.tparm(cap, 4)
        RESET = curses.tparm(cap, 9)
        if len(xthing) != xlen:
            print "...........[%sFAIL%s]" % (RED, RESET)
        else:
            print "...........[%sOK%s]" %(GREEN,RESET)
        

    def server_status(self):
        print "Checking Sguild",
        self.check(self.sguild_procs, 3)
        for i in self.sguild_procs:
            print "    sguild (%s)" % i

        print "Checking Mysql",
        self.check(self.mysql_procs, 2)
        for k,v in self.mysql_procs.iteritems():
            print "    %s (%s)" % (k,v)


class SguilSensorStatus:
    """ check the status of the passed sguil sensor and supporting processes. """

    def __init__(self, name = "fofw"):
        self.name = name
        self.allprocs = commands.getoutput('/bin/ps -ef').split('\n')
        self.grpprocs = []
        for i in self.allprocs:
            if self.name in i:
                self.grpprocs.append(i)

        self.sensor_procs = {}
        self.sensor_proc_count = 0
        for i in self.grpprocs:
            if '/'+name+'/sancp' in i:
                a = i.split()
                self.sensor_procs['sancp']=a[1]
                self.sensor_proc_count += 1
            elif 'barnyard-'+name+'.conf' in i:
                a = i.split()
                self.sensor_procs['barnyard']=a[1]
                self.sensor_proc_count += 1
            elif 'sensor_agent-'+name+'.conf' in i:
                a = i.split()
                self.sensor_procs['sguil sensor']=a[1]
                self.sensor_proc_count += 1
            elif 'snort -u sguil' in i and '-b' in i and 'snort-data/'+name+'/' in i:
                a = i.split()
                self.sensor_procs['snort logging']=a[1]
                self.sensor_proc_count += 1
            elif 'snort -u sguil' in i and '-D' in i and 'snort-'+name+' ' in i:
                a = i.split()
                self.sensor_procs['snort alerts']=a[1]
                self.sensor_proc_count += 1
		#print 'snort alerts', a[1] 

            if not self.sensor_procs.has_key('sancp'):
                self.sensor_procs['sancp']='/etc/init.d/sancp-%s' % name

            if not self.sensor_procs.has_key('barnyard'):
                self.sensor_procs['barnyard']='/etc/init.d/barnyard-%s' % name

            if not self.sensor_procs.has_key('sguil sensor'):
                self.sensor_procs['sguil sensor']='/etc/init.d/sguil_agent-%s' % name

            if not self.sensor_procs.has_key('snort alerts'):
                self.sensor_procs['snort alerts']='/etc/init.d/snort-%s' % name

            if not self.sensor_procs.has_key('snort logging'):
                self.sensor_procs['snort logging']='/etc/init.d/sguil_logger-%s' % name



    def check(self, xthing, xlen):
        """ return OK or FAIL """
        import curses
        curses.setupterm()
        cap = curses.tigetstr('setf')
        GREEN = curses.tparm(cap, 2)
        RED = curses.tparm(cap, 4)
        RESET = curses.tparm(cap, 9)
        if xthing != xlen:
            print "...........[%sFAIL%s] %d/%d" % (RED, RESET, xthing, xlen)
        else:
            print "...........[%sOK%s]" %(GREEN,RESET)

    def sensor_status(self):
        print "Checking", self.name,
        self.check(self.sensor_proc_count, 5)
        for k,v in self.sensor_procs.iteritems():
            print "    %s (%s)" % (k,v)
    


if __name__ == "__main__":
    
    server=SguilServerStatus()
    server.server_status()

    for i in SENSORS:
        xa = SguilSensorStatus(i)
        xa.sensor_status()
