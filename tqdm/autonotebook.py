import os

try:
    from IPython import get_ipython
    if 'IPKernelApp' not in get_ipython().config:  # pragma: no cover
        raise ImportError("console")
    if 'VSCODE_PID' in os.environ:  # pragma: no cover
        raise ImportError("vscode")
except:
    from .std import tqdm, trange
else:  # pragma: no cover
    from .notebook import tqdm, trange
    from .std import TqdmExperimentalWarning
    from warnings import warn
    warn("Using `tqdm.autonotebook.tqdm` in notebook mode."
         " Use `tqdm.tqdm` instead to force console mode"
         " (e.g. in jupyter console)", TqdmExperimentalWarning, stacklevel=2)
__all__ = ["tqdm", "trange"]
