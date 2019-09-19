from .cli import *  # NOQA
from .cli import __all__  # NOQA
from .std import TqdmDeprecationWarning
from warnings import warn
warn("This function will be removed in tqdm==5.0.0\n"
     "Please use `tqdm.cli.*` instead of `tqdm._main.*`",
     TqdmDeprecationWarning)
