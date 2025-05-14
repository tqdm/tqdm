"""
Asynchronous progressbar decorator for asyncio iterators in Jupyter notebooks.

Usage:
>>> from tqdm.asyncio_notebook import trange, tqdm
>>> async for i in trange(10):
...     ...
"""
from .asyncio import tqdm_asyncio
from .notebook import tqdm_notebook

__author__ = {"github.com/": ["grach0v"]}
__all__ = ['tqdm_asyncio_notebook', 'tarange', 'tqdm', 'trange']


class tqdm_asyncio_notebook(tqdm_asyncio, tqdm_notebook):
    """
    Asynchronous-friendly version of tqdm for Jupyter notebooks.
    MRO behaviour as if `tqdm_asyncio` is inherited after `tqdm_notebook`, instead of `std_tqdm`.
    """
    pass


def tarange(*args, **kwargs):
    """
    Shortcut for `tqdm.asyncio_notebook.tqdm(range(*args), **kwargs)`.
    """
    return tqdm_asyncio_notebook(range(*args), **kwargs)

# Aliases


tqdm = tqdm_asyncio_notebook
trange = tarange
