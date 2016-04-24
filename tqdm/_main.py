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


# RE_OPTS = re.compile(r' {8}(\S+)\s{2,}:\s*(str|int|float|bool)', flags=re.M)
RE_OPTS = re.compile(r'\n {8}(\S+)\s{2,}:\s*([^\s,]+)')

# TODO: add custom support for some of the following?
UNSUPPORTED_OPTS = ('iterable', 'gui', 'out', 'file')


def main():
    d = tqdm.__init__.__doc__

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
        for i in tqdm(sys.stdin, **tqdm_args):
            sys.stdout.write(i)
    except:  # pragma: no cover
        sys.stderr.write('\nError:\nUsage:\n  tqdm [--help | options]\n')
        for i in sys.stdin:
            sys.stdout.write(i)
        raise
