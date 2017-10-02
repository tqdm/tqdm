"""
Customisable progressbar decorator for iterators.
Includes a default (x)range iterator printing to stderr.

Usage:
  >>> from tqdm import trange[, tqdm]
  >>> for i in trange(10): #same as: for i in tqdm(xrange(10))
  ...     ...
"""
from __future__ import absolute_import
# integer division / : float, // : int
from __future__ import division
# compatibility functions and utilities
from ._utils import _supports_unicode, _environ_cols_wrapper, _range, _unich, \
    _term_move_up, _unicode, WeakSet, _basestring, _OrderedDict
# native libraries
import sys
from numbers import Number
from threading import Thread
from time import time
from time import sleep
from contextlib import contextmanager
# For parallelism safety
import multiprocessing as mp
import threading as th


__author__ = {"github.com/": ["noamraph", "obiwanus", "kmike", "hadim",
                              "casperdcl", "lrq3000"]}
__all__ = ['tqdm', 'trange',
           'TqdmTypeError', 'TqdmKeyError', 'TqdmDeprecationWarning']


class TqdmTypeError(TypeError):
    pass


class TqdmKeyError(KeyError):
    pass


class TqdmDeprecationWarning(Exception):
    # not suppressed if raised
    def __init__(self, msg, fp_write=None, *a, **k):
        if fp_write is not None:
            fp_write("\nTqdmDeprecationWarning: " + str(msg).rstrip() + '\n')
        else:
            super(TqdmDeprecationWarning, self).__init__(msg, *a, **k)


# Create global parallelism locks to avoid racing issues with parallel bars
# works only if fork available (Linux, MacOSX, but not on Windows)
mp_lock = mp.Lock()  # multiprocessing lock
th_lock = th.Lock()  # thread lock


class TqdmDefaultWriteLock(object):
    """
    Provide a default write lock for thread and multiprocessing safety.
    Works only on platforms supporting `fork` (so Windows is excluded).
    On Windows, you need to supply the lock from the parent to the children as
    an argument to joblib or the parallelism lib you use.
    """
    def __init__(self):
        global mp_lock, th_lock
        self.locks = [mp_lock, th_lock]

    def acquire(self):
        for lock in self.locks:
            lock.acquire()

    def release(self):
        for lock in self.locks[::-1]:  # Release in inverse order of acquisition
            lock.release()

    def __enter__(self):
        self.acquire()

    def __exit__(self, *exc):
        self.release()


class TMonitor(Thread):
    """
    Monitoring thread for tqdm bars.
    Monitors if tqdm bars are taking too much time to display
    and readjusts miniters automatically if necessary.

    Parameters
    ----------
    tqdm_cls  : class
        tqdm class to use (can be core tqdm or a submodule).
    sleep_interval  : fload
        Time to sleep between monitoring checks.
    """

    # internal vars for unit testing
    _time = None
    _sleep = None

    def __init__(self, tqdm_cls, sleep_interval):
        Thread.__init__(self)
        self.daemon = True  # kill thread when main killed (KeyboardInterrupt)
        self.was_killed = False
        self.woken = 0  # last time woken up, to sync with monitor
        self.tqdm_cls = tqdm_cls
        self.sleep_interval = sleep_interval
        if TMonitor._time is not None:
            self._time = TMonitor._time
        else:
            self._time = time
        if TMonitor._sleep is not None:
            self._sleep = TMonitor._sleep
        else:
            self._sleep = sleep
        self.start()

    def exit(self):
        self.was_killed = True
        # self.join()  # DO NOT, blocking event, slows down tqdm at closing
        return self.report()

    def run(self):
        cur_t = self._time()
        while True:
            # After processing and before sleeping, notify that we woke
            # Need to be done just before sleeping
            self.woken = cur_t
            # Sleep some time...
            self._sleep(self.sleep_interval)
            # Quit if killed
            # if self.exit_event.is_set():  # TODO: should work but does not...
            if self.was_killed:
                return
            # Then monitor!
            # Acquire lock (to access _instances)
            with self.tqdm_cls.get_lock():
                cur_t = self._time()
                # Check tqdm instances are waiting too long to print
                for instance in self.tqdm_cls._instances:
                    # Only if mininterval > 1 (else iterations are just slow)
                    # and last refresh exceeded maxinterval
                    if instance.miniters > 1 and \
                            (cur_t - instance.last_print_t) >= \
                            instance.maxinterval:
                        # force bypassing miniters on next iteration
                        # (dynamic_miniters adjusts mininterval automatically)
                        instance.miniters = 1
                        # Refresh now! (works only for manual tqdm)
                        instance.refresh(nolock=True)

    def report(self):
        # return self.is_alive()  # TODO: does not work...
        return not self.was_killed


