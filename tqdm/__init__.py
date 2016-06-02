from ._tqdm import tqdm
from ._tqdm import trange
from ._tqdm_gui import tqdm_gui
from ._tqdm_gui import tgrange
from ._tqdm_pandas import tqdm_pandas
from ._main import main
from ._main import TqdmKeyError
from ._main import TqdmTypeError
from ._version import __version__  # NOQA

__all__ = ['tqdm', 'tqdm_gui', 'trange', 'tgrange', 'tqdm_pandas',
           'tqdm_notebook', 'tnrange', 'main', 'TqdmKeyError', 'TqdmTypeError',
           '__version__']


def tqdm_notebook(*args, **kwargs):
    """See tqdm._tqdm_notebook.tqdm_notebook for full documentation

    This is just an adapter to delay imports
    """
    from ._tqdm_notebook import tqdm_notebook as _tqdm_notebook
    return _tqdm_notebook(*args, **kwargs)


def tnrange(*args, **kwargs):
    """See tqdm._tqdm_notebook.tnrange for full documentation

    This is just an adapter to delay imports
    """
    from ._tqdm_notebook import tnrange as _tnrange
    return _tnrange(*args, **kwargs)
