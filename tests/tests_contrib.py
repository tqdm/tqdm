"""
Tests for `tqdm.contrib`.
"""
import sys

import pytest

from tqdm import tqdm
from tqdm.contrib import tenumerate, tmap, tzip

from .tests_tqdm import StringIO, closing, importorskip


def incr(x):
    """Dummy function"""
    return x + 1


@pytest.mark.parametrize("tqdm_kwargs", [{}, {"tqdm_class": tqdm}])
def test_enumerate(tqdm_kwargs):
    """Test contrib.tenumerate"""
    with closing(StringIO()) as our_file:
        a = range(9)
        assert list(tenumerate(a, file=our_file, **tqdm_kwargs)) == list(enumerate(a))
        assert list(tenumerate(a, 42, file=our_file, **tqdm_kwargs)) == list(
            enumerate(a, 42)
        )
    with closing(StringIO()) as our_file:
        _ = list(tenumerate(iter(a), file=our_file, **tqdm_kwargs))
        assert "100%" not in our_file.getvalue()
    with closing(StringIO()) as our_file:
        _ = list(tenumerate(iter(a), file=our_file, total=len(a), **tqdm_kwargs))
        assert "100%" in our_file.getvalue()


def test_enumerate_numpy():
    """Test contrib.tenumerate(numpy.ndarray)"""
    np = importorskip("numpy")
    with closing(StringIO()) as our_file:
        a = np.random.random((42, 7))
        assert list(tenumerate(a, file=our_file)) == list(np.ndenumerate(a))


@pytest.mark.parametrize("tqdm_kwargs", [{}, {"tqdm_class": tqdm}])
def test_zip(tqdm_kwargs):
    """Test contrib.tzip"""
    with closing(StringIO()) as our_file:
        a = range(9)
        b = [i + 1 for i in a]
        if sys.version_info[:1] < (3,):
            assert tzip(a, b, file=our_file, **tqdm_kwargs) == zip(a, b)
        else:
            gen = tzip(a, b, file=our_file, **tqdm_kwargs)
            assert gen != list(zip(a, b))
            assert list(gen) == list(zip(a, b))


@pytest.mark.parametrize("tqdm_kwargs", [{}, {"tqdm_class": tqdm}])
def test_map(tqdm_kwargs):
    """Test contrib.tmap"""
    with closing(StringIO()) as our_file:
        a = range(9)
        b = [i + 1 for i in a]
        if sys.version_info[:1] < (3,):
            assert tmap(lambda x: x + 1, a, file=our_file, **tqdm_kwargs) == map(
                incr, a
            )
        else:
            gen = tmap(lambda x: x + 1, a, file=our_file, **tqdm_kwargs)
            assert gen != b
            assert list(gen) == b
