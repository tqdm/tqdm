import sys
import threading
import time

from pytest import mark, raises, skip, warns

from tqdm import TqdmWarning
from tqdm.contrib import concurrent
from tqdm.contrib.concurrent import interpreter_map, process_map, thread_map


def dummy_func(x):
    return x + 1


def test_min_map_len():
    assert concurrent._min_map_len([]) == 0
    assert concurrent._min_map_len([(i for i in range(9))]) == 0
    assert concurrent._min_map_len([(i for i in range(9)), range(5)]) == 5


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


@mark.parametrize("mapper", [interpreter_map, process_map, thread_map])
def test_concurrent_map_unknown_len(mapper, caperr):
    b = [i + 1 for i in range(9)]
    try:
        assert mapper(dummy_func, (i for i in range(9))) == b
    except ImportError as err:
        skip(str(err))
    err = caperr()
    assert '9it [' in err


def test_concurrent_map_buffersize():
    in_flight = 0
    max_in_flight = 0
    lock = threading.Lock()

    def work(x):
        nonlocal in_flight, max_in_flight
        with lock:
            in_flight += 1
            max_in_flight = max(max_in_flight, in_flight)
        time.sleep(0.01)
        with lock:
            in_flight -= 1
        return x + 1

    assert thread_map(work, range(10), max_workers=4, buffersize=2, disable=True) == list(
        range(1, 11)
    )
    assert max_in_flight <= 2
    assert process_map(dummy_func, range(6), max_workers=2, buffersize=2, disable=True) == list(
        range(1, 7)
    )
    with raises(ValueError):
        thread_map(dummy_func, range(3), buffersize=0, disable=True)


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
    result = str(tmp_path / 'result')
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
