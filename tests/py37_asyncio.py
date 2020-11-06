from functools import partial, wraps
from time import time
import asyncio

from tqdm.asyncio import tqdm_asyncio, tarange
from tqdm.contrib.asyncio import map_async
from .tests_tqdm import pretest_posttest  # NOQA, pylint: disable=unused-import
from .tests_tqdm import StringIO, closing
from .tests_perf import retry_on_except

tqdm = partial(tqdm_asyncio, miniters=0, mininterval=0)
trange = partial(tarange, miniters=0, mininterval=0)
as_completed = partial(tqdm_asyncio.as_completed, miniters=0, mininterval=0)


def with_setup_sync(func):
    @wraps(func)
    def inner(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return inner


def count(start=0, step=1):
    i = start
    while True:
        new_start = yield i
        if new_start is None:
            i += step
        else:
            i = new_start


async def acount(*args, **kwargs):
    for i in count(*args, **kwargs):
        yield i


async def square(x):
    await asyncio.sleep(0.1)
    return x ** 2


@with_setup_sync
async def test_generators():
    """Test asyncio generators"""
    with closing(StringIO()) as our_file:
        async for i in tqdm(count(), desc="counter", file=our_file):
            if i >= 8:
                break
        assert '9it' in our_file.getvalue()
        our_file.seek(0)
        our_file.truncate()

        async for i in tqdm(acount(), desc="async_counter", file=our_file):
            if i >= 8:
                break
        assert '9it' in our_file.getvalue()


@with_setup_sync
async def test_range():
    """Test asyncio range"""
    with closing(StringIO()) as our_file:
        async for _ in tqdm(range(9), desc="range", file=our_file):
            pass
        assert '9/9' in our_file.getvalue()
        our_file.seek(0)
        our_file.truncate()

        async for _ in trange(9, desc="trange", file=our_file):
            pass
        assert '9/9' in our_file.getvalue()


@with_setup_sync
async def test_nested():
    """Test asyncio nested"""
    with closing(StringIO()) as our_file:
        async for _ in tqdm(trange(9, desc="inner", file=our_file),
                            desc="outer", file=our_file):
            pass
        assert 'inner: 100%' in our_file.getvalue()
        assert 'outer: 100%' in our_file.getvalue()


@with_setup_sync
async def test_coroutines():
    """Test asyncio coroutine.send"""
    with closing(StringIO()) as our_file:
        with tqdm(count(), file=our_file) as pbar:
            async for i in pbar:
                if i == 9:
                    pbar.send(-10)
                elif i < 0:
                    assert i == -9
                    break
        assert '10it' in our_file.getvalue()


@retry_on_except(check_cpu_time=False)
@with_setup_sync
async def test_as_completed():
    """Test asyncio as_completed"""
    with closing(StringIO()) as our_file:
        t = time()
        skew = time() - t
        for i in as_completed([asyncio.sleep(0.01 * i)
                               for i in range(30, 0, -1)], file=our_file):
            await i
        t = time() - t - 2 * skew
        assert 0.27 < t < 0.33, t
        assert '30/30' in our_file.getvalue()


@with_setup_sync
async def test_map_async(capsys):
    await map_async(square, range(9))
    _, err = capsys.readouterr()
    assert '9/9' in err
