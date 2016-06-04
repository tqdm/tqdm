from ._tqdm import tqdm
from ._tqdm import trange
from ._tqdm_gui import tqdm_gui
from ._tqdm_gui import tgrange
from ._tqdm_pandas import tqdm_pandas
from ._main import main
from ._main import TqdmKeyError
from ._main import TqdmTypeError
from ._version import __version__  # NOQA
# from ._tqdm_notebook import tqdm_notebook
# from ._tqdm_notebook import tnrange
from ._lazy_import import LazyImport

__all__ = ['tqdm', 'tqdm_gui', 'trange', 'tgrange', 'tqdm_pandas',
           'tqdm_notebook', 'tnrange', 'main', 'TqdmKeyError', 'TqdmTypeError',
           '__version__']

# Slow imports

# tqdm_gui = LazyImport('tqdm_gui', '_tqdm_gui')
# tgrange = LazyImport('tgrange', '_tqdm_gui')
# tqdm_pandas = LazyImport('tqdm_pandas', '_tqdm_pandas')
tqdm_notebook = LazyImport('tqdm_notebook', '_tqdm_notebook')
tnrange = LazyImport('tnrange', '_tqdm_notebook')
