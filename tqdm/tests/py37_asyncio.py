import asyncio
from functools import partial

from tests_tqdm import with_setup, pretest, posttest, StringIO, closing
from tqdm.asyncio import tqdm_asyncio, tarange


def count(start=0, step=1):
    i = start
    while True:
        new_start = yield i
        if new_start is None:
            i += step
        else:
            i = new_start


async def main():
    with closing(StringIO()) as our_file:
        tqdm = partial(tqdm_asyncio, file=our_file, miniters=0, mininterval=0)
        trange = partial(tarange, file=our_file, miniters=0, mininterval=0)

        async for row in tqdm(count(), desc="counter"):
            if row >= 8:
                break
        assert '9it' in our_file.getvalue()
        our_file.seek(0)
        our_file.truncate()

        async for row in tqdm(range(9), desc="range"):
            pass
        assert '9/9' in our_file.getvalue()
        our_file.seek(0)
        our_file.truncate()

        async for row in tqdm(trange(9, desc="inner"), desc="outer"):
            pass
        assert 'inner: 100%' in our_file.getvalue()
        assert 'outer: 100%' in our_file.getvalue()
        our_file.seek(0)
        our_file.truncate()

        with tqdm(count(), desc="coroutine") as pbar:
            async for row in pbar:
                if row == 9:
                    pbar.send(-10)
                elif row < 0:
                    assert row == -9
                    break
        assert '10it' in our_file.getvalue()


@with_setup(pretest, posttest)
def test_all():
    asyncio.run(main())
