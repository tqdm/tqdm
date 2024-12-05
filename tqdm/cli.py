"""
Module version for monitoring CLI pipes (`... | python -m tqdm | ...`).
"""

from __future__ import annotations

import logging
import re
import sys
from ast import literal_eval as numeric
from pathlib import Path
from textwrap import indent
from typing import TYPE_CHECKING, Any, Callable, TextIO, overload

import importlib_resources as resources

from .std import TqdmKeyError, TqdmTypeError, tqdm
from .version import __version__

if TYPE_CHECKING:
    from typing import TypeVar, Union

    from _typeshed import SupportsFlush, SupportsRead, SupportsWrite
    from typing_extensions import TypeAlias

    _T_contra = TypeVar("_T_contra", contravariant=True)

    class _SupportsWriteAndFlush(SupportsWrite[_T_contra], SupportsFlush): ...

    WriteableAnyStr: TypeAlias = Union[SupportsWrite[str], SupportsWrite[bytes]]
    WriteableAndFlushableStrAny: TypeAlias = Union[
        _SupportsWriteAndFlush[str], _SupportsWriteAndFlush[bytes]
    ]
    Readable: TypeAlias = SupportsRead[Any]


class WriteableNullFile:
    def write(self, _: str, /) -> int:
        return len(_)


class TqdmExternalWriting:
    def __init__(self, stdout: SupportsWrite[str], fp: SupportsWrite[str]):
        self._stdout = stdout
        self._fp = fp

    def write(self, _: str, /) -> int:
        with tqdm.external_write_mode(file=self._fp):
            self._fp.write(_)
        self._stdout.write(_)
        return len(_)


__all__ = ["main"]
log = logging.getLogger(__name__)


def cast(val: Any, typ: Any) -> Any:
    log.debug((val, typ))
    if " or " in typ:
        for t in typ.split(" or "):
            try:
                return cast(val, t)
            except TqdmTypeError:
                pass
        raise TqdmTypeError(f"{val} : {typ}")

    # sys.stderr.write('\ndebug | `val:type`: `' + val + ':' + typ + '`.\n')
    if typ == "bool":
        if val in ("True", ""):
            return True
        if val == "False":
            return False
        raise TqdmTypeError(val + " : " + typ)
    if typ == "chr":
        if len(val) == 1:
            return val.encode()
        if re.match(r"^\\\w+$", val):
            return eval(f'"{val}"').encode()
        raise TqdmTypeError(f"{val} : {typ}")
    if typ == "str":
        return val
    if typ == "int":
        try:
            return int(val)
        except ValueError as exc:
            raise TqdmTypeError(f"{val} : {typ}") from exc
    if typ == "float":
        try:
            return float(val)
        except ValueError as exc:
            raise TqdmTypeError(f"{val} : {typ}") from exc
    raise TqdmTypeError(f"{val} : {typ}")


@overload
def posix_pipe(
    fin: Readable,
    fout: WriteableAnyStr | WriteableAndFlushableStrAny,
    delim: str | bytes = b"\\n",
    buf_size: int = 256,
    callback: Callable[[int], object] = (lambda _: None),
    callback_len: bool = True,
) -> None: ...


@overload
def posix_pipe(
    fin: Readable,
    fout: WriteableAnyStr | WriteableAndFlushableStrAny,
    delim: str | bytes = b"\\n",
    buf_size: int = 256,
    callback: Callable[[bytes], object] = (lambda _: None),
    callback_len: bool = False,
) -> None: ...


def posix_pipe(
    fin: Readable,
    fout: WriteableAnyStr | WriteableAndFlushableStrAny,
    delim: str | bytes = b"\\n",
    buf_size: int = 256,
    callback: Callable[[Any], object] = (lambda _: None),
    callback_len: bool = True,
) -> None:
    """
    Params
    ------
    fin  : file with `read(buf_size : int)` method
    fout  : file with `write` (and optionally `flush`) methods.
    callback  : function(float), e.g.: `tqdm.update`
    callback_len  : If (default: True) do `callback(len(buffer))`.
      Otherwise, do `callback(data) for data in buffer.split(delim)`.
    """
    fp_write = fout.write

    if not delim:
        while True:
            tmp = fin.read(buf_size)

            # flush at EOF
            if not tmp:
                getattr(fout, "flush", lambda: None)()
                return

            fp_write(tmp)
            callback(len(tmp))
        # return

    buf = b""
    len_delim = len(delim)
    # n = 0
    while True:
        tmp = fin.read(buf_size)

        # flush at EOF
        if not tmp:
            if buf:
                fp_write(buf)
                if callback_len:
                    # n += 1 + buf.count(delim)
                    callback(1 + buf.count(delim))
                else:
                    for i in buf.split(delim):
                        callback(i)
            getattr(fout, "flush", lambda: None)()
            return  # n

        while True:
            i = tmp.find(delim)
            if i < 0:
                buf += tmp
                break
            fp_write(buf + tmp[: i + len(delim)])
            # n += 1
            callback(1 if callback_len else (buf + tmp[:i]))
            buf = b""
            tmp = tmp[i + len_delim :]


