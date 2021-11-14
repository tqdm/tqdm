from tqdm.tk import tqdm, trange
from tkinter import Tk, Button
import time
from collections import namedtuple
from functools import partial
from threading import Thread


window = Tk()


pbar = tqdm(tk_parent=window, total=10)


def run():
    pbar.reset(total=10)
    for i in range(10):
        time.sleep(0.1)
        pbar.update(1)


button = Button(window, text="Start task", command=run)
button.pack()


# TODO - closing either window doesn't work yet


window.mainloop()

