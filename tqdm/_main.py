from ._tqdm import tqdm
from ._version import __version__  # NOQA
import sys
import re
__all__ = ["main"]


def cast(val, typ):
    if typ == 'bool':
        # sys.stderr.write('\ndebug | `val:type`: `' + val + ':' + typ + '`.\n')
        if (val == 'True') or (val == ''):
            return True
        elif val == 'False':
            return False
        else:
            raise ValueError(val + ' : ' + typ)

    return eval(typ + '("' + val + '")')


def posix_pipe(fin, fout, delim='\n', buf_size=4, callback=None):
    """
    Returns
    -------
    out  : int. The number of items processed.
    """
    if callback is None:
        def callback(i):
            pass

    buf = ''
    # n = 0
    while True:
        tmp = fin.read(buf_size)

        # flush at EOF
        if not tmp:
            if buf:
                fout.write(buf)
                callback(1 + buf.count(delim))  # n += 1 + buf.count(delim)
            getattr(fout, 'flush', lambda: None)()
            return  # n

        try:
            i = tmp.index(delim)
        except ValueError:
            buf += tmp
        else:
            callback(1)  # n += 1
            fout.write(buf + tmp[:i + len(delim)])
            buf = tmp[i + len(delim):]


# RE_OPTS = re.compile(r' {8}(\S+)\s{2,}:\s*(str|int|float|bool)', flags=re.M)
RE_OPTS = re.compile(r'\n {8}(\S+)\s{2,}:\s*([^\s,]+)')

# TODO: add custom support for some of the following?
UNSUPPORTED_OPTS = ('iterable', 'gui', 'out', 'file')

# The 8 leading spaces are required for consistency
CLI_EXTRA_DOC = """
        CLI Options
        -----------
        delim  : int, optional
            ascii ordinal for delimiting character [default: 10].
            Example common values are given below.
             0 : null
             9 : \\t
            10 : \\n
            13 : \\r
        buf_size  : int, optional
            String buffer size [default: 4] used when `delim` is specified.
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

    argv = re.split('\s*(--\S+)[=\s]*', ' '.join(sys.argv[1:]))
    opts = dict(zip(argv[1::2], argv[2::2]))

    tqdm_args = {}
    try:
        for (o, v) in opts.items():
            tqdm_args[o[2:]] = cast(v, opt_types[o[2:]])
        # sys.stderr.write('\ndebug | args: ' + str(tqdm_args) + '\n')

        delim = chr(tqdm_args.pop('delim', 10))
        buf_size = tqdm_args.pop('buf_size', 4)
        if delim == 10:
            for i in tqdm(sys.stdin, **tqdm_args):
                sys.stdout.write(i)
        else:
            with tqdm(**tqdm_args) as t:
                posix_pipe(sys.stdin, sys.stdout,
                           delim, buf_size, t.update)
    except:  # pragma: no cover
        sys.stderr.write('\nError:\nUsage:\n  tqdm [--help | options]\n')
        for i in sys.stdin:
            sys.stdout.write(i)
        raise
