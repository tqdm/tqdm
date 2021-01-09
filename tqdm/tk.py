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
from .std import TqdmExperimentalWarning, TqdmWarning
from .std import tqdm as std_tqdm
# import compatibility functions and utilities
from .utils import _range

__author__ = {"github.com/": ["richardsheridan", "casperdcl"]}
__all__ = ['tqdm_tk', 'ttkrange', 'tqdm', 'trange']


class tqdm_tk(std_tqdm):  # pragma: no cover
    """
    Experimental Tkinter GUI version of tqdm!

    Note: Window interactivity suffers if `tqdm_tk` is not running within
    a Tkinter mainloop and values are generated infrequently. In this case,
    consider calling `tqdm_tk.refresh()` frequently in the Tk thread.
    """

    # TODO: @classmethod: write() on GUI?

    def __init__(self, *args, **kwargs):
        """
        This class accepts the following parameters *in addition* to
        the parameters accepted by tqdm.

        Parameters
        ----------
        grab  : bool, optional
            Grab the input across all windows of the process.
        tk_parent  : tkinter.Wm, optional
            Parent Tk window.
        cancel_callback  : Callable, optional
            Create a cancel button and set cancel_callback to be called
            when the cancel or window close button is clicked.
        """
        # only meaningful to set this warning if someone sets the flag
        self._warn_leave = "leave" in kwargs
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
        kwargs["gui"] = True

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
                tk_parent = tkinter._default_root
            except AttributeError:
                raise ValueError("tk_parent required when using NoDefaultRoot")
            if tk_parent is None:
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

        self._tk_window.protocol("WM_DELETE_WINDOW", self.cancel)
        self._tk_window.wm_title(self.desc)
        self._tk_window.wm_attributes("-topmost", 1)
        self._tk_window.after(
            0,
            lambda: self._tk_window.wm_attributes("-topmost", 0),
        )
        self._tk_n_var = tkinter.DoubleVar(self._tk_window, value=0)
        self._tk_text_var = tkinter.StringVar(self._tk_window)
        pbar_frame = ttk.Frame(self._tk_window, padding=5)
        pbar_frame.pack()
        _tk_label = ttk.Label(
            pbar_frame,
            textvariable=self._tk_text_var,
            wraplength=600,
            anchor="center",
            justify="center",
        )
        _tk_label.pack()
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
            _tk_button = ttk.Button(
                pbar_frame,
                text="Cancel",
                command=self.cancel,
            )
            _tk_button.pack()
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
            Ignored, behaves as if always set True
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
        """Call cancel_callback and then close the progress bar

        Called when the window close or cancel buttons are clicked."""
        if self._cancel_callback is not None:
            self._cancel_callback()
        self.close()

    def reset(self, total=None):
        """
        Resets to 0 iterations for repeated use.

        Parameters
        ----------
        total  : int or float, optional. Total to use for the new bar.
                 If not set, transform progress bar to indeterminate mode.
        """
        if not self.disable:
            if total is None:
                self._tk_pbar.configure(maximum=100, mode="indeterminate")
            else:
                self._tk_pbar.configure(maximum=total, mode="determinate")
        super(tqdm_tk, self).reset(total)

    def close(self):
        if self.disable:
            return

        self.disable = True

        with self.get_lock():
            self._instances.remove(self)

        def _close():
            self._tk_window.after('idle', self._tk_window.destroy)
            if not self._tk_dispatching:
                self._tk_window.update()

        self._tk_window.protocol("WM_DELETE_WINDOW", _close)

        # if leave is set but we are self-dispatching, the left window is
        # totally unresponsive unless the user manually dispatches
        if not self.leave:
            _close()
        elif not self._tk_dispatching:
            if self._warn_leave:
                warn('leave flag ignored if not in tkinter mainloop',
                     TqdmWarning, stacklevel=2)
            _close()

    @staticmethod
    def _tk_dispatching_helper():
        """determine if Tkinter mainloop is dispatching events"""
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
tqdm = tqdm_tk
trange = ttkrange
