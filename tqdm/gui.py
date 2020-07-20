"""
GUI progressbar decorator for iterators.
Includes a default `range` iterator printing to `stderr`.

Usage:
>>> from tqdm.gui import trange, tqdm
>>> for i in trange(10):
...     ...
"""
# future division is important to divide integers and get as
# a result precise floating numbers (instead of truncated int)
from __future__ import absolute_import, division

from warnings import warn

# to inherit from the tqdm class
from .std import TqdmExperimentalWarning
from .std import tqdm as std_tqdm
# import compatibility functions and utilities
from .utils import _range

__author__ = {"github.com/": ["casperdcl", "lrq3000", "richardsheridan"]}
__all__ = ['tqdm_gui', 'tgrange', 'tqdm_tk', 'ttkrange', 'tqdm', 'trange']


class tqdm_gui(std_tqdm):  # pragma: no cover
    """
    Experimental GUI version of tqdm!
    """

    # TODO: @classmethod: write() on GUI?

    def __init__(self, *args, **kwargs):
        from collections import deque

        import matplotlib as mpl
        import matplotlib.pyplot as plt
        kwargs = kwargs.copy()
        kwargs['gui'] = True
        colour = kwargs.pop('colour', 'g')
        super(tqdm_gui, self).__init__(*args, **kwargs)

        # Initialize the GUI display
        if self.disable or not kwargs['gui']:
            return

        warn('GUI is experimental/alpha', TqdmExperimentalWarning, stacklevel=2)
        self.mpl = mpl
        self.plt = plt

        # Remember if external environment uses toolbars
        self.toolbar = self.mpl.rcParams['toolbar']
        self.mpl.rcParams['toolbar'] = 'None'

        self.mininterval = max(self.mininterval, 0.5)
        self.fig, ax = plt.subplots(figsize=(9, 2.2))
        # self.fig.subplots_adjust(bottom=0.2)
        total = self.__len__()  # avoids TypeError on None #971
        if total is not None:
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
        if total is not None:
            ax.set_xlim(0, 100)
            ax.set_xlabel('percent')
            self.fig.legend((self.line1, self.line2), ('cur', 'est'),
                            loc='center right')
            # progressbar
            self.hspan = plt.axhspan(0, 0.001, xmin=0, xmax=0, color=colour)
        else:
            # ax.set_xlim(-60, 0)
            ax.set_xlim(0, 60)
            ax.invert_xaxis()
            ax.set_xlabel('seconds')
            ax.legend(('cur', 'est'), loc='lower left')
        ax.grid()
        # ax.set_xlabel('seconds')
        ax.set_ylabel((self.unit if self.unit else 'it') + '/s')
        if self.unit_scale:
            plt.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
            ax.yaxis.get_offset_text().set_x(-0.15)

        # Remember if external environment is interactive
        self.wasion = plt.isinteractive()
        plt.ion()
        self.ax = ax

    def close(self):
        # if not self.gui:
        #   return super(tqdm_gui, self).close()
        if self.disable:
            return

        self.disable = True

        with self.get_lock():
            self._instances.remove(self)

        # Restore toolbars
        self.mpl.rcParams['toolbar'] = self.toolbar
        # Return to non-interactive mode
        if not self.wasion:
            self.plt.ioff()
        if self.leave:
            self.display()
        else:
            self.plt.close(self.fig)

    def clear(self, *_, **__):
        pass

    def display(self):
        n = self.n
        cur_t = self._time()
        elapsed = cur_t - self.start_t
        delta_it = n - self.last_print_n
        delta_t = cur_t - self.last_print_t

        # Inline due to multiple calls
        total = self.total
        xdata = self.xdata
        ydata = self.ydata
        zdata = self.zdata
        ax = self.ax
        line1 = self.line1
        line2 = self.line2
        # instantaneous rate
        y = delta_it / delta_t
        # overall rate
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
                self.hspan = self.plt.axhspan(0, 0.001, xmin=0, xmax=0, color='g')
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

        d = self.format_dict
        d["ncols"] = 0
        ax.set_title(self.format_meter(**d), fontname="DejaVu Sans Mono", fontsize=11)
        self.plt.pause(1e-9)


def tgrange(*args, **kwargs):
    """
    A shortcut for `tqdm.gui.tqdm(xrange(*args), **kwargs)`.
    On Python3+, `range` is used instead of `xrange`.
    """
    return tqdm_gui(_range(*args), **kwargs)


