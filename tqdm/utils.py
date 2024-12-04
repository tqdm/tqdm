"""
General helpers required for `tqdm.std`.
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timedelta, timezone
from functools import wraps
from inspect import signature

# TODO consider using wcswidth third-party package for 0-width characters
from typing import IO, TYPE_CHECKING, Any, BinaryIO, Callable, TextIO, TypeVar, cast
from unicodedata import east_asian_width
from weakref import proxy

from typing_extensions import ParamSpec

if TYPE_CHECKING:
    from typing import Protocol

    from tqdm.std import tqdm

    class _FileEncoding(Protocol):
        encoding: str


CUR_OS = sys.platform
IS_WINDOWS = any(CUR_OS.startswith(i) for i in ["win32", "cygwin"])
IS_UNIX = any(CUR_OS.startswith(i) for i in ["aix", "linux", "darwin", "freebsd"])
RE_ANSI = re.compile(r"\x1b\[[;\d]*[A-Za-z]")

P = ParamSpec("P")
T = TypeVar("T")

try:
    if IS_WINDOWS:
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


def envwrap(
    prefix: str,
    fallback_types: dict[str, type[Any]] | None = None,
    is_method: bool = False,  # noqa: ARG001
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Override parameter defaults via `os.environ[prefix + param_name]`.
    Maps UPPER_CASE env vars map to lower_case param names.
    camelCase isn't supported (because Windows ignores case).

    Precedence (highest first):

    - call (`foo(a=3)`)
    - environ (`FOO_A=2`)
    - signature (`def foo(a=1)`)

    Parameters
    ----------
    prefix  : str
        Env var prefix, e.g. "FOO_"
    fallback_types  : dict, optional
        Fallback mappings `{'param_name': type, ...}` if types cannot be
        inferred from function signature.
    is_method  : bool, optional
        Deprecated: no longer use functools.parital

    Examples
    --------
    ```
    $ cat foo.py
    from tqdm.utils import envwrap
    @envwrap("FOO_")
    def test(a=1, b=2, c=3):
        print(f"received: a={a}, b={b}, c={c}")

    $ FOO_A=42 FOO_C=1337 python -c 'import foo; foo.test(c=99)'
    received: a=42, b=2, c=99
    ```
    """
    fallback_types = fallback_types or {}

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        sig = signature(func)

        @wraps(func)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            bound_args = sig.bind_partial(*args, **kwargs)
            for param_name, param in sig.parameters.items():
                if param_name in bound_args.arguments:
                    continue
                env_var = prefix + param_name.upper()
                try:
                    value = os.environ[env_var]
                except KeyError:
                    continue
                if param.annotation is not param.empty:  # typehints
                    for typ in getattr(param.annotation, "__args__", (param.annotation,)):
                        try:
                            value = typ(value)
                        except Exception:
                            pass
                        else:
                            break
                elif param.default is not param.empty and param.default is not None:
                    value = type(param.default)(value)
                else:
                    typ = fallback_types.get(param_name)
                    if typ is not None:
                        value = typ(value)
                bound_args.arguments[param_name] = value
            return func(*bound_args.args, **bound_args.kwargs)

        return wrapped

    return decorator


class FormatReplace:
    """
    >>> a = FormatReplace('something')
    >>> f"{a:5d}"
    'something'
    """  # NOQA: P102

    def __init__(self, replace: str = "") -> None:
        self.replace = replace
        self.format_called = 0

    def __format__(self, _: str) -> str:
        self.format_called += 1
        return self.replace


class Comparable:
    """Assumes child has self._comparable attr/@property"""

    _comparable: Any

    def __lt__(self, other: object) -> bool:
        return self._comparable < other._comparable  # type: ignore

    def __le__(self, other: object) -> bool:
        return (self < other) or (self == other)

    def __eq__(self, other: object) -> bool:
        return self._comparable == other._comparable  # type: ignore

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __gt__(self, other: object) -> bool:
        return not self <= other

    def __ge__(self, other: object) -> bool:
        return not self < other


