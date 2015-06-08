import sys
import time

from tqdm._tqdm import StatusPrinter
from tqdm._tqdm import format_meter

__all__ = ['enable_progress_apply']


def enable_progress_apply():
    try:
        from pandas.core.groupby import DataFrameGroupBy
        DataFrameGroupBy.progress_apply = _progress_apply
    except ImportError:
        raise("You can't enable Pandas progress apply ",
              "because Pandas is not installed")


def _progress_apply(groups, func, progress_kwargs={}, *args, **kwargs):
    """Add a progress bar during DataFrameGroupBy.apply(). Largely inspired from
    https://stackoverflow.com/questions/18603270/progress-indicator-during-pandas-operations-python.

    Parameters
    ----------
    groups : DataFrameGroupBy
        Grouped data.
    func : function
        To be applied on the grouped data.
    progress_kwargs : dict
        Parameters for the progress bar (same as for `tqdm.tqdm`).

    *args and *kwargs are transmitted to DataFrameGroupBy.apply()

    Examples
    --------
    >>> import time
    >>> import pandas as pd
    >>> import numpy as np
    >>>
    >>> from tqdm import enable_progress_apply
    >>> enable_progress_apply()
    >>>
    >>> # Now you can use `progress_apply` instead of `apply`
    >>> df = pd.DataFrame(np.random.randint(0, 100, (100000, 6)))
    >>> df.groupby(0).progress_apply(lambda x: time.sleep(0.01))

    """

    mininterval = progress_kwargs['mininterval'] if 'mininterval' \
        in progress_kwargs.keys() else 0.5
    miniters = progress_kwargs['miniters'] if 'miniters' \
        in progress_kwargs.keys() else 1
    file = progress_kwargs['file'] if 'file' \
        in progress_kwargs.keys() else sys.stderr
    desc = progress_kwargs['desc'] if 'desc' \
        in progress_kwargs.keys() else ''
    leave = progress_kwargs['leave'] if 'leave' \
        in progress_kwargs.keys() else False

    for key, value in progress_kwargs.items():
        locals()[key] = value

    prefix = desc + ': ' if desc else ''

    total = len(groups)

    sp = StatusPrinter(file)
    sp.print_status(prefix + format_meter(0, total, 0))

    def progress_decorator(func):

        def wrapper(*args, **kwargs):

            start_t = wrapper.start_t
            last_print_t = wrapper.last_print_t
            last_print_n = wrapper.last_print_n
            n = wrapper.n

            if n - last_print_n >= miniters:
                # We check the counter first, to reduce the overhead of
                # time.time()
                cur_t = time.time()
                if cur_t - last_print_t >= mininterval:
                    fmeter = format_meter(n, total, cur_t - start_t)
                    sp.print_status(prefix + fmeter)
                    last_print_n = n
                    last_print_t = cur_t

            wrapper.n += 1
            return func(*args, **kwargs)

        wrapper.start_t = time.time()
        wrapper.last_print_t = wrapper.start_t
        wrapper.last_print_n = 0
        wrapper.n = 0

        return wrapper

    progress_func = progress_decorator(func)
    result = groups.apply(progress_func, *args, **kwargs)

    if not leave:
        sp.print_status('')
        sys.stdout.write('\r')

    return result
