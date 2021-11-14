from tqdm.tk import tqdm, trange
from tkinter import Tk, Button
import time
from collections import namedtuple
from functools import partial
from threading import Thread


class Task(Thread):
    def __init__(self):
        super().__init__()
        self.is_cancelled = False

    def run(self):
        for _ in range(10):
            if self.is_cancelled:
                return
            time.sleep(0.1)
            self.pbar.update(1)

        self.pbar.close()

    def cancel(self):
        self.is_cancelled = True


window = Tk()


def start():
    task = Task()
    pbar = tqdm(tk_parent=window, total=10, cancel_callback=task.cancel)
    task.pbar = pbar
    task.start()


button = Button(window, text="Start task", command=start)
button.pack()


window.mainloop()