class SimpleTextIOWrapper:
    """
    Change only `.write()` of the wrapped object by encoding the passed
    value and passing the result to the wrapped object's `.write()` method.
    """

    def __init__(self, wrapped: BinaryIO, encoding: str):
        self._wrapped = wrapped
        self._encoding = encoding

    def write(self, s: str, /) -> int:
        """
        Encode `s` and pass to the wrapped object's `.write()` method.
        """
        return self._wrapped.write(s.encode(self._encoding))

    def flush(self) -> None:
        try:
            self._wrapped.flush()
        except Exception:
            pass

    def __eq__(self, other: object) -> bool:
        return self._wrapped == getattr(other, "_wrapped", other)


class DisableOnWriteError:
    """
    Disable the given `tqdm_instance` upon `write()` or `flush()` errors.
    """

    def __init__(self, wrapped: IO[Any], tqdm_instance: tqdm):
        self._wrapped = wrapped
        self._instance = proxy(tqdm_instance)

    def write(self, s: Any, /) -> int | None:
        try:
            return self._wrapped.write(s)
        except OSError as e:
            if e.errno != 5:
                raise
            try:
                self._instance.miniters = float("inf")
            except ReferenceError:
                pass
        except ValueError as e:
            if "closed" not in str(e):
                raise
            try:
                self._instance.miniters = float("inf")
            except ReferenceError:
                pass

    def flush(self) -> None:
        try:
            self._wrapped.flush()
        except OSError as e:
            if e.errno != 5:
                raise
            try:
                self._instance.miniters = float("inf")
            except ReferenceError:
                pass
        except ValueError as e:
            if "closed" not in str(e):
                raise
            try:
                self._instance.miniters = float("inf")
            except ReferenceError:
                pass

    def __eq__(self, other: object) -> bool:
        return self._wrapped == getattr(other, "_wrapped", other)


class CallbackWriteIOWrapper:
    """
    Wrap a given `file`-like object's `write()` to report
    lengths to the given `callback`
    """

    def __init__(
        self,
        callback: Callable[[int], object],
        stream: IO[Any],
    ) -> None:
        self.callback = callback
        self.stream = stream

    def write(self, s: Any, /) -> int:
        out = self.stream.write(s)
        self.callback(out)
        return out


class CallbackReadIOWrapper:
    """
    Wrap a given `file`-like object's `read()` to report
    lengths to the given `callback`
    """

    def __init__(
        self,
        callback: Callable[[int], object],
        stream: IO[Any],
    ) -> None:
        self.callback = callback
        self.stream = stream

    def read(self, s: Any, /) -> int:
        blob = self.stream.read(s)
        self.callback(len(blob))
        return blob


def _is_utf(encoding: str) -> bool:
    try:
        "\u2588\u2589".encode(encoding)
    except UnicodeEncodeError:
        return False
    except Exception:
        try:
            return encoding.lower().startswith("utf-") or (encoding == "U8")
        except Exception:
            return False
    else:
        return True


def supports_unicode(fp: _FileEncoding) -> bool:
    try:
        return _is_utf(fp.encoding)
    except AttributeError:
        return False


def is_ascii(s: str | _FileEncoding) -> bool:
    if isinstance(s, str):
        return all(ord(c) <= 255 for c in s)
    return supports_unicode(s)


def screen_shape_wrapper() -> (
    Callable[[int], tuple[int | None, int | None]] | None
):  # pragma: no cover # noqa
    """
    Return a function which returns console dimensions (width, height).
    Supported: linux, osx, windows, cygwin.
    """
    _screen_shape = None
    if IS_WINDOWS:
        _screen_shape = _screen_shape_windows
        if _screen_shape is None:
            _screen_shape = _screen_shape_tput
    if IS_UNIX:
        _screen_shape = _screen_shape_linux
    return _screen_shape


def _screen_shape_windows(fp: int) -> tuple[int | None, int | None]:  # pragma: no cover # noqa
    try:
        import struct
        from ctypes import create_string_buffer, windll
        from sys import stdin, stdout

        io_handle = -12  # assume stderr
        if fp == stdin:
            io_handle = -10
        elif fp == stdout:
            io_handle = -11

        h = windll.kernel32.GetStdHandle(io_handle)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
        if res:
            (_bufx, _bufy, _curx, _cury, _wattr, left, top, right, bottom, _maxx, _maxy) = (
                struct.unpack("hhhhHhhhhhh", csbi.raw)
            )
            return right - left, bottom - top  # +1
    except Exception:  # nosec
        pass
    return None, None


