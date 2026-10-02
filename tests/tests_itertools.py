"""
Tests for `tqdm.contrib.itertools`.
"""
import itertools as it

from pytest import importorskip, mark, raises

from tqdm.contrib import itertools as tit


def no_len(iterable):
    yield from iterable


def test_chain(caperr):
    a = range(9)
    assert list(tit.chain(a, a)) == list(it.chain(a, a))
    assert "18/18" in caperr()

    assert list(tit.chain(a, no_len(a))) == list(it.chain(a, no_len(a)))
    res = caperr()
    assert "18it" in res
    assert "18/18" not in res

    assert list(tit.chain(a, no_len(a), total=18)) == list(it.chain(a, no_len(a)))
    assert "18/18" in caperr()


def test_product(caperr):
    a = range(9)
    assert list(tit.product(a, a)) == list(it.product(a, a))
    assert "81/81" in caperr()

    assert list(tit.product(a, no_len(a))) == list(it.product(a, no_len(a)))
    res = caperr()
    assert "81it" in res
    assert "81/81" not in res

    assert list(tit.product(a, no_len(a), total=81)) == list(it.product(a, no_len(a)))
    assert "81/81" in caperr()


@mark.parametrize('iterable', [[], range(3)])
@mark.parametrize('repeat', [-1, -2])
def test_product_negative_repeat(iterable, repeat):
    with raises(ValueError, match='repeat argument cannot be negative'):
        list(tit.product(iterable, repeat=repeat))


@mark.parametrize('sized', [True, False])
@mark.parametrize('total', [None, 3])
def test_product_zero_repeat(caperr, sized, total):
    iterable = range(3) if sized else no_len(range(3))
    assert list(tit.product(iterable, repeat=0, total=total)) == [()]
    assert f"1/{1 if total is None else total}" in caperr()


def test_product_repeat_index(caperr):
    class Repeat:
        def __index__(self):
            return 2

    a = range(3)
    assert list(tit.product(a, repeat=Repeat())) == list(it.product(a, repeat=Repeat()))
    assert "9/9" in caperr()


def test_product_numpy_repeat(caperr):
    np = importorskip('numpy')
    generator = tit.product(range(16), repeat=np.int64(16), bar_format='{total}')
    assert next(generator) == (0,) * 16
    generator.close()
    assert str(16 ** 16) in caperr()


def test_permutations(caperr):
    a = range(5)
    assert list(tit.permutations(a)) == list(it.permutations(a))
    assert "120/120" in caperr()

    assert list(tit.permutations(a, 10)) == list(it.permutations(a, 10)) == []
    caperr()

    assert list(tit.permutations(no_len(a))) == list(it.permutations(no_len(a)))
    res = caperr()
    assert "120it" in res
    assert "120/120" not in res

    assert list(tit.permutations(no_len(a), total=120)) == list(it.permutations(no_len(a)))
    assert "120/120" in caperr()


def test_combinations(caperr):
    a = range(9)
    assert list(tit.combinations(a, 3)) == list(it.combinations(a, 3))
    assert "84/84" in caperr()

    assert list(tit.combinations(a, 10)) == list(it.combinations(a, 10)) == []
    caperr()

    assert list(tit.combinations(no_len(a), 3)) == list(it.combinations(no_len(a), 3))
    res = caperr()
    assert "84it" in res
    assert "84/84" not in res

    assert list(tit.combinations(no_len(a), 3, total=84)) == list(it.combinations(no_len(a), 3))
    assert "84/84" in caperr()


def test_combinations_with_replacement(caperr):
    a = range(9)
    assert list(tit.combinations_with_replacement(a, 3)) == list(
        it.combinations_with_replacement(a, 3))
    assert "165/165" in caperr()

    assert list(tit.combinations_with_replacement(no_len(a), 3)) == list(
        it.combinations_with_replacement(no_len(a), 3))
    res = caperr()
    assert "165it" in res
    assert "165/165" not in res

    assert list(tit.combinations_with_replacement(no_len(a), 3, total=165)) == list(
        it.combinations_with_replacement(no_len(a), 3))
    assert "165/165" in caperr()

    a = range(5)
    assert list(tit.combinations_with_replacement(a, 6)) == list(
        it.combinations_with_replacement(a, 6))
    assert "210/210" in caperr()


@mark.skipif(not hasattr(it, 'batched'), reason="NotFound: itertools.batched")
def test_batched(caperr):
    a = range(10)
    assert list(tit.batched(a, 3)) == list(it.batched(a, 3))
    assert "12/12" in caperr()

    assert list(tit.batched(no_len(a), 3)) == list(it.batched(no_len(a), 3))
    res = caperr()
    assert "12it" in res
    assert "12/12" not in res

    assert list(tit.batched(no_len(a), 3, total=12)) == list(it.batched(no_len(a), 3))
    assert "12/12" in caperr()
