from __future__ import print_function, division

from nose.plugins.skip import SkipTest

from contextlib import contextmanager

import sys
from time import sleep, time

from tqdm import trange
from tqdm import tqdm

from tests_tqdm import with_setup, pretest, posttest, StringIO, closing, _range

# Use relative/cpu timer to have reliable timings when there is a sudden load
try:
    from time import process_time
except ImportError:
    from time import clock
    process_time = clock


def get_relative_time(prevtime=0):
    return process_time() - prevtime


def cpu_sleep(t):
    """Sleep the given amount of cpu time"""
    start = process_time()
    while (process_time() - start) < t:
        pass


def checkCpuTime(sleeptime=0.2):
    """Check if cpu time works correctly"""
    if checkCpuTime.passed:
        return True
    # First test that sleeping does not consume cputime
    start1 = process_time()
    sleep(sleeptime)
    t1 = process_time() - start1

    # secondly check by comparing to cpusleep (where we actually do something)
    start2 = process_time()
    cpu_sleep(sleeptime)
    t2 = process_time() - start2

    if abs(t1) < 0.0001 and (t1 < t2 / 10):
        return True
    raise SkipTest


checkCpuTime.passed = False


@contextmanager
def relative_timer():
    start = process_time()

    def elapser():
        return process_time() - start

    yield lambda: elapser()
    spent = process_time() - start

    def elapser():  # NOQA
        return spent


def retry_on_except(n=3):
    def wrapper(fn):
        def test_inner():
            for i in range(1, n + 1):
                try:
                    checkCpuTime()
                    fn()
                except SkipTest:
                    if i >= n:
                        raise
                else:
                    return

        test_inner.__doc__ = fn.__doc__
        return test_inner

    return wrapper


class MockIO(StringIO):
    """Wraps StringIO to mock a file with no I/O"""

    def write(self, data):
        return


def simple_progress(iterable=None, total=None, file=sys.stdout, desc='',
                    leave=False, miniters=1, mininterval=0.1, width=60):
    """Simple progress bar reproducing tqdm's major features"""
    n = [0]  # use a closure
    start_t = [time()]
    last_n = [0]
    last_t = [0]
    if iterable is not None:
        total = len(iterable)

    def format_interval(t):
        mins, s = divmod(int(t), 60)
        h, m = divmod(mins, 60)
        if h:
            return '{0:d}:{1:02d}:{2:02d}'.format(h, m, s)
        else:
            return '{0:02d}:{1:02d}'.format(m, s)

    def update_and_print(i=1):
        n[0] += i
        if (n[0] - last_n[0]) >= miniters:
            last_n[0] = n[0]

            if (time() - last_t[0]) >= mininterval:
                last_t[0] = time()  # last_t[0] == current time

                spent = last_t[0] - start_t[0]
                spent_fmt = format_interval(spent)
                rate = n[0] / spent if spent > 0 else 0
                if 0.0 < rate < 1.0:
                    rate_fmt = "%.2fs/it" % (1.0 / rate)
                else:
                    rate_fmt = "%.2fit/s" % rate

                frac = n[0] / total
                percentage = int(frac * 100)
                eta = (total - n[0]) / rate if rate > 0 else 0
                eta_fmt = format_interval(eta)

                # bar = "#" * int(frac * width)
                barfill = " " * int((1.0 - frac) * width)
                bar_length, frac_bar_length = divmod(int(frac * width * 10), 10)
                bar = '#' * bar_length
                frac_bar = chr(48 + frac_bar_length) if frac_bar_length \
                    else ' '

                file.write("\r%s %i%%|%s%s%s| %i/%i [%s<%s, %s]" %
                           (desc, percentage, bar, frac_bar, barfill, n[0],
                            total, spent_fmt, eta_fmt, rate_fmt))

                if n[0] == total and leave:
                    file.write("\n")
                file.flush()

    def update_and_yield():
        for elt in iterable:
            yield elt
            update_and_print()

    update_and_print(0)
    if iterable is not None:
        return update_and_yield()
    else:
        return update_and_print


def assert_performance(thresh, name_left, time_left, name_right, time_right):
    """raises if time_left > thresh * time_right"""
    if time_left > thresh * time_right:
        raise ValueError(
            ('{name[0]}: {time[0]:f}, '
             '{name[1]}: {time[1]:f}, '
             'ratio {ratio:f} > {thresh:f}').format(
                name=(name_left, name_right),
                time=(time_left, time_right),
                ratio=time_left / time_right, thresh=thresh))


