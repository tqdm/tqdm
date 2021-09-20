"""
Tests for `tqdm.contrib.itertools`.
"""
import itertools as it

from tqdm.contrib.itertools import product

from .tests_tqdm import StringIO, closing


class NoLenIter(object):
    def __init__(self, iterable):
        self._it = iterable

    def __iter__(self):
        for i in self._it:
            yield i


def test_product():
    """Test contrib.itertools.product"""
    with closing(StringIO()) as our_file:
        a = range(9)
        assert list(product(a, a[::-1], file=our_file)) == list(it.product(a, a[::-1]))

        assert list(product(a, NoLenIter(a), file=our_file)) == list(it.product(a, NoLenIter(a)))
