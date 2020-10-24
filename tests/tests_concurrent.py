"""
Tests for `tqdm.contrib.concurrent`.
"""
from warnings import catch_warnings

from tqdm.contrib.concurrent import thread_map, process_map
from .tests_tqdm import pretest_posttest  # NOQA, pylint: disable=unused-import
from .tests_tqdm import importorskip, skip, StringIO, closing


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


def test_process_map():
    """Test contrib.concurrent.process_map"""
    with closing(StringIO()) as our_file:
        a = range(9)
        b = [i + 1 for i in a]
        try:
            assert process_map(incr, a, file=our_file) == b
        except ImportError as err:
            skip(str(err))


def test_chunksize_warning():
    """Test contrib.concurrent.process_map chunksize warnings"""
    patch = importorskip("unittest.mock").patch

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
