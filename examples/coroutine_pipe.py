"""
Inserting `tqdm` as a "pipe" in a chain of coroutines.
Not to be confused with `asyncio.coroutine`.
"""
from functools import wraps

from tqdm.auto import tqdm


def autonext(func):
    @wraps(func)
    def inner(*args, **kwargs):
        res = func(*args, **kwargs)
        next(res)
        return res
    return inner


@autonext
def tqdm_pipe(target, **tqdm_kwargs):
    """
    Coroutine chain pipe `send()`ing to `target`.

    This:
    >>> r = receiver()
    >>> p = producer(r)
    >>> next(r)
    >>> next(p)

    Becomes:
    >>> r = receiver()
    >>> t = tqdm.pipe(r)
    >>> p = producer(t)
    >>> next(r)
    >>> next(p)
    """
    with tqdm(**tqdm_kwargs) as pbar:
        while True:
            obj = (yield)
            target.send(obj)
            pbar.update()


def source(target):
    for i in ["foo", "bar", "baz", "pythonista", "python", "py"]:
        target.send(i)
    target.close()


@autonext
def grep(pattern, target):
    while True:
        line = (yield)
        if pattern in line:
            target.send(line)


@autonext
def sink():
    while True:
        line = (yield)
        tqdm.write(line)


if __name__ == "__main__":
    source(
        tqdm_pipe(
            grep('python',
                 sink())))
