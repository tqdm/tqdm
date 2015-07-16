"""
Customisable progressbar decorator for iterators.
Includes a default (x)range iterator printing to stderr.

Usage:
  from tqdm import trange[, tqdm]
  for i in trange(10):
    ...
"""
# future division is important to divide integers and get as
# a result precise floating numbers (instead of truncated int)
from __future__ import division, absolute_import
# import compatibility functions and utilities
from ._utils import _supports_unicode, _environ_cols, _range, _unich
import sys
from time import time


__author__ = {"github.com/": ["noamraph", "JackMc", "arkottke", "obiwanus",
                              "fordhurley", "kmike", "hadim", "casperdcl"]}
__all__ = ['tqdm', 'trange', 'format_interval', 'format_meter']


def format_sizeof(num, suffix=''):
    """
    Formats a number (greater than unity) with SI Order of Magnitude prefixes.

    Parameters
    ----------
    num  : float
        Number ( >= 1) to format.
    suffix  : str, optional
        Post-postfix.

    Returns
    -------
    out  : str
        Number with Order of Magnitude SI unit postfix.
    """
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1000.0:
            if abs(num) < 100.0:
                if abs(num) < 10.0:
                    return '{0:1.2f}'.format(num) + unit + suffix
                return '{0:2.1f}'.format(num) + unit + suffix
            return '{0:3.0f}'.format(num) + unit + suffix
        num /= 1000.0
    return '{0:3.1f}Y'.format(num) + suffix


def format_interval(t):
    """
    Formats a number of seconds as a clock time, [H:]MM:SS

    Parameters
    ----------
    t  : int
        Number of seconds
    Returns
    -------
    out  : str
        [H:]MM:SS
    """
    mins, s = divmod(int(t), 60)
    h, m = divmod(mins, 60)
    if h:
        return '{0:d}:{1:02d}:{2:02d}'.format(h, m, s)
    else:
        return '{0:02d}:{1:02d}'.format(m, s)


def format_meter(n, total, elapsed, ncols=None, prefix='', ascii=False,
                 unit='it', unit_scale=False):
    """
    Return a string-based progress bar given some parameters

    Parameters
    ----------
    n  : int
        Number of finished iterations.
    total  : int
        The expected total number of iterations. If meaningless (), only basic
        progress statistics are displayed (no ETA).
    elapsed  : float
        Number of seconds passed since start.
    ncols  : int, optional
        The width of the entire output message. If sepcified, dynamically
        resizes the progress meter [default: None]. The fallback meter
        width is 10.
    prefix  : str, optional
        Prefix message (included in total width).
    ascii  : bool, optional
        If not set, use unicode (smooth blocks) to fill the meter
        [default: False]. The fallback is to use ASCII characters (1-9 #).
    unit  : str, optional
        The iteration unit [default: 'it'].
    unit_scale  : bool, optional
        If set, the number of iterations will printed with an appropriate
        SI metric prefix (K = 10^3, M = 10^6, etc.) [default: False].

    Returns
    -------
    out  : Formatted meter and stats, ready to display.
    """

    # in case the total is wrong (n is above the total), then
    # we switch to the mode without showing the total prediction
    # (since ETA would be wrong anyway)
    if total and n > total:
        total = None

    elapsed_str = format_interval(elapsed)

    rate_fmt = ((format_sizeof(n / elapsed) if unit_scale else
                 '{0:5.2f}'.format(n / elapsed)) if elapsed else
                '?') \
               + unit + '/s'

    if unit_scale:
        n_fmt = format_sizeof(n)
        total_fmt = format_sizeof(total) if total else None
    else:
        n_fmt = str(n)
        total_fmt = str(total)

    if total:
        frac = n / total
        percentage = frac * 100

        remaining_str = format_interval(elapsed * (total-n) / n) if n else '?'

        l_bar = (prefix if prefix else '') + '{0:3.0f}%|'.format(percentage)
        r_bar = '| {0}/{1} [{2}<{3}, {4}]'.format(
                n_fmt, total_fmt, elapsed_str, remaining_str, rate_fmt)

        if ncols == 0:
            bar = ''
        else:
            N_BARS = max(1, ncols - len(l_bar) - len(r_bar)) if ncols \
                         else 10

            if ascii:
                bar_length, frac_bar_length = divmod(
                    int(frac * N_BARS * 10), 10)

                bar = '#'*bar_length
                frac_bar = chr(48 + frac_bar_length) if frac_bar_length \
                    else ' '

            else:
                bar_length, frac_bar_length = divmod(int(frac * N_BARS * 8), 8)

                bar = _unich(0x2588)*bar_length
                frac_bar = _unich(0x2590 - frac_bar_length) \
                    if frac_bar_length else ' '

        if bar_length < N_BARS:
            full_bar = bar + frac_bar + \
                ' ' * max(N_BARS - bar_length - 1, 0)  # bar end padding
        else:
            full_bar = bar + \
                ' ' * max(N_BARS - bar_length, 0)  # bar end padding

        return l_bar + full_bar + r_bar

    else:  # no progressbar nor ETA, just progress statistics
        return '{0}{1} [{2}, {3}]'.format(
            n_fmt, unit, elapsed_str, rate_fmt)


