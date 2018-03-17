from threading import Thread
from time import time, sleep
__all__ = ["TMonitor"]


class TMonitor(Thread):
    """
    Monitoring thread for tqdm bars.
    Monitors if tqdm bars are taking too much time to display
    and readjusts miniters automatically if necessary.

    Parameters
    ----------
    tqdm_cls  : class
        tqdm class to use (can be core tqdm or a submodule).
    sleep_interval  : fload
        Time to sleep between monitoring checks.
    """

    # internal vars for unit testing
    _time = None
    _sleep = None

    def __init__(self, tqdm_cls, sleep_interval):
        Thread.__init__(self)
        self.daemon = True  # kill thread when main killed (KeyboardInterrupt)
        self.was_killed = False
        self.woken = 0  # last time woken up, to sync with monitor
        self.tqdm_cls = tqdm_cls
        self.sleep_interval = sleep_interval
        if TMonitor._time is not None:
            self._time = TMonitor._time
        else:
            self._time = time
        if TMonitor._sleep is not None:
            self._sleep = TMonitor._sleep
        else:
            self._sleep = sleep
        self.start()

    def exit(self):
        self.was_killed = True
        # self.join()  # DO NOT, blocking event, slows down tqdm at closing
        return self.report()

    def run(self):
        cur_t = self._time()
        while True:
            # After processing and before sleeping, notify that we woke
            # Need to be done just before sleeping
            self.woken = cur_t
            # Sleep some time...
            self._sleep(self.sleep_interval)
            # Quit if killed
            # if self.exit_event.is_set():  # TODO: should work but does not...
            if self.was_killed:
                return
            # Then monitor!
            # Acquire lock (to access _instances)
            with self.tqdm_cls.get_lock():
                cur_t = self._time()
                # Check tqdm instances are waiting too long to print
                for instance in self.tqdm_cls._instances:
                    # Avoid race by checking that the instance started
                    if not hasattr(instance, 'start_t'):  # pragma: nocover
                        continue
                    # Only if mininterval > 1 (else iterations are just slow)
                    # and last refresh exceeded maxinterval
                    if instance.miniters > 1 and \
                            (cur_t - instance.last_print_t) >= \
                            instance.maxinterval:
                        # force bypassing miniters on next iteration
                        # (dynamic_miniters adjusts mininterval automatically)
                        instance.miniters = 1
                        # Refresh now! (works only for manual tqdm)
                        instance.refresh(nolock=True)

    def report(self):
        # return self.is_alive()  # TODO: does not work...
        return not self.was_killed
