"""
Thin wrappers around `concurrent.futures`.
"""
import sys
from contextlib import contextmanager
from operator import length_hint

from ..auto import tqdm as tqdm_auto
from ..std import TqdmWarning

__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['thread_map', 'process_map', 'interpreter_map']


class _InterpreterLock:
    """Reentrant lock backed by a cross-interpreter queue."""
    from threading import get_ident
    from time import monotonic as _time

    def __init__(self, queue):
        from threading import RLock
        self._queue = queue
        self._lock = RLock()
        self._owner = None
        self._depth = 0

    def acquire(self, blocking=True, timeout=-1):
        from queue import Empty
        start = self._time()
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
                remaining = max(0, timeout - (self._time() - start))
                self._queue.get(timeout=remaining)
        except Empty:
            self._lock.release()
            return False
        self._owner = self.get_ident()
        self._depth = 1
        return True

    def release(self):
        if self._owner != self.get_ident():
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


def _get_interpreter_init(tqdm_class, lock_queue_id):
    """Return an initializer which bootstraps the parent import path and lock."""
    code = (
        "import sys\n"
        f"sys.path[:] = {sys.path!r}\n"
        "from concurrent import interpreters\n"
        "from importlib import import_module\n"
        "from tqdm.contrib.concurrent import _InterpreterLock\n"
        f"tqdm_class = import_module({tqdm_class.__module__!r})\n"
        f"for name in {tqdm_class.__qualname__.split('.')!r}:\n"
        "    tqdm_class = getattr(tqdm_class, name)\n"
        "tqdm_class.monitor_interval = 0\n"
        f"tqdm_class.set_lock(_InterpreterLock(interpreters.Queue({lock_queue_id!r})))")
    return exec, (code,)


def _min_map_len(iterables):
    """min(map(length_hint, iterables), default=0)"""
    return min((n for it in iterables if (n := length_hint(it, -1)) >= 0), default=0)


def _executor_map(
    PoolExecutor, fn, *iterables, max_workers=None, timeout=None, chunksize=1, lock_name="",
    tqdm_class=tqdm_auto, smoothing=0.0, _lock=None, _initializer=None, _initargs=None,
    **tqdm_kwargs
):
    """
    Implementation of `thread_map`, `process_map` and `interpreter_map`.

    Parameters
    ----------
    max_workers  : int
    timeout  : int
    buffersize  : int
        Requires Python>=3.14.
    thread_name_prefix  : str
    max_tasks_per_child  : int
    mp_context  : str
    """
    kwargs = tqdm_kwargs.copy()
    if 'total' not in kwargs:
        kwargs['total'] = _min_map_len(iterables)
    map_kwargs = {}
    if 'buffersize' in kwargs:
        map_kwargs['buffersize'] = kwargs.pop('buffersize')
    pool_kwargs = {}
    for k in ('thread_name_prefix', 'max_tasks_per_child', 'mp_context'):
        if k in kwargs:
            pool_kwargs[k] = kwargs.pop(k)
    dynamic_miniters = None
    if kwargs['total'] and 'miniters' not in kwargs:
        try:
            from os import process_cpu_count as cpu_count
        except ImportError:
            from os import cpu_count
        # thread & process pools have different default workers, but we KISS here
        rough_max = max_workers or min(32, (cpu_count() or 1) + 4)
        if kwargs['total'] > rough_max:
            kwargs['miniters'] = rough_max
            dynamic_miniters = True
    with ensure_lock(tqdm_class, lock_name=lock_name, lock=_lock) as lk:
        # share lock in case workers are already using `tqdm`
        if _initializer is None:
            _initializer = tqdm_class.set_lock
            _initargs = (lk,)
        with PoolExecutor(max_workers=max_workers, initializer=_initializer, initargs=_initargs,
                          **pool_kwargs) as ex:
            with tqdm_class(smoothing=smoothing, **kwargs) as pbar:
                if dynamic_miniters is not None:
                    pbar.dynamic_miniters = True
                orisubmit = ex.submit

                def patchsubmit(*args, **kwargs):
                    fut = orisubmit(*args, **kwargs)
                    fut.add_done_callback(lambda _: pbar.update())
                    return fut
                ex.submit = patchsubmit
                return list(ex.map(
                    fn, *iterables, timeout=timeout, chunksize=chunksize, **map_kwargs))


