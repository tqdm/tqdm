import pandas as pd
import numpy as np
from tqdm import tqdm, tqdm_pandas

df = pd.DataFrame(np.random.randint(0, 100, (100000, 6)))

# Create and register a new `tqdm` instance with `pandas`
# (can use tqdm_gui, optional kwargs, etc.)
tqdm_pandas(tqdm())

# Now you can use `progress_apply` instead of `apply`
df.groupby(0).progress_apply(lambda x: x**2)


""" Source code for `tqdm_pandas` (really simple!) """
# def tqdm_pandas(t):
#   from pandas.core.groupby import DataFrameGroupBy
#   def inner(groups, func, *args, **kwargs):
#       t.total = len(groups) + 1
#       def wrapper(*args, **kwargs):
#           t.update(1)
#           return func(*args, **kwargs)
#       result = groups.apply(wrapper, *args, **kwargs)
#       t.close()
#       return result
#   DataFrameGroupBy.progress_apply = inner
