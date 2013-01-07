#!/usr/bin/env python24

import logging
import anydbm
import ConfigParser
import rrd
import sys
import re
import errno
import os
import time
import traceback
import signal
import optparse
import gzip

def stack_dump_handler(signo, frame):
    print '-'*60
    print 'Stack dump:'
    traceback.print_stack(frame)
    print '-'*60

signal.signal(signal.SIGQUIT, stack_dump_handler)

syslog_re = re.compile("""
    ^
    (?P<nulls> \000*)
    (?P<date>
        (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \s+
        \d{1,2} \s
        \d{2}:\d{2}:\d{2}
    )
    \s
    \S+ # hostname
    \s
    (?P<line>.*)
    $
""", re.VERBOSE)

class SyslogRRD(rrd.RRD):
    def __init__(self, section, options):
        rrd.RRD.__init__(self, section, options)
        self._next_write_at = self.last_update
        self._first_write = True

    def _init_datasources(self, options):
        self._datasources = []
        for key, regexp_str in options.items():
            if key.startswith('ds_'):
                self._datasources.append({
                    'ds': key[3:],
                    'dst': 'ABSOLUTE',
                    'min': '0',
                    'max': 'U',
                    'regexp': re.compile(regexp_str),
                    'counter': 0,
                })
        if len(self._datasources) == 0:
            raise Exception('No data sources!')

    def process(self, timestamp, line, pos_updates, state):
        if timestamp <= self.last_update:
            return
        for datasource in self._datasources:
            if datasource['regexp'].search(line) is not None:
            #    logging.debug('%d: Found %s (line: %s)' %
            #        (timestamp, datasource['ds'], line))
                datasource['counter'] += 1
        minute = (timestamp//60) * 60
        if minute > self._next_write_at:
            self.update(minute, pos_updates, state)

    def update(self, minute, pos_updates, state):
        # Update all the minutes between in which nothing happened.
        # XXX: This should really go from the last timestamp that's still
        # around. I.e.,
        # - if we don't before a log is rotated into oblivion, leave unknowns
        # - otherwise fill in zeros between
        # which requires keeping additional state between runs, I think.
        if not self._first_write:
            while minute < self._next_write_at:
                rrd.RRD.update(self, minute,
                        ['0' for datasource in self._datasources])
                minute += 60
        # Update this minute.
        rrd.RRD.update(self, minute,
            [str(datasource['counter'])
             for datasource in self._datasources])

        # Prepare for the next update.
        for datasource in self._datasources:
            datasource['counter'] = 0
        self._next_write_at = minute + 60
        state.update(pos_updates)
        self._first_write = False

def main(args):
    optparser = optparse.OptionParser()
    optparser.add_option('-y', '--year', dest="starting_year",
                         type='int', default=time.localtime()[0])
    options, confs = optparser.parse_args(args)

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    confparser = ConfigParser.ConfigParser(
        # XXX: hostname should not be hardcoded...
        defaults={'hostname': 'calvin'}
    )
    confparser.read(confs)

    state = anydbm.open(confparser.get('DEFAULT', 'state'), 'c')

    rrds = {}
    for section in confparser.sections():
        rrds[section] = SyslogRRD(section, dict(confparser.items(section)))
    if len(rrds) == 0:
        raise Exception('No RRDs found in configuration!')

    logfiles = confparser.get('DEFAULT', 'inputs').split(' ')
    if len(logfiles) == 0:
        raise Exception('No input files!')

    last_timestamp = None
    year = options.starting_year
    have_warned_future = False
    pos_updates = {}
    seen_inodes = {}

    for logfile in logfiles:
        # If there are both compressed and uncompressed versions, compression
        # is currently in progress or failed. We want the uncompressed.
        fileclass = file
        try:
            stat = os.stat(logfile)
        except OSError, e:
            if e.errno == errno.ENOENT:
                # Try compressed.
                logfile = logfile + '.gz'
                fileclass = gzip.GzipFile
                try:
                    stat = os.stat(logfile)
                except OSError, e:
                    if e.errno == errno.ENOENT:
                        logging.info('Logfile <%s> does not exist' % logfile)
                        continue
                    else:
                        raise
            else:
                raise

        # Check where we are already.
        seen_inodes[str(stat.st_ino)] = True
        current_position = int(state.get(str(stat.st_ino), '0'))

        # See if we're done.
        #
        # XXX: For gzip files (where our current position is
        # in terms of the uncompressed stream), assume that if we've read
        # anything we've read it all. This isn't quite right - if we're
        # aborted in the middle, the next run assumes everything's okay.
        # Need to think about the proper way to handle this.
        if (fileclass == gzip.GzipFile and current_position > 0) \
            or current_position == stat.st_size:
            logging.debug('Finished with <%s> (len=%d)'
                          % (logfile, current_position))
            continue

        # Read the file.
        open_file = fileclass(logfile, 'r')
        logging.debug('Reading %s (inode %d), starting at position %d'
                      % (logfile, stat.st_ino, current_position))
        if fileclass == file:
            open_file.seek(current_position, 0)
        for line in open_file:
            current_position += len(line)
            match = syslog_re.match(line)
            if not match:
                raise Exception('Unparsable line <%s>' % line)
            nulls = len(match.group('nulls'))
            if nulls > 0:
                logging.warning('Skipped %d nulls at position %d'
                                % (nulls, current_position))
            try:
                timebits = list(time.strptime(
                        match.group('date'), '%b %d %H:%M:%S'))

                # Go through convoluted logic to guess year, since it's not
                # written in the entry.
                timebits[0] = year
                timestamp = time.mktime(timebits)
                now = time.time()
                if timestamp > now + 60*24*30:
                    logging.error(
                        'Log entry %d seconds in future. Wrong starting year!'
                        % (now - timestamp))
                    sys.exit(1)
                elif timestamp > now and not have_warned_future:
                    logging.warn('Log entry in future. (Right starting year?)')
                    have_warned_future = True
                elif last_timestamp is not None \
                     and timestamp < last_timestamp - 60*24*365/2:
                    logging.info(
                        'Apparently reached new year (%d-second diff)',
                        last_timestamp - timestamp)
                    year += 1
                    timebits[0] = year
                    timestamp = time.mktime(timebits)
                if last_timestamp is not None \
                    and timestamp < last_timestamp - 60:
                    logging.info('Major time correction (%d-second diff)',
                                 last_timestamp - timestamp)
                    timestamp = last_timestamp
                if timestamp > time.time():
                    logging.warn('After year jump, time %d in future!'
                                 % timestamp)
                last_timestamp = timestamp

            except:
                logging.error('Error while parsing date %r / sy=%r y=%r'
                              % (match.group('date'),
                                 options.starting_year,
                                 year))
                raise
            for rrd in rrds.values():
                rrd.process(timestamp, line, pos_updates, state)

            # XXX: need to either only write the positions after an update
            # minute or to keep the current-minute state between runs.
            pos_updates[str(stat.st_ino)] = str(current_position)

    # Since inode numbers get reused, we need to dump any we haven't seen
    # this time around.
    #
    # XXX: This still isn't right - the same number could go from used for one
    # file to used for a different one between two runs - but it's closer.
    for inode in state:
        if inode not in seen_inodes:
            del state[inode]

main(sys.argv[1:])

# TODO: Add tests for:
# - Parsing "Jan  1 00:01:37"
# - Starting for the first time after New Year's and getting correct year
#   on unprocessed data from last year.
# - Fall Back / Daylight Savings.
# - Saving position when last record in file doesn't start a new minute.
# - Time corrections.
# - inode reuse (currently wrong!)
# - cases around log rotation with compression.
# - update failure - state shouldn't advance beyond it
# - multiple runs within a single minute
