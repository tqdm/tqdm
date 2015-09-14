"""
Simple tqdm examples and profiling
"""

from time import sleep
from timeit import timeit

# Simple demo
from tqdm import trange
for i in trange(16, leave=True):
    sleep(0.1)

# Profiling/overhead tests
stmts = ('[i for i in xrange(int(1e8))]',
         'import tqdm; [i for i in tqdm.trange(int(1e8))]',
         'import tqdm; [i for i in tqdm.trange(int(1e8), miniters=int(1e6),'
         '    ascii=False, desc="cool")]',
         'from progressbar.progressbar import ProgressBar;'
         '    [i for i in ProgressBar()(xrange(int(1e8)))]')
for s in stmts:
    print s
    print timeit(stmt=s, number=1), 'seconds'