def _screen_shape_tput(*_: Any) -> tuple[int | None, int | None]:  # pragma: no cover # noqa
    """cygwin xterm (windows)"""
    try:
        import shlex
        from subprocess import check_call  # nosec

        return cast(
            tuple[int, int],
            tuple(int(check_call(shlex.split("tput " + i))) - 1 for i in ("cols", "lines")),
        )
    except Exception:  # nosec
        pass
    return None, None


def _screen_shape_linux(fp: int) -> tuple[int | None, int | None]:  # pragma: no cover
    if os.name == "nt":
        return None, None
    try:
        from array import array
        from fcntl import ioctl
        from termios import TIOCGWINSZ
    except ImportError:
        return None, None
    else:
        try:
            rows, cols = array("h", ioctl(fp, TIOCGWINSZ, "\0" * 8))[:2]
            return cols, rows
        except Exception:
            try:
                return tuple(int(os.environ[i]) - 1 for i in ("COLUMNS", "LINES"))
            except (KeyError, ValueError):
                return None, None


def _term_move_up() -> str:  # type: ignore # pragma: no cover
    return "" if (os.name == "nt") and (colorama is None) else "\x1b[A"


def _text_width(s: str) -> int:
    return sum(2 if east_asian_width(ch) in "FW" else 1 for ch in str(s))


def disp_len(data: str) -> int:
    """
    Returns the real on-screen length of a string which may contain
    ANSI control codes and wide chars.
    """
    return _text_width(RE_ANSI.sub("", data))


def disp_trim(data: str, length: int) -> str:
    """
    Trim a string which may contain ANSI control characters.
    """
    if len(data) == disp_len(data):
        return data[:length]

    ansi_present = bool(RE_ANSI.search(data))
    while disp_len(data) > length:  # carefully delete one char at a time
        data = data[:-1]
    if ansi_present and bool(RE_ANSI.search(data)):
        # assume ANSI reset is required
        return data if data.endswith("\033[0m") else data + "\033[0m"
    return data


