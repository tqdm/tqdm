from __future__ import division
from tqdm import tqdm, trange, TMonitor
from tests_tqdm import with_setup, pretest, posttest, SkipTest, \
    StringIO, closing
from tests_perf import retry_on_except

from time import sleep, time
from threading import Event
import sys



class OffsetTime(object):
    def __init__(self):
        self.offset = 0

    def time(self):
        return time() + self.offset

    def sleep(self, dur):
        return sleep(dur)

    def fake_sleep(self, dur):
        self.offset += dur
        sleep(0.000001)  # sleep to allow interrupt (instead of pass)


def make_create_fake_sleep_event(sleep):
    class FakeEvent(Event):
        def wait(self, timeout=None):
            if timeout is not None:
                sleep(timeout)
            return self.is_set()

    return FakeEvent


def cpu_timify(t, timer=None):
    """Force tqdm to use the specified timer instead of system-wide time()"""
    if timer is None:
        timer = OffsetTime()
    t._time = timer.time
    t._sleep = timer.fake_sleep
    t.start_t = t.last_print_t = t._time()
    return timer


class FakeTqdm(object):
    _instances = []
    get_lock = tqdm.get_lock


def incr(x):
    return x + 1


def incr_bar(x):
    with closing(StringIO()) as our_file:
        for _ in trange(x, lock_args=(False,), file=our_file):
            pass
    return incr(x)


@with_setup(pretest, posttest)
def test_monitor_thread():
    """Test dummy monitoring thread"""
    # patch sleep
    timer = OffsetTime()
    TMonitor._time = timer.time
    TMonitor._event = make_create_fake_sleep_event(timer.fake_sleep)

    monitor = TMonitor(FakeTqdm, 10)
    # Test if alive, then killed
    assert monitor.report()
    monitor.exit()
    assert not monitor.report()
    assert not monitor.is_alive()
    del monitor
    TMonitor._time = None
    TMonitor._event = None


@with_setup(pretest, posttest)
def test_monitoring_and_cleanup():
    """Test for stalled tqdm instance and monitor deletion"""
    # Note: should fix miniters for these tests, else with dynamic_miniters
    # it's too complicated to handle with monitoring update and maxinterval...
    maxinterval = tqdm.monitor_interval
    assert maxinterval == 10
    total = 1000

    # patch sleep
    timer = OffsetTime()
    TMonitor._time = timer.time
    TMonitor._event = make_create_fake_sleep_event(timer.fake_sleep)

    tqdm.monitor = None
    with closing(StringIO()) as our_file:
        with tqdm(total=total, file=our_file, miniters=500, mininterval=0.1,
                  maxinterval=maxinterval) as t:
            cpu_timify(t, timer)
            # Do a lot of iterations in a small timeframe
            # (smaller than monitor interval)
            timer.fake_sleep(maxinterval / 2)  # monitor won't wake up
            t.update(500)
            # check that our fixed miniters is still there
            assert t.miniters == 500
            # Then do 1 it after monitor interval, so that monitor kicks in
            timer.fake_sleep(maxinterval * 1.1)
            t.update(1)
            # Wait for the monitor to get out of sleep's loop and update tqdm..
            timeend = timer.time()
            while not (t.monitor.woken >= timeend and t.miniters == 1):
                timer.fake_sleep(1)  # Force monitor to wake up if it woken too soon
            assert t.miniters == 1  # check that monitor corrected miniters
            # Note: at this point, there may be a race condition: monitor saved
            # current woken time but timer.sleep() happen just before monitor
            # sleep. To fix that, either sleep here or increase time in a loop
            # to ensure that monitor wakes up at some point.

            # Try again but already at miniters = 1 so nothing will be done
            timer.fake_sleep(maxinterval * 1.1)
            t.update(2)
            timeend = timer.time()
            while t.monitor.woken < timeend:
                timer.fake_sleep(1)  # Force monitor to wake up if it woken too soon
            # Wait for the monitor to get out of sleep's loop and update tqdm..
            assert t.miniters == 1  # check that monitor corrected miniters

    # Check that class var monitor is deleted if no instance left
    tqdm.monitor_interval = 10
    assert not tqdm.monitor.get_instances()
    tqdm.monitor.exit()
    del tqdm.monitor
    tqdm.monitor = None
    TMonitor._time = None
    TMonitor._event = None


@with_setup(pretest, posttest)
def test_monitoring_multi():
    """Test on multiple bars, one not needing miniters adjustment"""
    # Note: should fix miniters for these tests, else with dynamic_miniters
    # it's too complicated to handle with monitoring update and maxinterval...
    maxinterval = tqdm.monitor_interval
    assert maxinterval == 10
    total = 1000

    # patch sleep
    timer = OffsetTime()
    TMonitor._time = timer.time
    TMonitor._event = make_create_fake_sleep_event(timer.fake_sleep)

    tqdm.monitor = None
    with closing(StringIO()) as our_file:
        with tqdm(total=total, file=our_file, miniters=500, mininterval=0.1,
                  maxinterval=maxinterval) as t1:
            cpu_timify(t1, timer)
            # Set high maxinterval for t2 so monitor does not need to adjust it
            with tqdm(total=total, file=our_file, miniters=500, mininterval=0.1,
                      maxinterval=1E5) as t2:
                cpu_timify(t2, timer)
                # Do a lot of iterations in a small timeframe
                timer.fake_sleep(maxinterval / 2)
                t1.update(500)
                t2.update(500)
                assert t1.miniters == 500
                assert t2.miniters == 500
                # Then do 1 it after monitor interval, so that monitor kicks in
                timer.fake_sleep(maxinterval * 1.1)
                t1.update(1)
                t2.update(1)
                # Wait for the monitor to get out of sleep and update tqdm
                timeend = timer.time()
                while not (t1.monitor.woken >= timeend and t1.miniters == 1):
                    sys.stderr.write("."); sys.stderr.flush()
                    timer.fake_sleep(1)
                assert t1.miniters == 1  # check that monitor corrected miniters
                assert t2.miniters == 500  # check that t2 was not adjusted

    # Check that class var monitor is deleted if no instance left
    tqdm.monitor_interval = 10
    assert not tqdm.monitor.get_instances()
    tqdm.monitor.exit()
    del tqdm.monitor
    tqdm.monitor = None
    TMonitor._time = None
    TMonitor._event = None


@with_setup(pretest, posttest)
def test_imap():
    """Test multiprocessing.Pool"""
    try:
        from multiprocessing import Pool
    except ImportError:
        raise SkipTest

    pool = Pool()
    res = list(tqdm(pool.imap(incr, range(100)), disable=True))
    assert res[-1] == 100


# py2: locks won't propagate to incr_bar so may cause `AttributeError`
@retry_on_except(n=3 if sys.version_info < (3,) else 1)
@with_setup(pretest, posttest)
def test_threadpool():
    """Test concurrent.futures.ThreadPoolExecutor"""
    try:
        from concurrent.futures import ThreadPoolExecutor
        from threading import RLock
    except ImportError:
        raise SkipTest

    default_lock = tqdm.get_lock()
    tqdm.set_lock(RLock())
    with ThreadPoolExecutor(8) as pool:
        try:
            res = list(tqdm(pool.map(incr_bar, range(100)), disable=True))
        except AttributeError:
            if sys.version_info < (3,):
                raise SkipTest
            else:
                raise
    assert sum(res) == sum(range(1, 101))
    tqdm.set_lock(default_lock)
