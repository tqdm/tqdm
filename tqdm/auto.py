"""
Enables multiple commonly used features.

Method resolution order:

- `tqdm.autonotebook` without import warnings
- `tqdm.asyncio`
- `tqdm.std` base class

Usage:
>>> from tqdm.auto import trange, tqdm
>>> for i in trange(10):
...     ...
"""

import warnings
from typing import Any

from .std import TqdmExperimentalWarning

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=TqdmExperimentalWarning)
    from .autonotebook import tqdm as notebook_tqdm

from .asyncio import tqdm as asyncio_tqdm
from .std import tqdm as std_tqdm

if notebook_tqdm is not std_tqdm:

    class tqdm(notebook_tqdm, asyncio_tqdm):  # type: ignore
        pass
else:

    class tqdm(asyncio_tqdm):
        pass


def trange(*args: Any, **kwargs: Any) -> tqdm:
    """
    A shortcut for `tqdm.auto.tqdm(range(*args), **kwargs)`.
    """
    return tqdm(range(*args), **kwargs)  # type: ignore


__all__ = ["tqdm", "trange"]
