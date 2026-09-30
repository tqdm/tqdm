from pytest import importorskip, mark

from tqdm import tqdm
from tqdm.contrib import tenumerate, tmap, tzip


@mark.parametrize("tqdm_kwargs", [{}, {"tqdm_class": tqdm}])
def test_enumerate(tqdm_kwargs, caperr):
    a = range(9)
    assert list(tenumerate(a, **tqdm_kwargs)) == list(enumerate(a))
    assert list(tenumerate(a, 42, **tqdm_kwargs)) == list(enumerate(a, 42))
    caperr()

    _ = list(tenumerate(iter(a), **tqdm_kwargs))
    assert "100%" not in caperr()
    _ = list(tenumerate(iter(a), total=len(a), **tqdm_kwargs))
    assert "100%" in caperr()


def test_enumerate_numpy(caperr):
    np = importorskip("numpy")
    a = np.random.random((42, 7))
    assert list(tenumerate(a)) == list(np.ndenumerate(a))
    assert "100%" in caperr()


@mark.parametrize("tqdm_kwargs", [{}, {"tqdm_class": tqdm}])
def test_zip(tqdm_kwargs):
    a = range(9)
    b = [i + 1 for i in a]
    gen = tzip(a, b, **tqdm_kwargs)
    assert gen != list(zip(a, b))
    assert list(gen) == list(zip(a, b))


@mark.parametrize("lengths", [(9, 3), (3, 9), (9, 0), (0, 9), (7, 5, 2)])
@mark.parametrize("wrapper", [tzip, tmap])
def test_zip_shortest_total(lengths, wrapper, tmp_file):
    bars = []

    class RecordingTqdm(tqdm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            bars.append(self)

    sequences = [range(length) for length in lengths]
    args = sequences if wrapper is tzip else [lambda *values: values, *sequences]
    assert list(wrapper(*args, tqdm_class=RecordingTqdm, file=tmp_file,
                        mininterval=0)) == list(zip(*sequences))
    assert bars[0].total == min(lengths)
    assert bars[0].n == min(lengths)
    assert bars[0].disable


@mark.parametrize("total", [None, 0, 42])
def test_zip_explicit_total(total, tmp_file):
    bars = []

    class RecordingTqdm(tqdm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            bars.append(self)

    assert list(tzip(range(9), range(3), total=total, tqdm_class=RecordingTqdm,
                     file=tmp_file)) == list(zip(range(9), range(3)))
    assert bars[0].total == (3 if total is None else total)
    assert bars[0].n == 3


@mark.parametrize("unsized_first", [False, True])
def test_zip_unsized_total(unsized_first, tmp_file):
    bars = []

    class RecordingTqdm(tqdm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            bars.append(self)

    sequences = [range(9), iter(range(3))]
    if unsized_first:
        sequences.reverse()
    assert list(tzip(*sequences, tqdm_class=RecordingTqdm, file=tmp_file)) == [
        (0, 0), (1, 1), (2, 2)]
    assert bars[0].total is None
    assert bars[0].n == 3


@mark.parametrize("tqdm_kwargs", [{}, {"tqdm_class": tqdm}])
def test_map(tqdm_kwargs):
    a = range(9)
    b = [i + 1 for i in a]
    gen = tmap(lambda x: x + 1, a, **tqdm_kwargs)
    assert gen != b
    assert list(gen) == b
