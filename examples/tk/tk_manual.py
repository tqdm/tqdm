from tqdm.tk import tqdm
from time import sleep
from tkinter import Tk, Button


window = Tk()


pbar = tqdm(total=30, tk_parent=window)


def run_task():
    for i in range(30):
        sleep(0.1)
        pbar.update(1)
    pbar.close()


start_button = Button(window, text="Start", command=run_task)
start_button.pack()


# Everything works fine (except some errors when you close the windows)
# Cancel not implemented here


window.mainloop()