class tqdm(object):
    """
    Decorate an iterable object, returning an iterator which acts exactly
    like the original iterable, but prints a dynamically updating
    progressbar every time a value is requested.
    """

    monitor_interval = 10  # set to 0 to disable the thread
    monitor = None
    _lock = TqdmDefaultWriteLock()

    @staticmethod
    def format_sizeof(num, suffix='', divisor=1000):
        """
        Formats a number (greater than unity) with SI Order of Magnitude
        prefixes.

        Parameters
        ----------
        num  : float
            Number ( >= 1) to format.
        suffix  : str, optional
            Post-postfix [default: ''].
        divisor  : float, optionl
            Divisor between prefixes [default: 1000].

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
            num /= divisor
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
    def format_meter(n, total, elapsed, ncols=None, prefix='', ascii=False,
                     unit='it', unit_scale=False, rate=None, bar_format=None,
                     postfix=None, unit_divisor=1000):
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
            Use as {desc} in bar_format string.
        ascii  : bool, optional
            If not set, use unicode (smooth blocks) to fill the meter
            [default: False]. The fallback is to use ASCII characters
            (1-9 #).
        unit  : str, optional
            The iteration unit [default: 'it'].
        unit_scale  : bool or int or float, optional
            If 1 or True, the number of iterations will be printed with an
            appropriate SI metric prefix (K = 10^3, M = 10^6, etc.)
            [default: False]. If any other non-zero number, will scale
            `total` and `n`.
        rate  : float, optional
            Manual override for iteration rate.
            If [default: None], uses n/elapsed.
        bar_format  : str, optional
            Specify a custom bar string formatting. May impact performance.
            [default: '{l_bar}{bar}{r_bar}'], where
            l_bar='{desc}: {percentage:3.0f}%|' and
            r_bar='| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, '
                  '{rate_fmt}{postfix}]'
            Possible vars: l_bar, bar, r_bar, n, n_fmt, total, total_fmt,
                percentage, rate, rate_fmt, rate_noinv, rate_noinv_fmt,
                rate_inv, rate_inv_fmt, elapsed, remaining, desc, postfix.
            Note that a trailing ": " is automatically removed after {desc}
            if the latter is empty.
        postfix  : str, optional
            Similar to `prefix`, but placed at the end
            (e.g. for additional stats).
            Note: postfix is a string for this method. Not a dict.
        unit_divisor  : float, optional
            [default: 1000], ignored unless `unit_scale` is True.

        Returns
        -------
        out  : Formatted meter and stats, ready to display.
        """

        # sanity check: total
        if total and n > total:
            total = None

        # apply custom scale if necessary
        if unit_scale and unit_scale not in (True, 1):
            total *= unit_scale
            n *= unit_scale
            unit_scale = False

        format_interval = tqdm.format_interval
        elapsed_str = format_interval(elapsed)

        # if unspecified, attempt to use rate = average speed
        # (we allow manual override since predicting time is an arcane art)
        if rate is None and elapsed:
            rate = n / elapsed
        inv_rate = 1 / rate if rate else None
        format_sizeof = tqdm.format_sizeof
        rate_noinv_fmt = ((format_sizeof(rate) if unit_scale else
                           '{0:5.2f}'.format(rate))
                          if rate else '?') + unit + '/s'
        rate_inv_fmt = ((format_sizeof(inv_rate) if unit_scale else
                         '{0:5.2f}'.format(inv_rate))
                        if inv_rate else '?') + 's/' + unit
        rate_fmt = rate_inv_fmt if inv_rate and inv_rate > 1 else rate_noinv_fmt

        if unit_scale:
            n_fmt = format_sizeof(n, divisor=unit_divisor)
            total_fmt = format_sizeof(total, divisor=unit_divisor) \
                if total else None
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
            if prefix:
                # old prefix setup work around
                bool_prefix_colon_already = (prefix[-2:] == ": ")
                l_bar = prefix if bool_prefix_colon_already else prefix + ": "
            else:
                l_bar = ''
            l_bar += '{0:3.0f}%|'.format(percentage)
            r_bar = '| {0}/{1} [{2}<{3}, {4}{5}]'.format(
                n_fmt, total_fmt, elapsed_str, remaining_str, rate_fmt,
                ', ' + postfix if postfix else '')

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
                            'rate': inv_rate if inv_rate and inv_rate > 1
                            else rate,
                            'rate_fmt': rate_fmt,
                            'rate_noinv': rate,
                            'rate_noinv_fmt': rate_noinv_fmt,
                            'rate_inv': inv_rate,
                            'rate_inv_fmt': rate_inv_fmt,
                            'elapsed': elapsed_str,
                            'remaining': remaining_str,
                            'l_bar': l_bar,
                            'r_bar': r_bar,
                            'desc': prefix or '',
                            'postfix': ', ' + postfix if postfix else '',
                            # 'bar': full_bar  # replaced by procedure below
                            }

                # auto-remove colon for empty `desc`
                if not prefix:
                    bar_format = bar_format.replace("{desc}: ", '')

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
            return ((prefix + ": ") if prefix else '') + \
                '{0}{1} [{2}, {3}{4}]'.format(
                    n_fmt, unit, elapsed_str, rate_fmt,
                    ', ' + postfix if postfix else '')

    def __new__(cls, *args, **kwargs):
        # Create a new instance
        instance = object.__new__(cls)
        # Add to the list of instances
        if "_instances" not in cls.__dict__:
            cls._instances = WeakSet()
        with cls._lock:
            cls._instances.add(instance)
        # Create the monitoring thread
        if cls.monitor_interval and (cls.monitor is None or not
                                     cls.monitor.report()):
            cls.monitor = TMonitor(cls, cls.monitor_interval)
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
            with cls._lock:
                cls._instances.remove(instance)
                for inst in cls._instances:
                    if inst.pos > instance.pos:
                        inst.pos -= 1
            # Kill monitor if no instances are left
            if not cls._instances and cls.monitor:
                try:
                    cls.monitor.exit()
                    del cls.monitor
                except AttributeError:  # pragma: nocover
                    pass
                else:
                    cls.monitor = None
        except KeyError:
            pass

    @classmethod
    def write(cls, s, file=None, end="\n", nolock=False):
        """
        Print a message via tqdm (without overlap with bars)
        """
        fp = file if file is not None else sys.stdout
        with cls.external_write_mode(file=file, nolock=nolock):
            # Write the message
            fp.write(s)
            fp.write(end)

    @classmethod
    @contextmanager
    def external_write_mode(cls, file=None, nolock=False):
        """
        Disable tqdm within context and refresh tqdm when exits.
        Useful when writing to standard output stream
        """
        fp = file if file is not None else sys.stdout

        if not nolock:
            cls._lock.acquire()
        # Clear all bars
        inst_cleared = []
        for inst in getattr(cls, '_instances', []):
            # Clear instance if in the target output file
            # or if write output + tqdm output are both either
            # sys.stdout or sys.stderr (because both are mixed in terminal)
            if inst.fp == fp or all(
                    f in (sys.stdout, sys.stderr) for f in (fp, inst.fp)):
                inst.clear(nolock=True)
                inst_cleared.append(inst)
        yield
        # Force refresh display of bars we cleared
        for inst in inst_cleared:
            # Avoid race conditions by checking that the instance started
            if hasattr(inst, 'start_t'):  # pragma: nocover
                inst.refresh(nolock=True)
        if not nolock:
            cls._lock.release()
        # TODO: make list of all instances incl. absolutely positioned ones?

    @classmethod
    def set_lock(cls, lock):
        cls._lock = lock

    @classmethod
    def get_lock(cls):
        return cls._lock

    @classmethod
    def pandas(tclass, *targs, **tkwargs):
        """
        Registers the given `tqdm` class with
            pandas.core.
            ( frame.DataFrame
            | series.Series
            | groupby.DataFrameGroupBy
            | groupby.SeriesGroupBy
            ).progress_apply

        A new instance will be create every time `progress_apply` is called,
        and each instance will automatically close() upon completion.

        Parameters
        ----------
        targs, tkwargs  : arguments for the tqdm instance

        Examples
        --------
        >>> import pandas as pd
        >>> import numpy as np
        >>> from tqdm import tqdm, tqdm_gui
        >>>
        >>> df = pd.DataFrame(np.random.randint(0, 100, (100000, 6)))
        >>> tqdm.pandas(ncols=50)  # can use tqdm_gui, optional kwargs, etc
        >>> # Now you can use `progress_apply` instead of `apply`
        >>> df.groupby(0).progress_apply(lambda x: x**2)

        References
        ----------
        https://stackoverflow.com/questions/18603270/
        progress-indicator-during-pandas-operations-python
        """
        from pandas.core.frame import DataFrame
        from pandas.core.series import Series
        from pandas.core.groupby import DataFrameGroupBy
        from pandas.core.groupby import SeriesGroupBy
        from pandas.core.groupby import GroupBy
        from pandas.core.groupby import PanelGroupBy
        from pandas import Panel

        deprecated_t = [tkwargs.pop('deprecated_t', None)]

        def inner_generator(df_function='apply'):
            def inner(df, func, *args, **kwargs):
                """
                Parameters
                ----------
                df  : (DataFrame|Series)[GroupBy]
                    Data (may be grouped).
                func  : function
                    To be applied on the (grouped) data.
                *args, *kwargs  : optional
                    Transmitted to `df.apply()`.
                """
                # Precompute total iterations
                total = getattr(df, 'ngroups', None)
                if total is None:  # not grouped
                    if isinstance(df, Series):
                        total = len(df)
                    else:
                        if kwargs.get('axis') == 1:
                            total = len(df)
                        else:
                            total = df.size // len(df)
                else:
                    total += 1  # pandas calls update once too many

                # Init bar
                if deprecated_t[0] is not None:
                    t = deprecated_t[0]
                    deprecated_t[0] = None
                else:
                    t = tclass(*targs, total=total, **tkwargs)

                # Define bar updating wrapper
                def wrapper(*args, **kwargs):
                    t.update()
                    return func(*args, **kwargs)

                # Apply the provided function (in *args and **kwargs)
                # on the df using our wrapper (which provides bar updating)
                result = getattr(df, df_function)(wrapper, *args, **kwargs)

                # Close bar and return pandas calculation result
                t.close()
                return result

            return inner

        # Monkeypatch pandas to provide easy methods
        # Enable custom tqdm progress in pandas!
        Series.progress_apply = inner_generator()
        SeriesGroupBy.progress_apply = inner_generator()
        Series.progress_map = inner_generator('map')
        SeriesGroupBy.progress_map = inner_generator('map')

        DataFrame.progress_apply = inner_generator()
        DataFrameGroupBy.progress_apply = inner_generator()
        DataFrame.progress_applymap = inner_generator('applymap')

        Panel.progress_apply = inner_generator()
        PanelGroupBy.progress_apply = inner_generator()

        GroupBy.progress_apply = inner_generator()
        GroupBy.progress_aggregate = inner_generator('aggregate')
        GroupBy.progress_transform = inner_generator('transform')

    def __init__(self, iterable=None, desc=None, total=None, leave=True,
                 file=None, ncols=None, mininterval=0.1, maxinterval=10.0,
                 miniters=None, ascii=None, disable=False, unit='it',
                 unit_scale=False, dynamic_ncols=False, smoothing=0.3,
                 bar_format=None, initial=0, position=None, postfix=None,
                 unit_divisor=1000, gui=False, **kwargs):
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
            (default: sys.stderr). Uses `file.write(str)` and `file.flush()`
            methods.
        ncols  : int, optional
            The width of the entire output message. If specified,
            dynamically resizes the progressbar to stay within this bound.
            If unspecified, attempts to use environment width. The
            fallback is a meter width of 10 and no limit for the counter and
            statistics. If 0, will not print any meter (only stats).
        mininterval  : float, optional
            Minimum progress display update interval, in seconds [default: 0.1].
        maxinterval  : float, optional
            Maximum progress display update interval, in seconds [default: 10].
            Automatically adjusts `miniters` to correspond to `mininterval`
            after long display update lag. Only works if `dynamic_miniters`
            or monitor thread is enabled.
        miniters  : int, optional
            Minimum progress display update interval, in iterations.
            If 0 and `dynamic_miniters`, will automatically adjust to equal
            `mininterval` (more CPU efficient, good for tight loops).
            If > 0, will skip display of specified number of iterations.
            Tweak this and `mininterval` to get very efficient loops.
            If your progress is erratic with both fast and slow iterations
            (network, skipping items, etc) you should set miniters=1.
        ascii  : bool, optional
            If unspecified or False, use unicode (smooth blocks) to fill
            the meter. The fallback is to use ASCII characters `1-9 #`.
        disable  : bool, optional
            Whether to disable the entire progressbar wrapper
            [default: False]. If set to None, disable on non-TTY.
        unit  : str, optional
            String that will be used to define the unit of each iteration
            [default: it].
        unit_scale  : bool or int or float, optional
            If 1 or True, the number of iterations will be reduced/scaled
            automatically and a metric prefix following the
            International System of Units standard will be added
            (kilo, mega, etc.) [default: False]. If any other non-zero
            number, will scale `total` and `n`.
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
            '{desc}: {percentage:3.0f}%|' and r_bar is
            '| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
            Possible vars: bar, n, n_fmt, total, total_fmt, percentage,
            rate, rate_fmt, elapsed, remaining, l_bar, r_bar, desc.
            Note that a trailing ": " is automatically removed after {desc}
            if the latter is empty.
        initial  : int, optional
            The initial counter value. Useful when restarting a progress
            bar [default: 0].
        position  : int, optional
            Specify the line offset to print this bar (starting from 0)
            Automatic if unspecified.
            Useful to manage multiple bars at once (eg, from threads).
        postfix  : dict, optional
            Specify additional stats to display at the end of the bar.
            Note: postfix is a dict ({'key': value} pairs) for this method,
            not a string.
        unit_divisor  : float, optional
            [default: 1000], ignored unless `unit_scale` is True.
        gui  : bool, optional
            WARNING: internal parameter - do not use.
            Use tqdm_gui(...) instead. If set, will attempt to use
            matplotlib animations for a graphical output [default: False].

        Returns
        -------
        out  : decorated iterator.
        """

        if file is None:
            file = sys.stderr

        if disable is None and hasattr(file, "isatty") and not file.isatty():
            disable = True

        if disable:
            self.iterable = iterable
            self.disable = disable
            self.pos = self._get_free_pos(self)
            self._instances.remove(self)
            self.n = initial
            return

        if kwargs:
            self.disable = True
            self.pos = self._get_free_pos(self)
            self._instances.remove(self)
            raise (TqdmDeprecationWarning("""\
