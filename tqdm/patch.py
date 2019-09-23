import ast
import builtins
import inspect
import os
import sys
from datetime import datetime as dt

import colorama
from colorama import Fore as F

from tqdm import tqdm as TQDM


def getCols(default=120):
    try:
        ncols, _rows = os.get_terminal_size(1)
    except:
        ncols = default
    return ncols

def print(*args, sep=' ', file=None, end='\n', color=None, flush=True):
    R = colorama.Style.RESET_ALL

    ncols = getCols()
    frame = inspect.stack()[1]
    fpath = frame.filename
    fname = F.CYAN + os.path.basename(fpath) + R
    dirpath = os.path.dirname(fpath)
    dirname = os.path.basename(dirpath)
    dirname = F.YELLOW + "{:<12}".format(dirname) + R

    lineno = frame.lineno
    funcname = frame.function
    funcwidth = max((len(f) for f in getFuncNames(fpath)), default=10)
    funcname = ("{:<%d}" % funcwidth).format(funcname)

    l_bar = f"{dirname}/{fname}({funcname}):{lineno} -> " + (
        ("{:<%d}" % (int(0.65*ncols))).format("{desc}"))

    bar_format = dt.now().strftime("%H:%M") + " | " f"{l_bar}"

    msg = sep.join(map(str, args))
    if color is not None: msg = color + msg + R
    msg = bar_format.format(desc=msg)
    r = tqdm.write(msg, end=end, file=file)
    if flush: sys.stdout.flush()
    return r


def wcl(infilepath):
    with open(infilepath) as infile:
        return sum(1 for line in infile)


def getFuncNames(infilepath):
    try:
        with open(infilepath) as infile:
            body = ast.parse(infile.read(), filename=infilepath)
            return [f.name for f in body.body if isinstance(f, ast.FunctionDef)]
    except:
        return []


class tqdm(TQDM):
    def __init__(self, iterable=None, desc=None, total=None, leave=True,
                 file=None, ncols=None, mininterval=0.1, maxinterval=10.0,
                 miniters=None, ascii=None, disable=False, unit='it',
                 unit_scale=False, dynamic_ncols=False, smoothing=0.3,
                 bar_format=None, initial=0, position=None, postfix=None,
                 unit_divisor=1000, write_bytes=None, gui=False, **kwargs):

        if desc is None: desc = "Doing stuff..."
        if not desc.endswith(":"): desc += ":"
        if ncols is None: ncols = getCols()

        R = colorama.Style.RESET_ALL

        frame = inspect.stack()[1]
        fpath = frame.filename
        fname = F.CYAN + os.path.basename(fpath) + R
        dirpath = os.path.dirname(fpath)
        dirname = F.YELLOW + "{:<12}".format(os.path.basename(dirpath)) + R

        lineno = frame.lineno
        funcname = frame.function
        funcwidth = max((len(f) for f in getFuncNames(fname)), default=10)
        funcname = ("{:<%d}" %funcwidth).format(funcname)

        if bar_format is None:

            l_bar = f"{dirname}/{fname}({funcname}):{lineno} -> " + ("{" + "{}:<{}".format("desc", int(0.65*ncols)) + "}")

            bar_format = dt.now().strftime("%H:%M") + " | " f"{l_bar}" "{bar}{r_bar}"

        super().__init__(iterable, desc, total, leave,
                         file, ncols, mininterval, maxinterval,
                         miniters, ascii, disable, unit,
                         unit_scale, dynamic_ncols, smoothing,
                         bar_format, initial, position, postfix,
                         unit_divisor, write_bytes, gui, **kwargs)

builtins.__print__, builtins.print = builtins.print, print
