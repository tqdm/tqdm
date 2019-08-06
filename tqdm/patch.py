import ast
import inspect
import os
import sys; sys.path.extend(('.', '..'))
from datetime import datetime as dt
import colorama
from colorama import Fore as F

from tqdm import tqdm as TQDM


def print(*args, sep=' ', file=None, end='\n', color=None):
    ncols, _rows = os.get_terminal_size(1)

    frame = inspect.stack()[1]
    fpath = frame.filename
    fname = os.path.basename(fpath)
    dirpath = os.path.dirname(fpath)
    dirname = os.path.basename(dirpath)

    lineno = frame.lineno
    funcname = frame.function
    # sys.stdout.write("*"*30 + '\n')
    # sys.stdout.write(fname)
    # sys.stdout.write('\n' + "*" * 30)
    funcwidth = max(len(f) for f in getFuncNames(fname))
    funcname = ("{:<%d}" % funcwidth).format(funcname)
    # sys.stdout.write("*"*30 + '\n')
    # sys.stdout.write("'" + funcname + "'")
    # sys.stdout.write('\n' + "*"*30)

    R = colorama.Style.RESET_ALL
    l_bar = f"{F.YELLOW + dirname + R}/{F.CYAN + fname + R}({funcname}):{lineno} -> " + (
        ("{:<%d}" % (int(0.75 * ncols))).format("{desc}"))

    bar_format = dt.now().strftime("%H:%M") + " | " f"{l_bar}"

    msg = sep.join(map(str, args))
    msg = l_bar.format(desc=msg)
    if color is not None: msg = color + msg + colorama.Style.RESET_ALL
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
        # if not desc.endswith(":"): desc += ":"
        if ncols is None:
            cols, rows = os.get_terminal_size(1)
            ncols = cols

        frame = inspect.stack()[1]
        fpath = frame.filename
        fname = os.path.basename(fpath)
        dirpath = os.path.dirname(fpath)
        dirname = os.path.basename(dirpath)

        lineno = frame.lineno
        funcname = frame.function
        # sys.stdout.write("*"*30 + '\n')
        # sys.stdout.write(fname)
        # sys.stdout.write('\n' + "*" * 30)
        funcwidth = max(len(f) for f in getFuncNames(fname))
        funcname = ("{:<%d}" %funcwidth).format(funcname)
        # sys.stdout.write("*"*30 + '\n')
        # sys.stdout.write("'" + funcname + "'")
        # sys.stdout.write('\n' + "*"*30)

        if bar_format is None:
            R = colorama.Style.RESET_ALL
            l_bar = f"{F.YELLOW + dirname + R}/{F.CYAN + fname + R}({funcname}):{lineno} -> " + (("{:<%d}" %(int(0.75*ncols))).format("{desc}"))

            bar_format = dt.now().strftime("%H:%M") + " | " f"{l_bar}" "{bar}{r_bar}"

        super().__init__(iterable, desc, total, leave,
                         file, ncols, mininterval, maxinterval,
                         miniters, ascii, disable, unit,
                         unit_scale, dynamic_ncols, smoothing,
                         bar_format, initial, position, postfix,
                         unit_divisor, write_bytes, gui, **kwargs)



for i in tqdm([1,2,3,4,5], desc='hello'):
#     # i**2
    print('hi', color=colorama.Fore.GREEN)
    # time.sleep(1)
# print(getFuncNames('patch.py'))