# ((opt, type), ... )
RE_OPTS = re.compile(r"\n {4}(\S+)\s{2,}:\s*([^,]+)")
# better split method assuming no positional args
RE_SHLEX = re.compile(r"\s*(?<!\S)--?([^\s=]+)(\s+|=|$)")

# TODO: add custom support for some of the following?
UNSUPPORTED_OPTS = ("iterable", "gui", "out", "file")

# The 8 leading spaces are required for consistency
CLI_EXTRA_DOC = r"""
    Extra CLI Options
    -----------------
    name  : type, optional
        TODO: find out why this is needed.
    delim  : chr, optional
        Delimiting character [default: '\n']. Use '\0' for null.
        N.B.: on Windows systems, Python converts '\n' to '\r\n'.
    buf_size  : int, optional
        String buffer size in bytes [default: 256]
        used when `delim` is specified.
    bytes  : bool, optional
        If true, will count bytes, ignore `delim`, and default
        `unit_scale` to True, `unit_divisor` to 1024, and `unit` to 'B'.
    tee  : bool, optional
        If true, passes `stdin` to both `stderr` and `stdout`.
    update  : bool, optional
        If true, will treat input as newly elapsed iterations,
        i.e. numbers to pass to `update()`. Note that this is slow
        (~2e5 it/s) since every input must be decoded as a number.
    update_to  : bool, optional
        If true, will treat input as total elapsed iterations,
        i.e. numbers to assign to `self.n`. Note that this is slow
        (~2e5 it/s) since every input must be decoded as a number.
    null  : bool, optional
        If true, will discard input (no stdout).
    manpath  : str, optional
        Directory in which to install tqdm man pages.
    comppath  : str, optional
        Directory in which to place tqdm completion.
    log  : str, optional
        CRITICAL|FATAL|ERROR|WARN(ING)|[default: 'INFO']|DEBUG|NOTSET.
"""


