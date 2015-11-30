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
# import IPython/Jupyter base widget and display utilities
try:  # pragma: no cover
    # For IPython 4.x using ipywidgets
    from ipywidgets import IntProgress, HBox, HTML
except ImportError:  # pragma: no cover
    try:  # pragma: no cover
        # For IPython 3.x
        from IPython.html.widgets import IntProgress, HBox, HTML
    except ImportError:  # pragma: no cover
        try:  # pragma: no cover
            # For IPython 2.x
            from IPython.html.widgets import IntProgressWidget as IntProgress
            from IPython.html.widgets import ContainerWidget as HBox
            from IPython.html.widgets import HTML
        except ImportError:  # pragma: no cover
            pass
try:  # pragma: no cover
    from IPython.display import display, clear_output
except ImportError:  # pragma: no cover
    pass
# to inherit from the tqdm class
from ._tqdm import tqdm, format_meter, StatusPrinter


__author__ = {"github.com/": ["casperdcl", "lrq3000"]}
__all__ = ['tqdm_notebook', 'tnrange']


def NotebookPrinter(total=None):  # pragma: no cover
    """
    Manage the printing of an IPython/Jupyter Notebook progress bar widget.
    """
    # Fallback to text bar if there's no total
    if not total:
        return StatusPrinter(sys.stdout)

    # Prepare IPython progress bar
    pbar = IntProgress(min=0, max=total)
    # Prepare status text
    ptext = HTML()
    # Only way to place text to the right of the bar is to use a container
    container = HBox(children=[pbar, ptext])
    display(container)

    def print_status(*args, **kwargs):
        #clear_output(wait=1)
        # Update progress bar with new values
        if args[0]:
            pbar.value = args[0]
            ptext.value = format_meter(*args, nobar=True, **kwargs)
        # If n is None, then special signal to close the bar
        elif args[0] is None:
            container.visible = False
    return print_status


class tqdm_notebook(tqdm):  # pragma: no cover
    """
    Experimental IPython/Jupyter Notebook widget using tqdm!
    """
    def __init__(self, *args, **kwargs):

        kwargs['file'] = sys.stdout  # avoid the red block in IPython

        super(tqdm_notebook, self).__init__(*args, **kwargs)

        # Delete the text progress bar display
        self.sp(None)
        # Replace with IPython progress bar display
        self.sp = NotebookPrinter(self.total)
        if not self.disable:
            self.sp(0, self.total, 0,
                        (dynamic_ncols(self.file) if self.dynamic_ncols else self.ncols),
                        self.desc, self.ascii, self.unit, self.unit_scale)


def tnrange(*args, **kwargs):  # pragma: no cover
    """
    A shortcut for tqdm_notebook(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    return tqdm_notebook(_range(*args), **kwargs)
