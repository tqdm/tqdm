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
        except:
            self.iterable = range(int(6e6))

        t0 = self.time()
        [0 for _ in self.iterable]
        t1 = self.time()
        self.t = t1 - t0


    def track_tqdm(self):
        t0 = self.time()
        [0 for _ in self.tqdm(self.iterable)]
        t1 = self.time()
        return (t1 - t0 - self.t) / self.t  # fractional overhead