def format_sizeof(num: float, suffix: str = "", divisor: int = 1000) -> str:
    """
    Formats a number (greater than unity) with SI Order of Magnitude
    prefixes.

    Parameters
    ----------
    num  : float
        Number ( >= 1) to format.
    suffix  : str, optional
        Post-postfix [default: ''].
    divisor  : float, optional
        Divisor between prefixes [default: 1000].

    Returns
    -------
    out  : str
        Number with Order of Magnitude SI unit postfix.
    """
    for unit in ["", "k", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 999.5:
            if abs(num) < 99.95:
                if abs(num) < 9.995:
                    return f"{num:1.2f}{unit}{suffix}"
                return f"{num:2.1f}{unit}{suffix}"
            return f"{num:3.0f}{unit}{suffix}"
        num /= divisor
    return f"{num:3.1f}Y{suffix}"


def format_interval(t: float) -> str:
    """
    Formats a number of seconds as a clock time, [H:]MM:SS

    Parameters
    ----------
    t  : float
        Number of seconds.

    Returns
    -------
    out  : str
        [H:]MM:SS
    """
    mins, s = divmod(int(t), 60)
    h, m = divmod(mins, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def format_num(n: int | float) -> str:
    """
    Intelligent scientific notation (.3g).

    Parameters
    ----------
    n  : int or float or Numeric
        A Number.

    Returns
    -------
    out  : str
        Formatted number.
    """
    f = f"{n:.3g}".replace("e+0", "e+").replace("e-0", "e-")
    ns = str(n)
    return f if len(f) < len(ns) else ns


@staticmethod
def status_printer(file: TextIO) -> Callable[[str], None]:
    """
    Manage the printing and in-place updating of a line of characters.
    Note that if the string is longer than a line, then in-place
    updating may not work (it will print a new line at each refresh).
    """
    fp = file
    fp_flush = getattr(fp, "flush", lambda: None)  # pragma: no cover
    if fp in (sys.stderr, sys.stdout):
        getattr(sys.stderr, "flush", lambda: None)()
        getattr(sys.stdout, "flush", lambda: None)()

    def fp_write(s: str) -> None:
        fp.write(str(s))
        fp_flush()

    last_len = [0]

    def print_status(s: str) -> None:
        len_s = disp_len(s)
        fp_write("\r" + s + (" " * max(last_len[0] - len_s, 0)))
        last_len[0] = len_s

    return print_status


def format_meter(
    n: int | float,
    total: int | float | None,
    elapsed: float,
    ncols: int | None = None,
    prefix: str = "",
    ascii: str | bool = False,
    unit: str = "it",
    unit_scale: bool | int | float = False,
    rate: float | None = None,
    bar_format: str | None = None,
    postfix: str | Any | None = None,
    unit_divisor: int = 1000,
    initial: int | float = 0,
    colour: str | None = None,
    **extra_kwargs: Any,
) -> str:
    """
    Return a string-based progress bar given some parameters

    Parameters
    ----------
    n  : int or float
        Number of finished iterations.
    total  : int or float
        The expected total number of iterations. If meaningless (None),
        only basic progress statistics are displayed (no ETA).
    elapsed  : float
        Number of seconds passed since start.
    ncols  : int, optional
        The width of the entire output message. If specified,
        dynamically resizes `{bar}` to stay within this bound
        [default: None]. If `0`, will not print any bar (only stats).
        The fallback is `{bar:10}`.
    prefix  : str, optional
        Prefix message (included in total width) [default: ''].
        Use as {desc} in bar_format string.
    ascii  : bool, optional or str, optional
        If not set, use unicode (smooth blocks) to fill the meter
        [default: False]. The fallback is to use ASCII characters
        " 123456789#".
    unit  : str, optional
        The iteration unit [default: 'it'].
    unit_scale  : bool or int or float, optional
        If 1 or True, the number of iterations will be printed with an
        appropriate SI metric prefix (k = 10^3, M = 10^6, etc.)
        [default: False]. If any other non-zero number, will scale
        `total` and `n`.
    rate  : float, optional
        Manual override for iteration rate.
        If [default: None], uses n/elapsed.
    bar_format  : str, optional
        Specify a custom bar string formatting. May impact performance.
        [default: '{l_bar}{bar}{r_bar}'], where
        l_bar='{desc}: {percentage:3.0f}%|' and
        r_bar='| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, '
            '{rate_fmt}{postfix}]'
        Possible vars: l_bar, bar, r_bar, n, n_fmt, total, total_fmt,
            percentage, elapsed, elapsed_s, ncols, nrows, desc, unit,
            rate, rate_fmt, rate_noinv, rate_noinv_fmt,
            rate_inv, rate_inv_fmt, postfix, unit_divisor,
            remaining, remaining_s, eta.
        Note that a trailing ": " is automatically removed after {desc}
        if the latter is empty.
    postfix  : *, optional
        Similar to `prefix`, but placed at the end
        (e.g. for additional stats).
        Note: postfix is usually a string (not a dict) for this method,
        and will if possible be set to postfix = ', ' + postfix.
        However other types are supported (#382).
    unit_divisor  : float, optional
        [default: 1000], ignored unless `unit_scale` is True.
    initial  : int or float, optional
        The initial counter value [default: 0].
    colour  : str, optional
        Bar colour (e.g. 'green', '#00ff00').

    Returns
    -------
    out  : Formatted meter and stats, ready to display.
    """

    from tqdm.std import Bar  # lazy import

    # sanity check: total
    if total and n >= (total + 0.5):  # allow float imprecision (#849)
        total = None

    # apply custom scale if necessary
    if unit_scale and unit_scale not in (True, 1):
        if total:
            total *= unit_scale
        n *= unit_scale
        if rate:
            rate *= unit_scale  # by default rate = self.avg_dn / self.avg_dt
        unit_scale = False

    elapsed_str = format_interval(elapsed)

    # if unspecified, attempt to use rate = average speed
    # (we allow manual override since predicting time is an arcane art)
    if rate is None and elapsed:
        rate = (n - initial) / elapsed
    inv_rate = 1 / rate if rate else None
    rate_noinv_fmt = (
        ((format_sizeof(rate) if unit_scale else f"{rate:5.2f}") if rate else "?") + unit + "/s"
    )
    rate_inv_fmt = (
        ((format_sizeof(inv_rate) if unit_scale else f"{inv_rate:5.2f}") if inv_rate else "?")
        + "s/"
        + unit
    )
    rate_fmt = rate_inv_fmt if inv_rate and inv_rate > 1 else rate_noinv_fmt

    if unit_scale:
        n_fmt = format_sizeof(n, divisor=unit_divisor)
        total_fmt = format_sizeof(total, divisor=unit_divisor) if total is not None else "?"
    else:
        n_fmt = str(n)
        total_fmt = str(total) if total is not None else "?"

    try:
        postfix = ", " + postfix if postfix else ""
    except TypeError:
        pass

    remaining = (total - n) / rate if rate and total else 0
    remaining_str = format_interval(remaining) if rate else "?"
    try:
        eta_dt = (
            datetime.now() + timedelta(seconds=remaining)
            if rate and total
            else datetime.fromtimestamp(0, timezone.utc)
        )
    except OverflowError:
        eta_dt = datetime.max

    # format the stats displayed to the left and right sides of the bar
    if prefix:
        # old prefix setup work around
        bool_prefix_colon_already = prefix[-2:] == ": "
        l_bar = prefix if bool_prefix_colon_already else prefix + ": "
    else:
        l_bar = ""

    r_bar = f"| {n_fmt}/{total_fmt} [{elapsed_str}<{remaining_str}, {rate_fmt}{postfix}]"

    # Custom bar formatting
    # Populate a dict with all available progress indicators
    format_dict = {
        # slight extension of self.format_dict
        "n": n,
        "n_fmt": n_fmt,
        "total": total,
        "total_fmt": total_fmt,
        "elapsed": elapsed_str,
        "elapsed_s": elapsed,
        "ncols": ncols,
        "desc": prefix or "",
        "unit": unit,
        "rate": inv_rate if inv_rate and inv_rate > 1 else rate,
        "rate_fmt": rate_fmt,
        "rate_noinv": rate,
        "rate_noinv_fmt": rate_noinv_fmt,
        "rate_inv": inv_rate,
        "rate_inv_fmt": rate_inv_fmt,
        "postfix": postfix,
        "unit_divisor": unit_divisor,
        "colour": colour,
        # plus more useful definitions
        "remaining": remaining_str,
        "remaining_s": remaining,
        "l_bar": l_bar,
        "r_bar": r_bar,
        "eta": eta_dt,
        **extra_kwargs,
    }

    # total is known: we can predict some stats
    if total:
        # fractional and percentage progress
        frac = n / total
        percentage = frac * 100

        l_bar += f"{percentage:3.0f}%|"

        if ncols == 0:
            return l_bar[:-1] + r_bar[1:]

        format_dict.update(l_bar=l_bar)
        if bar_format:
            format_dict.update(percentage=percentage)

            # auto-remove colon for empty `{desc}`
            if not prefix:
                bar_format = bar_format.replace("{desc}: ", "")
        else:
            bar_format = "{l_bar}{bar}{r_bar}"

        full_bar = FormatReplace()
        nobar = bar_format.format(bar=full_bar, **format_dict)
        if not full_bar.format_called:
            return nobar  # no `{bar}`; nothing else to do

        # Formatting progress bar space available for bar's display
        full_bar = Bar(
            frac,
            max(1, ncols - disp_len(nobar)) if ncols else 10,
            charset=Bar.ASCII if ascii is True else ascii or Bar.UTF,
            colour=colour,
        )
        if not is_ascii(full_bar.charset) and is_ascii(bar_format):
            bar_format = str(bar_format)
        res = bar_format.format(bar=full_bar, **format_dict)
        return disp_trim(res, ncols) if ncols else res

    elif bar_format:
        # user-specified bar_format but no total
        l_bar += "|"
        format_dict.update(l_bar=l_bar, percentage=0)
        full_bar = FormatReplace()
        nobar = bar_format.format(bar=full_bar, **format_dict)
        if not full_bar.format_called:
            return nobar
        full_bar = Bar(
            0, max(1, ncols - disp_len(nobar)) if ncols else 10, charset=Bar.BLANK, colour=colour
        )
        res = bar_format.format(bar=full_bar, **format_dict)
        return disp_trim(res, ncols) if ncols else res
    else:
        # no total: no progressbar, ETA, just progress stats
        return (
            f'{(prefix + ": ") if prefix else ""}'
            f'{n_fmt}{unit} [{elapsed_str}, {rate_fmt}{postfix}]'
        )