def main(fp: TextIO = sys.stderr, argv: list[str] | None = None) -> None:
    """
    Parameters (internal use only)
    ---------
    fp  : file-like object for tqdm
    argv  : list (default: sys.argv[1:])
    """
    if argv is None:
        argv = sys.argv[1:]
    try:
        log_idx = argv.index("--log")
    except ValueError:
        for i in argv:
            if i.startswith("--log="):
                logLevel = i[len("--log=") :]
                break
        else:
            logLevel = "INFO"
    else:
        # argv.pop(log_idx)
        # logLevel = argv.pop(log_idx)
        logLevel = argv[log_idx + 1]
    logging.basicConfig(
        level=getattr(logging, logLevel), format="%(levelname)s:%(module)s:%(lineno)d:%(message)s"
    )

    tqdm_doc = tqdm.__doc__ or ""

    # py<3.13 doesn't dedent docstrings
    full_doc = (
        tqdm_doc if sys.version_info < (3, 13) else indent(tqdm_doc, "    ")
    ) + CLI_EXTRA_DOC

    opt_types = dict(RE_OPTS.findall(full_doc))
    # opt_types['delim'] = 'chr'

    for o in UNSUPPORTED_OPTS:
        opt_types.pop(o)

    log.debug(sorted(opt_types.items()))

    # d = RE_OPTS.sub(r'  --\1=<\1>  : \2', d)
    split = RE_OPTS.split(full_doc)
    opt_types_desc = zip(split[1::3], split[2::3], split[3::3])
    full_doc = "".join(
        ("\n  --{0}  : {2}{3}" if otd[1] == "bool" else "\n  --{0}=<{1}>  : {2}{3}").format(
            otd[0].replace("_", "-"), otd[0], *otd[1:]
        )
        for otd in opt_types_desc
        if otd[0] not in UNSUPPORTED_OPTS
    )

    help_short = "Usage:\n  tqdm [--help | options]\n"
    full_doc = (
        help_short
        + """
Options:
  -h, --help     Print this help and exit.
  -v, --version  Print version and exit.
"""
        + full_doc.strip("\n")
        + "\n"
    )

    # opts = docopt(d, version=__version__)
    if any(v in argv for v in ("-v", "--version")):
        sys.stdout.write(__version__ + "\n")
        sys.exit(0)
    elif any(v in argv for v in ("-h", "--help")):
        sys.stdout.write(full_doc + "\n")
        sys.exit(0)
    elif argv and argv[0][:2] != "--":
        sys.stderr.write(f"Error: Unknown argument: {argv[0]}\n{help_short}")

    argv = RE_SHLEX.split(" ".join(["tqdm"] + argv))
    opts = dict(zip(argv[1::3], argv[3::3]))

    log.debug(opts)
    opts.pop("log", True)

    tqdm_args: dict[str, Any] = {"file": fp}
    try:
        for o, v in opts.items():
            o = o.replace("-", "_")  # noqa: PLW2901
            try:
                tqdm_args[o] = cast(v, opt_types[o])
            except KeyError as e:
                raise TqdmKeyError(str(e)) from None
        log.debug("args:" + str(tqdm_args))

        delim_per_char = tqdm_args.pop("bytes", False)
        update = tqdm_args.pop("update", False)
        update_to = tqdm_args.pop("update_to", False)
        if sum((delim_per_char, update, update_to)) > 1:
            raise TqdmKeyError("Can only have one of --bytes --update --update_to")
    except Exception:
        fp.write("\nError:\n" + help_short)
        stdin, stdout_write = sys.stdin, sys.stdout.write
        for i in stdin:
            stdout_write(i)
        raise

    buf_size = tqdm_args.pop("buf_size", 256)
    delim = tqdm_args.pop("delim", b"\\n")
    tee = tqdm_args.pop("tee", False)
    manpath = tqdm_args.pop("manpath", None)
    comppath = tqdm_args.pop("comppath", None)
    disable_output = tqdm_args.pop("null", False)

    if disable_output:
        stdout = WriteableNullFile()
    else:
        stdout = sys.stdout
        stdout = getattr(stdout, "buffer", stdout)

    stdin = getattr(sys.stdin, "buffer", sys.stdin)
    if manpath or comppath:

        def cp(name: str, dst: Path):
            """copy resource `name` to `dst`"""
            fi = resources.files("tqdm") / name
            dst.write_bytes(fi.read_bytes())
            log.info("written:%s", dst)

        if manpath is not None:
            cp("tqdm.1", Path(manpath) / "tqdm.1")
        if comppath is not None:
            cp("completion.sh", Path(comppath) / "tqdm_completion.sh")
        sys.exit(0)

    if tee:
        fp = getattr(fp, "buffer", fp)
        stdout = TqdmExternalWriting(stdout, fp)

    if delim_per_char:
        tqdm_args.setdefault("unit", "B")
        tqdm_args.setdefault("unit_scale", True)
        tqdm_args.setdefault("unit_divisor", 1024)
        log.debug(tqdm_args)
        with tqdm(**tqdm_args) as t:
            posix_pipe(stdin, stdout, "", buf_size, t.update, callback_len=True)
    elif delim == b"\\n":
        log.debug(tqdm_args)
        write = stdout.write
        if update or update_to:
            with tqdm(**tqdm_args) as t:

                def callback(i: str | bytes):
                    if isinstance(i, bytes):
                        i = i.decode()
                    if update:
                        t.update(numeric(i))
                    else:
                        t.update(numeric(i) - t.n)

                for i in stdin:
                    write(i)
                    callback(i)
        else:
            for i in tqdm(stdin, **tqdm_args):  # type: ignore
                write(i)  # type: ignore
    else:
        log.debug(tqdm_args)
        with tqdm(**tqdm_args) as t:
            callback_len = False
            if update:

                def callback(i: str | bytes):
                    if isinstance(i, bytes):
                        i = i.decode()
                    t.update(numeric(i))
            elif update_to:

                def callback(i: str | bytes):
                    if isinstance(i, bytes):
                        i = i.decode()
                    t.update(numeric(i) - t.n)
            else:
                callback = t.update  # type: ignore
                callback_len = True
            posix_pipe(stdin, stdout, delim, buf_size, callback, callback_len)
