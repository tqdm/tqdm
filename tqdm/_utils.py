import os

try:    # pragma: no cover
    _range = xrange
except NameError:    # pragma: no cover
    _range = range


try:    # pragma: no cover
    _unich = unichr
except NameError:    # pragma: no cover
    _unich = chr

try:  # pragma: no cover
    import colorama
    colorama.init()
except ImportError:  # pragma: no cover
    colorama = None


def _is_utf(encoding):
    return ('U8' == encoding) or ('utf' in encoding) or ('UTF' in encoding)


def _supports_unicode(file):
    if not getattr(file, 'encoding', None):
        return False
    return _is_utf(file.encoding)


def _environ_cols_wrapper():  # pragma: no cover
    """
    Return a function which gets width and height of console
    (linux,osx,windows,cygwin).
    """
    import platform
    current_os = platform.system()
    _environ_cols = None
    if current_os == 'Windows':
        _environ_cols = _environ_cols_windows
        if _environ_cols is None:
            _environ_cols = _environ_cols_tput
    if current_os in ['Linux', 'Darwin'] or current_os.startswith('CYGWIN'):
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
    if os.name == 'nt':
        if colorama is None:
            return ''
    return '\x1b[A'
