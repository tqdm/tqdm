"""
Auto-generate README.rst from .meta/.readme.rst and docstrings.
"""
import re
import subprocess
import sys
from io import StringIO
from pathlib import Path
from textwrap import dedent

sys.path.insert(0, str(Path(__file__).parent.parent))
import tqdm  # noqa: E402
import tqdm.cli  # noqa: E402

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


def doc2rst(doc, arglist=True, raw=False, md2rst=True):
    """
    arglist  : bool, whether to create argument lists
    raw  : bool, ignores arglist and indents by 10 spaces
    md2rst  : bool, converts markdown to reStructuredText
    """
    if md2rst:
        doc = doc.replace('`', '``')
    if raw:
        doc = doc.replace('\n', '\n          ')
        doc = doc.replace('\n          \n', '\n\n')
    else:
        doc = dedent(doc)
        if arglist:
            doc = '\n'.join(i if not i or i[0] == ' ' else '* ' + i + '  '
                            for i in doc.split('\n'))
    return doc


src_dir = Path(__file__).parent.resolve()
README_rst = (src_dir / '.readme.rst').read_text("utf-8")
class_doc, init_doc = tqdm.tqdm.__doc__.split('\n\n', 1)
DOC_tqdm = doc2rst(class_doc + '\n', False, md2rst=False).replace('\n', '\n      ')
DOC_tqdm_init = doc2rst('\n' + init_doc)
DOC_tqdm_init_args = DOC_tqdm_init.partition(doc2rst(HEAD_ARGS))[-1].replace(
    '\n      ', '\n    ').replace('\n      ', '\n    ')
DOC_tqdm_init_args, _, DOC_tqdm_init_rets = DOC_tqdm_init_args.partition(doc2rst(HEAD_RETS))
DOC_cli = doc2rst(tqdm.cli.CLI_EXTRA_DOC).partition(doc2rst(HEAD_CLI))[-1]
DOC_tqdm_tqdm = {}
for i in dir(tqdm.tqdm):
    doc = getattr(tqdm.tqdm, i).__doc__
    if doc:
        DOC_tqdm_tqdm[i] = doc2rst(doc, raw=True, md2rst=False)

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

# python -m tqdm --help
sys.stdout, man = StringIO(), sys.stdout
try:
    tqdm.cli.main(argv=['--help'])
except SystemExit:
    sys.stdout, man = man, sys.stdout
man.seek(0)
# tail -n+5
for _ in range(4):
    man.readline()
# sed -r
man = man.read().replace('\\', '\\\\')
man = re.sub(r'^  (--.*)=<(.*)>  : (.*)$', r'\n\\\1=*\2*\n: \3.', man, flags=re.M)
man = re.sub(r'^  (--.*)  : (.*)$', r'\n\\\1\n: \2.', man, flags=re.M)
man = re.sub(r'  (-.*, )(--.*)  ', r'\n\1\\\2\n: ', man, flags=re.M)
# cat ".meta/.tqdm.1.md" -
man = (src_dir / '.tqdm.1.md').read_text() + man
# pandoc -s -t man
try:
    p = subprocess.Popen(['pandoc', '-s', '-t', 'man'],  # nosec B603
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE)
except FileNotFoundError:
    MAN_1 = None
else:
    MAN_1, _ = p.communicate(input=man.encode())

if __name__ == "__main__":
    (src_dir.parent / 'README.rst').write_text(README_rst, encoding='utf-8')
    if MAN_1:
        (src_dir.parent / 'tqdm' / 'tqdm.1').write_bytes(MAN_1)
    else:
        print("pandoc not found, skipping man page generation", file=sys.stderr)
