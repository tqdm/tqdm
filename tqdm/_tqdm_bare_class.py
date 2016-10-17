"""
Standalone minimal tqdm but with major features.
For developers porting to other languages or speed freaks.
Includes a default (x)range iterator printing to stderr.

Usage:
  >>> from tqdm import tbcrange[, tqdm_bare_class]
  >>> for i in tbcrange(10): #same as: for i in tqdm_bare_class(xrange(10))
  ...     ...
"""
# future division is important to divide integers and get as
# a result precise floating numbers (instead of truncated int)
from __future__ import division
# import colorama to support move up character in windows term
# can't be included here because conflicts if both tqdm and tqdm_bare_class imported
from ._utils import IS_WIN, colorama
# import utilities
import sys
from time import time

try:
    _range = xrange
except:
    _range = range

try:
    _unicode = unicode
except NameError:
    _unicode = str

# Console move up control character (opposite of newline return)
_term_move_up = '' if IS_WIN and (colorama is None) else '\x1b[A'


__author__ = {"github.com/": ["noamraph", "obiwanus", "kmike", "hadim",
                              "casperdcl", "lrq3000"]}
__all__ = ['tqdm_bare_class', 'tbcrange']


class tqdm_bare_class(object):
    """
    Minimalist barebone progress bar reproducing tqdm's major features.
    Decorate an iterable object, returning an iterator which acts exactly
    like the original iterable, but prints a dynamically updating
    progressbar every time a value is requested.

    See core tqdm for arguments descriptions.

    STATUS: ALPHA EXPERIMENTAL.
    """
    @staticmethod
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

    @staticmethod
    def format_interval(t):
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
            fp.write(s)
            fp_flush()

        last_len = [0]

        def print_status(s):
            len_s = len(s)
            # Print current bar + fill with blank to clear previous display
            fp_write('\r' + s + (' ' * max(last_len[0] - len_s, 0)))
            # Store current string length for later clearing
            last_len[0] = len_s
        return print_status

    @staticmethod
    def format_meter(n, total, elapsed, width=78, prefix='',
                     unit='it', unit_scale=False, rate=None):
        """
        Return a string-based progress bar given some parameters
        """
        # faster access by inlining static call
        format_interval = tqdm_bare_class.format_interval
        format_sizeof = tqdm_bare_class.format_sizeof

        elapsed_fmt = format_interval(elapsed)
        if unit_scale:
            n_fmt = format_sizeof(n)
            total_fmt = format_sizeof(total) if total else None
        else:
            n_fmt = str(n)
            total_fmt = str(total) if total else None

        # if unspecified, attempt to use rate = average speed
        # (we allow manual override since predicting time is an arcane art)
        if rate is None and elapsed:
            rate = n / elapsed
        inv_rate = 1 / rate if (rate and (rate < 1)) else None
        rate_fmt = ((format_sizeof(inv_rate if inv_rate else rate)
                    if unit_scale else
                    '{0:5.2f}'.format(inv_rate if inv_rate else rate))
                    if rate else '?') \
            + ('s' if inv_rate else unit) + '/' + (unit if inv_rate else 's')

        if total:
            frac = n / total
            percentage = int(frac * 100)
            eta = (total - n) / rate if rate > 0 else 0
            eta_fmt = format_interval(eta)

            l_bar = '{0}{1}%|'.format(prefix, percentage)
            r_bar = '|{0}/{1} [{2}<{3}, {4}]'.format(n_fmt,
                          total_fmt, elapsed_fmt, eta_fmt, rate_fmt)
            bar_width = width - len(l_bar) - len(r_bar)

            bar = '#' * int(frac * bar_width)
            bar_length, frac_bar_length = divmod(
                int(frac * bar_width * 10), 10)
            bar = '#' * bar_length
            frac_bar = chr(48 + frac_bar_length) if frac_bar_length \
                else ''
            bar_fill = ' ' * (bar_width - (bar_length + len(frac_bar)))

            # Build complete bar
            full_bar = l_bar + bar + frac_bar + bar_fill + r_bar

        else:
            full_bar = '{0}{1}{2} [{3}, {4}]'.format(prefix, n, unit, elapsed_fmt, rate_fmt)

        return full_bar

    def moveto(self, pos):
        self.fp.write(_unicode('\n' * pos + _term_move_up * -pos))
    
    def __init__(self, iterable=None, desc=None, total=None, leave=True,
                    file=None, width=78, mininterval=0.1,
                    maxinterval=10, miniters=None, disable=False,
                    unit='it', unit_scale=False,
                    smoothing=0.3, initial=0, position=None,
                    **kwargs):

        # -- Initialization
        if disable:
            self.iterable = iterable
            self.disable = disable
            return

        # Define file default value at instanciation rather than class import
        # (ease file redirection)
        if file is None:
            file = sys.stdout

        # Preprocess the arguments
        if total is None and iterable is not None:
            try:
                total = len(iterable)
            except (TypeError, AttributeError):
                total = None

        desc = desc + ': ' if desc else ''

        if miniters is None:
            miniters = 0
            dynamic_miniters = True
        else:
            miniters = miniters
            dynamic_miniters = False

        if mininterval is None:
            mininterval = 0

        if maxinterval is None:
            maxinterval = 0

        # Position automagic management (aka nested bars)
        if not hasattr(tqdm_bare_class, '_instances'):
            # Create function variable if not existent
            # use a class property to share amongst all instances
            tqdm_bare_class._instances = set()
        if position is None:
            # Automatic position number generation
            prev_pos = -1  # position just before the hole
            for p in tqdm_bare_class._instances:
                # If there's a hole between two instances pos, pick this position
                if (p - prev_pos) > 1:
                    break
                prev_pos = p
            # Pick next position to the one before the hole
            position = prev_pos+1
        # Store position in the list (just to know which ones are taken)
        tqdm_bare_class._instances.add(position)

        # Store in instance for later access in methods
        self.iterable = iterable
        self.fp = file
        self.n = self.last_print_n = initial
        self.start_t = self.last_print_t = time()
        self.total = total
        self.desc = desc
        self.width = width
        self.mininterval = mininterval
        self.maxinterval = maxinterval
        self.miniters = miniters
        self.dynamic_miniters = dynamic_miniters
        self.smoothing = smoothing
        self.unit = unit
        self.unit_scale = unit_scale
        self.leave = leave
        self.pos = position
        self.disable = disable
        self.avg_time = None  # will be defined if smoothing > 0

        # Initialize the bar display
        if not disable:
            # Initialize the screen printer
            self.sp = self.status_printer(self.fp)
            
            self.moveto(self.pos)
            self.sp(self.format_meter(self.n, self.total, 0, self.width, self.desc, self.unit, self.unit_scale))
            self.moveto(-self.pos)
        # -- End of initialization
    
    def __len__(self):
        return len(self.iterable) if self.iterable is not None \
            else self.total

    def __iter__(self):
        """
        Iterable wrapper: for x in tqdm(iterable)
        """

        # Inlining instance variables as locals (speed optimisation)
        iterable = self.iterable

        # If the bar is disabled, then just walk the iterable
        # (note: keep this check outside the loop for performance)
        if self.disable:
            for obj in iterable:
                yield obj
        else:
            n = self.n
            total = self.total
            desc = self.desc
            width = self.width
            mininterval = self.mininterval
            maxinterval = self.maxinterval
            miniters = self.miniters
            dynamic_miniters = self.dynamic_miniters
            unit = self.unit
            unit_scale = self.unit_scale
            start_t = self.start_t
            last_print_t = self.last_print_t
            last_print_n = self.last_print_n
            pos = self.pos
            smoothing = self.smoothing
            avg_time = self.avg_time
            format_meter = self.format_meter

            for elt in iterable:
                yield elt

                # Update and print the progressbar.
                # Note: does not call self.update(1) for speed optimisation.
                n += 1
                # check the counter first (avoid calls to time()
                if n - last_print_n >= miniters:
                    delta_t = time() - last_print_t
                    if delta_t >= mininterval:
                        cur_t = time()
                        delta_it = n - last_print_n
                        last_print_t = cur_t
                        last_print_n = n

                        if dynamic_miniters:
                            if maxinterval and delta_t >= maxinterval and mininterval:
                                # Set miniters to correspond to maxinterval
                                miniters = delta_it * mininterval / delta_t
                            elif smoothing:
                                # EMA-weight miniters to converge
                                # towards the timeframe of mininterval
                                miniters = smoothing * delta_it * \
                                              (mininterval / delta_t
                                               if mininterval and delta_t
                                               else 1) + \
                                              (1 - smoothing) * miniters
                            else:
                                # Maximum nb of iterations between 2 prints
                                miniters = max(miniters, delta_it)

                        # EMA rate
                        if smoothing and delta_t:
                            avg_time = delta_t / delta_it \
                                if avg_time is None \
                                else smoothing * delta_t / delta_it + \
                                (1 - smoothing) * avg_time

                        # Position the cursor
                        if pos:
                            self.moveto(pos)

                        # Format and display current bar
                        self.sp(format_meter(n, total, cur_t - start_t, width, desc,
                                                unit, unit_scale,
                                                1 / avg_time if avg_time
                                                else None))

                        # Position the cursor back
                        if pos:
                            self.moveto(-pos)

        # Closing the progress bar.
        # Update some internal variables for close().
        self.last_print_n = last_print_n
        self.n = n
        self.close()

    def update(self, n=1):
        """
        Manual update the bar
        Exact same code as __iter__() but using instance variables
        """
        # Update and print the progressbar.
        self.n += n
        # check the counter first (avoid calls to time()
        if self.n - self.last_print_n >= self.miniters:
            delta_t = time() - self.last_print_t
            if delta_t >= self.mininterval:
                cur_t = time()
                delta_it = self.n - self.last_print_n
                self.last_print_t = cur_t
                self.last_print_n = n

                if self.dynamic_miniters:
                    if self.maxinterval and delta_t >= self.maxinterval and self.mininterval:
                        # Set miniters to correspond to maxinterval
                        self.miniters = delta_it * self.mininterval / delta_t
                    elif self.smoothing:
                        self.miniters = self.smoothing * delta_it * \
                                        (self.mininterval / delta_t
                                         if self.mininterval and delta_t
                                         else 1) + \
                                        (1 - self.smoothing) * self.miniters
                    else:
                        self.miniters = max(self.miniters, delta_it)

                # EMA rate
                if self.smoothing and delta_t:
                    self.avg_time = delta_t / delta_it \
                        if self.avg_time is None \
                        else self.smoothing * delta_t / delta_it + \
                        (1 - self.smoothing) * self.avg_time

                # Position the cursor
                if self.pos:
                    self.moveto(self.pos)

                # Format and display current bar
                self.sp(self.format_meter(self.n, self.total, cur_t - self.start_t, self.width, self.desc,
                                        self.unit, self.unit_scale,
                                        1 / self.avg_time if self.avg_time
                                        else None))

                # Position the cursor back
                if self.pos:
                    self.moveto(-self.pos)

    def close(self):
        """
        Cleanup at last iteration and (if leave=False) close the progressbar.
        """
        if self.disable:
            return

        pos = self.pos

        # Position cursor
        self.moveto(pos)
        # Leave last bar display?
        if self.leave:
            if self.last_print_n < self.n:
                # Display completed bar
                elapsed = time() - self.start_t
                self.sp(self.format_meter(self.n, self.total, elapsed, self.width, self.desc,
                                        self.unit, self.unit_scale,
                                        1 / self.avg_time if self.avg_time
                                        else None))
            if not pos or pos == 0:
                self.fp.write("\n")
        else:
            # clear up last bar ('\r' + blank fill last string length)
            self.fp.write('')

        # Position cursor back
        self.moveto(-pos)

        # Remove oneself from the list of positions
        tqdm_bare_class._instances.remove(self.pos)


def tbcrange(*args, **kwargs):
    """
    A shortcut for tqdm_bare(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    return tqdm_bare_class(_range(*args), **kwargs)
