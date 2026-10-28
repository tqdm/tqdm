"""
General helpers required for `tqdm.std`.
"""
import os
import re
import sys
from functools import partial, partialmethod, wraps
from inspect import signature
# TODO consider using wcswidth third-party package for 0-width characters
from unicodedata import east_asian_width
from warnings import warn
from weakref import proxy

_range, _unich, _unicode, _basestring = range, chr, str, str
CUR_OS = sys.platform
IS_WIN = any(CUR_OS.startswith(i) for i in ['win32', 'cygwin'])
IS_NIX = any(CUR_OS.startswith(i) for i in ['aix', 'linux', 'darwin', 'freebsd'])
RE_ANSI = re.compile(r"\x1b\[[;\d]*[A-Za-z]")
# Any ANSI escape sequence: CSI, OSC (BEL- or ST-terminated) and lone ESC sequences
RE_ESC = re.compile(
    r"\x1b\[[0-?]*[ -/]*[@-~]"  # CSI
    r"|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"  # OSC
    r"|\x1b[ -/]*[@-~]")  # other (Fe/Fs/Fp) escapes
# SGR (colour/attribute) sequences: the only escapes tqdm knowingly forwards
RE_SGR = re.compile(r"\x1b\[[0-9;:]*m")
# C0/C1 control characters except newline, tab and ESC (handled separately)
RE_CTRL = re.compile(r"[\x00-\x08\x0b-\x1a\x1c-\x1f\x7f-\x9f]")

try:
    if IS_WIN:
        import colorama
    else:
        raise ImportError
except ImportError:
    colorama = None
else:
    try:
        colorama.init(strip=False)
    except TypeError:
        colorama.init()


def envwrap(name, app="", types=None, is_method=False):
    """
    Basic (env-only) version of [envwrap](https://github.com/tqdm/envwrap).
    Install `envwrap` for config file support.
    """
    if types is None:
        types = {}
    if name[-1] == "_":
        name = name[:-1]
        warn("Trailing underscore in `name` is automatic", DeprecationWarning, stacklevel=2)
    prefixes = (name, f"{name}_{app}") if app else (name,)
    env_overrides = {}
    for prefix in prefixes:
        prefix = prefix.upper() + "_"
        i = len(prefix)
        env_overrides.update(
            (k[i:].lower(), v) for k, v in os.environ.items() if k.startswith(prefix))
    part = partialmethod if is_method else partial

    def wrap(func):
        params = signature(func).parameters
        # ignore unknown env vars
        overrides = {k: v for k, v in env_overrides.items() if k in params}
        # infer overrides' `type`s
        for k in overrides:
            param = params[k]
            if param.annotation is not param.empty:  # typehints
                for typ in getattr(param.annotation, '__args__', (param.annotation,)):
                    try:
                        overrides[k] = typ(overrides[k])
                    except Exception:  # nosec B110
                        pass
                    else:
                        break
            elif param.default is not None:  # type of default value
                overrides[k] = type(param.default)(overrides[k])
            else:
                try:  # `types` fallback
                    overrides[k] = types[k](overrides[k])
                except KeyError:  # keep unconverted (`str`)
                    pass
        return part(func, **overrides)
    return wrap


try:
    from envwrap import envwrap  # noqa: F401, F811, pylint: disable=unused-import
except ModuleNotFoundError:
    pass


class FormatReplace:
    """
    >>> a = FormatReplace('something')
    >>> f"{a:5d}"
    'something'
    """  # NOQA: P102
    def __init__(self, replace=''):
        self.replace = replace
        self.format_called = 0

    def __format__(self, _):
        self.format_called += 1
        return self.replace


class Comparable:
    """Assumes child has self._comparable attr/@property"""
    def __lt__(self, other):
        return self._comparable < other._comparable

    def __le__(self, other):
        return (self < other) or (self == other)

    def __eq__(self, other):
        return self._comparable == other._comparable

    def __ne__(self, other):
        return not self == other

    def __gt__(self, other):
        return not self <= other

    def __ge__(self, other):
        return not self < other


class ObjectWrapper:
    def __getattr__(self, name):
        return getattr(self._wrapped, name)

    def __setattr__(self, name, value):
        return setattr(self._wrapped, name, value)

    def wrapper_getattr(self, name):
        """Actual `self.getattr` rather than self._wrapped.getattr"""
        try:
            return object.__getattr__(self, name)
        except AttributeError:  # py2
            return getattr(self, name)

    def wrapper_setattr(self, name, value):
        """Actual `self.setattr` rather than self._wrapped.setattr"""
        return object.__setattr__(self, name, value)

    def __init__(self, wrapped):
        """
        Thin wrapper around a given object
        """
        self.wrapper_setattr('_wrapped', wrapped)


class SimpleTextIOWrapper(ObjectWrapper):
    """
    Change only `.write()` of the wrapped object by encoding the passed
    value and passing the result to the wrapped object's `.write()` method.
    """
    # pylint: disable=too-few-public-methods
    def __init__(self, wrapped, encoding):
        super().__init__(wrapped)
        self.wrapper_setattr('encoding', encoding)

    def write(self, s):
        """
        Encode `s` and pass to the wrapped object's `.write()` method.
        """
        return self._wrapped.write(s.encode(self.wrapper_getattr('encoding')))

    def __eq__(self, other):
        return self._wrapped == getattr(other, '_wrapped', other)


