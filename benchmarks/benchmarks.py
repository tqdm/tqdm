# Write the benchmarking functions here.
# See "Writing benchmarks" in the asv docs for more information.
from __future__ import division

from functools import partial


class Comparison:
    """Running time of wrapped empty loops"""
    def __init__(self, length):
        try:
            from time import process_time
            self.time = process_time
        except ImportError:
            from time import clock
            self.time = clock
        try:
            self.iterable = xrange(int(length))
        except NameError:
            self.iterable = range(int(length))

    def run(self, cls):
        pbar = cls(self.iterable)
        t0 = self.time()
        [0 for _ in pbar]  # pylint: disable=pointless-statement
        t1 = self.time()
        return t1 - t0

    def run_by_name(self, method):
        return getattr(self, method.replace("-", "_"))()

    def no_progress(self):
        return self.run(lambda x: x)

    def tqdm_optimised(self):
        from tqdm import tqdm
        return self.run(partial(tqdm, miniters=6e5, smoothing=0))

    def tqdm(self):
        from tqdm import tqdm
        return self.run(tqdm)

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

        return self.run(wrapper)

    # def progressbar(self):
    #     from progressbar.progressbar import ProgressBar
    #     return self.run(ProgressBar())

    def progressbar2(self):
        from progressbar import progressbar
        return self.run(progressbar)

    def rich(self):
        from rich.progress import track
        return self.run(track)


# thorough test against no-progress
slow = Comparison(6e6)


def track_tqdm(method):
    return slow.run_by_name(method)


track_tqdm.params = ["tqdm", "tqdm-optimised", "no-progress"]
track_tqdm.param_names = ["method"]
track_tqdm.unit = "Seconds (lower is better)"

# quick test against alternatives
fast = Comparison(1e5)


def track_alternatives(library):
    return fast.run_by_name(library)


track_alternatives.params = ["rich", "progressbar2", "alive-progress", "tqdm"]
track_alternatives.param_names = ["library"]
track_alternatives.unit = "Seconds (lower is better)"
