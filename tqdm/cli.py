"""
Module version for monitoring CLI pipes (`... | python -m tqdm | ...`).
"""
from .std import tqdm, TqdmTypeError, TqdmKeyError
from ._version import __version__  # NOQA
import sys
import re
import logging
__all__ = ["main"]


def cast(val, typ):
    log = logging.getLogger(__name__)
    log.debug((val, typ))
    if " or " in typ:
        for t in typ.split(" or "):
            try:
                return cast(val, t)
            except TqdmTypeError:
                pass
        raise TqdmTypeError(val + ' : ' + typ)

    # sys.stderr.write('\ndebug | `val:type`: `' + val + ':' + typ + '`.\n')
    if typ == 'bool':
        if (val == 'True') or (val == ''):
            return True
        elif val == 'False':
            return False
        else:
            raise TqdmTypeError(val + ' : ' + typ)
    try:
        return eval(typ + '("' + val + '")')
    except:
        if typ == 'chr':
            return chr(ord(eval('"' + val + '"'))).encode()
        else:
            raise TqdmTypeError(val + ' : ' + typ)


def isBytes(val):
    """Equivalent of `isinstance(val, six.binary_type)`."""
    try:
        val.index(b'')
    except TypeError:
        return False
    return True


def posix_pipe(fin, fout, delim=b'\\n', buf_size=256,
               callback=lambda int: None  # pragma: no cover
               ):
    """
    Params
    ------
    fin  : file with `read(buf_size : int)` method
    fout  : file with `write` (and optionally `flush`) methods.
    callback  : function(int), e.g.: `tqdm.update`
    """
    fp_write = fout.write

    # tmp = b''
    if not delim:
        while True:
            tmp = fin.read(buf_size)

            # flush at EOF
            if not tmp:
                getattr(fout, 'flush', lambda: None)()  # pragma: no cover
                return

            fp_write(tmp)
            callback(len(tmp))
        # return

    buf = b''
    check_bytes = True
    write_bytes = True
    # n = 0
    while True:
        tmp = fin.read(buf_size)

        if check_bytes:  # first time; check encoding
            check_bytes = False
            if not isBytes(tmp):
                # currently only triggered by `tests_main.py`.
                # TODO: mock stdin/out better so that this isn't needed
                write_bytes = False
                delim = delim.decode()
                buf = buf.decode()

        # flush at EOF
        if not tmp:
            if buf:
                fp_write(buf)
                callback(1 + buf.count(delim))  # n += 1 + buf.count(delim)
            getattr(fout, 'flush', lambda: None)()  # pragma: no cover
            return  # n

        while True:
            try:
                i = tmp.index(delim)
            except ValueError:
                buf += tmp
                break
            else:
                fp_write(buf + tmp[:i + len(delim)])
                callback(1)  # n += 1
                buf = b'' if write_bytes else ''
                tmp = tmp[i + len(delim):]


# ((opt, type), ... )
RE_OPTS = re.compile(r'\n {8}(\S+)\s{2,}:\s*([^,]+)')
# better split method assuming no positional args
RE_SHLEX = re.compile(r'\s*(?<!\S)--?([^\s=]+)(\s+|=|$)')

# TODO: add custom support for some of the following?
UNSUPPORTED_OPTS = ('iterable', 'gui', 'out', 'file')

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
        manpath  : str, optional
            Directory in which to install tqdm man pages.
        comppath  : str, optional
            Directory in which to place tqdm completion.
        log  : str, optional
            CRITICAL|FATAL|ERROR|WARN(ING)|[default: 'INFO']|DEBUG|NOTSET.
