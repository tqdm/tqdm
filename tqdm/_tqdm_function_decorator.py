from ._tqdm import tqdm

__author__ = {"github.com/": ["twolodzko"]}

def tqdm_function_decorator(*args, **kwargs):
    """
    Decorate a function by adding a progress bar

    Parameters
    ----------
    *args, **kwargs
        Parameters passed to tqdm.

    Returns
    -------
    Decorated function.

    Examples
    --------
    >>> from tqdm import tqdm_function_decorator
    >>> from time import sleep
    >>> N_ITERS = 5
    >>> @tqdm_function_decorator(total=N_ITERS)
        def sleeper():
            sleep(1)
    >>> for _ in range(N_ITERS):
            sleeper()
    """
    class PbarFuncDecorator(object):
        """
        The decorator class. It takes a function as an input
        and decorates it, so every call invokes tqdm an update
        in progress bar.
        """
        def __init__(self, func):
            self.func = func
            self.pbar = tqdm(*args, **kwargs)

        def __call__(self, *args, **kwargs):
            tmp = self.func(*args, **kwargs)
            self.pbar.update()
            return tmp
    return PbarFuncDecorator
