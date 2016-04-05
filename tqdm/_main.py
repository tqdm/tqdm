from ._tqdm import tqdm
from ._version import __version__  # NOQA
from docopt import docopt
import sys
import re
__all__ = ["main"]


def cast(val, typ):
    if val == 'None':
        return None
    if typ == 'bool':
        return str(val) == 'True'
    # try:
    return eval(typ + '("' + str(val) + '")')
    # except:
    #     # print val, typ
    #     if val == 'special':
    #         return 'whatever... just an example'
    #     else:
    #         return eval(typ + '()')


RE_OPTS = re.compile(r' {8}(\w+)\s{2,}:\s*(str|int|float|bool)', flags=re.M)
# RE_OPTS_SOME = re.compile(r' {8}(\w+)  : (str|int|float)', flags=re.M)
# RE_OPTS_BOOL = re.compile(r' {8}(\w+)  : bool', flags=re.M)


def main():
    d = tqdm.__init__.__doc__
    opt_types = dict(RE_OPTS.findall(d))
    # d = RE_OPTS_SOME.sub(r'  --\1=<v>  ', d)
    # d = RE_OPTS_BOOL.sub(r'  --\1      ', d)
    d = RE_OPTS.sub(r'  --\1=<v>  : \2', d)
    d = d[d.find('  --desc='):d.find('Returns\n')]
    __doc__ = """
Usage:
    tqdm [--help | options]

Options:
  -h, --help     Print this help and exit
  -v, --version  Print version and exit
""" + d
    opts = docopt(__doc__, version=__version__)

    try:
        for opt in opt_types:
            opt_types[opt] = cast(opts['--' + opt], opt_types[opt])
        for i in tqdm(sys.stdin, **opt_types):
            sys.stdout.write(i)
    except:  # pragma: no cover
        sys.stderr.write(__doc__ + '\n')
        for i in sys.stdin:
            sys.stdout.write(i)
