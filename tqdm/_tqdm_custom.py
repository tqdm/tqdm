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
import string
import sys

from ._utils import _range
# to inherit from the tqdm class
from ._tqdm import tqdm


__author__ = {"github.com/": ["lrq3000"]}
__all__ = ['tqdm_custom', 'tcrange']


# Characters mirror translation table
_mirror_in = '()<>[]\/{}bd'
_mirror_out = ')(><][/\}{db'

def mirror_line(s):
    """Mirror a line and its characters using translation"""
    global _mirror_in, _mirror_out
    s2 = s[::-1]
    trans = string.maketrans(_mirror_in, _mirror_out)
    return s2.translate(trans)


class tqdm_custom(tqdm):
    """
    tqdm with nice customizable bar symbols!
    """
    def format_meter(self, n, total, elapsed, ncols=None, prefix='',
                     ascii=False, unit='it', unit_scale=False, rate=None,
                     bar_format=None):
        """
        Return a string-based progress bar given some parameters

        Parameters
        ----------
        same as core tqdm.

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

        # No custom symbol (bar_format is not a dict), just call super
        if not bar_format or \
         bar_format and isinstance(bar_format, basestring):
            return super(tqdm_custom, self).format_meter(n, total, elapsed, ncols,
                     prefix, ascii, unit, unit_scale, rate, bar_format)

        # Custom symbols!
        else:
            # Unpack variables if it's a list
            if isinstance(bar_format, dict):
                bar_template = bar_format.get('template', None)
            else:
                bar_template = bar_format

            # Preprocess and generate bar arguments using super
            bar_args = super(tqdm_custom, self).format_meter(n, total, elapsed,
                         ncols, prefix, ascii, unit, unit_scale, rate,
                         bar_format=True)

            # Format bar using the template
            if bar_template:
                bar_args['bar'] = '{bar}'  # trick to format all except bar
                full_bar = bar_template.format(**bar_args)
                l_bar, r_bar = full_bar.split('{bar}')
            else:
                l_bar, r_bar = bar_args['l_bar'], bar_args['r_bar']

            custom_symbols = None

            # total is known: we can predict some stats
            if total:
                frac = bar_args['frac']
                percentage = bar_args['percentage']

                remaining_str = bar_args['remaining']

                N_BARS = bar_args['n_bars']

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
                        # increment one step in the animation for each display
                        self.n_anim += 1
                        # get the symbol for current animation step
                        bar = c_symb[divmod(self.n_anim, len(c_symb))[1]]
                        frac_bar = ''

                        bar_length = N_BARS  # avoid the filling
                        frac_bar_length = len(frac_bar)
                    # normal progress symbols
                    else:
                        nb_symb = len(c_symb)
                        len_filler = len(c_symb[-1])
                        bar_length, frac_bar_length = divmod(
                            int(frac * int(N_BARS/len_filler) * nb_symb), nb_symb)

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
                N_BARS = bar_args['n_bars']

                # Custom symbols!
                # get ascii or unicode template
                if ascii:
                    c_symb = bar_format['symbols_indeterminate'].get('ascii', ["====="])
                    c_symb_rev = bar_format['symbols_indeterminate'].get('ascii_rev', c_symb)
                else:
                    c_symb = bar_format['symbols_indeterminate'].get('unicode', ["====="])
                    c_symb_rev = bar_format['symbols_indeterminate'].get('unicode_rev', c_symb)
                # looping symbols: just update the symbol animation at each iteration
                if bar_format['symbols_indeterminate'].get('loop', False):
                    # increment one step in the animation for each display
                    self.n_anim += 1
                    # Get current bar animation
                    bar = c_symb[divmod(self.n_anim, len(c_symb))[1]]

                    bar_length = N_BARS  # avoid the filling
                # indeterminate progress bar (cycle from left to right then right to left)
                else:
                    # increment one step in the animation for each display
                    self.n_anim += 1
                    # Get current bar animation
                    symbol_idx = divmod(self.n_anim, len(c_symb))[1]
                    bar = c_symb[symbol_idx]
                    # Get left filling space and animation step (right pass or left?)
                    anim_step, fill_left = divmod(self.n_anim, (N_BARS - len(bar)))
                    # If anim_step is odd, then we do left pass (2nd pass)
                    if divmod(anim_step, 2)[1] == 1:
                        # Inverse the left filling space (now it's the right space)
                        fill_left = N_BARS - len(bar) - fill_left
                        # Get the reversed symbol
                        bar = c_symb_rev[symbol_idx]

                    # Generate bar with left filling space
                    bar = ' ' * fill_left + bar
                    bar_length = len(bar)

                # Right space padding
                full_bar = bar + \
                    ' ' * max(N_BARS - bar_length, 0)

                # Piece together the bar parts
                return l_bar + full_bar + r_bar

    def __init__(self, *args, **kwargs):
        """
        mininterval:  float, optional
            Controls display refresh rate just like for core tqdm,
            but in addition also controls looping symbols animation speed
            (except if miniters is set, then miniters controls the animation).
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
        self.n_anim = 0  # animation step for looping symbols

        # Preprocess symbols
        for key in self.bar_format.keys():
            if not isinstance(self.bar_format[key], dict):
                continue
            # Precompute reverse strings (if not provided) for loop symbol
            for type, type_rev in [('ascii','ascii_rev'), ('unicode', 'unicode_rev')]:
                entry = self.bar_format[key].get(type, None)
                entry_rev = self.bar_format[key].get(type_rev, None)
                # If type (ascii or unicode) exists but not the reversed
                if entry and not entry_rev:
                    # Then reverse each symbol
                    p_symb = []
                    for symb in entry:
                        p_symb.append( mirror_line(symb) )
                    # And store the reversed symbols
                    self.bar_format[key][type_rev] = p_symb


def tcrange(*args, **kwargs):
    """
    A shortcut for tqdm_custom(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    return tqdm_custom(_range(*args), **kwargs)
