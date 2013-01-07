#!/usr/bin/env python
"""Date helper stuff.

Just basic parsing that should be built into Python but isn't.
"""

import datetime
import re

# XXX: This regexp is a little too permissive - the optional separators should
# be all or none. We allow mixed.
# (Also not sure if the [\sT] is optional at all.)
iso8601_regex = re.compile(r"""
    ^
    (?P<year> \d{4} ) -?
    (?P<month> \d{2} ) -?
    (?P<day> \d{2} ) [ \s T ]?
    (?P<hour> \d{2} ) :?
    (?P<minute> \d{2} ) :?
    (?P<second> \d{2} (?: \. \d+ )? )
    $
""", re.VERBOSE)

def parse_iso8601_datetime(str):
    """Parses an ISO-8601 datetime.

    >>> parse_iso8601_datetime('1982-04-26 05:00:00')
    datetime.datetime(1982, 4, 26, 5, 0)

    >>> parse_iso8601_datetime('1982-04-26T05:00:00')
    datetime.datetime(1982, 4, 26, 5, 0)

    >>> parse_iso8601_datetime('1982-04-26T05:00:00.000000')
    datetime.datetime(1982, 4, 26, 5, 0)

    >>> parse_iso8601_datetime('invalid')
    Traceback (most recent call last):
        ...
    Exception: Illegal ISO-8601 datetime <invalid>

    >>> now = datetime.datetime.now()
    >>> parsed_now = parse_iso8601_datetime(str(now))
    >>> abs(now - parsed_now) <= datetime.datetime.resolution
    True
    """
    match = iso8601_regex.match(str)
    if match is None:
        raise Exception('Illegal ISO-8601 datetime <%s>' % str)
    sec_precise = float(match.group('second'))
    second = int(sec_precise)
    microsecond = int((sec_precise - second) * 1e6)
    return datetime.datetime(year=int(match.group('year')),
                             month=int(match.group('month')),
                             day=int(match.group('day')),
                             hour=int(match.group('hour')),
                             minute=int(match.group('minute')),
                             second=second,
                             microsecond=microsecond)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
