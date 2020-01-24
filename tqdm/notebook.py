"""
IPython/Jupyter Notebook progressbar decorator for iterators.
Includes a default (x)range iterator printing to stderr.

Usage:
  >>> from tqdm.notebook import trange[, tqdm]
  >>> for i in trange(10): #same as: for i in tqdm(xrange(10))
  ...     ...
"""
# future division is important to divide integers and get as
# a result precise floating numbers (instead of truncated int)
from __future__ import division, absolute_import
# import compatibility functions and utilities
import sys
from .utils import _range
# to inherit from the tqdm class
from .std import tqdm as std_tqdm


if True:  # pragma: no cover
    # import IPython/Jupyter base widget and display utilities
    IPY = 0
    IPYW = 0
    try:  # IPython 4.x
        import ipywidgets
        IPY = 4
        try:
            IPYW = int(ipywidgets.__version__.split('.')[0])
        except AttributeError:  # __version__ may not exist in old versions
            pass
    except ImportError:  # IPython 3.x / 2.x
        IPY = 32
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings(
                'ignore',
                message=".*The `IPython.html` package has been deprecated.*")
            try:
                import IPython.html.widgets as ipywidgets
            except ImportError:
                pass

    try:  # IPython 4.x / 3.x
        if IPY == 32:
            from IPython.html.widgets import FloatProgress as IProgress
            from IPython.html.widgets import HBox, HTML
            IPY = 3
        else:
            from ipywidgets import FloatProgress as IProgress
            from ipywidgets import HBox, HTML
    except ImportError:
        try:  # IPython 2.x
            from IPython.html.widgets import FloatProgressWidget as IProgress
            from IPython.html.widgets import ContainerWidget as HBox
            from IPython.html.widgets import HTML
            IPY = 2
        except ImportError:
            IPY = 0

    try:
        from IPython.display import display  # , clear_output
    except ImportError:
        pass

    # HTML encoding
    try:  # Py3
        from html import escape
    except ImportError:  # Py2
        from cgi import escape


__author__ = {"github.com/": ["lrq3000", "casperdcl", "alexanderkuk"]}
__all__ = ['tqdm_notebook', 'tnrange', 'tqdm', 'trange']


