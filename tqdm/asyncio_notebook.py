"""
Asynchronous progressbar decorator for asyncio iterators in Jupyter notebooks.

Usage:
>>> from tqdm.asyncio_notebook import trange, tqdm
>>> async for i in trange(10):
...     ...
"""
import asyncio
from sys import version_info

from .notebook import tqdm as std_tqdm  # notebook version

__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['tqdm_asyncio_notebook', 'tarange', 'tqdm', 'trange']

class tqdm_asyncio_notebook(std_tqdm):
    """
    Asynchronous-friendly version of tqdm for Jupyter notebooks.
    """
    def __init__(self, iterable=None, *args, **kwargs):
        super().__init__(iterable, *args, **kwargs)
        self.iterable_awaitable = False
        if iterable is not None:
            if hasattr(iterable, "__anext__"):
                self.iterable_next = iterable.__anext__
                self.iterable_awaitable = True
            elif hasattr(iterable, "__next__"):
                self.iterable_next = iterable.__next__
            else:
                self.iterable_iterator = iter(iterable)
                self.iterable_next = self.iterable_iterator.__next__

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            if self.iterable_awaitable:
                res = await self.iterable_next()
            else:
                res = self.iterable_next()
            self.update()
            return res
        except StopIteration:
            self.close()
            raise StopAsyncIteration
        except BaseException:
            self.close()
            raise

    def send(self, *args, **kwargs):
        return self.iterable.send(*args, **kwargs)

    @classmethod
    def as_completed(cls, fs, *, loop=None, timeout=None, total=None, **tqdm_kwargs):
        """
        Wrapper for `asyncio.as_completed` with progress bar.
        """
        if total is None:
            total = len(fs)
        kwargs = {}
        if version_info[:2] < (3, 10):
            kwargs['loop'] = loop
        # yield futures wrapped in progress bar
        yield from cls(asyncio.as_completed(fs, timeout=timeout, **kwargs),
                       total=total, **tqdm_kwargs)

    @classmethod
    async def gather(cls, *fs, loop=None, timeout=None, total=None, **tqdm_kwargs):
        """
        Wrapper for `asyncio.gather` with progress bar.
        """
        async def wrap_awaitable(i, f):
            return i, await f

        ifs = [wrap_awaitable(i, f) for i, f in enumerate(fs)]
        res = [await f for f in cls.as_completed(ifs, loop=loop, timeout=timeout,
                                                 total=total, **tqdm_kwargs)]
        return [i for _, i in sorted(res)]


def tarange(*args, **kwargs):
    """
    Shortcut for `tqdm.asyncio_notebook.tqdm(range(*args), **kwargs)`.
    """
    return tqdm_asyncio_notebook(range(*args), **kwargs)

# Aliases

tqdm = tqdm_asyncio_notebook
trange = tarange
