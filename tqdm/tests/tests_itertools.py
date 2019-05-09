import itertools

from tqdm import itertools as it

import pytest


_lengthless_generator = (i for i in range(5))


def test_zip():
    for args in [(range(5), range(5)),
                 (range(5), range(10))]:
        assert len(it.zip(*args)) == len(list(zip(*args)))
    with pytest.raises(TypeError):
        len(it.zip(range(5), _lengthless_generator))


def test_product():
    for args, kwargs in [((range(5), range(10)), {}),
                         ((range(5), range(10)), {"repeat": 2})]:
        assert len(it.product(*args, **kwargs)) \
            == len(list(itertools.product(*args, **kwargs)))
    with pytest.raises(TypeError):
        len(it.product(range(5), _lengthless_generator))


def test_zip_longest():
    for args in [(range(5), range(5)),
                 (range(5), range(10))]:
        assert len(it.zip_longest(*args)) \
            == len(list(itertools.zip_longest(*args)))
    with pytest.raises(TypeError):
        len(it.zip_longest(range(5), _lengthless_generator))
