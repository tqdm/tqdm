from ._tqdm import tqdm
from ._version import __version__  # NOQA
import sys
import re
__all__ = ["main"]


class TqdmTypeError(TypeError):
    pass


class TqdmKeyError(KeyError):
    pass


def cast(val, typ):
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
        if (typ == 'chr'):
            return chr(ord(eval('"' + val + '"')))
        else:
            raise TqdmTypeError(val + ' : ' + typ)


def posix_pipe(fin, fout, delim='\n', buf_size=256,
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

    buf = ''
    tmp = ''
    # n = 0
    while True:
        tmp = fin.read(buf_size)

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
                buf = ''
                tmp = tmp[i + len(delim):]


# ((opt, type), ... )
RE_OPTS = re.compile(r'\n {8}(\S+)\s{2,}:\s*([^\s,]+)')
# better split method assuming no positional args
RE_SHLEX = re.compile(r'\s*--?([^\s=]+)(?:\s*|=|$)')

# TODO: add custom support for some of the following?
UNSUPPORTED_OPTS = ('iterable', 'gui', 'out', 'file')

# The 8 leading spaces are required for consistency
CLI_EXTRA_DOC = r"""
        Extra CLI Options
        -----------------
        delim  : chr, optional
            Delimiting character [default: '\n']. Use '\0' for null.
            N.B.: on Windows systems, Python converts '\n' to '\r\n'.
        buf_size  : int, optional
            String buffer size in bytes [default: 256]
            used when `delim` is specified.
"""


def main():
    d = tqdm.__init__.__doc__ + CLI_EXTRA_DOC

    opt_types = dict(RE_OPTS.findall(d))

    for o in UNSUPPORTED_OPTS:
        opt_types.pop(o)

    # d = RE_OPTS.sub(r'  --\1=<\1>  : \2', d)
    split = RE_OPTS.split(d)
    opt_types_desc = zip(split[1::3], split[2::3], split[3::3])
    d = ''.join('\n  --{0}=<{0}>  : {1}{2}'.format(*otd)
                for otd in opt_types_desc if otd[0] not in UNSUPPORTED_OPTS)

    __doc__ = """Usage:
  tqdm [--help | options]

Options:
  -h, --help     Print this help and exit
  -v, --version  Print version and exit

""" + d.strip('\n') + '\n'

    # opts = docopt(__doc__, version=__version__)
    if any(v in sys.argv for v in ('-v', '--version')):
        sys.stdout.write(__version__ + '\n')
        sys.exit(0)
    elif any(v in sys.argv for v in ('-h', '--help')):
        sys.stdout.write(__doc__ + '\n')
        sys.exit(0)

    argv = RE_SHLEX.split(' '.join(sys.argv))
    opts = dict(zip(argv[1::2], argv[2::2]))

    tqdm_args = {}
    try:
        for (o, v) in opts.items():
            try:
                tqdm_args[o] = cast(v, opt_types[o])
            except KeyError as e:
                raise TqdmKeyError(str(e))
        # sys.stderr.write('\ndebug | args: ' + str(tqdm_args) + '\n')
    except:
        sys.stderr.write('\nError:\nUsage:\n  tqdm [--help | options]\n')
        for i in sys.stdin:
            sys.stdout.write(i)
        raise
    else:
        delim = tqdm_args.pop('delim', '\n')
        buf_size = tqdm_args.pop('buf_size', 256)
        if delim == '\n':
            for i in tqdm(sys.stdin, **tqdm_args):
                sys.stdout.write(i)
        else:
            with tqdm(**tqdm_args) as t:
                posix_pipe(sys.stdin, sys.stdout,
                           delim, buf_size, t.update)
