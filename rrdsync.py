#!/usr/bin/env python24
"""Ghetto script to update a bunch of rrds across the network.
It has two advantages over just using rsync:

* it uses a lot less bandwidth. (rsync has been using a megabyte lately for
  the one-hour updates).
* it can handle architectural differences between the RRD files.

It currently assumes that all files have been started already, either with
rsync or 'rrdtool dump' + 'rrdtool restore'.
"""

import subprocess
import sys

def client_main(args):
    server = subprocess.Popen(
        ['ssh', 'calvin.vpn.slamb.org', '/home/slamb/bin/rrdsync', '--server'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE
    )

    # write first
    for f in args[1:]:
        rrdtool = subprocess.Popen(['/usr/bin/rrdtool', 'last', f],
                                   stdout=subprocess.PIPE)
        last_update = int(rrdtool.stdout.read().rstrip())
        retcode = rrdtool.wait()
        if retcode != 0:
            raise Exception('rrdlast exited with code %d' % retcode)
        server.stdin.write('%d %s\n' % (last_update, f))
    server.stdin.close()

    # now read
    while True:
        f = server.stdout.readline()
        if f == '':
            break
        f = f[:-1]
        #print 'handling file %s' % f
        while True:
            inner_line = server.stdout.readline()
            if inner_line == '\n':
                break
            elif inner_line == '':
                raise Exception('unexpected EOF!')
            #print 'rrdupdate %s %s' % (f, inner_line[:-1])
            rrdupdate = subprocess.Popen(
                ['/usr/bin/rrdupdate', f, inner_line[:-1]]
            )
            retcode = rrdupdate.wait()
            if retcode != 0:
                raise Exception('rrdupdate exited with code %d' % retcode)

    retcode = server.wait()
    if retcode != 0:
        raise Exception('server exited with code %d' % retcode)
    return 0

def server_main():
    # Read first, so we don't have to deal with buffering complexity.
    files = []
    for line in sys.stdin:
        last_update, f = line[:-1].split(' ', 2)
        files.append((last_update, f))

    # Now send the updates.
    for last_update, f in files:
        sys.stdout.write('%s\n' % f)
        fetch = subprocess.Popen(['/usr/bin/rrdtool', 'fetch',
                                 f, 'AVERAGE', '--start', last_update],
                                 stdout=subprocess.PIPE)
        fetch.stdout.readline() # header
        assert fetch.stdout.readline() == '\n'
        for line in fetch.stdout.readlines():
            data = line[:-1].split()
            assert data[0][-1] == ':'
            timestamp = data[0][:-1]
            if int(timestamp) <= int(last_update):
                # They want values _after_ this one.
                continue
            for datum in data[1:]:
                if datum != 'nan':
                    break
            else:
                continue
            sys.stdout.write(data[0] + ':'.join(data[1:]) + '\n')
        retcode = fetch.wait()
        if retcode != 0:
            raise Exception('rrdfetch exited with code %d' % retcode)
        sys.stdout.write('\n')

    return 0

def main(args):
    if len(args) == 2 and args[1] == '--server':
        return server_main()
    else:
        return client_main(args)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