class tqdm_notebook(std_tqdm):
    """
    Experimental IPython/Jupyter Notebook widget using tqdm!
    """

    @staticmethod
    def status_printer(_, total=None, desc=None, ncols=None):
        """
        Manage the printing of an IPython/Jupyter Notebook progress bar widget.
        """
        # Fallback to text bar if there's no total
        # DEPRECATED: replaced with an 'info' style bar
        # if not total:
        #    return super(tqdm_notebook, tqdm_notebook).status_printer(file)

        # fp = file

        # Prepare IPython progress bar
        try:
            if total:
                pbar = IProgress(min=0, max=total)
            else:  # No total? Show info style bar with no progress tqdm status
                pbar = IProgress(min=0, max=1)
                pbar.value = 1
                pbar.bar_style = 'info'
        except NameError:
            # #187 #451 #558
            raise ImportError(
                "FloatProgress not found. Please update jupyter and ipywidgets."
                " See https://ipywidgets.readthedocs.io/en/stable"
                "/user_install.html")

        if desc:
            pbar.description = desc
            if IPYW >= 7:
                pbar.style.description_width = 'initial'
        # Prepare status text
        ptext = HTML()
        # Only way to place text to the right of the bar is to use a container
        container = HBox(children=[pbar, ptext])
        # Prepare layout
        if ncols is not None:  # use default style of ipywidgets
            # ncols could be 100, "100px", "100%"
            ncols = str(ncols)  # ipywidgets only accepts string
            try:
                if int(ncols) > 0:  # isnumeric and positive
                    ncols += 'px'
            except ValueError:
                pass
            pbar.layout.flex = '2'
            container.layout.width = ncols
            container.layout.display = 'inline-flex'
            container.layout.flex_flow = 'row wrap'
        display(container)

        return container

    def display(self, msg=None, pos=None,
                # additional signals
                close=False, bar_style=None):
        # Note: contrary to native tqdm, msg='' does NOT clear bar
        # goal is to keep all infos if error happens so user knows
        # at which iteration the loop failed.

        # Clear previous output (really necessary?)
        # clear_output(wait=1)

        if not msg and not close:
            msg = self.__repr__()

        pbar, ptext = self.container.children
        pbar.value = self.n

        if msg:
            # html escape special characters (like '&')
            if '<bar/>' in msg:
                left, right = map(escape, msg.split('<bar/>', 1))
            else:
                left, right = '', escape(msg)

            # remove inesthetical pipes
            if left and left[-1] == '|':
                left = left[:-1]
            if right and right[0] == '|':
                right = right[1:]

            # Update description
            pbar.description = left
            if IPYW >= 7:
                pbar.style.description_width = 'initial'

            # never clear the bar (signal: msg='')
            if right:
                ptext.value = right

        # Change bar style
        if bar_style:
            # Hack-ish way to avoid the danger bar_style being overridden by
            # success because the bar gets closed after the error...
            if not (pbar.bar_style == 'danger' and bar_style == 'success'):
                pbar.bar_style = bar_style

        # Special signal to close the bar
        if close and pbar.bar_style != 'danger':  # hide only if no error
            try:
                self.container.close()
            except AttributeError:
                self.container.visible = False

    def __init__(self, *args, **kwargs):
        # Setup default output
        file_kwarg = kwargs.get('file', sys.stderr)
        if file_kwarg is sys.stderr or file_kwarg is None:
            kwargs['file'] = sys.stdout  # avoid the red block in IPython

        # Initialize parent class + avoid printing by using gui=True
        kwargs['gui'] = True
        kwargs.setdefault('bar_format', '{l_bar}{bar}{r_bar}')
        kwargs['bar_format'] = kwargs['bar_format'].replace('{bar}', '<bar/>')
        # convert disable = None to False
        kwargs['disable'] = bool(kwargs.get('disable', False))
        super(tqdm_notebook, self).__init__(*args, **kwargs)
        if self.disable or not kwargs['gui']:
            return

        # Get bar width
        self.ncols = '100%' if self.dynamic_ncols else kwargs.get("ncols", None)

        # Replace with IPython progress bar display (with correct total)
        unit_scale = 1 if self.unit_scale is True else self.unit_scale or 1
        total = self.total * unit_scale if self.total else self.total
        self.container = self.status_printer(
            self.fp, total, self.desc, self.ncols)
        self.sp = self.display

        # Print initial bar state
        if not self.disable:
            self.display()

    def __iter__(self, *args, **kwargs):
        try:
            for obj in super(tqdm_notebook, self).__iter__(*args, **kwargs):
                # return super(tqdm...) will not catch exception
                yield obj
        # NB: except ... [ as ...] breaks IPython async KeyboardInterrupt
        except:  # NOQA
            self.sp(bar_style='danger')
            raise

    def update(self, *args, **kwargs):
        try:
            super(tqdm_notebook, self).update(*args, **kwargs)
        except Exception as exc:
            # cannot catch KeyboardInterrupt when using manual tqdm
            # as the interrupt will most likely happen on another statement
            self.sp(bar_style='danger')
            raise exc

    def close(self, *args, **kwargs):
        super(tqdm_notebook, self).close(*args, **kwargs)
        # If it was not run in a notebook, sp is not assigned, check for it
        if hasattr(self, 'sp'):
            # Try to detect if there was an error or KeyboardInterrupt
            # in manual mode: if n < total, things probably got wrong
            if self.total and self.n < self.total:
                self.sp(bar_style='danger')
            else:
                if self.leave:
                    self.sp(bar_style='success')
                else:
                    self.sp(close=True)

    def moveto(self, *args, **kwargs):
        # void -> avoid extraneous `\n` in IPython output cell
        return

    def reset(self, total=None):
        """
        Resets to 0 iterations for repeated use.

        Consider combining with `leave=True`.

        Parameters
        ----------
        total  : int or float, optional. Total to use for the new bar.
        """
        if total is not None:
            pbar, _ = self.container.children
            pbar.max = total
        return super(tqdm_notebook, self).reset(total=total)


def tnrange(*args, **kwargs):
    """
    A shortcut for `tqdm.notebook.tqdm(xrange(*args), **kwargs)`.
    On Python3+, `range` is used instead of `xrange`.
    """
    return tqdm_notebook(_range(*args), **kwargs)


# Aliases
tqdm = tqdm_notebook
trange = tnrange
