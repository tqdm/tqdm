"""
GUI progressbar decorator for iterators.
Includes a default (x)range iterator printing to stderr.

Usage:
  >>> from tqdm_gui import tgrange[, tqdm_gui]
  >>> for i in tgrange(10): #same as: for i in tqdm_gui(xrange(10))
  ...     ...
"""
# future division is important to divide integers and get as
# a result precise floating numbers (instead of truncated int)
from __future__ import division, absolute_import
# import compatibility functions and utilities
from time import time
from ._utils import _range
# to inherit from the tqdm class
from ._tqdm import tqdm


__author__ = {"github.com/": ["casperdcl", "lrq3000"]}
__all__ = ['tqdm_gui', 'tgrange']


class tqdm_gui(tqdm):  # pragma: no cover
    """
    Experimental GUI version of tqdm!
    """
    def __init__(self, *args, **kwargs):

        # try:  # pragma: no cover
        import matplotlib as mpl
        import matplotlib.pyplot as plt
        from collections import deque
        # except ImportError:  # gui not available
        #   kwargs['gui'] = False
        # else:
        kwargs['gui'] = True

        super(tqdm_gui, self).__init__(*args, **kwargs)

        # Initialize the GUI display
        if self.disable or not kwargs['gui']:
            return

        self.fp.write('Warning: GUI is experimental/alpha\n')
        self.mpl = mpl
        self.plt = plt
        self.sp = None

        # Remember if external environment uses toolbars
        self.toolbar = self.mpl.rcParams['toolbar']
        self.mpl.rcParams['toolbar'] = 'None'

        self.mininterval = max(self.mininterval, 0.5)
        self.fig, ax = plt.subplots(figsize=(9, 2.2))
        # self.fig.subplots_adjust(bottom=0.2)
        if self.total:
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
        if self.total:
            ax.set_xlim(0, 100)
            ax.set_xlabel('percent')
            self.fig.legend((self.line1, self.line2), ('cur', 'est'),
                            loc='center right')
            # progressbar
            self.hspan = plt.axhspan(0, 0.001,
                                     xmin=0, xmax=0, color='g')
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
            plt.ticklabel_format(style='sci', axis='y',
                                 scilimits=(0, 0))
            ax.yaxis.get_offset_text().set_x(-0.15)

        # Remember if external environment is interactive
        self.wasion = plt.isinteractive()
        plt.ion()
        self.ax = ax

    def __iter__(self):
        # TODO: somehow allow the following:
        # if not self.gui:
        #   return super(tqdm_gui, self).__iter__()
        iterable = self.iterable
        if self.disable:
            for obj in iterable:
                yield obj
            return

        # ncols = self.ncols
        mininterval = self.mininterval
        maxinterval = self.maxinterval
        miniters = self.miniters
        dynamic_miniters = self.dynamic_miniters
        unit = self.unit
        unit_scale = self.unit_scale
        ascii = self.ascii
        start_t = self.start_t
        last_print_t = self.last_print_t
        last_print_n = self.last_print_n
        n = self.n
        # dynamic_ncols = self.dynamic_ncols
        smoothing = self.smoothing
        avg_time = self.avg_time
        bar_format = self.bar_format

        plt = self.plt
        ax = self.ax
        xdata = self.xdata
        ydata = self.ydata
        zdata = self.zdata
        line1 = self.line1
        line2 = self.line2

        for obj in iterable:
            yield obj
            # Update and print the progressbar.
            # Note: does not call self.update(1) for speed optimisation.
            n += 1
            delta_it = n - last_print_n
            # check the counter first (avoid calls to time())
            if delta_it >= miniters:
                cur_t = time()
                delta_t = cur_t - last_print_t
                if delta_t >= mininterval:  # pragma: no cover
                    elapsed = cur_t - start_t
                    # EMA (not just overall average)
                    if smoothing and delta_t:
                        avg_time = delta_t / delta_it \
                            if avg_time is None \
                            else smoothing * delta_t / delta_it + \
                            (1 - smoothing) * avg_time

                    # Inline due to multiple calls
                    total = self.total
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
                            self.hspan = plt.axhspan(0, 0.001, xmin=0,
                                                     xmax=0, color='g')
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

                    ax.set_title(self.format_meter(
                        n, total, elapsed, 0,
                        self.desc, ascii, unit, unit_scale,
                        1 / avg_time if avg_time else None, bar_format),
                        fontname="DejaVu Sans Mono", fontsize=11)
                    plt.pause(1e-9)

                    # If no `miniters` was specified, adjust automatically
                    # to the maximum iteration rate seen so far.
                    if dynamic_miniters:
                        if maxinterval and delta_t > maxinterval:
                            # Set miniters to correspond to maxinterval
                            miniters = delta_it * maxinterval / delta_t
                        elif mininterval and delta_t:
                            # EMA-weight miniters to converge
                            # towards the timeframe of mininterval
                            miniters = smoothing * delta_it * mininterval \
                                / delta_t + (1 - smoothing) * miniters
                        else:
                            miniters = smoothing * delta_it + \
                                (1 - smoothing) * miniters

                    # Store old values for next call
                    last_print_n = n
                    last_print_t = cur_t

        # Closing the progress bar.
        # Update some internal variables for close().
        self.last_print_n = last_print_n
        self.n = n
        self.close()

    def update(self, n=1):
        # if not self.gui:
        #   return super(tqdm_gui, self).close()
        if self.disable:
            return

        if n < 0:
            n = 1
        self.n += n

        delta_it = self.n - self.last_print_n  # should be n?
        if delta_it >= self.miniters:
            # We check the counter first, to reduce the overhead of time()
            cur_t = time()
            delta_t = cur_t - self.last_print_t
            if delta_t >= self.mininterval:
                elapsed = cur_t - self.start_t
                # EMA (not just overall average)
                if self.smoothing and delta_t:
                    self.avg_time = delta_t / delta_it \
                        if self.avg_time is None \
                        else self.smoothing * delta_t / delta_it + \
                        (1 - self.smoothing) * self.avg_time

                # Inline due to multiple calls
                total = self.total
                ax = self.ax

                # instantaneous rate
                y = delta_it / delta_t
                # smoothed rate
                z = self.n / elapsed
                # update line data
                self.xdata.append(self.n * 100.0 / total
                                  if total else cur_t)
                self.ydata.append(y)
                self.zdata.append(z)

                # Discard old values
                if (not total) and elapsed > 66:
                    self.xdata.popleft()
                    self.ydata.popleft()
                    self.zdata.popleft()

                ymin, ymax = ax.get_ylim()
                if y > ymax or z > ymax:
                    ymax = 1.1 * y
                    ax.set_ylim(ymin, ymax)
                    ax.figure.canvas.draw()

                if total:
                    self.line1.set_data(self.xdata, self.ydata)
                    self.line2.set_data(self.xdata, self.zdata)
                    try:
                        poly_lims = self.hspan.get_xy()
                    except AttributeError:
                        self.hspan = self.plt.axhspan(0, 0.001, xmin=0,
                                                      xmax=0, color='g')
                        poly_lims = self.hspan.get_xy()
                    poly_lims[0, 1] = ymin
                    poly_lims[1, 1] = ymax
                    poly_lims[2] = [self.n / total, ymax]
                    poly_lims[3] = [poly_lims[2, 0], ymin]
                    if len(poly_lims) > 4:
                        poly_lims[4, 1] = ymin
                    self.hspan.set_xy(poly_lims)
                else:
                    t_ago = [cur_t - i for i in self.xdata]
                    self.line1.set_data(t_ago, self.ydata)
                    self.line2.set_data(t_ago, self.zdata)

                ax.set_title(self.format_meter(
                    self.n, total, elapsed, 0,
                    self.desc, self.ascii, self.unit, self.unit_scale,
                    1 / self.avg_time if self.avg_time else None,
                    self.bar_format),
                    fontname="DejaVu Sans Mono", fontsize=11)
                self.plt.pause(1e-9)

                # If no `miniters` was specified, adjust automatically to the
                # maximum iteration rate seen so far.
                # e.g.: After running `tqdm.update(5)`, subsequent
                # calls to `tqdm.update()` will only cause an update after
                # at least 5 more iterations.
                if self.dynamic_miniters:
                    if self.maxinterval and delta_t > self.maxinterval:
                        self.miniters = self.miniters * self.maxinterval \
                            / delta_t
                    elif self.mininterval and delta_t:
                        self.miniters = self.smoothing * delta_it \
                            * self.mininterval / delta_t + \
                            (1 - self.smoothing) * self.miniters
                    else:
                        self.miniters = self.smoothing * delta_it + \
                            (1 - self.smoothing) * self.miniters

                # Store old values for next call
                self.last_print_n = self.n
                self.last_print_t = cur_t

    def close(self):
        # if not self.gui:
        #   return super(tqdm_gui, self).close()
        if self.disable:
            return

        self.disable = True

        self._instances.remove(self)

        # Restore toolbars
        self.mpl.rcParams['toolbar'] = self.toolbar
        # Return to non-interactive mode
        if not self.wasion:
            self.plt.ioff()
        if not self.leave:
            self.plt.close(self.fig)


def tgrange(*args, **kwargs):
    """
    A shortcut for tqdm_gui(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    return tqdm_gui(_range(*args), **kwargs)
