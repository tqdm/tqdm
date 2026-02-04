import time
from tkinter import Button, Tk

from tqdm.tk import tqdm

window = Tk()


pbar = tqdm(tk_parent=window, total=10)


def run():
    pbar.reset(total=10)
    for _ in range(10):
        time.sleep(0.1)
        pbar.update(1)


button = Button(window, text="Start task", command=run)
button.pack()


# TODO - closing either window doesn't work yet


window.mainloop()
