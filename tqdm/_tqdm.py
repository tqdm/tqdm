"""
Customisable progressbar decorator for iterators.
Includes a default (x)range iterator printing to stderr.

Usage:
  >>> from tqdm import trange[, tqdm]
  >>> for i in trange(10): #same as: for i in tqdm(xrange(10))
  ...     ...
"""
# future division is important to divide integers and get as
# a result precise floating numbers (instead of truncated int)
from __future__ import division, absolute_import
# import compatibility functions and utilities
from ._utils import _supports_unicode, _environ_cols_wrapper, _range, _unich, \
    _term_move_up
import sys
from time import time


__author__ = {"github.com/": ["noamraph", "obiwanus", "kmike", "hadim",
                              "casperdcl", "lrq3000"]}
__all__ = ['tqdm', 'trange', 'format_interval', 'format_meter']


def format_sizeof(num, suffix=''):
    """
    Formats a number (greater than unity) with SI Order of Magnitude prefixes.

    Parameters
    ----------
    num  : float
        Number ( >= 1) to format.
    suffix  : str, optional
        Post-postfix [default: ''].

    Returns
    -------
    out  : str
        Number with Order of Magnitude SI unit postfix.
    """
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 999.95:
            if abs(num) < 99.95:
                if abs(num) < 9.995:
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
        Number of seconds.
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
                 unit='it', unit_scale=False, rate=None):
    """
    Return a string-based progress bar given some parameters

    Parameters
    ----------
    n  : int
        Number of finished iterations.
    total  : int
        The expected total number of iterations. If meaningless (), only
        basic progress statistics are displayed (no ETA).
    elapsed  : float
        Number of seconds passed since start.
    ncols  : int, optional
        The width of the entire output message. If specified, dynamically
        resizes the progress meter to stay within this bound
        [default: None]. The fallback meter width is 10 for the progress bar
        + no limit for the iterations counter and statistics. If 0, will not
        print any meter (only stats).
    prefix  : str, optional
        Prefix message (included in total width) [default: ''].
    ascii  : bool, optional
        If not set, use unicode (smooth blocks) to fill the meter
        [default: False]. The fallback is to use ASCII characters (1-9 #).
    unit  : str, optional
        The iteration unit [default: 'it'].
    unit_scale  : bool, optional
        If set, the number of iterations will printed with an appropriate
        SI metric prefix (K = 10^3, M = 10^6, etc.) [default: False].
    rate  : float, optional
        Manual override for iteration rate.
        If [default: None], uses n/elapsed.

    Returns
    -------
    out  : Formatted meter and stats, ready to display.
    """

    # sanity check: total
    if total and n > total:
        total = None

    elapsed_str = format_interval(elapsed)

    # if unspecified, attempt to use rate = average speed
    # (we allow manual override since predicting time is an arcane art)
    if rate is None and elapsed:
        rate = n / elapsed
    rate_fmt = ((format_sizeof(rate) if unit_scale else
                 '{0:5.2f}'.format(rate)) if elapsed else
                '?') \
        + unit + '/s'

    if unit_scale:
        n_fmt = format_sizeof(n)
        total_fmt = format_sizeof(total) if total else None
    else:
        n_fmt = str(n)
        total_fmt = str(total)

    # total is known: we can predict some stats
    if total:
        # fractional and percentage progress
        frac = n / total
        percentage = frac * 100

        remaining_str = format_interval((total - n) / rate) if rate else '?'

        # format the stats displayed to the left and right sides of the bar
        l_bar = (prefix if prefix else '') + '{0:3.0f}%|'.format(percentage)
        r_bar = '| {0}/{1} [{2}<{3}, {4}]'.format(
                n_fmt, total_fmt, elapsed_str, remaining_str, rate_fmt)

        if ncols == 0:
            return l_bar[:-1] + r_bar[1:]

        # space available for bar's display
        N_BARS = max(1, ncols - len(l_bar) - len(r_bar)) if ncols \
            else 10

        # format bar depending on availability of unicode/ascii chars
        if ascii:
            bar_length, frac_bar_length = divmod(
                int(frac * N_BARS * 10), 10)

            bar = '#' * bar_length
            frac_bar = chr(48 + frac_bar_length) if frac_bar_length \
                else ' '

        else:
            bar_length, frac_bar_length = divmod(int(frac * N_BARS * 8), 8)

            bar = _unich(0x2588) * bar_length
            frac_bar = _unich(0x2590 - frac_bar_length) \
                if frac_bar_length else ' '

        # whitespace padding
        if bar_length < N_BARS:
            full_bar = bar + frac_bar + \
                ' ' * max(N_BARS - bar_length - 1, 0)
        else:
            full_bar = bar + \
                ' ' * max(N_BARS - bar_length, 0)

        return l_bar + full_bar + r_bar

    # no total: no progressbar, ETA, just progress stats
    else:
        return (prefix if prefix else '') + '{0}{1} [{2}, {3}]'.format(
            n_fmt, unit, elapsed_str, rate_fmt)


