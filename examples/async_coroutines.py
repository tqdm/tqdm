"""
Asynchronous examples using `asyncio`, `async` and `await` on `python>=3.7`.
"""
import asyncio

from tqdm.asyncio import tqdm, trange


def count(start=0, step=1):
    i = start
    while True:
        new_start = yield i
        if new_start is None:
            i += step
        else:
            i = new_start


async def main():
    N = int(1e6)
    async for row in tqdm(trange(N, desc="inner"), desc="outer"):
        if row >= N:
            break
    with tqdm(count(), desc="coroutine", total=N + 2) as pbar:
        async for row in pbar:
            if row == N:
                pbar.send(-10)
            elif row < 0:
                assert row == -9
                break
    # should be ~1sec rather than ~50s due to async scheduling
    for i in tqdm.as_completed([asyncio.sleep(0.01 * i)
                                for i in range(100, 0, -1)], desc="as_completed"):
        await i


if __name__ == "__main__":
    asyncio.run(main())
