from __future__ import print_function
from os import path
import sys
sys.path.insert(0, path.dirname(path.dirname(__file__)))  # NOQA
import tqdm
import tqdm.cli
from io import open as io_open
from os import path
import re

RE_OPT = re.compile(r'(\w+)  :', flags=re.M)


def doc2opt(doc):
    """
    doc  : str, document to parse
    """
    return ('--' + i for i in RE_OPT.findall(doc))


# CLI options
options = {'-h', '--help', '-v', '--version'}
for doc in (tqdm.tqdm.__init__.__doc__, tqdm.cli.CLI_EXTRA_DOC):
    options.update(doc2opt(doc))
options.difference_update(
    '--' + i for i in ('name',) + tqdm.cli.UNSUPPORTED_OPTS)
src_dir = path.abspath(path.dirname(__file__))
completion = u"""\
#!/usr/bin/env bash

_tqdm()
{{
    local cur prv
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prv="${{COMP_WORDS[COMP_CWORD - 1]}}"

    case ${{prv}} in
        "--log")
            COMPREPLY=($(compgen -W 'CRITICAL FATAL ERROR WARN WARNING INFO DEBUG NOTSET' -- ${{cur}}))
            ;;
        *)
            COMPREPLY=($(compgen -W '{0}' -- ${{cur}}))
            ;;
    esac
}}

complete -F _tqdm tqdm
""".format(' '.join(options))

if __name__ == "__main__":
    fncompletion = path.join(path.dirname(src_dir), 'tqdm', 'completion.sh')
    with io_open(fncompletion, mode='w', encoding='utf-8') as fd:
        fd.write(completion)
