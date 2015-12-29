"""
Web-friendly progressbar decorator for iterators.
Includes a default (x)range iterator printing to stderr.

Usage:
  >>> from tqdm_web import twrange[, tqdm_web]
  >>> for i in twrange(10): #same as: for i in tqdm_web(xrange(10))
  ...     ...
"""
# future division is important to divide integers and get as
# a result precise floating numbers (instead of truncated int)
from __future__ import division, absolute_import
# import compatibility functions and utilities
import sys
import uuid
from ._utils import _range

# HTML encoding
try:  # pragma: no cover
    from html import escape  # python 3.x
except ImportError:  # pragma: no cover
    from cgi import escape  # python 2.x

# to inherit from the tqdm class
from ._tqdm import tqdm, format_meter, StatusPrinter


__author__ = {"github.com/": ["lrq3000", "aplavin"]}
__all__ = ['tqdm_notebook', 'tnrange']


def WebPrinter(key, file, total=None, desc=None):  # pragma: no cover
    """
    Manage the printing of an IPython/Jupyter Notebook progress bar widget.
    """
    def display_javascript(fp, s):
        fp.write('<script type="text/javascript">')
        fp.write(s)
        fp.write('</script>')

    def display_html(fp, s):
        fp.write(s)

    # Fallback to text bar if there's no total
    if not total:
        return StatusPrinter(file)

    fp = file
    if not getattr(fp, 'flush', False):  # pragma: no cover
        fp.flush = lambda: None

    desc = "<h3>%s</h3>" % desc if desc else ''
    html_id = 'tqdm_' + str(uuid.uuid4())

    # Prepare IPython progress bar
    display_javascript(fp, '$("[data-key=\'%s\']").parent().parent().remove()' % key)
    display_html(fp, '''
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
            ''' % (desc, html_id, key))

    def print_status(s='', close=False):
        # Clear previous output (really necessary?)
        # clear_output(wait=1)

        # Get current iteration value from format_meter string
        n = None
        if s:
            npos = s.find(r'/|/')  # because we use bar_format=r'{n}|...'
            # Check that n can be found in s (else n > total)
            if npos >= 0:
                n = int(s[:npos])  # get n from string
                s = s[npos+3:]  # remove from string

                # Update bar with current n value
                if n is not None:
                    display_javascript(fp, '$("#%s > .completed-part").css("width", "%f%%")' % (html_id, n/total*100))
                    display_javascript(fp, '$("#%s > .running-part").css("width", "%f%%")' % (html_id, total/100))

        # Print stats
        display_javascript(fp, '$("#%s > .text > .main").text("%s")' % (html_id, s))

        # Special signal to close the bar
        if close:
            display_javascript(fp, '$("#%s").parent().parent().hide()' % html_id)

    return print_status


class tqdm_web(tqdm):  # pragma: no cover
    """
    Experimental CSS/JSS web-friendly tqdm!
    """
    def __init__(self, *args, **kwargs):

        # Setup default output
        if not kwargs.get('file', None) or kwargs['file'] == sys.stderr:
            kwargs['file'] = sys.stdout  # avoid the red block in IPython

        # Remove the bar from the printed string, only print stats
        if not kwargs.get('bar_format', None):
            kwargs['bar_format'] = r'{n}/|/{l_bar}{r_bar}'

        super(tqdm_web, self).__init__(*args, **kwargs)

        # Delete the text progress bar display
        self.sp('')
        # Replace with web progress bar display
        self.sp_web = WebPrinter(self, self.fp, self.total, self.desc)
        self.sp = self.sprinter
        self.desc = None  # trick to place description before the bar

        # Print initial bar state
        if not self.disable:
            self.sp(format_meter(self.n, self.total, 0,
                    (self.dynamic_ncols(self.file) if self.dynamic_ncols
                     else self.ncols),
                    self.desc, self.ascii, self.unit, self.unit_scale, None,
                    self.bar_format))

    def sprinter(self, s=''):
        self.sp_web(s)

    def close(self, *args, **kwargs):
        super(tqdm_web, self).close(*args, **kwargs)
        if not self.leave:
            self.sp_web(s='', close=True)


def twrange(*args, **kwargs):  # pragma: no cover
    """
    A shortcut for tqdm_web(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    return tqdm_web(_range(*args), **kwargs)
