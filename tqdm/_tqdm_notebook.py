"""
IPython/Jupyter Notebook progressbar decorator for iterators.
Includes a default (x)range iterator printing to stderr.

Usage:
  >>> from tqdm_notebook import tnrange[, tqdm_notebook]
  >>> for i in tnrange(10): #same as: for i in tqdm_notebook(xrange(10))
  ...     ...
"""
# future division is important to divide integers and get as
# a result precise floating numbers (instead of truncated int)
from __future__ import division, absolute_import
# import compatibility functions and utilities
import sys
from ._utils import _range
# to inherit from the tqdm class
from ._tqdm import tqdm


if True:  # pragma: no cover
    # import IPython/Jupyter base widget and display utilities
    try:  # IPython 4.x
        import ipywidgets
        IPY = 4
    except ImportError:  # IPython 3.x / 2.x
        IPY = 32
        import warnings
        with warnings.catch_warnings():
            ipy_deprecation_msg = "The `IPython.html` package" \
                                  " has been deprecated"
            warnings.filterwarnings('error',
                                    message=".*" + ipy_deprecation_msg + ".*")
            try:
                import IPython.html.widgets as ipywidgets
            except Warning as e:
                if ipy_deprecation_msg not in str(e):
                    raise
                warnings.simplefilter('ignore')
                try:
                    import IPython.html.widgets as ipywidgets  # NOQA
                except ImportError:
                    pass
            except ImportError:
                pass

    try:  # IPython 4.x / 3.x
        if IPY == 32:
            from IPython.html.widgets import IntProgress, HBox, HTML
            IPY = 3
        else:
            from ipywidgets import IntProgress, HBox, HTML
    except ImportError:
        try:  # IPython 2.x
            from IPython.html.widgets import IntProgressWidget as IntProgress
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
__all__ = ['tqdm_notebook', 'tnrange']


class tqdm_notebook(tqdm):
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
        if total:
            pbar = IntProgress(min=0, max=total)
        else:  # No total? Show info style bar with no progress tqdm status
            pbar = IntProgress(min=0, max=1)
            pbar.value = 1
            pbar.bar_style = 'info'
        if desc:
            pbar.description = desc
        # Prepare status text
        ptext = HTML()
        # Only way to place text to the right of the bar is to use a container
        container = HBox(children=[pbar, ptext])
        # Prepare layout
        if ncols is not None:  # use default style of ipywidgets
            # ncols could be 100, "100px", "100%"
            ncols = str(ncols)  # ipywidgets only accepts string
            if ncols[-1].isnumeric():
                # if last value is digit, assume the value is digit
                ncols += 'px'
            pbar.layout.flex = '2'
            container.layout.width = ncols
            container.layout.display = 'inline-flex'
            container.layout.flex_flow = 'row wrap'
        display(container)

        def print_status(s='', close=False, bar_style=None, desc=None):
            # Note: contrary to native tqdm, s='' does NOT clear bar
            # goal is to keep all infos if error happens so user knows
            # at which iteration the loop failed.

            # Clear previous output (really necessary?)
            # clear_output(wait=1)

            # Get current iteration value from format_meter string
            if total:
                # n = None
                if s:
                    npos = s.find(r'/|/')  # cause we use bar_format=r'{n}|...'
                    # Check that n can be found in s (else n > total)
                    if npos >= 0:
                        n = int(s[:npos])  # get n from string
                        s = s[npos + 3:]  # remove from string

                        # Update bar with current n value
                        if n is not None:
                            pbar.value = n

            # Print stats
            if s:  # never clear the bar (signal: s='')
                s = s.replace('||', '')  # remove inesthetical pipes
                s = escape(s)  # html escape special characters (like '?')
                ptext.value = s

            # Change bar style
            if bar_style:
                # Hack-ish way to avoid the danger bar_style being overriden by
                # success because the bar gets closed after the error...
                if not (pbar.bar_style == 'danger' and bar_style == 'success'):
                    pbar.bar_style = bar_style

            # Special signal to close the bar
            if close and pbar.bar_style != 'danger':  # hide only if no error
                try:
                    container.close()
                except AttributeError:
                    container.visible = False

            # Update description
            if desc:
                pbar.description = desc

        return print_status

    def __init__(self, *args, **kwargs):
        # Setup default output
        if kwargs.get('file', sys.stderr) is sys.stderr:
            kwargs['file'] = sys.stdout  # avoid the red block in IPython

        # Remove the bar from the printed string, only print stats
        if not kwargs.get('bar_format', None):
            kwargs['bar_format'] = r'{n}/|/{l_bar}{r_bar}'

        # Initialize parent class + avoid printing by using gui=True
        kwargs['gui'] = True
        super(tqdm_notebook, self).__init__(*args, **kwargs)
        if self.disable or not kwargs['gui']:
            return

        # Delete first pbar generated from super() (wrong total and text)
        # DEPRECATED by using gui=True
        # self.sp('', close=True)

        # Get bar width
        self.ncols = '100%' if self.dynamic_ncols else kwargs.get("ncols", None)

        # Replace with IPython progress bar display (with correct total)
        self.sp = self.status_printer(
            self.fp, self.total, self.desc, self.ncols)
        self.desc = None  # trick to place description before the bar

        # Print initial bar state
        if not self.disable:
            self.sp(self.__repr__())  # same as self.refresh without clearing

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

    def set_description(self, desc=None, **_):
        """
        Set/modify description of the progress bar.

        Parameters
        ----------
        desc  : str, optional
        """
        self.sp(desc=desc)


def tnrange(*args, **kwargs):
    """
    A shortcut for tqdm_notebook(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    return tqdm_notebook(_range(*args), **kwargs)
