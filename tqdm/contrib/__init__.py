"""
Thin wrappers around common functions.

Subpackages contain potentially unstable extensions.
"""
from tqdm import tqdm
from tqdm.auto import tqdm as tqdm_auto
from tqdm.utils import ObjectWrapper
from copy import deepcopy
import functools
import sys
__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['tenumerate', 'tzip', 'tmap']


class DummyTqdmFile(ObjectWrapper):
    """Dummy file-like that will write to tqdm"""
    def write(self, x, nolock=False):
        # Avoid print() second call (useless \n)
        if len(x.rstrip()) > 0:
            tqdm.write(x, file=self._wrapped, nolock=nolock)


def tenumerate(iterable, start=0, total=None, tqdm_class=tqdm_auto,
               **tqdm_kwargs):
    """
    Equivalent of `numpy.ndenumerate` or builtin `enumerate`.

    Parameters
    ----------
    tqdm_class  : [default: tqdm.auto.tqdm].
    """
    try:
        import numpy as np
    except ImportError:
        pass
    else:
        if isinstance(iterable, np.ndarray):
            return tqdm_class(np.ndenumerate(iterable),
                              total=total or iterable.size, **tqdm_kwargs)
    return enumerate(tqdm_class(iterable, **tqdm_kwargs), start)


def _tzip(iter1, *iter2plus, **tqdm_kwargs):
    """
    Equivalent of builtin `zip`.

    Parameters
    ----------
    tqdm_class  : [default: tqdm.auto.tqdm].
    """
    kwargs = deepcopy(tqdm_kwargs)
    tqdm_class = kwargs.pop("tqdm_class", tqdm_auto)
    for i in zip(tqdm_class(iter1, **tqdm_kwargs), *iter2plus):
        yield i


def _tmap(function, *sequences, **tqdm_kwargs):
    """
    Equivalent of builtin `map`.

    Parameters
    ----------
    tqdm_class  : [default: tqdm.auto.tqdm].
    """
    for i in _tzip(*sequences, **tqdm_kwargs):
        yield function(*i)


if sys.version_info[:1] < (3,):
    @functools.wraps(_tzip)
    def tzip(*args, **kwargs):
        return list(_tzip(*args, **kwargs))

    @functools.wraps(_tmap)
    def tmap(*args, **kwargs):
        return list(_tmap(*args, **kwargs))
else:
    tzip = _tzip
    tmap = _tmap
