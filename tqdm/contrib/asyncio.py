"""
Thin wrappers around `asyncio`.
"""
import asyncio

from tqdm.auto import tqdm as tqdm_auto
from tqdm.contrib.concurrent import ensure_lock
__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['map_async']


async def map_async(fn, *iterables, **tqdm_kwargs):
    """
    Equivalent of `[(await i) for i in map(fn, *iterables)]`.

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
    tqdm_class = kwargs.pop("tqdm_class", tqdm_auto)
    lock_name = kwargs.pop("lock_name", "")
    with ensure_lock(tqdm_class, lock_name=lock_name):
        tasks = [asyncio.create_task(i) for i in map(fn, *iterables)]
        _ = [await i for i in tqdm_class.as_completed(tasks, **kwargs)]
    return [i.result() for i in tasks]
