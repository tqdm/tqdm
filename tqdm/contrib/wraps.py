"""
Thin wrappers around common functions.
"""
from tqdm.auto import tqdm as tqdm_auto
from copy import deepcopy
import functools
import sys

__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['tenumerate', 'tzip', 'tmap', 'thread_map', 'process_map']


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
                              total=total or len(iterable), **tqdm_kwargs)
    return enumerate(tqdm_class(iterable, start, **tqdm_kwargs))


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


def _executor_map(PoolExecutor, fn, *iterables, **tqdm_kwargs):
    """
    Implementation of `thread_map` and `process_map`.

    Parameters
    ----------
    tqdm_class  : [default: tqdm.auto.tqdm].
    """
    kwargs = deepcopy(tqdm_kwargs)
    kwargs.setdefault("total", len(iterables[0]))
    tqdm_class = kwargs.pop("tqdm_class", tqdm_auto)
    with PoolExecutor(max_workers=kwargs.pop("max_workers", None)) as ex:
        return list(tqdm_class(ex.map(fn, *iterables), **kwargs))


def thread_map(fn, *iterables, **tqdm_kwargs):
    """
    Equivalent of `list(map(fn, *iterables))`
    driven by `concurrent.futures.ThreadPoolExecutor`.

    Parameters
    ----------
    tqdm_class  : [default: tqdm.auto.tqdm].
    """
    from concurrent.futures import ThreadPoolExecutor
    return _executor_map(ThreadPoolExecutor, fn, *iterables, **tqdm_kwargs)


def process_map(fn, *iterables, **tqdm_kwargs):
    """
    Equivalent of `list(map(fn, *iterables))`
    driven by `concurrent.futures.ProcessPoolExecutor`.

    Parameters
    ----------
    tqdm_class  : [default: tqdm.auto.tqdm].
    """
    from concurrent.futures import ProcessPoolExecutor
    return _executor_map(ProcessPoolExecutor, fn, *iterables, **tqdm_kwargs)


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
