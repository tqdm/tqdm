"""
Customisable progressbar decorator for iterators.
Includes a default (x)range iterator printing to stderr.

Usage:
  from tqdm import trange[, tqdm]
  for i in trange(10):
    ...
"""
from __future__ import division, absolute_import
from _utils import _is_utf, _supports_unicode, _environ_cols
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


def format_meter(n, total, elapsed, ncols=None, prefix='', ascii=False):
    """
    Parameter parsing and formatting for output

    Parameters
    ----------
    n  : int
        Number of finished iterations
    total  : int
        The number of expected iterations. If None, only basic progress
        statistics are displayed.
    elapsed  : float
        Number of seconds passed since start
    ncols  : int, optional
        The width of the entire output message. If sepcified, dynamically
        resizes the progress meter [default: None]. The fallback meter
        width is 10.
    prefix  : str, optional
        Prefix message (included in total width)
    ascii  : bool, optional
        If not set, use unicode (smooth blocks) to fill the meter
        [default: False]. The fallback is to use ASCII characters (1-9 #).

    Returns
    -------
    out  : Formatted meter and stats, ready to display.
    """
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

        if ascii:
            bar_length, frac_bar_length = divmod(int(frac * N_BARS * 10), 10)

            bar = '#'*bar_length
            frac_bar = chr(48 + frac_bar_length) if frac_bar_length else ' '

        else:
            bar_length, frac_bar_length = divmod(int(frac * N_BARS * 8), 8)

            try:    # pragma: no cover
                unich = unichr
            except NameError:    # pragma: no cover
                unich = chr

            bar = unich(0x2588)*bar_length
            frac_bar = unich(0x2590 - frac_bar_length) \
                if frac_bar_length else ' '

        if bar_length < N_BARS:
            return l_bar + bar + frac_bar + \
                ' '*max(N_BARS - bar_length - 1, 0) + r_bar
        else:
            return l_bar + bar + r_bar

    else:
        return '{0:d} [{1}, {2} it/s]'.format(n, elapsed_str, rate)


class StatusPrinter(object):
    def __init__(self, file):
        self.file = file
        self.last_printed_len = 0

    def print_status(self, s):
        len_s = len(s)
        self.file.write('\r'+s+' '*max(self.last_printed_len - len_s, 0))
        self.file.flush()
        self.last_printed_len = len_s


def tqdm(iterable, desc=None, total=None, leave=False, file=sys.stderr,
         ncols=None, mininterval=0.1, miniters=None,
         ascii=None, disable=False):
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
        Uses file.write(str) and file.flush() methods.
    leave  : bool, optional
        if unset, removes all traces of the progressbar upon termination of
        iteration [default: False].
    ncols  : int, optional
        The width of the entire output message. If sepcified, dynamically
        resizes the progress meter [default: None]. The fallback meter
        width is 10.
    mininterval  : float, optional
        Minimum progress update interval, in seconds [default: 0.1].
    miniters  : int, optional
        Minimum progress update interval, in iterations [default: None].
    ascii  : bool, optional
        If not set, use unicode (smooth blocks) to fill the meter
        [default: False]. The fallback is to use ASCII characters (1-9 #).
    disable : bool
        Disable the progress bar if True [default: False].

    Returns
    -------
    out  : decorated iterator.
    """

    if disable:
        for obj in iterable:
            yield obj
        return

    if total is None:
        try:
            total = len(iterable)
        except (TypeError, AttributeError):
            total = None

    if (ncols is None) and (file in (sys.stderr, sys.stdout)):
        ncols = _environ_cols()

    if miniters is None:
        miniters = 0
        dynamic_miniters = True
    else:
        dynamic_miniters = False

    if ascii is None:
        ascii = not _supports_unicode(file)

    prefix = desc+': ' if desc else ''

    sp = StatusPrinter(file)
    sp.print_status(format_meter(0, total, 0, ncols, prefix, ascii))

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
                    n, total, cur_t-start_t, ncols, prefix, ascii))
                if dynamic_miniters:
                    miniters = max(miniters, n - last_print_n + 1)
                last_print_n = n
                last_print_t = cur_t

    if leave:
        if last_print_n < n:
            cur_t = time.time()
            sp.print_status(format_meter(
                n, total, cur_t-start_t, ncols, prefix, ascii))
        file.write('\n')
    else:
        sp.print_status('')
        sys.stdout.write('\r')


def trange(*args, **kwargs):
    """
    A shortcut for tqdm(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    try:    # pragma: no cover
        f = xrange
    except NameError:    # pragma: no cover
        f = range

    return tqdm(f(*args), **kwargs)
