"""
Thin wrappers around common functions.
"""
from tqdm.auto import tqdm
from copy import deepcopy
import sys

__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['tmap', 'thread_map', 'process_map']

PY2 = sys.version_info[:1] == (2,)


def tzip(iter1, *iter2plus, **tqdm_kwargs):
    """
    Equivalent of builtin `zip`.
    """
    for i in zip(tqdm(iter1, **tqdm_kwargs), *iter2plus):
        yield i

def tmap(function, *sequences, **tqdm_kwargs):
    """
    Equivalent of builtin `map`.
    """
    if PY2:
        return [function(*i) for i in tzip(*sequences, **tqdm_kwargs)]
    else:
        for i in tzip(*sequences, **tqdm_kwargs):
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
