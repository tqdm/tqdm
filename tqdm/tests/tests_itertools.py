"""
Tests for `tqdm.contrib.itertools`.
"""
from tqdm.contrib.itertools import product
from tests_tqdm import with_setup, pretest, posttest, StringIO, closing
import itertools


@with_setup(pretest, posttest)
def test_product():
    """Test contrib.itertools.product"""
    with closing(StringIO()) as our_file:
        a = range(9)
        b = a[::-1]
        assert list(product(a, b, file=our_file)) == \
            list(itertools.product(a, b))
