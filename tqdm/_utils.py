import os
import subprocess
from platform import system as _curos
CUR_OS = _curos()
IS_WIN = CUR_OS in ['Windows', 'cli']
IS_NIX = (not IS_WIN) and any(
    CUR_OS.startswith(i) for i in
    ['CYGWIN', 'MSYS', 'Linux', 'Darwin', 'SunOS', 'FreeBSD'])


if True:  # pragma: no cover
    try:
        _range = xrange
    except NameError:
        _range = range

    try:
        _unich = unichr
    except NameError:
        _unich = chr

    try:
        _unicode = unicode
    except NameError:
        _unicode = str

    try:
        if IS_WIN:
            import colorama
            colorama.init()
        else:
            colorama = None
    except ImportError:
        colorama = None

    try:
        from weakref import WeakSet
    except ImportError:
        WeakSet = set


def _is_utf(encoding):
    return encoding.lower().startswith('utf-') or ('U8' == encoding)


def _supports_unicode(file):
    return _is_utf(file.encoding) if (
        getattr(file, 'encoding', None) or
        # FakeStreams from things like bpython-curses can lie
        getattr(file, 'interface', None)) else False  # pragma: no cover


def _environ_cols_wrapper():  # pragma: no cover
    """
    Return a function which gets width and height of console
    (linux,osx,windows,cygwin).
    """
    _environ_cols = None
    if IS_WIN:
        _environ_cols = _environ_cols_windows
        if _environ_cols is None:
            _environ_cols = _environ_cols_tput
    if IS_NIX:
        _environ_cols = _environ_cols_linux
    return _environ_cols


def _environ_cols_windows(fp):  # pragma: no cover
    try:
        from ctypes import windll, create_string_buffer
        import struct
        from sys import stdin, stdout

        io_handle = None
        if fp == stdin:
            io_handle = -10
        elif fp == stdout:
            io_handle = -11
        else:  # assume stderr
            io_handle = -12

        h = windll.kernel32.GetStdHandle(io_handle)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
        if res:
            (bufx, bufy, curx, cury, wattr, left, top, right, bottom,
             maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
            # nlines = bottom - top + 1
            return right - left  # +1
    except:
        pass
    return None


def _environ_cols_tput(*args):  # pragma: no cover
    """ cygwin xterm (windows) """
    try:
        import subprocess
        import shlex
        cols = int(subprocess.check_call(shlex.split('tput cols')))
        # rows = int(subprocess.check_call(shlex.split('tput lines')))
        return cols
    except:
        pass
    return None


def _environ_cols_linux(fp):  # pragma: no cover

    # import os
    # if fp is None:
    #     try:
    #         fp = os.open(os.ctermid(), os.O_RDONLY)
    #     except:
    #         pass
    try:
        from termios import TIOCGWINSZ
        from fcntl import ioctl
        from array import array
    except ImportError:
        return None
    else:
        try:
            return array('h', ioctl(fp, TIOCGWINSZ, '\0' * 8))[1]
        except:
            try:
                from os.environ import get
            except ImportError:
                return None
            else:
                return int(get('COLUMNS', 1)) - 1


def _term_move_up():  # pragma: no cover
    return '' if (os.name == 'nt') and (colorama is None) else '\x1b[A'


def _sh(*cmd, **kwargs):
    return subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            **kwargs).communicate()[0].decode('utf-8')
