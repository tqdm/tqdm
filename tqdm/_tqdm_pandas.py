import sys

__author__ = "github.com/casperdcl"
__all__ = ['tqdm_pandas']


def tqdm_pandas(tclass, *targs, **tkwargs):
    """
    Registers the given `tqdm` instance with
    `pandas.core.groupby.DataFrameGroupBy.progress_apply`.
    It will even close() the `tqdm` instance upon completion.

    Parameters
    ----------
    tclass  : tqdm class you want to use (eg, tqdm, tqdm_notebook, etc)
    targs and tkwargs  : arguments for the tqdm instance

    Examples
    --------
    >>> import pandas as pd
    >>> import numpy as np
    >>> from tqdm import tqdm, tqdm_pandas
    >>>
    >>> df = pd.DataFrame(np.random.randint(0, 100, (100000, 6)))
    >>> tqdm_pandas(tqdm, leave=True)  # can use tqdm_gui, optional kwargs, etc
    >>> # Now you can use `progress_apply` instead of `apply`
    >>> df.groupby(0).progress_apply(lambda x: x**2)

    References
    ----------
    https://stackoverflow.com/questions/18603270/
    progress-indicator-during-pandas-operations-python
    """
    from tqdm import TqdmDeprecationWarning

    if isinstance(tclass, type) or (getattr(tclass, '__name__', '').startswith(
            'tqdm_')):  # delayed adapter case
        TqdmDeprecationWarning("""\
Please use `tqdm.pandas(...)` instead of `tqdm_pandas(tqdm, ...)`.
""", fp_write=getattr(tkwargs.get('file', None), 'write', sys.stderr.write))
        tclass.pandas(*targs, **tkwargs)
    else:
        TqdmDeprecationWarning("""\
Please use `tqdm.pandas(...)` instead of `tqdm_pandas(tqdm(...))`.
""", fp_write=getattr(tclass.fp, 'write', sys.stderr.write))
        type(tclass).pandas(deprecated_t=tclass)
