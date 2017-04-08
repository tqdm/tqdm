import os
from sys import stdout, stdin # pragma: no cover # regardless of OS, we'll need these, esp. stdout

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
        from pywintypes import error as _pywintypesErr
    except ImportError:
        _pywintypesErr = Exception

    if IS_WIN:
        try:
            from sys import stderr #, getwindowsversion
#           import struct # only needed in one method each, returned objects not from these classes
            from ctypes import windll, create_string_buffer
            import win32console # an object from this py is returned by _set_winansi_plus_handles():
        except ImportError:
            pass # must be cygwin? bad install of python?
        try:
            import colorama
            colorama.init()  # this loading does not nec. mean that ANSI escapes work in windows.
        except ImportError:
            colorama = None
    else:
        colorama = None

    (IS_WINANSI, ((_cm_stdout, _h_stdout), (_cm_stderr, _h_stderr))) = _set_winansi_plus_handles()

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

def _move_relative(fp, lines): # pragma: no cover
    if lines > 0:
        fp.write(_unicode('\n' * lines))
    elif lines < 0:
        if IS_NIX or IS_WINANSI or not (fp == stdout or fp == stderr):
            fp.write(_term_move_up() * -lines) # wouldn't navigation in a non-stream/tty device be different than stdout?
        elif IS_WIN:
            _console_move_cursor_up_windows(fp, -lines, bol=True)

def _term_move_up():  # pragma: no cover
    return '\x1b[A' # removed '' if (os.name == 'nt') and (colorama is None) else, due to IS_WINANSI variable and assoc. logic

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

## MS Windows-specific modules below

def _environ_cols_tput(*args):  # pragma: no cover
    """ cygwin xterm (windows) """
    try:
        import shlex, subprocess
        splitty = shlex.split('tput cols')
        cols = int(subprocess.check_call(splitty))
        # rows = int(subprocess.check_call(shlex.split('tput lines')))
        return cols
    except Exception:
        return None

def _environ_cols_windows(fp):  # pragma: no cover
    try:
        global_hn = _get_os_file_handle_num_windows(fp)
        (_, _, _, _, _, left, _, right, _, _, _) = _getIO_info_windows(global_hn)
        return right - left if not (left is None or right is None) else None
    # +1, but we don't want to put a character there or the cursor goes to the next line
    except Exception:
        return None

def _set_winansi_plus_handles():
    try:
        IS_WINANSI = False
        (cm_stdout, h_stdout, cm_stderr, h_stderr) = [None]*4 # used for resetting back to normal after execution if desired
        if IS_WIN: # ???? and not ((os.name == 'nt') and (colorama is None))
            from sys import getwindowsversion
            wv = getwindowsversion()
            # To check: if using ansicom instead of standard cmd shell, set IS_WINANSI to True
            # check also: what about DOSBOX? windows powershell?
            # specifics of checks below:
            # (wv[3] < 2) # windows 3.1 through 95/98/ME
            # (wv[0] < 5) or # windows NT 4.0 or earlier
            # (wv[0] == 5 and wv[1]<2): # windows 2000, XP (32 bit)
            if (wv[3] < 2) or (wv[0] < 5) or (wv[0] == 5 and wv[1]<2):
                IS_WINANSI = True
                # we should really do something to check if ANSI.sys is loaded and functional, but on these OSes it is at least available
                # should be tested on a 32-bit system w/o colorama (both in the NT and 9x series)
            else:
                # v[3] == 2 is NT series.
                # I'm not sure where winCE (wv[3]==3) falls along the ansi support continuum, so we may as well try to enable the console mode
#                import win32console
                h_stdout = win32console.GetStdHandle(-11) # stdout
                cm_stdout = h_stdout.GetConsoleMode()
                h_stderr = win32console.GetStdHandle(-12) # stderr
                cm_stderr = h_stderr.GetConsoleMode()
                if (cm_stdout | 0x04) > cm_stdout:
                    _set_console_mode_windows(h_stdout, cm_stdout | 4) # ENABLE_VIRTUAL_TERMINAL_PROCESSING
                if ((cm_stderr | 0x04) > cm_stderr) and (h_stderr.GetConsoleMode() == cm_stderr): # if it was altered by the above, we  don't really need to set it to that same value
                    _set_console_mode_windows(h_stderr, cm_stderr | 4)
                IS_WINANSI = True
    except (ImportError, _pywintypesErr):
        pass # (cm_stdout, h_stdout, cm_stderr, h_stderr) = [None]*4
    return (IS_WINANSI, ((cm_stdout, h_stdout), (cm_stderr, h_stderr)))

