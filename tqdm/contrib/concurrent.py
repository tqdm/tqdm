"""
Thin wrappers around `concurrent.futures`.
"""
from __future__ import absolute_import
from tqdm.auto import tqdm as tqdm_auto
from copy import deepcopy
try:
    from os import cpu_count
except ImportError:
    try:
        from multiprocessing import cpu_count
    except ImportError:
        def cpu_count():
            return 4
import sys
__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['thread_map', 'process_map']


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
    max_workers = kwargs.pop("max_workers", min(32, cpu_count() + 4))
    pool_kwargs = dict(max_workers=max_workers)
    if sys.version_info[:2] >= (3, 7):
        # share lock in case workers are already using `tqdm`
        pool_kwargs.update(
            initializer=tqdm_class.set_lock, initargs=(tqdm_class.get_lock(),))
    with PoolExecutor(**pool_kwargs) as ex:
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
