"""
Thin wrappers around `asyncio`.
"""
import asyncio

from tqdm.auto import tqdm as tqdm_auto
from tqdm.contrib.concurrent import ensure_lock, length_hint
__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['map_async']


async def map_async(fn, *iterables, **tqdm_kwargs):
    """
    Equivalent of `list(map(asyncio.run, map(fn, *iterables)))`.

    Parameters
    ----------
    tqdm_class  : optional
        `tqdm` class to use for bars [default: tqdm.auto.tqdm].
    loop  : optional
        Event loop to use [default: None].
    lock_name  : optional
        [default: "":str].
    """
    kwargs = tqdm_kwargs.copy()
    if "total" not in kwargs:
        kwargs["total"] = length_hint(iterables[0])
    tqdm_class = kwargs.pop("tqdm_class", tqdm_auto)
    loop = kwargs.pop("loop", None)
    lock_name = kwargs.pop("lock_name", "")
    with ensure_lock(tqdm_class, lock_name=lock_name):
        tasks = [asyncio.create_task(i) for i in map(fn, *iterables)]
        _ = [await i for i in tqdm_class(
             asyncio.as_completed(tasks, loop=loop), **kwargs)]
    return [i.result() for i in tasks]
