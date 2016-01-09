from time import time

from tqdm import trange
from tqdm import tqdm

from tests_tqdm import with_setup, pretest, posttest, StringIO, closing, _range

_tic_toc = [None]


def tic():
    _tic_toc[0] = time()


def toc():
    return time() - _tic_toc[0]


@with_setup(pretest, posttest)
def test_iter_overhead():
    """ Test overhead of iteration based tqdm """
    total = int(1e6)

    with closing(StringIO()) as our_file:
        a = 0
        tic()
        for i in trange(total, file=our_file):
            a += i
        time_tqdm = toc()
        assert(a == (total * total - total) / 2.0)

    a = 0
    tic()
    for i in _range(total):
        a += i
    time_bench = toc()

    # Compute relative overhead of tqdm against native range()
    try:
        assert(time_tqdm < 9 * time_bench)
    except AssertionError:
        raise AssertionError('trange(%g): %f, range(%g): %f' %
                             (total, time_tqdm, total, time_bench))


@with_setup(pretest, posttest)
def test_manual_overhead():
    """ Test overhead of manual tqdm """
    total = int(1e6)

    with closing(StringIO()) as our_file:
        with tqdm(total=total * 10, file=our_file, leave=True) as t:
            a = 0
            tic()
            for i in _range(total):
                a += i
                t.update(10)
            time_tqdm = toc()

    a = 0
    tic()
    for i in _range(total):
        a += i
    time_bench = toc()

    # Compute relative overhead of tqdm against native range()
    try:
        assert(time_tqdm < 19 * time_bench)
    except AssertionError:
        raise AssertionError('tqdm(%g): %f, range(%g): %f' %
                             (total, time_tqdm, total, time_bench))
