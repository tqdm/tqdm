"""
Thin wrappers around `itertools`.
"""
import itertools

__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['product']


def product(*iterables, **tqdm_kwargs):
    """
    Equivalent of `itertools.product`.

    Parameters
    ----------
    tqdm_class  : [default: tqdm.auto.tqdm].
    """
    kwargs = tqdm_kwargs.copy()
    tqdm_class = kwargs.pop("tqdm_class", None)
    if tqdm_class is None:
        from ..auto import tqdm as tqdm_class
    try:
        lens = list(map(len, iterables))
    except TypeError:
        total = None
    else:
        total = 1
        for i in lens:
            total *= i
        kwargs.setdefault("total", total)
    with tqdm_class(**kwargs) as t:
        it = itertools.product(*iterables)
        for i in it:
            yield i
            t.update()
