#!/usr/bin/env python
"""Creates RRDtool graphs from Linux sar output."""

__version__ = '$Revision$'

import ConfigParser
import subprocess
import os
import glob
import logging
import sys
import rrd

class SarRRD(rrd.RRD):
    def _init_datasources(self, options):
        """Load data sources from configuration."""
        self._datasources = []
        for key, value in options.items():
            if key.startswith('ds_'):
                value = value.split(':')
                dst, device, field = value[0:3]
                min = ''
                max = ''
                if len(value) > 3:
                    min = value[3]
                if len(value) > 4:
                    max = value[4]
                self._datasources.append({
                    'ds': key[3:],
                    'dst': dst,
                    'device': device,
                    'field': field,
                    'min': min,
                    'max': max,
                })
        if len(self._datasources) == 0:
            raise Exception('No data sources!')

    def update(self, timestamp, values):
        """Updates the RRD.
        @param values dict (device,field)->value, some of
                      which may apply to this RRD.
        """
        if timestamp <= self.last_update:
            logging.debug('Skipping update to %s (too old)' % self.filename)
            return
        rrd.RRD.update(self, timestamp,
            [values.get((datasource['device'], datasource['field']), 'U')
             for datasource in self._datasources])

def main(conf_files):
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    # Parse configuration.
    parser = ConfigParser.ConfigParser()
    parser.read(conf_files)

    # Create RRD objects.
    rrds = {}
    for section in parser.sections():
        rrds[section] = SarRRD(section, dict(parser.items(section)))
    if len(rrds) == 0:
        raise Exception('No RRDs found in configuration!')

    # Get list of input files.
    # At least for now, we'll assume all rrds use the same sarfiles.
    sarfile_glob = parser.get('DEFAULT', 'input')
    sarfiles = glob.glob(sarfile_glob)
    if len(sarfiles) == 0:
        raise Exception('No input files! glob <%s> has no matches.' % sarfile_glob)
    logging.debug(('sarfile glob <%s> matches ' % sarfile_glob)
                  + ', '.join(['<%s>' % i for i in sarfiles]))

    # Go through them in order, as required by rrdupdate.
    # We do this by mtime. We'd do it this way even if we only handled
    # /var/log/sa/sa[0-9][0-9] since during the beginning of the month
    # sa31 will be older than sa01.
    def modification_cmp(x, y):
        return os.stat(x).st_mtime - os.stat(y).st_mtime
    sarfiles.sort(modification_cmp)

    # If a data point is too old for all of our rrds, we're not interested.
    min_last_update = min([rrd.last_update for rrd in rrds.values()])
    logging.debug('Min last update is %d' % min_last_update)

    # We assume here that the intervals represented by each sarfile do not overlap.
    # So if we go through each sarfile according to its last modification time
    # and only sort the timestamps within each file, we'll get an increasing sequence
    # of timestamps.
    for sarfile in sarfiles:
        mtime = os.stat(sarfile).st_mtime
        if mtime <= min_last_update:
            logging.debug('Skipping %s due to age (mtime=%d)' % (sarfile, mtime))
            continue

        logging.debug('Processing %s (mtime=%d)' % (sarfile, mtime))
        sar = subprocess.Popen(['/usr/bin/sar', '-A', '-h', '-f', sarfile],
                               stdout=subprocess.PIPE)

        # "sar -A" doesn't give values in order, so we put them in a dict by timestamp,
        # sort them, and then add them.
        values = {}
        for line in sar.stdout:
            line = line.rstrip().split('\t')
            if len(line) == 4:
                assert line[3] == 'LINUX-RESTART'
            else:
                hostname, interval, timestamp, device, field, value = line
                timestamp = int(timestamp)
                mydict = values.get(timestamp, {})
                mydict[(device, field)] = value
                values[timestamp] = mydict
        timestamps = values.keys()
        timestamps.sort()
        for timestamp in timestamps:
            logging.debug('Handling timestamp %d' % timestamp)
            for rrd in rrds.values():
                rrd.update(timestamp, values[timestamp])

main(sys.argv[1:])
