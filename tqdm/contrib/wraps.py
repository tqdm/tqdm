"""
Thin wrappers around common functions.
"""
from tqdm.auto import tqdm
from copy import deepcopy

__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['tmap', 'thread_map', 'process_map']

def tmap(function, *sequences, **tqdm_kwargs):
    """
    Equivalent of builtin `map`.
    """
    kwargs = deepcopy(tqdm_kwargs)
    kwargs.setdefault("total", len(sequences[0]))
    return [function(*i) for i in tqdm(zip(*sequences), **kwargs)]


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
