from __future__ import division
from tqdm import tqdm, TMonitor
from tests_tqdm import with_setup, pretest, posttest, SkipTest, \
    StringIO, closing
from tests_tqdm import DiscreteTimer, cpu_timify

from time import sleep
from threading import Event


class FakeSleep(object):
    """Wait until the discrete timer reached the required time"""
    def __init__(self, dtimer):
        self.dtimer = dtimer

    def sleep(self, t):
        end = t + self.dtimer.t
        while self.dtimer.t < end:
            sleep(0.0000001)  # sleep a bit to interrupt (instead of pass)


class FakeTqdm(object):
    _instances = []


def make_create_fake_sleep_event(sleep):
    def wait(self, timeout=None):
        if timeout is not None:
            sleep(timeout)
        return self.is_set()

    def create_fake_sleep_event():
        event = Event()
        event.wait = wait
        return event

    return create_fake_sleep_event


def incr(x):
    return x + 1


@with_setup(pretest, posttest)
def test_monitor_thread():
    """Test dummy monitoring thread"""
    maxinterval = 10

    # Setup a discrete timer
    timer = DiscreteTimer()
    TMonitor._time = timer.time
    # And a fake sleeper
    sleeper = FakeSleep(timer)
    TMonitor._event = make_create_fake_sleep_event(sleeper.sleep)

    # Instanciate the monitor
    monitor = TMonitor(FakeTqdm, maxinterval)
    # Test if alive, then killed
    assert monitor.report()
    monitor.exit()
    timer.sleep(maxinterval * 2)  # need to go out of the sleep to die
    assert not monitor.report()
    # assert not monitor.is_alive()  # not working dunno why, thread not killed
    del monitor


@with_setup(pretest, posttest)
def test_monitoring_and_cleanup():
    """Test for stalled tqdm instance and monitor deletion"""
    # Note: should fix miniters for these tests, else with dynamic_miniters
    # it's too complicated to handle with monitoring update and maxinterval...
    maxinterval = 2

    total = 1000
    # Setup a discrete timer
    timer = DiscreteTimer()
    # And a fake sleeper
    sleeper = FakeSleep(timer)
    # Setup TMonitor to use the timer
    TMonitor._time = timer.time
    TMonitor._event = make_create_fake_sleep_event(sleeper.sleep)
    # Set monitor interval
    tqdm.monitor_interval = maxinterval
    with closing(StringIO()) as our_file:
        with tqdm(total=total, file=our_file, miniters=500, mininterval=0.1,
                  maxinterval=maxinterval) as t:
            cpu_timify(t, timer)
            # Do a lot of iterations in a small timeframe
            # (smaller than monitor interval)
            timer.sleep(maxinterval / 2)  # monitor won't wake up
            t.update(500)
            # check that our fixed miniters is still there
            assert t.miniters == 500
            # Then do 1 it after monitor interval, so that monitor kicks in
            timer.sleep(maxinterval * 2)
            t.update(1)
            # Wait for the monitor to get out of sleep's loop and update tqdm..
            timeend = timer.time()
            while not (t.monitor.woken >= timeend and t.miniters == 1):
                timer.sleep(1)  # Force monitor to wake up if it woken too soon
                sleep(0.000001)  # sleep to allow interrupt (instead of pass)
            assert t.miniters == 1  # check that monitor corrected miniters
            # Note: at this point, there may be a race condition: monitor saved
            # current woken time but timer.sleep() happen just before monitor
            # sleep. To fix that, either sleep here or increase time in a loop
            # to ensure that monitor wakes up at some point.

            # Try again but already at miniters = 1 so nothing will be done
            timer.sleep(maxinterval * 2)
            t.update(2)
            timeend = timer.time()
            while t.monitor.woken < timeend:
                timer.sleep(1)  # Force monitor to wake up if it woken too soon
                sleep(0.000001)
            # Wait for the monitor to get out of sleep's loop and update tqdm..
            assert t.miniters == 1  # check that monitor corrected miniters

    # Check that class var monitor is deleted if no instance left
    tqdm.monitor_interval = 10
    assert tqdm.monitor is None


@with_setup(pretest, posttest)
def test_monitoring_multi():
    """Test on multiple bars, one not needing miniters adjustment"""
    # Note: should fix miniters for these tests, else with dynamic_miniters
    # it's too complicated to handle with monitoring update and maxinterval...
    maxinterval = 2

    total = 1000
    # Setup a discrete timer
    timer = DiscreteTimer()
    # And a fake sleeper
    sleeper = FakeSleep(timer)
    # Setup TMonitor to use the timer
    TMonitor._time = timer.time
    TMonitor._event = make_create_fake_sleep_event(sleeper.sleep)
    # Set monitor interval
    tqdm.monitor_interval = maxinterval
    with closing(StringIO()) as our_file:
        with tqdm(total=total, file=our_file, miniters=500, mininterval=0.1,
                  maxinterval=maxinterval) as t1:
            # Set high maxinterval for t2 so monitor does not need to adjust it
            with tqdm(total=total, file=our_file, miniters=500, mininterval=0.1,
                      maxinterval=1E5) as t2:
                cpu_timify(t1, timer)
                cpu_timify(t2, timer)
                # Do a lot of iterations in a small timeframe
                timer.sleep(maxinterval / 2)
                t1.update(500)
                t2.update(500)
                assert t1.miniters == 500
                assert t2.miniters == 500
                # Then do 1 it after monitor interval, so that monitor kicks in
                timer.sleep(maxinterval * 2)
                t1.update(1)
                t2.update(1)
                # Wait for the monitor to get out of sleep and update tqdm
                timeend = timer.time()
                while not (t1.monitor.woken >= timeend and t1.miniters == 1):
                    timer.sleep(1)
                    sleep(0.000001)
                assert t1.miniters == 1  # check that monitor corrected miniters
                assert t2.miniters == 500  # check that t2 was not adjusted

    # Check that class var monitor is deleted if no instance left
    tqdm.monitor_interval = 10
    assert tqdm.monitor is None


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