class StatusPrinter(object):
    """
    Manage the printing and in-place updating of a line of characters.
    Note that if the string is longer than a line, then in-place updating
    may not work (it will print a new line at each refresh).
    """
    def __init__(self, file):
        self.file = file
        self.last_printed_len = 0

    def print_status(self, s):
        len_s = len(s)
        self.file.write('\r' + s + ' '*max(self.last_printed_len - len_s, 0))
        self.file.flush()
        self.last_printed_len = len_s


class tqdm(object):
    """
    Decorate an iterable object, returning an iterator which acts exactly
    like the orignal iterable, but prints a dynamically updating
    progressbar every time a value is requested.

    Parameters
    ----------
    iterable  : iterable, optional
        Iterable to decorate with a progressbar. You can leave
        it to None if you want to manually manage the updates.
    desc  : str, optional
        Prefix for the progressbar.
    total  : int, optional
        The number of expected iterations. If not given, len(iterable) is
        used if possible. As a last resort, only basic progress statistics
        are displayed (no ETA, no progressbar).
    file  : `io.TextIOWrapper` or `io.StringIO`, optional
        Specifies where to output the progress messages.
        Uses file.write(str) and file.flush() methods.
    leave  : bool, optional
        if unset, removes all traces of the progressbar upon termination of
        iteration [default: False].
    ncols  : int, optional
        The width of the entire output message. If specified, dynamically
        resizes the progress meter to stay within this bound [default: None].
        The fallback meter width is 10 for the progress bar + no limit for
        the iterations counter and statistics.
    mininterval  : float, optional
        Minimum progress update interval, in seconds [default: 0.1].
    miniters  : int, optional
        Minimum progress update interval, in iterations [default: None].
    unit  : str, optional
        String that will be used to define the unit of each iteration
        [default: 'it'].
    unit_scale  : bool, optional
        If set, the number of iterations will be reduced/scaled
        automatically and a metric prefix following the
        International System of Units standard will be added
        (kilo, mega, etc.). [default: False]
    ascii  : bool, optional
        If not set, use unicode (smooth blocks) to fill the meter
        [default: False]. The fallback is to use ASCII characters (1-9 #).
    disable : bool
        Disable the progress bar if True [default: False].

    Returns
    -------
    out  : decorated iterator.
    """

    def __init__(self, iterable=None, desc=None, total=None, leave=False,
                 file=sys.stderr, ncols=None, mininterval=0.1,
                 miniters=None, ascii=None, disable=False,
                 unit='it', unit_scale=False):

        # Preprocess the arguments
        if total is None and iterable is not None:
            try:
                total = len(iterable)
            except (TypeError, AttributeError):
                total = None

        if (ncols is None) and (file in (sys.stderr, sys.stdout)):
            ncols = _environ_cols(file)

        if miniters is None:
            miniters = 0
            dynamic_miniters = True
        else:
            dynamic_miniters = False

        if ascii is None:
            ascii = not _supports_unicode(file)

        # Store the arguments
        self.iterable = iterable
        self.total = total
        self.prefix = desc+': ' if desc else ''
        self.leave = leave
        self.file = file
        self.ncols = ncols
        self.mininterval = mininterval
        self.miniters = miniters
        self.dynamic_miniters = dynamic_miniters
        self.ascii = ascii
        self.unit = unit
        self.unit_scale = unit_scale
        self.disable = disable

        # Initialize the screen printer
        self.sp = StatusPrinter(self.file)
        if not disable:
            self.sp.print_status(format_meter(
                0, total, 0, ncols, self.prefix, ascii, unit, unit_scale))

        # Init the time/iterations counters
        self.start_t = self.last_print_t = time()
        self.last_print_n = 0
        self.n = 0

    def __len__(self):
        return self.iterable.__len__()

    def __iter__(self):
        ''' For backward-compatibility to use: for x in tqdm(iterable) '''

        # Inlining instance variables as locals (speed optimisation)
        iterable = self.iterable

        # if the bar is disabled, then just walk the iterable
        # (note that we keep this condition above the loop for performance,
        # so that we don't have to repeatedly check the condition inside
        # the loop)
        if self.disable:
            for obj in iterable:
                yield obj
        else:
            total = self.total
            prefix = self.prefix
            leave = self.leave
            file = self.file
            ncols = self.ncols
            mininterval = self.mininterval
            miniters = self.miniters
            dynamic_miniters = self.dynamic_miniters
            unit = self.unit
            unit_scale = self.unit_scale
            ascii = self.ascii
            sp = self.sp
            start_t = self.start_t
            last_print_t = self.last_print_t
            last_print_n = self.last_print_n
            n = self.n
            for obj in iterable:
                yield obj
                # UPDATE
                # Now that the iterable object was created and processed,
                # we can update and print the progress meter
                # Note: this is an optimization, we could call self.update(1)
                # but it would be way slower (because of method call)
                n += 1
                delta_it = n - last_print_n
                # check the counter first (avoid calls to time())
                if delta_it >= miniters:
                    cur_t = time()
                    if cur_t - last_print_t >= mininterval:
                        sp.print_status(format_meter(
                            n, total, cur_t-start_t, ncols,
                            prefix, ascii, unit, unit_scale))
                        if dynamic_miniters:
                            miniters = max(miniters, delta_it)
                        last_print_n = n
                        last_print_t = cur_t
            # CLOSE
            # Closing the progress bar
            if leave:
                if last_print_n < n:
                    cur_t = time()
                    sp.print_status(format_meter(
                        n, total, cur_t-start_t, ncols,
                        prefix, ascii, unit, unit_scale))
                file.write('\n')
            else:
                sp.print_status('')
                file.write('\r')

    def update(self, n=1):
        """
        Manually update the progress bar, useful for streams
        such as reading files.
        Eg, initialize tqdm(total=filesize), and then in the reading loop,
        use update(len(current_buffer)).

        Parameters
        ----------
        n  : int
            Increment to add to the internal counter of iterations.
        """
        if n < 1:
            n = 1
        self.n += n

        if self.disable:
            return

        delta_it = self.n - self.last_print_n
        if delta_it >= self.miniters:
            # We check the counter first, to reduce the overhead of time()
            cur_t = time()
            if cur_t - self.last_print_t >= self.mininterval:
                self.sp.print_status(format_meter(
                    self.n, self.total, cur_t-self.start_t, self.ncols,
                    self.prefix, self.ascii, self.unit, self.unit_scale))
                if self.dynamic_miniters:
                    self.miniters = max(self.miniters, delta_it)
                self.last_print_n = self.n
                self.last_print_t = cur_t

    def close(self):
        """
        Call this method to force print the last progress bar update
        based on the latest n value
        """
        if self.leave:
            if self.last_print_n < self.n:
                cur_t = time()
                self.sp.print_status(format_meter(
                    self.n, self.total, cur_t-self.start_t, self.ncols,
                    self.prefix, self.ascii, self.unit, self.unit_scale))
            self.file.write('\n')
        else:
            self.sp.print_status('')
            self.file.write('\r')


def trange(*args, **kwargs):
    """
    A shortcut for tqdm(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    return tqdm(_range(*args), **kwargs)
