from __future__ import print_function
from os import path
import sys
sys.path.insert(0, path.dirname(path.dirname(__file__)))  # NOQA
import tqdm
import tqdm.cli
from io import open as io_open
from os import path
import re

def doc2opt(doc):
    """
    doc  : str, document to parse
    """
    options = ['--' + i.strip('  :') for i in re.findall(r'\w+  :', doc)]
    return options

# CLI options
options = ['-h', '--help', '-v', '--version']
options += doc2opt(tqdm.tqdm.__init__.__doc__)
options += doc2opt(tqdm.cli.CLI_EXTRA_DOC)

# Remove options without CLI support
no_support = ['--' + i for i in tqdm.cli.UNSUPPORTED_OPTS]
# TODO: Check and remove option `name`
no_support += ['--name']
options = list(set(options) - set(no_support))

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
