from __future__ import print_function
from time import sleep
from tqdm import tqdm
from multiprocessing import Pool, freeze_support, RLock


L = list(range(9))


def progresser(n):
    interval = 0.001 / (n + 2)
    total = 5000
    text = "#{}, est. {:<04.2}s".format(n, interval * total)
    for _ in tqdm(range(total), desc=text, position=n):
        sleep(interval)


if __name__ == '__main__':
    freeze_support()  # for Windows support
    p = Pool(len(L),
             initializer=tqdm.set_lock,
             initargs=(RLock(),))
    p.map(progresser, L)
    print("\n" * (len(L) - 2))

    # alternatively, on UNIX, just use the default internal lock
    p = Pool(len(L))
    p.map(progresser, L)
    print("\n" * (len(L) - 2))
