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


@mark.skipif(sys.version_info < (3, 14), reason="requires Python 3.14+")
def test_interpreter_map(capsys):
    """Test contrib.concurrent.interpreter_map"""
    a = range(9)
    b = [i + 1 for i in a]
    try:
        assert interpreter_map(incr, a) == b
    except ImportError as err:
        skip(str(err))
    out, err = capsys.readouterr()
    assert not out
    assert '9/9' in err


def test_process_map():
    """Test contrib.concurrent.process_map"""
    with closing(StringIO()) as our_file:
        a = range(9)
        b = [i + 1 for i in a]
        try:
            assert process_map(incr, a, file=our_file) == b
        except ImportError as err:
            skip(str(err))


def test_process_map_chunksize_progress():
    """process_map should count items, not chunks, when chunksize > 1 (#1791)"""
    with closing(StringIO()) as our_file:
        a = range(101)
        b = [i + 1 for i in a]
        try:
            assert process_map(incr, a, chunksize=10, file=our_file, miniters=1) == b
        except ImportError as err:
            skip(str(err))
        assert '101/101' in our_file.getvalue()


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
def test_chunksize_warning(iterables, should_warn):
    """Test contrib.concurrent.process_map chunksize warnings"""
    patch = importorskip('unittest.mock').patch
    with patch('tqdm.contrib.concurrent._executor_map'):
        if should_warn:
            warns(TqdmWarning, process_map, incr, *iterables)
        else:
            process_map(incr, *iterables)
