"""
Auto-generate README.rst from .meta/.readme.rst and docstrings.
"""
from __future__ import print_function

import sys
from io import open as io_open
from os import path
from textwrap import dedent

sys.path.insert(0, path.dirname(path.dirname(__file__)))
import tqdm  # NOQA
import tqdm.cli  # NOQA

HEAD_ARGS = """
Parameters
----------
"""
HEAD_RETS = """
Returns
-------
"""
HEAD_CLI = """
Extra CLI Options
-----------------
name  : type, optional
    TODO: find out why this is needed.
"""


def doc2rst(doc, arglist=True, raw=False):
    """
    arglist  : bool, whether to create argument lists
    raw  : bool, ignores arglist and indents by 2 spaces
    """
    doc = doc.replace('`', '``')
    if raw:
        doc = doc.replace('\n ', '\n   ')
    else:
        doc = dedent(doc)
        if arglist:
            doc = '\n'.join(i if not i or i[0] == ' ' else '* ' + i + '  '
                            for i in doc.split('\n'))
    return doc


src_dir = path.abspath(path.dirname(__file__))
README_rst = path.join(src_dir, '.readme.rst')
with io_open(README_rst, mode='r', encoding='utf-8') as fd:
    README_rst = fd.read()
DOC_tqdm = doc2rst(tqdm.tqdm.__doc__, False).replace('\n', '\n      ')
DOC_tqdm_init = doc2rst(tqdm.tqdm.__init__.__doc__)
DOC_tqdm_init_args = DOC_tqdm_init.partition(doc2rst(HEAD_ARGS))[-1].replace('\n      ', '\n    ')
DOC_tqdm_init_args, _, DOC_tqdm_init_rets = DOC_tqdm_init_args.partition(doc2rst(HEAD_RETS))
DOC_cli = doc2rst(tqdm.cli.CLI_EXTRA_DOC).partition(doc2rst(HEAD_CLI))[-1]
DOC_tqdm_tqdm = {}
for i in dir(tqdm.tqdm):
    doc = getattr(tqdm.tqdm, i).__doc__
    if doc:
        DOC_tqdm_tqdm[i] = doc2rst(doc, raw=True)

# special cases
DOC_tqdm_init_args = DOC_tqdm_init_args.replace(' *,', ' ``*``,')
DOC_tqdm_init_args = DOC_tqdm_init_args.partition('* gui  : bool, optional')[0]

README_rst = (
    README_rst.replace('{DOC_tqdm}', DOC_tqdm)
    .replace('{DOC_tqdm.tqdm.__init__.Parameters}', DOC_tqdm_init_args)
    .replace('{DOC_tqdm.cli.CLI_EXTRA_DOC}', DOC_cli)
    .replace('{DOC_tqdm.tqdm.__init__.Returns}', DOC_tqdm_init_rets))
for k, v in DOC_tqdm_tqdm.items():
    README_rst = README_rst.replace('{DOC_tqdm.tqdm.%s}' % k, v)

if __name__ == "__main__":
    fndoc = path.join(path.dirname(src_dir), 'README.rst')
    with io_open(fndoc, mode='w', encoding='utf-8') as fd:
        fd.write(README_rst)
