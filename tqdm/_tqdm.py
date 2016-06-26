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
    _term_move_up, _unicode, WeakSet
import sys
from time import time


__author__ = {"github.com/": ["noamraph", "obiwanus", "kmike", "hadim",
                              "casperdcl", "lrq3000"]}
__all__ = ['tqdm', 'trange']


class tqdm(object):
    """
    Decorate an iterable object, returning an iterator which acts exactly
    like the original iterable, but prints a dynamically updating
    progressbar every time a value is requested.
    """
    @staticmethod
    def format_sizeof(num, suffix=''):
        """
        Formats a number (greater than unity) with SI Order of Magnitude
        prefixes.

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

    @staticmethod
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

    @staticmethod
    def status_printer(file):
        """
        Manage the printing and in-place updating of a line of characters.
        Note that if the string is longer than a line, then in-place
        updating may not work (it will print a new line at each refresh).
        """
        fp = file
        fp_flush = getattr(fp, 'flush', lambda: None)  # pragma: no cover

        def fp_write(s):
            fp.write(_unicode(s))
            fp_flush()

        last_len = [0]

        def print_status(s):
            len_s = len(s)
            fp_write('\r' + s + (' ' * max(last_len[0] - len_s, 0)))
            last_len[0] = len_s
        return print_status

    @staticmethod
    def format_meter(n, total, elapsed, ncols=None, prefix='',
                     ascii=False, unit='it', unit_scale=False, rate=None,
                     bar_format=None):
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
            The width of the entire output message. If specified,
            dynamically resizes the progress meter to stay within this bound
            [default: None]. The fallback meter width is 10 for the progress
            bar + no limit for the iterations counter and statistics. If 0,
            will not print any meter (only stats).
        prefix  : str, optional
            Prefix message (included in total width) [default: ''].
        ascii  : bool, optional
            If not set, use unicode (smooth blocks) to fill the meter
            [default: False]. The fallback is to use ASCII characters
            (1-9 #).
        unit  : str, optional
            The iteration unit [default: 'it'].
        unit_scale  : bool, optional
            If set, the number of iterations will printed with an
            appropriate SI metric prefix (K = 10^3, M = 10^6, etc.)
            [default: False].
        rate  : float, optional
            Manual override for iteration rate.
            If [default: None], uses n/elapsed.
        bar_format  : str, optional
            Specify a custom bar string formatting. May impact performance.
            [default: '{l_bar}{bar}{r_bar}'], where l_bar is
            '{desc}{percentage:3.0f}%|' and r_bar is
            '| {n_fmt}/{total_fmt} [{elapsed_str}<{remaining_str}, {rate_fmt}]'
            Possible vars: bar, n, n_fmt, total, total_fmt, percentage,
            rate, rate_fmt, elapsed, remaining, l_bar, r_bar, desc.

        Returns
        -------
        out  : Formatted meter and stats, ready to display.
        """

        # sanity check: total
        if total and n > total:
            total = None

        format_interval = tqdm.format_interval
        elapsed_str = format_interval(elapsed)

        # if unspecified, attempt to use rate = average speed
        # (we allow manual override since predicting time is an arcane art)
        if rate is None and elapsed:
            rate = n / elapsed
        inv_rate = 1 / rate if (rate and (rate < 1)) else None
        format_sizeof = tqdm.format_sizeof
        rate_fmt = ((format_sizeof(inv_rate if inv_rate else rate)
                    if unit_scale else
                    '{0:5.2f}'.format(inv_rate if inv_rate else rate))
                    if rate else '?') \
            + ('s' if inv_rate else unit) + '/' + (unit if inv_rate else 's')

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

            remaining_str = format_interval((total - n) / rate) \
                if rate else '?'

            # format the stats displayed to the left and right sides of the bar
            l_bar = (prefix if prefix else '') + \
                '{0:3.0f}%|'.format(percentage)
            r_bar = '| {0}/{1} [{2}<{3}, {4}]'.format(
                    n_fmt, total_fmt, elapsed_str, remaining_str, rate_fmt)

            if ncols == 0:
                return l_bar[:-1] + r_bar[1:]

            if bar_format:
                # Custom bar formatting
                # Populate a dict with all available progress indicators
                bar_args = {'n': n,
                            'n_fmt': n_fmt,
                            'total': total,
                            'total_fmt': total_fmt,
                            'percentage': percentage,
                            'rate': rate if inv_rate is None else inv_rate,
                            'rate_noinv': rate,
                            'rate_noinv_fmt': ((format_sizeof(rate)
                                               if unit_scale else
                                               '{0:5.2f}'.format(rate))
                                               if rate else '?') + unit + '/s',
                            'rate_fmt': rate_fmt,
                            'elapsed': elapsed_str,
                            'remaining': remaining_str,
                            'l_bar': l_bar,
                            'r_bar': r_bar,
                            'desc': prefix if prefix else '',
                            # 'bar': full_bar  # replaced by procedure below
                            }

                # Interpolate supplied bar format with the dict
                if '{bar}' in bar_format:
                    # Format left/right sides of the bar, and format the bar
                    # later in the remaining space (avoid breaking display)
                    l_bar_user, r_bar_user = bar_format.split('{bar}')
                    l_bar = l_bar_user.format(**bar_args)
                    r_bar = r_bar_user.format(**bar_args)
                else:
                    # Else no progress bar, we can just format and return
                    return bar_format.format(**bar_args)

            # Formatting progress bar
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

            # Piece together the bar parts
            return l_bar + full_bar + r_bar

        # no total: no progressbar, ETA, just progress stats
        else:
            return (prefix if prefix else '') + '{0}{1} [{2}, {3}]'.format(
                n_fmt, unit, elapsed_str, rate_fmt)

    def __new__(cls, *args, **kwargs):
        # Create a new instance
        instance = object.__new__(cls)
        # Add to the list of instances
        if "_instances" not in cls.__dict__:
            cls._instances = WeakSet()
        cls._instances.add(instance)
        # Return the instance
        return instance

    @classmethod
    def _get_free_pos(cls, instance=None):
        """ Skips specified instance """
        try:
            return max(inst.pos for inst in cls._instances
                       if inst is not instance) + 1
        except ValueError as e:
            if "arg is an empty sequence" in str(e):
                return 0
            raise  # pragma: no cover

    @classmethod
    def _decr_instances(cls, instance):
        """
        Remove from list and reposition other bars
        so that newer bars won't overlap previous bars
        """
        try:  # in case instance was explicitly positioned, it won't be in set
            cls._instances.remove(instance)
            for inst in cls._instances:
                if inst.pos > instance.pos:
                    inst.pos -= 1
        except KeyError:
            pass

    @classmethod
    def write(cls, s, file=sys.stdout, end="\n"):
        """
        Print a message via tqdm (without overlap with bars)
        """
        fp = file

        # Clear all bars
        inst_cleared = []
        for inst in cls._instances:
            # Clear instance if in the target output file
            # or if write output + tqdm output are both either
            # sys.stdout or sys.stderr (because both are mixed in terminal)
            if inst.fp == fp or all(f in (sys.stdout, sys.stderr)
                                    for f in (fp, inst.fp)):
                inst.clear()
                inst_cleared.append(inst)
        # Write the message
        fp.write(s)
        fp.write(end)
        # Force refresh display of bars we cleared
        for inst in inst_cleared:
            inst.refresh()
        # TODO: make list of all instances incl. absolutely positioned ones?

    def __init__(self, iterable=None, desc=None, total=None, leave=True,
                 file=sys.stderr, ncols=None, mininterval=0.1,
                 maxinterval=10.0, miniters=None, ascii=None, disable=False,
                 unit='it', unit_scale=False, dynamic_ncols=False,
                 smoothing=0.3, bar_format=None, initial=0, position=None,
                 gui=False, **kwargs):
        """
        Parameters
        ----------
        iterable  : iterable, optional
            Iterable to decorate with a progressbar.
            Leave blank to manually manage the updates.
        desc  : str, optional
            Prefix for the progressbar.
        total  : int, optional
            The number of expected iterations. If unspecified,
            len(iterable) is used if possible. As a last resort, only basic
            progress statistics are displayed (no ETA, no progressbar).
            If `gui` is True and this parameter needs subsequent updating,
            specify an initial arbitrary large positive integer,
            e.g. int(9e9).
        leave  : bool, optional
            If [default: True], keeps all traces of the progressbar
            upon termination of iteration.
        file  : `io.TextIOWrapper` or `io.StringIO`, optional
            Specifies where to output the progress messages
            [default: sys.stderr]. Uses `file.write(str)` and `file.flush()`
            methods.
        ncols  : int, optional
            The width of the entire output message. If specified,
            dynamically resizes the progressbar to stay within this bound.
            If unspecified, attempts to use environment width. The
            fallback is a meter width of 10 and no limit for the counter and
            statistics. If 0, will not print any meter (only stats).
        mininterval  : float, optional
            Minimum progress update interval, in seconds [default: 0.1].
        maxinterval  : float, optional
            Maximum progress update interval, in seconds [default: 10.0].
        miniters  : int, optional
            Minimum progress update interval, in iterations.
            If specified, will set `mininterval` to 0.
        ascii  : bool, optional
            If unspecified or False, use unicode (smooth blocks) to fill
            the meter. The fallback is to use ASCII characters `1-9 #`.
        disable  : bool, optional
            Whether to disable the entire progressbar wrapper
            [default: False].
        unit  : str, optional
            String that will be used to define the unit of each iteration
            [default: it].
        unit_scale  : bool, optional
            If set, the number of iterations will be reduced/scaled
            automatically and a metric prefix following the
            International System of Units standard will be added
            (kilo, mega, etc.) [default: False].
        dynamic_ncols  : bool, optional
            If set, constantly alters `ncols` to the environment (allowing
            for window resizes) [default: False].
        smoothing  : float, optional
            Exponential moving average smoothing factor for speed estimates
            (ignored in GUI mode). Ranges from 0 (average speed) to 1
            (current/instantaneous speed) [default: 0.3].
        bar_format  : str, optional
            Specify a custom bar string formatting. May impact performance.
            If unspecified, will use '{l_bar}{bar}{r_bar}', where l_bar is
            '{desc}{percentage:3.0f}%|' and r_bar is
            '| {n_fmt}/{total_fmt} [{elapsed_str}<{remaining_str}, {rate_fmt}]'
            Possible vars: bar, n, n_fmt, total, total_fmt, percentage,
            rate, rate_fmt, elapsed, remaining, l_bar, r_bar, desc.
        initial  : int, optional
            The initial counter value. Useful when restarting a progress
            bar [default: 0].
        position  : int, optional
            Specify the line offset to print this bar (starting from 0)
            Automatic if unspecified.
            Useful to manage multiple bars at once (eg, from threads).
        gui  : bool, optional
            WARNING: internal parameter - do not use.
            Use tqdm_gui(...) instead. If set, will attempt to use
            matplotlib animations for a graphical output [default: False].

        Returns
        -------
        out  : decorated iterator.
        """
        if disable:
            self.iterable = iterable
            self.disable = disable
            self.pos = self._get_free_pos(self)
            self._instances.remove(self)
            return

        if kwargs:
            self.disable = True
            self.pos = self._get_free_pos(self)
            self._instances.remove(self)
            raise (DeprecationWarning("nested is deprecated and"
                                      " automated.\nUse position instead"
                                      " for manual control")
                   if "nested" in kwargs else
                   Warning("Unknown argument(s): " + str(kwargs)))

        # Preprocess the arguments
        if total is None and iterable is not None:
            try:
                total = len(iterable)
            except (TypeError, AttributeError):
                total = None

        if ((ncols is None) and (file in (sys.stderr, sys.stdout))) or \
                dynamic_ncols:  # pragma: no cover
            if dynamic_ncols:
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

        if bar_format and not ascii:
            # Convert bar format into unicode since terminal uses unicode
            bar_format = _unicode(bar_format)

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
        self.avg_time = None
        self._time = time
        self.bar_format = bar_format

        # Init the iterations counters
        self.last_print_n = initial
        self.n = initial

        # if nested, at initial sp() call we replace '\r' by '\n' to
        # not overwrite the outer progress bar
        self.pos = self._get_free_pos(self) if position is None else position

        if not gui:
            # Initialize the screen printer
            self.sp = self.status_printer(self.fp)
            if self.pos:
                self.moveto(self.pos)
            self.sp(self.format_meter(self.n, total, 0,
                    (dynamic_ncols(file) if dynamic_ncols else ncols),
                    self.desc, ascii, unit, unit_scale, None, bar_format))
            if self.pos:
                self.moveto(-self.pos)

        # Init the time counter
        self.start_t = self.last_print_t = self._time()

    def __len__(self):
        return (self.iterable.shape[0] if hasattr(self.iterable, 'shape')
                else len(self.iterable)) if self.iterable is not None \
            else self.total

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def __del__(self):
        self.close()

    def __repr__(self):
        return self.format_meter(self.n, self.total,
                                 time() - self.last_print_t,
                                 self.ncols, self.desc, self.ascii, self.unit,
                                 self.unit_scale, 1 / self.avg_time
                                 if self.avg_time else None, self.bar_format)

    def __lt__(self, other):
        # try:
        return self.pos < other.pos
        # except AttributeError:
        #     return self.start_t < other.start_t

    def __le__(self, other):
        return (self < other) or (self == other)

    def __eq__(self, other):
        # try:
        return self.pos == other.pos
        # except AttributeError:
        #     return self.start_t == other.start_t

    def __ne__(self, other):
        return not (self == other)

    def __gt__(self, other):
        return not (self <= other)

    def __ge__(self, other):
        return not (self < other)

    def __hash__(self):
        return id(self)

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
            avg_time = self.avg_time
            bar_format = self.bar_format
            _time = self._time
            format_meter = self.format_meter

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
                # check the counter first (avoid calls to time())
                if n - last_print_n >= miniters:
                    delta_it = n - last_print_n
                    cur_t = _time()
                    delta_t = cur_t - last_print_t
                    if delta_t >= mininterval:
                        elapsed = cur_t - start_t
                        # EMA (not just overall average)
                        if smoothing and delta_t:
                            avg_time = delta_t / delta_it \
                                if avg_time is None \
                                else smoothing * delta_t / delta_it + \
                                (1 - smoothing) * avg_time

                        if self.pos:
                            self.moveto(self.pos)

                        # Printing the bar's update
                        sp(format_meter(
                            n, self.total, elapsed,
                            (dynamic_ncols(self.fp) if dynamic_ncols
                             else ncols),
                            self.desc, ascii, unit, unit_scale,
                            1 / avg_time if avg_time else None, bar_format))

                        if self.pos:
                            self.moveto(-self.pos)

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
                        self.n = self.last_print_n = last_print_n = n
                        self.last_print_t = last_print_t = cur_t

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

        if n < 0:
            raise ValueError("n ({0}) cannot be negative".format(n))
        self.n += n

        delta_it = self.n - self.last_print_n  # should be n?
        if delta_it >= self.miniters:
            # We check the counter first, to reduce the overhead of time()
            cur_t = self._time()
            delta_t = cur_t - self.last_print_t
            if delta_t >= self.mininterval:
                elapsed = cur_t - self.start_t
                # EMA (not just overall average)
                if self.smoothing and delta_t:
                    self.avg_time = delta_t / delta_it \
                        if self.avg_time is None \
                        else self.smoothing * delta_t / delta_it + \
                        (1 - self.smoothing) * self.avg_time

                if not hasattr(self, "sp"):
                    raise DeprecationWarning('Please use tqdm_gui(...)'
                                             ' instead of tqdm(..., gui=True)')

                if self.pos:
                    self.moveto(self.pos)

                # Print bar's update
                self.sp(self.format_meter(
                    self.n, self.total, elapsed,
                    (self.dynamic_ncols(self.fp) if self.dynamic_ncols
                     else self.ncols),
                    self.desc, self.ascii, self.unit, self.unit_scale,
                    1 / self.avg_time if self.avg_time else None,
                    self.bar_format))

                if self.pos:
                    self.moveto(-self.pos)

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

        # Prevent multiple closures
        self.disable = True

        # decrement instance pos and remove from internal set
        pos = self.pos
        self._decr_instances(self)

        # GUI mode
        if not hasattr(self, "sp"):
            return

        # annoyingly, _supports_unicode isn't good enough
        def fp_write(s):
            self.fp.write(_unicode(s))

        try:
            fp_write('')
        except ValueError as e:
            if 'closed' in str(e):
                return
            raise  # pragma: no cover

        if pos:
            self.moveto(pos)

        if self.leave:
            if self.last_print_n < self.n:
                cur_t = self._time()
                # stats for overall rate (no weighted average)
                self.sp(self.format_meter(
                    self.n, self.total, cur_t - self.start_t,
                    (self.dynamic_ncols(self.fp) if self.dynamic_ncols
                     else self.ncols),
                    self.desc, self.ascii, self.unit, self.unit_scale, None,
                    self.bar_format))
            if pos:
                self.moveto(-pos)
            else:
                fp_write('\n')
        else:
            self.sp('')  # clear up last bar
            if pos:
                self.moveto(-pos)
            else:
                fp_write('\r')

    def unpause(self):
        """
        Restart tqdm timer from last print time.
        """
        cur_t = self._time()
        self.start_t += cur_t - self.last_print_t
        self.last_print_t = cur_t

    def set_description(self, desc=None):
        """
        Set/modify description of the progress bar.
        """
        self.desc = desc + ': ' if desc else ''

    def moveto(self, n):
        self.fp.write(_unicode('\n' * n + _term_move_up() * -n))

    def clear(self, nomove=False):
        """
        Clear current bar display
        """
        if not nomove:
            self.moveto(self.pos)
        # clear up the bar (can't rely on sp(''))
        self.fp.write('\r')
        self.fp.write(' ' * (self.ncols if self.ncols else 10))
        self.fp.write('\r')  # place cursor back at the beginning of line
        if not nomove:
            self.moveto(-self.pos)

    def refresh(self):
        """
        Force refresh the display of this bar
        """
        self.moveto(self.pos)
        # clear up this line's content (whatever there was)
        self.clear(nomove=True)
        # Print current/last bar state
        self.fp.write(self.__repr__())
        self.moveto(-self.pos)


def trange(*args, **kwargs):
    """
    A shortcut for tqdm(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    return tqdm(_range(*args), **kwargs)