def thread_map(fn, *iterables, **tqdm_kwargs):
    """
    Equivalent of `list(map(fn, *iterables))`
    driven by `concurrent.futures.ThreadPoolExecutor`.

    Parameters
    ----------
    max_workers  : int, optional
        Maximum number of workers to spawn; passed to `concurrent.futures.ThreadPoolExecutor`.
    thread_name_prefix  : str, optional
        Passed to `concurrent.futures.ThreadPoolExecutor` [default: ''].
    timeout  : int or float, optional
        Seconds to wait before raising `TimeoutError` if `__next__` is called and the
        result isn't available. [default: None].
    buffersize  : int, optional
        Requires Python>=3.14 [default: None].
    tqdm_class  : optional
        `tqdm` class to use for bars [default: tqdm.auto.tqdm].
    smoothing  : float, optional
        Passed to `tqdm_class`; the [default: 0] is average (due to erratic update frequency).
    lock_name  : str, optional
        Member of `tqdm_class.get_lock()` to use [default: ''].
    """
    from concurrent.futures import ThreadPoolExecutor
    return _executor_map(ThreadPoolExecutor, fn, *iterables, **tqdm_kwargs)


def interpreter_map(fn, *iterables, **tqdm_kwargs):
    """
    Equivalent of `list(map(fn, *iterables))`
    driven by `concurrent.futures.InterpreterPoolExecutor` (Python 3.14+).

    Parameters
    ----------
    Same as `thread_map`.

    Notes
    -----
    `fn`, its arguments, and its return values must be pickleable.
    Worker progress bars using the same `tqdm_class` share a cross-interpreter write lock.
    """
    from concurrent import interpreters
    from concurrent.futures import InterpreterPoolExecutor
    lock_queue = interpreters.create_queue()
    lock_queue.put(None)
    tqdm_class = tqdm_kwargs.get("tqdm_class", tqdm_auto)
    initializer, initargs = _get_interpreter_init(tqdm_class, lock_queue.id)
    return _executor_map(
        InterpreterPoolExecutor, fn, *iterables, _lock=_InterpreterLock(lock_queue),
        _initializer=initializer, _initargs=initargs, **tqdm_kwargs)


def process_map(fn, *iterables, lock_name="mp_lock", **tqdm_kwargs):
    """
    Equivalent of `list(map(fn, *iterables))`
    driven by `concurrent.futures.ProcessPoolExecutor`.

    Parameters
    ----------
    max_workers  : int, optional
        Maximum number of workers to spawn; passed to `concurrent.futures.ProcessPoolExecutor`.
    timeout  : int or float, optional
        Seconds to wait before raising `TimeoutError` if `__next__` is called and the
        result isn't available. [default: None].
    chunksize  : int, optional
        Approximate size of chunks sent to worker processes; passed to
        `concurrent.futures.ProcessPoolExecutor.map`. [default: 1].
    buffersize  : int, optional
        Requires Python>=3.14 [default: None].
    max_tasks_per_child  : int, optional
        Maximum number of tasks a worker process can complete before being replaced
        with a new process; passed to `concurrent.futures.ProcessPoolExecutor`.
    mp_context  : multiprocessing.BaseContext, optional
        Multiprocessing context to use, e.g. `multiprocessing.get_context('fork')`.
    lock_name  : str, optional
        Member of `tqdm_class.get_lock()` to use [default: mp_lock].
    tqdm_class  : optional
        `tqdm` class to use for bars [default: tqdm.auto.tqdm].
    smoothing  : float, optional
        Passed to `tqdm_class`; the [default: 0] is average (due to erratic update frequency).
    """
    from concurrent.futures import ProcessPoolExecutor
    if iterables and 'chunksize' not in tqdm_kwargs:
        # default `chunksize=1` has poor performance for large iterables
        # (most time spent dispatching items to workers).
        shortest_iterable_len = _min_map_len(iterables)
        if shortest_iterable_len > 1000:
            from warnings import warn
            warn("Iterable length %d > 1000 but `chunksize` is not set."
                 " This may seriously degrade multiprocess performance."
                 " Set `chunksize=1` or more." % shortest_iterable_len,
                 TqdmWarning, stacklevel=2)
    return _executor_map(ProcessPoolExecutor, fn, *iterables, lock_name=lock_name, **tqdm_kwargs)
