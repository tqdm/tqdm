"""
`tqdm.autonotebook` but without import warnings.

Usage:
>>> from tqdm.auto import trange, tqdm
>>> for i in trange(10):
...     ...
"""
import warnings
from .std import TqdmExperimentalWarning
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=TqdmExperimentalWarning)
    from .autonotebook import tqdm, trange
__all__ = ["tqdm", "trange"]
