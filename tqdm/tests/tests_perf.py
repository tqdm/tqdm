from time import time

from tqdm import trange
from tqdm import tqdm

try:
    from StringIO import StringIO
except:
    from io import StringIO
# Ensure we can use `with closing(...) as ... :` syntax
if getattr(StringIO, '__exit__', False) and \
   getattr(StringIO, '__enter__', False):
    def closing(arg):
        return arg
else:
    from contextlib import closing

try:
    _range = xrange
except:
    _range = range


_tic_toc = [None]


def tic():
    _tic_toc[0] = time()


def toc():
    return time() - _tic_toc[0]


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


def test_manual_overhead():
    """ Test overhead of manual tqdm """
    total = int(1e6)

    with closing(StringIO()) as our_file:
        t = tqdm(total=total * 10, file=our_file, leave=True)
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
