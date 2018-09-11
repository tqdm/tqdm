try:
    from IPython import get_ipython
    if 'IPKernelApp' not in get_ipython().config:  # pragma: no cover
        raise ImportError("console")
except:
    from .._tqdm import tqdm, trange
else:  # pragma: no cover
    from .._tqdm_notebook import tqdm_notebook as tqdm
    from .._tqdm_notebook import tnrange as trange
    from .._tqdm import TqdmExperimentalWarning
    from warnings import warn
    warn("Using `tqdm.autonotebook.tqdm` in notebook mode."
         " Use `tqdm.tqdm` instead to force console mode"
         " (e.g. in jupyter console)", TqdmExperimentalWarning)
__all__ = ["tqdm", "trange"]
