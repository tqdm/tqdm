"""
Tests for `tqdm.contrib.concurrent`.
"""
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
