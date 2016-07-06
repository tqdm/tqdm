# future division is important to divide integers and get as
# a result precise floating numbers (instead of truncated int)
from __future__ import absolute_import
from __future__ import division

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
    from pandas.core.frame import DataFrame
    from pandas.core.series import Series
    from pandas.core.groupby import DataFrameGroupBy, SeriesGroupBy

    def inner(df, func, *args, **kwargs):
        """
        Parameters
        ----------
        df  : DataFrame[GroupBy]
            Data (may be grouped).
        func  : function
            To be applied on the (grouped) data.

        *args and *kwargs are transmitted to DataFrameGroupBy.apply()
        """
        # Precompute total iterations
        total = getattr(df, 'ngroups', None)
        if total is None:  # not grouped
            total = len(df) if isinstance(df, Series) \
                else df.size // len(df)
        else:
            total += 1  # pandas calls update once too many

        # Init bar
        if isinstance(tclass, type) or \
            (hasattr(tclass, '__name__') and
                tclass.__name__ == 'tqdm_notebook'):  # delayed adapter case
            t = tclass(*targs, total=total, **tkwargs)
        else:
            t = tclass
            t.total = total
            t.write("Warning: tqdm_pandas: using a bar instance is deprecated,"
                    " please provide a bar class instead.", file=t.fp)

        # Define bar updating wrapper
        def wrapper(*args, **kwargs):
            t.update()
            return func(*args, **kwargs)

        # Apply the provided function (in *args and **kwargs)
        # on the df using our wrapper (which provides bar updating)
        result = df.apply(wrapper, *args, **kwargs)

        # Close bar and return pandas calculation result
        t.close()
        return result

    # Monkeypatch pandas to provide easy methods
    # Enable custom tqdm progress in pandas!
    DataFrame.progress_apply = inner
    DataFrameGroupBy.progress_apply = inner
    Series.progress_apply = inner
    SeriesGroupBy.progress_apply = inner
