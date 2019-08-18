from __future__ import print_function
from time import sleep
from tqdm import tqdm, trange
from multiprocessing import Pool, freeze_support
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import sys


L = list(range(9))[::-1]


def progresser(n, auto_position=False):
    interval = 0.001 / (len(L) - n + 2)
    total = 5000
    text = "#{}, est. {:<04.2}s".format(n, interval * total)
    for _ in tqdm(range(total), desc=text, position=None if auto_position else n):
        sleep(interval)
    # NB: may not clear instances with higher `position` upon completion
    # since this worker may not know about other bars #796
    if auto_position:
        # we think we know about other bars (currently only py3 threading)
        if n == 6:
            tqdm.write("n == 6 completed")

if sys.version_info[:1] > (2,):
    progresser_thread = partial(progresser, auto_position=True)
else:
    progresser_thread = progresser


if __name__ == '__main__':
    freeze_support()  # for Windows support
    print("Multi-processing")
    p = Pool(len(L), initializer=tqdm.set_lock, initargs=(tqdm.get_lock(),))
    p.map(progresser, L)

    # unfortunately need ncols
    # to print spaces over leftover multi-processing bars (#796)
    with tqdm(leave=False) as t:
        ncols = t.ncols or 80
    print(("{msg:<{ncols}}").format(msg="Multi-threading", ncols=ncols))

    with ThreadPoolExecutor(4) as p:
        p.map(progresser_thread, L)

    print("Manual nesting")
    for i in trange(16, desc="1"):
        for _ in trange(16, desc="2 @ %d" % i, leave=i % 2):
            sleep(0.01)
