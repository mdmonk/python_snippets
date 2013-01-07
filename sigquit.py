#!/usr/bin/env python
"""A backtrace SIGQUIT handler like Java's.

Single-threaded, at least for now.
"""

__version__ = '$Revision$'

import signal
import traceback

def backtrace_handler(signo, frame):
    traceback.print_stack(frame)

def install():
    signal.signal(signal.SIGQUIT, backtrace_handler)

if __name__ == '__main__':
    # Quick test.
    import time
    install()
    print 'Ready'
    while True:
        time.sleep(1)
