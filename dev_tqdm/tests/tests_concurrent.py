"""
Tests for `tqdm.contrib.concurrent`.
"""
from warnings import catch_warnings
from tqdm.contrib.concurrent import thread_map, process_map
from tests_tqdm import with_setup, pretest, posttest, SkipTest, StringIO, \
    closing


def incr(x):
    """Dummy function"""
    return x + 1


@with_setup(pretest, posttest)
def test_thread_map():
    """Test contrib.concurrent.thread_map"""
    with closing(StringIO()) as our_file:
        a = range(9)
        b = [i + 1 for i in a]
        try:
            assert thread_map(lambda x: x + 1, a, file=our_file) == b
        except ImportError:
            raise SkipTest
        assert thread_map(incr, a, file=our_file) == b


@with_setup(pretest, posttest)
def test_process_map():
    """Test contrib.concurrent.process_map"""
    with closing(StringIO()) as our_file:
        a = range(9)
        b = [i + 1 for i in a]
        try:
            assert process_map(incr, a, file=our_file) == b
        except ImportError:
            raise SkipTest


def test_chunksize_warning():
    """Test contrib.concurrent.process_map chunksize warnings"""
    try:
        from unittest.mock import patch
    except ImportError:
        raise SkipTest

    for iterables, should_warn in [
        ([], False),
        (['x'], False),
        ([()], False),
        (['x', ()], False),
        (['x' * 1001], True),
        (['x' * 100, ('x',) * 1001], True),
    ]:
        with patch('tqdm.contrib.concurrent._executor_map'):
            with catch_warnings(record=True) as w:
                process_map(incr, *iterables)
                assert should_warn == bool(w)
