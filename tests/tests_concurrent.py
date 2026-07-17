"""
Tests for `tqdm.contrib.concurrent`.
"""
import sys

from pytest import warns

from tqdm.contrib.concurrent import interpreter_map, process_map, thread_map

from .tests_tqdm import StringIO, TqdmWarning, closing, importorskip, mark, skip


def incr(x):
    """Dummy function"""
    return x + 1


def check_lock(args):
    """Check that another interpreter cannot acquire a held tqdm lock."""
    from os.path import exists
    from time import sleep

    from tqdm.auto import tqdm

    held, checked, result, role = args
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


def test_thread_map():
    """Test contrib.concurrent.thread_map"""
    with closing(StringIO()) as our_file:
        a = range(9)
        b = [i + 1 for i in a]
        try:
            assert thread_map(lambda x: x + 1, a, file=our_file) == b
        except ImportError as err:
            skip(str(err))
        assert thread_map(incr, a, file=our_file) == b


def test_process_map():
    """Test contrib.concurrent.process_map"""
    with closing(StringIO()) as our_file:
        a = range(9)
        b = [i + 1 for i in a]
        try:
            assert process_map(incr, a, file=our_file) == b
        except ImportError as err:
            skip(str(err))


def test_interpreter_map():
    """Test contrib.concurrent.interpreter_map"""
    if sys.version_info < (3, 14):
        skip("requires Python 3.14+")
    with closing(StringIO()) as our_file:
        a = range(9)
        b = [i + 1 for i in a]
        assert interpreter_map(incr, a, file=our_file) == b


def test_interpreter_map_lock(tmp_path):
    """Test interpreter workers share tqdm's write lock"""
    if sys.version_info < (3, 14):
        skip("requires Python 3.14+")
    held = str(tmp_path / 'held')
    checked = str(tmp_path / 'checked')
    result = tmp_path / 'result'
    roles = ['holder', 'contender']
    args = [(held, checked, str(result), role) for role in roles]
    assert interpreter_map(check_lock, args, max_workers=2, disable=True) == roles
    assert result.read_text() == 'False'


@mark.parametrize("iterables,should_warn", [([], False), (['x'], False), ([()], False),
                                            (['x', ()], False), (['x' * 1001], True),
                                            (['x' * 100, ('x',) * 1001], True)])
def test_chunksize_warning(iterables, should_warn):
    """Test contrib.concurrent.process_map chunksize warnings"""
    patch = importorskip('unittest.mock').patch
    with patch('tqdm.contrib.concurrent._executor_map'):
        if should_warn:
            warns(TqdmWarning, process_map, incr, *iterables)
        else:
            process_map(incr, *iterables)
