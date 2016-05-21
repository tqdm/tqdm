import pandas as pd
import numpy as np
from tqdm import tqdm, tqdm_pandas

df = pd.DataFrame(np.random.randint(0, 100, (100000, 6)))

# Create and register a new `tqdm` instance with `pandas`
# (can use tqdm_gui, optional kwargs, etc.)
tqdm_pandas(tqdm())

# Now you can use `progress_apply` instead of `apply`
df.progress_apply(lambda x: x**2)
# can also groupby:
# df.groupby(0).progress_apply(lambda x: x**2)


""" Source code for `tqdm_pandas` (really simple!) """
# def tqdm_pandas(t):
#   from pandas.core.frame import DataFrame
#   def inner(df, func, *args, **kwargs):
#       t.total = groups.size // len(groups)
#       def wrapper(*args, **kwargs):
#           t.update(1)
#           return func(*args, **kwargs)
#       result = df.apply(wrapper, *args, **kwargs)
#       t.close()
#       return result
#   DataFrame.progress_apply = inner
