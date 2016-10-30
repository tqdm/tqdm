# Write the benchmarking functions here.
# See "Writing benchmarks" in the asv docs for more information.


class TimeSuite:
    """
    An example benchmark that times the performance of various kinds
    of iterating over dictionaries in Python.
    """
    def setup(self):
        from tqdm import tqdm
        self.tqdm = tqdm
        try:
            self.iterable = xrange(int(6e6))
        except:
            self.iterable = range(int(6e6))

    def time_tqdm(self):
        [0 for _ in self.tqdm(self.iterable)]


class MemSuite:
    # def mem_list(self):
    #     return [0] * 256
    pass
