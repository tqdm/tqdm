from __future__ import print_function
from time import sleep
from tqdm import tqdm, trange
from multiprocessing import Pool, freeze_support, RLock


L = list(range(9))


def progresser(n):
    interval = 0.001 / (len(L) - n + 2)
    total = 5000
    text = "#{}, est. {:<04.2}s".format(n, interval * total)
    # NB: ensure position>0 to prevent printing '\n' on completion.
    # `tqdm` can't autmoate this since this thread
    # may not know about other bars in other threads #477.
    for _ in tqdm(range(total), desc=text, position=n + 1):
        sleep(interval)


if __name__ == '__main__':
    freeze_support()  # for Windows support
    p = Pool(len(L),
             initializer=tqdm.set_lock,
             initargs=(RLock(),))
    p.map(progresser, L)
    print('\n' * len(L))

    # alternatively, on UNIX, just use the default internal lock
    p = Pool(len(L))
    p.map(progresser, L)
    print('\n' * len(L))

    # a manual test demonstrating automatic fix for #477 on one thread
    for _ in trange(10, desc="1", position=1):
        for _ in trange(10, desc="2", position=0):
            sleep(0.01)
    print('\n')
