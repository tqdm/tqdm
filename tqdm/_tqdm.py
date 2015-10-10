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
from ._utils import _supports_unicode, _environ_cols, _range, _unich
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
            return l_bar[:-1] + r_bar[1:]

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
        return (prefix if prefix else '') + '{0}{1} [{2}, {3}]'.format(
            n_fmt, unit, elapsed_str, rate_fmt)


def StatusPrinter(file):
    """
    Manage the printing and in-place updating of a line of characters.
    Note that if the string is longer than a line, then in-place updating
    may not work (it will print a new line at each refresh).
    """
    fp = file
    last_printed_len = [0]  # closure over mutable variable (fast)

    def print_status(s):
        len_s = len(s)
        fp.write('\r' + s + ' '*max(last_printed_len[0] - len_s, 0))
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
                 miniters=None, ascii=None, disable=False,
                 unit='it', unit_scale=False, gui=False):
        """
        Parameters
        ----------
        iterable  : iterable, optional
            Iterable to decorate with a progressbar.
            Leave blank [default: None] to manually manage the updates.
        desc  : str, optional
            Prefix for the progressbar [default: None].
        total  : int, optional
            The number of expected iterations. If not given, len(iterable) is
            used if possible. As a last resort, only basic progress
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
            The width of the entire output message. If specified, dynamically
            resizes the progressbar to stay within this bound
            [default: None]. The fallback is a meter width of 10 and no
            limit for the counter and statistics. If 0, will not print any
            meter (only stats).
        mininterval  : float, optional
            Minimum progress update interval, in seconds [default: 0.1].
        miniters  : int, optional
            Minimum progress update interval, in iterations [default: None].
            If specified, will set `mininterval` to 0.
        ascii  : bool, optional
            If [default: None] or false, use unicode (smooth blocks) to fill
            the meter. The fallback is to use ASCII characters `1-9 #`.
        disable : bool
            Whether to disable the entire progressbar wrapper [default: False].
        unit  : str, optional
            String that will be used to define the unit of each iteration
            [default: 'it'].
        unit_scale  : bool, optional
            If set, the number of iterations will be reduced/scaled
            automatically and a metric prefix following the
            International System of Units standard will be added
            (kilo, mega, etc.) [default: False].
        gui  : bool, optional
            If set, will attempt to use matplotlib animations for a
            graphical output [default: false].

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

        if (ncols is None) and (file in (sys.stderr, sys.stdout)):
            ncols = _environ_cols(file)

        if miniters is None:
            miniters = 0
            dynamic_miniters = True
        else:
            dynamic_miniters = False
            mininterval = 0

        if ascii is None:
            ascii = not _supports_unicode(file)

        if gui: # pragma: no cover
            try:
                import matplotlib as mpl
                import matplotlib.pyplot as plt
                from collections import deque
            except ImportError:
                gui = False
            else:
                self.mpl = mpl
                self.plt = plt

        # Store the arguments
        self.iterable = iterable
        self.desc = desc+': ' if desc else ''
        self.total = total
        self.leave = leave
        self.file = file
        self.ncols = ncols
        self.mininterval = mininterval
        self.miniters = miniters
        self.dynamic_miniters = dynamic_miniters
        self.ascii = ascii
        self.disable = disable
        self.unit = unit
        self.unit_scale = unit_scale
        self.gui = gui

        if gui: # pragma: no cover
            # Initialize the GUI display
            if not disable:
                file.write('Warning: GUI is experimental/alpha\n')

                # Remember if external environment uses toolbars
                self.toolbar = self.mpl.rcParams['toolbar']
                self.mpl.rcParams['toolbar'] = 'None'

                self.mininterval = max(mininterval, 0.5)
                self.fig, ax = plt.subplots(figsize=(9, 2.2))
                # self.fig.subplots_adjust(bottom=0.2)
                if total:
                    self.xdata = []
                    self.ydata = []
                    self.zdata = []
                else:
                    self.xdata = deque([])
                    self.ydata = deque([])
                    self.zdata = deque([])
                self.line1, = ax.plot(self.xdata, self.ydata, color='b')
                self.line2, = ax.plot(self.xdata, self.zdata, color='k')
                ax.set_ylim(0, 0.001)
                if total:
                    ax.set_xlim(0, 100)
                    ax.set_xlabel('percent')
                    self.fig.legend((self.line1, self.line2), ('cur', 'est'),
                                    loc='center right')
                    # progressbar
                    self.hspan = plt.axhspan(0, 0.001,
                                             xmin=0, xmax=0, color='g')
                else:
                    # ax.set_xlim(-60, 0)
                    ax.set_xlim(0, 60)
                    ax.invert_xaxis()
                    ax.set_xlabel('seconds')
                    ax.legend(('cur', 'est'), loc='lower left')
                ax.grid()
                # ax.set_xlabel('seconds')
                ax.set_ylabel((unit if unit else 'it') + '/s')
                if unit_scale:
                    plt.ticklabel_format(style='sci', axis='y',
                                         scilimits=(0, 0))
                    ax.yaxis.get_offset_text().set_x(-0.15)

                # Remember if external environment is interactive
                self.wasion = plt.isinteractive()
                plt.ion()
                self.ax = ax
        else:
            # Initialize the screen printer
            self.sp = StatusPrinter(self.file)
            if not disable:
                self.sp(format_meter(
                    0, total, 0, ncols, self.desc, ascii, unit, unit_scale))

        # Init the time/iterations counters
        self.start_t = self.last_print_t = time()
        self.last_print_n = 0
        self.n = 0

    def __len__(self):
        return len(self.iterable)

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
            miniters = self.miniters
            dynamic_miniters = self.dynamic_miniters
            unit = self.unit
            unit_scale = self.unit_scale
            ascii = self.ascii
            start_t = self.start_t
            last_print_t = self.last_print_t
            last_print_n = self.last_print_n
            n = self.n
            gui = self.gui
            if gui: # pragma: no cover
                plt = self.plt
                ax = self.ax
                xdata = self.xdata
                ydata = self.ydata
                zdata = self.zdata
                line1 = self.line1
                line2 = self.line2
            else:
                sp = self.sp

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
                        if gui: # pragma: no cover
                            # Inline due to multiple calls
                            total = self.total
                            # instantaneous rate
                            y = delta_it / delta_t
                            # smoothed rate
                            z = n / elapsed
                            # update line data
                            xdata.append(n * 100.0 / total if total else cur_t)
                            ydata.append(y)
                            zdata.append(z)

                            # Discard old values
                            # xmin, xmax = ax.get_xlim()
                            # if (not total) and elapsed > xmin * 1.1:
                            if (not total) and elapsed > 66:
                                xdata.popleft()
                                ydata.popleft()
                                zdata.popleft()

                            ymin, ymax = ax.get_ylim()
                            if y > ymax or z > ymax:
                                ymax = 1.1 * y
                                ax.set_ylim(ymin, ymax)
                                ax.figure.canvas.draw()

                            if total:
                                line1.set_data(xdata, ydata)
                                line2.set_data(xdata, zdata)
                                try:
                                    poly_lims = self.hspan.get_xy()
                                except AttributeError:
                                    self.hspan = plt.axhspan(0, 0.001, xmin=0,
                                                             xmax=0, color='g')
                                    poly_lims = self.hspan.get_xy()
                                poly_lims[0, 1] = ymin
                                poly_lims[1, 1] = ymax
                                poly_lims[2] = [n / total, ymax]
                                poly_lims[3] = [poly_lims[2, 0], ymin]
                                if len(poly_lims) > 4:
                                    poly_lims[4, 1] = ymin
                                self.hspan.set_xy(poly_lims)
                            else:
                                t_ago = [cur_t - i for i in xdata]
                                line1.set_data(t_ago, ydata)
                                line2.set_data(t_ago, zdata)

                            ax.set_title(format_meter(
                                n, total, elapsed, 0,
                                self.desc, ascii, unit, unit_scale),
                                fontname="DejaVu Sans Mono",
                                fontsize=11)
                            plt.pause(1e-9)
                        else:
                            sp(format_meter(
                                n, self.total, elapsed, ncols,
                                self.desc, ascii, unit, unit_scale))

                        if dynamic_miniters:
                            miniters = max(miniters, delta_it)
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
                if self.gui:  # pragma: no cover
                    # Inline due to multiple calls
                    total = self.total
                    ax = self.ax

                    # instantaneous rate
                    y = delta_it / delta_t
                    # smoothed rate
                    z = self.n / elapsed
                    # update line data
                    self.xdata.append(self.n * 100.0 / total
                                      if total else cur_t)
                    self.ydata.append(y)
                    self.zdata.append(z)

                    # Discard old values
                    if (not total) and elapsed > 66:
                        self.xdata.popleft()
                        self.ydata.popleft()
                        self.zdata.popleft()

                    ymin, ymax = ax.get_ylim()
                    if y > ymax or z > ymax:
                        ymax = 1.1 * y
                        ax.set_ylim(ymin, ymax)
                        ax.figure.canvas.draw()

                    if total:
                        self.line1.set_data(self.xdata, self.ydata)
                        self.line2.set_data(self.xdata, self.zdata)
                        try:
                            poly_lims = self.hspan.get_xy()
                        except AttributeError:
                            self.hspan = self.plt.axhspan(0, 0.001, xmin=0,
                                                          xmax=0, color='g')
                            poly_lims = self.hspan.get_xy()
                        poly_lims[0, 1] = ymin
                        poly_lims[1, 1] = ymax
                        poly_lims[2] = [self.n / total, ymax]
                        poly_lims[3] = [poly_lims[2, 0], ymin]
                        if len(poly_lims) > 4:
                            poly_lims[4, 1] = ymin
                        self.hspan.set_xy(poly_lims)
                    else:
                        t_ago = [cur_t - i for i in self.xdata]
                        self.line1.set_data(t_ago, self.ydata)
                        self.line2.set_data(t_ago, self.zdata)

                    ax.set_title(format_meter(
                        self.n, total, elapsed, 0,
                        self.desc, self.ascii, self.unit, self.unit_scale),
                        fontname="DejaVu Sans Mono",
                        fontsize=11)
                    self.plt.pause(1e-9)
                else:
                    self.sp(format_meter(
                        self.n, self.total, elapsed, self.ncols,
                        self.desc, self.ascii, self.unit, self.unit_scale))
                if self.dynamic_miniters:
                    self.miniters = max(self.miniters, delta_it)
                self.last_print_n = self.n
                self.last_print_t = cur_t

    def close(self):
        """
        Cleanup and (if leave=False) close the progressbar.
        """
        if self.disable:
            return

        if self.gui:  # pragma: no cover
            # Restore toolbars
            self.mpl.rcParams['toolbar'] = self.toolbar
            # Return to non-interactive mode
            if not self.wasion:
                self.plt.ioff()
            if not self.leave:
                self.plt.close(self.fig)
        else:
            if self.leave:
                if self.last_print_n < self.n:
                    cur_t = time()
                    self.sp(format_meter(
                        self.n, self.total, cur_t-self.start_t, self.ncols,
                        self.desc, self.ascii, self.unit, self.unit_scale))
                self.file.write('\n')
            else:
                self.sp('')
                self.file.write('\r')


def trange(*args, **kwargs):
    """
    A shortcut for tqdm(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    return tqdm(_range(*args), **kwargs)
