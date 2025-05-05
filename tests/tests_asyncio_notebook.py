"""
Tests for tqdm.asyncio_notebook functionality in Jupyter notebook context.
"""
import asyncio
from functools import partial

from tqdm.asyncio_notebook import tarange, tqdm_asyncio_notebook
from .tests_tqdm import mark

# Create partials for convenience with no miniters/mininterval delays
tqdm = partial(tqdm_asyncio_notebook, miniters=0, mininterval=0)
trange = partial(tarange, miniters=0, mininterval=0)
as_completed = partial(tqdm_asyncio_notebook.as_completed, miniters=0, mininterval=0)
gather = partial(tqdm_asyncio_notebook.gather, miniters=0, mininterval=0)

async def work(i):
    """Coroutine that sleeps then returns its input."""
    await asyncio.sleep(0.01 * i)
    return i

async def double(i):
    """Simple coroutine doubling its input."""
    return i * 2

@mark.asyncio
async def test_notebook_async_range():
    """Test async iteration over trange in notebook."""
    results = []
    async for i in trange(5):
        results.append(i)
    assert results == list(range(5))

@mark.asyncio
async def test_notebook_async_as_completed():
    """Test as_completed yields tasks as they complete in notebook."""
    tasks = [work(i) for i in range(5, 0, -1)]
    order = []
    for fut in as_completed(tasks, total=5):
        order.append(await fut)
    assert set(order) == set(range(1, 6))
    # ensure it's not sequential order
    assert order != list(range(1, 6))

@mark.asyncio
async def test_notebook_async_gather():
    """Test gather returns results in original order in notebook."""
    res = await gather(*[double(i) for i in range(5)])
    assert res == [i * 2 for i in range(5)]
