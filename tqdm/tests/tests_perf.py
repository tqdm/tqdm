from contextlib import contextmanager

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

# Use relative/cpu timer to have reliable timings when there is a sudden load
try:
    from time import process_time
except ImportError:
    from time import clock
    process_time = clock


# def cpu_sleep(t):
#     '''Sleep the given amount of cpu time'''
#     start = process_time()
#     while((process_time() - start) < t):
#         pass


def get_relative_time(prevtime=0):
    return process_time() - prevtime


@contextmanager
def relative_timer():
    start = process_time()
    elapser = lambda: process_time() - start
    yield lambda: elapser()
    spent = process_time() - start
    elapser = lambda: spent


class MockFileNoWrite(StringIO):
    """ Wraps StringIO to mock a file with no I/O """
    def write(self, data):
        return


def test_iter_overhead():
    """ Test overhead of iteration based tqdm """
    total = int(1e6)

    with closing(MockFileNoWrite()) as our_file:
        a = 0
        with relative_timer() as time_tqdm:
            for i in trange(total, file=our_file):
                a += i
        assert(a == (total * total - total) / 2.0)

        a = 0
        with relative_timer() as time_bench:
            for i in _range(total):
                a += i
                our_file.write(a)

    # Compute relative overhead of tqdm against native range()
    try:
        assert(time_tqdm() < 3 * time_bench())
    except AssertionError:
        raise AssertionError('trange(%g): %f, range(%g): %f' %
                             (total, time_tqdm(), total, time_bench()))


def test_manual_overhead():
    """ Test overhead of manual tqdm """
    total = int(1e6)

    with closing(MockFileNoWrite()) as our_file:
        t = tqdm(total=total * 10, file=our_file, leave=True)
        a = 0
        with relative_timer() as time_tqdm:
            for i in _range(total):
                a += i
                t.update(10)

        a = 0
        with relative_timer() as time_bench:
            for i in _range(total):
                a += i
                our_file.write(a)

    # Compute relative overhead of tqdm against native range()
    try:
        assert(time_tqdm() < 10 * time_bench())
    except AssertionError:
        raise AssertionError('tqdm(%g): %f, range(%g): %f' %
                             (total, time_tqdm(), total, time_bench()))


def test_iter_overhead_hard():
    """ Test overhead of iteration based tqdm (hard) """
    total = int(1e5)

    with closing(MockFileNoWrite()) as our_file:
        a = 0
        with relative_timer() as time_tqdm:
            for i in trange(total, file=our_file, leave=True,
                            miniters=1, mininterval=0, maxinterval=0):
                a += i
        assert(a == (total * total - total) / 2.0)

        a = 0
        with relative_timer() as time_bench:
            for i in _range(total):
                a += i
                our_file.write(("%i" % a) * 40)

    # Compute relative overhead of tqdm against native range()
    try:
        assert(time_tqdm() < 60 * time_bench())
    except AssertionError:
        raise AssertionError('trange(%g): %f, range(%g): %f' %
                             (total, time_tqdm(), total, time_bench()))


def test_manual_overhead_hard():
    """ Test overhead of manual tqdm (hard) """
    total = int(1e5)

    with closing(MockFileNoWrite()) as our_file:
        t = tqdm(total=total * 10, file=our_file, leave=True,
                 miniters=1, mininterval=0, maxinterval=0)
        a = 0
        with relative_timer() as time_tqdm:
            for i in _range(total):
                a += i
                t.update(10)

        a = 0
        with relative_timer() as time_bench:
            for i in _range(total):
                a += i
                our_file.write(("%i" % a) * 40)

    # Compute relative overhead of tqdm against native range()
    try:
        assert(time_tqdm() < 100 * time_bench())
    except AssertionError:
        raise AssertionError('tqdm(%g): %f, range(%g): %f' %
                             (total, time_tqdm(), total, time_bench()))
