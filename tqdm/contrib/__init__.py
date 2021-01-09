"""
Thin wrappers around common functions.

Subpackages contain potentially unstable extensions.
"""
import sys
from functools import wraps

from tqdm import tqdm
from tqdm.auto import tqdm as tqdm_auto
from tqdm.utils import ObjectWrapper

__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['tenumerate', 'tzip', 'tmap']


class DummyTqdmFile(ObjectWrapper):
    """Dummy file-like that will write to tqdm"""
    def write(self, x, nolock=False):
        # Avoid print() second call (useless \n)
        if len(x.rstrip()) > 0:
            tqdm.write(x, file=self._wrapped, nolock=nolock)


def builtin_iterable(func):
    """Wraps `func()` output in a `list()` in py2"""
    if sys.version_info[:1] < (3,):
        @wraps(func)
        def inner(*args, **kwargs):
            return list(func(*args, **kwargs))
        return inner
    return func


def tenumerate(iterable, start=0, total=None, tqdm_class=tqdm_auto, **tqdm_kwargs):
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
            return tqdm_class(np.ndenumerate(iterable), total=total or iterable.size,
                              **tqdm_kwargs)
    return enumerate(tqdm_class(iterable, total=total, **tqdm_kwargs), start)


@builtin_iterable
def tzip(iter1, *iter2plus, **tqdm_kwargs):
    """
    Equivalent of builtin `zip`.

    Parameters
    ----------
    tqdm_class  : [default: tqdm.auto.tqdm].
    """
    kwargs = tqdm_kwargs.copy()
    tqdm_class = kwargs.pop("tqdm_class", tqdm_auto)
    for i in zip(tqdm_class(iter1, **tqdm_kwargs), *iter2plus):
        yield i


@builtin_iterable
def tmap(function, *sequences, **tqdm_kwargs):
    """
    Equivalent of builtin `map`.

    Parameters
    ----------
    tqdm_class  : [default: tqdm.auto.tqdm].
    """
    for i in tzip(*sequences, **tqdm_kwargs):
        yield function(*i)
