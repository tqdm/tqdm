# Write the benchmarking functions here.
# See "Writing benchmarks" in the asv docs for more information.
from __future__ import division


class FractionalOverheadSuite:
    """
    An example benchmark that times the performance of various kinds
    of iterating over dictionaries in Python.
    """
    def setup(self):
        try:
            from time import process_time
            self.time = process_time
        except ImportError:
            from time import clock
            self.time = clock
        from tqdm import tqdm
        self.tqdm = tqdm
        try:
            self.iterable = xrange(int(6e6))
        except NameError:
            self.iterable = range(int(6e6))

        t0 = self.time()
        [0 for _ in self.iterable]
        t1 = self.time()
        self.t = t1 - t0

    def track_tqdm(self):
        with self.tqdm(self.iterable) as pbar:
            t0 = self.time()
            [0 for _ in pbar]
            t1 = self.time()
        return (t1 - t0 - self.t) / self.t

    def track_optimsed(self):
        with self.tqdm(self.iterable, miniters=6e5, smoothing=0) as pbar:
            # TODO: miniters=None, mininterval=0.1, smoothing=0)]
            t0 = self.time()
            [0 for _ in pbar]
            t1 = self.time()
        return (t1 - t0 - self.t) / self.t