def StatusPrinter(file):
    """
    Manage the printing and in-place updating of a line of characters.
    Note that if the string is longer than a line, then in-place updating
    may not work (it will print a new line at each refresh).
    """
    fp = file
    if not getattr(fp, 'flush', False):  # pragma: no cover
        fp.flush = lambda: None

    last_printed_len = [0]  # closure over mutable variable (fast)

    def print_status(s):
        len_s = len(s)
        fp.write('\r' + s + (' ' * max(last_printed_len[0] - len_s, 0)))
        fp.flush()
        last_printed_len[0] = len_s
    return print_status


class tqdm(object):
    """
    Decorate an iterable object, returning an iterator which acts exactly
    like the orignal iterable, but prints a dynamically updating
    progressbar every time a value is requested.
    """
    def __init__(self, iterable=None, desc=None, total=None, leave=False,
                 file=sys.stderr, ncols=None, mininterval=0.1,
                 maxinterval=10.0, miniters=None, ascii=None, disable=False,
                 unit='it', unit_scale=False, dynamic_ncols=False,
                 smoothing=0.3, nested=False, gui=False):
        """
        Parameters
        ----------
        iterable  : iterable, optional
            Iterable to decorate with a progressbar.
            Leave blank [default: None] to manually manage the updates.
        desc  : str, optional
            Prefix for the progressbar [default: None].
        total  : int, optional
            The number of expected iterations. If not given, len(iterable)
            is used if possible. As a last resort, only basic progress
            statistics are displayed (no ETA, no progressbar). If `gui` is
            True and this parameter needs subsequent updating, specify an
            initial arbitrary large positive integer, e.g. int(9e9).
        leave  : bool, optional
            If [default: False], removes all traces of the progressbar
            upon termination of iteration.
        file  : `io.TextIOWrapper` or `io.StringIO`, optional
            Specifies where to output the progress messages
            [default: sys.stderr]. Uses `file.write(str)` and `file.flush()`
            methods.
        ncols  : int, optional
            The width of the entire output message. If specified,
            dynamically resizes the progressbar to stay within this bound.
            If [default: None], attempts to use environment width. The
            fallback is a meter width of 10 and no limit for the counter and
            statistics. If 0, will not print any meter (only stats).
        mininterval  : float, optional
            Minimum progress update interval, in seconds [default: 0.1].
        maxinterval  : float, optional
            Maximum progress update interval, in seconds [default: 10.0].
        miniters  : int, optional
            Minimum progress update interval, in iterations [default: None].
        ascii  : bool, optional
            If [default: None] or false, use unicode (smooth blocks) to fill
            the meter. The fallback is to use ASCII characters `1-9 #`.
        disable : bool
            Whether to disable the entire progressbar wrapper
            [default: False].
        unit  : str, optional
            String that will be used to define the unit of each iteration
            [default: 'it'].
        unit_scale  : bool, optional
            If set, the number of iterations will be reduced/scaled
            automatically and a metric prefix following the
            International System of Units standard will be added
            (kilo, mega, etc.) [default: False].
        dynamic_ncols  : bool, optional
            If set, constantly alters `ncols` to the environment (allowing
            for window resizes) [default: False].
        smoothing  : float
            Exponential moving average smoothing factor for speed estimates
            (ignored in GUI mode). Ranges from 0 (average speed) to 1
            (current/instantaneous speed) [default: 0.3].
        nested  : bool, optional
            Whether this iterable is nested in another one also managed by
            `tqdm` [default: False]. Allows display of multiple, nested
            progress bars.
        gui  : bool, optional
            WARNING: internal paramer - do not use.
            Use tqdm_gui(...) instead. If set, will attempt to use
            matplotlib animations for a graphical output [default: false].

        Returns
        -------
        out  : decorated iterator.
        """
        # Preprocess the arguments
        if total is None and iterable is not None:
            try:
                total = len(iterable)
            except (TypeError, AttributeError):
                total = None

        if ((ncols is None) and (file in (sys.stderr, sys.stdout))) or \
                dynamic_ncols:
            if dynamic_ncols:  # pragma: no cover
                dynamic_ncols = _environ_cols_wrapper()
                ncols = dynamic_ncols(file)
            else:
                ncols = _environ_cols_wrapper()(file)

        if miniters is None:
            miniters = 0
            dynamic_miniters = True
        else:
            dynamic_miniters = False

        if mininterval is None:
            mininterval = 0

        if maxinterval is None:
            maxinterval = 0

        if ascii is None:
            ascii = not _supports_unicode(file)

        if smoothing is None:
            smoothing = 0

        # Store the arguments
        self.iterable = iterable
        self.desc = desc + ': ' if desc else ''
        self.total = total
        self.leave = leave
        self.fp = file
        self.ncols = ncols
        self.mininterval = mininterval
        self.maxinterval = maxinterval
        self.miniters = miniters
        self.dynamic_miniters = dynamic_miniters
        self.ascii = ascii
        self.disable = disable
        self.unit = unit
        self.unit_scale = unit_scale
        self.gui = gui
        self.dynamic_ncols = dynamic_ncols
        self.smoothing = smoothing
        self.avg_rate = None
        # if nested, at initial sp() call we replace '\r' by '\n' to
        # not overwrite the outer progress bar
        self.nested = nested

        if not gui:
            # Initialize the screen printer
            self.sp = StatusPrinter(self.fp)
            if not disable:
                if self.nested:
                    self.fp.write('\n')
                self.sp(format_meter(0, total, 0,
                        (dynamic_ncols(file) if dynamic_ncols else ncols),
                        self.desc, ascii, unit, unit_scale))

        # Init the time/iterations counters
        self.start_t = self.last_print_t = time()
        self.last_print_n = 0
        self.n = 0

    def __len__(self):
        return len(self.iterable) if self.iterable else self.total

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def __iter__(self):
        ''' Backward-compatibility to use: for x in tqdm(iterable) '''

        # Inlining instance variables as locals (speed optimisation)
        iterable = self.iterable

        # If the bar is disabled, then just walk the iterable
        # (note: keep this check outside the loop for performance)
        if self.disable:
            for obj in iterable:
                yield obj
        else:
            ncols = self.ncols
            mininterval = self.mininterval
            maxinterval = self.maxinterval
            miniters = self.miniters
            dynamic_miniters = self.dynamic_miniters
            unit = self.unit
            unit_scale = self.unit_scale
            ascii = self.ascii
            start_t = self.start_t
            last_print_t = self.last_print_t
            last_print_n = self.last_print_n
            n = self.n
            dynamic_ncols = self.dynamic_ncols
            smoothing = self.smoothing
            avg_rate = self.avg_rate

            try:
                sp = self.sp
            except AttributeError:
                raise DeprecationWarning('Please use tqdm_gui(...)'
                                         ' instead of tqdm(..., gui=True)')

            for obj in iterable:
                yield obj
                # Update and print the progressbar.
                # Note: does not call self.update(1) for speed optimisation.
                n += 1
                delta_it = n - last_print_n
                # check the counter first (avoid calls to time())
                if delta_it >= miniters:
                    cur_t = time()
                    delta_t = cur_t - last_print_t
                    if delta_t >= mininterval:
                        elapsed = cur_t - start_t
                        # EMA (not just overall average)
                        if smoothing and delta_t:
                            avg_rate = delta_it / delta_t \
                                if avg_rate is None \
                                else smoothing * delta_it / delta_t + \
                                (1 - smoothing) * avg_rate

                        sp(format_meter(
                            n, self.total, elapsed,
                            (dynamic_ncols(self.fp) if dynamic_ncols
                             else ncols),
                            self.desc, ascii, unit, unit_scale, avg_rate))

                        # If no `miniters` was specified, adjust automatically
                        # to the maximum iteration rate seen so far.
                        if dynamic_miniters:
                            if maxinterval and delta_t > maxinterval:
                                # Set miniters to correspond to maxinterval
                                miniters = delta_it * maxinterval / delta_t
                            elif mininterval and delta_t:
                                # EMA-weight miniters to converge
                                # towards the timeframe of mininterval
                                miniters = smoothing * delta_it * mininterval \
                                    / delta_t + (1 - smoothing) * miniters
                            else:
                                miniters = smoothing * delta_it + \
                                    (1 - smoothing) * miniters

                        # Store old values for next call
                        last_print_n = n
                        last_print_t = cur_t

            # Closing the progress bar.
            # Update some internal variables for close().
            self.last_print_n = last_print_n
            self.n = n
            self.close()

    def update(self, n=1):
        """
        Manually update the progress bar, useful for streams
        such as reading files.
        E.g.:
        >>> t = tqdm(total=filesize) # Initialise
        >>> for current_buffer in stream:
        ...    ...
        ...    t.update(len(current_buffer))
        >>> t.close()
        The last line is highly recommended, but possibly not necessary if
        `t.update()` will be called in such a way that `filesize` will be
        exactly reached and printed.

        Parameters
        ----------
        n  : int
            Increment to add to the internal counter of iterations
            [default: 1].
        """
        if self.disable:
            return

        if n < 1:
            n = 1
        self.n += n

        delta_it = self.n - self.last_print_n  # should be n?
        if delta_it >= self.miniters:
            # We check the counter first, to reduce the overhead of time()
            cur_t = time()
            delta_t = cur_t - self.last_print_t
            if delta_t >= self.mininterval:
                elapsed = cur_t - self.start_t
                # EMA (not just overall average)
                if self.smoothing and delta_t:
                    self.avg_rate = delta_it / delta_t \
                        if self.avg_rate is None \
                        else self.smoothing * delta_it / delta_t + \
                        (1 - self.smoothing) * self.avg_rate

                if not hasattr(self, "sp"):
                    raise DeprecationWarning('Please use tqdm_gui(...)'
                                             ' instead of tqdm(..., gui=True)')

                self.sp(format_meter(
                    self.n, self.total, elapsed,
                    (self.dynamic_ncols(self.fp) if self.dynamic_ncols
                     else self.ncols),
                    self.desc, self.ascii, self.unit, self.unit_scale,
                    self.avg_rate))

                # If no `miniters` was specified, adjust automatically to the
                # maximum iteration rate seen so far.
                # e.g.: After running `tqdm.update(5)`, subsequent
                # calls to `tqdm.update()` will only cause an update after
                # at least 5 more iterations.
                if self.dynamic_miniters:
                    if self.maxinterval and delta_t > self.maxinterval:
                        self.miniters = self.miniters * self.maxinterval \
                            / delta_t
                    elif self.mininterval and delta_t:
                        self.miniters = self.smoothing * delta_it \
                            * self.mininterval / delta_t + \
                            (1 - self.smoothing) * self.miniters
                    else:
                        self.miniters = self.smoothing * delta_it + \
                            (1 - self.smoothing) * self.miniters

                # Store old values for next call
                self.last_print_n = self.n
                self.last_print_t = cur_t

    def close(self):
        """
        Cleanup and (if leave=False) close the progressbar.
        """
        if self.disable:
            return

        endchar = '\r'
        if self.nested:
            endchar += _term_move_up()

        if self.leave:
            if self.last_print_n < self.n:
                cur_t = time()
                # stats for overall rate (no weighted average)
                self.sp(format_meter(
                    self.n, self.total, cur_t - self.start_t,
                    (self.dynamic_ncols(self.fp) if self.dynamic_ncols
                     else self.ncols),
                    self.desc, self.ascii, self.unit, self.unit_scale))
            if self.nested:
                self.fp.write(endchar)
            else:
                self.fp.write('\n')
        else:
            self.sp('')
            self.fp.write(endchar)

    def set_description(self, desc=None):
        """
        Set/modify description of the progress bar.
        """
        self.desc = desc + ': ' if desc else ''


def trange(*args, **kwargs):
    """
    A shortcut for tqdm(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    return tqdm(_range(*args), **kwargs)