"""


def main(fp=sys.stderr, argv=None):
    """
    Parameters (internal use only)
    ---------
    fp  : file-like object for tqdm
    argv  : list (default: sys.argv[1:])
    """
    if argv is None:
        argv = sys.argv[1:]
    try:
        log = argv.index('--log')
    except ValueError:
        for i in argv:
            if i.startswith('--log='):
                logLevel = i[len('--log='):]
                break
        else:
            logLevel = 'INFO'
    else:
        # argv.pop(log)
        # logLevel = argv.pop(log)
        logLevel = argv[log + 1]
    logging.basicConfig(
        level=getattr(logging, logLevel),
        format="%(levelname)s:%(module)s:%(lineno)d:%(message)s")
    log = logging.getLogger(__name__)

    d = tqdm.__init__.__doc__ + CLI_EXTRA_DOC

    opt_types = dict(RE_OPTS.findall(d))
    # opt_types['delim'] = 'chr'

    for o in UNSUPPORTED_OPTS:
        opt_types.pop(o)

    log.debug(sorted(opt_types.items()))

    # d = RE_OPTS.sub(r'  --\1=<\1>  : \2', d)
    split = RE_OPTS.split(d)
    opt_types_desc = zip(split[1::3], split[2::3], split[3::3])
    d = ''.join('\n  --{0}=<{0}>  : {1}{2}'.format(*otd)
                for otd in opt_types_desc if otd[0] not in UNSUPPORTED_OPTS)

    d = """Usage:
  tqdm [--help | options]

Options:
  -h, --help     Print this help and exit
  -v, --version  Print version and exit

""" + d.strip('\n') + '\n'

    # opts = docopt(d, version=__version__)
    if any(v in argv for v in ('-v', '--version')):
        sys.stdout.write(__version__ + '\n')
        sys.exit(0)
    elif any(v in argv for v in ('-h', '--help')):
        sys.stdout.write(d + '\n')
        sys.exit(0)

    argv = RE_SHLEX.split(' '.join(["tqdm"] + argv))
    opts = dict(zip(argv[1::3], argv[3::3]))

    log.debug(opts)
    opts.pop('log', True)

    tqdm_args = {'file': fp}
    try:
        for (o, v) in opts.items():
            try:
                tqdm_args[o] = cast(v, opt_types[o])
            except KeyError as e:
                raise TqdmKeyError(str(e))
        log.debug('args:' + str(tqdm_args))
    except:
        fp.write('\nError:\nUsage:\n  tqdm [--help | options]\n')
        for i in sys.stdin:
            sys.stdout.write(i)
        raise
    else:
        buf_size = tqdm_args.pop('buf_size', 256)
        delim = tqdm_args.pop('delim', b'\\n')
        delim_per_char = tqdm_args.pop('bytes', False)
        tee = tqdm_args.pop('tee', False)
        manpath = tqdm_args.pop('manpath', None)
        comppath = tqdm_args.pop('comppath', None)
        stdin = getattr(sys.stdin, 'buffer', sys.stdin)
        stdout = getattr(sys.stdout, 'buffer', sys.stdout)
        if manpath or comppath:
            from os import path
            from shutil import copyfile
            from pkg_resources import resource_filename, Requirement

            def cp(src, dst):
                """copies from src path to dst"""
                copyfile(src, dst)
                log.info("written:" + dst)
            if manpath is not None:
                cp(resource_filename(Requirement.parse('tqdm'), 'tqdm/tqdm.1'),
                   path.join(manpath, 'tqdm.1'))
            if comppath is not None:
                cp(resource_filename(Requirement.parse('tqdm'),
                                     'tqdm/completion.sh'),
                   path.join(comppath, 'tqdm_completion.sh'))
            sys.exit(0)
        if tee:
            stdout_write = stdout.write
            fp_write = getattr(fp, 'buffer', fp).write

            class stdout(object):
                @staticmethod
                def write(x):
                    with tqdm.external_write_mode(file=fp):
                        fp_write(x)
                    stdout_write(x)
        if delim_per_char:
            tqdm_args.setdefault('unit', 'B')
            tqdm_args.setdefault('unit_scale', True)
            tqdm_args.setdefault('unit_divisor', 1024)
            log.debug(tqdm_args)
            with tqdm(**tqdm_args) as t:
                posix_pipe(stdin, stdout, '', buf_size, t.update)
        elif delim == b'\\n':
            log.debug(tqdm_args)
            for i in tqdm(stdin, **tqdm_args):
                stdout.write(i)
        else:
            log.debug(tqdm_args)
            with tqdm(**tqdm_args) as t:
                posix_pipe(stdin, stdout, delim, buf_size, t.update)