@with_setup(pretest, posttest)
@retry_on_except()
def test_iter_overhead():
    """Test overhead of iteration based tqdm"""

    total = int(1e6)

    with closing(MockIO()) as our_file:
        a = 0
        with trange(total, file=our_file) as t:
            with relative_timer() as time_tqdm:
                for i in t:
                    a += i
        assert a == (total * total - total) / 2.0

        a = 0
        with relative_timer() as time_bench:
            for i in _range(total):
                a += i
                our_file.write(a)

    assert_performance(6, 'trange', time_tqdm(), 'range', time_bench())


@with_setup(pretest, posttest)
@retry_on_except()
def test_manual_overhead():
    """Test overhead of manual tqdm"""

    total = int(1e6)

    with closing(MockIO()) as our_file:
        with tqdm(total=total * 10, file=our_file, leave=True) as t:
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

    assert_performance(6, 'tqdm', time_tqdm(), 'range', time_bench())


def worker(total, blocking=True):
    def incr_bar(x):
        with closing(StringIO()) as our_file:
            for _ in trange(
                    total, file=our_file,
                    lock_args=None if blocking else (False,),
                    miniters=1, mininterval=0, maxinterval=0):
                pass
        return x + 1
    return incr_bar


@with_setup(pretest, posttest)
@retry_on_except()
def test_lock_args():
    """Test overhead of nonblocking threads"""
    try:
        from concurrent.futures import ThreadPoolExecutor
        from threading import RLock
    except ImportError:
        raise SkipTest
    import sys

    total = 8
    subtotal = 1000

    tqdm.set_lock(RLock())
    with ThreadPoolExecutor(total) as pool:
        sys.stderr.write('block ... ')
        sys.stderr.flush()
        with relative_timer() as time_tqdm:
            res = list(pool.map(worker(subtotal, True), range(total)))
            assert sum(res) == sum(range(total)) + total
        sys.stderr.write('noblock ... ')
        sys.stderr.flush()
        with relative_timer() as time_noblock:
            res = list(pool.map(worker(subtotal, False), range(total)))
            assert sum(res) == sum(range(total)) + total

    assert_performance(0.2, 'noblock', time_noblock(), 'tqdm', time_tqdm())


@with_setup(pretest, posttest)
@retry_on_except()
def test_iter_overhead_hard():
    """Test overhead of iteration based tqdm (hard)"""

    total = int(1e5)

    with closing(MockIO()) as our_file:
        a = 0
        with trange(total, file=our_file, leave=True, miniters=1,
                    mininterval=0, maxinterval=0) as t:
            with relative_timer() as time_tqdm:
                for i in t:
                    a += i
        assert a == (total * total - total) / 2.0

        a = 0
        with relative_timer() as time_bench:
            for i in _range(total):
                a += i
                our_file.write(("%i" % a) * 40)

    assert_performance(85, 'trange', time_tqdm(), 'range', time_bench())


@with_setup(pretest, posttest)
@retry_on_except()
def test_manual_overhead_hard():
    """Test overhead of manual tqdm (hard)"""

    total = int(1e5)

    with closing(MockIO()) as our_file:
        t = tqdm(total=total * 10, file=our_file, leave=True, miniters=1,
                 mininterval=0, maxinterval=0)
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

    assert_performance(85, 'tqdm', time_tqdm(), 'range', time_bench())


@with_setup(pretest, posttest)
@retry_on_except()
def test_iter_overhead_simplebar_hard():
    """Test overhead of iteration based tqdm vs simple progress bar (hard)"""

    total = int(1e4)

    with closing(MockIO()) as our_file:
        a = 0
        with trange(total, file=our_file, leave=True, miniters=1,
                    mininterval=0, maxinterval=0) as t:
            with relative_timer() as time_tqdm:
                for i in t:
                    a += i
        assert a == (total * total - total) / 2.0

        a = 0
        s = simple_progress(_range(total), file=our_file, leave=True,
                            miniters=1, mininterval=0)
        with relative_timer() as time_bench:
            for i in s:
                a += i

    assert_performance(
        5, 'trange', time_tqdm(), 'simple_progress', time_bench())


@with_setup(pretest, posttest)
@retry_on_except()
def test_manual_overhead_simplebar_hard():
    """Test overhead of manual tqdm vs simple progress bar (hard)"""

    total = int(1e4)

    with closing(MockIO()) as our_file:
        t = tqdm(total=total * 10, file=our_file, leave=True, miniters=1,
                 mininterval=0, maxinterval=0)
        a = 0
        with relative_timer() as time_tqdm:
            for i in _range(total):
                a += i
                t.update(10)

        simplebar_update = simple_progress(
            total=total * 10, file=our_file, leave=True, miniters=1,
            mininterval=0)
        a = 0
        with relative_timer() as time_bench:
            for i in _range(total):
                a += i
                simplebar_update(10)

    assert_performance(
        5, 'tqdm', time_tqdm(), 'simple_progress', time_bench())
