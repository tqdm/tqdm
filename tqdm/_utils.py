from warnings import warn

from .std import TqdmDeprecationWarning

warn("This function will be removed in tqdm==5.0.0\n"
     "Please use `tqdm.utils.*` instead of `tqdm._utils.*`",
     TqdmDeprecationWarning, stacklevel=2)
