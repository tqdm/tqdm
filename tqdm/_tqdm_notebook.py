from .notebook import *  # NOQA
from .notebook import __all__  # NOQA
from .std import TqdmDeprecationWarning
from warnings import warn
warn("This function will be removed in tqdm==5.0.0\n"
     "Please use `tqdm.notebook.*` instead of `tqdm._tqdm_notebook.*`",
     TqdmDeprecationWarning)
