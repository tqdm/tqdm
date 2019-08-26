import ast
import inspect
import os
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

def print(*args, sep=' ', file=None, end='\n', color=None):
    ncols = getCols()
    frame = inspect.stack()[1]
    fpath = frame.filename
    fname = os.path.basename(fpath)
    dirpath = os.path.dirname(fpath)
    dirname = os.path.basename(dirpath)

    lineno = frame.lineno
    funcname = frame.function
    funcwidth = max(len(f) for f in getFuncNames(fname))
    funcname = ("{:<%d}" % funcwidth).format(funcname)

    R = colorama.Style.RESET_ALL
    l_bar = f"{F.YELLOW + dirname + R}/{F.CYAN + fname + R}({funcname}):{lineno} -> " + (
        ("{:<%d}" % (int(0.7*ncols))).format("{desc}"))

    bar_format = dt.now().strftime("%H:%M") + " | " f"{l_bar}"

    msg = sep.join(map(str, args))
    if color is not None: msg = color + msg + colorama.Style.RESET_ALL
    msg = bar_format.format(desc=msg)
    return tqdm.write(msg, end=end, file=file)


def wcl(infilepath):
    with open(infilepath) as infile:
        return sum(1 for line in infile)


def getFuncNames(infilepath):
    with open(infilepath) as infile:
        body = ast.parse(infile.read(), filename=infilepath)
        return [f.name for f in body.body if isinstance(f, ast.FunctionDef)]


class tqdm(TQDM):
    def __init__(self, iterable=None, desc=None, total=None, leave=True,
                 file=None, ncols=None, mininterval=0.1, maxinterval=10.0,
                 miniters=None, ascii=None, disable=False, unit='it',
                 unit_scale=False, dynamic_ncols=False, smoothing=0.3,
                 bar_format=None, initial=0, position=None, postfix=None,
                 unit_divisor=1000, write_bytes=None, gui=False, **kwargs):

        if desc is None: desc = "Doing stuff..."
        if not desc.endswith(":"): desc += ":"
        if ncols is None:
            ncols = getCols()

        frame = inspect.stack()[1]
        fpath = frame.filename
        fname = os.path.basename(fpath)
        dirpath = os.path.dirname(fpath)
        dirname = os.path.basename(dirpath)

        lineno = frame.lineno
        funcname = frame.function
        funcwidth = max(len(f) for f in getFuncNames(fname))
        funcname = ("{:<%d}" %funcwidth).format(funcname)

        if bar_format is None:
            R = colorama.Style.RESET_ALL
            l_bar = f"{F.YELLOW + dirname + R}/{F.CYAN + fname + R}({funcname}):{lineno} -> " + ("{" + "{}:<{}".format("desc", int(0.7*ncols)) + "}")

            bar_format = dt.now().strftime("%H:%M") + " | " f"{l_bar}" "{bar}{r_bar}"

        super().__init__(iterable, desc, total, leave,
                         file, ncols, mininterval, maxinterval,
                         miniters, ascii, disable, unit,
                         unit_scale, dynamic_ncols, smoothing,
                         bar_format, initial, position, postfix,
                         unit_divisor, write_bytes, gui, **kwargs)
