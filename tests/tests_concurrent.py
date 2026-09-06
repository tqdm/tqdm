import sys
from contextlib import nullcontext
from threading import RLock

from pytest import mark, raises, skip, warns

from tqdm import TqdmWarning, tqdm
from tqdm.contrib import concurrent
from tqdm.contrib.concurrent import ensure_lock, interpreter_map, process_map, thread_map


def dummy_func(x):
    return x + 1


def failing_func(x):
    raise ValueError("worker failed")


@mark.parametrize("error", [None, ValueError, KeyboardInterrupt])
def test_ensure_lock_restore(error, monkeypatch):
    original_lock, temporary_lock = RLock(), RLock()
    monkeypatch.setattr(tqdm, '_lock', original_lock, raising=False)
    with raises(error, match="test failure") if error else nullcontext():
        with ensure_lock(tqdm, lock=temporary_lock) as lock:
            assert lock is temporary_lock
            assert tqdm.get_lock() is temporary_lock
            if error:
                raise error("test failure")
    assert tqdm.get_lock() is original_lock


@mark.parametrize("error", [None, ValueError, KeyboardInterrupt])
def test_ensure_lock_remove(error, monkeypatch):
    monkeypatch.setattr(tqdm, '_lock', None, raising=False)
    monkeypatch.delattr(tqdm, '_lock')
    with raises(error, match="test failure") if error else nullcontext():
        with ensure_lock(tqdm) as lock:
            assert tqdm.get_lock() is lock
            if error:
                raise error("test failure")
    assert not hasattr(tqdm, '_lock')


def test_ensure_lock_nested_exception(monkeypatch):
    original_lock, outer_lock, inner_lock = RLock(), RLock(), RLock()
    monkeypatch.setattr(tqdm, '_lock', original_lock, raising=False)
    with ensure_lock(tqdm, lock=outer_lock):
        with raises(ValueError, match="inner failure"):
            with ensure_lock(tqdm, lock=inner_lock):
                assert tqdm.get_lock() is inner_lock
                raise ValueError("inner failure")
        assert tqdm.get_lock() is outer_lock
    assert tqdm.get_lock() is original_lock


@mark.parametrize("mapper", [interpreter_map, process_map, thread_map])
def test_concurrent_map(mapper, caperr):
    a = range(9)
    b = [i + 1 for i in a]
    try:
        assert mapper(dummy_func, a, miniters=1) == b
    except ImportError as err:
        skip(str(err))
    err = caperr()
    assert '0/9' in err


@mark.parametrize("mapper,lock_name", [(interpreter_map, ''), (process_map, 'mp_lock'),
                                       (thread_map, 'th_lock')])
@mark.parametrize("worker_error", [False, True])
def test_concurrent_map_exception(mapper, lock_name, worker_error, monkeypatch):
    original_lock = tqdm.get_lock()
    monkeypatch.setattr(tqdm, '_lock', original_lock)
    fn = failing_func if worker_error else dummy_func
    max_workers = 1 if worker_error else 0
    with raises(ValueError, match="worker failed" if worker_error else "max_workers"):
        try:
            mapper(fn, [0], max_workers=max_workers, lock_name=lock_name,
                   tqdm_class=tqdm, disable=True)
        except ImportError as err:
            skip(str(err))
    assert tqdm.get_lock() is original_lock


def check_lock(args):
    """Check that another interpreter cannot acquire a held tqdm lock"""
    from os.path import exists
    from time import sleep

    from tqdm.auto import tqdm

    held, checked, result, role = args
    assert tqdm.monitor_interval == 0
    lock = tqdm.get_lock()
    if role == 'holder':
        with lock, lock:  # also check that the lock is reentrant
            with open(held, 'w'):
                pass
            while not exists(checked):
                sleep(0.01)
    else:
        while not exists(held):
            sleep(0.01)
        acquired = lock.acquire(False)
        if acquired:
            lock.release()
        with open(result, 'w') as result_file:
            result_file.write(str(acquired))
        with open(checked, 'w'):
            pass
    return role


@mark.skipif(sys.version_info < (3, 14), reason="requires Python 3.14+")
def test_interpreter_map_lock(tmp_path):
    """Test interpreter workers share tqdm's write lock"""
    held = str(tmp_path / 'held')
    checked = str(tmp_path / 'checked')
    result = tmp_path / 'result'
    roles = ['holder', 'contender']
    args = [(held, checked, str(result), role) for role in roles]
    try:
        assert interpreter_map(check_lock, args, max_workers=2, disable=True) == roles
    except ImportError as err:
        skip(str(err))
    assert result.read_text() == 'False'


@mark.parametrize("iterables,should_warn", [([], False), (['x'], False), ([()], False),
                                            (['x', ()], False), (['x' * 1001], True),
                                            (['x' * 100, ('x',) * 1001], False),
                                            (['x' * 1001, ('x',) * 100], False),
                                            (['x' * 1001, ('x',) * 1001], True)])
def test_chunksize_warning(iterables, should_warn, monkeypatch):
    monkeypatch.setattr(concurrent, '_executor_map', lambda *_, **__: None)
    if should_warn:
        with warns(TqdmWarning):
            process_map(dummy_func, *iterables)
    else:
        process_map(dummy_func, *iterables)
