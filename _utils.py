import os
import subprocess
from platform import system as _curos
CUR_OS = _curos()
IS_WIN = CUR_OS in ['Windows', 'cli']
IS_NIX = (not IS_WIN) and any(
    CUR_OS.startswith(i) for i in
    ['CYGWIN', 'MSYS', 'Linux', 'Darwin', 'SunOS', 'FreeBSD', 'NetBSD'])


# Py2/3 compat. Empty conditional to avoid coverage
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
        IS_WIN10 = False
        if IS_WIN:
            import pywintypes
            import win32console
            h_stdout = win32console.GetStdHandle(-11)
            cm_stdout = h_stdout.GetConsoleMode()
            h_stdout.SetConsoleMode(cm_stdout | 4) # ENABLE_VIRTUAL_TERMINAL_PROCESSING
            h_stderr = win32console.GetStdHandle(-12)
            cm_stderr = h_stderr.GetConsoleMode()
            h_stderr.SetConsoleMode(cm_stderr | 4)
            IS_WIN10 = True
        else:
            (cm_stdout, h_stdout, cm_stderr, h_stderr) = (None, None, None, None)
    except pywintypes.error:
        (cm_stdout, h_stdout, cm_stderr, h_stderr) = (None, None, None, None)
    except ImportError:
        (cm_stdout, h_stdout, cm_stderr, h_stderr) = (None, None, None, None)
        
    try:
        from weakref import WeakSet
    except ImportError:
        WeakSet = set

    try:
        _basestring = basestring
    except NameError:
        _basestring = str

    try:  # py>=2.7,>=3.1
        from collections import OrderedDict as _OrderedDict
    except ImportError:
        try:  # older Python versions with backported ordereddict lib
            from ordereddict import OrderedDict as _OrderedDict
        except ImportError:  # older Python versions without ordereddict lib
            # Py2.6,3.0 compat, from PEP 372
            from collections import MutableMapping

            class _OrderedDict(dict, MutableMapping):
                # Methods with direct access to underlying attributes
                def __init__(self, *args, **kwds):
                    if len(args) > 1:
                        raise TypeError('expected at 1 argument, got %d',
                                        len(args))
                    if not hasattr(self, '_keys'):
                        self._keys = []
                    self.update(*args, **kwds)

                def clear(self):
                    del self._keys[:]
                    dict.clear(self)

                def __setitem__(self, key, value):
                    if key not in self:
                        self._keys.append(key)
                    dict.__setitem__(self, key, value)

                def __delitem__(self, key):
                    dict.__delitem__(self, key)
                    self._keys.remove(key)

                def __iter__(self):
                    return iter(self._keys)

                def __reversed__(self):
                    return reversed(self._keys)

                def popitem(self):
                    if not self:
                        raise KeyError
                    key = self._keys.pop()
                    value = dict.pop(self, key)
                    return key, value

                def __reduce__(self):
                    items = [[k, self[k]] for k in self]
                    inst_dict = vars(self).copy()
                    inst_dict.pop('_keys', None)
                    return (self.__class__, (items,), inst_dict)

                # Methods with indirect access via the above methods
                setdefault = MutableMapping.setdefault
                update = MutableMapping.update
                pop = MutableMapping.pop
                keys = MutableMapping.keys
                values = MutableMapping.values
                items = MutableMapping.items

                def __repr__(self):
                    pairs = ', '.join(map('%r: %r'.__mod__, self.items()))
                    return '%s({%s})' % (self.__class__.__name__, pairs)

                def copy(self):
                    return self.__class__(self)

                @classmethod
                def fromkeys(cls, iterable, value=None):
                    d = cls()
                    for key in iterable:
                        d[key] = value
                    return d


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
    """
    could alternately use e.g. sb = win32console.GetStdHandle(-11)
    sb.GetConsoleScreenBufferInfo() which returns key->values MaximumWindowSize[X, Y], CursorPosition[X, Y], Window[Left, Top, Right, Bottom], Attributes, Size[X, Y]
    sb.SetConsoleCursorPosition(win32console.PyCoordType(X,Y)) allows you to change the position
    """
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
            (_bufx, _bufy, _curx, _cury, _wattr, left, _top, right, _bottom,
             _maxx, _maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
            # nlines = bottom - top + 1
            return right - left  # +1
    except:
        pass
    return None

def _reset_mode_stdconsoles(h_stdout, cm_stdout, h_stderr, cm_stderr):
    _reset_console_mode_win(h_stderr, cm_stderr) # do this one first in case the stdout mode changed the default stderr mode
    _reset_console_mode_win(h_stdout, cm_stdout)

def _reset_console_mode_win(h, cm):
    h.SetConsoleMode(cm)

def _environ_cols_tput(*args):  # pragma: no cover
    """ cygwin xterm (windows) """
    try:
        import shlex
        cols = int(subprocess.check_call(shlex.split('tput cols')))
        # rows = int(subprocess.check_call(shlex.split('tput lines')))
        return cols
    except:
        pass
    return None


def _environ_cols_linux(fp):  # pragma: no cover

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

def _console_get_pos_windows(): # pragma: no cover
    try:
        from ctypes import windll, create_string_buffer
        import struct
        h = windll.kernel32.GetStdHandle(-11)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
        if res:
            (_bufx, _bufy, _curx, _cury, _wattr, left, _top, right, _bottom,
             _maxx, _maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
            # nlines = bottom - top + 1
            return _cury*65536 + _curx  # +1
    except:
        pass
    return None

def _move_relative(fp, lines):
    from sys import stdout, stderr
    if (fp == stdout or fp == stderr): # otherwise don't bother moving
        if lines > 0:
            fp.write(_unicode('\n' * lines))
        elif lines < 0:
            if IS_NIX or IS_WIN10 or not (fp == stdout or fp == stderr):
                fp.write(_term_move_up() * -lines)
            elif IS_WIN:
                _console_move_cursor_up_windows(-lines)

def _move_absolute(fp, xy = None, x = None, y = None):
    from sys import stdout, stderr
    from ctypes import windll
    if (fp == stdout or fp == stderr):
        if xy is None:
            xy = y*65536 + x
        if y is None: # someone probably put x into xy and y into x by positional arguments
            xy = x*65536 + xy
        if xy is not None:
            suc = windll.kernel32.SetConsoleCursorPosition(windll.kernel32.GetStdHandle(-11),xy)
            if suc: return xy
    return None

def _console_move_cursor_up_windows(lines=0, cp=None):
    from ctypes import windll
#    from sys import stdout
    h = windll.kernel32.GetStdHandle(-11)
    if cp is None:
        cp = _console_get_pos_windows()
    if cp:
        new_coords = cp - (lines*65536)
        suc = windll.kernel32.SetConsoleCursorPosition(h,new_coords)
        if suc:
            return new_coords
        else: # failure to move. Consider raising an exception.
            return cp
    return None

def _term_move_up():  # pragma: no cover
    return '' if (os.name == 'nt') and (colorama is None) else '\x1b[A'