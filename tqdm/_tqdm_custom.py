"""
Customisable progressbar decorator for iterators.
Includes a default (x)range iterator printing to stderr.

Usage:
  >>> from tqdm import trange[, tqdm]
  >>> for i in trange(10): #same as: for i in tqdm(xrange(10))
  ...     ...
"""
from __future__ import absolute_import, division
# import compatibility functions and utilities
from ._utils import _supports_unicode, _environ_cols_wrapper, _range, _unich, \
    _unicode
import sys

from ._utils import _range
# to inherit from the tqdm class
from ._tqdm import tqdm


__author__ = {"github.com/": ["lrq3000"]}
__all__ = ['tqdm_custom', 'tcrange']


class tqdm_custom(tqdm):
    """
    tqdm with nice customizable bar symbols!
    """
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
        bar_format  : str/list, optional
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

        custom_symbols = None

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
                # Unpack variables if it's a list
                if isinstance(bar_format, dict):
                    bar_format_template = bar_format.get('template', None)
                else:
                    bar_format_template = bar_format

                if bar_format_template:
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
                    if '{bar}' in bar_format_template:
                        # Format left/right sides of the bar, and format the bar
                        # later in the remaining space (avoid breaking display)
                        l_bar_user, r_bar_user = bar_format_template.split('{bar}')
                        l_bar = l_bar_user.format(**bar_args)
                        r_bar = r_bar_user.format(**bar_args)
                    else:
                        # Else no progress bar, we can just format and return
                        return bar_format_template.format(**bar_args)

            # Formatting progress bar
            # space available for bar's display
            N_BARS = max(1, ncols - len(l_bar) - len(r_bar)) if ncols \
                else 10

            # custom symbols format
            # need to provide both ascii and unicode versions of custom symbols
            if bar_format and isinstance(bar_format, dict):
                # get ascii or unicode template
                if ascii:
                    c_symb = bar_format['symbols'].get('ascii', list("123456789#"))
                else:
                    c_symb = bar_format['symbols'].get('unicode', map(_unich, range(0x258F, 0x2587, -1)))
                # looping symbols: just update the symbol animation at each iteration
                if bar_format['symbols'].get('loop', False):
                    # increment one step in the animation at each step
                    bar = c_symb[divmod(n, len(c_symb))[1]]
                    frac_bar = ''

                    bar_length = N_BARS  # avoid the filling
                    frac_bar_length = len(frac_bar)
                # normal progress symbols
                else:
                    nb_symb = len(c_symb)
                    len_filler = len(c_symb[-1])
                    bar_length, frac_bar_length = divmod(
                        int((frac/len_filler) * N_BARS * nb_symb), nb_symb)

                    bar = c_symb[-1] * bar_length  # last symbol is always the filler
                    frac_bar = c_symb[frac_bar_length] if frac_bar_length \
                        else ' '
                    # update real bar length (if symbols > 1 char) for correct filler
                    bar_length = bar_length * len_filler

            # ascii format
            elif ascii:
                # get the remainder of the division of current fraction with number of symbols
                # this will tell us which symbol we should pick
                bar_length, frac_bar_length = divmod(
                    int(frac * N_BARS * 10), 10)

                bar = '#' * bar_length
                frac_bar = chr(48 + frac_bar_length) if frac_bar_length \
                    else ' '

            # unicode format (if available)
            else:
                bar_length, frac_bar_length = divmod(int(frac * N_BARS * 8), 8)

                bar = _unich(0x2588) * bar_length
                frac_bar = _unich(0x2590 - frac_bar_length) \
                    if frac_bar_length else ' '

            # whitespace padding
            if bar_length < N_BARS:
                full_bar = bar + frac_bar + \
                    ' ' * max(N_BARS - bar_length - len(frac_bar), 0)
            else:
                full_bar = bar + \
                    ' ' * max(N_BARS - bar_length, 0)

            # Piece together the bar parts
            return l_bar + full_bar + r_bar

        # no total: no progressbar, ETA, just progress stats
        else:
            return (prefix if prefix else '') + '{0}{1} [{2}, {3}]'.format(
                n_fmt, unit, elapsed_str, rate_fmt)

    def __init__(self, *args, **kwargs):
        """
        bar_format:  str/dict, optional
        Can either be a string, or a dict for more complex templating.
        Format: {'template': '{l_bar}{bar}{r_bar}',
                     'symbols': {'unicode': ['1', '2', '3', '4', '5', '6'],
                                     'ascii': ['1', '2', '3'],
                                     'loop': False}
                     'symbols_indeterminate': {'unicode': ....
                     }
        """
        # get bar_format
        bar_format = kwargs.get('bar_format', None)
        
        if bar_format and isinstance(bar_format, dict):
            kwargs['bar_format'] = bar_format.get('template', None)

        # Do rest of init with cleaned up bar_format
        super(tqdm_custom, self).__init__(*args, **kwargs)

        # Store the arguments
        bar_format['template'] = self.bar_format
        self.bar_format = bar_format


def tcrange(*args, **kwargs):
    """
    A shortcut for tqdm_custom(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    return tqdm_custom(_range(*args), **kwargs)
