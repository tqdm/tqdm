import re
import tqdm
import tqdm.cli

RE_OPT = re.compile(r'(\w+)  :', flags=re.M)


def doc2opt(doc):
    return ('--' + i for i in RE_OPT.findall(doc))


def test_autogenerate_cli():
    # CLI options
    options = {'-h', '--help', '-v', '--version'}
    for doc in (tqdm.tqdm.__init__.__doc__, tqdm.cli.CLI_EXTRA_DOC):
        options.update(doc2opt(doc))
    options.difference_update(
        '--' + i for i in ('name',) + tqdm.cli.UNSUPPORTED_OPTS)

    # All options
    # Add new CLI options to this list
    all_opts = {
            '-h', '-v', '--help', '--version',
            '--desc', '--total', '--leave', '--ncols',
            '--mininterval', '--maxinterval', '--miniters',
            '--ascii', '--disable', '--unit', '--unit_scale',
            '--dynamic_ncols', '--smoothing', '--bar_format',
            '--initial', '--position', '--postfix', '--unit_divisor',
            '--bytes', '--write_bytes', '--lock_args', '--nrows',
            '--delim', '--buf_size', '--manpath', '--log',
            '--comppath'
        }

    assert options == all_opts
