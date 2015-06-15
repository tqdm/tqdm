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


__author__ = {"github.com/": ["noamraph", "JackMc", "arkottke", "obiwanus",
                              "fordhurley", "kmike", "hadim", "casperdcl"]}
__all__ = ['tqdm', 'trange', 'format_interval', 'format_meter']


def format_interval(t):
    mins, s = divmod(int(t), 60)
    h, m = divmod(mins, 60)
    if h:
        return '{0:d}:{1:02d}:{2:02d}'.format(h, m, s)
    else:
        return '{0:02d}:{1:02d}'.format(m, s)


def format_meter(n, total, elapsed, ncols=None, prefix=''):
    # n - number of finished iterations
    # total - total number of iterations, or None
    # elapsed - number of seconds passed since start
    # ncols - the output width in chars. If specified, dynamically resizes bar.
    #     [default bar width: 10].
    # prefix - prepend message (included in total width)
    if total and n > total:
        total = None

    elapsed_str = format_interval(elapsed)
    rate = '{0:5.2f}'.format(n / elapsed) if elapsed else '?'

    if total:
        frac = float(n) / total

        left_str = format_interval(elapsed * (total-n) / n) if n else '?'

        l_bar = '{1}{0:.0f}%|'.format(frac * 100, prefix) if prefix else \
                '{0:3.0f}%|'.format(frac * 100)
        r_bar = '| {0}/{1} [{2}<{3}, {4} it/s]'.format(
                n, total, elapsed_str, left_str, rate)

        N_BARS = max(1, ncols - len(l_bar) - len(r_bar)) if ncols else 10
        bar_length = int(frac * N_BARS)
        frac_bar_length = int((frac * N_BARS * 8) % 8)

        try:
            unich = unichr
        except:
            unich = chr

        bar = unich(0x2588)*bar_length
        frac_bar = unich(0x2590 - frac_bar_length) if frac_bar_length else ' '

        if bar_length < N_BARS:
            bar = bar + frac_bar + ' '*max(N_BARS - bar_length - 1, 0)

        return l_bar + bar + r_bar

    else:
        return '{0:d} [{1}, {2} it/s]'.format(n, elapsed_str, rate)


class StatusPrinter(object):
    def __init__(self, file):
        self.file = file
        self.last_printed_len = 0

    def print_status(self, s):
        self.file.write('\r'+s+' '*max(self.last_printed_len-len(s), 0))
        self.file.flush()
        self.last_printed_len = len(s)


def tqdm(iterable, desc=None, total=None, leave=False, file=sys.stderr,
         ncols=None, mininterval=0.1, miniters=1):
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
    ncols  : int, optional
        The width of the entire output message. If sepcified, dynamically
        resizes the progress meter [default: None]. The fallback meter
        width is 10.
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
    sp.print_status(format_meter(0, total, 0, ncols, prefix))

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
                sp.print_status(format_meter(
                    n, total, cur_t-start_t, ncols, prefix))
                last_print_n = n
                last_print_t = cur_t

    if not leave:
        sp.print_status('')
        sys.stdout.write('\r')
    else:
        if last_print_n < n:
            cur_t = time.time()
            sp.print_status(format_meter(
                n, total, cur_t-start_t, ncols, prefix))
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
