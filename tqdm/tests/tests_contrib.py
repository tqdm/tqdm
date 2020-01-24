"""
Tests for `tqdm.contrib`.
"""
import sys
from tqdm.contrib import tenumerate, tzip, tmap
from tests_tqdm import with_setup, pretest, posttest, SkipTest, StringIO, \
    closing


def incr(x):
    """Dummy function"""
    return x + 1


@with_setup(pretest, posttest)
def test_enumerate():
    """Test contrib.tenumerate"""
    with closing(StringIO()) as our_file:
        a = range(9)
        assert list(tenumerate(a, file=our_file)) == list(enumerate(a))
        assert list(tenumerate(a, 42, file=our_file)) == list(enumerate(a, 42))


@with_setup(pretest, posttest)
def test_enumerate_numpy():
    """Test contrib.tenumerate(numpy.ndarray)"""
    try:
        import numpy as np
    except ImportError:
        raise SkipTest
    with closing(StringIO()) as our_file:
        a = np.random.random((42, 1337))
        assert list(tenumerate(a, file=our_file)) == list(np.ndenumerate(a))


@with_setup(pretest, posttest)
def test_zip():
    """Test contrib.tzip"""
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
    """Test contrib.tmap"""
    with closing(StringIO()) as our_file:
        a = range(9)
        b = [i + 1 for i in a]
        if sys.version_info[:1] < (3,):
            assert tmap(lambda x: x + 1, a, file=our_file) == map(incr, a)
        else:
            gen = tmap(lambda x: x + 1, a, file=our_file)
            assert gen != b
            assert list(gen) == b
