"""
# Simple tqdm examples and profiling

# Benchmark
for i in _range(int(1e8)):
    pass

# Basic demo
import tqdm
for i in tqdm.trange(int(1e8)):
    pass

# Some decorations
import tqdm
for i in tqdm.trange(int(1e8), miniters=int(1e6), ascii=True,
                     desc="cool", dynamic_ncols=True):
    pass

# Nested bars
from tqdm import trange
for i in trange(10):
    for j in trange(int(1e7), leave=False, unit_scale=True):
        pass

# Experimental GUI demo
import tqdm
for i in tqdm.tgrange(int(1e8)):
    pass

# Comparison to https://code.google.com/p/python-progressbar/
try:
    from progressbar.progressbar import ProgressBar
except ImportError:
    pass
else:
    for i in ProgressBar()(_range(int(1e8))):
        pass

# Dynamic miniters benchmark
from tqdm import trange
for i in trange(int(1e8), miniters=None, mininterval=0.1, smoothing=0):
    pass

# Fixed miniters benchmark
from tqdm import trange
for i in trange(int(1e8), miniters=4500000, mininterval=0.1, smoothing=0):
    pass
"""

from time import sleep
from timeit import timeit
import re

# Simple demo
from tqdm import trange
for i in trange(16, leave=True):
    sleep(0.1)

# Profiling/overhead tests
stmts = filter(None, re.split(r'\n\s*#.*?\n', __doc__))
for s in stmts:
    print(s.replace('import tqdm\n', ''))
    print(timeit(stmt='try:\n\t_range = xrange'
                 '\nexcept:\n\t_range = range\n' + s, number=1), 'seconds')
