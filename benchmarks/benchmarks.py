# Write the benchmarking functions here.
# See "Writing benchmarks" in the asv docs for more information.
from __future__ import division
from functools import partial


class Base:
    def __init__(self, length):
        try:
            from time import process_time
            self.time = process_time
        except ImportError:
            from time import clock
            self.time = clock
        from tqdm import tqdm
        self.tqdm = tqdm
        try:
            self.iterable = xrange(int(length))
        except NameError:
            self.iterable = range(int(length))

    def fraction(self, cls, invert=False):
        pbar = cls(self.iterable)
        t0 = self.time()
        [0 for _ in pbar]
        t1 = self.time()
        if invert:
            return self.bench_time / (t1 - t0 - self.bench_time)
        return (t1 - t0 - self.bench_time) / self.bench_time


class Overhead(Base):
    """Fractional overhead compared to an empty loop"""
    def __init__(self):
        super(Overhead, self).__init__(6e6)

        # compare to empty loop
        t0 = self.time()
        [0 for _ in self.iterable]
        t1 = self.time()
        self.bench_time = t1 - t0

    def tqdm_basic(self):
        return self.fraction(self.tqdm)

    def tqdm_optimised(self):
        return self.fraction(partial(self.tqdm, miniters=6e5, smoothing=0))


overhead = Overhead()
def track_tqdm(method):
    if method == "no-progress":
        return 1
    global overhead
    return getattr(overhead, method.replace("-", "_"))()
track_tqdm.params = ["no-progress", "tqdm-basic", "tqdm-optimised"]
track_tqdm.param_names = ["method"]
track_tqdm.unit = "Relative time (lower is better)"


class Alternatives(Base):
    """Fractional overhead compared to alternatives"""
    def __init__(self):
        super(Alternatives, self).__init__(1e5)

        # compare to `tqdm`
        with self.tqdm(self.iterable) as pbar:
            t0 = self.time()
            [0 for _ in pbar]
            t1 = self.time()
        self.bench_time = t1 - t0

        # invert to track `tqdm` regressions (rather than the alternative)
        self.fraction = partial(self.fraction, invert=True)

    # def progressbar(self):
    #     from progressbar.progressbar import ProgressBar
    #     return self.fraction(ProgressBar())

    def progressbar2(self):
        from progressbar import progressbar
        return self.fraction(progressbar)

    def rich(self):
        from rich.progress import track
        return self.fraction(track)

    def alive_progress(self):
        from alive_progress import alive_bar

        class wrapper:
            def __init__(self, iterable):
                self.iterable = iterable
            def __iter__(self):
                iterable = self.iterable
                with alive_bar(len(iterable)) as bar:
                    for i in iterable:
                        yield i
                        bar()

        return self.fraction(wrapper)


alternatives = Alternatives()
def track_alternatives(library):
    if library == "tqdm":
        return 1
    global alternatives
    return getattr(alternatives, library.replace("-", "_"))()
track_alternatives.params = ["tqdm", "progressbar2", "rich", "alive-progress"]
track_alternatives.param_names = ["library"]
track_alternatives.unit = "Relative speed (higher is better)"