`nested` is deprecated and automated. Use position instead for manual control.
""", fp_write=getattr(file, 'write', sys.stderr.write)) if "nested" in kwargs
                else TqdmKeyError("Unknown argument(s): " + str(kwargs)))

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
                if dynamic_ncols:
                    ncols = dynamic_ncols(file)
                # elif ncols is not None:
                #     ncols = 79
            else:
                _dynamic_ncols = _environ_cols_wrapper()
                if _dynamic_ncols:
                    ncols = _dynamic_ncols(file)
                # else:
                #     ncols = 79

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
        self.desc = desc or ''
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
        self.unit_divisor = unit_divisor
        self.gui = gui
        self.dynamic_ncols = dynamic_ncols
        self.smoothing = smoothing
        self.avg_time = None
        self._time = time
        self.bar_format = bar_format
        self.postfix = None
        if postfix:
            self.set_postfix(refresh=False, **postfix)

        # Init the iterations counters
        self.last_print_n = initial
        self.n = initial

        # if nested, at initial sp() call we replace '\r' by '\n' to
        # not overwrite the outer progress bar
        if position is None:
            self.pos = self._get_free_pos(self)
        else:
            self.pos = position
            self._instances.remove(self)

        if not gui:
            # Initialize the screen printer
            self.sp = self.status_printer(self.fp)
            with self._lock:
                if self.pos:
                    self.moveto(self.pos)
                self.sp(self.__repr__(elapsed=0))
                if self.pos:
                    self.moveto(-self.pos)

        # Init the time counter
        self.last_print_t = self._time()
        # NB: Avoid race conditions by setting start_t at the very end of init
        self.start_t = self.last_print_t

    def __len__(self):
        return self.total if self.iterable is None else \
            (self.iterable.shape[0] if hasattr(self.iterable, "shape")
             else len(self.iterable) if hasattr(self.iterable, "__len__")
             else self.total)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def __del__(self):
        self.close()

    def __repr__(self, elapsed=None):
        return self.format_meter(
            self.n, self.total,
            elapsed if elapsed is not None else self._time() - self.start_t,
            self.dynamic_ncols(self.fp) if self.dynamic_ncols else self.ncols,
            self.desc, self.ascii, self.unit,
            self.unit_scale, 1 / self.avg_time if self.avg_time else None,
            self.bar_format, self.postfix, self.unit_divisor)

    def __lt__(self, other):
        return self.pos < other.pos

    def __le__(self, other):
        return (self < other) or (self == other)

    def __eq__(self, other):
        return self.pos == other.pos

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
            mininterval = self.mininterval
            maxinterval = self.maxinterval
            miniters = self.miniters
            dynamic_miniters = self.dynamic_miniters
            last_print_t = self.last_print_t
            last_print_n = self.last_print_n
            n = self.n
            smoothing = self.smoothing
            avg_time = self.avg_time
            _time = self._time

            try:
                sp = self.sp
            except AttributeError:
                raise TqdmDeprecationWarning("""\
