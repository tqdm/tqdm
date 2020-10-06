"""
Tests for `tqdm.contrib.itertools`.
"""
from tqdm.contrib.itertools import product
from tests_tqdm import TestWithInstancesCheck, StringIO, closing
import itertools


class NoLenIter(object):
    def __init__(self, iterable):
        self._it = iterable

    def __iter__(self):
        for i in self._it:
            yield i


class TestTqdmItertools(TestWithInstancesCheck):
    def test_product(self):
        """Test contrib.itertools.product"""
        with closing(StringIO()) as our_file:
            a = range(9)
            assert list(product(a, a[::-1], file=our_file)) == \
                list(itertools.product(a, a[::-1]))

            assert list(product(a, NoLenIter(a), file=our_file)) == \
                list(itertools.product(a, NoLenIter(a)))