class tqdm_tk(std_tqdm):
    """
    Experimental Tkinter GUI version of tqdm!
    """

    def __init__(self, *args, **kwargs):
        try:
            grab = kwargs.pop("grab")
        except KeyError:
            grab = False
        try:
            tk_parent = kwargs.pop("tk_parent")
        except KeyError:
            tk_parent = None
        try:
            self._cancel_callback = kwargs.pop("cancel_callback")
        except KeyError:
            self._cancel_callback = None
        try:
            bar_format = kwargs.pop("bar_format")
        except KeyError:
            bar_format = None

        kwargs["gui"] = True

        # Tkinter specific default bar format
        if bar_format is None:
            kwargs["bar_format"] = (
                "{n_fmt}/{total_fmt}, {rate_noinv_fmt}\n"
                "{elapsed} elapsed, {remaining} ETA\n\n"
                "{percentage:3.0f}%"
            )

        # This signals std_tqdm that it's a GUI but no need to crash
        # Maybe there is a better way?
        self.sp = object()

        super(tqdm_tk, self).__init__(*args, **kwargs)

        if self.disable:
            return

        try:
            import tkinter
            import tkinter.ttk as ttk
        except ImportError:
            import Tkinter as tkinter
            import ttk as ttk

        # Discover parent widget
        if tk_parent is None:
            # this will error if tkinter.NoDefaultRoot() called
            try:
                tkparent = tkinter._default_root
            except AttributeError:
                raise ValueError("tk_parent required when using NoDefaultRoot")
            if tkparent is None:
                # use new default root window as display
                self._tk_window = tkinter.Tk()
            else:
                # some other windows already exist
                self._tk_window = tkinter.Toplevel()
        else:
            self._tk_window = tkinter.Toplevel(tk_parent)

        warn('GUI is experimental/alpha', TqdmExperimentalWarning, stacklevel=2
             )
        self._tk_dispatching = self._tk_dispatching_helper()
        if not self._tk_dispatching:
            # leave is problematic if the mainloop is not running
            self.leave = False

        self._tk_window.protocol("WM_DELETE_WINDOW", self.cancel)
        self._tk_window.wm_title(self.desc)
        self._tk_window.wm_attributes("-topmost", 1)
        self._tk_window.after(
            0,
            lambda: self._tk_window.wm_attributes("-topmost", 0),
        )
        self._tk_n_var = tkinter.DoubleVar(self._tk_window, value=0)
        self._tk_desc_var = tkinter.StringVar(self._tk_window)
        self._tk_desc_var.set(self.desc)
        self._tk_text_var = tkinter.StringVar(self._tk_window)
        pbar_frame = ttk.Frame(self._tk_window, padding=5)
        pbar_frame.pack()
        self._tk_desc_frame = ttk.Frame(pbar_frame)
        self._tk_desc_frame.pack()
        self._tk_desc_var.set(self.desc)
        self._tk_label = ttk.Label(
            pbar_frame,
            textvariable=self._tk_text_var,
            wraplength=600,
            anchor="center",
            justify="center",
        )
        self._tk_label.pack()
        self._tk_pbar = ttk.Progressbar(
            pbar_frame,
            variable=self._tk_n_var,
            length=450,
        )
        if self.total is not None:
            self._tk_pbar.configure(maximum=self.total)
        else:
            self._tk_pbar.configure(mode="indeterminate")
        self._tk_pbar.pack()
        if self._cancel_callback is not None:
            self._tk_button = ttk.Button(
                pbar_frame,
                text="Cancel",
                command=self.cancel,
            )
            self._tk_button.pack()
        if grab:
            self._tk_window.grab_set()

    def set_description(self, desc=None, refresh=True):
        self.set_description_str(desc, refresh)

    def set_description_str(self, desc=None, refresh=True):
        self.desc = desc
        if not self.disable:
            self._tk_window.wm_title(desc)
            if refresh and not self._tk_dispatching:
                self._tk_window.update()

    def refresh(self, nolock=True, lock_args=None):
        """
        Force refresh the display of this bar.

        Parameters
        ----------
        nolock  : bool, optional
            Ignored, behaves as if always set true
        lock_args  : tuple, optional
            Ignored
        """
        nolock = True  # necessary to force true or is default true enough?
        return super(tqdm_tk, self).refresh(nolock, lock_args)

    def display(self):
        self._tk_n_var.set(self.n)
        self._tk_text_var.set(
            self.format_meter(
                n=self.n,
                total=self.total,
                elapsed=self._time() - self.start_t,
                ncols=None,
                prefix=self.desc,
                ascii=self.ascii,
                unit=self.unit,
                unit_scale=self.unit_scale,
                rate=1 / self.avg_time if self.avg_time else None,
                bar_format=self.bar_format,
                postfix=self.postfix,
                unit_divisor=self.unit_divisor,
            )
        )
        if not self._tk_dispatching:
            self._tk_window.update()

    def cancel(self):
        """Call cancel_callback and close the progress bar"""
        if self._cancel_callback is not None:
            self._cancel_callback()
        self.close()

    def reset(self, total=None):
        if total is not None and not self.disable:
            self._tk_pbar.configure(maximum=total)
        super(tqdm_tk, self).reset(total)

    def close(self):
        if self.disable:
            return

        self.disable = True

        with self.get_lock():
            self._instances.remove(self)

        def _close():
            self._tk_window.after(0, self._tk_window.destroy)
            if not self._tk_dispatching:
                self._tk_window.update()

        self._tk_window.protocol("WM_DELETE_WINDOW", _close)
        if not self.leave:
            _close()

    def _tk_dispatching_helper(self):
        """determine if Tkinter mainloop is dispatching events"""
        try:
            # Landing in CPython 3.10
            return self._tk_window.dispatching()
        except AttributeError:
            pass

        try:
            import tkinter
        except ImportError:
            import Tkinter as tkinter
        import sys

        codes = set((tkinter.mainloop.__code__,
                     tkinter.Misc.mainloop.__code__))
        for frame in sys._current_frames().values():
            while frame:
                if frame.f_code in codes:
                    return True
                frame = frame.f_back
        return False


def ttkrange(*args, **kwargs):
    """
    A shortcut for `tqdm.gui.tqdm_tk(xrange(*args), **kwargs)`.
    On Python3+, `range` is used instead of `xrange`.
    """
    return tqdm_tk(_range(*args), **kwargs)


# Aliases
tqdm = tqdm_gui
trange = tgrange
