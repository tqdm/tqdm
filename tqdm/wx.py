"""
WX progressbar decorator for iterators.

Usage:
>>> from tqdm.wx import trange, tqdm
>>> for i in trange(10, parent=wx.Panel()):
...     ...
"""
from __future__ import absolute_import, division

import re
from warnings import warn

import wx

from .std import TqdmExperimentalWarning
from .std import tqdm as std_tqdm
from .utils import _range

__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['tqdm_wx', 'twrange', 'tqdm', 'trange']


class tqdm_wx(std_tqdm):  # pragma: no cover
    """
    Experimental WX version of tqdm!
    """

    # TODO: @classmethod: write() on GUI?

    def __init__(self, *args, **kwargs):
        kwargs = kwargs.copy()
        parent = kwargs.pop('parent')
        kwargs['gui'] = True
        colour = wx.Colour(kwargs.pop('colour', 'black'))
        super(tqdm_wx, self).__init__(*args, **kwargs)

        if self.disable:
            return

        warn("WX is experimental/alpha", TqdmExperimentalWarning, stacklevel=2)
        self.panel = pnl = wx.Panel(parent)
        pnl.SetForegroundColour(colour)
        left = wx.StaticText(pnl)
        gauge = wx.Gauge(pnl, range=self.__len__() or 100)
        right = wx.StaticText(pnl)

        sizer = wx.BoxSizer()
        sizer.Add(left)
        sizer.Add(gauge)
        sizer.Add(right)
        pnl.SetSizer(sizer)
        self.container = left, gauge, right
        self.display()

    def close(self):
        if self.disable:
            return

        self.disable = True

        with self.get_lock():
            self._instances.remove(self)

        if self.leave:
            self.display()

    def clear(self, *_, **__):
        pass

    def display(self, *_, **__):
        d = self.format_dict
        # remove {bar}
        d['bar_format'] = (d['bar_format'] or "{l_bar}<bar/>{r_bar}").replace(
            "{bar}", "<bar/>")
        msg = self.format_meter(**d)
        _left, gauge, _right = self.container
        if '<bar/>' in msg:
            left, right = re.split(r'\|?<bar/>\|?', msg, 1)
            if self.__len__():
                gauge.SetValue(self.n)
            else:
                gauge.Pulse()
        else:
            left, right = msg, ""
        _left.SetLabel(left)
        _right.SetLabel(right)
        self.panel.Fit()

    def reset(self, total=None):
        """
        Resets to 0 iterations for repeated use.

        Consider combining with `leave=True`.

        Parameters
        ----------
        total  : int or float, optional. Total to use for the new bar.
        """
        if self.disable:
            return super(tqdm_wx, self).reset(total=total)
        if total is not None:
            self.container[1].SetRange(total)
        return super(tqdm_wx, self).reset(total=total)


def twrange(*args, **kwargs):
    """
    A shortcut for `tqdm.wx.tqdm(xrange(*args), **kwargs)`.
    On Python3+, `range` is used instead of `xrange`.
    """
    return tqdm_wx(_range(*args), **kwargs)


# Aliases
tqdm = tqdm_wx
trange = twrange
