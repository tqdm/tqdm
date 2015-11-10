from time import time

try:
    from StringIO import StringIO
    _range = xrange
except:
    from io import StringIO
    _range = range

from tqdm import trange
from tqdm import tqdm


_tic_toc = [None]


def tic():
    _tic_toc[0] = time()


def toc():
    return time() - _tic_toc[0]


def test_iter_overhead():
    """ Test overhead of iteration based tqdm """
    total = int(1e6)

    our_file = StringIO()
    a = 0
    tic()
    for i in trange(total, file=our_file):  # pragma: no cover
        a = a + i
    time_tqdm = toc()
    our_file.close()

    a = 0
    tic()
    for i in _range(total):
        a = a + i
    time_bench = toc()

    # Compute relative overhead of tqdm against native range()
    try:
        assert(time_tqdm < 5 * time_bench)
    except AssertionError:
        raise AssertionError('trange(%g): %f, range(%g): %f' %
                             (total, time_tqdm, total, time_bench))

def test_manual_overhead():
    """ Test overhead of manual tqdm """
    total = int(1e6)

    our_file = StringIO()
    t = tqdm(total=total*10, file=our_file, leave=True)
    a = 0
    tic()
    for i in _range(total):
        a = a + i
        t.update(10)
    time_tqdm = toc()
    our_file.close()

    a = 0
    tic()
    for i in _range(total):
        a = a + i
    time_bench = toc()

    # Compute relative overhead of tqdm against native range()
    try:
        assert(time_tqdm < 12 * time_bench)
    except AssertionError:
        raise AssertionError('tqdm(%g): %f, range(%g): %f' %
                             (total, time_tqdm, total, time_bench))
