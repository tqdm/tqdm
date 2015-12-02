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
import uuid
try:  # pragma: no cover
    # For IPython 4.x using ipywidgets
    from ipywidgets import IntProgress, HBox, HTML
    from IPython.display import display_html, display_javascript
except ImportError:  # pragma: no cover
    try:  # pragma: no cover
        # For IPython 3.x
        from IPython.html.widgets import IntProgress, HBox, HTML
        from IPython.display import display_html, display_javascript
    except ImportError:  # pragma: no cover
        try:  # pragma: no cover
            # For IPython 2.x
            from IPython.html.widgets import IntProgressWidget as IntProgress
            from IPython.html.widgets import ContainerWidget as HBox
            from IPython.html.widgets import HTML
            from IPython.display import display_html, display_javascript
        except ImportError:  # pragma: no cover
            pass
try:  # pragma: no cover
    from IPython.display import display  # , clear_output
except ImportError:  # pragma: no cover
    pass
# to inherit from the tqdm class
from ._tqdm import tqdm, format_meter, StatusPrinter


__author__ = {"github.com/": ["lrq3000", "casperdcl"]}
__all__ = ['tqdm_notebook', 'tnrange', 'tqdm_notebook_pretty', 'tnprange']


def NotebookPrinter(total=None, desc=None):  # pragma: no cover
    """
    Manage the printing of an IPython/Jupyter Notebook progress bar widget.
    """
    # Fallback to text bar if there's no total
    if not total:
        return StatusPrinter(sys.stdout)

    # Prepare IPython progress bar
    pbar = IntProgress(min=0, max=total)
    if desc:
        pbar.description = desc
    # Prepare status text
    ptext = HTML()
    # Only way to place text to the right of the bar is to use a container
    container = HBox(children=[pbar, ptext])
    display(container)

    def print_status(*args, **kwargs):
        # clear_output(wait=1)
        # Update progress bar with new values
        if args[0] is not None:
            pbar.value = args[0]
            ptext.value = format_meter(*args, nobar=True, **kwargs)
        # If n is None, then special signal to close the bar
        else:
            container.visible = False
    return print_status


def NotebookPrettyPrinter(key=None, total=None, desc=None):  # pragma: no cover
    """
    Manage the printing of an IPython/Jupyter Notebook progress bar widget.
    """
    # Fallback to text bar if there's no total
    if not total:
        return StatusPrinter(sys.stdout)

    desc = "<h3>%s</h3>" % desc if desc else ''
    html_id = 'a' + str(uuid.uuid4())

    # Prepare IPython progress bar
    display_javascript('$("[data-key=\'%s\']").parent().parent().remove()' % key, raw=True)
    display_html('''
            <style>
                .progress {
                    text-align:center;
                }
                .progress > .progress-bar {
                    transition-property: none;
                }
                .progress > .text {
                    position: absolute;
                    right: 0;
                    left: 0;
                }
            </style>
            %s
            <div class="progress" id="%s" data-key="%s">
                <div class="progress-bar progress-bar-success completed-part" style="width: 0%%"></div>
                <div class="progress-bar progress-bar-warning running-part" style="width: 100%%"></div>
                <span class="text">
                    <span class="main">Starting...</span>
                    <span class="extra"></span>
                </span>
            </div>
            ''' % (desc, html_id, key), raw=True)

    def print_status(*args, **kwargs):
        # clear_output(wait=1)
        # Update progress bar with new values
        if args[0] is not None:
            n = args[0]
            s = format_meter(*args, nobar=True, **kwargs)
            display_javascript('$("#%s > .completed-part").css("width", "%f%%")' % (html_id, n/total*100), raw=True)
            display_javascript('$("#%s > .running-part").css("width", "%f%%")' % (html_id, total/100), raw=True)
            display_javascript('$("#%s > .text > .main").text("%s")' % (html_id, s), raw=True)
        # If n is None, then special signal to close the bar
        else:
            display_javascript('$("#%s").parent().parent().hide()' % html_id, raw=True)
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
        self.sp = NotebookPrinter(self.total, self.desc)
        self.desc = None  # trick to place description before the bar

        # Print initial bar state
        if not self.disable:
            self.sp(0, self.total, 0,
                    (self.dynamic_ncols(self.file) if self.dynamic_ncols
                     else self.ncols),
                    self.desc, self.ascii, self.unit, self.unit_scale)


class tqdm_notebook_pretty(tqdm):  # pragma: no cover
    """
    Experimental IPython/Jupyter Notebook widget using tqdm!
    """
    def __init__(self, *args, **kwargs):

        kwargs['file'] = sys.stdout  # avoid the red block in IPython

        super(tqdm_notebook_pretty, self).__init__(*args, **kwargs)

        # Delete the text progress bar display
        self.sp(None)
        # Replace with IPython progress bar display
        self.sp = NotebookPrettyPrinter(self, self.total, self.desc)
        self.desc = None  # trick to place description before the bar

        # Print initial bar state
        if not self.disable:
            self.sp(0, self.total, 0,
                    (self.dynamic_ncols(self.file) if self.dynamic_ncols
                     else self.ncols),
                    self.desc, self.ascii, self.unit, self.unit_scale)


def tnrange(*args, **kwargs):  # pragma: no cover
    """
    A shortcut for tqdm_notebook(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    return tqdm_notebook(_range(*args), **kwargs)


def tnprange(*args, **kwargs):  # pragma: no cover
    """
    A shortcut for tqdm_notebook(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    return tqdm_notebook_pretty(_range(*args), **kwargs)