def _reset_mode_stdconsoles_windows(h_stdout = _h_stdout, cm_stdout = _cm_stdout, h_stderr = _h_stderr, cm_stderr = _cm_stderr): # pragma: no cover
    if cm_stderr != h_stderr.GetConsoleMode():
        _set_console_mode_windows(h_stderr, cm_stderr) # do in reverse order of initial set
    if cm_stdout != h_stdout.GetConsoleMode():
        _set_console_mode_windows(h_stdout, cm_stdout)

def _set_console_mode_windows(h_obj, cm): # pragma: no cover
    try:
        h_obj.SetConsoleMode(cm)
    except AttributeError: # h is probably None
        pass # swallow exception. Don't bother setting

def _getIO_info_windows(os_handle_num): # pragma: no cover
    """
    could alternately use e.g.
      sb = win32console.GetStdHandle(-11)
      sb.GetConsoleScreenBufferInfo() which returns key->values MaximumWindowSize[X, Y], CursorPosition[X, Y], Window[Left, Top, Right, Bottom], Attributes, Size[X, Y]
      sb.SetConsoleCursorPosition(win32console.PyCoordType(X,Y)) allows you to change the position

    returns (bufx, bufy, curx, cury, wattr, left, top, right, bottom, maxx, maxy)
    """
    try:
#        from ctypes import windll, create_string_buffer
        import struct
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(os_handle_num, csbi)
        return struct.unpack("hhhhHhhhhhh", csbi.raw) if res else None
    except Exception:
        raise # punt to next level
    return [None]*11

def _get_local_file_handle_num_windows(fp):
    try:
        if fp == stdin:
            std_hn = -10
        elif fp == stdout:
            std_hn = -11
        elif fp == stderr:
            std_hn = -12
        else:
            std_hn = fp.fileno() # file handle/descriptor number for the file within this program instance
    except Exception: # in any of the 4 imports or associated function calls
        std_hn = None
    return std_hn

def _get_os_file_handle_num_windows(fp): # pragma: no cover
    lcl = _get_local_file_handle_num_windows(fp)
    try:
        glob = windll.kernel32.GetStdHandle(lcl)
    except Exception:
        try:
            import msvcrt
            glob = msvcrt.get_osfhandle(fp.fileno()) # alternative: win32file._get_osfhandle(fp.fileno())
        except Exception:
            glob = None
    return glob

def _console_get_pos_windows(os_handle_num): # pragma: no cover
    try:
        (_, _, curx, cury, _, _, _, _, _, _, _) = _getIO_info_windows(os_handle_num) # would this be true for non-console/TTY?
        return cury*65536 + curx if not (curx is None or cury is None) else None
    except:
        pass
    return None

def _move_absolute_windows(fp, xy = None, x = None, y = None): # pragma: no cover
    global_hn = _get_os_file_handle_num_windows(fp)
    if global_hn:
        if xy is None:
            xy = y*65536 + x
        if y is None: # user probably used positional args and put x into xy and y into x
            xy = x*65536 + xy
        if xy is not None:
            suc = windll.kernel32.SetConsoleCursorPosition(global_hn, xy)
            return xy if suc else None
    return None

def _console_move_cursor_up_windows(fp, lines=0, cp=None, bol = False): # pragma: no cover
    try:
        global_hn = _get_os_file_handle_num_windows(fp)
        if cp is None and (not (global_hn is None)):
            cp = _console_get_pos_windows(global_hn)
        if not (cp is None):
            if not (cp >= 65536*lines):
                lines = cp // 65536
            if cp >= 0: # if at 0,0 this won't be attempted
                new_coords =  cp - (lines*65536) - (cp % 65536 if bol else 0) # or ((cp // 65536) - lines)*65536 + (0 if bol else cp % 65536)
                suc = windll.kernel32.SetConsoleCursorPosition(global_hn, new_coords)
                return new_coords if suc else cp # cp = failure to move. Consider raising an exception.
            else:
                return 0
    except Exception:
        return None
