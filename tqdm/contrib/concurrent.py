"""
Thin wrappers around `concurrent.futures`.
"""
from contextlib import contextmanager
from operator import length_hint
from os import cpu_count
from queue import Empty
from threading import RLock, get_ident
from time import monotonic

from ..auto import tqdm as tqdm_auto
from ..std import TqdmWarning

__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['thread_map', 'process_map', 'interpreter_map']


class _InterpreterLock:
    """Reentrant lock backed by a cross-interpreter queue."""

    def __init__(self, queue):
        self._queue = queue
        self._lock = RLock()
        self._owner = None
        self._depth = 0

    def acquire(self, blocking=True, timeout=-1):
        start = monotonic()
        if timeout == -1:
            acquired = self._lock.acquire(blocking)
        else:
            acquired = self._lock.acquire(blocking, timeout)
        if not acquired:
            return False
        if self._depth:
            self._depth += 1
            return True
        try:
            if not blocking:
                self._queue.get_nowait()
            elif timeout == -1:
                self._queue.get()
            else:
                remaining = max(0, timeout - (monotonic() - start))
                self._queue.get(timeout=remaining)
        except Empty:
            self._lock.release()
            return False
        self._owner = get_ident()
        self._depth = 1
        return True

    def release(self):
        if self._owner != get_ident():
            raise RuntimeError("cannot release un-acquired lock")
        self._depth -= 1
        if not self._depth:
            self._owner = None
            self._queue.put(None)
        self._lock.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *exc):
        self.release()


@contextmanager
def ensure_lock(tqdm_class, lock_name="", lock=None):
    """get (create if necessary) and then restore `tqdm_class`'s lock"""
    old_lock = getattr(tqdm_class, '_lock', None)  # don't create a new lock
    if lock is None:
        lock = old_lock or tqdm_class.get_lock()  # maybe create a new lock
    lock = getattr(lock, lock_name, lock)  # maybe subtype
    tqdm_class.set_lock(lock)
    yield lock
    if old_lock is None:
        del tqdm_class._lock
    else:
        tqdm_class.set_lock(old_lock)


def _set_interpreter_lock(tqdm_class, lock_queue_id):
    """Install an interpreter-local lock backed by a shared queue."""
    from concurrent import interpreters
    tqdm_class.set_lock(_InterpreterLock(interpreters.Queue(lock_queue_id)))


def _executor_map(PoolExecutor, fn, *iterables, _lock=None, _initializer=None,
                  _initargs=None, **tqdm_kwargs):
    """
    Implementation of `thread_map`, `process_map` and `interpreter_map`.

    Parameters
    ----------
    tqdm_class  : [default: tqdm.auto.tqdm].
    max_workers  : [default: min(32, cpu_count() + 4)].
    chunksize  : [default: 1].
    lock_name  : [default: "":str].
    """
    kwargs = tqdm_kwargs.copy()
    if "total" not in kwargs:
        kwargs["total"] = length_hint(iterables[0])
    tqdm_class = kwargs.pop("tqdm_class", tqdm_auto)
    max_workers = kwargs.pop("max_workers", min(32, cpu_count() + 4))
    chunksize = kwargs.pop("chunksize", 1)
    lock_name = kwargs.pop("lock_name", "")
    with ensure_lock(tqdm_class, lock_name=lock_name, lock=_lock) as lk:
        pool_kwargs = {"max_workers": max_workers}
        # share lock in case workers are already using `tqdm`
        if _initializer is None:
            _initializer = tqdm_class.set_lock
            _initargs = (lk,)
        pool_kwargs.update(initializer=_initializer, initargs=_initargs)
        with PoolExecutor(**pool_kwargs) as ex:
            return list(tqdm_class(ex.map(fn, *iterables, chunksize=chunksize), **kwargs))


def thread_map(fn, *iterables, **tqdm_kwargs):
    """
    Equivalent of `list(map(fn, *iterables))`
    driven by `concurrent.futures.ThreadPoolExecutor`.

    Parameters
    ----------
    tqdm_class  : optional
        `tqdm` class to use for bars [default: tqdm.auto.tqdm].
    max_workers  : int, optional
        Maximum number of workers to spawn; passed to
        `concurrent.futures.ThreadPoolExecutor.__init__`.
        [default: max(32, cpu_count() + 4)].
    """
    from concurrent.futures import ThreadPoolExecutor
    return _executor_map(ThreadPoolExecutor, fn, *iterables, **tqdm_kwargs)


def interpreter_map(fn, *iterables, **tqdm_kwargs):
    """
    Equivalent of `list(map(fn, *iterables))`
    driven by `concurrent.futures.InterpreterPoolExecutor` (Python 3.14+).

    Parameters
    ----------
    tqdm_class  : optional
        `tqdm` class to use for bars [default: tqdm.auto.tqdm].
    max_workers  : int, optional
        Maximum number of workers to spawn; passed to
        `concurrent.futures.InterpreterPoolExecutor.__init__`.
        [default: min(32, cpu_count() + 4)].

    Notes
    -----
    `fn`, its arguments, and its return values must be pickleable.
    Worker progress bars using the same `tqdm_class` share a
    cross-interpreter write lock.
    """
    from concurrent import interpreters
    from concurrent.futures import InterpreterPoolExecutor
    lock_queue = interpreters.create_queue()
    lock_queue.put(None)
    tqdm_class = tqdm_kwargs.get("tqdm_class", tqdm_auto)
    return _executor_map(
        InterpreterPoolExecutor, fn, *iterables, _lock=_InterpreterLock(lock_queue),
        _initializer=_set_interpreter_lock, _initargs=(tqdm_class, lock_queue.id), **tqdm_kwargs)


def process_map(fn, *iterables, **tqdm_kwargs):
    """
    Equivalent of `list(map(fn, *iterables))`
    driven by `concurrent.futures.ProcessPoolExecutor`.

    Parameters
    ----------
    tqdm_class  : optional
        `tqdm` class to use for bars [default: tqdm.auto.tqdm].
    max_workers  : int, optional
        Maximum number of workers to spawn; passed to
        `concurrent.futures.ProcessPoolExecutor.__init__`.
        [default: min(32, cpu_count() + 4)].
    chunksize  : int, optional
        Size of chunks sent to worker processes; passed to
        `concurrent.futures.ProcessPoolExecutor.map`. [default: 1].
    lock_name  : str, optional
        Member of `tqdm_class.get_lock()` to use [default: mp_lock].
    """
    from concurrent.futures import ProcessPoolExecutor
    if iterables and "chunksize" not in tqdm_kwargs:
        # default `chunksize=1` has poor performance for large iterables
        # (most time spent dispatching items to workers).
        longest_iterable_len = max(map(length_hint, iterables))
        if longest_iterable_len > 1000:
            from warnings import warn
            warn("Iterable length %d > 1000 but `chunksize` is not set."
                 " This may seriously degrade multiprocess performance."
                 " Set `chunksize=1` or more." % longest_iterable_len,
                 TqdmWarning, stacklevel=2)
    if "lock_name" not in tqdm_kwargs:
        tqdm_kwargs = tqdm_kwargs.copy()
        tqdm_kwargs["lock_name"] = "mp_lock"
    return _executor_map(ProcessPoolExecutor, fn, *iterables, **tqdm_kwargs)
