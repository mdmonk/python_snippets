#!/usr/bin/env python
"""rrdtool stuff."""

import subprocess
import os
import logging

class RRD(object):
    def __init__(self, name, options):
        # Sanity checks.
        directory = options['directory']
        if not name.endswith('.rrd'):
            raise Exception('Output file <%s> should end with .rrd' % name)
        if not os.path.exists(directory):
            raise Exception('Output directory <%s> does not exist' % directory)
        self.filename = os.path.join(directory, name)

        self._init_datasources(options)

        if not os.path.exists(self.filename):
            self._create(options)

        self._get_last_update()

    def _create(self, options):
        logging.info('Creating RRD %s' % self.filename)
        args = \
            ['/usr/bin/rrdtool', 'create', self.filename,
             '--start=%s' % options['start']] \
            + ['DS:%s:%s:%s:%s:%s' %
               (value['ds'], value['dst'], options['heartbeat'],
                value['min'], value['max'])
               for value in self._datasources] \
            + options['rras'].split(' ')
        retcode = subprocess.call(args)
        if retcode != 0:
            raise Exception('<%s> exited with code %d' % (' '.join(args), retcode))

    def _get_last_update(self):
        rrdtool = subprocess.Popen(['/usr/bin/rrdtool', 'last', self.filename],
                                   stdout=subprocess.PIPE)
        self.last_update = int(rrdtool.stdout.read().rstrip())
        retcode = rrdtool.wait()
        if retcode != 0:
            raise Exception('rrdlast exited with code %d' % retcode)
        logging.debug('Last update on RRD <%s> was %d'
                      % (self.filename, self.last_update))

    def update(self, timestamp, values):
        """Updates the RRD.
        @param values list of values.
        """
        args = [
            '/usr/bin/rrdupdate',
            self.filename,
            ('%d:' % timestamp) + ':'.join(values),
        ]
        logging.debug('Executing: <%s>' % ' '.join(args))
        retcode = subprocess.call(args)
        if retcode != 0:
            raise Exception('rrdupdate exited with code %d' % retcode)
