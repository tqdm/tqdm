"""
Standalone minimal tqdm but with major features.
For developers porting to other languages or speed freaks.
Includes a default (x)range iterator printing to stderr.

Usage:
  >>> from tqdm import tbrange[, tqdm_bare]
  >>> for i in tbrange(10): #same as: for i in tqdm_bare(xrange(10))
  ...     ...
"""
# future division is important to divide integers and get as
# a result precise floating numbers (instead of truncated int)
from __future__ import division
# import colorama to support move up character in windows term
# can't be included here because conflicts if both tqdm and tqdm_bare imported
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
__all__ = ['tqdm_bare', 'tbrange']


def tqdm_bare(iterable=None, desc=None, total=None, leave=True,
                    file=sys.stdout, width=78, mininterval=0.1,
                    maxinterval=10, miniters=None, disable=False,
                    unit='it', unit_scale=False,
                    smoothing=0.3, initial=0, position=None,
                    **kwargs):
    """
    Minimalist barebone progress bar reproducing tqdm's major features.
    Decorate an iterable object, returning an iterator which acts exactly
    like the original iterable, but prints a dynamically updating
    progressbar every time a value is requested.

    See core tqdm for arguments descriptions.

    STATUS: ALPHA EXPERIMENTAL.
    """
    def format_interval(t):
        mins, s = divmod(int(t), 60)
        h, m = divmod(mins, 60)
        if h:
            return '{0:d}:{1:02d}:{2:02d}'.format(h, m, s)
        else:
            return '{0:02d}:{1:02d}'.format(m, s)

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

    def format_meter(n, total, elapsed, ncols=None, prefix='',
                     unit='it', unit_scale=False, rate=None):
        """
        Return a string-based progress bar given some parameters
        """
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

    def moveto(pos):
        file.write(_unicode('\n' * pos + _term_move_up * -pos))

    def update_and_print(i=1):
        """
        Main function to update bar progress
        """
        n[0] += i
        last_iteration = (n[0] == total) if total else False
        if (n[0] - last_print_n[0]) >= miniters[0] or last_iteration:
            delta_t = time() - last_print_t[0]
            if delta_t >= mininterval or last_iteration:
                cur_t = time()
                delta_it = n[0] - last_print_n[0]
                last_print_t[0] = cur_t
                last_print_n[0] = n[0]

                if dynamic_miniters:
                    if maxinterval and delta_t >= maxinterval and mininterval:
                        # Set miniters to correspond to maxinterval
                        miniters[0] = delta_it * mininterval / delta_t
                    elif smoothing:
                        # EMA-weight miniters to converge
                        # towards the timeframe of mininterval
                        miniters[0] = smoothing * delta_it * \
                                            (mininterval / delta_t
                                             if mininterval and delta_t
                                             else 1) + \
                                            (1 - smoothing) * miniters[0]
                    else:
                        # Maximum nb of iterations between 2 prints
                        miniters[0] = max(miniters[0], delta_it)

                # EMA rate
                if smoothing and delta_t:
                    avg_time[0] = delta_t / delta_it \
                        if avg_time[0] is None \
                        else smoothing * delta_t / delta_it + \
                        (1 - smoothing) * avg_time[0]

                # Format bar
                elapsed = cur_t - start_t
                full_bar = format_meter(n[0], total, elapsed, width, desc,
                                        unit, unit_scale,
                                        1 / avg_time[0] if avg_time[0]
                                        else None)

                # Position the cursor
                if my_pos[0]:
                    moveto(my_pos[0])

                # Clear up previous bar display
                file.write("\r" + (" " * last_len[0]))

                # Display current bar
                file.write("\r" + full_bar)

                # Save current bar size
                last_len[0] = len(full_bar)

                # Leave last bar display?
                if last_iteration:
                    if leave:
                        if not my_pos or my_pos[0] == 0:
                            file.write("\n")
                    else:
                        file.write("\r" + (" " * last_len[0]) + "\r")
                    # Remove oneself from the list of positions
                    tqdm_bare._instances.remove(my_pos[0])

                # Position the cursor back
                if my_pos[0]:
                    moveto(-my_pos[0])

                # Force output the display
                file.flush()

    def update_and_yield():
        """
        Iterable wrapper for update_and_print()
        """
        local_n = n[0]
        local_last_print_n = last_print_n[0]
        local_start_t = start_t
        local_last_print_t = last_print_t[0]
        local_miniters = miniters[0]
        local_mininterval = mininterval
        local_maxinterval = maxinterval
        local_dynamic_miniters = dynamic_miniters
        local_smoothing = smoothing
        local_avg_time = avg_time[0]
        local_total = total
        local_desc = desc
        local_width = width
        local_unit = unit
        local_unit_scale = unit_scale
        local_my_pos = my_pos[0]
        local_last_len = last_len[0]
        for elt in iterable:
            yield elt
            #update_and_print()

            local_n += 1
            #last_iteration = (n[0] == total) if total else False
            if (local_n - local_last_print_n) >= local_miniters:# or last_iteration:
                delta_t = time() - local_last_print_t
                if delta_t >= local_mininterval:# or last_iteration:
                    cur_t = time()
                    delta_it = local_n - local_last_print_n
                    local_last_print_t = cur_t
                    local_last_print_n = local_n

                    if local_dynamic_miniters:
                        if local_maxinterval and delta_t >= local_maxinterval and local_mininterval:
                            # Set miniters to correspond to maxinterval
                            local_miniters = delta_it * local_mininterval / delta_t
                        elif smoothing:
                            # EMA-weight miniters to converge
                            # towards the timeframe of mininterval
                            local_miniters = local_smoothing * delta_it * \
                                                 (local_mininterval / delta_t
                                                 if local_mininterval and delta_t
                                                 else 1) + \
                                                (1 - local_smoothing) * local_miniters
                        else:
                            # Maximum nb of iterations between 2 prints
                            local_miniters = max(local_miniters, delta_it)

                    # EMA rate
                    if local_smoothing and delta_t:
                        local_avg_time = delta_t / delta_it \
                            if local_avg_time is None \
                            else local_smoothing * delta_t / delta_it + \
                            (1 - local_smoothing) * local_avg_time

                    # Format bar
                    elapsed = cur_t - local_start_t
                    full_bar = format_meter(local_n, local_total, elapsed, local_width, local_desc,
                                            local_unit, local_unit_scale,
                                            1 / local_avg_time if local_avg_time
                                            else None)

                    # Position the cursor
                    if local_my_pos:
                        moveto(local_my_pos)

                    # Clear up previous bar display
                    file.write("\r" + (" " * local_last_len))

                    # Display current bar
                    file.write("\r" + full_bar)

                    # Save current bar size
                    local_last_len = len(full_bar)

                    # Position the cursor back
                    if local_my_pos:
                        moveto(-local_my_pos)

                    # Force output the display
                    file.flush()

        # Postprocessing at closing (last iteration)
        moveto(local_my_pos)
        # Print last status
        # Format bar
        cur_t = time()
        elapsed = cur_t - local_start_t
        full_bar = format_meter(local_n, local_total, elapsed, local_width, local_desc,
                                local_unit, local_unit_scale,
                                1 / local_avg_time if local_avg_time
                                else None)
        # Clear up previous bar display
        file.write("\r" + (" " * local_last_len))
        # Display current bar
        file.write("\r" + full_bar)
        # Save current bar size
        local_last_len = len(full_bar)
        # Leave last bar display?
        if leave:
            if not local_my_pos or local_my_pos == 0:
                file.write("\n")
        else:
            file.write("\r" + (" " * local_last_len) + "\r")
        moveto(-local_my_pos)
        # Remove oneself from the list of positions
        tqdm_bare._instances.remove(local_my_pos)


    # -- Initialization
    n = [initial]  # use a closure to store and modify within subfunctions
    start_t = time()  # simple variable enough for access in subfunctions
    last_print_n = [initial]
    last_print_t = [start_t]
    last_len = [0]
    desc = desc + ': ' if desc else ''
    avg_time = [None]

    if miniters is None:
        miniters = [0]
        dynamic_miniters = True
    else:
        miniters = [miniters]
        dynamic_miniters = False

    # Position management
    if not hasattr(tqdm_bare, '_instances'):
        # Create function variable if not existent
        tqdm_bare._instances = set()
    if position is None:
        # Automatic position number generation
        prev_pos = -1  # position just before the hole
        for p in tqdm_bare._instances:
            # If there's a hole between two instances pos, pick this position
            if (p - prev_pos) > 1:
                break
            prev_pos = p
        # Pick next position to the one before the hole
        position = prev_pos+1

    # Assign position to current instance
    my_pos = [position]
    # Store position in the list (just to know which ones are taken)
    tqdm_bare._instances.add(position)

    if iterable is not None:
        total = len(iterable)

    # Initialize the bar display
    if not disable:
        moveto(my_pos[0])
        file.write(format_meter(n[0], total, 0, width, desc, unit, unit_scale))
        moveto(-my_pos[0])
    # -- End of initialization

    # Iterable and manual mode are supported
    if iterable is not None:
        # Iterable mode
        if disable:
            return iterable
        else:
            return update_and_yield()
    else:
        # Manual mode
        if disable:
            return lambda x: x
        else:
            return update_and_print


def tbrange(*args, **kwargs):
    """
    A shortcut for tqdm_bare(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    return tqdm_bare(_range(*args), **kwargs)
