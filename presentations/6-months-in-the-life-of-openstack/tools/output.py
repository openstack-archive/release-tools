import contextlib
import functools
import io
import re
import sys

import cog


def capture(f):
    @functools.wraps(f)
    def wrap(*a, **kw):
        sys.stderr.write('\n{}({}, {})\n'.format(f.__name__, a, kw))
        buf = io.StringIO()
        sys.stdout = buf
        f(*a, **kw)
        sys.stdout = sys.__stdout__
        results = buf.getvalue()
        sys.stderr.write(results)
        sys.stderr.write('\n')
        cog.out(results)
        return results
    return wrap
