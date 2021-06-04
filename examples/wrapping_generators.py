import numpy as np

from tqdm.contrib import tenumerate, tmap, tzip

for _ in tenumerate(range(int(1e6)), desc="builtin enumerate"):
    pass

for _ in tenumerate(np.random.random((999, 999)), desc="numpy.ndenumerate"):
    pass

for _ in tzip(np.arange(1e6), np.arange(1e6) + 1, desc="builtin zip"):
    pass

mapped = tmap(lambda x: x + 1, np.arange(1e6), desc="builtin map")
assert (np.arange(1e6) + 1 == list(mapped)).all()
