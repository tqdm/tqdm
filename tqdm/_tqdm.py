"""
Customisable progressbar decorator for iterators.
Includes a default (x)range iterator printing to stderr.

Usage:
  from tqdm import trange[, tqdm]
  for i in trange(10):
    ...
"""
from __future__ import division, absolute_import
import sys
import time


__author__ = {"github.com/" : ["noamraph", "JackMc", "arkottke", "obiwanus",
        "fordhurley", "kmike", "hadim", "casperdcl"]}
__all__ = ['tqdm', 'trange', 'format_interval', 'format_meter']


def format_interval(t):
    mins, s = divmod(int(t), 60)
    h, m = divmod(mins, 60)
    if h:
        return '{0:d}:{1:02d}:{2:02d}'.format(h, m, s)
    else:
        return '{0:02d}:{1:02d}'.format(m, s)


def format_meter(n, total, elapsed):
    # n - number of finished iterations
    # total - total number of iterations, or None
    # elapsed - number of seconds passed since start
    if total and n > total:
        total = None

    elapsed_str = format_interval(elapsed)
    rate = '{0:5.2f}'.format(n / elapsed) if elapsed else '?'

    if total:
        frac = float(n) / total

        N_BARS = 10
        bar_length = int(frac*N_BARS)
        bar = '#'*bar_length + '-'*(N_BARS-bar_length)

        left_str = format_interval(elapsed * (total-n) / n) if n else '?'

        return '|{0}| {1}/{2} {3:3.0f}% [elapsed: {4} left: {5}, {6} iters/sec]'.format(
            bar, n, total, frac * 100, elapsed_str, left_str, rate)

    else:
        return '{0:d} [elapsed: {1}, {2} iters/sec]'.format(n, elapsed_str, rate)


class StatusPrinter(object):
    def __init__(self, file):
        self.file = file
        self.last_printed_len = 0

    def print_status(self, s):
        self.file.write('\r'+s+' '*max(self.last_printed_len-len(s), 0))
        self.file.flush()
        self.last_printed_len = len(s)


def tqdm(iterable, desc=None, total=None, leave=False, file=sys.stderr,
         mininterval=0.5, miniters=1):
    """
    Decorate an iterable object, returning an iterator which acts exactly
    like the orignal iterable, but prints a dynamically updating
    progressbar.
    
    Parameters
    ----------
    iterable  : iterable
        Iterable to decorate with a progressbar.
    desc  : str, optional
        Prefix for the progressbar.
    total  : int, optional
        The number of expected iterations. If not given, len(iterable) is
        used if possible. As a last resort, only basic progress statistics
        are displayed.
    file  : `io.TextIOWrapper` or `io.StringIO`, optional
        Specifies where to output the progress messages.
    leave  : bool, optional
        if unset, removes all traces of the progressbar upon termination of
        iteration [default: False].
    mininterval  : float, optional
        Minimum progress update interval, in seconds [default: 0.5].
    miniters  : int, optional
        Minimum progress update interval, in iterations [default: 1].
    
    Returns
    -------
    out  : decorated iterator.
    """
    if total is None:
        try:
            total = len(iterable)
        except (TypeError, AttributeError):
            total = None

    prefix = desc+': ' if desc else ''

    sp = StatusPrinter(file)
    sp.print_status(prefix + format_meter(0, total, 0))

    start_t = last_print_t = time.time()
    last_print_n = 0
    n = 0
    for obj in iterable:
        yield obj
        # Now the object was created and processed, so we can print the meter.
        n += 1
        if n - last_print_n >= miniters:
            # We check the counter first, to reduce the overhead of time.time()
            cur_t = time.time()
            if cur_t - last_print_t >= mininterval:
                sp.print_status(prefix + format_meter(n, total, cur_t-start_t))
                last_print_n = n
                last_print_t = cur_t

    if not leave:
        sp.print_status('')
        sys.stdout.write('\r')
    else:
        if last_print_n < n:
            cur_t = time.time()
            sp.print_status(prefix + format_meter(n, total, cur_t-start_t))
        file.write('\n')


def trange(*args, **kwargs):
    """
    A shortcut for tqdm(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    try:
        f = xrange
    except NameError:
        f = range

    return tqdm(f(*args), **kwargs)
