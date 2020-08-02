"""
Asynchronous progressbar decorator for iterators.
Includes a default `range` iterator printing to `stderr`.

Usage:
>>> from tqdm.asyncio import trange, tqdm
>>> async for i in trange(10):
...     ...
"""
from .std import tqdm as std_tqdm
import asyncio
__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['tqdm_asyncio', 'tarange', 'tqdm', 'trange']


class tqdm_asyncio(std_tqdm):
    """
    Asynchronous-friendly version of tqdm (Python 3.5+).
    """
    def __init__(self, iterable=None, *args, **kwargs):
        super(tqdm_asyncio, self).__init__(iterable, *args, **kwargs)
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
        except:
            self.close()
            raise

    def send(self, *args, **kwargs):
        return self.iterable.send(*args, **kwargs)

    @classmethod
    def as_completed(cls, fs, *, loop=None, timeout=None, total=None,
                     **tqdm_kwargs):
        """
        Wrapper for `asyncio.as_completed`.
        """
        if total is None:
            total = len(fs)
        yield from cls(asyncio.as_completed(fs, loop=loop, timeout=timeout),
                       total=total, **tqdm_kwargs)


def tarange(*args, **kwargs):
    """
    A shortcut for `tqdm.asyncio.tqdm(range(*args), **kwargs)`.
    """
    return tqdm_asyncio(range(*args), **kwargs)


# Aliases
tqdm = tqdm_asyncio
trange = tarange
