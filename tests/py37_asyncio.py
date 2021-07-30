import asyncio
from functools import partial
from sys import platform
from time import time

from tqdm.asyncio import tarange, tqdm_asyncio

from .tests_tqdm import StringIO, closing, mark

tqdm = partial(tqdm_asyncio, miniters=0, mininterval=0)
trange = partial(tarange, miniters=0, mininterval=0)
as_completed = partial(tqdm_asyncio.as_completed, miniters=0, mininterval=0)
gather = partial(tqdm_asyncio.gather, miniters=0, mininterval=0)


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


@mark.asyncio
async def test_break():
    """Test asyncio break"""
    pbar = tqdm(count())
    async for _ in pbar:
        break
    pbar.close()


@mark.asyncio
async def test_generators(capsys):
    """Test asyncio generators"""
    with tqdm(count(), desc="counter") as pbar:
        async for i in pbar:
            if i >= 8:
                break
    _, err = capsys.readouterr()
    assert '9it' in err

    with tqdm(acount(), desc="async_counter") as pbar:
        async for i in pbar:
            if i >= 8:
                break
    _, err = capsys.readouterr()
    assert '9it' in err


@mark.asyncio
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


@mark.asyncio
async def test_nested():
    """Test asyncio nested"""
    with closing(StringIO()) as our_file:
        async for _ in tqdm(trange(9, desc="inner", file=our_file),
                            desc="outer", file=our_file):
            pass
        assert 'inner: 100%' in our_file.getvalue()
        assert 'outer: 100%' in our_file.getvalue()


@mark.asyncio
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


@mark.slow
@mark.asyncio
@mark.parametrize("tol", [0.2 if platform.startswith("darwin") else 0.1])
async def test_as_completed(capsys, tol):
    """Test asyncio as_completed"""
    for retry in range(3):
        t = time()
        skew = time() - t
        for i in as_completed([asyncio.sleep(0.01 * i) for i in range(30, 0, -1)]):
            await i
        t = time() - t - 2 * skew
        try:
            assert 0.3 * (1 - tol) < t < 0.3 * (1 + tol), t
            _, err = capsys.readouterr()
            assert '30/30' in err
        except AssertionError:
            if retry == 2:
                raise


async def double(i):
    return i * 2


@mark.asyncio
async def test_gather(capsys):
    """Test asyncio gather"""
    res = await gather(*map(double, range(30)))
    _, err = capsys.readouterr()
    assert '30/30' in err
    assert res == list(range(0, 30 * 2, 2))
