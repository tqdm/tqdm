"""
GUI progressbar decorator for iterators.

Based on the progress_meter module by Michael Lange, Thomas Kluyver,
licensed under MIT: https://bitbucket.org/takluyver/progress_meter

Usage:
  >>> from tqdm_gui import tqdm_gui
  >>> for i in tqdm_gui(range(10)):
  ...     ...
"""
# future division is important to divide integers and get as
# a result precise floating numbers (instead of truncated int)
from __future__ import division, absolute_import

import os
import sys
import pty
from ._tqdm import tqdm

try:
    from tkinter import Tk, Frame, Canvas, Button, READABLE
except ImportError:
    from Tkinter import Tk, Frame, Canvas, Button, READABLE


__author__ = {"github.com/": ["iamale"], "bitbucket.org/": ["takluyver"]}
__all__ = ['tqdm_tk']


class Meter(Frame):
    """
    The Meter class provides a simple progress bar widget for Tkinter.

    INITIALIZATION OPTIONS:
      The widget accepts all options of a Tkinter.Frame plus the following:

      fillcolor -- the color that is used to indicate the progress of the
                   corresponding process; default is "orchid1".
      value -- a float value between 0.0 and 1.0 (corresponding to 0% - 100%)
               that represents the current status of the process; values higher
               than 1.0 (lower than 0.0) are automagically set to 1.0 (0.0);
               default is 0.0 .
      text -- the text that is displayed inside the widget; if set to None
              the widget displays its value as percentage; if you don't want
              any text, use text=""; default is None.
      font -- the font to use for the widget's text; the default is system
              specific.
      textcolor -- the color to use for the widget's text; default is "black".

    WIDGET METHODS:
    All methods of a Tkinter.Frame can be used; additionally there are two
    widget specific methods:

      get() -- returns a tuple of the form (value, text)
      set(value, text) -- updates the widget's value and the displayed text;
                          if value is omitted it defaults to 0.0 , text
                          defaults to None .
    """

    def __init__(self, master, width=300, height=20, bg='white',
                 fillcolor='orchid1', value=0.0, text=None, font=None,
                 textcolor='black', *args, **kw):
        Frame.__init__(self, master, bg=bg, width=width, height=height,
                       *args, **kw)
        self._value = value

        self._canv = Canvas(self, bg=self['bg'], width=self['width'],
                            height=self['height'], highlightthickness=0,
                            relief='flat', bd=0)
        self._canv.pack(fill='both', expand=1)
        self._rect = self._canv.create_rectangle(0, 0, 0,
                                                 self._canv.winfo_reqheight(),
                                                 fill=fillcolor, width=0)
        self._text = self._canv.create_text(self._canv.winfo_reqwidth() / 2,
                                            self._canv.winfo_reqheight() / 2,
                                            text='', fill=textcolor)
        if font:
            self._canv.itemconfigure(self._text, font=font)

        self.set(value, text)
        self.bind('<Configure>', self._update_coords)

    def _update_coords(self, event):
        """
        Updates the position of the text and rectangle inside the canvas
        when the size of the widget gets changed.
        """

        # looks like we have to call update_idletasks() twice to make sure
        # to get the results we expect
        self._canv.update_idletasks()
        self._canv.coords(self._text, self._canv.winfo_width() / 2,
                          self._canv.winfo_height()/2)
        self._canv.coords(self._rect, 0, 0,
                          self._canv.winfo_width() * self._value,
                          self._canv.winfo_height())
        self._canv.update_idletasks()

    def get(self):
        return self._value, self._canv.itemcget(self._text, 'text')

    def set(self, value=0.0, text=None):
        # make the value failsafe:
        if value < 0.0:
            value = 0.0
        elif value > 1.0:
            value = 1.0
        self._value = value
        if text is None:
            # if no text is specified use the default percentage string:
            text = str(int(round(100 * value))) + ' %'
        self._canv.coords(self._rect, 0, 0, self._canv.winfo_width() * value,
                          self._canv.winfo_height())
        self._canv.itemconfigure(self._text, text=text)
        self._canv.update_idletasks()


class MeterWindow(Tk):
    def __init__(self, cancelbutton=False, barcolor="orchid1", **kwargs):
        Tk.__init__(self, **kwargs)
        self.meter = Meter(self, relief='ridge', fillcolor=barcolor, bd=3)
        self.meter.pack(fill='x')
        self.meter.set(0.0)
        if cancelbutton:
            self.cancel = Button(self, text="Cancel")
            self.cancel.pack()


def fork_window(title="Loading...", barcolor="orchid1"):
    """
    Creates a window, returns a function to update percentage.
    """

    pid, fd = pty.fork()
    if pid != 0:
        return lambda value: os.write(fd, (str(value) + "\n").encode())

    # We're in the child process!
    mw = MeterWindow(cancelbutton=False, barcolor=barcolor)
    mw.title(title)
    mw.meter.set(0.0)

    def _step(file, mask):
        line = file.readline().strip()
        if line == "quit":
            mw.quit()
        else:
            mw.meter.set(float(line))

    mw.tk.createfilehandler(sys.stdin, READABLE, _step)
    mw.mainloop()


class tqdm_tk(tqdm):  # pragma: no cover
    """
    Experimental Tk version of tqdm!
    """

    @classmethod
    def write(cls, s, file=sys.stdout, end="\n"):
        """
        Just an alias for print.
        """
        # TODO: print text on GUI?
        file.write(s)
        file.write(end)

    def __init__(self, *args, **kwargs):
        kwargs['gui'] = True
        super(tqdm_tk, self).__init__(*args, **kwargs)

        if self.disable or not kwargs['gui']:
            return

        self.window = fork_window()

    def __iter__(self):
        if self.disable:
            for obj in self.iterable:
                yield obj
            return

        for obj in self.iterable:
            yield obj
            self.n += 1
            self.window(self.n / self.total)

        self.close()

    def update(self, n=1):
        if self.disable:
            return

        if n < 0:
            n = 1
        self.n += n
        self.window(self.n / self.total)

    def close(self):
        if self.disable:
            return

        self.disable = True
        self.window("quit")