class DisableOnWriteError(ObjectWrapper):
    """
    Disable the given `tqdm_instance` upon `write()` or `flush()` errors.
    """
    @staticmethod
    def disable_on_exception(tqdm_instance, func):
        """
        Quietly set `tqdm_instance.miniters=inf` if `func` raises `errno=5`.
        """
        tqdm_instance = proxy(tqdm_instance)

        def inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except OSError as e:
                if e.errno != 5:
                    raise
                try:
                    tqdm_instance.miniters = float('inf')
                except ReferenceError:
                    pass
            except ValueError as e:
                if 'closed' not in str(e):
                    raise
                try:
                    tqdm_instance.miniters = float('inf')
                except ReferenceError:
                    pass
        return inner

    def __init__(self, wrapped, tqdm_instance):  # noqa: B042
        super().__init__(wrapped)
        if hasattr(wrapped, 'write'):
            self.wrapper_setattr(
                'write', self.disable_on_exception(tqdm_instance, wrapped.write))
        if hasattr(wrapped, 'flush'):
            self.wrapper_setattr(
                'flush', self.disable_on_exception(tqdm_instance, wrapped.flush))

    def __eq__(self, other):
        return self._wrapped == getattr(other, '_wrapped', other)


class CallbackIOWrapper(ObjectWrapper):
    def __init__(self, callback, stream, method="read"):
        """
        Wrap a given `file`-like object's `read()` or `write()` to report
        lengths to the given `callback`
        """
        super().__init__(stream)
        func = getattr(stream, method)
        if method == "write":
            @wraps(func)
            def write(data, *args, **kwargs):
                res = func(data, *args, **kwargs)
                callback(len(data))
                return res
            self.wrapper_setattr('write', write)
        elif method == "read":
            @wraps(func)
            def read(*args, **kwargs):
                data = func(*args, **kwargs)
                callback(len(data))
                return data
            self.wrapper_setattr('read', read)
        else:
            raise KeyError("Can only wrap read/write methods")


def _is_utf(encoding):
    try:
        '\u2588\u2589'.encode(encoding)
    except UnicodeEncodeError:
        return False
    except Exception:
        try:
            return encoding.lower().startswith('utf-') or ('U8' == encoding)
        except Exception:
            return False
    else:
        return True


def _supports_unicode(fp):
    try:
        return _is_utf(fp.encoding)
    except AttributeError:
        return False


def _is_ascii(s):
    if isinstance(s, str):
        for c in s:
            if ord(c) > 255:
                return False
        return True
    return _supports_unicode(s)


def _screen_shape_wrapper():  # pragma: no cover
    """
    Return a function which returns console dimensions (width, height).
    Supported: linux, osx, windows, cygwin.
    """
    def inner(fp):
        try:
            from os import get_terminal_size
            cols, lines = get_terminal_size(getattr(fp, 'fileno', lambda: None)())
            return cols - 1, lines - 1
        except Exception:
            return None, None

    return inner


def _environ_cols_wrapper():  # pragma: no cover
    """
    Return a function which returns console width.
    Supported: linux, osx, windows, cygwin.
    """
    warn("Use `_screen_shape_wrapper()(file)[0]` instead of"
         " `_environ_cols_wrapper()(file)`", DeprecationWarning, stacklevel=2)
    shape = _screen_shape_wrapper()
    if not shape:
        return None

    @wraps(shape)
    def inner(fp):
        return shape(fp)[0]

    return inner


def _term_move_up():  # pragma: no cover
    return '' if (os.name == 'nt') and (colorama is None) else '\x1b[A'


def _text_width(s):
    return sum(2 if east_asian_width(ch) in 'FW' else 1 for ch in str(s))


def disp_len(data):
    """
    Returns the real on-screen length of a string which may contain
    ANSI control codes and wide chars.
    """
    return _text_width(RE_ESC.sub('', data))


def _esc_tokens(data):
    """Yield `(text, is_escape)` chunks of `data`, escapes kept intact."""
    pos = 0
    for match in RE_ESC.finditer(data):
        if match.start() > pos:
            yield data[pos:match.start()], False
        yield match.group(), True
        pos = match.end()
    if pos < len(data):
        yield data[pos:], False


def disp_trim(data, length):
    """
    Trim a string which may contain ANSI control characters.
    """
    if len(data) == disp_len(data):
        return data[:length]

    length = max(0, length)
    res = []
    width = 0
    stopped = False
    for text, is_escape in _esc_tokens(data):
        if is_escape:
            # never cut a sequence in half: keep it, even past the limit
            res.append(text)
            continue
        if stopped:
            continue
        for char in text:
            char_width = 2 if east_asian_width(char) in 'FW' else 1
            if width + char_width > length:
                stopped = True
                break
            res.append(char)
            width += char_width
    trimmed = ''.join(res)
    if RE_SGR.search(trimmed) and not trimmed.endswith("\033[0m"):
        # assume ANSI reset is required
        trimmed += "\033[0m"
    return trimmed


def disp_escape(data):
    """
    Make untrusted text safe to send to a terminal.

    SGR (colour/attribute) sequences are forwarded unchanged so that coloured
    descriptions keep working; every other escape sequence and C0/C1 control
    character is rendered visually (`^[`, `^G`, ...) instead of being executed
    by the terminal. Newlines and tabs are preserved.
    """
    def _escape_ctrl(match):
        code = ord(match.group())
        if code == 0x7f:
            return '^?'
        if code < 0x20:
            return '^' + chr(code + 0x40)
        return f'\\x{code:02x}'  # C1 controls (0x80-0x9f)

    def _escape_text(text):
        return RE_CTRL.sub(_escape_ctrl, text).replace('\x1b', '^[')

    res = []
    for text, is_escape in _esc_tokens(data):
        if is_escape and RE_SGR.fullmatch(text):
            res.append(text)  # colour/attributes are honoured
        else:
            res.append(_escape_text(text))
    return ''.join(res)
