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
stmts = (
    # Benchmark
    'for i in _range(int(1e8)):\n\tpass',
    # Basic demo
    'import tqdm\nfor i in tqdm.trange(int(1e8)):\n\tpass',
    # Some decorations
    'import tqdm\nfor i in tqdm.trange(int(1e8), miniters=int(1e6),'
    ' ascii=True, desc="cool", dynamic_ncols=True):\n\tpass',
    # Nested bars
    'from tqdm import trange\nfor i in trange(10):\n\t'
    'for j in trange(int(1e7), leave=False, unit_scale=True):\n\t\tpass',
    # Experimental GUI demo
    'import tqdm\nfor i in tqdm.tgrange(int(1e8)):\n\tpass',
    # Comparison to https://code.google.com/p/python-progressbar/
    'from progressbar.progressbar import ProgressBar\n'
    'for i in ProgressBar()(_range(int(1e8))):\n\tpass')

for s in stmts:
    print(s.replace('import tqdm\n', ''))
    print(timeit(stmt='try:\n\t_range = xrange'
                      '\nexcept:\n\t_range = range\n' + s, number=1),
          'seconds')
