# Write the benchmarking functions here.
# See "Writing benchmarks" in the asv docs for more information.
from __future__ import division
from functools import partial


class Base:
    def setup(self, length=6e6):
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

        t0 = self.time()
        [0 for _ in self.iterable]
        t1 = self.time()
        self.bench_time = t1 - t0

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
    def setup(self):
        super(Overhead, self).setup(6e6)

    def track_tqdm(self):
        return self.fraction(self.tqdm)

    def track_optimsed(self):
        return self.fraction(partial(self.tqdm, miniters=6e5, smoothing=0))


class Alternatives(Base):
    """Fractional overhead compared to alternatives"""
    def setup(self):
        super(Alternatives, self).setup(1e5)

        # compare to `tqdm` rather than empty loop
        with self.tqdm(self.iterable) as pbar:
            t0 = self.time()
            [0 for _ in pbar]
            t1 = self.time()
        self.bench_time = t1 - t0

        # invert to track `tqdm` regressions (rather than the alternative)
        self.fraction = partial(self.fraction, invert=True)

    # def track_progressbar(self):
    #     from progressbar.progressbar import ProgressBar
    #     return self.fraction(ProgressBar())

    def track_progressbar2(self):
        from progressbar import progressbar
        return self.fraction(progressbar)

    def track_rich(self):
        from rich.progress import track
        return self.fraction(track)

    def track_alive_progress(self):
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
