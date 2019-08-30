from tqdm import trange, tqdm_multi
from tests_tqdm import _range, with_setup, pretest, posttest, StringIO, closing

@with_setup(pretest, posttest)
def multi_iterable_test():
    """Test tqdm_multi with trange"""
    multi = tqdm_multi()
    with closing(StringIO()) as our_file:
        for __ in _range(1, 5):
            job = trange(1, 10, file=our_file)
            multi.register_job(job)
        multi.run(sleep_delay=.001)
