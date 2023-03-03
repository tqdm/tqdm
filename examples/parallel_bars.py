from concurrent.futures import ThreadPoolExecutor
from functools import partial
from multiprocessing import Pool, RLock, freeze_support
from random import random
from threading import RLock as TRLock
from time import sleep

from tqdm.auto import tqdm, trange
from tqdm.contrib.concurrent import process_map, thread_map

NUM_SUBITERS = 9


def progresser(n, auto_position=True, write_safe=False, blocking=True, progress=False):
    interval = random() * 0.002 / (NUM_SUBITERS - n + 2)  # nosec
    total = 5000
    text = f"#{n}, est. {interval * total:<04.2g}s"
    for _ in trange(total, desc=text, disable=not progress,
                    lock_args=None if blocking else (False,),
                    position=None if auto_position else n):
        sleep(interval)
    # NB: may not clear instances with higher `position` upon completion
    # since this worker may not know about other bars #796
    if write_safe:
        # we think we know about other bars (currently only py3 threading)
        if n == 6:
            tqdm.write("n == 6 completed")
    return n + 1


if __name__ == '__main__':
    freeze_support()  # for Windows support
    L = list(range(NUM_SUBITERS))[::-1]

    print("Simple thread mapping")
    thread_map(partial(progresser, write_safe=True), L, max_workers=4)

    print("Simple process mapping")
    process_map(partial(progresser), L, max_workers=4)

    print("Manual nesting")
    for i in trange(16, desc="1"):
        for _ in trange(16, desc="2 @ %d" % i, leave=i % 2):
            sleep(0.01)

    print("Multi-processing")
    tqdm.set_lock(RLock())
    p = Pool(initializer=tqdm.set_lock, initargs=(tqdm.get_lock(),))
    p.map(partial(progresser, progress=True), L)

    print("Multi-threading")
    tqdm.set_lock(TRLock())
    with ThreadPoolExecutor(initializer=tqdm.set_lock, initargs=(tqdm.get_lock(),)) as p:
        p.map(partial(progresser, progress=True, write_safe=True, blocking=False), L)
