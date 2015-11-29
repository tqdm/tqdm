# future division is important to divide integers and get as
# a result precise floating numbers (instead of truncated int)
from __future__ import division, absolute_import


__author__ = {"github.com/": ["casperdcl", "hadim"]}
__all__ = ['tqdm_pandas']


def tqdm_pandas(t):
    """
    Adds given `tqdm` instance to `DataFrameGroupBy.progress_apply()`.
    Don't forget to close the `tqdm` instance afterwards
    (or just use `with` syntax):

    Examples
    --------
    >>> import pandas as pd
    >>> import numpy as np
    >>> from tqdm import tqdm, tqdm_pandas
    >>> form time import time
    >>>
    >>> df = pd.DataFrame(np.random.randint(0, 100, (100000, 6)))
    >>> with tqdm(...) as t:
    ...     tqdm_pandas(t)
    ...     # Now you can use `progress_apply` instead of `apply`
    ...     df.groupby(0).progress_apply(lambda x: time.sleep(0.01))

    References
    ----------
    https://stackoverflow.com/questions/18603270/
    progress-indicator-during-pandas-operations-python
    """
    from pandas.core.groupby import DataFrameGroupBy

    def inner(groups, func, progress_kwargs={}, *args, **kwargs):
        """
        Parameters
        ----------
        groups  : DataFrameGroupBy
            Grouped data.
        func  : function
            To be applied on the grouped data.
        progress_kwargs  : dict
            Parameters for the progress bar (same as for `tqdm`).

        *args and *kwargs are transmitted to DataFrameGroupBy.apply()
        """
        for key, val in progress_kwargs.items():
            # TODO: do we need this?
            if getattr(t, key, None) is not None:
                setattr(t, key, val)

        t.total = len(groups)

        # def progress_decorator(func):
        #     def wrapper(*args, **kwargs):
        #         start_t = wrapper.start_t
        #         last_print_t = wrapper.last_print_t
        #         last_print_n = wrapper.last_print_n
        #         n = wrapper.n
        #
        #         if n - last_print_n >= miniters:
        #             # We check the counter first, to reduce the overhead of
        #             # time.time()
        #             cur_t = time.time()
        #             if cur_t - last_print_t >= mininterval:
        #                 fmeter = format_meter(n, total, cur_t - start_t)
        #                 sp.print_status(prefix + fmeter)
        #                 last_print_n = n
        #                 last_print_t = cur_t
        #
        #         wrapper.n += 1
        #
        #         return func(*args, **kwargs)
        #
        #     wrapper.start_t = time.time()
        #     wrapper.last_print_t = wrapper.start_t
        #     wrapper.last_print_n = 0
        #     wrapper.n = 0
        #
        #     return wrapper
        # progress_func = progress_decorator(func)
        # result = groups.apply(progress_func, *args, **kwargs)

        def wrapper(*args, **kwargs):
            t.update()
            return func(*args, **kwargs)

        result = groups.apply(wrapper, *args, **kwargs)

        # if not leave:
        #     sp.print_status('')
        #     sys.stdout.write('\r')
        # TODO: check if above can be replaced by:
        t.close()

        return result

    # Enable custom tqdm progress in pandas!
    DataFrameGroupBy.progress_apply = inner
