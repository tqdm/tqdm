"""
Thin wrappers around common functions.

Subpackages contain potentially unstable extensions.
"""
from warnings import warn

from ..auto import tqdm as tqdm_auto
from ..std import TqdmDeprecationWarning, tqdm
from ..utils import ObjectWrapper

__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['tenumerate', 'tzip', 'tmap']


class DummyTqdmFile(ObjectWrapper):
    """Dummy file-like that will write to tqdm"""

    def __init__(self, wrapped):
        """
        Parameters
        ----------
        wrapped  : file-like
            Underlying file object to write to via `tqdm.write()`.
        """
        super().__init__(wrapped)
        self._buf = []

    def write(self, x, nolock=False):
        """
        Buffer and flush `x` to `tqdm.write()` on each newline.

        Parameters
        ----------
        x  : str or bytes
            Data to write.
        nolock  : bool, optional
            If (default: False), do not acquire the tqdm lock.
        """
        nl = b"\n" if isinstance(x, bytes) else "\n"
        pre, sep, post = x.rpartition(nl)
        if sep:
            blank = type(nl)()
            tqdm.write(blank.join(self._buf + [pre, sep]),
                       end=blank, file=self._wrapped, nolock=nolock)
            self._buf = [post]
        else:
            self._buf.append(x)

    def __del__(self):
        """Flush any remaining buffered data via `tqdm.write()`."""
        if self._buf:
            blank = type(self._buf[0])()
            try:
                tqdm.write(blank.join(self._buf), end=blank, file=self._wrapped)
            except (OSError, ValueError):
                pass


def builtin_iterable(func):
    """Returns `func`"""
    warn("This function has no effect, and will be removed in tqdm==5.0.0",
         TqdmDeprecationWarning, stacklevel=2)
    return func


def tenumerate(iterable, start=0, total=None, tqdm_class=tqdm_auto, **tqdm_kwargs):
    """
    Equivalent of `numpy.ndenumerate` or builtin `enumerate`.

    Parameters
    ----------
    iterable  : iterable or numpy.ndarray
        Object to enumerate. `numpy.ndenumerate` is used when possible.
    start  : int, optional
        Starting index for builtin `enumerate` [default: 0].
    total  : int, optional
        Hint for the total number of iterations passed to `tqdm_class`.
    tqdm_class  : optional
        `tqdm` class used for the progress bar [default: tqdm.auto.tqdm].
    **tqdm_kwargs  : passed to `tqdm_class`.
    """
    try:
        import numpy as np
    except ImportError:
        pass
    else:
        if isinstance(iterable, np.ndarray):
            return tqdm_class(np.ndenumerate(iterable), total=total or iterable.size,
                              **tqdm_kwargs)
    return enumerate(tqdm_class(iterable, total=total, **tqdm_kwargs), start)


def tzip(iter1, *iter2plus, **tqdm_kwargs):
    """
    Equivalent of builtin `zip`.

    Parameters
    ----------
    iter1  : iterable
        First iterable; the progress bar tracks this one.
    *iter2plus  : iterable
        Additional iterables zipped alongside `iter1` (untracked).
    tqdm_class  : optional
        `tqdm` class used for the progress bar [default: tqdm.auto.tqdm].
    **tqdm_kwargs  : passed to `tqdm_class`.
    """
    kwargs = tqdm_kwargs.copy()
    tqdm_class = kwargs.pop("tqdm_class", tqdm_auto)
    yield from zip(tqdm_class(iter1, **kwargs), *iter2plus)


def tmap(function, *sequences, **tqdm_kwargs):
    """
    Equivalent of builtin `map`.

    Parameters
    ----------
    function  : callable
        Function to apply to each element.
    *sequences  : iterable
        One or more iterables whose elements are passed to `function`.
    tqdm_class  : optional
        `tqdm` class used for the progress bar [default: tqdm.auto.tqdm].
    **tqdm_kwargs  : passed to `tqdm_class` via `tzip`.
    """
    for i in tzip(*sequences, **tqdm_kwargs):
        yield function(*i)
