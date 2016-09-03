"""
Simple but extremely fast progressbar decorator for iterators.
Includes a default (x)range iterator printing to stderr.

Usage:
  >>> from tqdm import tbrange[, tqdm_bare]
  >>> for i in tbrange(10): #same as: for i in tqdm_bare(xrange(10))
  ...     ...
"""
# future division is important to divide integers and get as
# a result precise floating numbers (instead of truncated int)
from __future__ import division
# import compatibility functions and utilities
import sys
from time import time

try:
    _range = xrange
except:
    _range = range


__author__ = {"github.com/": ["noamraph", "obiwanus", "kmike", "hadim",
                              "casperdcl", "lrq3000"]}
__all__ = ['tqdm_bare', 'tbrange']


def tqdm_bare(iterable=None, total=None, file=sys.stdout, desc='',
                    leave=False, miniters=1, mininterval=0.1, unit='it', width=78):
    """
    Extremely fast barebone progress bar reproducing tqdm's major features.
    Decorate an iterable object, returning an iterator which acts exactly
    like the original iterable, but prints a dynamically updating
    progressbar every time a value is requested.
    STATUS: ALPHA EXPERIMENTAL.
    """
    n = [0]  # use a closure
    start_t = [time()]
    last_n = [0]
    last_t = [0]
    last_len = [0]
    if iterable is not None:
        total = len(iterable)

    def format_interval(t):
        mins, s = divmod(int(t), 60)
        h, m = divmod(mins, 60)
        if h:
            return '{0:d}:{1:02d}:{2:02d}'.format(h, m, s)
        else:
            return '{0:02d}:{1:02d}'.format(m, s)

    def update_and_print(i=1):
        n[0] += i
        if (n[0] - last_n[0]) >= miniters:
            last_n[0] = n[0]

            if (time() - last_t[0]) >= mininterval:
                last_t[0] = time()  # last_t[0] == current time

                spent = last_t[0] - start_t[0]
                spent_fmt = format_interval(spent)
                rate = n[0] / spent if spent > 0 else 0
                if 0.0 < rate < 1.0:
                    rate_fmt = "%.2fs/%s" % (1.0 / rate, unit)
                else:
                    rate_fmt = "%.2f%s/s" % (rate, unit)

                if total:
                    frac = n[0] / total
                    percentage = int(frac * 100)
                    #eta = spent / n[0] * total if n[0] else 0
                    eta = (total - n[0]) / rate if rate > 0 else 0
                    eta_fmt = format_interval(eta)

                    l_bar = "%s: %i%%|" % (desc, percentage)
                    r_bar = "|%i/%i [%s<%s, %s]" % (n[0],
                                  total, spent_fmt, eta_fmt, rate_fmt)
                    bar_width = width - len(l_bar) - len(r_bar)

                    bar = "#" * int(frac * bar_width)
                    barfill = " " * int((1.0 - frac) * bar_width)
                    bar_length, frac_bar_length = divmod(
                        int(frac * bar_width * 10), 10)
                    bar = '#' * bar_length
                    frac_bar = chr(48 + frac_bar_length) if frac_bar_length \
                        else ' '

                    # Build complete bar
                    full_bar = l_bar + bar + frac_bar + barfill + r_bar

                else:
                    full_bar = "{0}: {1}{2} [{3}, {4}]".format(desc, n[0], unit, spent_fmt, rate_fmt)

                # Clear up previous bar display
                file.write("\r" + (" " * last_len[0]))

                # Display current bar
                file.write("\r" + full_bar)

                # Save current bar size
                last_len[0] = len(full_bar)

                # Leave last bar display?
                if n[0] == total:
                    if leave:
                        file.write("\n")
                    else:
                        file.write("\r" + (" " * last_len[0]) + "\r")

                file.flush()

    def update_and_yield():
        for elt in iterable:
            yield elt
            update_and_print()

    # Initialize the bar display
    update_and_print(0)

    # Iterable and manual mode are supported
    if iterable is not None:
        return update_and_yield()
    else:
        return update_and_print


def tbrange(*args, **kwargs):
    """
    A shortcut for tqdm_bare(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    return tqdm_bare(_range(*args), **kwargs)