Please use `tqdm_gui(...)` instead of `tqdm(..., gui=True)`
""", fp_write=getattr(self.fp, 'write', sys.stderr.write))

            for obj in iterable:
                yield obj
                # Update and possibly print the progressbar.
                # Note: does not call self.update(1) for speed optimisation.
                n += 1
                # check counter first to avoid calls to time()
                if n - last_print_n >= self.miniters:
                    miniters = self.miniters  # watch monitoring thread changes
                    delta_t = _time() - last_print_t
                    if delta_t >= mininterval:
                        cur_t = _time()
                        delta_it = n - last_print_n
                        # EMA (not just overall average)
                        if smoothing and delta_t and delta_it:
                            avg_time = delta_t / delta_it \
                                if avg_time is None \
                                else smoothing * delta_t / delta_it + \
                                (1 - smoothing) * avg_time

                        self.n = n
                        with self._lock:
                            if self.pos:
                                self.moveto(self.pos)
                            # Print bar update
                            sp(self.__repr__())
                            if self.pos:
                                self.moveto(-self.pos)

                        # If no `miniters` was specified, adjust automatically
                        # to the max iteration rate seen so far between 2 prints
                        if dynamic_miniters:
                            if maxinterval and delta_t >= maxinterval:
                                # Adjust miniters to time interval by rule of 3
                                if mininterval:
                                    # Set miniters to correspond to mininterval
                                    miniters = delta_it * mininterval / delta_t
                                else:
                                    # Set miniters to correspond to maxinterval
                                    miniters = delta_it * maxinterval / delta_t
                            elif smoothing:
                                # EMA-weight miniters to converge
                                # towards the timeframe of mininterval
                                miniters = smoothing * delta_it * \
                                    (mininterval / delta_t
                                     if mininterval and delta_t else 1) + \
                                    (1 - smoothing) * miniters
                            else:
                                # Maximum nb of iterations between 2 prints
                                miniters = max(miniters, delta_it)

                        # Store old values for next call
                        self.n = self.last_print_n = last_print_n = n
                        self.last_print_t = last_print_t = cur_t
                        self.miniters = miniters

            # Closing the progress bar.
            # Update some internal variables for close().
            self.last_print_n = last_print_n
            self.n = n
            self.miniters = miniters
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
        n  : int, optional
            Increment to add to the internal counter of iterations
            [default: 1].
        """
        # N.B.: see __iter__() for more comments.
        if self.disable:
            return

        if n < 0:
            raise ValueError("n ({0}) cannot be negative".format(n))
        self.n += n

        # check counter first to reduce calls to time()
        if self.n - self.last_print_n >= self.miniters:
            delta_t = self._time() - self.last_print_t
            if delta_t >= self.mininterval:
                cur_t = self._time()
                delta_it = self.n - self.last_print_n  # >= n
                # elapsed = cur_t - self.start_t
                # EMA (not just overall average)
                if self.smoothing and delta_t and delta_it:
                    self.avg_time = delta_t / delta_it \
                        if self.avg_time is None \
                        else self.smoothing * delta_t / delta_it + \
                        (1 - self.smoothing) * self.avg_time

                if not hasattr(self, "sp"):
                    raise TqdmDeprecationWarning("""\
Please use `tqdm_gui(...)` instead of `tqdm(..., gui=True)`
""", fp_write=getattr(self.fp, 'write', sys.stderr.write))

                with self._lock:
                    if self.pos:
                        self.moveto(self.pos)

                    # Print bar update
                    self.sp(self.__repr__())

                    if self.pos:
                        self.moveto(-self.pos)

                # If no `miniters` was specified, adjust automatically to the
                # maximum iteration rate seen so far between two prints.
                # e.g.: After running `tqdm.update(5)`, subsequent
                # calls to `tqdm.update()` will only cause an update after
                # at least 5 more iterations.
                if self.dynamic_miniters:
                    if self.maxinterval and delta_t >= self.maxinterval:
                        if self.mininterval:
                            self.miniters = delta_it * self.mininterval \
                                / delta_t
                        else:
                            self.miniters = delta_it * self.maxinterval \
                                / delta_t
                    elif self.smoothing:
                        self.miniters = self.smoothing * delta_it * \
                            (self.mininterval / delta_t
                             if self.mininterval and delta_t
                             else 1) + \
                            (1 - self.smoothing) * self.miniters
                    else:
                        self.miniters = max(self.miniters, delta_it)

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

        with self._lock:
            if pos:
                self.moveto(pos)

            if self.leave:
                if self.last_print_n < self.n:
                    # stats for overall rate (no weighted average)
                    self.avg_time = None
                    self.sp(self.__repr__())
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

    def set_description(self, desc=None, refresh=True):
        """
        Set/modify description of the progress bar.

        Parameters
        ----------
        desc  : str, optional
        refresh  : bool, optional
            Forces refresh [default: True].
        """
        self.desc = desc + ': ' if desc else ''
        if refresh:
            self.refresh()

    def set_description_str(self, desc=None, refresh=True):
        """
        Set/modify description without ': ' appended.
        """
        self.desc = desc or ''
        if refresh:
            self.refresh()

    def set_postfix(self, ordered_dict=None, refresh=True, **kwargs):
        """
        Set/modify postfix (additional stats)
        with automatic formatting based on datatype.

        Parameters
        ----------
        ordered_dict  : dict or OrderedDict, optional
        refresh  : bool, optional
            Forces refresh [default: True].
        kwargs  : dict, optional
        """
        # Sort in alphabetical order to be more deterministic
        postfix = _OrderedDict([] if ordered_dict is None else ordered_dict)
        for key in sorted(kwargs.keys()):
            postfix[key] = kwargs[key]
        # Preprocess stats according to datatype
        for key in postfix.keys():
            # Number: limit the length of the string
            if isinstance(postfix[key], Number):
                postfix[key] = '{0:2.3g}'.format(postfix[key])
            # Else for any other type, try to get the string conversion
            elif not isinstance(postfix[key], _basestring):
                postfix[key] = str(postfix[key])
            # Else if it's a string, don't need to preprocess anything
        # Stitch together to get the final postfix
        self.postfix = ', '.join(key + '=' + postfix[key].strip()
                                 for key in postfix.keys())
        if refresh:
            self.refresh()

    def set_postfix_str(self, s='', refresh=True):
        """
        Postfix without dictionary expansion, similar to prefix handling.
        """
        self.postfix = str(s)
        if refresh:
            self.refresh()

    def moveto(self, n):
        self.fp.write(_unicode('\n' * n + _term_move_up() * -n))

    def clear(self, nomove=False, nolock=False):
        """
        Clear current bar display
        """
        if self.disable:
            return

        if not nolock:
            self._lock.acquire()
        if not nomove:
            self.moveto(self.pos)
        # clear up the bar (can't rely on sp(''))
        self.fp.write('\r')
        self.fp.write(' ' * (self.ncols if self.ncols else 10))
        self.fp.write('\r')  # place cursor back at the beginning of line
        if not nomove:
            self.moveto(-self.pos)
        if not nolock:
            self._lock.release()

    def refresh(self, nolock=False):
        """
        Force refresh the display of this bar
        """
        if self.disable:
            return

        if not nolock:
            self._lock.acquire()
        self.moveto(self.pos)
        # clear up this line's content (whatever there was)
        self.clear(nomove=True, nolock=True)
        # Print current/last bar state
        self.fp.write(self.__repr__())
        self.moveto(-self.pos)
        if not nolock:
            self._lock.release()


def trange(*args, **kwargs):
    """
    A shortcut for tqdm(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    return tqdm(_range(*args), **kwargs)
