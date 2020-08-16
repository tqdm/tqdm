"""
Tests for `tqdm.contrib.itertools`.
"""
import itertools

from tests_tqdm import StringIO, closing, posttest, pretest, with_setup

from tqdm.contrib.itertools import product


class NoLenIter(object):
    def __init__(self, iterable):
        self._it = iterable

    def __iter__(self):
        for i in self._it:
            yield i


@with_setup(pretest, posttest)
def test_product():
    """Test contrib.itertools.product"""
    with closing(StringIO()) as our_file:
        a = range(9)
        assert list(product(a, a[::-1], file=our_file)) == \
            list(itertools.product(a, a[::-1]))

        assert list(product(a, NoLenIter(a), file=our_file)) == \
            list(itertools.product(a, NoLenIter(a)))
