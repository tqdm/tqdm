"""
Automatically choose between `tqdm.notebook` and `tqdm.std`.

Usage:
>>> from tqdm.autonotebook import trange, tqdm
>>> for i in trange(10):
...     ...
"""
import sys
from warnings import warn

try:
    if 'ipykernel' not in sys.modules:
        raise ImportError("console")
    get_ipython = sys.modules['IPython'].get_ipython
    ipython = get_ipython()
    if not ipython:
        raise ImportError("console")
    from ipykernel.zmqshell import ZMQInteractiveShell
    if not isinstance(ipython, ZMQInteractiveShell):
        raise ImportError("console")
    from .notebook import WARN_NOIPYW, IProgress
    if IProgress is None:
        from .std import TqdmWarning
        warn(WARN_NOIPYW, TqdmWarning, stacklevel=2)
        raise ImportError('ipywidgets')
except Exception:
    from .std import tqdm, trange
else:  # pragma: no cover
    from .notebook import tqdm, trange
    from .std import TqdmExperimentalWarning
    warn("Using `tqdm.autonotebook.tqdm` in notebook mode."
         " Use `tqdm.tqdm` instead to force console mode"
         " (e.g. in jupyter console)", TqdmExperimentalWarning, stacklevel=2)
__all__ = ["tqdm", "trange"]
