from __future__ import division
import sys
from tqdm.contrib.wraps import tenumerate, tzip, tmap, thread_map, process_map
from tests_tqdm import with_setup, pretest, posttest, SkipTest, StringIO, \
    closing


def incr(x):
    return x + 1


@with_setup(pretest, posttest)
def test_enumerate():
    """Test contrib.wraps.tenumerate"""
    with closing(StringIO()) as our_file:
        a = range(9)
        assert list(tenumerate(a, file=our_file)) == list(enumerate(a))


@with_setup(pretest, posttest)
def test_enumerate_numpy():
    """Test contrib.wraps.tenumerate(numpy.ndarray)"""
    try:
        import numpy as np
    except ImportError:
        raise SkipTest
    with closing(StringIO()) as our_file:
        a = np.arange(9)
        assert list(tenumerate(a, file=our_file)) == list(np.ndenumerate(a))


@with_setup(pretest, posttest)
def test_zip():
    """Test contrib.wraps.tzip"""
    with closing(StringIO()) as our_file:
        a = range(9)
        b = [i + 1 for i in a]
        if sys.version_info[:1] < (3,):
            assert tzip(a, b, file=our_file) == zip(a, b)
        else:
            gen = tzip(a, b, file=our_file)
            assert gen != list(zip(a, b))
            assert list(gen) == list(zip(a, b))


@with_setup(pretest, posttest)
def test_map():
    """Test contrib.wraps.tmap"""
    with closing(StringIO()) as our_file:
        a = range(9)
        b = [i + 1 for i in a]
        if sys.version_info[:1] < (3,):
            assert tmap(lambda x: x + 1, a, file=our_file) == map(incr, a)
        else:
            gen = tmap(lambda x: x + 1, a, file=our_file)
            assert gen != b
            assert list(gen) == b


@with_setup(pretest, posttest)
def test_thread_map():
    """Test contrib.wraps.thread_map"""
    with closing(StringIO()) as our_file:
        a = range(9)
        b = [i + 1 for i in a]
        assert thread_map(lambda x: x + 1, a, file=our_file) == b
        assert thread_map(incr, a, file=our_file) == b


@with_setup(pretest, posttest)
def test_process_map():
    """Test contrib.wraps.process_map"""
    with closing(StringIO()) as our_file:
        a = range(9)
        b = [i + 1 for i in a]
        assert process_map(incr, a, file=our_file) == b
