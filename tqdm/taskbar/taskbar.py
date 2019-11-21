"""
Cross-platform progress display in the taskbar
"""
from __future__ import division, absolute_import
from .meta_reporter import MetaReporter
from tqdm.std import tqdm as std_tqdm

__author__ = {"github.com/": ["KOLANICH", "casperdcl"]}
__all__ = ['tqdm', 'trange']


class tqdm(std_tqdm):
    def __init__(**kwargs):
        """
        Same as tqdm.tqdm
        """
        self._entered=0
        self.platform_specific_reporter = None
        super(tqdm, self).__init__(**kwargs)

    def __enter__(self):
        if not self._entered:
            self.platform_specific_reporter=MetaReporter(self.total, self.unit).__enter__()
            self._entered+=1
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self._entered:
            if self.platform_specific_reporter:
                if exc_traceback:
                    import traceback
                    self.platform_specific_reporter.fail("".join(traceback.format_exception(exc_type, exc_value, exc_traceback, limit=1)))
                elif self.total and self.n < self.total:
                    self.platform_specific_reporter.fail("The iteration not reached its finishing amount, though no exception has been thrown.")
                self.platform_specific_reporter.__exit__(exc_type, exc_value, exc_traceback)
                self.platform_specific_reporter = None
            super(tqdm, self).__exit__(exc_type, exc_value, exc_traceback)
            self._entered-=1
            return False

    def __del__(self):
        self.__exit__(None, None, None)
        super(tqdm, self).__del__()

    def __iter__(self):
        """Backward-compatibility to use: for x in tqdm(iterable)"""
        if not self._entered and self.iterable:
            self.__enter__()

        for obj in super(tqdm, self):
            yield obj

        if self.platform_specific_reporter:
            self.platform_specific_reporter.success()
            self.platform_specific_reporter.__exit__(None, None, None)
            self.platform_specific_reporter = None

    def close(self):
        """Cleanup and (if leave=False) close the progressbar."""
        if self.disable:
            return

        if self.platform_specific_reporter:
            self.platform_specific_reporter.clear()

        super(tqdm, self).close()

    def display(self, msg=None, pos=None):
        """
        Use `self.sp` to display `msg` in the specified `pos`.

        Consider overloading this function when inheriting to use e.g.:
        `self.some_frontend(**self.format_dict)` instead of `self.sp`.

        Parameters
        ----------
        msg  : str, optional. What to display (default: `repr(self)`).
        pos  : int, optional. Position to `moveto`
          (default: `abs(self.pos)`).
        """
        super(tqdm, self).display(self, msg=msg, pos=pos)
        if self.platform_specific_reporter:
            self.platform_specific_reporter.prefix(self.desc)
            self.platform_specific_reporter.postfix(self.postfix)
            #self.platform_specific_reporter.message(msg)
            self.platform_specific_reporter.progress(self.n, self.avg_time)


def trange(*args, **kwargs):
    """
    A shortcut for tqdm(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    return tqdm(_range(*args), **kwargs)
