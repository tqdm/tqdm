"""
Thin wrappers around common functions.
"""
from tqdm.auto import tqdm
from copy import deepcopy
import functools
import sys

__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['tenumerate', 'tzip', 'tmap', 'thread_map', 'process_map']


def tenumerate(iterable, start=0, total=None, **tqdm_kwargs):
    """
    Equivalent of `numpy.ndenumerate` or builtin `enumerate`.
    """
    _enumerate = enumerate
    try:
        import numpy as np
    except ImportError:
        pass
    else:
        if isinstance(iterable, np.ndarray):
            _enumerate = np.ndenumerate
    return tqdm(
        _enumerate(iterable), total=total or len(iterable), **tqdm_kwargs)


def _tzip(iter1, *iter2plus, **tqdm_kwargs):
    """
    Equivalent of builtin `zip`.
    """
    for i in zip(tqdm(iter1, **tqdm_kwargs), *iter2plus):
        yield i


def _tmap(function, *sequences, **tqdm_kwargs):
    """
    Equivalent of builtin `map`.
    """
    for i in _tzip(*sequences, **tqdm_kwargs):
        yield function(*i)


def _executor_map(PoolExecutor, fn, *iterables, **tqdm_kwargs):
    """
    Implementation of `thread_map` and `process_map`.
    """
    kwargs = deepcopy(tqdm_kwargs)
    kwargs.setdefault("total", len(iterables[0]))
    with PoolExecutor(max_workers=kwargs.pop("max_workers", None)) as ex:
        return list(tqdm(ex.map(fn, *iterables), **kwargs))


def thread_map(fn, *iterables, **tqdm_kwargs):
    """
    Equivalent of `list(map(fn, *iterables))`
    driven by `concurrent.futures.ThreadPoolExecutor`.
    """
    from concurrent.futures import ThreadPoolExecutor
    return _executor_map(ThreadPoolExecutor, fn, *iterables, **tqdm_kwargs)


def process_map(fn, *iterables, **tqdm_kwargs):
    """
    Equivalent of `list(map(fn, *iterables))`
    driven by `concurrent.futures.ProcessPoolExecutor`.
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
