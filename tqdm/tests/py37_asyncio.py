import asyncio
from functools import partial, wraps
from time import time

from tests_tqdm import with_setup, pretest, posttest, StringIO, closing
from tqdm.asyncio import tqdm_asyncio, tarange


def with_setup_sync(func):
    @with_setup(pretest, posttest)
    @wraps(func)
    def inner():
        return asyncio.run(func())
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


@with_setup_sync
async def test_generators():
    """Test asyncio generators"""
    with closing(StringIO()) as our_file:
        tqdm = partial(tqdm_asyncio, file=our_file, miniters=0, mininterval=0)

        async for row in tqdm(count(), desc="counter"):
            if row >= 8:
                break
        assert '9it' in our_file.getvalue()
        our_file.seek(0)
        our_file.truncate()

        async for row in tqdm(acount(), desc="async_counter"):
            if row >= 8:
                break
        assert '9it' in our_file.getvalue()


@with_setup_sync
async def test_range():
    """Test asyncio range"""
    with closing(StringIO()) as our_file:
        tqdm = partial(tqdm_asyncio, file=our_file, miniters=0, mininterval=0)
        trange = partial(tarange, file=our_file, miniters=0, mininterval=0)

        async for row in tqdm(range(9), desc="range"):
            pass
        assert '9/9' in our_file.getvalue()
        our_file.seek(0)
        our_file.truncate()

        async for row in trange(9, desc="trange"):
            pass
        assert '9/9' in our_file.getvalue()


@with_setup_sync
async def test_nested():
    """Test asyncio nested"""
    with closing(StringIO()) as our_file:
        tqdm = partial(tqdm_asyncio, file=our_file, miniters=0, mininterval=0)
        trange = partial(tarange, file=our_file, miniters=0, mininterval=0)

        async for row in tqdm(trange(9, desc="inner"), desc="outer"):
            pass
        assert 'inner: 100%' in our_file.getvalue()
        assert 'outer: 100%' in our_file.getvalue()


@with_setup_sync
async def test_coroutines():
    """Test asyncio coroutine.send"""
    with closing(StringIO()) as our_file:
        tqdm = partial(tqdm_asyncio, file=our_file, miniters=0, mininterval=0)

        with tqdm(count()) as pbar:
            async for row in pbar:
                if row == 9:
                    pbar.send(-10)
                elif row < 0:
                    assert row == -9
                    break
        assert '10it' in our_file.getvalue()


@with_setup_sync
async def test_async_with():
    """Test asyncio async with context manager"""
    with closing(StringIO()) as our_file:
        tqdm = partial(tqdm_asyncio, file=our_file, miniters=0, mininterval=0)

        async with tqdm(count()) as pbar:
            async for row in pbar:
                if row >= 8:
                    break
        assert '9it' in our_file.getvalue()


@with_setup_sync
async def test_as_completed():
    """Test asyncio as_completed"""
    with closing(StringIO()) as our_file:
        as_completed = partial(tqdm_asyncio.as_completed, file=our_file,
                               miniters=0, mininterval=0)

        t = time()
        skew = time() - t
        for i in as_completed([asyncio.sleep(0.01) for _ in range(100)]):
            await i
        assert time() - t - 2 * skew < (0.01 * 100) / 2, "Assuming >= 2 cores"
        assert '100/100' in our_file.getvalue()
